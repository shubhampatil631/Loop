# PRD — Loop
### Product Requirements Document

---

## 1. Vision

An adult self-learner should be able to open the app, talk in their target language for 10–15 minutes, and have the app quietly figure out what they're weak at and make sure it comes back around — without the learner ever picking a lesson.

## 2. Problem Statement

Existing apps (Duolingo, Babbel) are content-first: a fixed lesson tree with spaced repetition bolted on. Two failure modes:

- **Recognition ≠ production.** Learners recognize words in multiple-choice tiles but freeze producing them unprompted.
- **Generic scheduling.** Fixed review intervals ignore that forgetting curves differ per learner and per word.

## 3. Target Users

**Primary persona — "Maya," 29, relocating for work in 3 months.**
- Intermediate beginner (A2), learning Spanish.
- 10–15 min/day, usually on a commute.
- Wants to be able to *use* the language, not pass a vocab quiz.
- Frustrated that her current app (Duolingo) has her at a 200-day streak but she still can't order food confidently.

**Secondary persona — "Raj," 34, reconnecting with a heritage language.**
- Understands more than he can produce (passive bilingual).
- Wants conversation practice more than vocabulary drilling.

Both personas are served by the same core loop; the difference is starting vocabulary size, not app behavior.

## 4. Goals

- G1: Close the recognition→production gap — every due item must be *produced*, not just recognized, before being marked learned.
- G2: Personalize review timing per learner per word (not a fixed schedule).
- G3: Make review content feel like a conversation, not a flashcard deck.
- G4: Make the system's memory visible — the learner should be able to tell it remembers their specific mistakes.

## 5. Non-Goals (out of scope for hackathon submission)

- Multi-language support (ship one language pair: Spanish for English speakers)
- Social/leaderboard/cohort features
- Offline mode
- Full pronunciation/phoneme-level ASR scoring
- Payment, auth beyond a single demo user, multi-tenant infra

## 6. Success Metrics (how a judge — or you — evaluates this is working)

| Metric | Target for demo |
|---|---|
| Full daily loop completes end-to-end (placement → conversation → error tagging → schedule update) | 100% of demo runs, no manual intervention |
| A previously-tagged mistake gets naturally re-surfaced in a later session | At least once, on camera, in the demo video |
| Conversation Agent stays within the learner's level (no B2 grammar sprung on an A1 learner) | Verified manually across ≥5 test conversations |
| Session length | 10–15 min for a full loop, ~5 min for review-only mode |

## 7. Feature List (MoSCoW)

**Must have**
- Placement Agent: 3–4 turn conversation → rough CEFR level
- Conversation Partner Agent: roleplay conversation grounded to learner's level
- Error-Analysis Agent: tags mistakes silently per turn
- Curriculum/Scheduler Agent: FSRS-style scheduling + decides what to re-trigger
- Session summary screen (mastery delta, next review ETA)
- One seeded vocab bank (~50–100 items, Spanish, leveled A1–B1)

**Should have**
- Review/Recall Agent (lightweight 5-min mode using tagged mistakes)
- Weekly digest (strongest/weakest areas)
- "Words closer to fluent" counter

**Could have**
- Speak-back mode (ASR) instead of typed responses
- MCP-exposed agent tools (vs. direct function calls) — differentiator, but not required for the core loop to work

**Won't have (this cycle)**
- Multi-language, social features, offline mode, payments

## 8. User Stories

1. As a learner, I complete a 3-turn placement chat and the app starts me at the right difficulty, so I'm not bored or overwhelmed on day one.
2. As a learner, I have a short roleplay conversation and get corrected afterward in plain language, so I understand *why* something was wrong, not just that it was.
3. As a learner, a mistake I made three days ago comes back naturally in a new conversation, so I feel like the app actually knows me.
4. As a learner, I see a mastery score and next-review estimate after each session, so progress feels concrete, not just a streak number.

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| LLM generates grammar/vocab above the learner's level | RAG-ground the Conversation Agent against a leveled vocab bank (see ARCHITECTURE.md §4) |
| FSRS scheduling is over-engineered for 3-week solo build | Fall back to a simplified Leitner box (see AGENT-SPECS.md, Curriculum Agent) if time is short |
| Demo fails live because of API latency | Record the demo video from a rehearsed run, don't attempt fully live |
| Scope creep into multi-language / social features | This PRD's Non-Goals section is the cut line — check it before adding anything |
