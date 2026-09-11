"""
Verify Admin Endpoints & Newly Created Users in MongoDB
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_admin():
    print("=" * 60)
    print(" VERIFYING ADMIN OVERVIEW & USER LIST")
    print("=" * 60)

    # 1. Overview
    res = client.get("/users/admin/overview")
    assert res.status_code == 200, f"Failed: {res.text}"
    overview = res.json()
    print(f"[Admin Overview] Total Learners: {overview.get('total_learners_registered')}")
    print(f"[Admin Overview] Total Sessions: {overview.get('total_sessions_conducted')}")
    print(f"[Admin Overview] Total Mistakes: {overview.get('total_mistakes_classified')}")
    print(f"[Admin Overview] DB Connected:   {overview.get('database_connected')}")
    print(f"[Admin Overview] Active DB:      {overview.get('active_database')}")
    print(f"[Admin Overview] LLM Hierarchy:  {overview.get('configured_llm_hierarchy')}")

    # 2. List Learners
    res = client.get("/users?limit=50")
    assert res.status_code == 200
    data = res.json()
    learners = data.get("learners", [])
    print(f"\n[Learners List] Retrieved {len(learners)} registered learners:")
    for l in learners[:8]:
        print(f"  - {l.get('name'):<20} | ID: {l.get('user_id'):<10} | Level: {l.get('level'):<3} | Goal: {l.get('goal'):<8} | Sessions: {l.get('total_sessions')} | Mistakes: {l.get('total_mistakes')}")

    # 3. Inspect recent user full history
    if learners:
        recent_uid = learners[0].get("user_id") or learners[0].get("id")
        hist_res = client.get(f"/users/{recent_uid}/history")
        assert hist_res.status_code == 200
        hist = hist_res.json()
        print(f"\n[Detailed Dossier for {hist['user']['name']} ({recent_uid})]:")
        print(f"  Sessions count: {hist['statistics']['total_sessions']}")
        print(f"  Mistakes count: {hist['statistics']['total_mistakes_tagged']}")
        print(f"  Vocab count:    {hist['statistics']['vocab_items_tracked']}")
        if hist.get("sessions"):
            last_sess = hist["sessions"][0]
            print(f"  Latest session ID: {last_sess.get('id')}")
            print(f"  Turns recorded:    {len(last_sess.get('conversation_turns', []))}")
        if hist.get("mistake_tags"):
            print("  Sample tagged mistake:")
            m = hist["mistake_tags"][0]
            print(f"    - Type: {m.get('error_type')}, Severity: {m.get('severity')}")
            print(f"    - Turn: {m.get('example_turn')}")
            print(f"    - Correction: {m.get('correction')}")
            print(f"    - Explanation: {m.get('explanation')}")

    print("\n" + "=" * 60)
    print(" ALL ADMIN & RECORD AUDIT CHECKS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_admin()
