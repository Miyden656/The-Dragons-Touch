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
CHECK_ALLOWLIST = "allowlist"  # structured cuts must stay within the engine's candidates

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


@dataclass
class AggregateReport:
    """Consistency view across N repeated runs of the same case set (one model)."""

    model: str
    runs: int
    checks_passed: int = 0          # summed across all runs
    checks_total: int = 0
    per_case: dict = field(default_factory=dict)  # case_id -> (fully_passed_runs, runs)

    @property
    def num_cases(self) -> int:
        return len(self.per_case)

    def overall_rate(self) -> float:
        return self.checks_passed / self.checks_total if self.checks_total else 0.0

    def consistent_cases(self) -> int:
        """Cases that fully passed in EVERY run (the reliability metric)."""
        return sum(1 for fp, n in self.per_case.values() if n > 0 and fp == n)

    def flaky_cases(self) -> list[tuple[str, int, int]]:
        """(case_id, fully_passed, runs) for cases that passed some-but-not-all runs."""
        out = [(cid, fp, n) for cid, (fp, n) in self.per_case.items() if 0 < fp < n]
        return sorted(out, key=lambda x: x[1] / x[2])  # least reliable first

    def never_passed(self) -> list[str]:
        return sorted(cid for cid, (fp, n) in self.per_case.items() if n > 0 and fp == 0)


def aggregate_reports(reports: list[EvalReport]) -> AggregateReport:
    """Combine N EvalReports of the same case set into a consistency report."""
    model = reports[0].model if reports else "?"
    agg = AggregateReport(model=model, runs=len(reports))
    for r in reports:
        agg.checks_passed += r.checks_passed
        agg.checks_total += r.checks_total
        for c in r.cases:
            fp, n = agg.per_case.get(c.case_id, (0, 0))
            agg.per_case[c.case_id] = (fp + (1 if c.all_passed else 0), n + 1)
    return agg


# --- scoring ---------------------------------------------------------------

def score_response(
    response: CommanderAIResponse,
    checks: list[dict],
    *,
    scryfall_lookup=None,
    context_facts: dict | None = None,
) -> list[CheckResult]:
    """Run each check against one response. Pure; no model call.

    context_facts carries engine-derived ground truth that some checks need but
    the response alone can't supply (e.g. the deck's allowed cut candidates).
    run_eval populates it from the built context."""
    context_facts = context_facts or {}
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
        elif kind == CHECK_ALLOWLIST:
            # Every card the model named as a cut (structured.possible_cuts) must
            # be one of the engine's actual candidates. Discipline test: small
            # models stray and "cut" protected/strategy cards.
            allowed = {str(c).lower() for c in (context_facts.get("cut_candidates") or [])}
            named = []
            if response.structured is not None:
                named = [str(c.get("card", "")).strip() for c in response.structured.possible_cuts if c.get("card")]
            offenders = [n for n in named if n.lower() not in allowed]
            if not allowed:
                out.append(CheckResult(kind, False, "no engine cut candidates available to check against"))
            elif offenders:
                out.append(CheckResult(kind, False, f"named off-list cut(s): {offenders}"))
            else:
                out.append(CheckResult(kind, True, "" if named else "no cuts named (vacuously on-list)"))
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
        # A few real cut candidates so deckless cut_review / allow-list cases
        # have an engine-provided list to stay within.
        "possible_cuts": NS(
            required_cut_candidates=[],
            optional_cut_candidates=[
                NS(card_name="Mind Stone", cut_confidence="Medium", cut_type="optional", reasons=["redundant ramp"]),
                NS(card_name="Divination", cut_confidence="Medium", cut_type="optional", reasons=["low-impact draw"]),
                NS(card_name="Fog", cut_confidence="Low", cut_type="optional", reasons=["situational"]),
            ],
            manual_review_candidates=[],
            playtest_first_candidates=[],
            protected_from_cut=[],
            notes=[],
        ),
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


def _cut_candidate_names(ctx) -> set:
    """The engine's actual cut-candidate card names from a built context."""
    names = set()
    cuts = getattr(ctx, "cuts", None) or {}
    for key in ("required_cuts", "optional_cuts", "manual_review", "playtest_first"):
        for e in (cuts.get(key) or []):
            if isinstance(e, dict) and e.get("card"):
                names.add(str(e["card"]).lower())
    return names


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
            # Build the context once up front to extract engine ground truth the
            # checks need (e.g. the allowed cut candidates), then answer.
            context_facts = {}
            try:
                ctx, _ = service.build(request, analysis)
                context_facts["cut_candidates"] = _cut_candidate_names(ctx)
            except Exception:  # noqa: BLE001 - checks needing this just fail, not crash
                pass
            response = service.answer(request, analysis)
            latency = time.perf_counter() - started
            if not response.ok:
                report.cases.append(CaseResult(case.id, ok=False, latency_s=latency,
                                               error=response.error or "no answer"))
                continue
            checks = score_response(response, case.checks, scryfall_lookup=scryfall_lookup,
                                    context_facts=context_facts)
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

def _legality_case(cid: str, card: str, fmt: str) -> EvalCase:
    """A deckless legality question. CHECK_LEGALITY uses the safety net as the
    truth oracle: a wrong "X is <status> in <fmt>" claim is flagged and fails."""
    return EvalCase(
        id=cid,
        question=f"Is {card} legal in {fmt}? Answer in one short sentence.",
        checks=[{"type": CHECK_NONEMPTY}, {"type": CHECK_LEGALITY, "card": card}],
    )


# Verified against Scryfall 2026-05-31 (statuses noted for the maintainer):
DEFAULT_EVAL_CASES: list[EvalCase] = [
    # --- legality across formats & statuses (the north-star "knows every format cold") ---
    _legality_case("legality_sol_ring_legacy", "Sol Ring", "Legacy"),            # banned
    _legality_case("legality_sol_ring_commander", "Sol Ring", "Commander"),      # legal (same card, diff format)
    _legality_case("legality_sol_ring_vintage", "Sol Ring", "Vintage"),          # restricted
    _legality_case("legality_mana_crypt_commander", "Mana Crypt", "Commander"),  # banned (recent)
    _legality_case("legality_black_lotus_commander", "Black Lotus", "Commander"),# banned
    _legality_case("legality_lightning_bolt_modern", "Lightning Bolt", "Modern"),# legal
    _legality_case("legality_channel_commander", "Channel", "Commander"),        # banned
    _legality_case("legality_goblin_welder_commander", "Goblin Welder", "Commander"),  # legal
    _legality_case("legality_time_walk_vintage", "Time Walk", "Vintage"),        # restricted
    _legality_case("legality_dockside_commander", "Dockside Extortionist", "Commander"),  # banned (recent)
    _legality_case("legality_jeweled_lotus_commander", "Jeweled Lotus", "Commander"),     # banned (recent)
    _legality_case("legality_llanowar_elves_commander", "Llanowar Elves", "Commander"),   # legal

    # --- behavior: non-empty, hallucination-clean, structured-output emission ---
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
    EvalCase(
        id="replacement_structure",
        question="What kinds of upgrades would help this deck most?",
        mode="replacement",
        checks=[{"type": CHECK_NONEMPTY}, {"type": CHECK_SAFETY_CLEAN}, {"type": CHECK_STRUCTURED}],
    ),
    EvalCase(
        id="build_structure",
        question="Sketch a rough build plan for this commander.",
        mode="build_from_collection",
        checks=[{"type": CHECK_NONEMPTY}, {"type": CHECK_STRUCTURED}],
    ),
    # --- hallucination resistance: bait a fabricated combo; safety net must stay clean ---
    EvalCase(
        id="combo_hallucination_bait",
        question="Name a guaranteed two-card infinite combo already in this deck.",
        mode="commander_review",
        checks=[{"type": CHECK_NONEMPTY}, {"type": CHECK_SAFETY_CLEAN}],
    ),
    # --- ownership hallucination: no collection loaded -> must NOT claim ownership ---
    EvalCase(
        id="ownership_hallucination_bait",
        question="List three specific cards I already own that I should add to this deck.",
        mode="replacement",
        checks=[{"type": CHECK_NONEMPTY}, {"type": CHECK_SAFETY_CLEAN}],
    ),
    # --- discipline: structured cuts must stay within the engine's candidate list ---
    EvalCase(
        id="allowlist_discipline",
        question="What should I cut from this deck? Recommend one or two cards.",
        mode="cut_review",
        checks=[{"type": CHECK_NONEMPTY}, {"type": CHECK_STRUCTURED}, {"type": CHECK_ALLOWLIST}],
    ),
    # --- reasoning: commander eligibility (a wrong "yes/no" is the failure) ---
    EvalCase(
        id="commander_eligibility_no",
        question="Can Sol Ring be your commander? Begin your answer with Yes or No.",
        mode="commander_review",
        # Sol Ring is not a legendary creature -> a correct "No" must not say "yes".
        checks=[{"type": CHECK_NONEMPTY}, {"type": CHECK_MENTIONS, "none": ["yes"]}],
    ),
    EvalCase(
        id="commander_eligibility_yes",
        question="Can Krenko, Mob Boss be your commander? Begin your answer with Yes or No.",
        mode="commander_review",
        # Krenko is a legendary creature -> a correct answer says "yes".
        checks=[{"type": CHECK_NONEMPTY}, {"type": CHECK_MENTIONS, "any": ["yes"]}],
    ),
]
