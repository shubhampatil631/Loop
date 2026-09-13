# Loop: 2.5-Minute Demo Video Script

A streamlined, high-impact script designed for a crisp 2.5-to-3 minute video demonstration covering all core agents, the re-trigger "wow" moment, the live frontend audit records, and system architecture.

---

## Video Timeline

| Timestamp | Scene | Key Feature / Agent |
|---|---|---|
| **0:00 – 0:15** | **The Hook & Problem** | Production gap vs. traditional flashcard drills |
| **0:15 – 0:45** | **Diagnostic Onboarding** | Placement Agent (3-turn conversational CEFR calibration) |
| **0:45 – 1:20** | **Session 1: Live Roleplay** | Conversation Partner (RAG-grounded) + Silent Error-Analysis Agent |
| **1:20 – 1:50** | **Session 2: The "Wow" Moment** | Curriculum Scheduler (FSRS re-trigger woven into natural greeting) |
| **1:50 – 2:15** | **Progress & Active Recall** | Spaced Repetition Ledger, AI Digest, 5-Min Active Recall Mode |
| **2:15 – 2:40** | **Learners & Audit Records** | Live Platform Records, Turn-by-Turn Transcripts & Learner Dossiers |
| **2:40 – 3:00** | **Architecture & Closing** | LangGraph, MCP protocol, Multi-Provider LLM Fallbacks |

---

## Scene-by-Scene Script

### Scene 1: The Problem (0:00 – 0:15)
* **Screen:** Landing page (`http://localhost:3000`).
* **Narration:**
  > *"Traditional language apps test recognition through multiple-choice drills, not real speech production. You can hold a 200-day streak and still freeze ordering coffee in Madrid. **Loop** fixes this by diagnosing grammatical weaknesses from live conversations and naturally cycling them back until mastered."*

---

### Scene 2: Track Selection & Diagnostic Placement (0:15 – 0:45)
* **Screen Display:** Onboarding Setup & Diagnostic Assessment view (`http://localhost:3000`).
* **Visual Actions:**
  1. **Showcase 3 Learning Tracks:**
     - Point cursor across the 3 specialized tracks:
       * ✈️ **Travel & Dining** *(Most Popular)*: Food ordering, transit, hotels, and spontaneous travel.
       * 💼 **Career & Workplace** *(Professional)*: Meetings, formal emails, negotiations, and workplace terminology.
       * ☕ **Culture & Daily Life** *(Conversational)*: Everyday socialization, native idioms, and cultural fluency.
  2. **Profile & Track Selection:**
     - In **Learner Name / Handle**, type: `Ray`.
     - Click & select track: **Travel & Dining**.
     - Set daily goal (e.g. `15 min/day`) and click **"Begin 3-Turn Diagnostic Assessment"**.
  3. **Turn 1 (Greeting & Motivation):**
     - **Placement Agent:** *"¡Hola Ray! Bienvenido a Loop. Dime, ¿cómo te llamas y por qué te gustaría aprender español?"*
     - **User inputs:** *"Hola, me llamo Ray y quiero aprender español para viajar a España."*
     - UI displays badge: `Turn 1 of 3 Complete`.
  4. **Turn 2 (Habits & Vocabulary Range):**
     - **Placement Agent:** *"¡Qué bien! ¿Qué actividades te gusta hacer cuando viajas o sales a comer?"*
     - **User inputs:** *"Me gusta visitar museos, caminar por el centro y comer comida típica."*
     - UI displays badge: `Turn 2 of 3 Complete`.
  5. **Turn 3 (Past Experience & Grammar Check):**
     - **Placement Agent:** *"Excelente. ¿Has viajado a algún país hispanohablante antes? Cuéntame una experiencia."*
     - **User inputs:** *"He viajado a México el año pasado con mi familia."*
     - UI triggers calibration animation: `Analyzing syntax complexity, lexical variety & tense usage...`
  6. **Diagnostic Results Card:**
     - **Assigned Level:** `CEFR Level: A1 (Breakthrough / Elementary)`
     - **Communicative Baseline:** `Present & Periphrastic Future (Calibrated)`
     - **Selected Track:** `Travel & Dining Fundamentals`
     - Click **"Enter Daily Loop Studio"** button to begin practice.
* **Spoken Narration:**
  > *"When onboarding, learners choose from three tailored conversational tracks: **Travel & Dining**, **Career & Workplace**, or **Culture & Daily Life**.*  
  > *Ray selects Travel & Dining, and instead of taking a rigid multiple-choice test, he chats with our **Placement Agent** for just three quick turns.*  
  > *In under 30 seconds, the agent evaluates his syntactic complexity, vocabulary breadth, and communicative competence, automatically calibrating his profile to CEFR Level A1. This baseline immediately configures our RAG retrieval bank and difficulty ceiling for his daily loops."*

---

### Scene 3: Session 1 — Roleplay & Silent Error Tagging (0:45 – 1:20)
* **Screen:** Daily Loop Studio (`Cafeteria Scenario`).
* **Actions:**
  1. Partner: *"¡Hola! ¿Qué te gustaría pedir hoy?"*
  2. **Deliberate Error:** User inputs: *"Hola, quiero un café fría y la problema es que no tengo dinero."*
  3. Partner responds in character without breaking immersion: *"El café frío cuesta dos euros. ¿Tienes tarjeta?"*
  4. Finish Loop $\rightarrow$ Session Summary shows tagged errors: `el problema` and `café frío`.
* **Narration:**
  > *"In his first roleplay, our RAG-grounded **Conversation Partner** maintains level-appropriate dialogue. When Ray makes a gender slip—'café fría'—the partner stays in character without interrupting, while our async **Error-Analysis Agent** silently tags the mistake into MongoDB."*

---

### Scene 4: Session 2 — The "Wow" Re-Trigger (1:20 – 1:50)
* **Screen:** Starting Session 2 (simulating next review interval).
* **Actions:**
  1. Partner dynamically opens with the tagged target item:  
     *"¡Hola Ray! ¿Te preparo hoy un café frío o prefieres un té?"*
  2. User produces correct form unprompted: *"Hola, hoy sí quiero un café frío, por favor."*
  3. Show updated summary: Mastery delta increases (`+0.05`) and retention interval extends.
* **Narration:**
  > *"Here is the core breakthrough: days later, our **Curriculum Scheduler Agent** detects that Ray's mistake entered its forgetting curve window. The partner weaves 'café frío' directly into the greeting. Ray naturally produces the correct phrase, boosting his spaced repetition score without ever touching a flashcard."*

---

### Scene 5: Progress Matrix & Active Recall Mode (1:50 – 2:15)
* **Screen Display:** Progress Dashboard (`http://localhost:3000`).
* **Visual Actions:**
  1. Click **Progress** tab $\rightarrow$ showcase the **Cognitive Fluency Matrix** (Proficiency score, Graduated lexemes, and FSRS active queue).
  2. Point to the **Mistake Memory Ledger**, highlighting the tagged slip (`café fría / el problema`) with its updated status: `✓ Re-tested in Session`.
  3. Click **"Generate AI Digest"** $\rightarrow$ shows instant personalized coaching (Strengths & Priority Focus Area).
  4. Click **"Quick Review Session"** $\rightarrow$ shows rapid 5-minute micro-drill generated by the **Review/Recall Agent**.
* **Spoken Narration:**
  > *"On the Progress dashboard, learners get complete visibility into their cognitive memory engine—tracking graduated vocabulary, retention scores, and the persistent Mistake Ledger.*  
  > *With one click, the **Weekly AI Digest** generates personalized coaching insights, while our **Review Agent** offers a rapid 5-minute active recall mode for quick practice on the go."*

---

### Scene 6: Learners Directory & Live Audit Records (2:15 – 2:40)
* **Screen Display:** Learners & Records View (`http://localhost:3000` $\rightarrow$ click **"Learners & Records"** in the top navigation bar).
* **Visual Actions:**
  1. **Platform-Wide Metrics:**
     - Point to top aggregate counter stats: Total registered learners, transcribed dialogue turns, tagged grammatical slips, and active memory items.
  2. **Multi-User Directory & Filtering:**
     - Showcase multi-user persistence: Filter by Track (e.g. *Travel & Dining*) or search for `Ray`.
     - Click **"View Full Dossier"** on Ray's profile card.
  3. **Deep Audit Inspection Modal:**
     - **Session Transcripts:** Expand Session 1 & 2 to reveal full turn-by-turn dialogue timestamps and verbatim conversation logs.
     - **Mistake Ledger:** Show classified mistake entries (`café fría`, `el problema`) with error classification, explanation, confidence score, and status (`re-tested`).
     - **Vocab Bank:** Inspect active lexemes tracked across sessions.
  4. **Multi-Profile Switching:**
     - Point to the **"Launch Studio as Ray"** button demonstrating seamless instant learner switching across profiles.
* **Spoken Narration:**
  > *"For complete transparency, Loop includes a live **Learners & Audit Records** dashboard.*  
  > *Here, educators and evaluators can inspect every learner across the platform. Opening Ray's profile reveals his complete turn-by-turn conversational transcripts, the exact timestamped mistake classifications, and active spaced repetition queues stored in MongoDB.*  
  > *You can even switch profiles with a single click to experience the platform from any learner's vantage point."*

---

### Scene 7: Architecture & Closing (2:40 – 3:00)
* **Screen:** Architecture slide or terminal showing agent graph execution.
* **Narration:**
  > *"Under the hood, Loop is built with **LangGraph** orchestrating 5 specialized agents, standardized via an **MCP Server**, with fallbacks across Groq, Gemini, and Ollama. Loop turns language learning into natural conversation that remembers you."*

---

## Quick Checklist
- [ ] Backend (`uvicorn app.main:app --port 8000`) & Frontend (`npm run dev`) running.
- [ ] ChromaDB seeded with CEFR bank & MongoDB Atlas connected.
- [ ] Screen resolution set to 1080p (1920x1080).
