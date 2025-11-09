from enum import Enum
from typing import Union

from pydantic import BaseModel, Field, field_validator


class GoalStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


class Goal(BaseModel):
    description: str
    status: GoalStatus = GoalStatus.NOT_STARTED
    confidence: int = Field(default=0)

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: int) -> int:
        return max(0, min(100, v))


class Fact(BaseModel):
    topic: str
    claim: str
    source: str = "user"
    timestamp: Union[str, None] = None
    confidence: str = Field(default="certain")  # "certain" or "uncertain"


class Message(BaseModel):
    role: str  # "assistant" or "user"
    content: str
    timestamp: str


class Answer(BaseModel):
    answer: str
    reasoning: str


class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETE = "complete"


class Actor(BaseModel):
    """Represents a person involved in the drama incident."""
    name: str
    relationships: list[str] = Field(default_factory=list)
    emotional_state: list[str] = Field(default_factory=list)
    role: str = ""  # Optional descriptive role like "the friend", "coworker", etc.


class Conflict(BaseModel):
    """Represents the conflicts in the drama incident."""
    primary: str
    secondary: list[str] = Field(default_factory=list)


class GeneralDetails(BaseModel):
    """General contextual details about the drama incident."""
    timeline_markers: list[str] = Field(default_factory=list)
    location_context: list[str] = Field(default_factory=list)
    communication_history: list[str] = Field(default_factory=list)
    emotional_atmosphere: str = ""


class ExtractedSummary(BaseModel):
    """Structured extraction from raw drama summary."""
    actors: list[Actor]
    point_of_conflict: Conflict
    general_details: GeneralDetails
    missing_info: list[str] = Field(default_factory=list)

    @field_validator("actors")
    @classmethod
    def validate_actors_not_empty(cls, v: list[Actor]) -> list[Actor]:
        """Ensure actors array is never empty per prompt requirements."""
        if not v:
            raise ValueError("Actors array cannot be empty")
        return v


class DriftAnalysis(BaseModel):
    """Analysis of whether an answer addressed the question."""
    addressed_question: bool
    drift_reason: str
    redirect_suggestion: str


class QuestionWithAnswers(BaseModel):
    """Interview question with multiple choice answers."""
    question: str
    target_goal: str
    reasoning: str
    answers: list[Answer]

    @field_validator("answers")
    @classmethod
    def validate_four_answers(cls, v: list[Answer]) -> list[Answer]:
        """Ensure exactly 4 answers per schema requirements."""
        if len(v) != 4:
            raise ValueError("Must have exactly 4 answers")
        return v


class TimelineEvent(BaseModel):
    """Single event in the timeline."""
    time: str
    event: str


class Verdict(BaseModel):
    """Verdict assigning responsibility for the drama."""
    primary_responsibility: str
    percentage: int = Field(ge=0, le=100)
    reasoning: str
    contributing_factors: str
    drama_rating: int = Field(ge=1, le=10)
    drama_rating_explanation: str


class AnalysisReport(BaseModel):
    """Comprehensive analysis report for a drama incident."""
    timeline: list[TimelineEvent]
    key_facts: list[str]
    gaps: list[str]
    verdict: Verdict


class Session(BaseModel):
    session_id: str
    incident_name: str
    created_at: str
    status: SessionStatus = SessionStatus.ACTIVE
    summary: str = ""
    extracted_summary: Union[ExtractedSummary, None] = None
    interviewee_name: str = ""
    interviewee_role: str = ""  # "participant", "witness", "secondhand", "friend"
    confidence_threshold: int = Field(default=90, ge=20, le=95)  # Confidence level to end investigation
    goals: list[Goal] = Field(default_factory=list)
    messages: list[Message] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    answers: list[Answer] = Field(default_factory=list)
    current_question: str = ""
    turn_count: int = 0
