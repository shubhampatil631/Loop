# Build Plan — Loop
### Solo, 3-week window (submissions close Sep 18, 2026)

Each day has one primary deliverable. If you finish early, pull from the next day rather than gold-plating what you just built.

---

## Week 1 — Foundation (data + one agent working end to end)

**Day 1 — Repo + infra**
- Scaffold repo per SETUP-GUIDE.md §1
- Docker Compose up with empty FastAPI + Mongo + Chroma running
- ✅ Checkpoint: `GET /health` returns 200 through Docker

**Day 2 — Data layer**
- Implement Mongo models (`users`, `vocab_items`, `mistake_tags`) per DATA-MODELS.md
- Write and run `seed_vocab_bank.py` with ~50 Spanish A1 items
- ✅ Checkpoint: can query `vocab_bank` in Chroma and get back sensible nearest-neighbor sentences

**Day 3 — Placement Agent**
- Implement `placement.py` per AGENT-SPECS.md §1
- Wire `/onboarding/start` and `/onboarding/placement/turn`
- ✅ Checkpoint: a 3-turn scripted conversation returns a plausible CEFR level

**Day 4 — Conversation Partner Agent (no RAG yet)**
- Implement `conversation.py` with a hardcoded persona and theme, Gemini call, no vocab grounding yet
- Wire `/session/start`, `/session/turn`
- ✅ Checkpoint: can hold a 3-turn roleplay conversation in Spanish

**Day 5 — RAG grounding**
- Wire `fetch_level_vocab` into the Conversation Agent's prompt (ARCHITECTURE.md §4)
- Manually test: does the agent stay at A1 vocabulary for an A1 learner?
- ✅ Checkpoint: run the same conversation prompt at A1 vs B1 level, confirm visibly different vocabulary complexity

**Days 6–7 — Buffer / catch-up**
- Use for whichever of Days 1–5 ran over. Do not start Week 2 material early even if ahead — instead, write tests for what exists so far.

---

## Week 2 — The agent loop that produces the "wow" moment

**Day 8 — Error-Analysis Agent**
- Implement `error_analysis.py` per AGENT-SPECS.md §3
- Runs async after each learner turn, writes to `mistake_tags`
- ✅ Checkpoint: intentionally make a gender-agreement mistake in a test conversation, confirm it gets tagged correctly

**Day 9 — Curriculum/Scheduler Agent (scheduling half)**
- Implement `update_item()` FSRS-lite logic per AGENT-SPECS.md §4
- Wire `schedule_next_review` MCP tool
- ✅ Checkpoint: after a session, `due_at` on touched items visibly changes based on outcome

**Day 10 — Curriculum/Scheduler Agent (re-trigger half)**
- Implement re-trigger selection logic (mistake tags 2–5 days old, `retriggered_count == 0`)
- Wire this into the Conversation Agent's prompt context for the *next* session
- ✅ Checkpoint: this is the core bet of the whole project — do not move on until you've verified it works

**Day 11 — Full LangGraph wiring**
- Assemble all nodes into the actual state graph per ARCHITECTURE.md §3
- Replace the manually-chained calls from Days 3–10 with the graph
- ✅ Checkpoint: `POST /session/start` → several `/session/turn` calls → `/session/end` runs the full pipeline with no manual glue code

**Day 12 — THE non-negotiable end-to-end test**
- Run two full sessions, days apart (simulate by manually backdating `mistake_tags.created_at` if needed)
- Confirm a mistake from session 1 gets naturally woven into session 2's conversation
- ✅ Checkpoint: this is the moment your demo video is built around — do not proceed until it works reliably, twice in a row

**Days 13–14 — Buffer / MCP wrapper**
- If on schedule: wrap the tools in an actual MCP server (was direct function calls until now) per API-SPEC.md §3
- If behind schedule: skip MCP, keep direct function calls — it's a "should have," the re-trigger loop is the "must have"

---

## Week 3 — Frontend, polish, demo

**Day 15 — Frontend: onboarding + daily loop screens**
- `Onboarding.tsx`, `DailyLoop.tsx` wired to the real API
- ✅ Checkpoint: can complete a full loop through the UI, not just curl/Postman

**Day 16 — Frontend: session summary + progress**
- `SessionSummary.tsx`, `Progress.tsx`
- ✅ Checkpoint: mastery delta and "words closer to fluent" counter visibly update after a session

**Day 17 — Review/Recall Agent (should-have)**
- Only if Days 1–16 are solid. Otherwise skip and spend the day hardening what exists.

**Day 18 — Bug pass + seed data polish**
- Run through DEMO-CHECKLIST.md test scenarios
- Fix anything that would visibly break on camera

**Day 19 — Record the demo video**
- Follow the script in DEMO-CHECKLIST.md / solution doc §8
- Record 2–3 takes, pick the cleanest

**Day 20 — Write submission + deploy demo link**
- Deploy backend + frontend (Hugging Face Spaces / Render / Vercel)
- Write the "what you built, how, what's next" submission text — reuse language from PRD.md §1, §9

**Day 21 — Buffer**
- Final smoke test on the deployed link, submit

---

## What to cut, in order, if you fall behind

1. Review/Recall Agent (should-have, cut first)
2. MCP wrapper (keep direct function calls instead)
3. Weekly digest
4. Speak-back/ASR (were never in scope for MVP anyway)
5. **Never cut:** Placement → Conversation → Error-Analysis → Curriculum re-trigger loop. If this doesn't work, there is no demo.
