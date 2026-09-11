import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.models.db import db

print("Checking DB connection...")
t0 = time.time()
users = list(db.db.users.find().sort("created_at", -1).limit(50))
t1 = time.time()
print(f"Users query: {t1-t0:.3f}s ({len(users)} users)")

uids = [str(d["_id"]) for d in users]

t0 = time.time()
sess_agg = list(db.db.sessions.aggregate([
    {"$match": {"user_id": {"$in": uids}}},
    {"$group": {"_id": "$user_id", "count": {"$sum": 1}}}
]))
t1 = time.time()
print(f"Sessions aggregate: {t1-t0:.3f}s ({len(sess_agg)} results)")

t0 = time.time()
mistake_agg = list(db.db.mistake_tags.aggregate([
    {"$match": {"user_id": {"$in": uids}}},
    {"$group": {"_id": "$user_id", "count": {"$sum": 1}}}
]))
t1 = time.time()
print(f"Mistakes aggregate: {t1-t0:.3f}s ({len(mistake_agg)} results)")
