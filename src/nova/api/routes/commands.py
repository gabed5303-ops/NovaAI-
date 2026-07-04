"""/commands endpoints — list available commands and run one by name."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from nova.api.deps import get_context
from nova.api.schemas import CommandRunIn
from nova.context import NovaContext
from nova.core.exceptions import CommandError

router = APIRouter(prefix="/commands", tags=["commands"])


@router.get("")
async def list_commands(context: NovaContext = Depends(get_context)) -> list[dict[str, str]]:
    """List every command Nova knows (added by plugins)."""
    return [{"name": c.name, "description": c.description} for c in context.commands.all()]


@router.post("/{name}")
async def run_command(
    name: str,
    body: CommandRunIn | None = None,
    context: NovaContext = Depends(get_context),
) -> dict[str, Any]:
    """Run the command called `name`, passing optional `args`."""
    args = body.args if body else {}
    try:
        result = await context.commands.run(name, args)
    except CommandError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"command": name, "result": result}
