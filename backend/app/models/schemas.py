from pydantic import BaseModel, Field, AliasChoices
from datetime import datetime
from typing import Literal, Optional, List, Any, Dict

CEFRLevel = Literal["A1", "A2", "B1", "B2"]
ErrorType = Literal["gender_agreement", "conjugation", "word_order", "false_friend", "other"]
Severity = Literal["low", "medium", "high"]
SessionMode = Literal["placement", "daily_loop", "review_only"]
OutcomeType = Literal["correct", "incorrect", "hesitated"]

class User(BaseModel):
    id: str = Field(default="", validation_alias=AliasChoices("id", "_id"))
    name: str
    target_language: str = "es"
    goal: str = "travel"
    level: CEFRLevel = "A1"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_session_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "json_encoders": {datetime: lambda v: v.isoformat()}
    }

class VocabItem(BaseModel):
    id: str = Field(default="", validation_alias=AliasChoices("id", "_id"))
    user_id: Optional[str] = None
    lemma: str
    cefr_level: CEFRLevel = "A1"
    theme: str = "travel"
    ease_factor: float = 2.5
    interval_days: int = 1
    due_at: datetime = Field(default_factory=datetime.utcnow)
    reps: int = 0
    last_outcome: Optional[OutcomeType] = None
    last_reviewed_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "json_encoders": {datetime: lambda v: v.isoformat()}
    }

class MistakeTag(BaseModel):
    id: str = Field(default="", validation_alias=AliasChoices("id", "_id"))
    user_id: Optional[str] = None
    vocab_item_id: Optional[str] = None
    error_type: ErrorType = "other"
    severity: Severity = "medium"
    example_turn: str = ""
    correction: Optional[str] = None
    explanation: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    retriggered_count: int = 0

    model_config = {
        "populate_by_name": True,
        "json_encoders": {datetime: lambda v: v.isoformat()}
    }


class ConversationTurn(BaseModel):
    role: Literal["agent", "learner"]
    text: str
    ts: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat()}
    }

class NextScenario(BaseModel):
    title: str
    description: str
    level: str = "A1"

class SessionSummary(BaseModel):
    session_id: str
    mastery_delta: float
    next_review_eta: datetime
    mistakes_this_session: List[MistakeTag] = []
    words_closer_to_fluent: int = 0
    accuracy_percentage: int = 100
    stability_factor_delta: str = "+0.10x"
    recall_probability: int = 92
    next_recommended_scenario: Optional[NextScenario] = None

    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat()}
    }

# API Request/Response Models

class OnboardingStartRequest(BaseModel):
    name: str
    target_language: str = "es"
    goal: str = "travel"

class OnboardingStartResponse(BaseModel):
    user_id: str
    placement_session_id: str
    greeting: Optional[str] = None

class PlacementTurnRequest(BaseModel):
    placement_session_id: str
    learner_text: str

class PlacementTurnResponse(BaseModel):
    agent_text: str
    placement_complete: bool = False
    level: Optional[CEFRLevel] = None
    notes: Optional[str] = None

class SessionStartRequest(BaseModel):
    user_id: str
    mode: SessionMode = "daily_loop"

class SessionStartResponse(BaseModel):
    session_id: str
    agent_text: str
    scenario: Optional[str] = None

class SessionTurnRequest(BaseModel):
    session_id: str
    learner_text: str

class SessionTurnResponse(BaseModel):
    agent_text: str
    turn_count: int
    session_complete: bool = False

class ReviewDueResponse(BaseModel):
    due_items: List[VocabItem]
    count: int

class ProgressResponse(BaseModel):
    mastery_score: float
    words_graduated: int
    words_in_progress: int
    recent_mistakes: List[Dict[str, Any]]
    streak_days: int
    total_sessions: int = 0
    total_mistakes: int = 0
    accuracy_rate: int = 100
    retention_rate: int = 92

