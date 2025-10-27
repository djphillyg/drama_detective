from unittest.mock import Mock

from src.agents.drift_detector import DriftDetectorAgent
from src.api_client import ClaudeClient


def test_detect_no_drift():
    # Create mock client
    mock_client = Mock(spec=ClaudeClient)

    # Mock response showing question was addressed
    mock_response = """{
        "addressed_question": true,
        "drift_reason": null,
        "redirect_suggestion": null
    }"""
    mock_client.call.return_value = mock_response

    # Mock extract_json_from_response to return dict
    mock_client.extract_json_from_response.return_value = {
        "addressed_question": True,
        "drift_reason": None,
        "redirect_suggestion": None,
    }

    # Create agent with mocked client
    agent = DriftDetectorAgent(mock_client)

    # Call check_drift with on-topic answer
    question = "What time did Sarah arrive at the party?"
    answer = "She got there around 5:30pm"
    result = agent.check_drift(question, answer)

    # Assert addressed_question is True
    assert result["addressed_question"] is True


def test_detect_drift():
    # Create mock client
    mock_client = Mock(spec=ClaudeClient)

    # Mock response showing drift detected
    mock_response = """{
        "addressed_question": false,
        "drift_reason": "User went on tangent about unrelated past incident",
        "redirect_suggestion": "Let's get back to the party - what time did Sarah actually arrive?"
    }"""
    mock_client.call.return_value = mock_response

    # Mock extract_json_from_response to return dict
    mock_client.extract_json_from_response.return_value = {
        "addressed_question": False,
        "drift_reason": "User went on tangent about unrelated past incident",
        "redirect_suggestion": "Let's get back to the party - what time did Sarah actually arrive?",
    }

    # Create agent with mocked client
    agent = DriftDetectorAgent(mock_client)

    # Call check_drift with off-topic answer
    question = "What time did Sarah arrive at the party?"
    answer = "Well, last year there was this other party where Sarah was late too..."
    result = agent.check_drift(question, answer)

    # Assert addressed_question is False
    assert result["addressed_question"] is False
    # Assert redirect_suggestion is present
    assert "redirect_suggestion" in result
    assert result["redirect_suggestion"] is not None
    assert "party" in result["redirect_suggestion"].lower()
