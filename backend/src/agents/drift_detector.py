from typing import Optional

from ..api_client import ClaudeClient
from ..models import DriftAnalysis
from ..prompts import DRIFT_DETECTOR_SYSTEM, build_drift_detector_prompt
from ..schemas import DRIFT_DETECTOR_SCHEMA


class DriftDetectorAgent:
    def __init__(self, client: ClaudeClient):
        self.client = client

    def check_drift(
        self, question: str, answer: str, session_id: Optional[str] = None
    ) -> DriftAnalysis:
        """
        Check if an answer addressed the question asked.

        Args:
            question: The question that was asked
            answer: The user's answer
            session_id: Optional session ID for context isolation

        Returns:
            DriftAnalysis model with addressed_question, drift_reason, redirect_suggestion
        """
        # Build user prompt
        user_prompt = build_drift_detector_prompt(question, answer)

        # Call Claude API with tool schema enforcement
        response = self.client.call_with_tool(
            DRIFT_DETECTOR_SYSTEM,
            user_prompt,
            DRIFT_DETECTOR_SCHEMA,
            session_id=session_id,
            use_cache=True
        )

        # Convert dict response to DriftAnalysis Pydantic model
        return DriftAnalysis.model_validate(response)
