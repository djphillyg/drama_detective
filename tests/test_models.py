import pytest
from src.models import Goal, GoalStatus, Fact, Message, Session, SessionStatus
from datetime import datetime

def test_goal_creation():
    goal = Goal(
        description="Establish timeline of events",
        status=GoalStatus.NOT_STARTED,
        confidence=0
    )
    assert goal.description == "Establish timeline of events"
    assert goal.status == GoalStatus.NOT_STARTED
    assert goal.confidence == 0

def test_goal_confidence_bounds():
    goal = Goal(
        description="Test goal",
        status=GoalStatus.IN_PROGRESS,
        confidence=150
    )
    assert goal.confidence == 100  # Should cap at 100

def test_fact_creation():
    fact = Fact(
        topic="cake incident",
        claim="Sarah forgot dessert",
        timestamp="5pm"
    )
    assert fact.topic == "cake incident"
    assert fact.confidence == "certain"

def test_session_creation():
    session = Session(
        session_id="test-123",
        incident_name="birthday drama",
        created_at=datetime.now().isoformat()
    )
    assert session.status == SessionStatus.ACTIVE
    assert len(session.goals) == 0
    assert session.turn_count == 0