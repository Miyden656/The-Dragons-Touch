"""Phase 4.5 tests: conversation session memory. Run via tests/run_all.py."""
from __future__ import annotations

from _test_helpers import TestRun

from ai.commander_ai_sessions import ConversationSession, SessionStore


def main() -> None:
    t = TestRun("ai_sessions")

    store = SessionStore()
    s1 = store.get_or_create("deck-A", deck_key="krenko")
    s1b = store.get_or_create("deck-A", deck_key="krenko")
    t.true("same id returns same session", s1 is s1b)
    t.eq("store has one session", len(store), 1)

    s1.add_user("What should I cut?")
    s1.add_assistant("Consider these review candidates...")
    hist = s1.history()
    t.eq("history length 2", len(hist), 2)
    t.eq("first turn is user", hist[0]["role"], "user")
    t.eq("first turn content", hist[0]["content"], "What should I cut?")
    t.eq("second turn is assistant", hist[1]["role"], "assistant")

    # empty/whitespace text is ignored
    s1.add_user("   ")
    t.eq("blank user text ignored", len(s1), 2)

    # max-turns cap keeps the most recent
    capped = ConversationSession(session_id="c", max_turns=4)
    for i in range(10):
        capped.add_user(f"q{i}")
    t.eq("cap keeps last 4", len(capped), 4)
    t.eq("oldest kept is q6", capped.history()[0]["content"], "q6")

    # reset clears
    s1.reset()
    t.eq("reset clears turns", len(s1), 0)

    # changing the deck under the same id resets the conversation
    s1.add_user("stale")
    s2 = store.get_or_create("deck-A", deck_key="atraxa")
    t.true("deck change returns same object", s2 is s1)
    t.eq("deck change reset history", len(s2), 0)
    t.eq("deck key updated", s2.deck_key, "atraxa")

    # drop removes
    store.drop("deck-A")
    t.eq("drop removes session", len(store), 0)

    t.report_and_exit()


if __name__ == "__main__":
    main()
