from typing import Optional

from src.api_client import ClaudeClient
from src.prompts import DRIFT_DETECTOR_SYSTEM, build_drift_detector_prompt
from src.schemas import DRIFT_DETECTOR_SCHEMA


class DriftDetectorAgent:
    def __init__(self, client: ClaudeClient):
        self.client = client

    def check_drift(
        self, question: str, answer: str, session_id: Optional[str] = None
    ) -> dict:
        # Build user prompt
        user_prompt = build_drift_detector_prompt(question, answer)

        # Call Claude API with tool schema enforcement
        drift_analysis = self.client.call_with_tool(
            DRIFT_DETECTOR_SYSTEM,
            user_prompt,
            DRIFT_DETECTOR_SCHEMA,
            session_id=session_id
        )

        # Schema guarantees valid dict structure
        return drift_analysis
