# Loop — Project Documentation
### Nerdy AI Hackathon Challenge (Prompt 02: Language Learning App)

This is the pre-build documentation set for **Loop**, an agent-orchestrated conversational language tutor. Read these in order the first time; after that, treat each as a standalone reference while you build.

| # | Doc | What it's for | Read this when... |
|---|---|---|---|
| 01 | [PRD.md](01-PRD.md) | Product Requirements — problem, users, scope, success metrics | You're deciding what to build vs. cut |
| 02 | [ARCHITECTURE.md](02-ARCHITECTURE.md) | System design — components, agent graph, request lifecycle | You're structuring the codebase or explaining the system to a judge |
| 03 | [DATA-MODELS.md](03-DATA-MODELS.md) | MongoDB collections, Pydantic schemas, vector store schema | You're writing DB models or the seed script |
| 04 | [API-SPEC.md](04-API-SPEC.md) | FastAPI endpoints + MCP tool definitions, request/response shapes | You're building a route or an agent tool |
| 05 | [AGENT-SPECS.md](05-AGENT-SPECS.md) | Each LangGraph agent's inputs, outputs, prompt template, model | You're writing an agent node |
| 06 | [SETUP-GUIDE.md](06-SETUP-GUIDE.md) | Repo structure, env vars, Docker, local run instructions | You're setting up the repo on day 1 |
| 07 | [BUILD-PLAN.md](07-BUILD-PLAN.md) | Day-by-day 3-week solo build plan with checkpoints | You need to know what to do today |
| 08 | [DEMO-CHECKLIST.md](08-DEMO-CHECKLIST.md) | Pre-submission test checklist + demo video script | You're in the last few days before Sep 18 |

## How to use this set

1. **Day 1:** read PRD → ARCHITECTURE → SETUP-GUIDE, then scaffold the repo per SETUP-GUIDE.
2. **Days 2–15:** build against BUILD-PLAN.md day by day; pull exact schemas from DATA-MODELS.md and AGENT-SPECS.md as you implement each piece — don't re-derive them, copy them.
3. **Last 3–4 days:** shift to DEMO-CHECKLIST.md — testing, recording, submission.

## Source of truth

If a later doc conflicts with an earlier one (e.g., BUILD-PLAN.md implies a different schema than DATA-MODELS.md), **DATA-MODELS.md and API-SPEC.md win** — they're the contracts the rest of the system is built against. Update them first, then propagate the change.

## Non-negotiable feature

Every doc in this set assumes one thing must ship no matter what gets cut: **the Curriculum Agent re-triggering a specific past mistake in a later conversation.** If you're behind schedule, protect this over everything else in BUILD-PLAN.md except the Placement → Conversation → Error-Analysis pipeline that feeds it.
