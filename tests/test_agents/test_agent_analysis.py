from unittest.mock import Mock

from src.agents.agent_analysis import AnalysisAgent
from src.api_client import ClaudeClient


def test_generate_analysis():
    # Create mock client
    mock_client = Mock(spec=ClaudeClient)

    # Mock response with complete analysis
    mock_response = """{
        "timeline": [
            {"time": "3:00pm", "event": "Sarah agreed to bring dessert"},
            {"time": "5:00pm", "event": "Party started, no cake arrived"},
            {"time": "5:30pm", "event": "Sarah arrived late without dessert"}
        ],
        "key_facts": [
            "Sarah was responsible for bringing dessert",
            "No confirmation was sent in group chat",
            "Alex sent a reminder that wasn't acknowledged",
            "Sarah arrived 30 minutes late"
        ],
        "gaps": [
            "Did Sarah actually see the reminder message?",
            "Was there any prior discussion about backup plans?",
            "Why was Sarah late?"
        ],
        "verdict": {
            "primary_responsibility": "Sarah",
            "percentage": 70,
            "reasoning": "Failed to confirm commitment and didn't communicate issues in advance",
            "contributing_factors": "Group didn't establish backup plan (30%)",
            "drama_rating": 6,
            "drama_rating_explanation": "Moderate - Solvable with honest conversation"
        }
    }"""
    mock_client.call.return_value = mock_response

    # Mock extract_json_from_response to return analysis dict
    mock_client.extract_json_from_response.return_value = {
        "timeline": [
            {"time": "3:00pm", "event": "Sarah agreed to bring dessert"},
            {"time": "5:00pm", "event": "Party started, no cake arrived"},
            {"time": "5:30pm", "event": "Sarah arrived late without dessert"},
        ],
        "key_facts": [
            "Sarah was responsible for bringing dessert",
            "No confirmation was sent in group chat",
            "Alex sent a reminder that wasn't acknowledged",
            "Sarah arrived 30 minutes late",
        ],
        "gaps": [
            "Did Sarah actually see the reminder message?",
            "Was there any prior discussion about backup plans?",
            "Why was Sarah late?",
        ],
        "verdict": {
            "primary_responsibility": "Sarah",
            "percentage": 70,
            "reasoning": "Failed to confirm commitment and didn't communicate issues in advance",
            "contributing_factors": "Group didn't establish backup plan (30%)",
            "drama_rating": 6,
            "drama_rating_explanation": "Moderate - Solvable with honest conversation",
        },
    }

    # Create agent with mocked client
    agent = AnalysisAgent(mock_client)

    # Create session_data dict
    session_data = {
        "incident_name": "The Dessert Disaster",
        "summary": "Sarah didn't bring the dessert to the party",
        "goals": [
            {"description": "Establish chronological timeline of events"},
            {"description": "Identify all people involved"},
        ],
        "facts": [
            {"claim": "Party started at 5pm"},
            {"claim": "Sarah arrived at 5:30pm"},
            {"claim": "Sarah was responsible for dessert"},
        ],
    }

    # Call generate_analysis
    analysis = agent.generate_analysis(session_data)

    # Assert analysis has all required sections
    assert "timeline" in analysis
    assert "key_facts" in analysis
    assert "gaps" in analysis
    assert "verdict" in analysis

    # Assert verdict has drama_rating
    assert "drama_rating" in analysis["verdict"]
    assert analysis["verdict"]["drama_rating"] == 6
    assert "drama_rating_explanation" in analysis["verdict"]

    # Assert timeline is a list
    assert isinstance(analysis["timeline"], list)
    assert len(analysis["timeline"]) == 3

    # Assert key_facts is a list
    assert isinstance(analysis["key_facts"], list)
    assert len(analysis["key_facts"]) > 0

    # Assert verdict has required fields
    assert "primary_responsibility" in analysis["verdict"]
    assert "percentage" in analysis["verdict"]
    assert "reasoning" in analysis["verdict"]
