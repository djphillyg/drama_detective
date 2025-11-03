"""Tests for SummaryExtractorAgent."""

from unittest.mock import Mock

from src.agents.summary_extractor import SummaryExtractorAgent
from src.api_client import ClaudeClient


def test_extract_summary():
    """Test that extract_summary returns structured summary data"""
    # Create mock client
    mock_client = Mock(spec=ClaudeClient)

    # Mock call_with_tool to return structured summary data
    mock_response = {
        "actors": [
            {
                "name": "Lamar",
                "role": "upset friend",
                "relationships": ["John's friend", "Rob's friend"],
                "emotional_state": "angry/hurt"
            },
            {
                "name": "John",
                "role": "trip organizer",
                "relationships": ["Lamar's friend", "Rob's travel companion"],
                "emotional_state": "unclear"
            },
            {
                "name": "Rob",
                "role": "trip participant",
                "relationships": ["Lamar's friend", "John's travel companion"],
                "emotional_state": "unclear"
            }
        ],
        "point_of_conflict": {
            "primary": "John and Rob went to Mexico together, excluding Lamar",
            "secondary": [
                "Lamar feels betrayed by friends",
                "Unclear if Lamar was invited or deliberately excluded"
            ]
        },
        "general_details": {
            "timeline_markers": ["trip to Mexico (timeframe unspecified)"],
            "location_context": ["Mexico (destination)", "unclear where exclusion/upset occurred"],
            "communication_history": ["no mention of how Lamar found out", "no indication of prior discussion"],
            "emotional_atmosphere": "tense, feelings of betrayal and exclusion"
        },
        "missing_info": [
            "Was Lamar invited to Mexico?",
            "What is the history between these three friends?",
            "How did Lamar find out about the trip?",
            "When did this happen?",
            "Have they discussed this conflict?"
        ]
    }
    mock_client.call_with_tool.return_value = mock_response

    # Create agent with mocked client
    agent = SummaryExtractorAgent(mock_client)

    # Call extract_summary
    raw_summary = "Lamar got really upset because John took Rob to Mexico and they're supposed to be his friends"
    structured_summary = agent.extract_summary(raw_summary)

    # Assert call_with_tool was called correctly
    mock_client.call_with_tool.assert_called_once()
    call_args = mock_client.call_with_tool.call_args

    # Verify the correct prompts and schema were used
    from src.prompts import SUMMARY_EXTRACTOR_SYSTEM
    from src.schemas import SUMMARY_EXTRACTOR_SCHEMA

    assert call_args[0][0] == SUMMARY_EXTRACTOR_SYSTEM
    assert raw_summary in call_args[0][1]  # User prompt should contain raw summary
    assert call_args[0][2] == SUMMARY_EXTRACTOR_SCHEMA

    # Assert returns dict with all required fields
    assert isinstance(structured_summary, dict)
    assert "actors" in structured_summary
    assert "point_of_conflict" in structured_summary
    assert "general_details" in structured_summary
    assert "missing_info" in structured_summary

    # Assert actors are properly structured
    assert len(structured_summary["actors"]) == 3
    assert structured_summary["actors"][0]["name"] == "Lamar"
    assert structured_summary["actors"][0]["role"] == "upset friend"
    assert "John's friend" in structured_summary["actors"][0]["relationships"]
    assert structured_summary["actors"][0]["emotional_state"] == "angry/hurt"

    # Assert conflict structure
    assert structured_summary["point_of_conflict"]["primary"] == "John and Rob went to Mexico together, excluding Lamar"
    assert len(structured_summary["point_of_conflict"]["secondary"]) == 2

    # Assert general details structure
    assert "timeline_markers" in structured_summary["general_details"]
    assert "location_context" in structured_summary["general_details"]
    assert "communication_history" in structured_summary["general_details"]
    assert "emotional_atmosphere" in structured_summary["general_details"]

    # Assert missing_info is a list
    assert isinstance(structured_summary["missing_info"], list)
    assert len(structured_summary["missing_info"]) == 5


def test_extract_summary_with_session_id():
    """Test that extract_summary passes session_id to API client"""
    # Create mock client
    mock_client = Mock(spec=ClaudeClient)

    # Mock call_with_tool to return minimal valid response
    mock_response = {
        "actors": [{"name": "Test", "role": "test", "relationships": [], "emotional_state": "test"}],
        "point_of_conflict": {"primary": "test", "secondary": []},
        "general_details": {
            "timeline_markers": [],
            "location_context": [],
            "communication_history": [],
            "emotional_atmosphere": "test"
        },
        "missing_info": []
    }
    mock_client.call_with_tool.return_value = mock_response

    # Create agent with mocked client
    agent = SummaryExtractorAgent(mock_client)

    # Call extract_summary with session_id
    session_id = "test-session-123"
    agent.extract_summary("test summary", session_id=session_id)

    # Assert session_id was passed to call_with_tool
    call_args = mock_client.call_with_tool.call_args
    assert call_args[1]["session_id"] == session_id


def test_extract_summary_returns_original_response():
    """Test that extract_summary returns the API response unchanged"""
    # Create mock client
    mock_client = Mock(spec=ClaudeClient)

    # Mock call_with_tool to return structured summary
    mock_response = {
        "actors": [
            {
                "name": "Alice",
                "role": "organizer",
                "relationships": ["Bob's colleague"],
                "emotional_state": "stressed"
            }
        ],
        "point_of_conflict": {
            "primary": "Event scheduling conflict",
            "secondary": ["Poor communication"]
        },
        "general_details": {
            "timeline_markers": ["last Friday"],
            "location_context": ["office"],
            "communication_history": ["email exchange"],
            "emotional_atmosphere": "tense"
        },
        "missing_info": ["Who made the final decision?"]
    }
    mock_client.call_with_tool.return_value = mock_response

    # Create agent with mocked client
    agent = SummaryExtractorAgent(mock_client)

    # Call extract_summary
    structured_summary = agent.extract_summary("Some drama happened")

    # Assert returns the exact response from API
    assert structured_summary == mock_response
    assert structured_summary is mock_response  # Should be the same object