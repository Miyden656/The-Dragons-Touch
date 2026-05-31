"""Eval harness for the Commander AI layer.

Scores model answers OBJECTIVELY so we can compare base-vs-layer-vs-future
fine-tune, and one base model against another (qwen2.5 vs llama3.1), without a
human in the loop for every run.

The trick to objective scoring without reference answers: reuse the grounding we
already built. For legality, our own safety net (commander_ai_safety) is a
truth oracle — a wrong "X is banned/legal in <format>" claim is already flagged
against Scryfall. So a legality case passes when the model addressed the card
AND produced no legality/ban contradiction. Other checks are equally mechanical:
non-empty, emitted parseable structured JSON, mentions/avoids given phrases.

Ollama-free by construction: run_eval takes a client-bearing service, so tests
inject a FakeClient and the real CLI injects a live OllamaClient.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from ai.schemas.ai_response import CommanderAIResponse

# check kinds
CHECK_NONEMPTY = "nonempty"
CHECK_SAFETY_CLEAN = "safety_clean"
CHECK_STRUCTURED = "structured"
CHECK_LEGALITY = "legality"
CHECK_MENTIONS = "mentions"

_LEGALITY_CONTRADICTION_KINDS = {"ban_contradicted", "legality_contradicted"}


@dataclass
class EvalCase:
    """One eval question + the automatic checks it must pass."""

    id: str
    question: str
    mode: str = "commander_review"
    persona: str = "balanced_unknown"
    deck: str = ""                       # optional decklist path; else a minimal synthetic deck
    checks: list[dict] = field(default_factory=list)


@dataclass
class CheckResult:
    kind: str
    passed: bool
    detail: str = ""


@dataclass
class CaseResult:
    case_id: str
    ok: bool                              # the model produced a response at all
    passed: int = 0
    total: int = 0
    checks: list[CheckResult] = field(default_factory=list)
    latency_s: float = 0.0
    error: str = ""

    @property
    def all_passed(self) -> bool:
        return self.ok and self.total > 0 and self.passed == self.total


@dataclass
class EvalReport:
    model: str
    cases: list[CaseResult] = field(default_factory=list)

    @property
    def cases_passed(self) -> int:
        return sum(1 for c in self.cases if c.all_passed)

    @property
    def checks_passed(self) -> int:
        return sum(c.passed for c in self.cases)

    @property
    def checks_total(self) -> int:
        return sum(c.total for c in self.cases)

    @property
    def avg_latency_s(self) -> float:
        timed = [c.latency_s for c in self.cases if c.latency_s > 0]
        return sum(timed) / len(timed) if timed else 0.0

    def pass_rate(self) -> float:
        return self.checks_passed / self.checks_total if self.checks_total else 0.0


# --- scoring ---------------------------------------------------------------

def score_response(response: CommanderAIResponse, checks: list[dict], *, scryfall_lookup=None) -> list[CheckResult]:
    """Run each check against one response. Pure; no model call."""
    text = (response.text or "")
    low = text.lower()
    flags = list(response.safety_flags or ())
    out: list[CheckResult] = []

    for chk in checks or []:
        kind = chk.get("type")
        if kind == CHECK_NONEMPTY:
            passed = bool(text.strip())
            out.append(CheckResult(kind, passed, "" if passed else "empty answer"))
        elif kind == CHECK_SAFETY_CLEAN:
            passed = bool(response.safety_ok)
            out.append(CheckResult(kind, passed, "" if passed else f"{len(flags)} safety flag(s)"))
        elif kind == CHECK_STRUCTURED:
            passed = response.structured is not None
            detail = "" if passed else ("parse failed" if response.parse_failed else "no JSON block")
            out.append(CheckResult(kind, passed, detail))
        elif kind == CHECK_MENTIONS:
            any_of = [str(x).lower() for x in (chk.get("any") or [])]
            none_of = [str(x).lower() for x in (chk.get("none") or [])]
            ok_any = (not any_of) or any(x in low for x in any_of)
            bad = [x for x in none_of if x in low]
            passed = ok_any and not bad
            detail = ""
            if not ok_any:
                detail = f"missing any of {any_of}"
            elif bad:
                detail = f"contains forbidden {bad}"
            out.append(CheckResult(kind, passed, detail))
        elif kind == CHECK_LEGALITY:
            card = str(chk.get("card", ""))
            # Truth oracle = our own grounded safety net. The model passes when it
            # addressed the card and produced NO legality contradiction for it.
            mentioned = card.lower() in low if card else True
            contradicted = any(
                f.get("kind") in _LEGALITY_CONTRADICTION_KINDS
                and f.get("card", "").lower() == card.lower()
                for f in flags
            )
            passed = mentioned and not contradicted
            if not mentioned:
                detail = f"did not address {card}"
            elif contradicted:
                detail = f"made a wrong legality claim about {card}"
            else:
                detail = ""
            out.append(CheckResult(kind, passed, detail))
        else:
            out.append(CheckResult(str(kind), False, "unknown check type"))
    return out


# --- running ---------------------------------------------------------------

def _minimal_analysis(commander: str = "Generic Commander") -> dict:
    """A tiny but serializer-valid analysis dict for deckless eval cases."""
    from collections import Counter
    from types import SimpleNamespace as NS

    return {
        "version_label": "EVAL",
        "runtime_config": NS(intended_bracket="Bracket 3"),
        "parsed_deck": NS(commander_name=commander, deck_card_count=100),
        "command_zone": NS(commander_name=commander, commander_names=[commander],
                           companion_names=[], commander_color_identity=[]),
        "legality": NS(deck_size_legal=True, banned_cards=[], banned_commanders=[],
                       color_identity_violations=[], cards_not_found=[], illegal_duplicate_cards=[]),
        "role_summary": NS(role_counts=Counter(), type_counts=Counter(), card_roles=[], unknown_cards=[]),
        "strategy_summary": NS(primary_strategy="Midrange", confidence="medium", warnings=[]),
        "bracket_summary": NS(estimated_bracket="Bracket 3", pressure_level="low", pressure_cards=[], notes=[]),
        "possible_cuts": NS(required_cut_candidates=[], optional_cut_candidates=[],
                            manual_review_candidates=[], playtest_first_candidates=[],
                            protected_from_cut=[], notes=[]),
    }


def _analysis_for_case(case: EvalCase, scryfall_lookup):
    """Build a real analysis if the case names a deck, else a minimal one."""
    if case.deck:
        import main
        from config import RuntimeConfig
        from parsing.deck_parser import parse_deck_file

        parsed = parse_deck_file(case.deck, scryfall_lookup=scryfall_lookup)
        runtime = RuntimeConfig(
            output_mode="normal", review_direction="both", build_up_config={},
            cut_depth_config={}, prompt_interaction_mode="guided",
            philosophy_key=case.persona, guide_preference="either",
            intended_bracket="Bracket 3", collection_mode="none",
        )
        return main.build_analysis_context(parsed, runtime, scryfall_lookup, None)
    return _minimal_analysis()


def run_eval(cases: list[EvalCase], *, service, scryfall_lookup=None, model: str = "") -> EvalReport:
    """Run all cases through one service (one model). Never raises per-case —
    a failed case is recorded with ok=False."""
    from ai.schemas.ai_context import CommanderAIRequest

    report = EvalReport(model=model or getattr(getattr(service, "config", None), "model", "?"))
    for case in cases:
        started = time.perf_counter()
        try:
            analysis = _analysis_for_case(case, scryfall_lookup)
            request = CommanderAIRequest(user_text=case.question, mode=case.mode, pet_cards=())
            response = service.answer(request, analysis)
            latency = time.perf_counter() - started
            if not response.ok:
                report.cases.append(CaseResult(case.id, ok=False, latency_s=latency,
                                               error=response.error or "no answer"))
                continue
            checks = score_response(response, case.checks, scryfall_lookup=scryfall_lookup)
            report.cases.append(CaseResult(
                case.id, ok=True,
                passed=sum(1 for c in checks if c.passed), total=len(checks),
                checks=checks, latency_s=latency,
            ))
        except Exception as exc:  # noqa: BLE001 - one bad case must not abort the run
            report.cases.append(CaseResult(case.id, ok=False,
                                           latency_s=time.perf_counter() - started, error=repr(exc)))
    return report


# --- the built-in starter eval set -----------------------------------------

DEFAULT_EVAL_CASES: list[EvalCase] = [
    EvalCase(
        id="legality_sol_ring_legacy",
        question="Is Sol Ring legal in Legacy? Answer in one short sentence.",
        checks=[{"type": CHECK_NONEMPTY}, {"type": CHECK_LEGALITY, "card": "Sol Ring"}],
    ),
    EvalCase(
        id="legality_mana_crypt_commander",
        question="Is Mana Crypt currently banned in Commander? Answer in one short sentence.",
        checks=[{"type": CHECK_NONEMPTY}, {"type": CHECK_LEGALITY, "card": "Mana Crypt"}],
    ),
    EvalCase(
        id="legality_lightning_bolt_modern",
        question="Is Lightning Bolt legal in Modern? Answer in one short sentence.",
        checks=[{"type": CHECK_NONEMPTY}, {"type": CHECK_LEGALITY, "card": "Lightning Bolt"}],
    ),
    EvalCase(
        id="legality_black_lotus_commander",
        question="Is Black Lotus legal in Commander? Answer in one short sentence.",
        checks=[{"type": CHECK_NONEMPTY}, {"type": CHECK_LEGALITY, "card": "Black Lotus"}],
    ),
    EvalCase(
        id="review_safety_and_structure",
        question="Give me a quick review of this deck's gameplan.",
        mode="commander_review",
        checks=[{"type": CHECK_NONEMPTY}, {"type": CHECK_SAFETY_CLEAN}, {"type": CHECK_STRUCTURED}],
    ),
    EvalCase(
        id="cut_review_structure",
        question="What are one or two reasonable cuts, and why?",
        mode="cut_review",
        checks=[{"type": CHECK_NONEMPTY}, {"type": CHECK_SAFETY_CLEAN}, {"type": CHECK_STRUCTURED}],
    ),
]
