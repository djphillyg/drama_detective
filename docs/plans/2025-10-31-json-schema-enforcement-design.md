# JSON Schema Enforcement Design

**Date:** 2025-10-31
**Status:** Approved
**Problem:** Question generator returning malformed JSON after adding interviewee context

## Problem Summary

The Drama Detective system uses 6 LLM agents that return JSON responses. Previously, JSON extraction relied on regex parsing of free-form text responses. After adding interviewee context to the question generator prompt (lines 458-480 in `prompts.py`), the model consistently returns malformed JSON structures.

**Root Cause:**
- No structured output enforcement at API level
- Reliance on prompt instructions ("Return only the JSON object, no additional text")
- Complex prompts reduce model's ability to maintain format discipline
- Regex parsing (`extract_json_from_response`) cannot fix structurally broken JSON

## Solution: Tool-Based JSON Schema Enforcement

Use Anthropic's tool calling feature to enforce JSON schemas at the API level. Instead of hoping the model formats text correctly, we define exact schemas as "tools" that the model must use to return data.

### Architecture Changes

#### Before
```
LLM API → Free text response → Regex extraction → Hope it's valid JSON → Parse
```

#### After
```
LLM API (with tool schema) → Tool use response → Guaranteed valid JSON
```

## Implementation Plan

### 1. Create Schema Definitions (`src/schemas.py`)

Define JSON schemas for all 6 agents:

#### Goal Generator Schema
```python
GOAL_GENERATOR_SCHEMA = {
    "name": "generate_investigation_goals",
    "description": "Generate 5-7 specific investigation goals for a drama incident",
    "input_schema": {
        "type": "object",
        "properties": {
            "goals": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 5,
                "maxItems": 7
            }
        },
        "required": ["goals"]
    }
}
```

#### Fact Extractor Schema
```python
FACT_EXTRACTOR_SCHEMA = {
    "name": "extract_facts",
    "description": "Extract concrete facts from interview answer",
    "input_schema": {
        "type": "object",
        "properties": {
            "facts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "claim": {"type": "string"},
                        "timestamp": {"type": "string"},
                        "confidence": {"type": "string", "enum": ["certain", "uncertain"]}
                    },
                    "required": ["topic", "claim", "timestamp", "confidence"]
                }
            }
        },
        "required": ["facts"]
    }
}
```

#### Drift Detector Schema
```python
DRIFT_DETECTOR_SCHEMA = {
    "name": "detect_answer_drift",
    "description": "Determine if user's answer addressed the question",
    "input_schema": {
        "type": "object",
        "properties": {
            "addressed_question": {"type": "boolean"},
            "drift_reason": {"type": "string"},
            "redirect_suggestion": {"type": "string"}
        },
        "required": ["addressed_question", "drift_reason", "redirect_suggestion"]
    }
}
```

#### Goal Tracker Schema
```python
GOAL_TRACKER_SCHEMA = {
    "name": "update_goal_progress",
    "description": "Update investigation goal confidence scores",
    "input_schema": {
        "type": "object",
        "properties": {
            "goal_updates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "goal": {"type": "string"},
                        "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
                        "status": {"type": "string", "enum": ["not_started", "in_progress", "complete"]},
                        "reasoning": {"type": "string"}
                    },
                    "required": ["goal", "confidence", "status", "reasoning"]
                }
            }
        },
        "required": ["goal_updates"]
    }
}
```

#### Question Generator Schema
```python
QUESTION_WITH_ANSWERS_SCHEMA = {
    "name": "generate_question_with_answers",
    "description": "Generate interview question with multiple choice answers",
    "input_schema": {
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "target_goal": {"type": "string"},
            "reasoning": {"type": "string"},
            "answers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "answer": {"type": "string"},
                        "reasoning": {"type": "string"}
                    },
                    "required": ["answer", "reasoning"]
                },
                "minItems": 4,
                "maxItems": 4
            }
        },
        "required": ["question", "target_goal", "reasoning", "answers"]
    }
}
```

#### Analysis Schema
```python
ANALYSIS_SCHEMA = {
    "name": "generate_analysis_report",
    "description": "Generate comprehensive drama incident analysis",
    "input_schema": {
        "type": "object",
        "properties": {
            "timeline": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "time": {"type": "string"},
                        "event": {"type": "string"}
                    },
                    "required": ["time", "event"]
                }
            },
            "key_facts": {
                "type": "array",
                "items": {"type": "string"}
            },
            "gaps": {
                "type": "array",
                "items": {"type": "string"}
            },
            "verdict": {
                "type": "object",
                "properties": {
                    "primary_responsibility": {"type": "string"},
                    "percentage": {"type": "integer", "minimum": 0, "maximum": 100},
                    "reasoning": {"type": "string"},
                    "contributing_factors": {"type": "string"},
                    "drama_rating": {"type": "integer", "minimum": 1, "maximum": 10},
                    "drama_rating_explanation": {"type": "string"}
                },
                "required": ["primary_responsibility", "percentage", "reasoning", "contributing_factors", "drama_rating", "drama_rating_explanation"]
            }
        },
        "required": ["timeline", "key_facts", "gaps", "verdict"]
    }
}
```

**Schema Features:**
- Exact field names (typos impossible)
- Type validation (string, integer, boolean enforced)
- Enum constraints (confidence values, status values)
- Range validation (confidence 0-100, drama_rating 1-10)
- Array size limits (5-7 goals, exactly 4 answers)

### 2. Add Tool-Based API Method (`src/api_client.py`)

Add new method to `ClaudeClient`:

```python
from anthropic.types import ToolUseBlock

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
    Returns the tool use input directly (guaranteed to match schema).
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
                tools=[tool_schema],  # Provide the tool schema
                tool_choice={"type": "tool", "name": tool_schema["name"]}  # Force tool use
            )

            # Extract tool use from response
            for block in response.content:
                if block.type == "tool_use":
                    assert isinstance(block, ToolUseBlock)
                    return block.input  # Guaranteed valid JSON matching schema

            raise ValueError("No tool_use block found in response")

        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # exponential backoff
                time.sleep(wait_time)

    raise Exception(f"Failed after {max_retries} attempts: {last_error}")
```

**Key Parameters:**
- `tools=[tool_schema]` - Provides schema definition to API
- `tool_choice={"type": "tool", "name": "..."}` - Forces model to use the tool (not optional)
- `block.input` - Direct JSON extraction, guaranteed to match schema

### 3. Update All Agent Classes

Each agent's generation method follows this pattern:

```python
from src.schemas import RELEVANT_SCHEMA

class AgentName:
    def generate_method(self, ...):
        # Build prompt as before
        user_prompt = build_prompt(...)

        # Call with tool schema enforcement
        response = self.client.call_with_tool(
            SYSTEM_PROMPT,
            user_prompt,
            RELEVANT_SCHEMA,
            session_id=session_id,
            use_cache=True
        )

        # Extract relevant data (schema guarantees structure)
        return response  # or response["key"] depending on schema
```

**Agents to Update:**
1. `GoalGeneratorAgent` → `generate_goals()` → returns `response["goals"]`
2. `FactExtractorAgent` → `extract_facts()` → returns `response["facts"]`
3. `DriftDetectorAgent` → `detect_drift()` → returns full `response` dict
4. `GoalTrackerAgent` → `update_goals()` → returns `response["goal_updates"]`
5. `QuestionGeneratorAgent` → `generate_question_with_answers()` → returns full `response` dict
6. `AnalysisAgent` → `generate_analysis()` → returns full `response` dict

**Removed from all agents:**
- `self.client.extract_json_from_response()` calls
- Type assertions (`assert isinstance(...)`)
- Manual JSON validation

### 4. Simplify System Prompts

Update each system prompt in `src/prompts.py`:

**Remove:**
- "Output format: Return JSON..."
- Example JSON outputs
- "Return only the JSON, no additional text"

**Add:**
- Single line: "Use the '[tool_name]' tool to return your response."

**Keep:**
- All behavioral guidelines (what to generate, not how to format)

Example for Question Generator:

```python
QUESTION_WITH_ANSWERS_SYSTEM = """You are a question and answer generation agent in the Drama Detective system.
Your job: Generate the next best interview question based on investigation state, along with 4 multiple choice answer options.

Use the 'generate_question_with_answers' tool to return your structured response.

Guidelines for question generation:
- Prioritize goals with lowest confidence scores
- Do not hallucinate new people that have not been established
- Reference previous answers to create natural conversation flow
[... rest of guidelines ...]
"""
```

## Benefits

### Reliability
- ✅ Zero malformed JSON - API enforces structure
- ✅ Zero regex parsing failures
- ✅ Prompt complexity doesn't affect output format
- ✅ Interviewee context safe to add/modify

### Type Safety
- ✅ Field names guaranteed (no typos)
- ✅ Data types enforced (int, string, bool)
- ✅ Enum values validated
- ✅ Ranges enforced (0-100 confidence, 1-10 ratings)

### Developer Experience
- ✅ Clear API errors when model can't comply
- ✅ No silent JSON corruption
- ✅ Same retry logic with exponential backoff
- ✅ Cleaner agent code (remove validation boilerplate)

## Migration Strategy

1. Create `src/schemas.py` with all 6 schemas
2. Add `call_with_tool()` method to `ClaudeClient`
3. Update all 6 agent classes one by one
4. Simplify system prompts after agents updated
5. Keep `extract_json_from_response()` for backward compatibility (can remove later)

## Testing Recommendations

- Test each agent individually after migration
- Verify schemas with intentionally complex prompts (like interviewee context)
- Validate that retry logic works (test with temporary API errors)
- Check that all downstream code handles the new response structure

## Future Considerations

- Consider using Pydantic models to validate schemas at runtime
- Could auto-generate schemas from existing model classes
- Tool calling adds ~50-100ms latency vs. text completion (acceptable tradeoff for reliability)