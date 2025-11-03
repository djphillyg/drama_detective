from datetime import datetime

from src.models import Fact, Goal, GoalStatus, Session, SessionStatus


def test_goal_creation():
    goal = Goal(
        description="Establish timeline of events",
        status=GoalStatus.NOT_STARTED,
        confidence=0,
    )
    assert goal.description == "Establish timeline of events"
    assert goal.status == GoalStatus.NOT_STARTED
    assert goal.confidence == 0


def test_goal_confidence_bounds():
    goal = Goal(description="Test goal", status=GoalStatus.IN_PROGRESS, confidence=150)
    assert goal.confidence == 100  # Should cap at 100


def test_fact_creation():
    fact = Fact(topic="cake incident", claim="Sarah forgot dessert", timestamp="5pm")
    assert fact.topic == "cake incident"
    assert fact.confidence == "certain"


def test_session_creation():
    session = Session(
        session_id="test-123",
        incident_name="birthday drama",
        created_at=datetime.now().isoformat(),
    )
    assert session.status == SessionStatus.ACTIVE
    assert len(session.goals) == 0
    assert session.turn_count == 0


def test_session_with_extracted_summary():
    """Test that Session can store extracted summary data"""
    extracted_summary = {
        "actors": [
            {
                "name": "Sarah",
                "role": "birthday person",
                "relationships": ["friend of John"],
                "emotional_state": "upset"
            }
        ],
        "point_of_conflict": {
            "primary": "Forgotten cake",
            "secondary": ["Lack of communication"]
        },
        "general_details": {
            "timeline_markers": ["5pm"],
            "location_context": ["party venue"],
            "communication_history": ["no heads up about cake"],
            "emotional_atmosphere": "tense"
        },
        "missing_info": ["Who was supposed to bring cake?"]
    }

    session = Session(
        session_id="test-456",
        incident_name="cake drama",
        created_at=datetime.now().isoformat(),
        extracted_summary=extracted_summary
    )

    assert session.extracted_summary == extracted_summary
    assert session.extracted_summary["actors"][0]["name"] == "Sarah"
    assert session.extracted_summary["point_of_conflict"]["primary"] == "Forgotten cake"


def test_session_extracted_summary_defaults_to_none():
    """Test that extracted_summary defaults to None if not provided"""
    session = Session(
        session_id="test-789",
        incident_name="test incident",
        created_at=datetime.now().isoformat(),
    )

    assert session.extracted_summary is None
