"""Commander AI service — the single orchestration entry point.

One call does the whole chain:
    analysis dict + request
      -> serialize_context        (Phase 3)
      -> build_messages           (Phase 4)
      -> Ollama chat / stream      (Phase 2)
      -> verify_response (safety)  (Phase 4)
      -> CommanderAIResponse

The UI and CLI talk only to this class. It never raises on an Ollama failure —
a down/slow/missing model becomes a CommanderAIResponse with ok=False and a
friendly message, exactly like the client layer guarantees.
"""

from __future__ import annotations

from typing import Any, Callable

from ai.commander_ai_config import CommanderAIConfig
from ai.commander_ai_prompts import build_messages
from ai.commander_ai_safety import verify_response
from ai.commander_ai_sessions import ConversationSession
from ai.context.context_serializer import serialize_context
from ai.ollama_client import OllamaClient
from ai.schemas.ai_context import CommanderAIContext, CommanderAIRequest
from ai.schemas.ai_response import CommanderAIResponse


class CommanderAIService:
    def __init__(
        self,
        config: CommanderAIConfig,
        *,
        client: Any | None = None,
        scryfall_lookup: dict | None = None,
    ) -> None:
        self.config = config
        # client is injectable so tests (and future runtimes) can supply a fake.
        self.client = client if client is not None else OllamaClient(config)
        self.scryfall_lookup = scryfall_lookup

    # -- prompt building (also used by CLI --dry-run and tests) -------------

    def build(
        self,
        request: CommanderAIRequest,
        analysis: dict,
        *,
        session: ConversationSession | None = None,
        history: list[dict] | None = None,
        combo_summary: Any | None = None,
    ) -> tuple[CommanderAIContext, list[dict]]:
        ctx = serialize_context(
            analysis, request, guide_style=self.config.guide_style, combo_summary=combo_summary
        )
        hist = history if history is not None else (session.history() if session else None)
        messages = build_messages(ctx, history=hist)
        return ctx, messages

    # -- the main entry point ---------------------------------------------

    def answer(
        self,
        request: CommanderAIRequest,
        analysis: dict,
        *,
        session: ConversationSession | None = None,
        history: list[dict] | None = None,
        combo_summary: Any | None = None,
        on_delta: Callable[[str], None] | None = None,
    ) -> CommanderAIResponse:
        ctx, messages = self.build(
            request, analysis, session=session, history=history, combo_summary=combo_summary
        )

        if self.config.stream or on_delta is not None:
            result = self.client.stream_chat(messages, on_delta=on_delta)
        else:
            result = self.client.chat(messages)

        if not result.ok:
            return CommanderAIResponse.from_error(
                error=result.error or "The local Commander AI could not produce a response.",
                kind=result.kind or "error",
                mode=ctx.mode,
                model=result.model or self.config.model,
            )

        report = verify_response(
            result.text,
            ctx,
            scryfall_lookup=self.scryfall_lookup,
            strict=self.config.strict_fact_check,
        )

        # Record the turn for continuity (short text only — see sessions module).
        if session is not None:
            session.add_user(request.user_text)
            session.add_assistant(result.text)

        return CommanderAIResponse(
            ok=True,
            text=report.annotated_text or result.text,
            raw_text=result.text,
            mode=ctx.mode,
            guide_style=ctx.guide_style,
            model=result.model or self.config.model,
            safety_ok=report.ok,
            safety_flags=tuple(
                {"kind": f.kind, "card": f.card, "note": f.note} for f in report.flags
            ),
            meta=dict(ctx.meta),
        )

    # -- convenience -------------------------------------------------------

    def is_available(self):
        """Pass-through to the client's availability check."""
        return self.client.is_available()
