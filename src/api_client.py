import json
import re
import time
from typing import Optional, Union

from anthropic import Anthropic
from anthropic.types import TextBlock, ToolUseBlock
from dotenv import load_dotenv

load_dotenv()


class ClaudeClient:
    def __init__(
        self,
        model: str = "claude-sonnet-4-5-20250929",
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
        use_cache: bool = False,
    ) -> str:
        last_error: Optional[Exception] = None

        # Add session ID to system prompt to prevent cross-session context bleeding
        if session_id:
            system_prompt = f"[Session: {session_id}]\n\n{system_prompt}"

        for attempt in range(max_retries):
            try:
                # Format system prompt with cache control if enabled
                if use_cache:
                    system = [
                        {
                            "type": "text",
                            "text": system_prompt,
                            "cache_control": {"type": "ephemeral"}
                        }
                    ]
                else:
                    system = system_prompt

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system, # type: ignore
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

    def call_with_tool(
        self,
        system_prompt: str,
        user_prompt: str,
        tool_schema: dict,
        max_retries: int = 3,
        session_id: Optional[str] = None,
        use_cache: bool = False,
    ) -> dict:
        """
        Call Claude API with tool calling to enforce JSON schema.

        Args:
            system_prompt: System instructions for the model
            user_prompt: User prompt to process
            tool_schema: JSON schema defining the expected tool structure
            max_retries: Number of retry attempts on failure
            session_id: Optional session ID to prevent context bleeding
            use_cache: Whether to use prompt caching for system prompt

        Returns:
            Dictionary matching the tool schema (guaranteed valid structure)

        Raises:
            Exception: If all retries fail
            ValueError: If response doesn't contain tool_use block
        """
        last_error: Optional[Exception] = None

        # Add session ID to system prompt if provided
        if session_id:
            system_prompt = f"[Session: {session_id}]\n\n{system_prompt}"

        # Format system prompt with cache control if enabled
        if use_cache:
            system = [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ]
        else:
            system = system_prompt

        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system,  # type: ignore
                    messages=[{"role": "user", "content": user_prompt}],
                    tools=[tool_schema],  # Provide the tool schema # type: ignore
                    tool_choice={"type": "tool", "name": tool_schema["name"]}  # Force tool use
                )

                # Extract tool use from response
                for block in response.content:
                    if block.type == "tool_use":
                        assert isinstance(block, ToolUseBlock), (
                            f"Expected ToolUseBlock, got {type(block).__name__}"
                        )
                        # block.input is guaranteed to match the schema
                        return block.input  # type: ignore

                raise ValueError("No tool_use block found in response")

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
