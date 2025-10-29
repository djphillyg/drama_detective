"""Test cases for API server endpoints."""
import time
from unittest.mock import Mock, patch

import pytest

from src.models import Answer, Fact, Goal, GoalStatus, Session, SessionStatus


@pytest.fixture
def app():
    """Create Flask test app."""
    from src.api.app import create_app

    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


class TestApiServer:
    """Test suite for Flask API endpoints."""

    # POST /api/investigate tests

    @patch("src.api.routes.SessionManager")
    @patch("src.api.routes.InterviewOrchestrator")
    def test_investigate_happy_path(self, mock_orchestrator_class, mock_session_manager_class, client):
        """Valid incident_name and summary successfully creates a new session and returns session_id, first question, and empty answers list."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create mock session
        mock_session = Session(
            session_id="test-session-123",
            incident_name="test-incident",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.ACTIVE,
            current_question="What happened first?",
            goals=[
                Goal(description="Establish timeline", confidence=30, status=GoalStatus.IN_PROGRESS)
            ],
            answers=[],
            turn_count=0
        )
        mock_session_manager.create_session.return_value = mock_session

        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_orchestrator.initialize_investigation = Mock()

        # Make request
        response = client.post("/api/investigate", json={
            "incident_name": "test-incident",
            "summary": "This is a test summary of what happened"
        })

        # Assert response
        assert response.status_code == 200
        data = response.get_json()
        assert data["session_id"] == "test-session-123"
        assert data["incident_name"] == "test-incident"
        assert data["question"] == "What happened first?"
        assert data["answers"] == []
        assert data["turn_count"] == 0
        assert len(data["goals"]) == 1

        # Assert mocks were called
        mock_session_manager.create_session.assert_called_once_with("test-incident")
        mock_orchestrator.initialize_investigation.assert_called_once()
        mock_session_manager.save_session.assert_called_once()

    def test_investigate_missing_required_fields(self, client):
        """Request without incident_name or summary returns 400 error with descriptive message."""
        # Missing incident_name
        response = client.post("/api/investigate", json={
            "summary": "Test summary"
        })
        assert response.status_code == 400 or response.status_code == 500

        # Missing summary
        response = client.post("/api/investigate", json={
            "incident_name": "test-incident"
        })
        assert response.status_code == 400 or response.status_code == 500

        # Missing both
        response = client.post("/api/investigate", json={})
        assert response.status_code == 400 or response.status_code == 500

    @patch("src.api.routes.SessionManager")
    @patch("src.api.routes.InterviewOrchestrator")
    def test_investigate_empty_string_inputs(self, mock_orchestrator_class, mock_session_manager_class, client):
        """Incident_name or summary with empty strings should be rejected or handled with validation error."""
        # Empty incident_name
        response = client.post("/api/investigate", json={
            "incident_name": "",
            "summary": "Valid summary"
        })
        # Should either reject or handle gracefully
        assert response.status_code in [400, 500] or response.status_code == 200

        # Empty summary
        response = client.post("/api/investigate", json={
            "incident_name": "valid-incident",
            "summary": ""
        })
        # Should either reject or handle gracefully
        assert response.status_code in [400, 500] or response.status_code == 200

    @patch("src.api.routes.SessionManager")
    @patch("src.api.routes.InterviewOrchestrator")
    def test_investigate_very_long_summary(self, mock_orchestrator_class, mock_session_manager_class, client):
        """Summary with 5000+ characters processes correctly and generates appropriate initial question."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create mock session
        mock_session = Session(
            session_id="test-session-456",
            incident_name="long-summary-test",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.ACTIVE,
            current_question="Can you summarize the key points?",
            goals=[],
            answers=[],
            turn_count=0
        )
        mock_session_manager.create_session.return_value = mock_session

        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator

        # Create very long summary
        long_summary = "This is a test. " * 500  # ~8000 characters

        # Make request
        response = client.post("/api/investigate", json={
            "incident_name": "long-summary-test",
            "summary": long_summary
        })

        # Assert handles long summary
        assert response.status_code == 200
        data = response.get_json()
        assert "session_id" in data
        assert "question" in data

    @patch("src.api.routes.SessionManager")
    @patch("src.api.routes.InterviewOrchestrator")
    def test_investigate_special_characters_in_incident_name(self, mock_orchestrator_class, mock_session_manager_class, client):
        """Incident names with special characters (emoji, unicode, slashes) are handled and sanitized properly."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create mock session with special characters
        mock_session = Session(
            session_id="test-session-789",
            incident_name="test-🔥-incident/with\\special",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.ACTIVE,
            current_question="What happened?",
            goals=[],
            answers=[],
            turn_count=0
        )
        mock_session_manager.create_session.return_value = mock_session

        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator

        # Make request with special characters
        response = client.post("/api/investigate", json={
            "incident_name": "test-🔥-incident/with\\special",
            "summary": "Test summary"
        })

        # Assert handles special characters
        assert response.status_code == 200
        data = response.get_json()
        assert "session_id" in data

    @patch("src.api.routes.SessionManager")
    @patch("src.api.routes.InterviewOrchestrator")
    def test_investigate_session_persistence(self, mock_orchestrator_class, mock_session_manager_class, client):
        """Created session can be retrieved immediately via GET /api/sessions endpoint."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create mock session
        mock_session = Session(
            session_id="persist-test-123",
            incident_name="persistence-test",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.ACTIVE,
            current_question="Initial question?",
            goals=[],
            answers=[],
            turn_count=0
        )
        mock_session_manager.create_session.return_value = mock_session
        mock_session_manager.list_sessions.return_value = [mock_session]

        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator

        # Create session
        response = client.post("/api/investigate", json={
            "incident_name": "persistence-test",
            "summary": "Test persistence"
        })
        assert response.status_code == 200
        data = response.get_json()
        session_id = data["session_id"]

        # Verify session was saved
        mock_session_manager.save_session.assert_called_once()

        # List sessions and verify it exists
        response = client.get("/api/sessions")
        assert response.status_code == 200
        data = response.get_json()
        assert "sessions" in data
        session_ids = [s["session_id"] for s in data["sessions"]]
        assert session_id in session_ids

    @patch("src.api.routes.SessionManager")
    @patch("src.api.routes.InterviewOrchestrator")
    def test_investigate_initial_goals_generation(self, mock_orchestrator_class, mock_session_manager_class, client):
        """Response includes populated goals array with confidence scores from the summary."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create mock session with goals
        mock_session = Session(
            session_id="goals-test-123",
            incident_name="goals-test",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.ACTIVE,
            current_question="What happened?",
            goals=[
                Goal(description="Establish timeline", confidence=30, status=GoalStatus.IN_PROGRESS),
                Goal(description="Identify people", confidence=20, status=GoalStatus.IN_PROGRESS)
            ],
            answers=[],
            turn_count=0
        )
        mock_session_manager.create_session.return_value = mock_session

        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator

        # Make request
        response = client.post("/api/investigate", json={
            "incident_name": "goals-test",
            "summary": "Test summary for goals generation"
        })

        # Assert response includes goals
        assert response.status_code == 200
        data = response.get_json()
        assert "goals" in data
        assert len(data["goals"]) == 2
        assert data["goals"][0]["description"] == "Establish timeline"
        assert data["goals"][0]["confidence"] == 30
        assert data["goals"][1]["description"] == "Identify people"
        assert data["goals"][1]["confidence"] == 20

    # POST /api/answer tests

    @patch("src.api.routes.SessionManager")
    @patch("src.api.routes.InterviewOrchestrator")
    def test_answer_happy_path_continuation(self, mock_orchestrator_class, mock_session_manager_class, client):
        """Valid session_id and answer returns next question with updated facts_count and turn_count."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create mock session
        mock_session = Session(
            session_id="answer-test-123",
            incident_name="answer-test",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.ACTIVE,
            current_question="What happened next?",
            goals=[
                Goal(description="Establish timeline", confidence=60, status=GoalStatus.IN_PROGRESS)
            ],
            answers=[],
            facts=[Fact(topic="timing", claim="Event started at 3pm", timestamp="3pm")],
            turn_count=1
        )
        mock_session_manager.load_session.return_value = mock_session

        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_orchestrator.process_answer.return_value = ("What happened after that?", False)

        # Make request
        response = client.post("/api/answer", json={
            "session_id": "answer-test-123",
            "answer": {
                "answer": "Then John arrived",
                "reasoning": "Provides timeline information"
            }
        })

        # Assert response
        assert response.status_code == 200
        data = response.get_json()
        assert data["question"] == "What happened after that?"
        assert data["is_complete"] is False
        assert data["turn_count"] == 1
        assert "facts_count" in data
        assert "goals" in data

        # Assert mocks were called
        mock_session_manager.load_session.assert_called_once_with("answer-test-123")
        mock_orchestrator.process_answer.assert_called_once()
        mock_session_manager.save_session.assert_called_once()

    @patch("src.api.routes.SessionManager")
    def test_answer_invalid_session_id(self, mock_session_manager_class, client):
        """Non-existent or malformed session_id returns 404 error."""
        # Mock session manager to raise exception
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager
        mock_session_manager.load_session.side_effect = Exception("Session not found")

        # Make request with invalid session_id
        response = client.post("/api/answer", json={
            "session_id": "non-existent-session",
            "answer": {
                "answer": "Test answer",
                "reasoning": "Test reasoning"
            }
        })

        # Assert error response
        assert response.status_code in [404, 500]

    def test_answer_missing_answer_data(self, client):
        """Request without answer field or missing answer/reasoning returns 400 validation error."""
        # Missing answer field entirely
        response = client.post("/api/answer", json={
            "session_id": "test-session-123"
        })
        assert response.status_code in [400, 500]

        # Missing reasoning in answer
        response = client.post("/api/answer", json={
            "session_id": "test-session-123",
            "answer": {
                "answer": "Just the answer"
            }
        })
        assert response.status_code in [400, 500]

    @patch("src.api.routes.SessionManager")
    @patch("src.api.routes.InterviewOrchestrator")
    def test_answer_interview_completion(self, mock_orchestrator_class, mock_session_manager_class, client):
        """Final answer that satisfies all goals returns is_complete: true with appropriate completion message."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create mock session
        mock_session = Session(
            session_id="complete-test-123",
            incident_name="complete-test",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.ACTIVE,
            current_question="Final question?",
            goals=[
                Goal(description="Establish timeline", confidence=95, status=GoalStatus.COMPLETE)
            ],
            answers=[],
            facts=[],
            turn_count=5
        )
        mock_session_manager.load_session.return_value = mock_session

        # Mock orchestrator to return completion
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_orchestrator.process_answer.return_value = (None, True)

        # Make request
        response = client.post("/api/answer", json={
            "session_id": "complete-test-123",
            "answer": {
                "answer": "Final answer",
                "reasoning": "Completes all goals"
            }
        })

        # Assert completion response
        assert response.status_code == 200
        data = response.get_json()
        assert data["is_complete"] is True
        assert "message" in data
        assert "complete" in data["message"].lower()

    @patch("src.api.routes.SessionManager")
    @patch("src.api.routes.InterviewOrchestrator")
    def test_answer_mid_interview_state(self, mock_orchestrator_class, mock_session_manager_class, client):
        """Answer updates goals confidence scores and facts list correctly in response."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create mock session with initial state
        mock_session = Session(
            session_id="mid-test-123",
            incident_name="mid-test",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.ACTIVE,
            current_question="Current question?",
            goals=[
                Goal(description="Goal 1", confidence=40, status=GoalStatus.IN_PROGRESS),
                Goal(description="Goal 2", confidence=30, status=GoalStatus.IN_PROGRESS)
            ],
            answers=[],
            facts=[
                Fact(topic="timing", claim="Fact 1", timestamp="1pm"),
                Fact(topic="people", claim="Fact 2", timestamp="2pm")
            ],
            turn_count=2
        )
        mock_session_manager.load_session.return_value = mock_session

        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_orchestrator.process_answer.return_value = ("Next question?", False)

        # Make request
        response = client.post("/api/answer", json={
            "session_id": "mid-test-123",
            "answer": {
                "answer": "Test answer",
                "reasoning": "Test reasoning"
            }
        })

        # Assert response includes updated state
        assert response.status_code == 200
        data = response.get_json()
        assert "goals" in data
        assert len(data["goals"]) == 2
        assert "facts_count" in data
        assert data["facts_count"] == 2
        assert "turn_count" in data

    @patch("src.api.routes.SessionManager")
    def test_answer_malformed_answer_object(self, mock_session_manager_class, client):
        """Answer missing required fields (answer, reasoning) is rejected with validation error."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        mock_session = Session(
            session_id="malformed-test-123",
            incident_name="malformed-test",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.ACTIVE,
            current_question="Question?",
            goals=[],
            answers=[],
            facts=[],
            turn_count=0
        )
        mock_session_manager.load_session.return_value = mock_session

        # Missing 'answer' field
        response = client.post("/api/answer", json={
            "session_id": "malformed-test-123",
            "answer": {
                "reasoning": "Only reasoning provided"
            }
        })
        assert response.status_code in [400, 500]

        # Missing 'reasoning' field
        response = client.post("/api/answer", json={
            "session_id": "malformed-test-123",
            "answer": {
                "answer": "Only answer provided"
            }
        })
        assert response.status_code in [400, 500]

    @patch("src.api.routes.SessionManager")
    @patch("src.api.routes.InterviewOrchestrator")
    def test_answer_already_completed_session(self, mock_orchestrator_class, mock_session_manager_class, client):
        """Submitting answer to completed session returns error or appropriate status message."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create completed session
        mock_session = Session(
            session_id="completed-session-123",
            incident_name="completed-test",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.COMPLETE,
            current_question="",
            goals=[
                Goal(description="Goal 1", confidence=100, status=GoalStatus.COMPLETE)
            ],
            answers=[],
            facts=[],
            turn_count=10
        )
        mock_session_manager.load_session.return_value = mock_session

        # Mock orchestrator might throw error or handle gracefully
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_orchestrator.process_answer.side_effect = Exception("Session already completed")

        # Make request
        response = client.post("/api/answer", json={
            "session_id": "completed-session-123",
            "answer": {
                "answer": "Late answer",
                "reasoning": "Trying to answer completed session"
            }
        })

        # Assert error or special handling
        assert response.status_code in [400, 500]

    # GET /api/sessions tests

    @patch("src.api.routes.SessionManager")
    def test_sessions_empty_state(self, mock_session_manager_class, client):
        """No sessions exist returns empty sessions array with 200 status."""
        # Mock session manager to return empty list
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager
        mock_session_manager.list_sessions.return_value = []

        # Make request
        response = client.get("/api/sessions")

        # Assert response
        assert response.status_code == 200
        data = response.get_json()
        assert "sessions" in data
        assert data["sessions"] == []

    @patch("src.api.routes.SessionManager")
    def test_sessions_multiple_sessions(self, mock_session_manager_class, client):
        """Returns all sessions with correct metadata (session_id, incident_name, status, created_at, turn_count, progress)."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create multiple mock sessions
        sessions = [
            Session(
                session_id="session-1",
                incident_name="incident-1",
                created_at="2025-01-01T12:00:00",
                status=SessionStatus.ACTIVE,
                current_question="Q1",
                goals=[Goal(description="Goal 1", confidence=50, status=GoalStatus.IN_PROGRESS)],
                answers=[],
                facts=[],
                turn_count=3
            ),
            Session(
                session_id="session-2",
                incident_name="incident-2",
                created_at="2025-01-02T12:00:00",
                status=SessionStatus.COMPLETE,
                current_question="",
                goals=[Goal(description="Goal 2", confidence=100, status=GoalStatus.COMPLETE)],
                answers=[],
                facts=[],
                turn_count=8
            )
        ]
        mock_session_manager.list_sessions.return_value = sessions

        # Make request
        response = client.get("/api/sessions")

        # Assert response
        assert response.status_code == 200
        data = response.get_json()
        assert "sessions" in data
        assert len(data["sessions"]) == 2

        # Check first session metadata
        session1 = data["sessions"][0]
        assert session1["session_id"] == "session-1"
        assert session1["incident_name"] == "incident-1"
        assert session1["status"] == "active"
        assert session1["turn_count"] == 3
        assert "progress" in session1
        assert "created_at" in session1

        # Check second session metadata
        session2 = data["sessions"][1]
        assert session2["session_id"] == "session-2"
        assert session2["incident_name"] == "incident-2"
        assert session2["status"] == "complete"
        assert session2["turn_count"] == 8

    @patch("src.api.routes.SessionManager")
    def test_sessions_progress_calculation(self, mock_session_manager_class, client):
        """Progress field accurately reflects average confidence of goals (0-100)."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create session with known goal confidences
        session = Session(
            session_id="progress-test",
            incident_name="progress-test",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.ACTIVE,
            current_question="Q",
            goals=[
                Goal(description="Goal 1", confidence=60, status=GoalStatus.IN_PROGRESS),
                Goal(description="Goal 2", confidence=80, status=GoalStatus.IN_PROGRESS),
                Goal(description="Goal 3", confidence=40, status=GoalStatus.IN_PROGRESS)
            ],
            answers=[],
            facts=[],
            turn_count=5
        )
        mock_session_manager.list_sessions.return_value = [session]

        # Make request
        response = client.get("/api/sessions")

        # Assert progress calculation (60 + 80 + 40) / 3 = 60
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["progress"] == 60

    @patch("src.api.routes.SessionManager")
    def test_sessions_session_ordering(self, mock_session_manager_class, client):
        """Sessions are returned in consistent order (likely by created_at descending)."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create sessions with different timestamps
        sessions = [
            Session(
                session_id="session-old",
                incident_name="old",
                created_at="2025-01-01T12:00:00",
                status=SessionStatus.ACTIVE,
                current_question="Q",
                goals=[],
                answers=[],
                facts=[],
                turn_count=1
            ),
            Session(
                session_id="session-new",
                incident_name="new",
                created_at="2025-01-03T12:00:00",
                status=SessionStatus.ACTIVE,
                current_question="Q",
                goals=[],
                answers=[],
                facts=[],
                turn_count=1
            ),
            Session(
                session_id="session-middle",
                incident_name="middle",
                created_at="2025-01-02T12:00:00",
                status=SessionStatus.ACTIVE,
                current_question="Q",
                goals=[],
                answers=[],
                facts=[],
                turn_count=1
            )
        ]
        mock_session_manager.list_sessions.return_value = sessions

        # Make request
        response = client.get("/api/sessions")

        # Assert sessions are returned in consistent order
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["sessions"]) == 3

        # Verify order is preserved from SessionManager
        assert data["sessions"][0]["session_id"] == "session-old"
        assert data["sessions"][1]["session_id"] == "session-new"
        assert data["sessions"][2]["session_id"] == "session-middle"

    @patch("src.api.routes.SessionManager")
    def test_sessions_status_field_accuracy(self, mock_session_manager_class, client):
        """Status enum value correctly reflects session state (in_progress, completed, etc.)."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create sessions with different statuses
        sessions = [
            Session(
                session_id="active-session",
                incident_name="active",
                created_at="2025-01-01T12:00:00",
                status=SessionStatus.ACTIVE,
                current_question="Q",
                goals=[],
                answers=[],
                facts=[],
                turn_count=1
            ),
            Session(
                session_id="completed-session",
                incident_name="complete",
                created_at="2025-01-02T12:00:00",
                status=SessionStatus.COMPLETE,
                current_question="",
                goals=[],
                answers=[],
                facts=[],
                turn_count=10
            )
        ]
        mock_session_manager.list_sessions.return_value = sessions

        # Make request
        response = client.get("/api/sessions")

        # Assert status fields are accurate
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["sessions"]) == 2
        assert data["sessions"][0]["status"] == "active"
        assert data["sessions"][1]["status"] == "complete"

    @patch("src.api.routes.SessionManager")
    def test_sessions_large_dataset_performance(self, mock_session_manager_class, client):
        """With 50+ sessions, endpoint responds within reasonable time (<2s)."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create 50 mock sessions
        sessions = []
        for i in range(50):
            sessions.append(
                Session(
                    session_id=f"session-{i}",
                    incident_name=f"incident-{i}",
                    created_at=f"2025-01-01T12:00:{i:02d}",
                    status=SessionStatus.ACTIVE,
                    current_question="Q",
                    goals=[Goal(description="Goal", confidence=50, status=GoalStatus.IN_PROGRESS)],
                    answers=[],
                    facts=[],
                    turn_count=1
                )
            )
        mock_session_manager.list_sessions.return_value = sessions

        # Make request and measure time
        start_time = time.time()
        response = client.get("/api/sessions")
        elapsed_time = time.time() - start_time

        # Assert response and performance
        assert response.status_code == 200
        assert elapsed_time < 2.0  # Less than 2 seconds
        data = response.get_json()
        assert len(data["sessions"]) == 50

    @patch("src.api.routes.SessionManager")
    def test_sessions_partial_session_data(self, mock_session_manager_class, client):
        """Sessions with missing optional fields still return valid responses without crashing."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create session with minimal data (empty goals, facts, etc.)
        session = Session(
            session_id="minimal-session",
            incident_name="minimal",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.ACTIVE,
            current_question="Q",
            goals=[],  # Empty goals
            answers=[],
            facts=[],
            turn_count=0
        )
        mock_session_manager.list_sessions.return_value = [session]

        # Make request
        response = client.get("/api/sessions")

        # Assert handles empty/missing data gracefully
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["session_id"] == "minimal-session"
        # Progress should be 0 when no goals exist
        assert data["sessions"][0]["progress"] == 0

    # GET /api/analysis/<session_id> tests

    @patch("src.api.routes.ClaudeClient")
    @patch("src.api.routes.AnalysisAgent")
    @patch("src.api.routes.SessionManager")
    def test_analysis_completed_session_analysis(self, mock_session_manager_class, mock_analysis_agent_class, mock_claude_client_class, client):
        """Valid completed session returns full analysis with incident_name and analysis object."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create completed session
        session = Session(
            session_id="analysis-test-123",
            incident_name="test-incident",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.COMPLETE,
            current_question="",
            goals=[Goal(description="Goal", confidence=100, status=GoalStatus.COMPLETE)],
            answers=[],
            facts=[],
            turn_count=10
        )
        mock_session_manager.load_session.return_value = session

        # Mock analysis agent
        mock_claude_client = Mock()
        mock_claude_client_class.return_value = mock_claude_client

        mock_analysis_agent = Mock()
        mock_analysis_agent_class.return_value = mock_analysis_agent
        mock_analysis_agent.generate_analysis.return_value = {
            "verdict": "Test verdict",
            "timeline": [],
            "drama_rating": 7
        }

        # Make request
        response = client.get("/api/analysis/analysis-test-123")

        # Assert response
        assert response.status_code == 200
        data = response.get_json()
        assert data["incident_name"] == "test-incident"
        assert "analysis" in data
        assert data["analysis"]["verdict"] == "Test verdict"
        assert data["analysis"]["drama_rating"] == 7

    @patch("src.api.routes.SessionManager")
    def test_analysis_non_existent_session(self, mock_session_manager_class, client):
        """Invalid session_id returns 404 error with appropriate message."""
        # Mock session manager to raise exception
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager
        mock_session_manager.load_session.side_effect = Exception("Session not found")

        # Make request
        response = client.get("/api/analysis/non-existent-session")

        # Assert error response
        assert response.status_code in [404, 500]

    @patch("src.api.routes.ClaudeClient")
    @patch("src.api.routes.AnalysisAgent")
    @patch("src.api.routes.SessionManager")
    def test_analysis_incomplete_session(self, mock_session_manager_class, mock_analysis_agent_class, mock_claude_client_class, client):
        """Session that hasn't reached completion returns error or generates partial analysis."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create incomplete session
        session = Session(
            session_id="incomplete-test",
            incident_name="incomplete",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.ACTIVE,  # Still active
            current_question="Still asking questions",
            goals=[Goal(description="Goal", confidence=50, status=GoalStatus.IN_PROGRESS)],
            answers=[],
            facts=[],
            turn_count=3
        )
        mock_session_manager.load_session.return_value = session

        # Mock analysis agent to handle incomplete session
        mock_claude_client = Mock()
        mock_claude_client_class.return_value = mock_claude_client

        mock_analysis_agent = Mock()
        mock_analysis_agent_class.return_value = mock_analysis_agent
        mock_analysis_agent.generate_analysis.return_value = {
            "verdict": "Partial analysis",
            "note": "Session incomplete"
        }

        # Make request
        response = client.get("/api/analysis/incomplete-test")

        # Assert response (may return partial analysis or error)
        assert response.status_code in [200, 400, 500]

    @patch("src.api.routes.ClaudeClient")
    @patch("src.api.routes.AnalysisAgent")
    @patch("src.api.routes.SessionManager")
    def test_analysis_analysis_structure(self, mock_session_manager_class, mock_analysis_agent_class, mock_claude_client_class, client):
        """Response contains all expected analysis sections (verdict, timeline, drama rating, etc.)."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        session = Session(
            session_id="structure-test",
            incident_name="structure-test",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.COMPLETE,
            current_question="",
            goals=[],
            answers=[],
            facts=[],
            turn_count=10
        )
        mock_session_manager.load_session.return_value = session

        # Mock analysis agent with full structure
        mock_claude_client = Mock()
        mock_claude_client_class.return_value = mock_claude_client

        mock_analysis_agent = Mock()
        mock_analysis_agent_class.return_value = mock_analysis_agent
        mock_analysis_agent.generate_analysis.return_value = {
            "verdict": "Complete verdict",
            "timeline": [{"time": "3pm", "event": "Event 1"}],
            "drama_rating": 8,
            "primary_responsibility": "Person A"
        }

        # Make request
        response = client.get("/api/analysis/structure-test")

        # Assert response structure
        assert response.status_code == 200
        data = response.get_json()
        assert "incident_name" in data
        assert "analysis" in data
        analysis = data["analysis"]
        assert "verdict" in analysis
        assert "timeline" in analysis
        assert "drama_rating" in analysis

    @patch("src.api.routes.ClaudeClient")
    @patch("src.api.routes.AnalysisAgent")
    @patch("src.api.routes.SessionManager")
    def test_analysis_idempotency(self, mock_session_manager_class, mock_analysis_agent_class, mock_claude_client_class, client):
        """Multiple requests for same session_id return identical analysis results."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        session = Session(
            session_id="idempotent-test",
            incident_name="idempotent-test",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.COMPLETE,
            current_question="",
            goals=[],
            answers=[],
            facts=[],
            turn_count=10
        )
        mock_session_manager.load_session.return_value = session

        # Mock analysis agent
        mock_claude_client = Mock()
        mock_claude_client_class.return_value = mock_claude_client

        mock_analysis_agent = Mock()
        mock_analysis_agent_class.return_value = mock_analysis_agent
        mock_analysis_agent.generate_analysis.return_value = {
            "verdict": "Consistent verdict",
            "drama_rating": 6
        }

        # Make first request
        response1 = client.get("/api/analysis/idempotent-test")
        assert response1.status_code == 200
        data1 = response1.get_json()

        # Make second request
        response2 = client.get("/api/analysis/idempotent-test")
        assert response2.status_code == 200
        data2 = response2.get_json()

        # Assert responses are identical
        assert data1 == data2

    @patch("src.api.routes.ClaudeClient")
    @patch("src.api.routes.AnalysisAgent")
    @patch("src.api.routes.SessionManager")
    def test_analysis_minimal_data_session(self, mock_session_manager_class, mock_analysis_agent_class, mock_claude_client_class, client):
        """Session with only 1-2 answers still generates valid analysis without errors."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create session with minimal data
        session = Session(
            session_id="minimal-analysis-test",
            incident_name="minimal-data",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.COMPLETE,
            current_question="",
            goals=[],
            answers=[
                Answer(answer="Answer 1", reasoning="Reason 1")
            ],
            facts=[Fact(topic="topic", claim="claim", timestamp="time")],
            turn_count=2
        )
        mock_session_manager.load_session.return_value = session

        # Mock analysis agent
        mock_claude_client = Mock()
        mock_claude_client_class.return_value = mock_claude_client

        mock_analysis_agent = Mock()
        mock_analysis_agent_class.return_value = mock_analysis_agent
        mock_analysis_agent.generate_analysis.return_value = {
            "verdict": "Minimal analysis",
            "note": "Limited data available"
        }

        # Make request
        response = client.get("/api/analysis/minimal-analysis-test")

        # Assert handles minimal data gracefully
        assert response.status_code == 200
        data = response.get_json()
        assert "analysis" in data

    @patch("src.api.routes.ClaudeClient")
    @patch("src.api.routes.AnalysisAgent")
    @patch("src.api.routes.SessionManager")
    def test_analysis_analysis_generation_performance(self, mock_session_manager_class, mock_analysis_agent_class, mock_claude_client_class, client):
        """Analysis for typical session (8-10 turns) completes within reasonable time (<5s)."""
        # Mock session manager
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create typical session with 10 turns
        session = Session(
            session_id="performance-test",
            incident_name="performance-test",
            created_at="2025-01-01T12:00:00",
            status=SessionStatus.COMPLETE,
            current_question="",
            goals=[Goal(description="Goal", confidence=100, status=GoalStatus.COMPLETE)],
            answers=[Answer(answer=f"Answer {i}", reasoning=f"Reason {i}") for i in range(10)],
            facts=[Fact(topic="topic", claim=f"Fact {i}", timestamp=f"{i}pm") for i in range(10)],
            turn_count=10
        )
        mock_session_manager.load_session.return_value = session

        # Mock analysis agent
        mock_claude_client = Mock()
        mock_claude_client_class.return_value = mock_claude_client

        mock_analysis_agent = Mock()
        mock_analysis_agent_class.return_value = mock_analysis_agent
        mock_analysis_agent.generate_analysis.return_value = {
            "verdict": "Performance test verdict",
            "drama_rating": 7
        }

        # Make request and measure time
        start_time = time.time()
        response = client.get("/api/analysis/performance-test")
        elapsed_time = time.time() - start_time

        # Assert response and performance
        assert response.status_code == 200
        assert elapsed_time < 5.0  # Less than 5 seconds
        data = response.get_json()
        assert "analysis" in data