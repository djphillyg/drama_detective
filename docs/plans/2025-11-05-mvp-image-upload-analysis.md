# MVP Image Upload & Analysis Page Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add screenshot upload capability alongside text input, create structured analysis page, and polish UI for 3-hour MVP deadline.

**Architecture:** Extend Claude API client with vision support, modify existing summary extractor to process images+text, build new analysis page with structured sections, apply theme polish inspired by known.design.

**Tech Stack:** Python (Flask, Anthropic SDK), TypeScript/React (Next.js 14, Redux Toolkit, Tailwind CSS, shadcn/ui)

---

## Overview

This plan implements 4 core features in priority order:
1. **Backend Image Support** - Extend API to accept images, add vision processing
2. **Frontend Image Upload** - Add file upload UI to deets page
3. **Analysis Page** - Create structured results page with share functionality
4. **Polish & Testing** - Theme improvements and loading animations

**Critical Path:** Backend image support → Frontend upload → Analysis page → Polish

**Estimated Time:** 3 hours (4 phases × 45min avg)

---

## Phase 1: Backend Image Support (1 hour)

### Task 1.1: Add Vision Support to ClaudeClient

**Files:**
- Modify: `backend/src/api_client.py:1-86`

**Goal:** Extend `ClaudeClient` class to support image content blocks for vision API.

**Step 1: Add call_with_images method**

Add this method to `ClaudeClient` class after the `extract_json_from_response` method:

```python
def call_with_images(
    self,
    system_prompt: str,
    text_prompt: str,
    image_data_list: list[dict],  # [{"data": base64_str, "media_type": "image/jpeg"}, ...]
    max_retries: int = 3,
    session_id: Optional[str] = None,
) -> str:
    """
    Call Claude API with text and images for vision processing.

    Args:
        system_prompt: System instruction
        text_prompt: Text portion of user message
        image_data_list: List of dicts with 'data' (base64) and 'media_type' keys
        max_retries: Number of retry attempts
        session_id: Optional session ID for caching

    Returns:
        Response text from Claude
    """
    last_error: Optional[Exception] = None

    # Add session ID to system prompt
    if session_id:
        system_prompt = f"[Session: {session_id}]\n\n{system_prompt}"

    # Build content array with text + images
    content = []

    # Add images first
    for img in image_data_list:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": img["media_type"],
                "data": img["data"]
            }
        })

    # Add text prompt
    content.append({
        "type": "text",
        "text": text_prompt
    })

    for attempt in range(max_retries):
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": content}],
            )
            # Extract text from response
            content_block = response.content[0]
            assert isinstance(content_block, TextBlock), (
                f"Expected TextBlock, got {type(content_block).__name__}"
            )
            return content_block.text
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                time.sleep(wait_time)

    raise Exception(f"Failed after {max_retries} attempts: {last_error}")
```

**Step 2: Add call_with_tool_and_images method**

Add this method after `call_with_images`:

```python
def call_with_tool_and_images(
    self,
    system_prompt: str,
    text_prompt: str,
    tool_schema: dict,
    image_data_list: list[dict] = None,
    max_retries: int = 3,
    session_id: Optional[str] = None,
    use_cache: bool = False
) -> dict:
    """
    Call Claude API with tool use (structured output) and optional images.

    Args:
        system_prompt: System instruction
        text_prompt: Text portion of user message
        tool_schema: JSON schema for tool use
        image_data_list: Optional list of image dicts
        max_retries: Number of retry attempts
        session_id: Optional session ID
        use_cache: Whether to use prompt caching

    Returns:
        Structured dict extracted from tool use
    """
    last_error: Optional[Exception] = None

    # Add session ID to system prompt
    if session_id:
        system_prompt = f"[Session: {session_id}]\n\n{system_prompt}"

    # Build content array
    content = []

    # Add images if present
    if image_data_list:
        for img in image_data_list:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img["media_type"],
                    "data": img["data"]
                }
            })

    # Add text prompt
    content.append({
        "type": "text",
        "text": text_prompt
    })

    # Prepare system with caching if requested
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
                system=system,
                messages=[{"role": "user", "content": content}],
                tools=[tool_schema]
            )

            # Extract tool use from response
            for block in response.content:
                if block.type == "tool_use":
                    return block.input  # This is already a dict

            # If no tool use found, raise error
            raise ValueError("No tool use found in response")

        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                time.sleep(wait_time)

    raise Exception(f"Failed after {max_retries} attempts: {last_error}")
```

**Step 3: Verify imports**

Ensure these imports exist at the top of `backend/src/api_client.py`:

```python
import json
import re
import time
from typing import Optional, Union

from anthropic import Anthropic
from anthropic.types import TextBlock
from dotenv import load_dotenv
```

**No test needed yet** - we'll test integration in Task 1.3

**Step 4: Commit**

```bash
git add backend/src/api_client.py
git commit -m "feat: add vision API support to ClaudeClient

- Add call_with_images() for vision processing
- Add call_with_tool_and_images() for structured vision output
- Support base64 image content blocks
- Maintain retry logic and session isolation"
```

---

### Task 1.2: Update Summary Extractor for Images

**Files:**
- Modify: `src/agents/summary_extractor.py:1-47`

**Goal:** Extend `SummaryExtractorAgent` to process images alongside text.

**Step 1: Update extract_summary method signature**

Replace the current `extract_summary` method in `src/agents/summary_extractor.py`:

```python
def extract_summary(
    self,
    raw_summary: str = None,
    image_data_list: list[dict] = None,
    session_id: Optional[str] = None
) -> dict:
    """
    Extract structured data from raw drama summary (text and/or images).

    Args:
        raw_summary: Optional user's free-form text description
        image_data_list: Optional list of image dicts with 'data' and 'media_type'
        session_id: Optional session ID for caching

    Returns:
        Dict with actors, point_of_conflict, general_details, missing_info
    """
    # Validate at least one input provided
    if not raw_summary and not image_data_list:
        raise ValueError("Must provide either raw_summary or image_data_list")

    # Build user prompt based on inputs
    if image_data_list and not raw_summary:
        # Images only
        user_prompt = """Analyze the screenshots provided to extract drama information.

Extract structured data from these images. Look for:
- Conversations, messages, or text visible in the screenshots
- Names of people involved
- Timestamps or time references
- Emotional indicators (tone, emoji, punctuation)
- Context about what happened

Return only the JSON object, no additional text."""
    elif raw_summary and not image_data_list:
        # Text only (existing behavior)
        user_prompt = build_summary_extractor_prompt(raw_summary)
    else:
        # Both text and images
        user_prompt = f"""User's context: {raw_summary}

Additionally, analyze the screenshots provided for more details.

Extract structured data combining the text summary and visual information. Merge insights from both sources into a single coherent analysis.

Return only the JSON object, no additional text."""

    # Call Claude API with vision if images present
    if image_data_list:
        response = self.client.call_with_tool_and_images(
            SUMMARY_EXTRACTOR_SYSTEM,
            user_prompt,
            SUMMARY_EXTRACTOR_SCHEMA,
            image_data_list=image_data_list,
            session_id=session_id,
            use_cache=True
        )
    else:
        # Text-only path (existing)
        response = self.client.call_with_tool(
            SUMMARY_EXTRACTOR_SYSTEM,
            user_prompt,
            SUMMARY_EXTRACTOR_SCHEMA,
            session_id=session_id,
            use_cache=True
        )

    return response
```

**Note:** This assumes `call_with_tool` exists. If it doesn't, you'll need to implement it following the same pattern as `call_with_tool_and_images` but without images.

**Step 2: Verify existing call_with_tool exists**

Check if `ClaudeClient` has a `call_with_tool` method. If not, add it to `backend/src/api_client.py`:

```python
def call_with_tool(
    self,
    system_prompt: str,
    user_prompt: str,
    tool_schema: dict,
    max_retries: int = 3,
    session_id: Optional[str] = None,
    use_cache: bool = False
) -> dict:
    """
    Call Claude API with tool use (structured output) for text-only input.

    Args:
        system_prompt: System instruction
        user_prompt: User message text
        tool_schema: JSON schema for tool use
        max_retries: Number of retry attempts
        session_id: Optional session ID
        use_cache: Whether to use prompt caching

    Returns:
        Structured dict extracted from tool use
    """
    last_error: Optional[Exception] = None

    # Add session ID to system prompt
    if session_id:
        system_prompt = f"[Session: {session_id}]\n\n{system_prompt}"

    # Prepare system with caching if requested
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
                system=system,
                messages=[{"role": "user", "content": user_prompt}],
                tools=[tool_schema]
            )

            # Extract tool use from response
            for block in response.content:
                if block.type == "tool_use":
                    return block.input

            raise ValueError("No tool use found in response")

        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                time.sleep(wait_time)

    raise Exception(f"Failed after {max_retries} attempts: {last_error}")
```

**Step 3: Commit**

```bash
git add src/agents/summary_extractor.py backend/src/api_client.py
git commit -m "feat: support images in summary extraction

- Update extract_summary() to accept optional images
- Handle text-only, image-only, or combined inputs
- Build appropriate prompts for each scenario
- Add call_with_tool() method if missing"
```

---

### Task 1.3: Update API Routes for Image Upload

**Files:**
- Modify: `backend/src/api/routes.py:14-52`

**Goal:** Accept base64 images in `/investigate` endpoint and pass to summary extractor.

**Step 1: Update investigate route to handle images**

Replace the `/investigate` route in `backend/src/api/routes.py`:

```python
@api_bp.route("/investigate", methods=["POST"])
def investigate():
    try:
        data = request.get_json()
        incident_name = data.get("incident_name")
        summary: str = data.get("summary", "")
        interviewee_name = data.get("interviewee_name", "Anonymous")
        relationship = data.get("relationship", "participant")
        images = data.get("images", [])  # NEW: Array of base64 image strings

        # Validate at least one input provided
        if not incident_name:
            return jsonify({'error': 'incident_name is required'}), 400

        if not summary and not images:
            return jsonify({'error': 'Either summary or images must be provided'}), 400

        # Process images into format for API client
        image_data_list = []
        if images:
            for img_base64 in images:
                # Detect media type from base64 prefix or default to jpeg
                if img_base64.startswith('/9j/'):  # JPEG magic bytes
                    media_type = "image/jpeg"
                elif img_base64.startswith('iVBORw'):  # PNG magic bytes
                    media_type = "image/png"
                elif img_base64.startswith('R0lG'):  # GIF magic bytes
                    media_type = "image/gif"
                elif img_base64.startswith('UklGR'):  # WebP magic bytes
                    media_type = "image/webp"
                else:
                    media_type = "image/jpeg"  # Default fallback

                image_data_list.append({
                    "data": img_base64,
                    "media_type": media_type
                })

        # Create session
        session_manager: SessionManager = SessionManager()
        session: Session = session_manager.create_session(
            incident_name,
            interviewee_name=interviewee_name,
            relationship=relationship
        )

        # Initialize investigation with optional images
        orchestrator: InterviewOrchestrator = InterviewOrchestrator(session)

        # Pass images to orchestrator (we'll update this next)
        if image_data_list:
            orchestrator.initialize_investigation(
                summary if summary else "",
                image_data_list=image_data_list
            )
        else:
            orchestrator.initialize_investigation(summary)

        session_manager.save_session(session)

        # Return response
        return jsonify({
            'session_id': session.session_id,
            'incident_name': session.incident_name,
            'question': session.current_question,
            'answers': [a.model_dump() for a in session.answers],
            'turn_count': session.turn_count,
            'goals': [g.model_dump() for g in session.goals]
        })
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Step 2: Update InterviewOrchestrator.initialize_investigation**

Modify `backend/src/interview.py` to accept images. Find the `initialize_investigation` method and update it:

```python
def initialize_investigation(self, summary: str, image_data_list: list[dict] = None):
    """
    Initialize a new investigation from summary and/or images.

    Args:
        summary: Text description of the drama
        image_data_list: Optional list of image dicts for vision processing
    """
    # Extract structured summary (with optional images)
    from src.agents.summary_extractor import SummaryExtractorAgent
    from src.api_client import ClaudeClient

    client = ClaudeClient()
    extractor = SummaryExtractorAgent(client)

    structured_summary = extractor.extract_summary(
        raw_summary=summary if summary else None,
        image_data_list=image_data_list,
        session_id=self.session.session_id
    )

    # Store original summary in session
    self.session.summary = summary

    # Generate goals from structured summary
    from src.agents.goal_generator import GoalGeneratorAgent
    goal_gen = GoalGeneratorAgent(client)
    goal_descriptions = goal_gen.generate_goals(structured_summary, self.session.session_id)

    # Create Goal objects
    from src.models import Goal, GoalStatus
    self.session.goals = [
        Goal(description=desc, status=GoalStatus.NOT_STARTED, confidence=0)
        for desc in goal_descriptions
    ]

    # Generate first question
    self._generate_next_question()
```

**Step 3: Test with curl**

Create a test script `test_image_upload.sh`:

```bash
#!/bin/bash

# Create a small test base64 image (1x1 red pixel PNG)
TEST_IMAGE="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

curl -X POST http://localhost:5001/api/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "incident_name": "Test Image Upload",
    "summary": "Testing image processing",
    "images": ["'"$TEST_IMAGE"'"],
    "interviewee_name": "Tester",
    "relationship": "participant"
  }'
```

**Step 4: Run test**

```bash
chmod +x test_image_upload.sh
./test_image_upload.sh
```

Expected: JSON response with `session_id`, `question`, and `answers` fields.

**Step 5: Commit**

```bash
git add backend/src/api/routes.py backend/src/interview.py test_image_upload.sh
git commit -m "feat: accept images in /investigate endpoint

- Parse images array from request body
- Detect image media type from base64 prefix
- Pass images to InterviewOrchestrator
- Update initialize_investigation to handle images
- Add test script for image upload"
```

---

## Phase 2: Frontend Image Upload (45 minutes)

### Task 2.1: Add Image Upload UI to Deets Page

**Files:**
- Modify: `frontend/src/app/deets/page.tsx:1-158`

**Goal:** Add file input and image preview to deets page.

**Step 1: Update state to include images**

Add image state after existing state declarations in `DeetsPage` component (around line 24):

```typescript
const [images, setImages] = useState<string[]>([]);  // base64 strings
const [imagePreviews, setImagePreviews] = useState<string[]>([]);  // data URLs for preview
```

**Step 2: Add image upload handler**

Add this function before the `handleSubmit` function:

```typescript
const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
  const files = e.target.files;
  if (!files) return;

  // Limit to 5 images max
  const fileArray = Array.from(files).slice(0, 5);

  // Convert to base64 and create previews
  Promise.all(
    fileArray.map(file => {
      return new Promise<{ base64: string; preview: string }>((resolve, reject) => {
        // Create preview URL
        const previewUrl = URL.createObjectURL(file);

        // Convert to base64 for API
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = reader.result as string;
          // Remove data URL prefix to get pure base64
          const base64Data = base64.split(',')[1];
          resolve({ base64: base64Data, preview: previewUrl });
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    })
  ).then(results => {
    setImages(results.map(r => r.base64));
    setImagePreviews(results.map(r => r.preview));
  }).catch(error => {
    toast.error('Failed to process images');
    console.error(error);
  });
};
```

**Step 3: Add remove image handler**

Add this function after `handleImageUpload`:

```typescript
const handleRemoveImage = (index: number) => {
  setImages(prev => prev.filter((_, i) => i !== index));
  setImagePreviews(prev => {
    // Revoke object URL to prevent memory leak
    URL.revokeObjectURL(prev[index]);
    return prev.filter((_, i) => i !== index);
  });
};
```

**Step 4: Update handleSubmit to include images**

Modify the `handleSubmit` function to send images:

```typescript
const handleSubmit = async () => {
  // Validate at least one input
  if (summary.trim().length < 10 && images.length === 0) {
    toast.error('Please provide text (10+ chars) or upload screenshots');
    return;
  }

  setIsLoading(true);

  try {
    const incidentName = generateIncidentName(summary || 'Screenshot Drama');

    await dispatch(startInvestigation({
      incidentName,
      summary: summary.trim(),
      images,  // NEW: Include images
      intervieweeName: intervieweeName.trim() || 'Anonymous',
      relationship
    })).unwrap();

    // Navigate to question page on success
    router.push('/question');
  } catch (error) {
    toast.error('Failed to start investigation');
    setIsLoading(false);
  }
};
```

**Step 5: Add image upload UI to JSX**

Add this section after the summary textarea and before the name input (around line 83):

```tsx
{/* Image Upload Section */}
<div className="space-y-2">
  <Label htmlFor="images">Or upload screenshots</Label>
  <div className="space-y-3">
    <input
      id="images"
      type="file"
      accept="image/*"
      multiple
      onChange={handleImageUpload}
      className="block w-full text-sm text-muted-foreground
        file:mr-4 file:py-2 file:px-4
        file:rounded-md file:border-0
        file:text-sm file:font-semibold
        file:bg-primary file:text-primary-foreground
        hover:file:bg-primary/90
        cursor-pointer"
    />
    <p className="text-xs text-muted-foreground">
      Upload up to 5 screenshots (PNG, JPG, GIF, WebP)
    </p>

    {/* Image Previews */}
    {imagePreviews.length > 0 && (
      <div className="grid grid-cols-2 gap-3 mt-3">
        {imagePreviews.map((preview, index) => (
          <div key={index} className="relative group">
            <img
              src={preview}
              alt={`Screenshot ${index + 1}`}
              className="w-full h-32 object-cover rounded-md border border-border"
            />
            <button
              type="button"
              onClick={() => handleRemoveImage(index)}
              className="absolute top-1 right-1 bg-destructive text-destructive-foreground
                rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
              aria-label="Remove image"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        ))}
      </div>
    )}
  </div>
</div>
```

**Step 6: Update button disabled condition**

Change the button disabled condition (around line 148):

```tsx
<Button
  size="lg"
  className="w-full min-h-touch text-lg"
  onClick={handleSubmit}
  disabled={isLoading || (summary.trim().length < 10 && images.length === 0)}
>
  {isLoading ? 'Starting Detective...' : 'Start Detective'}
</Button>
```

**Step 7: Commit**

```bash
git add frontend/src/app/deets/page.tsx
git commit -m "feat: add image upload to deets page

- Add file input with multi-select support
- Display image previews in grid
- Convert images to base64 for API
- Allow removing images before submit
- Validate at least text or images provided"
```

---

### Task 2.2: Update Redux Thunk to Send Images

**Files:**
- Modify: `frontend/src/store/thunks/investigationThunks.ts:17-59`
- Modify: `frontend/src/lib/api.ts:28-45`

**Goal:** Pass images through Redux action to API.

**Step 1: Update startInvestigation thunk signature**

Modify the `startInvestigation` thunk in `frontend/src/store/thunks/investigationThunks.ts`:

```typescript
export const startInvestigation = createAsyncThunk(
  'investigation/start',
  async (
    {
      incidentName,
      summary,
      images,  // NEW
      intervieweeName,
      relationship
    }: {
      incidentName: string;
      summary: string;
      images?: string[];  // NEW: Optional array of base64 strings
      intervieweeName?: string;
      relationship?: string;
    },
    { dispatch, rejectWithValue }
  ) => {
    try {
      dispatch(setStatus('investigating'));

      const response = await api.investigate(
        incidentName,
        summary,
        intervieweeName,
        relationship,
        images  // NEW: Pass images to API
      );

      dispatch(setSessionId(response.session_id));
      dispatch(setIncidentName(response.incident_name));
      dispatch(setQuestion({
        question: response.question,
        answers: response.answers,
      }));
      dispatch(updateProgress({
        turnCount: response.turn_count,
        goals: response.goals,
      }));
      dispatch(setStatus('questioning'));

      return response;
    } catch (error) {
      const message = error instanceof ApiError
        ? error.message
        : 'Failed to start investigation';
      dispatch(setError(message));
      return rejectWithValue(message);
    }
  }
);
```

**Step 2: Update api.investigate to accept images**

Modify the `investigate` method in `frontend/src/lib/api.ts`:

```typescript
async investigate(
  incidentName: string,
  summary: string,
  intervieweeName?: string,
  relationship?: string,
  images?: string[]  // NEW
): Promise<InvestigateResponse> {
  return fetchWithErrorHandling(`${API_BASE}/investigate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      incident_name: incidentName,
      summary,
      interviewee_name: intervieweeName,
      relationship,
      images: images || []  // NEW: Include images array
    }),
  });
}
```

**Step 3: Test the flow**

No automated test - manual testing after starting both servers.

**Step 4: Commit**

```bash
git add frontend/src/store/thunks/investigationThunks.ts frontend/src/lib/api.ts
git commit -m "feat: send images through API layer

- Add images param to startInvestigation thunk
- Pass images to api.investigate method
- Include images array in POST body"
```

---

## Phase 3: Analysis Page (45 minutes)

### Task 3.1: Create Analysis Page Component

**Files:**
- Create: `frontend/src/app/analysis/page.tsx`

**Goal:** Build analysis results page with structured sections.

**Step 1: Create analysis page file**

Create `frontend/src/app/analysis/page.tsx`:

```typescript
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { selectSessionId, selectIncidentName } from '@/store/selectors';
import {
  selectAnalysisData,
  selectAnalysisLoading,
  selectAnalysisLoadingMessage
} from '@/store/selectors';
import { fetchAnalysis } from '@/store/thunks/investigationThunks';
import ShareButton from '@/components/ShareButton';
import LoadingMessages from '@/components/LoadingMessages';
import AnalysisSection from '@/components/AnalysisSection';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface TimelineEvent {
  time: string;
  event: string;
}

interface Verdict {
  primary_responsibility: string;
  percentage: number;
  reasoning: string;
  contributing_factors: string;
  drama_rating: number;
  drama_rating_explanation: string;
}

interface AnalysisData {
  timeline: TimelineEvent[];
  key_facts: string[];
  gaps: string[];
  verdict: Verdict;
}

export default function AnalysisPage() {
  const router = useRouter();
  const dispatch = useAppDispatch();

  const sessionId = useAppSelector(selectSessionId);
  const incidentName = useAppSelector(selectIncidentName);
  const analysisData = useAppSelector(selectAnalysisData) as AnalysisData | null;
  const isLoading = useAppSelector(selectAnalysisLoading);
  const loadingMessage = useAppSelector(selectAnalysisLoadingMessage);

  // Redirect if no session
  useEffect(() => {
    if (!sessionId) {
      router.push('/');
      return;
    }

    // Fetch analysis on mount
    if (!analysisData && !isLoading) {
      dispatch(fetchAnalysis(sessionId));
    }
  }, [sessionId, analysisData, isLoading, dispatch, router]);

  if (!sessionId) return null;

  // Loading state
  if (isLoading || !analysisData) {
    return (
      <main className="min-h-screen p-4 bg-gradient-to-b from-background to-muted">
        <div className="max-w-3xl mx-auto">
          <LoadingMessages message={loadingMessage} />
        </div>
      </main>
    );
  }

  const { timeline, key_facts, gaps, verdict } = analysisData;

  // Helper to get drama rating color
  const getDramaRatingColor = (rating: number) => {
    if (rating <= 3) return 'bg-green-500';
    if (rating <= 6) return 'bg-yellow-500';
    if (rating <= 8) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <main className="min-h-screen p-4 bg-gradient-to-b from-background to-muted">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={() => router.push('/')}
            size="sm"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            New Investigation
          </Button>
        </div>

        {/* Title Card */}
        <Card className="border-2">
          <CardHeader>
            <div className="flex items-start justify-between gap-4">
              <div>
                <CardTitle className="text-2xl mb-2">{incidentName}</CardTitle>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">Drama Rating:</span>
                  <Badge className={`${getDramaRatingColor(verdict.drama_rating)} text-white`}>
                    {verdict.drama_rating}/10
                  </Badge>
                </div>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Verdict Section */}
        <AnalysisSection title="The Verdict" icon="⚖️">
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-sm mb-2">Primary Responsibility</h4>
              <p className="text-sm">
                <span className="font-bold">{verdict.primary_responsibility}</span>
                {' '}({verdict.percentage}% responsible)
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-sm mb-2">Reasoning</h4>
              <p className="text-sm text-muted-foreground">{verdict.reasoning}</p>
            </div>
            {verdict.contributing_factors && (
              <div>
                <h4 className="font-semibold text-sm mb-2">Contributing Factors</h4>
                <p className="text-sm text-muted-foreground">{verdict.contributing_factors}</p>
              </div>
            )}
            <div>
              <h4 className="font-semibold text-sm mb-2">Drama Assessment</h4>
              <p className="text-sm text-muted-foreground">{verdict.drama_rating_explanation}</p>
            </div>
          </div>
        </AnalysisSection>

        {/* Timeline Section */}
        {timeline && timeline.length > 0 && (
          <AnalysisSection title="Timeline" icon="⏱️">
            <div className="space-y-3">
              {timeline.map((event, index) => (
                <div key={index} className="flex gap-3">
                  <div className="text-sm font-semibold text-primary min-w-[80px]">
                    {event.time}
                  </div>
                  <div className="text-sm text-muted-foreground flex-1">
                    {event.event}
                  </div>
                </div>
              ))}
            </div>
          </AnalysisSection>
        )}

        {/* Key Facts Section */}
        {key_facts && key_facts.length > 0 && (
          <AnalysisSection title="Key Facts" icon="📋">
            <ul className="list-disc list-inside space-y-2">
              {key_facts.map((fact, index) => (
                <li key={index} className="text-sm text-muted-foreground">
                  {fact}
                </li>
              ))}
            </ul>
          </AnalysisSection>
        )}

        {/* Gaps Section */}
        {gaps && gaps.length > 0 && (
          <AnalysisSection title="What's Still Unclear" icon="❓">
            <ul className="list-disc list-inside space-y-2">
              {gaps.map((gap, index) => (
                <li key={index} className="text-sm text-muted-foreground">
                  {gap}
                </li>
              ))}
            </ul>
          </AnalysisSection>
        )}

        {/* Share Button */}
        <div className="pt-4">
          <ShareButton
            analysisText={`Drama Rating: ${verdict.drama_rating}/10\n\n${verdict.reasoning}`}
            incidentName={incidentName}
          />
        </div>
      </div>
    </main>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/app/analysis/page.tsx
git commit -m "feat: create structured analysis page

- Display verdict with responsibility percentage
- Show timeline with time markers
- List key facts and gaps
- Drama rating badge with color coding
- Include ShareButton component"
```

---

### Task 3.2: Add Analysis Redux Action

**Files:**
- Modify: `frontend/src/store/thunks/investigationThunks.ts`
- Modify: `frontend/src/store/selectors.ts`

**Goal:** Add Redux thunk to fetch analysis from backend.

**Step 1: Add fetchAnalysis thunk**

Add this thunk to `frontend/src/store/thunks/investigationThunks.ts` after `submitAnswer`:

```typescript
export const fetchAnalysis = createAsyncThunk(
  'investigation/fetchAnalysis',
  async (sessionId: string, { dispatch, rejectWithValue }) => {
    try {
      dispatch(setAnalysisLoading(true));

      const response = await api.getAnalysis(sessionId);

      dispatch(setAnalysisData(response.analysis));

      return response;
    } catch (error) {
      const message = error instanceof ApiError
        ? error.message
        : 'Failed to fetch analysis';
      return rejectWithValue(message);
    }
  }
);
```

**Step 2: Add analysis selectors if missing**

Check if these selectors exist in `frontend/src/store/selectors.ts`. If not, add:

```typescript
// Analysis selectors
export const selectAnalysisData = (state: RootState) => state.analysis.data;
export const selectAnalysisLoading = (state: RootState) => state.analysis.isLoading;
export const selectAnalysisLoadingMessage = (state: RootState) => state.analysis.loadingMessage;
```

**Step 3: Verify analysis slice has setAnalysisData action**

Check `frontend/src/store/slices/analysisSlice.ts` has these actions. If not, ensure they exist:

```typescript
setAnalysisData: (state, action: PayloadAction<any>) => {
  state.data = action.payload;
  state.isLoading = false;
},
setAnalysisLoading: (state, action: PayloadAction<boolean>) => {
  state.isLoading = action.payload;
  if (action.payload) {
    state.loadingMessage = 'Analyzing the drama...';
  }
},
```

**Step 4: Commit**

```bash
git add frontend/src/store/thunks/investigationThunks.ts frontend/src/store/selectors.ts frontend/src/store/slices/analysisSlice.ts
git commit -m "feat: add fetchAnalysis Redux thunk

- Create fetchAnalysis async thunk
- Set loading state during analysis fetch
- Add analysis selectors if missing
- Update analysis slice actions"
```

---

## Phase 4: Polish & Testing (30 minutes)

### Task 4.1: Add Loading Animations

**Files:**
- Modify: `frontend/src/components/LoadingMessages.tsx`
- Modify: `frontend/src/app/deets/page.tsx`

**Goal:** Enhance loading states with animated messages.

**Step 1: Check LoadingMessages component**

Verify `frontend/src/components/LoadingMessages.tsx` exists and has rotating messages. If it needs improvement:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Spinner } from '@/components/ui/spinner';

interface LoadingMessagesProps {
  message?: string;
}

const DEFAULT_MESSAGES = [
  'Brewing some tea...',
  'Analyzing the drama...',
  'Connecting the dots...',
  'Reading between the lines...',
  'Fact-checking the tea...',
  'Investigating the situation...',
  'Gathering evidence...',
];

export default function LoadingMessages({ message }: LoadingMessagesProps) {
  const [currentMessage, setCurrentMessage] = useState(message || DEFAULT_MESSAGES[0]);
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    if (message) {
      setCurrentMessage(message);
      return;
    }

    // Rotate through messages every 3 seconds
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % DEFAULT_MESSAGES.length);
    }, 3000);

    return () => clearInterval(interval);
  }, [message]);

  useEffect(() => {
    if (!message) {
      setCurrentMessage(DEFAULT_MESSAGES[messageIndex]);
    }
  }, [messageIndex, message]);

  return (
    <Card className="border-2">
      <CardContent className="pt-6">
        <div className="flex flex-col items-center justify-center space-y-4 py-8">
          <Spinner className="h-12 w-12" />
          <p className="text-lg font-medium animate-pulse">
            {currentMessage}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
```

**Step 2: Add loading animation to deets page during submit**

If not already present, ensure the deets page shows loading state during investigation start.

**Step 3: Commit**

```bash
git add frontend/src/components/LoadingMessages.tsx
git commit -m "feat: enhance loading animations

- Rotate through themed loading messages
- Add pulse animation to text
- Use Spinner component for visual feedback"
```

---

### Task 4.2: Theme Polish

**Files:**
- Modify: `frontend/src/app/globals.css`
- Modify: `frontend/tailwind.config.ts` (if needed)

**Goal:** Apply sleeker theme inspired by known.design (softer colors, better spacing).

**Step 1: Update CSS variables for softer theme**

Modify the `:root` and `.dark` sections in `frontend/src/app/globals.css`:

```css
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;

    /* Softer primary - purple/blue */
    --primary: 250 70% 60%;
    --primary-foreground: 0 0% 100%;

    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;

    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;

    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;

    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 0 0% 98%;

    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 250 70% 60%;

    --radius: 0.75rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;

    /* Softer primary - purple/blue */
    --primary: 250 70% 65%;
    --primary-foreground: 222.2 84% 4.9%;

    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;

    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;

    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;

    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;

    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 250 70% 65%;
  }
}
```

**Step 2: Add smooth transitions**

Add global transition styles at the end of `globals.css`:

```css
@layer base {
  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground;
  }

  /* Smooth transitions */
  button, a, input, textarea {
    @apply transition-all duration-200 ease-in-out;
  }

  /* Card hover effects */
  .card-hover {
    @apply hover:shadow-lg hover:scale-[1.02] transition-all duration-200;
  }
}
```

**Step 3: Add subtle shadows to cards**

Update card components to use softer shadows. Add utility class:

```css
.card-soft-shadow {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06);
}

.dark .card-soft-shadow {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.4);
}
```

**Step 4: Commit**

```bash
git add frontend/src/app/globals.css
git commit -m "style: apply sleeker theme polish

- Update primary color to softer purple/blue
- Add smooth transitions to interactive elements
- Implement soft shadow utility for cards
- Improve spacing and visual hierarchy"
```

---

### Task 4.3: End-to-End Testing

**Files:**
- Create: `TEST_CHECKLIST.md`

**Goal:** Verify complete user flow works.

**Step 1: Create test checklist**

Create `TEST_CHECKLIST.md`:

```markdown
# MVP Testing Checklist

## Prerequisites
- [ ] Backend server running on port 5001
- [ ] Frontend dev server running on port 3000
- [ ] `.env` file configured with Anthropic API key

## Test Cases

### 1. Text-Only Flow
- [ ] Navigate to home page
- [ ] Click "💬 Deets" button
- [ ] Enter drama summary (50+ chars)
- [ ] Enter name and select relationship
- [ ] Click "Start Detective"
- [ ] Verify question page loads with 4 answer options
- [ ] Answer 3-5 questions
- [ ] Verify navigation to analysis page
- [ ] Check all sections render (verdict, timeline, facts, gaps)
- [ ] Click share button and verify copy to clipboard

### 2. Image-Only Flow
- [ ] Navigate to home page
- [ ] Click "💬 Deets"
- [ ] Upload 2-3 screenshots (no text summary)
- [ ] Verify image previews display
- [ ] Enter name and relationship
- [ ] Click "Start Detective"
- [ ] Verify question page loads
- [ ] Complete investigation
- [ ] Verify analysis extracts data from images

### 3. Text + Image Flow
- [ ] Navigate to home page
- [ ] Click "💬 Deets"
- [ ] Enter brief summary
- [ ] Upload 1-2 screenshots
- [ ] Verify both inputs present
- [ ] Complete investigation
- [ ] Verify analysis merges both data sources

### 4. Image Upload Features
- [ ] Upload image and verify preview shows
- [ ] Click X button to remove image
- [ ] Upload 6 images and verify limit to 5
- [ ] Upload non-image file and verify error/rejection

### 5. Loading States
- [ ] Verify loading animation during investigation start
- [ ] Verify rotating messages during questions
- [ ] Verify loading state during analysis generation

### 6. Theme & Polish
- [ ] Verify purple/blue primary color throughout
- [ ] Check smooth transitions on button hovers
- [ ] Verify card shadows look subtle
- [ ] Test dark mode if enabled

### 7. Error Handling
- [ ] Try submitting with no text and no images - verify error
- [ ] Try uploading very large image (>10MB) - verify handling
- [ ] Disconnect backend and verify error messages display

## Performance
- [ ] Image upload completes in <3 seconds
- [ ] Question generation takes <5 seconds
- [ ] Analysis generation takes <10 seconds
- [ ] No memory leaks from image previews

## Browser Testing
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari
- [ ] Mobile Chrome
- [ ] Mobile Safari
```

**Step 2: Manual test execution**

Run through each checklist item. Document any failures.

**Step 3: Fix critical bugs**

If any blockers found, fix immediately. Nice-to-haves can be deferred.

**Step 4: Commit**

```bash
git add TEST_CHECKLIST.md
git commit -m "docs: add comprehensive MVP test checklist

- Cover text-only, image-only, and combined flows
- Include UI/UX validation points
- Document error handling scenarios
- Add performance benchmarks"
```

---

## Bonus: Screenshots Button on Home (if time permits)

**Files:**
- Modify: `frontend/src/app/page.tsx:20-28`

**Goal:** Make screenshots button navigate to upload flow.

**Step 1: Enable screenshots button**

Modify `frontend/src/app/page.tsx`:

```tsx
<Button
  variant="outline"
  size="lg"
  className="w-full min-h-touch text-lg"
  onClick={() => router.push('/deets')}  // Changed from disabled
>
  📸 Screenshots
</Button>
```

**Step 2: Remove "Coming Soon" text**

```tsx
<Button
  variant="outline"
  size="lg"
  className="w-full min-h-touch text-lg"
  onClick={() => router.push('/deets')}
>
  📸 Screenshots
</Button>
```

Since we've combined both flows in the deets page, this button can just go to deets.

**Step 3: Commit**

```bash
git add frontend/src/app/page.tsx
git commit -m "feat: enable screenshots button on home

- Route to deets page (which now supports images)
- Remove 'Coming Soon' indicator"
```

---

## Final Integration

### Create `.gitignore` Entry for Test Images

Add to `.gitignore`:

```
# Test files
test_image_upload.sh
test_images/
*.test.png
*.test.jpg
```

### Create Environment Variable Documentation

Create `ENV.md` if it doesn't exist:

```markdown
# Environment Variables

## Backend (.env in root)

```bash
ANTHROPIC_API_KEY=your_api_key_here
FLASK_ENV=development
PORT=5001
```

## Frontend (.env.local in frontend/)

```bash
NEXT_PUBLIC_API_URL=http://localhost:5001/api
```

## Production

- Set `ANTHROPIC_API_KEY` in production environment
- Update `NEXT_PUBLIC_API_URL` to production backend URL
```

### Final Commit

```bash
git add .gitignore ENV.md
git commit -m "docs: add environment setup and ignore patterns

- Document required environment variables
- Ignore test files and images
- Add setup instructions"
```

---

## Plan Complete!

**Total Tasks:** 13 tasks across 4 phases
**Estimated Time:** 3 hours
**Deliverables:**
- ✅ Backend image processing via Claude vision API
- ✅ Frontend image upload with previews
- ✅ Structured analysis page with share functionality
- ✅ Theme polish and loading animations

**Implementation Notes:**
- Follow tasks in order (they build on each other)
- Test integration points after each phase
- Commit frequently (after each task)
- If time runs short, skip Phase 4 polish tasks

**Next Steps:**
1. Start backend servers: `cd backend && flask run`
2. Start frontend: `cd frontend && npm run dev`
3. Begin with Phase 1, Task 1.1
4. Follow task sequence exactly
5. Test after each phase completion

