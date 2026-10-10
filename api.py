"""HTTP adapter for the existing compiled graph; run from the project root."""

import json
import logging
from threading import Lock
from typing import Any
from weakref import WeakValueDictionary

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, Field, field_validator

from Agent import app as agent_app

logger = logging.getLogger(__name__)
app = FastAPI(title="Mizaan API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, description="The user's message")
    session_id: str = Field(min_length=1, description="Conversation thread ID")

    @field_validator("message", "session_id")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Must not be blank")
        return value


class ChatResponse(BaseModel):
    answer: str
    dashboard: dict[str, Any] | None = None


def extract_answer(messages: list) -> str:
    """Expose final model text only, never metadata or tool-call blocks."""
    for message in reversed(messages):
        if not isinstance(message, AIMessage) or message.tool_calls:
            continue
        content = message.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(
                block["text"]
                for block in content
                if isinstance(block, dict)
                and block.get("type") == "text"
                and isinstance(block.get("text"), str)
            )
        return ""
    return ""


def extract_dashboard(messages: list) -> dict[str, Any] | None:
    """Parse the latest optimizer ToolMessage without reshaping its JSON."""
    for message in reversed(messages):
        if not isinstance(message, ToolMessage) or message.name != "optimize_farm_plan":
            continue
        try:
            parsed = json.loads(message.content) if isinstance(message.content, str) else None
        except (ValueError, TypeError):
            return None
        return parsed if isinstance(parsed, dict) else None
    return None


# Serialize calls in the same conversation; independent sessions can run together.
# Weak references avoid retaining locks for sessions that are no longer running.
_session_locks = WeakValueDictionary()
_locks_guard = Lock()


def session_lock(session_id: str):
    with _locks_guard:
        lock = _session_locks.get(session_id)
        if lock is None:
            lock = Lock()
            _session_locks[session_id] = lock
        return lock


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        with session_lock(request.session_id):
            result = agent_app.invoke(
                {"messages": [HumanMessage(content=request.message)]},
                config={"configurable": {"thread_id": request.session_id}},
            )
        messages = result.get("messages") or []
        return ChatResponse(
            answer=extract_answer(messages),
            dashboard=extract_dashboard(messages),
        )
    except Exception:
        logger.exception("Agent invocation failed")
        raise HTTPException(status_code=502, detail="تعذر الحصول على رد من الوكيل. يرجى المحاولة مرة أخرى.") from None
