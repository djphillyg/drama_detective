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


class Session(BaseModel):
    session_id: str
    incident_name: str
    created_at: str
    status: SessionStatus = SessionStatus.ACTIVE
    summary: str = ""
    extracted_summary: Union[dict, None] = None
    interviewee_name: str = ""
    interviewee_role: str = ""  # "participant", "witness", "secondhand", "friend"
    goals: list[Goal] = Field(default_factory=list)
    messages: list[Message] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    answers: list[Answer] = Field(default_factory=list)
    current_question: str = ""
    turn_count: int = 0
