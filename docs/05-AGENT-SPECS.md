# Agent Specifications — Loop

Each agent below is a LangGraph node. Format: purpose, input/output slice of `LoopState`, model choice, prompt template, and edge cases to handle.

---

## 1. Placement Agent

**Purpose:** estimate a rough CEFR level (A1/A2/B1) from a 3–4 turn conversation, run once per new user.

**Reads:** `user_id`, incoming `learner_text`
**Writes:** `level`, appends to `conversation_history`

**Model:** Gemini Pro (better instruction-following for a structured assessment task than Groq's faster/cheaper models)

**System prompt (template):**
```
You are a language placement assessor for {target_language}. Hold a brief,
friendly 3-4 exchange conversation with the learner in {target_language},
mixed with English if they seem to struggle. After each learner reply,
silently estimate their CEFR level (A1/A2/B1) based on: vocabulary range,
grammatical accuracy, and sentence complexity. Do not tell the learner
their level mid-conversation. After 3-4 exchanges, output ONLY:
{"level": "A1|A2|B1", "notes": "one sentence justification"}
```

**Edge case:** if the learner responds entirely in English (can't produce any target-language text), default to A1 and note it — don't loop indefinitely trying to elicit target-language output.

---

## 2. Conversation Partner Agent

**Purpose:** hold a natural roleplay conversation (barista, coworker, friend) calibrated to the learner's level, weaving in 1–2 due/mistake items per session.

**Reads:** `level`, `due_items`, `conversation_history`, `tagged_mistakes` (from prior sessions, passed in by Curriculum Agent)
**Writes:** appends to `conversation_history`, increments `turn_count`

**Model:** Gemini Pro primary, Groq fallback on timeout/rate-limit (see API-SPEC.md §4)

**Tool call before each generation:** `fetch_level_vocab(level, theme, k=5)` — retrieved sentences go into the prompt context so the model has concrete, in-level examples to anchor to, not just an instruction to "stay simple."

**System prompt (template):**
```
You are roleplaying as {persona} in a {theme}-themed scenario, speaking
{target_language} with a learner at CEFR level {level}. Use ONLY vocabulary
and grammar at or below {level} — here are example in-level sentences to
anchor your style: {retrieved_vocab_examples}.

Naturally work in these words if a natural opening arises (don't force it
into every turn): {due_items}.
If a natural opening arises, try to prompt the learner to use one of these
words/structures they've previously struggled with: {tagged_mistakes}.

Keep each of your turns to 1-2 short sentences. Stay in character as {persona}.
```

**Edge case:** if the learner's reply is incomprehensible or off-topic, respond in-character with a natural clarifying question rather than breaking character to correct them — corrections happen via the Error-Analysis Agent, not live in the conversation.

---

## 3. Error-Analysis Agent

**Purpose:** silently classify mistakes in each learner turn; does not interrupt the conversation.

**Reads:** the most recent learner turn from `conversation_history`, `level`
**Writes:** appends to `tagged_mistakes`, calls `log_error_tag` MCP tool

**Model:** Gemini Pro (classification benefits from stronger reasoning; this call is not latency-sensitive since it runs async after the reply is already sent to the learner)

**System prompt (template):**
```
You are a language error classifier for {target_language}. Given one
learner turn, identify errors ONLY from this set: gender_agreement,
conjugation, word_order, false_friend, other. For each error found,
output: {"vocab_item": "the lemma involved, if any", "error_type": "...",
"severity": "low|medium|high", "correction": "the corrected form",
"explanation": "one plain-language sentence"}.
If there are no errors, output an empty list. Do not flag stylistic
choices or minor disfluencies as errors — only grammatical/lexical mistakes.
```

**Edge case:** if the learner's turn is too short/ambiguous to classify confidently (e.g., a single word), skip tagging rather than guessing — a false-positive mistake tag is worse than a missed one, since it pollutes future re-triggering.

---

## 4. Curriculum / Scheduler Agent

**Purpose:** own the spaced-repetition state; decide what's due, update it after each session, and decide which past mistakes should be re-triggered in the next conversation.

**Reads:** `user_id` (via `get_due_items`, `get_learner_profile`), `tagged_mistakes` from this session
**Writes:** `due_items` (at session start), persists FSRS updates via `schedule_next_review`

**Model:** none required for the core scheduling logic — this is deterministic code (FSRS/Leitner math), not an LLM call. An LLM call is only used for the optional weekly digest (see §5 below).

**Scheduling rule (simplified FSRS/SM-2 — use this if full FSRS is too much for the timeline):**
```python
def update_item(item: VocabItem, outcome: str) -> VocabItem:
    if outcome == "correct":
        item.ease_factor = min(item.ease_factor + 0.1, 3.0)
        item.interval_days = round(item.interval_days * item.ease_factor)
    elif outcome == "hesitated":
        item.interval_days = max(1, round(item.interval_days * 0.7))
    else:  # incorrect
        item.ease_factor = max(item.ease_factor - 0.3, 1.3)
        item.interval_days = 1
    item.due_at = now() + timedelta(days=item.interval_days)
    item.reps += 1
    return item
```

**Re-trigger selection logic:** when building the prompt context for the Conversation Agent's next session, prefer mistake tags where `retriggered_count == 0` and `created_at` is 2–5 days old (long enough that natural forgetting has started, not so long it's stale) — this is what produces the "it remembers me" moment. Increment `retriggered_count` once it's woven into a conversation.

---

## 5. Review/Recall Agent (Should-have)

**Purpose:** a lighter 5-minute mode — quick-fire prompts pulled directly from `due_items` and `tagged_mistakes`, no roleplay framing.

**Reads:** `due_items`
**Writes:** same outcome logging as Conversation Agent, feeds into `schedule_next_review`

**Model:** Groq (this mode is explicitly optimized for speed — quick-fire prompts, low latency matters more than conversational nuance)

**System prompt (template):**
```
Generate one short recall prompt in {target_language} using the word
"{due_item}". Format: a fill-in-the-blank or a one-line translation
prompt. Keep it under 10 words. Do not explain, just output the prompt.
```

---

## 6. Weekly Digest (optional, LLM-assisted summary — not a LangGraph node, a scheduled job)

**Trigger:** once per week per user (or on-demand for the demo).
**Reads:** last 7 days of `sessions` + `mistake_tags`.
**Model:** Groq (cheap summarization task).
**Prompt:** "Given this learner's mistake tags and mastery deltas from the past week, write a 2-sentence summary: one strength, one focus area for next week."
