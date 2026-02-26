"""
Assistant Chat endpoint — passthrough to OpenAI / Anthropic with tool-calling support.

This is intentionally thin: auth + passthrough + usage tracking.
The intelligence (tool registry, execution, context building) lives in the frontend.

Provider routing:
  - Models starting with "claude" → Anthropic
  - Everything else → OpenAI (supports openai, openrouter, etc.)
"""

from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api import token_service
from environment import OPENAI_API_KEY, ANTHROPIC_API_KEY

assistant_router = APIRouter()

# ── OpenAI client ────────────────────────────────────────────────────────
openai_client = None
try:
    from openai import OpenAI
    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    print(f"Warning: OpenAI client not initialized for assistant: {e}")

# ── Anthropic client ─────────────────────────────────────────────────────
anthropic_client = None
try:
    import anthropic
    if ANTHROPIC_API_KEY:
        anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
except Exception as e:
    print(f"Warning: Anthropic client not initialized for assistant: {e}")


# ── Available models ──────────────────────────────────────────────────────
AVAILABLE_MODELS = []

# OpenAI models (available if OPENAI_API_KEY is set)
if OPENAI_API_KEY:
    AVAILABLE_MODELS.extend([
        {"id": "gpt-5.2", "name": "GPT-5.2", "provider": "openai"},
        {"id": "gpt-5.2-pro", "name": "GPT-5.2 Pro", "provider": "openai"},
        {"id": "gpt-5-mini", "name": "GPT-5 Mini", "provider": "openai"},
    ])

# Anthropic models (available if ANTHROPIC_API_KEY is set)
if ANTHROPIC_API_KEY:
    AVAILABLE_MODELS.extend([
        {"id": "claude-opus-4-6", "name": "Claude Opus 4.6", "provider": "anthropic"},
        {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6", "provider": "anthropic"},
        {"id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5", "provider": "anthropic"},
    ])


@assistant_router.get("/models")
async def list_assistant_models(
    user_id: str = Depends(token_service.verify_jwt),
):
    """Return the list of available assistant models based on configured API keys."""
    return AVAILABLE_MODELS


class AssistantChatRequest(BaseModel):
    """Request model for the assistant chat endpoint."""
    messages: List[Dict[str, Any]]              # Full conversation history
    tools: Optional[List[Dict[str, Any]]] = None  # Tool schemas in OpenAI format
    model: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int = 4096
    project_id: Optional[str] = None            # For usage tracking


def _is_anthropic_model(model: str) -> bool:
    """Check if the model name indicates Anthropic."""
    return model.startswith("claude")


def _convert_openai_tools_to_anthropic(tools: List[Dict]) -> List[Dict]:
    """
    Convert OpenAI-format tool schemas to Anthropic format.

    OpenAI:  { type: "function", function: { name, description, parameters } }
    Anthropic: { name, description, input_schema }
    """
    result = []
    for tool in tools:
        fn = tool.get("function", {})
        result.append({
            "name": fn.get("name", ""),
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
        })
    return result


def _convert_openai_messages_to_anthropic(messages: List[Dict]) -> tuple:
    """
    Convert OpenAI-format messages to Anthropic format.

    Returns (system_prompt, anthropic_messages).

    Key differences:
    - Anthropic system prompt is separate, not a message
    - Anthropic uses tool_use/tool_result content blocks instead of
      separate role="tool" messages
    - Assistant messages with tool_calls become content blocks with tool_use
    - Messages MUST strictly alternate user/assistant — consecutive same-role
      messages are merged into one message with multiple content blocks
    """
    import json as _json

    system_prompt = ""
    raw_messages = []  # collect before merging

    for msg in messages:
        role = msg.get("role")

        if role == "system":
            system_prompt = msg.get("content", "")

        elif role == "user":
            content = msg.get("content", "")
            # Normalize to content blocks
            if isinstance(content, str):
                raw_messages.append({
                    "role": "user",
                    "content": [{"type": "text", "text": content}] if content else [],
                })
            else:
                # Already content blocks (shouldn't happen from OpenAI format, but safe)
                raw_messages.append({"role": "user", "content": content})

        elif role == "assistant":
            content_blocks = []

            text = msg.get("content")
            if text:
                content_blocks.append({"type": "text", "text": text})

            tool_calls = msg.get("tool_calls", [])
            for tc in tool_calls:
                fn = tc.get("function", {})
                args = fn.get("arguments", "{}")
                if isinstance(args, str):
                    try:
                        args = _json.loads(args)
                    except (ValueError, _json.JSONDecodeError):
                        args = {}

                content_blocks.append({
                    "type": "tool_use",
                    "id": tc.get("id", ""),
                    "name": fn.get("name", ""),
                    "input": args,
                })

            if content_blocks:
                raw_messages.append({"role": "assistant", "content": content_blocks})

        elif role == "tool":
            # Tool results become user messages with tool_result blocks
            raw_messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": msg.get("tool_call_id", ""),
                    "content": msg.get("content", ""),
                }],
            })

    # Merge consecutive messages with the same role (Anthropic requires strict alternation)
    merged = []
    for msg in raw_messages:
        if merged and merged[-1]["role"] == msg["role"]:
            # Merge content blocks into the previous message
            prev_content = merged[-1]["content"]
            new_content = msg["content"]
            if isinstance(prev_content, list) and isinstance(new_content, list):
                prev_content.extend(new_content)
            elif isinstance(prev_content, str) and isinstance(new_content, str):
                merged[-1]["content"] = prev_content + "\n" + new_content
            else:
                # Mixed types — normalize both to lists
                if isinstance(prev_content, str):
                    merged[-1]["content"] = [{"type": "text", "text": prev_content}]
                if isinstance(new_content, str):
                    new_content = [{"type": "text", "text": new_content}]
                merged[-1]["content"].extend(new_content)
        else:
            merged.append(msg)

    # Anthropic requires the first message to be from the user
    if merged and merged[0]["role"] != "user":
        merged.insert(0, {"role": "user", "content": [{"type": "text", "text": "Hello"}]})

    return system_prompt, merged


def _convert_anthropic_response_to_openai(response) -> Dict:
    """
    Convert Anthropic response to OpenAI-compatible format so the frontend
    can use the same parsing logic (OpenAIAdapter.parseResponse).
    """
    content_text = ""
    tool_calls = []

    for block in response.content:
        if block.type == "text":
            content_text += block.text
        elif block.type == "tool_use":
            tool_calls.append({
                "id": block.id,
                "type": "function",
                "function": {
                    "name": block.name,
                    "arguments": __import__("json").dumps(block.input),
                },
            })

    message = {
        "role": "assistant",
        "content": content_text or None,
    }
    if tool_calls:
        message["tool_calls"] = tool_calls

    return {
        "id": response.id,
        "model": response.model,
        "choices": [{
            "index": 0,
            "message": message,
            "finish_reason": response.stop_reason or "stop",
        }],
        "usage": {
            "prompt_tokens": response.usage.input_tokens if response.usage else 0,
            "completion_tokens": response.usage.output_tokens if response.usage else 0,
            "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0,
        },
    }


@assistant_router.post("/chat")
async def assistant_chat(
    request: AssistantChatRequest,
    user_id: str = Depends(token_service.verify_jwt),
):
    """
    Chat completion with tool-calling support for the workflow assistant.

    Routes to Anthropic or OpenAI based on the model name.
    Returns OpenAI-compatible response format regardless of provider.
    """
    if _is_anthropic_model(request.model):
        return await _handle_anthropic(request)
    else:
        return await _handle_openai(request)


async def _handle_openai(request: AssistantChatRequest) -> Dict:
    """Handle OpenAI chat completion."""
    if not openai_client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI client not initialized. Please set OPENAI_API_KEY.",
        )

    kwargs = {
        "model": request.model,
        "messages": request.messages,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }

    if request.tools and len(request.tools) > 0:
        kwargs["tools"] = request.tools
        kwargs["tool_choice"] = "auto"

    try:
        response = openai_client.chat.completions.create(**kwargs)
        return response.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")


async def _handle_anthropic(request: AssistantChatRequest) -> Dict:
    """Handle Anthropic chat completion, returning OpenAI-compatible format."""
    if not anthropic_client:
        raise HTTPException(
            status_code=503,
            detail="Anthropic client not initialized. Please set ANTHROPIC_API_KEY.",
        )

    # Convert messages and tools from OpenAI format to Anthropic format
    system_prompt, messages = _convert_openai_messages_to_anthropic(request.messages)

    kwargs = {
        "model": request.model,
        "messages": messages,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
    }

    if system_prompt:
        kwargs["system"] = system_prompt

    if request.tools and len(request.tools) > 0:
        kwargs["tools"] = _convert_openai_tools_to_anthropic(request.tools)

    # Retry once on transient Anthropic 500s (overloaded / internal server error)
    last_error = None
    for attempt in range(2):
        try:
            response = anthropic_client.messages.create(**kwargs)
            return _convert_anthropic_response_to_openai(response)
        except anthropic.BadRequestError as e:
            raise HTTPException(status_code=400, detail=f"Anthropic: {e.message}")
        except anthropic.AuthenticationError as e:
            raise HTTPException(status_code=401, detail=f"Anthropic auth error: {e.message}")
        except anthropic.RateLimitError as e:
            raise HTTPException(status_code=429, detail=f"Anthropic rate limit: {e.message}")
        except anthropic.InternalServerError as e:
            last_error = e
            if attempt == 0:
                import asyncio
                await asyncio.sleep(1)  # brief pause before retry
                continue
            raise HTTPException(status_code=502, detail=f"Anthropic internal error (retried): {e.message}")
        except anthropic.APIStatusError as e:
            raise HTTPException(status_code=e.status_code, detail=f"Anthropic API error: {e.message}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Anthropic API error: {str(e)}")
