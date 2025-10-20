import pytest
import tempfile
import time
from pathlib import Path
from drama_detective.session import SessionManager
from drama_detective.models import Session, SessionStatus


class TestSessionManager:
    """Test suite for SessionManager functionality"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def session_manager(self, temp_dir):
        """Create a SessionManager instance with temp directory"""
        return SessionManager(data_dir=temp_dir)

    def test_temp_directory_creation(self, temp_dir):
        """Test that SessionManager creates the data directory"""
        # Create a subdirectory path that doesn't exist yet
        test_dir = temp_dir / "test_sessions"
        assert not test_dir.exists(), "Directory should not exist before SessionManager creation"

        # Create SessionManager with non-existent directory
        manager = SessionManager(data_dir=test_dir)

        # Verify directory was created
        assert test_dir.exists(), "Directory should be created by SessionManager"
        assert test_dir.is_dir(), "Path should be a directory"
        assert manager.data_dir == test_dir, "SessionManager should store correct data_dir"

    def test_create_session(self, session_manager):
        """Test creating a new session"""
        incident_name = "Test Incident"

        # Create session
        session = session_manager.create_session(incident_name)

        # Verify session properties
        assert isinstance(session, Session), "Should return a Session object"
        assert session.incident_name == incident_name, "Incident name should match"
        assert session.session_id is not None, "Session ID should be generated"
        assert len(session.session_id) > 0, "Session ID should not be empty"
        assert session.created_at is not None, "Created timestamp should be set"
        assert session.status == SessionStatus.ACTIVE, "New session should be ACTIVE"
        assert session.summary == "", "Summary should be empty initially"
        assert session.goals == [], "Goals should be empty list initially"
        assert session.messages == [], "Messages should be empty list initially"
        assert session.facts == [], "Facts should be empty list initially"
        assert session.turn_count == 0, "Turn count should be 0 initially"

    def test_save_and_load_session(self, session_manager, temp_dir):
        """Test saving a session and loading it back"""
        # Create a session
        incident_name = "Drama at the Office"
        session = session_manager.create_session(incident_name)
        session_id = session.session_id

        # Save the session
        session_manager.save_session(session)

        # Verify file was created
        session_file = temp_dir / f"{session_id}.json"
        assert session_file.exists(), "Session file should be created"

        # Load the session
        loaded_session = session_manager.load_session(session_id)

        # Verify loaded session matches original
        assert loaded_session.session_id == session.session_id, "Session ID should match"
        assert loaded_session.incident_name == session.incident_name, "Incident name should match"
        assert loaded_session.created_at == session.created_at, "Created timestamp should match"
        assert loaded_session.status == session.status, "Status should match"
        assert loaded_session.summary == session.summary, "Summary should match"
        assert loaded_session.goals == session.goals, "Goals should match"
        assert loaded_session.messages == session.messages, "Messages should match"
        assert loaded_session.facts == session.facts, "Facts should match"
        assert loaded_session.turn_count == session.turn_count, "Turn count should match"

    def test_load_nonexistent_session(self, session_manager):
        """Test that loading a non-existent session raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError, match="Session .* not found"):
            session_manager.load_session("nonexistent-session-id")

    def test_list_sessions_with_multiple_sessions(self, session_manager, temp_dir):
        """Test creating 2 sessions and verifying they appear in list_sessions"""
        # Create first session
        session1 = session_manager.create_session("First Incident")
        session_manager.save_session(session1)

        # Small delay to ensure different timestamps
        time.sleep(0.01)

        # Create second session
        session2 = session_manager.create_session("Second Incident")
        session_manager.save_session(session2)

        # List all sessions
        sessions = session_manager.list_sessions()

        # Verify both sessions are in the list
        assert len(sessions) == 2, "Should have 2 sessions in the list"

        # Verify sessions are sorted by created_at (newest first)
        assert sessions[0].session_id == session2.session_id, "Newest session should be first"
        assert sessions[1].session_id == session1.session_id, "Older session should be second"

        # Verify session details
        session_ids = {s.session_id for s in sessions}
        assert session1.session_id in session_ids, "First session should be in list"
        assert session2.session_id in session_ids, "Second session should be in list"

        # Verify incident names
        incident_names = {s.incident_name for s in sessions}
        assert "First Incident" in incident_names, "First incident name should be in list"
        assert "Second Incident" in incident_names, "Second incident name should be in list"

    def test_list_sessions_empty_directory(self, session_manager):
        """Test that list_sessions returns empty list when no sessions exist"""
        sessions = session_manager.list_sessions()
        assert sessions == [], "Should return empty list when no sessions exist"

    def test_list_sessions_ignores_corrupted_files(self, session_manager, temp_dir):
        """Test that list_sessions skips corrupted JSON files"""
        # Create a valid session
        session = session_manager.create_session("Valid Session")
        session_manager.save_session(session)

        # Create a corrupted JSON file
        corrupted_file = temp_dir / "corrupted.json"
        corrupted_file.write_text("{ invalid json content")

        # List sessions should only return the valid one
        sessions = session_manager.list_sessions()
        assert len(sessions) == 1, "Should only return valid sessions"
        assert sessions[0].session_id == session.session_id, "Should return the valid session"