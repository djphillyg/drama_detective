from typing import Optional

from ..api_client import ClaudeClient
from ..models import Answer, Fact
from ..prompts import FACT_EXTRACTOR_SYSTEM, build_fact_extractor_prompt
from ..schemas import FACT_EXTRACTOR_SCHEMA


class FactExtractorAgent:
    def __init__(self, client: ClaudeClient):
        # TODO: Store client (or create new one if None)
        self.client = client
        pass

    def extract_facts(
        self, question: str, answer_obj: Answer, session_id: Optional[str] = None
    ) -> list[Fact]:
        """
        Extract facts from a user-selected answer.

        Args:
            question: The question that was asked
            answer_obj: Dict with 'answer' and 'reasoning' keys from Answer model
            session_id: Optional session ID for context isolation

        Returns:
            List of Fact objects
        """
        # Build user prompt from question + answer object (convert to dict for prompt)
        fact_gen_prompt: str = build_fact_extractor_prompt(
            question, answer_obj.model_dump()
        )

        # Call Claude API with tool schema enforcement
        response = self.client.call_with_tool(
            FACT_EXTRACTOR_SYSTEM,
            fact_gen_prompt,
            FACT_EXTRACTOR_SCHEMA,
            session_id=session_id,
            use_cache=True
        )

        # Schema guarantees response["facts"] is a list of valid fact dicts
        facts_list = response["facts"]

        # Convert fact dicts to Fact objects
        list_facts: list[Fact] = [Fact(**fact_dict) for fact_dict in facts_list]

        return list_facts
