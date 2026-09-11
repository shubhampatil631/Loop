import sys
import io
from pathlib import Path

# UTF-8 on Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.db import db
from datetime import datetime

def view_learners():
    print("==================================================================")
    print("           LOOP PLATFORM: REGISTERED LEARNERS & AUDIT             ")
    print("==================================================================")
    print(f"MongoDB Connected: {db.is_connected} (DB: {db.db.name if db.db is not None else 'In-Memory'})")

    users = db.get_all_users(limit=50)
    print(f"\nTotal Learners Found: {len(users)}\n")
    if not users:
        print("No learners found in database yet.")
        return

    print(f"{'ID':<10} | {'Name':<18} | {'Level':<6} | {'Goal':<10} | {'Sessions':<9} | {'Mistakes':<9} | {'Created'}")
    print("-" * 88)
    for u in users:
        uid = u.get("id", "")
        name = (u.get("name") or "Anonymous")[:18]
        lvl = u.get("level", "A1")
        goal = u.get("goal", "travel")
        sess_count = u.get("total_sessions", 0)
        mistakes = u.get("total_mistakes", 0)
        created = u.get("created_at")
        created_str = created.strftime("%Y-%m-%d %H:%M") if isinstance(created, datetime) else str(created)[:16]
        print(f"{uid:<10} | {name:<18} | {lvl:<6} | {goal:<10} | {sess_count:<9} | {mistakes:<9} | {created_str}")

    print("\n------------------------------------------------------------------")
    print("To view full session transcripts and mistake breakdown for any user:")
    print("API: GET http://localhost:8000/users/<user_id>/history")
    print("==================================================================")

if __name__ == "__main__":
    view_learners()
