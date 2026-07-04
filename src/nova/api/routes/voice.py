"""/voice endpoints — turn text into speech (tts) and audio into text (stt).

Reminder: today's engines are PLACEHOLDERS. These endpoints prove the shape of
the feature works; real audio arrives when real engines are plugged in.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response

from nova.api.deps import get_context
from nova.api.schemas import VoiceSpeakIn
from nova.context import NovaContext

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/tts")
async def text_to_speech(
    body: VoiceSpeakIn, context: NovaContext = Depends(get_context)
) -> Response:
    """Turn text into audio bytes. Returns raw bytes (placeholder for now)."""
    audio = await context.voice.speak(body.text)
    return Response(
        content=audio,
        media_type="application/octet-stream",
        headers={"X-Voice-Engine": context.voice.tts.name},
    )


@router.post("/stt")
async def speech_to_text(
    request: Request, context: NovaContext = Depends(get_context)
) -> dict[str, str]:
    """Turn uploaded audio bytes into text. Send raw audio as the request body."""
    audio = await request.body()
    text = await context.voice.listen(audio)
    return {"engine": context.voice.stt.name, "text": text}
