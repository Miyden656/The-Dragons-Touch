"""Per-deck conversation memory.

A ConversationSession stores the short back-and-forth (user text + assistant
reply) so follow-up turns have continuity. It deliberately stores ONLY the
conversational text, never the full context-laden user prompt — the latest turn
always carries fresh engine context, so re-sending stale context would waste the
model's window and risk contradicting current deck state.

In-memory by default (SessionStore). Persistence to disk can be layered on later
without changing this interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_MAX_TURNS = 12  # keep the last N messages (user+assistant combined)


@dataclass
class ConversationSession:
    session_id: str
    deck_key: str = ""
    max_turns: int = DEFAULT_MAX_TURNS
    _turns: list[dict] = field(default_factory=list)

    def add_user(self, text: str) -> None:
        self._append("user", text)

    def add_assistant(self, text: str) -> None:
        self._append("assistant", text)

    def history(self) -> list[dict]:
        """Prior turns as [{role, content}], ready to splice into build_messages."""
        return [dict(t) for t in self._turns]

    def reset(self) -> None:
        self._turns.clear()

    def __len__(self) -> int:
        return len(self._turns)

    def _append(self, role: str, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return
        self._turns.append({"role": role, "content": text})
        if self.max_turns >= 0 and len(self._turns) > self.max_turns:
            # drop the oldest, keeping the most recent max_turns messages
            self._turns = self._turns[-self.max_turns:]


class SessionStore:
    """In-memory registry of conversations keyed by session id."""

    def __init__(self, max_turns: int = DEFAULT_MAX_TURNS) -> None:
        self._sessions: dict[str, ConversationSession] = {}
        self._max_turns = max_turns

    def get_or_create(self, session_id: str, *, deck_key: str = "") -> ConversationSession:
        session = self._sessions.get(session_id)
        if session is None:
            session = ConversationSession(
                session_id=session_id, deck_key=deck_key, max_turns=self._max_turns
            )
            self._sessions[session_id] = session
        elif deck_key and session.deck_key != deck_key:
            # The deck changed under this session id — start a clean conversation.
            session.deck_key = deck_key
            session.reset()
        return session

    def drop(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def __len__(self) -> int:
        return len(self._sessions)
