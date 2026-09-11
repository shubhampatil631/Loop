# Demo & Submission Checklist — Loop

---

## 1. Functional Test Scenarios (run all before recording)

| # | Scenario | Expected result |
|---|---|---|
| 1 | New user completes placement | Gets a level (A1/A2/B1) after 3–4 turns, no crash |
| 2 | New user's first daily loop | Conversation stays within their placed level (spot-check vocab manually) |
| 3 | Learner makes a deliberate gender-agreement mistake | Mistake appears in session summary with correct `error_type` |
| 4 | Same learner, second session 2+ days later | The earlier mistake is naturally woven into the new conversation |
| 5 | Learner answers correctly on a due item | `interval_days` increases, `due_at` moves further out |
| 6 | Learner answers incorrectly | `interval_days` resets to 1, `ease_factor` decreases |
| 7 | Progress view | Mastery score, words graduated, streak all render without errors |
| 8 | LLM provider fails (simulate by revoking one API key temporarily) | Fails over to the other provider rather than crashing the session |
| 9 | Full loop via the deployed link (not localhost) | Same behavior as local — no env var or CORS issues in production |

Don't record the demo until #4 (the re-trigger) passes reliably — it's the entire thesis of the project.

## 2. Demo Video Script (2–3 min, maps to solution doc §8)

**0:00–0:15 — Pitch**
> "Loop is an agent-based language tutor that learns your weaknesses from real conversation, not quizzes."

**0:15–0:55 — Live walkthrough**
- Show onboarding → placement → first daily loop conversation
- Narrate: point out that the vocabulary stays appropriate to the placed level

**0:55–1:35 — Behind the scenes**
- Cut to a terminal/log view showing the LangGraph trace: which agent fired, the Error-Analysis Agent tagging a mistake in real time
- Narrate: explain in one sentence what each visible agent is doing

**1:35–2:15 — The wow moment**
- Show a second session (can be pre-recorded from a day or two earlier)
- The Curriculum Agent re-triggers the earlier tagged mistake inside the new conversation
- Narrate: "this is the part no flashcard app does — it remembers exactly what I got wrong and brings it back."

**2:15–2:45 — Architecture + close**
- Hold the architecture diagram (ARCHITECTURE.md §1) on screen for a few seconds
- One line on what's next: "next: more languages, speech input, a peer-practice mode"

## 3. Submission Form Checklist

- [ ] "What did you build?" — pull from PRD.md §1 (vision) + §9 non-goals as the "what's next"
- [ ] Prompt selected: **Language Learning App**
- [ ] Demo video link (YouTube/Loom/Drive, unlisted is fine)
- [ ] Code repo link (public or judge-accessible)
- [ ] Live demo link (deployed backend + frontend)
- [ ] Confirm the deployed link actually works from a fresh/incognito browser session before submitting — test scenario #9 above, one more time, last thing before you submit

## 4. Judge Q&A Prep (things a Nerdy engineer is likely to ask)

| Likely question | Your answer, in one line |
|---|---|
| "Why LangGraph and not just one big prompt?" | Each agent has one narrow, inspectable job — the orchestration is what makes this defensible against "just an LLM wrapper." |
| "Why MCP for the tools?" | Decouples the tools from the orchestration framework — you could swap LangGraph for CrewAI without touching the tools. |
| "How do you keep the model from drifting above the learner's level?" | RAG-grounded generation — retrieval is filtered to `cefr_level <= learner.level` before the Conversation Agent generates anything. |
| "What would you build next?" | Multi-language support, ASR/speak-back, a peer-practice mode — see PRD.md §9 and solution doc §7. |
| "What was hardest to get right?" | The re-trigger timing — surfacing a mistake too soon feels repetitive, too late feels like it forgot. Landed on 2–5 days as the window. |
