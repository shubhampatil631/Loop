import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.config import settings

import threading
from concurrent.futures import ThreadPoolExecutor

class InMemoryDatabase:
    """Fallback in-memory database if MongoDB is not running."""
    def __init__(self):
        self.users: Dict[str, dict] = {}
        self.vocab_items: Dict[str, dict] = {}
        self.mistake_tags: Dict[str, dict] = {}
        self.conversations: Dict[str, dict] = {}
        self.sessions: Dict[str, dict] = {}

class Database:
    def __init__(self):
        self.mongo_client: Optional[MongoClient] = None
        self.db = None
        self.is_connected = False
        self.fallback = InMemoryDatabase()
        self.connect()

    def connect(self):
        try:
            self.mongo_client = MongoClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=10000,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=120000,
                retryWrites=True,
                appName="LoopTutor"
            )
            # Trigger a quick command to test connection
            self.mongo_client.admin.command('ping')
            try:
                self.db = self.mongo_client.get_default_database()
            except Exception:
                self.db = self.mongo_client["loop"]
            if self.db is None:
                self.db = self.mongo_client["loop"]
            self.is_connected = True
            # Run index initialization in background thread to avoid blocking connect/startup
            threading.Thread(target=self.init_indexes, daemon=True).start()
            print(f"[DB] Connected successfully to MongoDB: {self.db.name}")
        except Exception as e:
            self.is_connected = False
            self.db = None
            print(f"[DB] MongoDB not available ({e}). Using robust In-Memory Database store.")

    def init_indexes(self):
        if not self.is_connected or self.db is None:
            return
        try:
            self.db.users.create_index([("created_at", DESCENDING)])
            self.db.vocab_items.create_index([("user_id", ASCENDING), ("due_at", ASCENDING)])
            self.db.mistake_tags.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
            self.db.sessions.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
            self.db.conversations.create_index([("session_id", ASCENDING)])
            self.db.conversations.create_index([("user_id", ASCENDING)])
        except Exception as e:
            print(f"[DB] Index creation warning: {e}")

    # User operations
    def create_user(
        self,
        name: str,
        target_language: str = "es",
        goal: str = "travel",
        level: str = "A1",
        seed_starter_vocab: bool = True
    ) -> dict:
        user_id = str(uuid.uuid4())[:8]
        user_doc = {
            "_id": user_id,
            "id": user_id,
            "name": name,
            "target_language": target_language,
            "goal": goal,
            "level": level,
            "created_at": datetime.utcnow(),
            "last_session_at": None,
            "streak_days": 1
        }
        if self.is_connected and self.db is not None:
            self.db.users.insert_one(user_doc)
        else:
            self.fallback.users[user_id] = user_doc

        if seed_starter_vocab:
            starter_words = [
                ("el café", "A1", "travel"),
                ("el boleto", "A1", "travel"),
                ("la cuenta", "A1", "travel"),
                ("la estación", "A1", "travel"),
                ("el hotel", "A1", "travel"),
                ("la familia", "A1", "family"),
                ("el trabajo", "A2", "work"),
                ("la reunión", "A2", "work"),
            ]
            for lemma, lvl, thm in starter_words:
                self.create_vocab_item(user_id=user_id, lemma=lemma, cefr_level=lvl, theme=thm)

        return user_doc


    def get_user(self, user_id: str) -> Optional[dict]:
        if self.is_connected and self.db is not None:
            doc = self.db.users.find_one({"_id": user_id})
            if doc:
                doc["id"] = str(doc["_id"])
                return doc
        return self.fallback.users.get(user_id)

    def get_all_users(self, limit: int = 100) -> List[dict]:
        """Fetch all learners who tried the platform, with session count summaries."""
        if self.is_connected and self.db is not None:
            cursor = list(self.db.users.find().sort("created_at", -1).limit(limit))
            if not cursor:
                return []

            uids = [str(doc["_id"]) for doc in cursor]

            session_counts = {}
            mistake_counts = {}

            def fetch_session_counts():
                counts = {}
                try:
                    for r in self.db.sessions.aggregate([
                        {"$match": {"user_id": {"$in": uids}}},
                        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}}
                    ]):
                        counts[str(r["_id"])] = r["count"]
                except Exception as e:
                    print(f"[DB] Session aggregation warning: {e}")
                return counts

            def fetch_mistake_counts():
                counts = {}
                try:
                    for r in self.db.mistake_tags.aggregate([
                        {"$match": {"user_id": {"$in": uids}}},
                        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}}
                    ]):
                        counts[str(r["_id"])] = r["count"]
                except Exception as e:
                    print(f"[DB] Mistake aggregation warning: {e}")
                return counts

            # Run aggregations concurrently across thread pool
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_sessions = executor.submit(fetch_session_counts)
                future_mistakes = executor.submit(fetch_mistake_counts)
                session_counts = future_sessions.result()
                mistake_counts = future_mistakes.result()

            users_list = []
            for doc in cursor:
                uid = str(doc["_id"])
                doc["id"] = uid
                doc["total_sessions"] = session_counts.get(uid, 0)
                doc["total_mistakes"] = mistake_counts.get(uid, 0)
                users_list.append(doc)
            return users_list

        users_list = []
        for uid, doc in self.fallback.users.items():
            u_copy = dict(doc)
            u_copy["id"] = uid
            u_copy["total_sessions"] = len([s for s in self.fallback.sessions.values() if s.get("user_id") == uid])
            u_copy["total_mistakes"] = len([m for m in self.fallback.mistake_tags.values() if m.get("user_id") == uid])
            users_list.append(u_copy)
        return sorted(users_list, key=lambda x: x.get("created_at") or datetime.min, reverse=True)[:limit]

    def get_user_sessions(self, user_id: str, limit: int = 50) -> List[dict]:
        """Fetch all sessions belonging to a specific learner."""
        if self.is_connected and self.db is not None:
            cursor = self.db.sessions.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
            return [dict(doc, id=str(doc["_id"])) for doc in cursor]
        sessions = [dict(s, id=str(s.get("id") or s.get("_id"))) for s in self.fallback.sessions.values() if s.get("user_id") == user_id]
        return sorted(sessions, key=lambda x: x.get("created_at") or datetime.min, reverse=True)[:limit]

    def update_user(self, user_id: str, updates: dict) -> Optional[dict]:
        if self.is_connected and self.db is not None:
            self.db.users.update_one({"_id": user_id}, {"$set": updates})
            return self.get_user(user_id)
        if user_id in self.fallback.users:
            self.fallback.users[user_id].update(updates)
            return self.fallback.users[user_id]
        return None

    # Vocab Item operations
    def create_vocab_item(self, user_id: str, lemma: str, cefr_level: str = "A1", theme: str = "travel", ease_factor: float = 2.5, interval_days: int = 1) -> dict:
        item_id = str(uuid.uuid4())[:8]
        doc = {
            "_id": item_id,
            "id": item_id,
            "user_id": user_id,
            "lemma": lemma,
            "cefr_level": cefr_level,
            "theme": theme,
            "ease_factor": ease_factor,
            "interval_days": interval_days,
            "due_at": datetime.utcnow() - timedelta(minutes=5),  # immediately available
            "reps": 0,
            "last_outcome": None,
            "last_reviewed_at": None
        }
        if self.is_connected and self.db is not None:
            self.db.vocab_items.insert_one(doc)
        else:
            self.fallback.vocab_items[item_id] = doc
        return doc

    def get_due_vocab_items(self, user_id: str, limit: int = 10) -> List[dict]:
        now = datetime.utcnow()
        if self.is_connected and self.db is not None:
            cursor = self.db.vocab_items.find({
                "user_id": user_id,
                "due_at": {"$lte": now}
            }).sort("due_at", ASCENDING).limit(limit)
            items = []
            for doc in cursor:
                doc["id"] = str(doc["_id"])
                items.append(doc)
            return items
        items = [
            doc for doc in self.fallback.vocab_items.values()
            if doc.get("user_id") == user_id and doc.get("due_at", now) <= now
        ]
        items.sort(key=lambda x: x.get("due_at", now))
        return items[:limit]

    def get_all_user_vocab(self, user_id: str) -> List[dict]:
        if self.is_connected and self.db is not None:
            cursor = self.db.vocab_items.find({"user_id": user_id})
            items = []
            for doc in cursor:
                doc["id"] = str(doc["_id"])
                items.append(doc)
            return items
        return [doc for doc in self.fallback.vocab_items.values() if doc.get("user_id") == user_id]

    def update_vocab_item(self, item_id: str, updates: dict) -> Optional[dict]:
        if self.is_connected and self.db is not None:
            self.db.vocab_items.update_one({"_id": item_id}, {"$set": updates})
            doc = self.db.vocab_items.find_one({"_id": item_id})
            if doc:
                doc["id"] = str(doc["_id"])
                return doc
        if item_id in self.fallback.vocab_items:
            self.fallback.vocab_items[item_id].update(updates)
            return self.fallback.vocab_items[item_id]
        return None

    def log_mistake_tag(self, user_id: str, vocab_item_id: Optional[str], error_type: str, severity: str, example_turn: str, correction: Optional[str] = None, explanation: Optional[str] = None) -> dict:
        tag_id = str(uuid.uuid4())[:8]
        doc = {
            "_id": tag_id,
            "id": tag_id,
            "user_id": user_id,
            "vocab_item_id": vocab_item_id,
            "error_type": error_type,
            "severity": severity,
            "example_turn": example_turn,
            "correction": correction,
            "explanation": explanation,
            "created_at": datetime.utcnow(),
            "retriggered_count": 0
        }
        if self.is_connected and self.db is not None:
            self.db.mistake_tags.insert_one(doc)
        else:
            self.fallback.mistake_tags[tag_id] = doc
        return doc

    def update_mistake_tag(self, tag_id: str, updates: dict) -> Optional[dict]:
        if self.is_connected and self.db is not None:
            self.db.mistake_tags.update_one({"_id": tag_id}, {"$set": updates})
            doc = self.db.mistake_tags.find_one({"_id": tag_id})
            if doc:
                doc["id"] = str(doc["_id"])
                return doc
        if tag_id in self.fallback.mistake_tags:
            self.fallback.mistake_tags[tag_id].update(updates)
            return self.fallback.mistake_tags[tag_id]
        return None


    def get_retriggerable_mistakes(self, user_id: str, limit: int = 5) -> List[dict]:
        """
        Fetch mistakes eligible for conversational re-triggering per AGENT-SPECS.md §4.
        Priority:
        1. Mistakes with retriggered_count == 0 created 2-5 days ago (ideal forgetting window).
        2. Mistakes with retriggered_count == 0 created < 2 days ago or < 7 days ago.
        3. Mistakes with lowest retriggered_count ordered by oldest created_at.
        """
        now = datetime.utcnow()
        t_2d = now - timedelta(days=2)
        t_5d = now - timedelta(days=5)
        t_7d = now - timedelta(days=7)

        if self.is_connected and self.db is not None:
            tier1 = list(self.db.mistake_tags.find({
                "user_id": user_id,
                "retriggered_count": 0,
                "created_at": {"$gte": t_5d, "$lte": t_2d}
            }).sort("created_at", ASCENDING).limit(limit))

            results = [dict(d, id=str(d["_id"])) for d in tier1]
            if len(results) >= limit:
                return results[:limit]

            existing_ids = {d["id"] for d in results}
            tier2 = list(self.db.mistake_tags.find({
                "user_id": user_id,
                "retriggered_count": 0,
                "_id": {"$nin": [d["_id"] for d in tier1]}
            }).sort("created_at", ASCENDING).limit(limit - len(results)))

            for d in tier2:
                doc_dict = dict(d, id=str(d["_id"]))
                if doc_dict["id"] not in existing_ids:
                    results.append(doc_dict)
                    existing_ids.add(doc_dict["id"])

            if len(results) >= limit:
                return results[:limit]

            tier3 = list(self.db.mistake_tags.find({
                "user_id": user_id,
                "_id": {"$nin": [d["_id"] for d in tier1 + tier2]}
            }).sort([("retriggered_count", ASCENDING), ("created_at", ASCENDING)]).limit(limit - len(results)))

            for d in tier3:
                doc_dict = dict(d, id=str(d["_id"]))
                if doc_dict["id"] not in existing_ids:
                    results.append(doc_dict)

            return results[:limit]

        # In-memory fallback
        all_user_mistakes = [
            doc for doc in self.fallback.mistake_tags.values()
            if doc.get("user_id") == user_id
        ]

        def get_age_days(doc):
            created = doc.get("created_at", now)
            if isinstance(created, str):
                try:
                    created = datetime.fromisoformat(created)
                except Exception:
                    created = now
            return max(0.0, (now - created).total_seconds() / 86400.0)

        # Tier 1: 2 to 5 days old, retriggered_count == 0
        tier1 = [
            d for d in all_user_mistakes
            if d.get("retriggered_count", 0) == 0 and 2.0 <= get_age_days(d) <= 5.0
        ]
        tier1.sort(key=get_age_days, reverse=True)

        # Tier 2: other retriggered_count == 0
        tier2 = [
            d for d in all_user_mistakes
            if d.get("retriggered_count", 0) == 0 and d not in tier1
        ]
        tier2.sort(key=get_age_days, reverse=True)

        # Tier 3: lowest retriggered count
        tier3 = [
            d for d in all_user_mistakes
            if d not in tier1 and d not in tier2
        ]
        tier3.sort(key=lambda d: (d.get("retriggered_count", 0), -get_age_days(d)))

        combined = tier1 + tier2 + tier3
        return combined[:limit]

    def increment_mistake_retrigger(self, mistake_id: str):
        if self.is_connected and self.db is not None:
            self.db.mistake_tags.update_one({"_id": mistake_id}, {"$inc": {"retriggered_count": 1}})
        elif mistake_id in self.fallback.mistake_tags:
            self.fallback.mistake_tags[mistake_id]["retriggered_count"] = self.fallback.mistake_tags[mistake_id].get("retriggered_count", 0) + 1


    def get_user_mistakes(self, user_id: str, limit: int = 10) -> List[dict]:
        if self.is_connected and self.db is not None:
            cursor = self.db.mistake_tags.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
            items = []
            for doc in cursor:
                doc["id"] = str(doc["_id"])
                items.append(doc)
            return items
        items = [doc for doc in self.fallback.mistake_tags.values() if doc.get("user_id") == user_id]
        items.sort(key=lambda x: x.get("created_at", datetime.utcnow()), reverse=True)
        return items[:limit]

    def get_mistakes_by_ids(self, mistake_ids: List[str]) -> List[dict]:
        if not mistake_ids:
            return []
        if self.is_connected and self.db is not None:
            cursor = self.db.mistake_tags.find({"_id": {"$in": mistake_ids}})
            items = []
            for doc in cursor:
                doc["id"] = str(doc["_id"])
                items.append(doc)
            return items
        return [
            doc for doc in self.fallback.mistake_tags.values()
            if doc.get("id") in mistake_ids or doc.get("_id") in mistake_ids
        ]


    # Session & Conversation operations
    def create_session(self, user_id: str, mode: str = "daily_loop") -> dict:
        sess_id = str(uuid.uuid4())[:8]
        doc = {
            "_id": sess_id,
            "id": sess_id,
            "user_id": user_id,
            "mode": mode,
            "mastery_delta": 0.0,
            "items_touched": [],
            "mistakes_tagged": [],
            "mistakes_retriggered": [],
            "next_review_eta": datetime.utcnow() + timedelta(days=1),
            "created_at": datetime.utcnow(),
            "turns": [],
            "is_ended": False
        }
        if self.is_connected and self.db is not None:
            self.db.sessions.insert_one(doc)
        else:
            self.fallback.sessions[sess_id] = doc
        return doc

    def get_session(self, session_id: str) -> Optional[dict]:
        if self.is_connected and self.db is not None:
            doc = self.db.sessions.find_one({"_id": session_id})
            if doc:
                doc["id"] = str(doc["_id"])
                return doc
        return self.fallback.sessions.get(session_id)

    def update_session(self, session_id: str, updates: dict) -> Optional[dict]:
        if self.is_connected and self.db is not None:
            self.db.sessions.update_one({"_id": session_id}, {"$set": updates})
            return self.get_session(session_id)
        if session_id in self.fallback.sessions:
            self.fallback.sessions[session_id].update(updates)
            return self.fallback.sessions[session_id]
        return None

    # Conversation Collection operations (DATA-MODELS.md §1)
    def create_conversation(self, user_id: str, session_id: str, initial_turns: Optional[List[dict]] = None) -> dict:
        conv_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow()
        doc = {
            "_id": conv_id,
            "id": conv_id,
            "user_id": user_id,
            "session_id": session_id,
            "turns": initial_turns or [],
            "started_at": now,
            "ended_at": None
        }
        if self.is_connected and self.db is not None:
            self.db.conversations.insert_one(doc)
        else:
            self.fallback.conversations[conv_id] = doc
        return doc

    def append_conversation_turn(self, session_id: str, role: str, text: str) -> Optional[dict]:
        turn = {
            "role": role,
            "text": text,
            "ts": datetime.utcnow()
        }
        if self.is_connected and self.db is not None:
            self.db.conversations.update_one(
                {"session_id": session_id},
                {"$push": {"turns": turn}}
            )
            doc = self.db.conversations.find_one({"session_id": session_id})
            if doc:
                doc["id"] = str(doc["_id"])
                return doc
        for conv in self.fallback.conversations.values():
            if conv.get("session_id") == session_id:
                conv.setdefault("turns", []).append(turn)
                return conv
        return None

    def end_conversation(self, session_id: str):
        now = datetime.utcnow()
        if self.is_connected and self.db is not None:
            self.db.conversations.update_one(
                {"session_id": session_id},
                {"$set": {"ended_at": now}}
            )
        else:
            for conv in self.fallback.conversations.values():
                if conv.get("session_id") == session_id:
                    conv["ended_at"] = now

    def get_conversation_by_session(self, session_id: str) -> Optional[dict]:
        if self.is_connected and self.db is not None:
            doc = self.db.conversations.find_one({"session_id": session_id})
            if doc:
                doc["id"] = str(doc["_id"])
                return doc
        for conv in self.fallback.conversations.values():
            if conv.get("session_id") == session_id:
                return conv
        return None

    def get_user_conversations(self, user_id: str) -> List[dict]:
        if self.is_connected and self.db is not None:
            cursor = self.db.conversations.find({"user_id": user_id}).sort("started_at", DESCENDING)
            convs = []
            for doc in cursor:
                doc["id"] = str(doc["_id"])
                convs.append(doc)
            return convs
        return [c for c in self.fallback.conversations.values() if c.get("user_id") == user_id]

db = Database()

