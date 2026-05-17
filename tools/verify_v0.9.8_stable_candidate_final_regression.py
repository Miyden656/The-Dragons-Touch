from pathlib import Path
import sys
from collections import Counter

ERROR_TOKENS = [
    "NameError",
    "RecursionError",
    "IndexError",
    "SyntaxError",
    "Traceback (most recent call last)",
]

RAW_TRIGGER_TOKENS = [
    " — triggered by: ReplacementNeedSummary(",
    " — triggered by: ReplacementNeedDetail(",
]

REQUIRED_REPORT_TEXT = [
    "## Replacement Candidate Engine Preview",
    "## Full-Card-Pool Fallback Preview",
    "collection-first remains primary",
    "Automatic swaps: No",
]

FIELD_SURFACE_TERMS = {
    "source": ["source", "collection", "full-card-pool", "full card pool", "owned"],
    "ownership": ["owned", "ownership", "not owned-card claims", "not claimed as owned", "not necessarily owned"],
    "confidence": ["confidence"],
    "explanation": ["why it fits", "fit", "supports", "commander", "strategy", "plan"],
    "caution": ["caution", "budget", "bracket", "table fit", "table-fit", "power", "price data source"],
    "filter_reason": ["manual review", "filtered", "not confirmed owned", "not claimed as owned", "color identity not verified", "do_not_recommend"],
    "preference": ["protected", "pet card", "category-only", "exact full-pool", "combo-card examples stay suppressed", "automatic swaps: no"],
}

ARCHETYPE_KEYWORDS = {
    "Tokens": ["token", "go-wide", "creature tokens"],
    "Aristocrats / Sacrifice": ["aristocrat", "sacrifice", "dies", "death trigger"],
    "Voltron / Combat": ["voltron", "equipment", "aura", "combat damage", "evasion", "trample"],
    "Spellslinger": ["spellslinger", "instant", "sorcery", "noncreature spell", "magecraft", "casualty"],
    "Graveyard / Recursion": ["graveyard", "recursion", "reanimate", "mill", "escape"],
    "Artifacts": ["artifact", "treasure", "clue", "food", "equipment"],
    "Enchantress": ["enchantment", "enchantress", "aura", "constellation"],
    "Landfall / Lands": ["landfall", "land", "lands matter", "land entering"],
    "Big Mana / Battlecruiser": ["big mana", "battlecruiser", "high mana", "ramp", "big threat"],
    "Typal / Kindred": ["typal", "tribal", "kindred", "dragon", "elf", "goblin", "zombie", "wizard", "sliver"],
}

MODE_SIGNALS = {
    "collection_first": ["collection-first", "collection mode", "prefer collection", "collection source"],
    "full_pool": ["full-card-pool", "full card pool", "full-pool"],
    "combo_aware": ["combo awareness", "commander spellbook", "combo tracker", "relevant potential combo"],
    "budget": ["budget", "price data source", "price"],
    "protected": ["protected", "pet card", "cards i would not cut", "protected from cut"],
    "category_or_exact_boundary": ["category-only", "categories only", "exact full-pool", "exact cards"],
    "manual_review": ["manual review", "held for manual review"],
    "no_auto_swaps": ["automatic swaps: no"],
}

def yes_no(label: str, condition: bool) -> bool:
    print(("PASS" if condition else "FAIL") + f" — {label}")
    return condition

def candidate_reports(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted([p for p in root.rglob("*deck_report*.md") if "debug" not in p.name.lower()], key=lambda p: str(p).lower())

def aggregate_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("batch_deck_reports.md"), key=lambda p: str(p).lower())

def exact_blocks(text: str) -> list[str]:
    blocks = []
    start = 0
    while True:
        idx = text.find("### Exact Full-Pool Candidate Preview", start)
        if idx == -1:
            break
        end = text.find("\n## ", idx + 1)
        blocks.append(text[idx:end if end != -1 else len(text)])
        start = idx + 1
    return blocks

def replacement_need_count(text: str) -> int:
    start = text.find("## Replacement / Addition Needs")
    if start == -1:
        return 0
    end = text.find("\n## ", start + 1)
    section = text[start:end if end != -1 else len(text)]
    count = 0
    for line in section.splitlines():
        if not line.startswith("- "):
            continue
        low = line.lower()
        if low.startswith("- note:") or "no urgent replacement category" in low:
            continue
        count += 1
    return count

def classify_archetypes(text: str, path: Path) -> set[str]:
    low = (text + "\n" + str(path)).lower()
    hits = set()
    for archetype, keywords in ARCHETYPE_KEYWORDS.items():
        if any(keyword in low for keyword in keywords):
            hits.add(archetype)
    return hits

def mode_hits(text: str) -> set[str]:
    low = text.lower()
    hits = set()
    for mode, keywords in MODE_SIGNALS.items():
        if any(keyword in low for keyword in keywords):
            hits.add(mode)
    return hits

def combo_status_text(text: str) -> bool:
    low = text.lower()
    return any(term in low for term in MODE_SIGNALS["combo_aware"])

def verify_scope(label: str, root: Path, require_combo: bool = False) -> dict:
    reports = candidate_reports(root)
    aggregates = aggregate_files(root)

    stats = {
        "reports": len(reports),
        "readable": 0,
        "replacement_preview": 0,
        "fallback_preview": 0,
        "collection_boundary": 0,
        "auto_swaps_no": 0,
        "exact_reports": 0,
        "exact_blocks": 0,
        "need_rich_exact_reports": 0,
        "generic_only_need_rich": 0,
        "exact_color_guard": 0,
        "exact_budget_labels": 0,
        "exact_owned_claims": 0,
        "exact_unsuppressed_combo": 0,
        "raw_summary_trigger": 0,
        "raw_detail_trigger": 0,
        "error_text": 0,
        "combo_reports": 0,
        "combo_with_replacement": 0,
        "combo_with_fallback": 0,
        "aggregate_files": len(aggregates),
        "aggregate_success_lines": 0,
        "aggregate_failure_zero_lines": 0,
        "field_terms": {key: 0 for key in FIELD_SURFACE_TERMS},
    }

    archetype_counts = Counter()
    mode_counts = Counter()
    generic_categories = {
        "#### Better role coverage",
        "#### General role coverage only if the pilot wants outside-card options",
    }

    generic_only_examples = []

    for path in reports:
        text = path.read_text(encoding="utf-8", errors="replace")
        low = text.lower()
        blocks = exact_blocks(text)
        needs = replacement_need_count(text)
        archetypes = classify_archetypes(text, path)
        modes = mode_hits(text)
        has_combo = combo_status_text(text)

        if text.strip():
            stats["readable"] += 1
        if "## Replacement Candidate Engine Preview" in text:
            stats["replacement_preview"] += 1
        if "## Full-Card-Pool Fallback Preview" in text:
            stats["fallback_preview"] += 1
        if "collection-first remains primary" in low:
            stats["collection_boundary"] += 1
        if "Automatic swaps: No" in text:
            stats["auto_swaps_no"] += 1
        if RAW_TRIGGER_TOKENS[0] in text:
            stats["raw_summary_trigger"] += 1
        if RAW_TRIGGER_TOKENS[1] in text:
            stats["raw_detail_trigger"] += 1
        if any(token in text for token in ERROR_TOKENS):
            stats["error_text"] += 1

        if has_combo:
            stats["combo_reports"] += 1
            if "## Replacement Candidate Engine Preview" in text:
                stats["combo_with_replacement"] += 1
            if "## Full-Card-Pool Fallback Preview" in text:
                stats["combo_with_fallback"] += 1

        for key, terms in FIELD_SURFACE_TERMS.items():
            if any(term in low for term in terms):
                stats["field_terms"][key] += 1

        if blocks:
            stats["exact_reports"] += 1
            stats["exact_blocks"] += len(blocks)
        if blocks and needs >= 2:
            stats["need_rich_exact_reports"] += 1

        for arch in archetypes:
            archetype_counts[arch] += 1
        for mode in modes:
            mode_counts[mode] += 1

        for block in blocks:
            block_low = block.lower()
            if "commander color identity check:" in block_low:
                stats["exact_color_guard"] += 1
            if "budget not checked" in block_low or "price data source: none" in block_low:
                stats["exact_budget_labels"] += 1
            if "owned status" in block_low or "source: collection" in block_low:
                stats["exact_owned_claims"] += 1
            if "combo" in block_low:
                allowed = (
                    "no exact combo card examples shown unless combo optimization is explicitly enabled" in block_low
                    or "combo-card examples stay suppressed" in block_low
                )
                if not allowed:
                    stats["exact_unsuppressed_combo"] += 1

            cats = [line for line in block.splitlines() if line.startswith("#### ")]
            if needs >= 2 and cats and all(line in generic_categories for line in cats):
                stats["generic_only_need_rich"] += 1
                generic_only_examples.append(str(path))

    for path in aggregates:
        text = path.read_text(encoding="utf-8", errors="replace")
        if "Successes:" in text:
            stats["aggregate_success_lines"] += 1
        if "Failures: 0" in text:
            stats["aggregate_failure_zero_lines"] += 1

    print("")
    print(label)
    print("-" * len(label))
    print(f"Root: {root}")
    print(f"Reports scanned: {stats['reports']}")
    print(f"Readable reports: {stats['readable']}")
    print(f"Reports with combo-aware/status text: {stats['combo_reports']}")
    print(f"Reports with Replacement Candidate Engine Preview: {stats['replacement_preview']}")
    print(f"Reports with Full-Card-Pool Fallback Preview: {stats['fallback_preview']}")
    print(f"Reports with collection-first boundary: {stats['collection_boundary']}")
    print(f"Reports with Automatic swaps: No: {stats['auto_swaps_no']}")
    print(f"Reports with Exact Full-Pool Candidate Preview: {stats['exact_reports']}")
    print(f"Exact preview blocks found: {stats['exact_blocks']}")
    print(f"Need-rich reports with exact previews: {stats['need_rich_exact_reports']}")
    print(f"Need-rich exact-preview reports still generic-only: {stats['generic_only_need_rich']}")
    print(f"Exact preview blocks with color guard: {stats['exact_color_guard']}")
    print(f"Exact preview blocks with budget/price labels: {stats['exact_budget_labels']}")
    print(f"Exact preview blocks with owned/source claims: {stats['exact_owned_claims']}")
    print(f"Exact preview blocks with unsuppressed combo examples: {stats['exact_unsuppressed_combo']}")
    print(f"Reports with raw ReplacementNeedSummary trigger lines: {stats['raw_summary_trigger']}")
    print(f"Reports with raw ReplacementNeedDetail trigger lines: {stats['raw_detail_trigger']}")
    print(f"Reports with error/crash text: {stats['error_text']}")
    for key, count in stats["field_terms"].items():
        print(f"Reports with {key} field/surface language: {count}")
    print(f"Aggregate batch_deck_reports.md files found: {stats['aggregate_files']}")
    print(f"Aggregate files with Successes line: {stats['aggregate_success_lines']}")
    print(f"Aggregate files with Failures: 0: {stats['aggregate_failure_zero_lines']}")

    print("")
    print("Archetype coverage")
    print("------------------")
    for archetype in ARCHETYPE_KEYWORDS:
        print(f"{archetype}: {archetype_counts[archetype]}")

    print("")
    print("Mode / safety signal coverage")
    print("-----------------------------")
    for mode in MODE_SIGNALS:
        print(f"{mode}: {mode_counts[mode]}")

    failures = 0
    checks = [
        ("reports exist", stats["reports"] > 0),
        ("all reports readable", stats["reports"] > 0 and stats["readable"] == stats["reports"]),
        ("replacement preview appears in all reports", stats["reports"] > 0 and stats["replacement_preview"] == stats["reports"]),
        ("fallback preview appears in all reports", stats["reports"] > 0 and stats["fallback_preview"] == stats["reports"]),
        ("collection-first boundary appears in all reports", stats["reports"] > 0 and stats["collection_boundary"] == stats["reports"]),
        ("Automatic swaps: No appears in all reports", stats["reports"] > 0 and stats["auto_swaps_no"] == stats["reports"]),
        ("need-rich exact previews are not generic-only", stats["generic_only_need_rich"] == 0),
        ("every exact preview block has color guard", stats["exact_blocks"] == stats["exact_color_guard"]),
        ("every exact preview block has budget/price label", stats["exact_blocks"] == stats["exact_budget_labels"]),
        ("exact preview does not claim collection ownership", stats["exact_owned_claims"] == 0),
        ("exact preview does not show unsuppressed combo examples", stats["exact_unsuppressed_combo"] == 0),
        ("no raw ReplacementNeedSummary trigger lines", stats["raw_summary_trigger"] == 0),
        ("no raw ReplacementNeedDetail trigger lines", stats["raw_detail_trigger"] == 0),
        ("no error/crash text", stats["error_text"] == 0),
        ("source surface appears in all reports", stats["field_terms"]["source"] == stats["reports"] if stats["reports"] else False),
        ("ownership surface appears in all reports", stats["field_terms"]["ownership"] == stats["reports"] if stats["reports"] else False),
        ("confidence surface appears in all reports", stats["field_terms"]["confidence"] == stats["reports"] if stats["reports"] else False),
        ("explanation surface appears in all reports", stats["field_terms"]["explanation"] == stats["reports"] if stats["reports"] else False),
        ("caution surface appears in all reports", stats["field_terms"]["caution"] == stats["reports"] if stats["reports"] else False),
        ("filter/manual-review surface appears in all reports", stats["field_terms"]["filter_reason"] == stats["reports"] if stats["reports"] else False),
        ("preference-protection surface appears in all reports", stats["field_terms"]["preference"] == stats["reports"] if stats["reports"] else False),
        ("at least 8 archetype keyword groups represented", sum(1 for a in ARCHETYPE_KEYWORDS if archetype_counts[a] > 0) >= 8),
        ("collection-first mode signal represented", mode_counts["collection_first"] > 0),
        ("full-pool mode signal represented", mode_counts["full_pool"] > 0),
        ("budget signal represented", mode_counts["budget"] > 0),
        ("protected-card signal represented", mode_counts["protected"] > 0),
        ("manual-review signal represented", mode_counts["manual_review"] > 0),
        ("no-auto-swaps signal represented", mode_counts["no_auto_swaps"] > 0),
    ]

    if require_combo:
        checks.extend([
            ("combo-aware/status text appears in all reports", stats["reports"] > 0 and stats["combo_reports"] == stats["reports"]),
            ("combo-aware reports keep replacement preview", stats["combo_reports"] > 0 and stats["combo_with_replacement"] == stats["combo_reports"]),
            ("combo-aware reports keep fallback preview", stats["combo_reports"] > 0 and stats["combo_with_fallback"] == stats["combo_reports"]),
            ("combo-aware mode signal represented", mode_counts["combo_aware"] > 0),
        ])

    if stats["aggregate_files"] > 0:
        checks.extend([
            ("aggregate file has success line", stats["aggregate_success_lines"] == stats["aggregate_files"]),
            ("aggregate file reports zero failures", stats["aggregate_failure_zero_lines"] == stats["aggregate_files"]),
        ])

    for check_label, ok in checks:
        if not yes_no(check_label, ok):
            failures += 1

    if generic_only_examples:
        print("")
        print("Need-rich reports still generic-only examples:")
        for item in generic_only_examples[:10]:
            print(f"  - {item}")

    stats["failures"] = failures
    return stats

def main() -> int:
    normal_root = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    combo_root = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    print("v0.9.8 Stable Candidate Final Regression")
    print("========================================")
    print("Usage:")
    print("  py tools\\verify_v0.9.8_stable_candidate_final_regression.py <normal_outputs_root> <combo_outputs_root>")
    print("Example:")
    print("  py tools\\verify_v0.9.8_stable_candidate_final_regression.py Outputs\\v0.9.5.5.2 Outputs\\v0.9.5.6_combo_on")

    if normal_root is None:
        print("")
        print("FAIL — missing normal outputs root argument.")
        print("")
        print("COPY/PASTE THIS WHOLE OUTPUT INTO CHAT.")
        return 1

    total_failures = 0
    normal_stats = verify_scope("Normal / non-combo stable-candidate scope", normal_root, require_combo=False)
    total_failures += normal_stats["failures"]

    if combo_root is not None:
        combo_stats = verify_scope("Combo-aware stable-candidate scope", combo_root, require_combo=True)
        total_failures += combo_stats["failures"]
    else:
        print("")
        print("WARN — no combo-aware output root supplied; combo-aware final regression skipped.")

    print("")
    print("Final v0.9.8 Stable Candidate Verdict")
    print("-------------------------------------")
    if total_failures == 0:
        print("PASS — v0.9.8 stable-candidate final regression passed.")
    else:
        print(f"FAIL — v0.9.8 stable-candidate final regression found {total_failures} failing check(s).")

    print("")
    print("COPY/PASTE THIS WHOLE OUTPUT INTO CHAT.")
    return 1 if total_failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
