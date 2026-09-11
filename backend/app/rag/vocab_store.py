import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.config import settings

LEVEL_HIERARCHY = {
    "A1": ["A1"],
    "A2": ["A1", "A2"],
    "B1": ["A1", "A2", "B1"],
    "B2": ["A1", "A2", "B1", "B2"]
}

THEME_ALIASES = {
    "cafe": ["cafe", "travel", "shopping"],
    "food": ["cafe", "travel", "shopping"],
    "travel": ["travel", "cafe", "transport"],
    "transport": ["travel", "transport"],
    "work": ["work", "business"],
    "business": ["work", "business"],
    "family": ["family", "daily", "social"],
    "daily": ["family", "daily", "social"],
    "social": ["social", "family", "daily"],
    "shopping": ["shopping", "travel", "cafe"],
    "health": ["health", "daily"]
}

class VocabStore:
    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.is_chroma_ready = False
        self.in_memory_docs: List[Dict[str, Any]] = []
        self._init_store()

    def _init_store(self):
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            persist_dir = os.path.abspath(settings.CHROMA_PERSIST_DIR)
            os.makedirs(persist_dir, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(path=persist_dir)
            self.collection = self.chroma_client.get_or_create_collection(
                name="vocab_bank",
                metadata={"description": "Static leveled reference CEFR vocabulary bank"}
            )
            self.is_chroma_ready = True
            doc_count = self.collection.count()
            print(f"[RAG] ChromaDB initialized at {persist_dir}, total docs in vocab_bank: {doc_count}")

            # Auto-seed if collection is empty
            if doc_count == 0:
                self._auto_seed()

        except Exception as e:
            self.is_chroma_ready = False
            print(f"[RAG] ChromaDB init fallback ({e}). Using local in-memory vocabulary RAG.")
            self._auto_seed()

    def _auto_seed(self):
        """Auto-seeds vocabulary dataset into store if empty."""
        try:
            from scripts.seed_vocab_bank import VOCAB_DATA, normalize_vocab_id
            docs = [item["sentence"] for item in VOCAB_DATA]
            metas = [
                {
                    "lemma": item["lemma"],
                    "cefr_level": item["cefr_level"],
                    "pos": item["pos"],
                    "theme": item["theme"],
                    "translation": item.get("translation", "")
                }
                for item in VOCAB_DATA
            ]
            ids = [normalize_vocab_id(item["lemma"], item["cefr_level"]) for item in VOCAB_DATA]
            self.add_documents(documents=docs, metadatas=metas, ids=ids)
            print(f"[RAG] Auto-seeded {len(VOCAB_DATA)} reference CEFR items.")
        except Exception as err:
            print(f"[RAG] Auto-seed note: {err}")

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        """Upsert vocab items into Chroma and in-memory cache."""
        for doc, meta, doc_id in zip(documents, metadatas, ids):
            # Update existing or append new in-memory item
            existing = next((d for d in self.in_memory_docs if d["id"] == doc_id), None)
            if existing:
                existing["document"] = doc
                existing["metadata"] = meta
            else:
                self.in_memory_docs.append({
                    "id": doc_id,
                    "document": doc,
                    "metadata": meta
                })

        if self.is_chroma_ready and self.collection is not None:
            try:
                self.collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
            except Exception as e:
                print(f"[RAG] Warning upserting to ChromaDB: {e}")

    def query_vocab(
        self,
        level: str = "A1",
        theme: str = "travel",
        k: int = 5,
        query_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query vocab items strictly grounded in CEFR level hierarchy (level <= learner.level)
        and biased toward theme and query context.
        """
        allowed_levels = LEVEL_HIERARCHY.get(level.upper(), ["A1"])
        theme_clean = theme.lower().strip()
        matching_themes = THEME_ALIASES.get(theme_clean, [theme_clean])

        q_text = query_text or f"Conversational Spanish vocabulary about {theme} at level {level}"

        # 1. Query ChromaDB if ready
        if self.is_chroma_ready and self.collection is not None and self.collection.count() > 0:
            try:
                # First attempt: Level filter + Theme filter
                # Handle single or multiple theme aliases
                theme_filter = (
                    {"theme": {"$in": matching_themes}}
                    if len(matching_themes) > 1
                    else {"theme": matching_themes[0]}
                )
                where_filter = {
                    "$and": [
                        {"cefr_level": {"$in": allowed_levels}},
                        theme_filter
                    ]
                }
                chroma_res = self.collection.query(
                    query_texts=[q_text],
                    n_results=k,
                    where=where_filter
                )

                results = []
                if chroma_res and chroma_res.get("documents") and len(chroma_res["documents"][0]) > 0:
                    for i in range(len(chroma_res["documents"][0])):
                        doc = chroma_res["documents"][0][i]
                        meta = chroma_res["metadatas"][0][i] if chroma_res.get("metadatas") else {}
                        results.append({"document": doc, "metadata": meta})
                    if len(results) >= min(k, 3):
                        return results

                # Second attempt: Widen filter to Level only if theme results were sparse
                where_level_only = {"cefr_level": {"$in": allowed_levels}}
                chroma_res_widen = self.collection.query(
                    query_texts=[q_text],
                    n_results=k,
                    where=where_level_only
                )
                if chroma_res_widen and chroma_res_widen.get("documents") and len(chroma_res_widen["documents"][0]) > 0:
                    widen_results = []
                    for i in range(len(chroma_res_widen["documents"][0])):
                        doc = chroma_res_widen["documents"][0][i]
                        meta = chroma_res_widen["metadatas"][0][i] if chroma_res_widen.get("metadatas") else {}
                        widen_results.append({"document": doc, "metadata": meta})
                    return widen_results

            except Exception as e:
                print(f"[RAG] Chroma query fallback: {e}")

        # 2. In-Memory Search Fallback
        # Strict level filter
        candidates = [
            d for d in self.in_memory_docs
            if d["metadata"].get("cefr_level") in allowed_levels
        ]

        if not candidates:
            return []

        # Score in-memory candidates by theme match + lexical overlap
        def score_doc(item: Dict[str, Any]) -> float:
            score = 0.0
            meta = item["metadata"]
            if meta.get("theme", "").lower() in matching_themes:
                score += 3.0
            if meta.get("cefr_level") == level.upper():
                score += 1.5  # Slightly prefer exact target level over lower
            doc_words = set(re.findall(r"\w+", (item["document"] + " " + meta.get("lemma", "")).lower()))
            q_words = set(re.findall(r"\w+", q_text.lower()))
            overlap = len(doc_words.intersection(q_words))
            score += overlap * 0.8
            return score

        sorted_candidates = sorted(candidates, key=score_doc, reverse=True)
        return [
            {"document": d["document"], "metadata": d["metadata"]}
            for d in sorted_candidates[:k]
        ]

vocab_store = VocabStore()

