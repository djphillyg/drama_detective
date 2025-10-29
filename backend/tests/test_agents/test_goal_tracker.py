from unittest.mock import Mock

from src.agents.goal_tracker import GoalTrackerAgent
from src.api_client import ClaudeClient
from src.models import Fact, Goal, GoalStatus


def test_update_goals():
    # Create mock client
    mock_client = Mock(spec=ClaudeClient)

    # Mock response with updated confidence scores
    mock_response = """[
        {
            "goal": "Establish chronological timeline of events",
            "confidence": 75,
            "status": "in_progress",
            "reasoning": "We now have 3 time markers, but missing details about the middle period"
        },
        {
            "goal": "Identify all people involved and their roles",
            "confidence": 85,
            "status": "complete",
            "reasoning": "All major parties identified and their roles are clear"
        }
    ]"""
    mock_client.call.return_value = mock_response

    # Mock extract_json_from_response to return list of goal update dicts
    mock_client.extract_json_from_response.return_value = [
        {
            "goal": "Establish chronological timeline of events",
            "confidence": 75,
            "status": "in_progress",
            "reasoning": "We now have 3 time markers, but missing details about the middle period",
        },
        {
            "goal": "Identify all people involved and their roles",
            "confidence": 85,
            "status": "complete",
            "reasoning": "All major parties identified and their roles are clear",
        },
    ]

    # Create agent with mocked client
    agent = GoalTrackerAgent(mock_client)

    # Create initial goals with low confidence
    initial_goals = [
        Goal(
            description="Establish chronological timeline of events",
            confidence=30,
            status=GoalStatus.IN_PROGRESS,
        ),
        Goal(
            description="Identify all people involved and their roles",
            confidence=50,
            status=GoalStatus.IN_PROGRESS,
        ),
    ]

    # Create new facts that address the goals
    new_facts = [
        Fact(topic="timing", claim="Party started at 5pm", timestamp="5pm"),
        Fact(topic="timing", claim="Sarah arrived at 5:30pm", timestamp="5:30pm"),
        Fact(topic="people", claim="Sarah, John, and Alex were at the party"),
    ]

    # Call update_goals
    updated_goals = agent.update_goals(initial_goals, new_facts)

    # Assert confidence scores updated
    assert updated_goals[0].confidence == 75
    assert updated_goals[1].confidence == 85

    # Assert status updated based on confidence (>= 80 should be complete)
    assert updated_goals[0].status == GoalStatus.IN_PROGRESS
    assert updated_goals[1].status == GoalStatus.COMPLETE
