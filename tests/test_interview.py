from unittest.mock import Mock, patch

from src.interview import InterviewOrchestrator
from src.models import Answer, Fact, Goal, GoalStatus, Session, SessionStatus


def test_orchestrator_initialization():
    # Create Session
    session = Session(
        session_id="test-123",
        incident_name="Test Incident",
        created_at="2025-01-01T12:00:00",
        status=SessionStatus.ACTIVE,
    )

    # Mock ClaudeClient to avoid real API calls
    with patch("src.interview.ClaudeClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Create InterviewOrchestrator with session
        orchestrator = InterviewOrchestrator(session)

        # Assert session is stored
        assert orchestrator.session == session
        assert orchestrator.session.session_id == "test-123"

        # Assert turn_count starts at 0
        assert orchestrator.turn_count == 0

        # Assert agents are initialized
        assert orchestrator.summary_extractor is not None
        assert orchestrator.goal_generator is not None
        assert orchestrator.fact_extractor is not None
        assert orchestrator.drift_detector is not None
        assert orchestrator.goal_tracker is not None
        assert orchestrator.question_generator is not None


def test_process_answer_pipeline():
    # Create session with current_question and goals
    session = Session(
        session_id="test-123",
        incident_name="Test Incident",
        created_at="2025-01-01T12:00:00",
        status=SessionStatus.ACTIVE,
        current_question="What time did Sarah arrive?",
        goals=[
            Goal(
                description="Establish timeline",
                confidence=30,
                status=GoalStatus.IN_PROGRESS,
            ),
            Goal(
                description="Identify people involved",
                confidence=50,
                status=GoalStatus.IN_PROGRESS,
            ),
        ],
        facts=[Fact(topic="timing", claim="Party started at 5pm", timestamp="5pm")],
    )

    # Mock ClaudeClient to avoid real API calls
    with patch("src.interview.ClaudeClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Create orchestrator
        orchestrator = InterviewOrchestrator(session)

        # Mock all agent methods
        # Mock fact_extractor
        mock_facts = [
            Fact(
                topic="timing",
                claim="Sarah arrived at 5:30pm",
                timestamp="5:30pm",
                confidence="certain",
            )
        ]
        orchestrator.fact_extractor.extract_facts = Mock(return_value=mock_facts)

        # Mock drift_detector (no drift detected)
        orchestrator.drift_detector.check_drift = Mock(
            return_value={
                "addressed_question": True,
                "drift_reason": None,
                "redirect_suggestion": None,
            }
        )

        # Mock goal_tracker
        updated_goals = [
            Goal(
                description="Establish timeline",
                confidence=60,
                status=GoalStatus.IN_PROGRESS,
            ),
            Goal(
                description="Identify people involved",
                confidence=70,
                status=GoalStatus.IN_PROGRESS,
            ),
        ]
        orchestrator.goal_tracker.update_goals = Mock(return_value=updated_goals)

        # Mock question_generator
        next_question_data = {
            "question": "Who else was at the party?",
            "target_goal": "Identify people involved",
            "reasoning": "Need to identify more attendees",
            "answers": [
                {
                    "answer": "John and Alex were there",
                    "reasoning": "Provides specific names",
                },
                {
                    "answer": "A bunch of people",
                    "reasoning": "Vague, indicates uncertainty",
                },
                {"answer": "I don't remember", "reasoning": "Shows lack of knowledge"},
                {
                    "answer": "Why does it matter?",
                    "reasoning": "Red herring, indicates deflection",
                },
            ],
        }
        orchestrator.question_generator.generate_question_with_answers = Mock(
            return_value=next_question_data
        )

        # Create answer from user
        user_answer = Answer(
            answer="She arrived at 5:30pm",
            reasoning="Provides specific timeline information",
        )

        # Call process_answer()
        next_question, is_complete = orchestrator.process_answer(user_answer)

        # Assert next question returned
        assert next_question == "Who else was at the party?"
        assert not is_complete

        # Assert turn_count incremented
        assert orchestrator.turn_count == 1

        # Assert messages added to session (user answer + assistant question)
        assert len(session.messages) >= 2
        # Check that user message was added
        user_messages = [m for m in session.messages if m.role == "user"]
        assert len(user_messages) >= 1
        assert user_messages[-1].content == "She arrived at 5:30pm"

        # Check that assistant message was added
        assistant_messages = [m for m in session.messages if m.role == "assistant"]
        assert len(assistant_messages) >= 1
        assert assistant_messages[-1].content == "Who else was at the party?"

        # Assert facts were added
        assert len(session.facts) == 2  # 1 initial + 1 new
        assert session.facts[-1].claim == "Sarah arrived at 5:30pm"

        # Assert goals were updated
        assert session.goals[0].confidence == 60
        assert session.goals[1].confidence == 70

        # Assert current_question was updated
        assert session.current_question == "Who else was at the party?"

        # Assert answers were stored
        assert len(session.answers) == 4
        assert session.answers[0].answer == "John and Alex were there"


def test_initialize_investigation_uses_summary_extractor():
    """Test that initialize_investigation calls summary extractor and passes result to goal generator"""
    # Create session
    session = Session(
        session_id="test-extract-123",
        incident_name="Test Incident",
        created_at="2025-01-01T12:00:00",
        status=SessionStatus.ACTIVE,
    )

    # Mock ClaudeClient to avoid real API calls
    with patch("src.interview.ClaudeClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Create orchestrator
        orchestrator = InterviewOrchestrator(session)

        # Mock summary extractor response
        mock_extracted_summary = {
            "actors": [
                {
                    "name": "Lamar",
                    "role": "upset friend",
                    "relationships": ["John's friend", "Rob's friend"],
                    "emotional_state": "angry/hurt"
                }
            ],
            "point_of_conflict": {
                "primary": "John and Rob went to Mexico together, excluding Lamar",
                "secondary": ["Lamar feels betrayed by friends"]
            },
            "general_details": {
                "timeline_markers": ["trip to Mexico"],
                "location_context": ["Mexico"],
                "communication_history": ["no mention of how Lamar found out"],
                "emotional_atmosphere": "tense, feelings of betrayal"
            },
            "missing_info": ["Was Lamar invited to Mexico?"]
        }
        orchestrator.summary_extractor.extract_summary = Mock(return_value=mock_extracted_summary)

        # Mock goal generator to return goals
        mock_goals = [
            Goal(description="Understand why John and Rob excluded Lamar", status=GoalStatus.NOT_STARTED),
            Goal(description="Clarify if Lamar was invited", status=GoalStatus.NOT_STARTED),
        ]
        orchestrator.goal_generator.generate_goals = Mock(return_value=mock_goals)

        # Mock question generator
        mock_question_data = {
            "question": "How did you find out about the trip?",
            "target_goal": "Understand why John and Rob excluded Lamar",
            "reasoning": "Need to understand communication",
            "answers": [
                {"answer": "They told me", "reasoning": "Direct communication"},
                {"answer": "I saw it on social media", "reasoning": "Indirect discovery"},
                {"answer": "Someone else told me", "reasoning": "Third party"},
                {"answer": "I don't want to talk about it", "reasoning": "Avoidance"},
            ],
        }
        orchestrator.question_generator.generate_question_with_answers = Mock(
            return_value=mock_question_data
        )

        # Call initialize_investigation
        raw_summary = "Lamar got really upset because John took Rob to Mexico and they're supposed to be his friends"
        first_question = orchestrator.initialize_investigation(raw_summary)

        # Assert summary extractor was called with raw summary
        orchestrator.summary_extractor.extract_summary.assert_called_once_with(
            raw_summary, session_id=session.session_id
        )

        # Assert extracted summary was stored in session
        assert session.extracted_summary == mock_extracted_summary

        # Assert goal generator was called with extracted summary (not raw summary)
        orchestrator.goal_generator.generate_goals.assert_called_once()
        call_args = orchestrator.goal_generator.generate_goals.call_args
        # The first positional argument should be the extracted summary
        assert call_args[0][0] == mock_extracted_summary

        # Assert goals were stored in session
        assert session.goals == mock_goals

        # Assert first question returned
        assert first_question == "How did you find out about the trip?"
