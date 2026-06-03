"""Persona gendered-voice-variant selection (plumbing, no voice content yet).

Verifies the masc/feminine/general voice-variant SELECTION works before any
variant voices are authored: a guide-presentation choice picks the matching
`### key: <key>:masculine` / `:feminine` asset block, "either"/no-named uses the
general `### key: <key>` block, and a missing variant falls back to the general
voice (so unwritten variants never break rendering).

Run via tests/run_all.py.
"""
from __future__ import annotations

from _test_helpers import TestRun

import ai.commander_ai_personas as personas
from ai.commander_ai_personas import render_persona_block, _voice_variant_suffix


def _persona(presentation: str, key: str = "pet_card") -> dict:
    return {
        "key": key, "label": "Pet Card", "guide_name": "Milo",
        "guide_role": "The Pet Card Mentor", "core_question": "Which cards matter to you?",
        "family_tone": "warm", "family_label": "Timmy / Tammy",
        "guide_presentation": presentation,
    }


def main() -> None:
    t = TestRun("persona_voice_variants")

    # --- suffix mapping ---
    t.eq("masculine -> masculine", _voice_variant_suffix("masculine"), "masculine")
    t.eq("feminine -> feminine", _voice_variant_suffix("feminine"), "feminine")
    t.eq("masc alias -> masculine", _voice_variant_suffix("masc"), "masculine")
    t.eq("either -> general (empty)", _voice_variant_suffix("either"), "")
    t.eq("no_named_guide -> general (empty)", _voice_variant_suffix("no-named-guide"), "")
    t.eq("unknown -> general (empty)", _voice_variant_suffix("whatever"), "")

    # --- selection against a synthetic voice asset (no real content needed) ---
    saved = personas._VOICE_CACHE
    try:
        personas._VOICE_CACHE = {
            "pet_card": {"essence": "GENERALVOICE", "vocabulary": "joy slot",
                         "sounds_like": "g", "avoid": "x"},
            "pet_card:masculine": {"essence": "MILOVOICE", "vocabulary": "joy slot",
                                   "sounds_like": "m", "avoid": "x"},
            "pet_card:feminine": {"essence": "MIAVOICE", "vocabulary": "joy slot",
                                  "sounds_like": "f", "avoid": "x"},
            # spike has NO variant blocks -> must fall back to general
            "spike": {"essence": "SPIKEGENERAL", "vocabulary": "win", "sounds_like": "s", "avoid": "x"},
        }
        masc = render_persona_block(_persona("masculine"))
        fem = render_persona_block(_persona("feminine"))
        gen = render_persona_block(_persona("either"))
        none = render_persona_block(_persona("no_named_guide"))

        t.true("masculine picks the masculine variant", "MILOVOICE" in masc and "GENERALVOICE" not in masc)
        t.true("feminine picks the feminine variant", "MIAVOICE" in fem and "GENERALVOICE" not in fem)
        t.true("either uses the general voice", "GENERALVOICE" in gen)
        t.true("no-named-guide uses the general voice", "GENERALVOICE" in none)

        # missing variant -> fall back to the general block, no crash
        fallback = render_persona_block(_persona("masculine", key="spike"))
        t.true("missing variant falls back to general", "SPIKEGENERAL" in fallback)
    finally:
        personas._VOICE_CACHE = saved

    # --- against the REAL asset: pet_card now HAS Milo/Mia variants ---
    real_m = render_persona_block(_persona("masculine"))
    real_f = render_persona_block(_persona("feminine"))
    real_g = render_persona_block(_persona("either"))
    t.true("real asset: masculine pet_card uses Milo's voice",
           "keep your buddy" in real_m or "no guilt" in real_m)
    t.true("real asset: feminine pet_card uses Mia's voice", "what it means to you" in real_f)
    t.true("real asset: either uses the general voice",
           "protected joy slot" in real_g and "keep your buddy" not in real_g)
    t.true("real asset: masc and fem genuinely differ", real_m != real_f)
    t.true("real asset: still renders a Voice block", "Voice — how this guide speaks:" in real_g)

    # a guide WITHOUT variants (spike is neutral, no pair) still falls back cleanly
    spike_m = render_persona_block({"key": "spike", "label": "Spike", "guide_name": "Spike",
                                    "family_label": "Spike", "guide_presentation": "masculine"})
    t.true("neutral guide with no variant still renders", "Voice — how this guide speaks:" in spike_m)

    t.report_and_exit()


if __name__ == "__main__":
    main()
