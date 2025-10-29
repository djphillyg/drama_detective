from unittest.mock import Mock

from src.agents.goal_generator import GoalGeneratorAgent
from src.api_client import ClaudeClient
from src.models import Goal


def test_generate_goals():
    # Create mock client
    mock_client = Mock(spec=ClaudeClient)

    # Mock client.call to return a response
    mock_response = '["Find out who started the rumor", "Discover the timeline of events", "Identify key witnesses"]'
    mock_client.call.return_value = mock_response

    # Mock extract_json_from_response to return list of goal descriptions
    mock_client.extract_json_from_response.return_value = [
        "Find out who started the rumor",
        "Discover the timeline of events",
        "Identify key witnesses",
    ]

    # Create agent with mocked client
    agent = GoalGeneratorAgent(mock_client)

    # Call generate_goals
    summary = "There's drama about a leaked secret"
    goals = agent.generate_goals(summary)

    # Assert returns list of Goal objects with correct descriptions
    assert len(goals) == 3
    assert all(isinstance(goal, Goal) for goal in goals)
    assert goals[0].description == "Find out who started the rumor"
    assert goals[1].description == "Discover the timeline of events"
    assert goals[2].description == "Identify key witnesses"
    assert all(goal.status.value == "not_started" for goal in goals)
