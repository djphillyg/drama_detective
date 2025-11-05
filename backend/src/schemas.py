"""
JSON schemas for tool-based LLM agent responses.

These schemas enforce strict JSON structure at the API level using Anthropic's
tool calling feature. Each schema defines the exact format that an agent must
return, preventing malformed JSON and ensuring type safety.
"""

# Goal Generator Schema
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

# Fact Extractor Schema
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

# Drift Detector Schema
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

# Goal Tracker Schema
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

# Question Generator Schema
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

# Summary Extractor Schema
SUMMARY_EXTRACTOR_SCHEMA = {
    "name": "extract_summary_structure",
    "description": "Extract structured data from raw drama summary",
    "input_schema": {
        "type": "object",
        "properties": {
            "actors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "role": {"type": "string"},
                        "relationships": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "emotional_state": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["name", "role", "relationships", "emotional_state"]
                }
            },
            "point_of_conflict": {
                "type": "object",
                "properties": {
                    "primary": {"type": "string"},
                    "secondary": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["primary", "secondary"]
            },
            "general_details": {
                "type": "object",
                "properties": {
                    "timeline_markers": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "location_context": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "communication_history": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "emotional_atmosphere": {"type": "string"}
                },
                "required": ["timeline_markers", "location_context", "communication_history", "emotional_atmosphere"]
            },
            "missing_info": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["actors", "point_of_conflict", "general_details", "missing_info"]
    }
}

# Analysis Schema
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