import json
from src.api_client import ClaudeClient
from src.prompts import FACT_EXTRACTOR_SYSTEM, build_fact_extractor_prompt
from src.models import Fact, Answer


class FactExtractorAgent:
    def __init__(self, client: ClaudeClient):
        # TODO: Store client (or create new one if None)
        self.client = client
        pass

    def extract_facts(self, question: str, answer_obj: Answer) -> list[Fact]:
        """
        Extract facts from a user-selected answer.

        Args:
            question: The question that was asked
            answer_obj: Dict with 'answer' and 'reasoning' keys from Answer model

        Returns:
            List of Fact objects
        """
        # Build user prompt from question + answer object (convert to dict for prompt)
        fact_gen_prompt: str = build_fact_extractor_prompt(question, answer_obj.model_dump())

        # Call Claude API
        response = self.client.call(
            FACT_EXTRACTOR_SYSTEM,
            fact_gen_prompt
        )

        # Parse JSON response
        cleaned_json = self.client.extract_json_from_response(response)

        # Convert fact dicts to Fact objects
        list_facts: list[Fact] = [Fact(**o) for o in cleaned_json]

        return list_facts