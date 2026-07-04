"""POST /chat — send a message to the AI brain and get a reply.

You can send the simple form `{"message": "Hi"}` or the full form
`{"messages": [{"role": "user", "content": "Hi"}]}`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from nova.ai.schemas import ChatRequest, Message
from nova.api.deps import get_context
from nova.api.schemas import ChatIn, ChatOut
from nova.context import NovaContext
from nova.core.exceptions import ProviderUnavailableError

router = APIRouter(tags=["ai"])


@router.post("/chat", response_model=ChatOut)
async def chat(body: ChatIn, context: NovaContext = Depends(get_context)) -> ChatOut:
    # Figure out the list of messages from whichever form the caller used.
    if body.messages:
        messages = list(body.messages)
    elif body.message:
        messages = [Message(role="user", content=body.message)]
    else:
        raise HTTPException(status_code=400, detail="Provide either 'message' or 'messages'.")

    # Give Nova its personality: if the caller didn't include a system message,
    # add the one from settings so the assistant knows it's "Nova".
    if not any(m.role == "system" for m in messages):
        messages.insert(0, Message(role="system", content=context.settings.ai.system_prompt))

    request = ChatRequest(
        messages=messages,
        model=body.model,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
    )

    try:
        response = await context.ai.chat(request)
    except ProviderUnavailableError as exc:
        # 503 = "Service Unavailable" — the AI brain isn't reachable right now.
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ChatOut(content=response.content, model=response.model, provider=response.provider)
