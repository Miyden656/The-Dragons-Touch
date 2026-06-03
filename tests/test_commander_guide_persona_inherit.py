"""Tests: the Commander Guide inherits the pre-analysis persona + presentation.

The Guide panel (ui/pages/commander_ai_panel.py) must coach as the SAME philosophy
the user staged on the Philosophy Lens page — a specific subtype winning over the
top-level lens — and in the SAME masculine/feminine/neither voice picked in
Settings, instead of resetting to Balanced / "either". This exercises the pure
resolvers only (no Qt widgets constructed); it SKIPS if PySide6 is unavailable, so
the headless suite still passes on a clone without the GUI dependency.
"""
from __future__ import annotations

import sys
from types import SimpleNamespace as NS

from _test_helpers import TestRun

try:
    import ui.pages.commander_ai_panel as panel
except Exception as exc:  # noqa: BLE001 - PySide6 (or its libs) absent -> skip, don't fail.
    print(f"SKIP: commander_ai_panel not importable ({exc!r}). PySide6 likely absent.")
    sys.exit(0)


def _win(subtype="None / top-level only", lens="Balanced / Unknown", pres="Either / random"):
    return NS(state=NS(philosophy_subtype=subtype, selected_philosophy=lens, guide_presentation=pres))


def main() -> None:
    t = TestRun("commander_guide_persona_inherit")

    # The subtype->key map is built from the canonical ordered key list.
    from analysis.deck_building_philosophies import PHILOSOPHY_PROFILES, SUBTYPE_KEYS
    valid = set(PHILOSOPHY_PROFILES.keys())
    t.eq("subtype map covers all 18 subtypes", len(panel._SUBTYPE_LABEL_TO_KEY), len(SUBTYPE_KEYS))
    t.true("every mapped subtype is a real philosophy key",
           all(k in valid for k in panel._SUBTYPE_LABEL_TO_KEY.values()))

    # A specific subtype wins over the top-level lens sentinel (matches the run).
    t.eq("Pet Card subtype -> pet_card", panel._philosophy_key(
        _win(subtype="Milo / Mia — Pet Card", lens="Specific philosophy subtype")), "pet_card")
    t.eq("Interaction Controller subtype -> interaction_controller", panel._philosophy_key(
        _win(subtype="Riley — Interaction Controller", lens="Specific philosophy subtype")),
        "interaction_controller")

    # Top-level lens labels resolve to their family/profile keys.
    t.eq("Spike lens -> spike", panel._philosophy_key(_win(lens="Spike")), "spike")
    t.eq("Timmy / Tammy lens -> timmy_tammy", panel._philosophy_key(_win(lens="Timmy / Tammy")), "timmy_tammy")
    t.eq("Johnny / Jenny lens -> johnny_jenny", panel._philosophy_key(_win(lens="Johnny / Jenny")), "johnny_jenny")
    t.eq("default lens -> balanced_unknown", panel._philosophy_key(_win()), "balanced_unknown")

    # "None / top-level only" subtype is ignored; the lens is used instead.
    t.eq("None subtype falls through to lens", panel._philosophy_key(
        _win(subtype="None / top-level only", lens="Spike")), "spike")

    # Guide presentation: the staged display label -> engine GuidePreference token.
    t.eq("Masculine guide -> masculine", panel._guide_preference(_win(pres="Masculine guide")), "masculine")
    t.eq("Feminine guide -> feminine", panel._guide_preference(_win(pres="Feminine guide")), "feminine")
    t.eq("Neither -> none", panel._guide_preference(_win(pres="Neither / no named guide")), "none")
    t.eq("Either / random -> either", panel._guide_preference(_win(pres="Either / random")), "either")
    t.eq("empty presentation defaults to either", panel._guide_preference(_win(pres="")), "either")

    # Robustness: missing state / attrs never raise.
    t.eq("no state -> balanced_unknown", panel._philosophy_key(NS()), "balanced_unknown")
    t.eq("no state -> either", panel._guide_preference(NS()), "either")

    t.report_and_exit()


if __name__ == "__main__":
    main()
