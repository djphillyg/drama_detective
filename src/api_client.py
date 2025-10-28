import json
import re
import time
from typing import Optional, Union

from anthropic import Anthropic
from anthropic.types import TextBlock
from dotenv import load_dotenv

load_dotenv()


class ClaudeClient:
    def __init__(
        self,
        model: str = "claude-3-7-sonnet-latest",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = Anthropic()
        pass

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
        session_id: Optional[str] = None,
    ) -> str:
        last_error: Optional[Exception] = None

        # Add session ID to system prompt to prevent cross-session context bleeding
        if session_id:
            system_prompt = f"[Session: {session_id}]\n\n{system_prompt}"

        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                # Assert first content block is TextBlock and extract text
                content_block = response.content[0]
                assert isinstance(content_block, TextBlock), (
                    f"Expected TextBlock, got {type(content_block).__name__}"
                )
                return content_block.text
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # exponential backoff: 1s, 2s, 4s
                    time.sleep(wait_time)

        # If we've exhausted all retries, raise the last error
        raise Exception(f"Failed after {max_retries} attempts: {last_error}")

    def extract_json_from_response(self, response_text: str) -> Union[dict, list]:
        # Try different patterns in order of preference
        patterns = [
            r"```json\s*(.*?)\s*```",  # Markdown code block with json tag
            r"```\s*(.*?)\s*```",  # Generic code block
            r"\{.*\}",  # JSON object - Check objects before arrays
            r"\[.*\]",  # JSON array
        ]

        for pattern in patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                json_str = match.group(1) if "```" in pattern else match.group(0)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue

        # Include the actual response in the error for debugging
        raise ValueError(
            f"No valid JSON found in response.\n"
            f"Response text (first 500 chars):\n{response_text[:500]}"
        )
