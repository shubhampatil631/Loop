import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        
        # Header (on pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "Loop 🔄 — Autonomous Multi-Agent Language Learning Architecture")
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.5)
            self.line(54, 742, letter[0] - 54, 742)
            
        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 36, footer_text)
        self.drawString(54, 36, "Confidential — Nerdy AI Hackathon Project Submission Document")
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.5)
        self.line(54, 48, letter[0] - 54, 48)
        
        self.restoreState()

def build_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    primary_color = colors.HexColor("#1E3A8A")     # Deep Indigo / Blue
    accent_color = colors.HexColor("#2563EB")      # Vibrant Blue
    dark_neutral = colors.HexColor("#1F2937")      # Slate Dark
    light_bg = colors.HexColor("#F8FAFC")          # Off-white / light slate
    border_color = colors.HexColor("#E2E8F0")      # Light border
    highlight_color = colors.HexColor("#0D9488")   # Teal
    
    # Custom typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=12
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6
    )
    
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=accent_color,
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=dark_neutral,
        spaceAfter=6
    )
    
    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A")
    )
    
    meta_label = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=primary_color
    )
    
    meta_val = ParagraphStyle(
        'MetaVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=dark_neutral
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=dark_neutral
    )

    story = []

    # Title & Metadata Banner
    story.append(Paragraph("Loop 🔄 — Technical Architecture & Specification", title_style))
    story.append(Paragraph("Autonomous Multi-Agent Conversational Language Learning System with Spaced-Repetition Memory & Dynamic Error Retriggering", subtitle_style))
    
    # Metadata Card
    meta_data = [
        [
            Paragraph("<b>Author:</b> Shubham Patil", meta_val),
            Paragraph("<b>Email:</b> sup31patil@gmail.com", meta_val)
        ],
        [
            Paragraph("<b>Track:</b> Language Learning App", meta_val),
            Paragraph("<b>Code Repo:</b> <a href='https://github.com/shubhampatil631/Loop' color='#2563EB'>github.com/shubhampatil631/Loop</a>", meta_val)
        ],
        [
            Paragraph("<b>Demo Video:</b> <a href='https://youtu.be/0D93_SNgMBI' color='#2563EB'>youtu.be/0D93_SNgMBI</a>", meta_val),
            Paragraph("<b>Stack:</b> FastAPI, LangGraph, ChromaDB, Mongo, React+TS, MCP", meta_val)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[240, 264])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary & Problem Solved", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=accent_color, spaceBefore=2, spaceAfter=6))
    story.append(Paragraph(
        "Current digital language learning tools suffer from a clear dichotomy: static flashcard apps (e.g. Anki, Duolingo) rely on rote memorization without situational fluency, while open-ended LLM chatbots lack pedagogical memory, fail to track learner mistakes systematically, and hallucinate vocabulary outside the user's comprehension level.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Loop</b> bridges this gap by delivering an end-to-end, multi-agent educational pipeline. It conducts natural conversational roleplay strictly grounded in CEFR-appropriate vocabulary, silently classifies mistakes without interrupting dialogue flow, tracks individual memory decay via the FSRS algorithm, and dynamically re-injects past errors and overdue words into subsequent scenarios until mastery is proven.",
        body_style
    ))

    # Multi-Agent Architecture
    story.append(Spacer(1, 6))
    story.append(Paragraph("2. Multi-Agent Orchestration Engine (LangGraph)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=accent_color, spaceBefore=2, spaceAfter=6))
    story.append(Paragraph(
        "Loop's cognitive architecture is implemented as a stateful, compiled LangGraph graph comprising six specialized, modular agents communicating over a unified state machine:",
        body_style
    ))

    agent_data = [
        [
            Paragraph("Agent Name", table_header_style),
            Paragraph("Core Responsibility", table_header_style),
            Paragraph("Technical Implementation & Role", table_header_style)
        ],
        [
            Paragraph("<b>Placement Agent</b>", table_cell_style),
            Paragraph("CEFR Diagnostic Baseline", table_cell_style),
            Paragraph("Runs an adaptive 3-4 turn diagnostic interview to assess grammatical range, lexical breadth, and coherence to assign A1–B2 baseline levels.", table_cell_style)
        ],
        [
            Paragraph("<b>Conversation Partner</b>", table_cell_style),
            Paragraph("Immersive Grounded Roleplay", table_cell_style),
            Paragraph("Simulates rich real-world scenarios (boulangerie, airport, cafe). Dynamically queries ChromaDB RAG to constrain language strictly within CEFR ceiling.", table_cell_style)
        ],
        [
            Paragraph("<b>Error-Analysis Agent</b>", table_cell_style),
            Paragraph("Non-blocking Diagnostics", table_cell_style),
            Paragraph("Asynchronously parses learner inputs to detect and tag mistake taxonomy (conjugations, gender agreements, false friends, syntax) with corrections.", table_cell_style)
        ],
        [
            Paragraph("<b>Curriculum Scheduler</b>", table_cell_style),
            Paragraph("Spaced Repetition (FSRS)", table_cell_style),
            Paragraph("Computes stability, ease factors (EF), and review intervals. Dynamically re-queues lapsed vocabulary and past mistake tags for future scenario insertion.", table_cell_style)
        ],
        [
            Paragraph("<b>Review Recall Agent</b>", table_cell_style),
            Paragraph("Active Recall Verification", table_cell_style),
            Paragraph("Administers pre-session targeted flashcard drills, calculating active recall response accuracy and updating memory retention scores.", table_cell_style)
        ],
        [
            Paragraph("<b>Weekly Digest Agent</b>", table_cell_style),
            Paragraph("Longitudinal Mastery Analytics", table_cell_style),
            Paragraph("Aggregates historical session data into mastery percentages, retention curves, mistake heatmaps, and prescriptive weekly improvement plans.", table_cell_style)
        ]
    ]
    
    agent_table = Table(agent_data, colWidths=[110, 120, 274])
    agent_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(agent_table)

    # Key Technical Innovations
    story.append(Spacer(1, 8))
    story.append(Paragraph("3. Key Technical Innovations", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=accent_color, spaceBefore=2, spaceAfter=6))
    
    story.append(Paragraph("<b>A. Resilient 3-Tier LLM Cascading Fallback Engine</b>", h2_style))
    story.append(Paragraph(
        "To achieve zero-downtime reliability against API rate limits and network outages, Loop implements an automatic 3-tier cascade: <b>Tier 1: Google Gemini 1.5 Flash</b> (Cloud Primary) &rarr; <b>Tier 2: Groq LLaMA 3.3 70B Versatile</b> (Ultra-fast Cloud Backup) &rarr; <b>Tier 3: Local Ollama (Qwen 2.5 / LLaMA 3.2)</b> (Air-gapped on-device fallback).",
        body_style
    ))
    
    story.append(Paragraph("<b>B. FSRS Spaced-Repetition Memory Matrix & Dynamic Error Retriggering</b>", h2_style))
    story.append(Paragraph(
        "Unlike standard flashcards, Loop calculates dynamic memory decay curves using Free Spaced Repetition Scheduler (FSRS) formulas. When a user fails a grammatical concept or vocabulary item, the Curriculum Agent silently flags it as an active trigger. In future roleplay sessions, the Conversation Partner naturally engineers situational prompts forcing the learner to apply that specific concept again.",
        body_style
    ))

    story.append(Paragraph("<b>C. RAG-Grounded Vector Vocabulary (ChromaDB)</b>", h2_style))
    story.append(Paragraph(
        "Hallucination prevention is enforced by vectorizing 200+ curated CEFR vocabulary targets using <code>all-MiniLM-L6-v2</code> embeddings. Queries are filtered by CEFR hierarchy (A1 &sube; A2 &sube; B1 &sube; B2) and contextual scenario tags.",
        body_style
    ))

    story.append(Paragraph("<b>D. Standardized Model Context Protocol (MCP) Server</b>", h2_style))
    story.append(Paragraph(
        "Loop features a native MCP server exposing JSON-RPC 2.0 endpoints (<code>get_due_items</code>, <code>fetch_level_vocab</code>, <code>log_error_tag</code>, <code>schedule_next_review</code>, <code>get_learner_profile</code>) enabling external agent interoperability.",
        body_style
    ))

    # Architecture Diagram Flow (Visual Representation)
    story.append(Spacer(1, 8))
    story.append(Paragraph("4. End-to-End System Flow & Architecture Diagram", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=accent_color, spaceBefore=2, spaceAfter=6))
    
    diagram_box = [
        [Paragraph("<b>USER / LEARNER</b> (React 18 + TypeScript Glassmorphism UI)", table_header_style)],
        [Paragraph(
            "&nbsp;&nbsp;&nbsp;&nbsp;&darr; <i>REST APIs / WebSockets / MCP JSON-RPC</i><br/>"
            "<b>FASTAPI GATEWAY (Python 3.11 + Pydantic v2)</b><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&darr; <i>State Graph Dispatch</i><br/>"
            "<b>LANGGRAPH ORCHESTRATION ENGINE</b><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&bull; <b>Placement Node:</b> Evaluates CEFR level baseline (A1-B2)<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&bull; <b>Conversation Partner:</b> Roleplay &amp; Retriggering Prompt Construction<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&bull; <b>Error-Analysis Node (Async):</b> Mistake categorization &amp; scoring<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&bull; <b>Curriculum &amp; FSRS Scheduler:</b> Dynamic review scheduling &amp; decay tracking<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&darr; <i>Data &amp; Memory Persistence Layer</i><br/>"
            "<b>ChromaDB (Vector RAG) &nbsp;&bull;&nbsp; MongoDB Atlas (Learners &amp; FSRS Matrices) &nbsp;&bull;&nbsp; 3-Tier LLMs</b>",
            table_cell_style
        )]
    ]
    diag_table = Table(diagram_box, colWidths=[504])
    diag_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('BACKGROUND', (0, 1), (-1, -1), light_bg),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(diag_table)

    # Technical Specifications & Stack
    story.append(Spacer(1, 8))
    story.append(Paragraph("5. Full Technology Stack & Deliverables", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=accent_color, spaceBefore=2, spaceAfter=6))
    
    stack_data = [
        [Paragraph("Layer", table_header_style), Paragraph("Technologies & Frameworks", table_header_style)],
        [Paragraph("<b>Backend</b>", table_cell_style), Paragraph("Python 3.11, FastAPI, Uvicorn, LangGraph, LangChain, Pydantic v2", table_cell_style)],
        [Paragraph("<b>AI Models & Fallback</b>", table_cell_style), Paragraph("Google Gemini 1.5 Flash (Tier 1), Groq LLaMA 3.3 70B (Tier 2), Ollama Qwen/LLaMA (Tier 3)", table_cell_style)],
        [Paragraph("<b>Vector Store & Embeddings</b>", table_cell_style), Paragraph("ChromaDB persistent vector database with all-MiniLM-L6-v2 embeddings", table_cell_style)],
        [Paragraph("<b>Database</b>", table_cell_style), Paragraph("MongoDB Atlas & Local MongoDB instance via PyMongo", table_cell_style)],
        [Paragraph("<b>Frontend UI</b>", table_cell_style), Paragraph("React 18, TypeScript, Vite, Lucide Icons, Custom Glassmorphic Dark UI", table_cell_style)],
        [Paragraph("<b>Protocol & Integration</b>", table_cell_style), Paragraph("Model Context Protocol (MCP) Server & Standard JSON-RPC 2.0 Tools", table_cell_style)],
        [Paragraph("<b>DevOps & Packaging</b>", table_cell_style), Paragraph("Docker, Docker Compose, Pytest automation suites", table_cell_style)]
    ]
    stack_table = Table(stack_data, colWidths=[120, 384])
    stack_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(stack_table)

    # Future Roadmap
    story.append(Spacer(1, 8))
    story.append(Paragraph("6. Future Roadmap", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=accent_color, spaceBefore=2, spaceAfter=6))
    story.append(Paragraph("&bull; <b>Full-Duplex Voice & Pronunciation:</b> Streaming WebRTC speech-to-text with phoneme scoring.", bullet_style))
    story.append(Paragraph("&bull; <b>Multimodal Contextual Stimuli:</b> Visual roleplay elements (menus, street signs, tickets).", bullet_style))
    story.append(Paragraph("&bull; <b>Multi-Language Expansion:</b> Grammar taxonomies for Japanese, German, Mandarin, and Spanish.", bullet_style))
    story.append(Paragraph("&bull; <b>Edge / Mobile Deployment:</b> React Native client with local SLM execution on Apple Silicon / Snapdragon.", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)

if __name__ == "__main__":
    out_pdf = os.path.abspath("Loop_System_Architecture_and_Specification.pdf")
    build_pdf(out_pdf)
    print(f"Successfully generated PDF at: {out_pdf}")
