import json
from src.api_client import ClaudeClient
from src.prompts import FACT_EXTRACTOR_SYSTEM, build_fact_extractor_prompt
from src.models import Fact


class FactExtractorAgent:
    def __init__(self, client: ClaudeClient):
        # TODO: Store client (or create new one if None)
        self.client = client
        pass

    def extract_facts(self, question: str, answer: str) -> list[Fact]:
        # TODO: Build user prompt from question + answer
        # Call Claude API
        # Parse JSON response (handle extra text)
        # Convert fact dicts to Fact objects
        # Return list of Fact objects
        fact_gen_prompt: str = build_fact_extractor_prompt(question, answer)
        response = self.client.call(
            FACT_EXTRACTOR_SYSTEM,
            fact_gen_prompt
        )
        cleaned_json = self.client.extract_json_from_response(response)
        list_facts: list[Fact] = [Fact(**o) for o in cleaned_json]
        return list_facts