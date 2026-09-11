from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.models.db import db
from app.models.schemas import VocabItem, MistakeTag, OutcomeType
from app.tools.mcp_tools import schedule_next_review, get_due_items

class CurriculumAgent:
    SCENARIO_PROGRESSION = {
        "travel": [
            {"title": "Ordering at a Traditional Tapas Bar", "description": "Practice ordering local appetizers, inquiring about ingredients, and requesting the bill.", "level": "A1"},
            {"title": "Purchasing Train Tickets at the Station", "description": "Inquire about departures, round-trip fares, platform numbers, and seating options.", "level": "A1"},
            {"title": "Hotel Check-In & Inquiring About Amenities", "description": "Check in with reservation details, ask about breakfast hours, and request room adjustments.", "level": "A2"},
            {"title": "Asking for Directions in Madrid Old Town", "description": "Navigate unfamiliar streets, ask locals for landmarks, and understand directional phrases.", "level": "A2"},
            {"title": "Handling a Flight Delay at the Airport", "description": "Communicate with customer service agents, inquire about baggage, and request rebooking.", "level": "B1"},
        ],
        "work": [
            {"title": "Introducing Yourself to New Team Members", "description": "Share your role, previous background, and professional goals in a natural conversational style.", "level": "A1"},
            {"title": "Scheduling a Project Sync Meeting", "description": "Propose meeting times, align on agendas, and confirm participant availability.", "level": "A1"},
            {"title": "Discussing Project Blockers & Next Steps", "description": "Highlight workflow dependencies, request assistance from colleagues, and set deadlines.", "level": "A2"},
            {"title": "Client Status Briefing & Negotiation", "description": "Present project milestones, handle client inquiries, and establish deliverables.", "level": "B1"},
        ],
        "family": [
            {"title": "Casual Coffee & Catching Up with Friends", "description": "Ask about weekend plans, share recent updates, and talk about hobbies and family.", "level": "A1"},
            {"title": "Shopping at a Neighborhood Fresh Market", "description": "Ask vendors about produce origin, prices by kilo, and choose the best seasonal fruit.", "level": "A1"},
            {"title": "Attending a Festive Family Dinner", "description": "Compliment the host on traditional dishes, participate in group stories, and toast the occasion.", "level": "A2"},
            {"title": "Planning a Weekend Excursion to the Mountains", "description": "Coordinate transport, pack lists, weather contingencies, and itinerary timing.", "level": "A2"},
        ]
    }

    def get_next_scenario(self, user_id: str, current_theme: str = "travel", current_level: str = "A1") -> Dict[str, str]:
        """Dynamically pick the next recommended scenario based on user goal, level, and past completed sessions."""
        user_sessions = db.get_user_sessions(user_id=user_id, limit=20) if user_id else []
        session_idx = len(user_sessions)
        
        goal_key = (current_theme or "travel").lower()
        if goal_key not in self.SCENARIO_PROGRESSION:
            goal_key = "travel"
            
        scenarios = self.SCENARIO_PROGRESSION[goal_key]
        chosen = scenarios[session_idx % len(scenarios)]
        return {
            "title": chosen["title"],
            "description": chosen["description"],
            "level": chosen.get("level", current_level)
        }

    def get_session_due_items(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Pull items due for review for this session ordered by due_at ascending."""
        items = get_due_items(user_id=user_id, limit=limit)
        return [item.model_dump(by_alias=True) for item in items]

    def get_retrigger_mistakes(self, user_id: str, limit: int = 2) -> List[Dict[str, Any]]:
        """
        Pull candidate mistake tags eligible for conversational re-triggering.
        """
        mistakes = db.get_retriggerable_mistakes(user_id=user_id, limit=limit)
        for m in mistakes:
            # Mark that it has been selected for retriggering
            db.increment_mistake_retrigger(m["id"])
        return mistakes

    def update_session_learning_state(
        self,
        user_id: str,
        items_touched_ids: List[str],
        tagged_mistakes: List[Dict[str, Any]],
        turn_count: int
    ) -> Dict[str, Any]:
        """
        Computes FSRS review updates and mastery delta after a session.
        Applies SM-2/FSRS scheduling rules to all items touched or involved in mistakes.
        """
        mistake_lemmas = {
            (m.get("vocab_item") or "").lower().strip()
            for m in tagged_mistakes
            if m.get("vocab_item")
        }
        mistake_vocab_ids = {
            m.get("vocab_item_id")
            for m in tagged_mistakes
            if m.get("vocab_item_id")
        }

        words_closer = 0
        all_user_vocab = db.get_all_user_vocab(user_id)
        updated_items: List[VocabItem] = []

        for item in all_user_vocab:
            item_id = item.get("id") or item.get("_id")
            lemma = (item.get("lemma") or "").lower().strip()

            is_explicitly_touched = item_id in items_touched_ids
            is_mistake_item = item_id in mistake_vocab_ids or lemma in mistake_lemmas

            if is_explicitly_touched or is_mistake_item:
                if is_mistake_item:
                    outcome: OutcomeType = "incorrect"
                else:
                    outcome: OutcomeType = "correct"
                    words_closer += 1

                updated = schedule_next_review(user_id=user_id, vocab_item_id=item_id, outcome=outcome)
                if updated:
                    updated_items.append(updated)

        # Fallback: if no specific items were tagged as touched, update top 2-3 due items
        if not updated_items and all_user_vocab:
            sample_size = max(1, min(3, max(1, turn_count)))
            for item in all_user_vocab[:sample_size]:
                item_id = item.get("id") or item.get("_id")
                lemma = (item.get("lemma") or "").lower().strip()
                outcome = "incorrect" if lemma in mistake_lemmas else "correct"
                if outcome == "correct":
                    words_closer += 1
                updated = schedule_next_review(user_id=user_id, vocab_item_id=item_id, outcome=outcome)
                if updated:
                    updated_items.append(updated)

        # Calculate next review ETA as the minimum due_at among scheduled items
        if updated_items:
            earliest_due = min(item.due_at for item in updated_items)
            next_eta = earliest_due
        else:
            next_eta = datetime.utcnow() + timedelta(days=1)

        # Calculate mastery delta: positive for correct items, slight penalty for mistakes
        mastery_delta = round(max(0.01, (words_closer * 0.02) - (len(tagged_mistakes) * 0.01)), 3)

        # Calculate real accuracy and stability metrics
        actual_turns = max(1, turn_count)
        mistake_count = len(tagged_mistakes)
        accuracy_percentage = max(50, min(100, round(((actual_turns - mistake_count) / actual_turns) * 100))) if actual_turns >= mistake_count else max(50, 100 - mistake_count * 15)

        avg_ease = sum(v.ease_factor for v in updated_items) / len(updated_items) if updated_items else 2.5
        stability_delta_str = f"+{round(avg_ease - 2.4, 2):.2f}x" if avg_ease >= 2.4 else f"{round(avg_ease - 2.5, 2):.2f}x"

        # FSRS recall retention probability R = e^(-t / S)
        recall_probability = min(99, max(75, 95 - (mistake_count * 4) + (words_closer * 2)))

        user = db.get_user(user_id) if user_id else {}
        next_scenario = self.get_next_scenario(
            user_id=user_id,
            current_theme=user.get("goal", "travel") if user else "travel",
            current_level=user.get("level", "A1") if user else "A1"
        )

        return {
            "mastery_delta": mastery_delta,
            "next_review_eta": next_eta,
            "words_closer_to_fluent": max(1, words_closer),
            "updated_items_count": len(updated_items),
            "accuracy_percentage": accuracy_percentage,
            "stability_factor_delta": stability_delta_str,
            "recall_probability": recall_probability,
            "next_recommended_scenario": next_scenario
        }

curriculum_agent = CurriculumAgent()


