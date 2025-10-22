import pytest
from unittest.mock import Mock
from src.agents.fact_extractor import FactExtractorAgent
from src.api_client import ClaudeClient
from src.models import Fact

def test_extract_facts():
    # Create mock client
    mock_client = Mock(spec=ClaudeClient)

    # Mock client.call to return a response
    mock_response = '''[
        {
            "topic": "timing",
            "claim": "The party started at 5pm",
            "timestamp": "5pm",
            "confidence": "certain"
        },
        {
            "topic": "attendance",
            "claim": "Sarah arrived 30 minutes late",
            "timestamp": "5:30pm",
            "confidence": "certain"
        }
    ]'''
    mock_client.call.return_value = mock_response

    # Mock extract_json_from_response to return list of fact dicts
    mock_client.extract_json_from_response.return_value = [
        {
            "topic": "timing",
            "claim": "The party started at 5pm",
            "timestamp": "5pm",
            "confidence": "certain"
        },
        {
            "topic": "attendance",
            "claim": "Sarah arrived 30 minutes late",
            "timestamp": "5:30pm",
            "confidence": "certain"
        }
    ]

    # Create agent with mocked client
    agent = FactExtractorAgent(mock_client)

    # Call extract_facts
    question = "What time did the party start and when did Sarah arrive?"
    answer = "The party started at 5pm and Sarah got there around 5:30pm"
    facts = agent.extract_facts(question, answer)

    # Assert returns list of Fact objects with correct data
    assert len(facts) == 2
    assert all(isinstance(fact, Fact) for fact in facts)
    assert facts[0].topic == "timing"
    assert facts[0].claim == "The party started at 5pm"
    assert facts[0].timestamp == "5pm"
    assert facts[0].confidence == "certain"
    assert facts[1].topic == "attendance"
    assert facts[1].claim == "Sarah arrived 30 minutes late"
    assert facts[1].timestamp == "5:30pm"
    assert facts[1].confidence == "certain"