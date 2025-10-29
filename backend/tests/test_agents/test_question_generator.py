from unittest.mock import Mock

from src.agents.question_generator import QuestionGeneratorAgent
from src.api_client import ClaudeClient
from src.models import Fact, Goal, GoalStatus, Message


def test_generate_question():
    # Create mock client
    mock_client = Mock(spec=ClaudeClient)

    # Mock response with new question and answers
    mock_response = """{
        "question": "What time did Sarah arrive at the party?",
        "target_goal": "Establish chronological timeline of events",
        "reasoning": "Timeline has gaps, need to clarify Sarah's arrival time",
        "answers": [
            {
                "answer": "She arrived at 5:30pm",
                "reasoning": "Provides specific timeline information"
            },
            {
                "answer": "She was really late, maybe around 6pm",
                "reasoning": "Shows uncertainty about exact time"
            },
            {
                "answer": "I don't remember exactly",
                "reasoning": "Indicates lack of knowledge"
            },
            {
                "answer": "Who cares when she arrived?",
                "reasoning": "Red herring - indicates drift or defensiveness"
            }
        ]
    }"""
    mock_client.call.return_value = mock_response

    # Mock extract_json_from_response to return dict
    mock_client.extract_json_from_response.return_value = {
        "question": "What time did Sarah arrive at the party?",
        "target_goal": "Establish chronological timeline of events",
        "reasoning": "Timeline has gaps, need to clarify Sarah's arrival time",
        "answers": [
            {
                "answer": "She arrived at 5:30pm",
                "reasoning": "Provides specific timeline information",
            },
            {
                "answer": "She was really late, maybe around 6pm",
                "reasoning": "Shows uncertainty about exact time",
            },
            {
                "answer": "I don't remember exactly",
                "reasoning": "Indicates lack of knowledge",
            },
            {
                "answer": "Who cares when she arrived?",
                "reasoning": "Red herring - indicates drift or defensiveness",
            },
        ],
    }

    # Create agent with mocked client
    agent = QuestionGeneratorAgent(mock_client)

    # Create low-confidence goals
    goals = [
        Goal(
            description="Establish chronological timeline of events",
            confidence=30,
            status=GoalStatus.IN_PROGRESS,
        ),
        Goal(
            description="Identify all people involved",
            confidence=60,
            status=GoalStatus.IN_PROGRESS,
        ),
    ]
    facts = [Fact(topic="timing", claim="Party started at 5pm", timestamp="5pm")]
    messages = [
        Message(
            role="assistant",
            content="Tell me about the party",
            timestamp="2025-01-01T12:00:00",
        )
    ]

    # Call generate_question_with_answers
    result = agent.generate_question_with_answers(goals, facts, messages)

    # Assert returns question dict with target_goal and answers
    assert "question" in result
    assert "target_goal" in result
    assert "answers" in result
    assert result["target_goal"] == "Establish chronological timeline of events"
    assert len(result["answers"]) == 4


def test_generate_wrap_up_when_goals_complete():
    # Create mock client
    mock_client = Mock(spec=ClaudeClient)

    # Mock response with wrap-up question
    mock_response = """{
        "question": "Is there anything else you'd like to add about what happened?",
        "target_goal": "wrap_up",
        "reasoning": "All goals above 80% confidence, wrapping up the interview",
        "answers": [
            {
                "answer": "No, I think that covers everything",
                "reasoning": "Indicates completion"
            },
            {
                "answer": "Actually, there's one more thing...",
                "reasoning": "Provides opportunity for additional information"
            },
            {
                "answer": "I want to clarify something I said earlier",
                "reasoning": "Allows for corrections"
            },
            {
                "answer": "That's all I know",
                "reasoning": "Confirms no additional information"
            }
        ]
    }"""
    mock_client.call.return_value = mock_response

    # Mock extract_json_from_response to return dict
    mock_client.extract_json_from_response.return_value = {
        "question": "Is there anything else you'd like to add about what happened?",
        "target_goal": "wrap_up",
        "reasoning": "All goals above 80% confidence, wrapping up the interview",
        "answers": [
            {
                "answer": "No, I think that covers everything",
                "reasoning": "Indicates completion",
            },
            {
                "answer": "Actually, there's one more thing...",
                "reasoning": "Provides opportunity for additional information",
            },
            {
                "answer": "I want to clarify something I said earlier",
                "reasoning": "Allows for corrections",
            },
            {
                "answer": "That's all I know",
                "reasoning": "Confirms no additional information",
            },
        ],
    }

    # Create agent with mocked client
    agent = QuestionGeneratorAgent(mock_client)

    # Create high-confidence goals
    goals = [
        Goal(
            description="Establish chronological timeline of events",
            confidence=85,
            status=GoalStatus.COMPLETE,
        ),
        Goal(
            description="Identify all people involved",
            confidence=90,
            status=GoalStatus.COMPLETE,
        ),
    ]
    facts = [
        Fact(topic="timing", claim="Party started at 5pm", timestamp="5pm"),
        Fact(topic="timing", claim="Sarah arrived at 5:30pm", timestamp="5:30pm"),
    ]
    messages = [
        Message(
            role="assistant",
            content="Tell me about the party",
            timestamp="2025-01-01T12:00:00",
        )
    ]

    # Call generate_question_with_answers
    result = agent.generate_question_with_answers(goals, facts, messages)

    # Assert target_goal == "wrap_up"
    assert result["target_goal"] == "wrap_up"
