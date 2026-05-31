"""Phase 7: QA / regression matrix for the whole Commander AI layer.

A broad, Ollama-free battery (FakeClient) that exercises the full pipeline
across the cross-product of modes x guide styles x personas, plus targeted
scenarios (banned card, no collection, garbage input) and a hallucination-
resistance battery. The point is to catch a combination that breaks assembly
or safety — the kind of regression a single happy-path test misses.

Run via tests/run_all.py.
"""
from __future__ import annotations

from collections import Counter
from types import SimpleNamespace as NS

from _test_helpers import TestRun

from ai.commander_ai_config import from_settings, normalize_guide_style
from ai.commander_ai_guide_styles import available_styles
from ai.commander_ai_prompts import STRUCTURED_MODES
from ai.commander_ai_service import CommanderAIService
from ai.ollama_client import OllamaChatResult
from ai.schemas.ai_context import ALL_MODES, CommanderAIRequest
from ai.schemas.ai_response import CommanderAIResponse, CommanderAIStructured


class FakeClient:
    def __init__(self, text: str = "A short grounded answer.") -> None:
        self.result = OllamaChatResult(ok=True, text=text, model="fake")

    def chat(self, messages, **kwargs):
        return self.result

    def stream_chat(self, messages, *, on_delta=None, **kwargs):
        if on_delta:
            on_delta(self.result.text)
        return self.result


def _philosophy_context(key: str) -> dict:
    """Real engine persona context for `key` (authentic bias lists)."""
    try:
        from analysis.deck_building_philosophies import build_philosophy_context

        return build_philosophy_context(key)
    except Exception:  # noqa: BLE001
        return {"key": key, "label": key}


def _analysis(*, banned=False, collection=False, philosophy="balanced_unknown") -> dict:
    banned_cards = ["Mana Crypt"] if banned else []
    coll = NS(
        candidate_matching_active=collection,
        strong_candidates=([NS(card_name="Goblin Chieftain", quantity_owned=1, confidence="High",
                                matched_needs=[], reason="owned")] if collection else []),
        possible_candidates=[],
    )
    return {
        "version_label": "TEST",
        "runtime_config": NS(intended_bracket="Bracket 3"),
        "parsed_deck": NS(commander_name="Krenko, Mob Boss", deck_card_count=100),
        "command_zone": NS(commander_name="Krenko, Mob Boss", commander_names=["Krenko, Mob Boss"],
                           companion_names=[], commander_color_identity=["R"],
                           commander_color_identity_text="Mono-Red"),
        "legality": NS(deck_size_legal=True, expected_deck_size=100, has_any_issues=bool(banned),
                       banned_cards=banned_cards, banned_commanders=[], color_identity_violations=[],
                       cards_not_found=[], illegal_duplicate_cards=[]),
        "role_summary": NS(role_counts=Counter({"Ramp": 10}), type_counts=Counter({"Creature": 30}),
                           card_roles=[NS(card_name="Sol Ring", quantity=1, detected_roles=["ramp"],
                                          mana_value=1, card_types=["Artifact"])], unknown_cards=[]),
        "strategy_summary": NS(primary_strategy="Goblins", secondary_strategy="", confidence="high",
                               warnings=[], core_synergy_packages=[], candidates=[]),
        "plan_fit_summary": NS(strong_synergy_cards=[], possible_off_plan_cards=[]),
        "bracket_summary": NS(estimated_bracket="Bracket 3", pressure_level="low", pressure_cards=[], notes=[]),
        "possible_cuts": NS(required_cut_candidates=[],
                            optional_cut_candidates=[NS(card_name="Mind Stone", cut_confidence="Medium",
                                                        cut_type="optional", reasons=["redundant ramp"])],
                            manual_review_candidates=[], playtest_first_candidates=[],
                            protected_from_cut=[], notes=[]),
        "protected_cards": [],
        "replacement_needs": NS(priority_categories=["More draw"],
                                need_details=[NS(category="More draw", priority="high", reason="low draw")]),
        "replacement_candidates": NS(top_ranked_candidates=[], candidates=[]),
        "collection_candidates": coll,
        "philosophy_context": _philosophy_context(philosophy),
    }


def _service(text: str = "A short grounded answer.") -> CommanderAIService:
    return CommanderAIService(from_settings({}), client=FakeClient(text))


def main() -> None:
    t = TestRun("ai_regression_matrix")
    analysis = _analysis()

    # === 1. cross-product: every mode x every guide style assembles + answers ===
    styles = available_styles()
    t.true("has 4 guide styles", len(styles) == 4)
    combo_failures = []
    answer_failures = []
    for mode in ALL_MODES:
        for style in styles:
            svc = CommanderAIService(from_settings({"commander_ai_guide_style": style}), client=FakeClient())
            req = CommanderAIRequest(user_text="Help me with this deck.", mode=mode)
            try:
                ctx, messages = svc.build(req, analysis)
                sys_text = messages[0]["content"]
                if normalize_guide_style(style).capitalize() not in sys_text:
                    combo_failures.append(f"{mode}/{style}: style missing")
                if not messages or messages[-1]["role"] != "user":
                    combo_failures.append(f"{mode}/{style}: bad messages")
                resp = svc.answer(req, analysis)
                if not (resp.ok and resp.text):
                    answer_failures.append(f"{mode}/{style}")
            except Exception as exc:  # noqa: BLE001
                combo_failures.append(f"{mode}/{style}: raised {exc!r}")
    t.eq("all mode x style assemble cleanly", combo_failures, [])
    t.eq("all mode x style answer ok", answer_failures, [])

    # === 2. all 22 personas flow through without crashing ===
    persona_failures = []
    try:
        from analysis.deck_building_philosophies import PHILOSOPHY_PROFILES
        persona_keys = list(PHILOSOPHY_PROFILES.keys())
    except Exception:  # noqa: BLE001
        persona_keys = ["balanced_unknown", "pet_card", "spike"]
    for key in persona_keys:
        a = _analysis(philosophy=key)
        try:
            ctx, messages = _service().build(CommanderAIRequest(user_text="x", mode="commander_review"), a)
            if ctx.persona.get("key") != key:
                persona_failures.append(f"{key}: ctx persona {ctx.persona.get('key')}")
        except Exception as exc:  # noqa: BLE001
            persona_failures.append(f"{key}: raised {exc!r}")
    t.true("exercised many personas", len(persona_keys) >= 18)
    t.eq("all personas flow cleanly", persona_failures, [])

    # === 3. persona bias actually lands in the prompt ===
    pet_ctx, pet_msgs = _service().build(
        CommanderAIRequest(user_text="cuts?", mode="cut_review"), _analysis(philosophy="pet_card")
    )
    pet_sys = pet_msgs[0]["content"]
    t.true("pet_card label in prompt", "Pet Card" in pet_sys)
    t.true("pet_card protect bias rendered", "pet card" in pet_sys.lower())

    # === 4. scenario battery ===
    # banned card -> surfaced as a warning; engine-echoed ban not false-flagged
    banned_ctx, _ = _service().build(CommanderAIRequest(user_text="legal?", mode="commander_review"),
                                     _analysis(banned=True))
    t.true("banned card surfaced in warnings", any("Mana Crypt" in w for w in banned_ctx.warnings))
    r = _service("Note that Mana Crypt is banned, so it's excluded.").answer(
        CommanderAIRequest(user_text="legal?", mode="commander_review"), _analysis(banned=True)
    )
    t.true("engine-listed ban not flagged", r.safety_ok)

    # no collection -> an uncertainty is surfaced
    nocoll_ctx, _ = _service().build(CommanderAIRequest(user_text="build?", mode="build_from_collection"),
                                     _analysis(collection=False))
    t.true("no-collection uncertainty surfaced",
           any("collection" in u.lower() for u in nocoll_ctx.uncertainties))

    # garbage / empty analysis -> never crashes, returns a response
    raised = ""
    try:
        gr = _service().answer(CommanderAIRequest(user_text="hi", mode="commander_review"), {})
    except Exception as exc:  # noqa: BLE001
        raised = repr(exc)
    t.eq("empty analysis did not raise", raised, "")
    t.true("empty analysis still returns a response", isinstance(gr, CommanderAIResponse) and gr.ok)

    raised = ""
    try:
        _service().answer(CommanderAIRequest(user_text="hi", mode="not_a_real_mode"), _analysis())
    except Exception as exc:  # noqa: BLE001
        raised = repr(exc)
    t.eq("unknown mode did not raise", raised, "")

    # === 5. hallucination-resistance battery ===
    lookup = _legality_lookup()
    fabricated = (
        "You already own Dockside Extortionist, so add it. "
        "Sol Ring is banned in Commander. "
        "This deck goes infinite with a two-card combo."
    )
    svc = CommanderAIService(from_settings({}), client=FakeClient(fabricated), scryfall_lookup=lookup)
    rh = svc.answer(CommanderAIRequest(user_text="review", mode="commander_review"), _analysis())
    kinds = {f["kind"] for f in rh.safety_flags}
    t.eq("fabrication response not safety_ok", rh.safety_ok, False)
    t.true("fabricated ownership caught", "ownership_unverified" in kinds)
    t.true("wrong ban caught (real legality)",
           "ban_contradicted" in kinds or "ban_unverified" in kinds)
    t.true("unverified combo caught", "combo_unverified" in kinds)
    t.true("strict footer appended", "Fact-check notes" in rh.text)

    clean = "This deck wants to go wide with Goblins and close with a big swing. Sol Ring ramps you."
    rc = CommanderAIService(from_settings({}), client=FakeClient(clean), scryfall_lookup=lookup).answer(
        CommanderAIRequest(user_text="review", mode="commander_review"), _analysis()
    )
    t.true("clean grounded answer passes safety", rc.safety_ok)
    t.true("clean answer has no footer", "Fact-check notes" not in rc.text)

    # === 6. structured output: attached for structured modes, absent for chat ===
    json_answer = 'Cut Mind Stone.\n```json\n{"summary":"trim ramp","confidence":"medium","possible_cuts":[{"card":"Mind Stone","reason":"redundant"}]}\n```'
    for mode in STRUCTURED_MODES:
        resp = _service(json_answer).answer(CommanderAIRequest(user_text="cuts?", mode=mode), analysis)
        t.true(f"{mode}: structured attached", isinstance(resp.structured, CommanderAIStructured))
        t.true(f"{mode}: prose cleaned of json", "```" not in resp.text)
    chat_resp = _service(json_answer).answer(
        CommanderAIRequest(user_text="coach me", mode="persona_coaching"), analysis
    )
    # parser still strips a stray block, but conversational modes were not asked for one
    t.true("persona_coaching not in structured modes", "persona_coaching" not in STRUCTURED_MODES)
    t.eq("persona_coaching ok", chat_resp.ok, True)

    t.report_and_exit()


def _legality_lookup() -> dict:
    """Use the real Scryfall lookup if present; else a tiny stub so the
    hallucination battery still runs (Sol Ring legal in commander, etc.)."""
    try:
        from _test_helpers import load_scryfall_or_skip  # noqa: F401
        import json
        from pathlib import Path
        from _test_helpers import PROJECT_ROOT

        path = PROJECT_ROOT / "data" / "scryfall_cards.json"
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            cards = raw if isinstance(raw, list) else raw.get("data", [])
            return {(c.get("name") or "").lower(): c for c in cards if isinstance(c, dict)}
    except Exception:  # noqa: BLE001
        pass
    return {
        "sol ring": {"name": "Sol Ring", "legalities": {"commander": "legal", "legacy": "banned"}},
        "dockside extortionist": {"name": "Dockside Extortionist", "legalities": {"commander": "banned"}},
    }


if __name__ == "__main__":
    main()
