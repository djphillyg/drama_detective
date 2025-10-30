# Drama Summary Extractor Design

**Date:** 2025-10-29
**Status:** Approved
**Author:** Brainstorming Session

## Overview

A preprocessing layer that transforms raw user drama descriptions into structured, investigation-ready data before goal generation. This replaces the current direct-to-goal-generator approach with a two-stage pipeline that improves investigation accuracy through comprehensive conflict detection and actor profiling.

## Problem Statement

Currently, the goal generator receives unstructured user summaries, which limits its ability to:
- Generate actor-specific investigation goals
- Distinguish between primary and secondary conflicts
- Account for relationship dynamics and emotional states
- Handle incomplete or vague descriptions systematically

## Solution: Structured Summary Extraction

### Pipeline Architecture

**Current Flow:**
```
User Summary → GOAL_GENERATOR_SYSTEM → Questions
```

**New Flow:**
```
User Summary → SUMMARY_EXTRACTOR_SYSTEM → Structured Data → GOAL_GENERATOR_SYSTEM → Questions
```

### Output Data Structure

```json
{
  "actors": [
    {
      "name": "string",
      "role": "string (role in the drama)",
      "relationships": ["array of relationship descriptions"],
      "emotional_state": "string (current emotional condition)"
    }
  ],
  "point_of_conflict": {
    "primary": "string (main conflict description)",
    "secondary": ["array of contributing issues"]
  },
  "general_details": {
    "timeline_markers": ["array of time references"],
    "location_context": ["array of places/spaces where drama occurred"],
    "communication_history": ["array of what was/wasn't said"],
    "emotional_atmosphere": "string (overall mood/tension level)"
  },
  "missing_info": ["array of what's unclear and needs clarification"]
}
```

## Implementation Components

### 1. System Prompt: `SUMMARY_EXTRACTOR_SYSTEM`

**Purpose:** Instruct LLM to parse drama descriptions into structured format

**Key Instructions:**
- Extract all mentioned actors with full profile details
- Identify explicit and implicit conflicts
- Detect emotional indicators and relationship dynamics
- Surface communication patterns and gaps
- Flag missing or unclear information

**Conflict Detection Strategy:**
The prompt instructs thorough analysis of:
- Explicit conflicts (arguments, betrayals, breakups)
- Implicit tensions (unmet expectations, boundary violations)
- Emotional indicators (upset, angry, hurt, confused)
- Power dynamics and relationship imbalances
- Passive-aggressive or avoidant patterns

**Output Requirements:**
- Must return valid JSON with all four top-level fields
- Actors array cannot be empty (at minimum, extract "unknown person")
- Missing_info field helps identify gaps for follow-up
- Uses "Request clarification" approach: extract what's explicit, flag what's missing

### 2. Prompt Builder Function

```python
def build_summary_extractor_prompt(raw_summary: str) -> str:
    """
    Build prompt for extracting structured data from raw drama summary.

    Args:
        raw_summary: User's free-form description of the drama

    Returns:
        Formatted prompt ready for LLM API call
    """
```

Simple wrapper that formats the raw summary for the extraction system prompt.

### 3. API Client Method

```python
def extract_summary_structure(raw_summary: str) -> dict:
    """
    Call LLM to extract structured data from raw summary.

    Args:
        raw_summary: User's drama description

    Returns:
        Dict with actors, point_of_conflict, general_details, missing_info
    """
```

Makes API call with `SUMMARY_EXTRACTOR_SYSTEM` and parses JSON response.

### 4. Modified Goal Generator

Update `build_goal_generator_prompt()` to accept structured extraction output instead of raw summary:

```python
def build_goal_generator_prompt(structured_summary: dict) -> str:
    """
    Generate investigation goals from structured drama data.

    Args:
        structured_summary: Output from summary extractor with actors,
                          conflicts, and context

    Returns:
        Prompt for goal generation with enriched context
    """
```

**Benefits:**
- Can generate actor-specific goals (e.g., "Understand Sarah's perspective on the cake incident")
- Can target primary vs secondary conflicts separately
- Can reference relationship dynamics in goal phrasing
- Can incorporate missing_info to generate clarifying goals

## Future-Proofing: Multimodal Input

### Vision Capability Integration

The structured extraction design supports future screenshot analysis with minimal changes:

**Unified Normalization Layer:**
Regardless of input type (text, screenshots, or both), the output structure remains identical. This makes the extractor a **format-agnostic normalization layer**.

**Implementation Approach:**

```python
def extract_summary_structure(text_summary=None, screenshots=None):
    """
    Extract structured drama data from text, images, or both.

    Args:
        text_summary: Optional user-provided text description
        screenshots: Optional array of group chat screenshot images

    Returns:
        Same structured dict regardless of input type
    """
```

**Vision-Specific Enhancements:**
When processing screenshots, additional instructions would guide extraction of:
- Exact quotes from visible messages
- Timestamps from message headers
- Participant identification from names/avatars
- Tone indicators from emoji, punctuation, typing patterns
- Emotional signals from read receipts and reactions

**Architectural Benefit:**
The goal generator and downstream systems remain unchanged - they always receive the same structured format whether the drama was described in text or shown in screenshots.

## Integration Points

### New Files to Create
- Add `SUMMARY_EXTRACTOR_SYSTEM` constant to `backend/src/prompts.py`
- Add `build_summary_extractor_prompt()` to `backend/src/prompts.py`
- Add `extract_summary_structure()` to `backend/src/api_client.py`

### Files to Modify
- `backend/src/prompts.py`: Update `build_goal_generator_prompt()` signature and implementation
- `backend/src/api_client.py`: Update goal generation flow to call extractor first
- API routes that handle new investigation creation: Insert extraction step before goal generation

## Success Criteria

1. **Accuracy:** Structured extraction correctly identifies all actors, primary conflict, and key details from test cases
2. **Completeness:** Missing_info field accurately flags gaps in vague summaries
3. **Goal Quality:** Goals generated from structured data are more specific and targeted than current baseline
4. **Future-Ready:** Architecture supports adding screenshot input without changing downstream systems

## Example Transformation

### Input (Raw Summary)
```
"Lamar got really upset because John took Rob to Mexico and they're supposed to be his friends"
```

### Output (Structured)
```json
{
  "actors": [
    {
      "name": "Lamar",
      "role": "upset friend",
      "relationships": ["John's friend", "Rob's friend"],
      "emotional_state": "angry/hurt"
    },
    {
      "name": "John",
      "role": "trip organizer",
      "relationships": ["Lamar's friend", "Rob's travel companion"],
      "emotional_state": "unclear"
    },
    {
      "name": "Rob",
      "role": "trip participant",
      "relationships": ["Lamar's friend", "John's travel companion"],
      "emotional_state": "unclear"
    }
  ],
  "point_of_conflict": {
    "primary": "John and Rob went to Mexico together, excluding Lamar",
    "secondary": [
      "Lamar feels betrayed by friends",
      "Unclear if Lamar was invited or deliberately excluded"
    ]
  },
  "general_details": {
    "timeline_markers": ["trip to Mexico (timeframe unspecified)"],
    "location_context": ["Mexico (destination)", "unclear where exclusion/upset occurred"],
    "communication_history": ["no mention of how Lamar found out", "no indication of prior discussion"],
    "emotional_atmosphere": "tense, feelings of betrayal and exclusion"
  },
  "missing_info": [
    "Was Lamar invited to Mexico?",
    "What is the history between these three friends?",
    "How did Lamar find out about the trip?",
    "When did this happen?",
    "Have they discussed this conflict?"
  ]
}
```

### Result: Better Goals
With this structured input, the goal generator can produce:
- "Understand why John and Rob chose to travel together without including Lamar"
- "Clarify whether Lamar was invited to Mexico or deliberately excluded"
- "Establish the relationship history between Lamar, John, and Rob"
- "Determine how and when Lamar discovered the Mexico trip"
- "Assess each person's current emotional state and openness to resolution"

Compared to generic goals from the raw summary.

## Next Steps

1. Implement `SUMMARY_EXTRACTOR_SYSTEM` prompt with examples
2. Create `build_summary_extractor_prompt()` function
3. Add `extract_summary_structure()` to API client
4. Update `build_goal_generator_prompt()` to accept structured input
5. Modify investigation creation flow to insert extraction step
6. Test with diverse drama scenarios (friendship, romantic, group dynamics)
7. Validate that missing_info field correctly identifies gaps
