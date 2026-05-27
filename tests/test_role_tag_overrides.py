"""Test card-side role-tag fixes (Bin B Item 6 Phase A, v1.5).

Covers:
- analysis/role_tags.py pattern fixes (shroud -> protection, narrowed board_wipe)
- analysis/role_tag_overrides.py curated EDH staples
- Combined behavior on key cards

Run from project root: py -3 tests/test_role_tag_overrides.py
"""
from _test_helpers import TestRun, load_scryfall_or_skip


def tags_for(scry, name):
    from analysis.role_tags import infer_card_role_tags
    c = scry.get(name.lower())
    if not c:
        return None
    return set(infer_card_role_tags(c))


def main() -> None:
    t = TestRun("test_role_tag_overrides")
    scry = load_scryfall_or_skip()

    # --- Shroud is now a protection keyword (Item 6 Phase A) ---
    greaves = tags_for(scry, "Lightning Greaves")
    t.true("Lightning Greaves found in Scryfall", greaves is not None)
    if greaves is not None:
        t.in_set("Lightning Greaves tagged protection (shroud now detected)",
                 "protection", greaves)
        t.in_set("Lightning Greaves tagged equipment_synergy",
                 "equipment_synergy", greaves)

    swiftfoot = tags_for(scry, "Swiftfoot Boots")
    if swiftfoot is not None:
        t.in_set("Swiftfoot Boots tagged protection",
                 "protection", swiftfoot)

    # --- Narrowed board_wipe pattern: Demonic Consultation no longer false-positive ---
    consultation = tags_for(scry, "Demonic Consultation")
    if consultation is not None:
        t.not_in_set("Demonic Consultation NOT falsely tagged board_wipe (was: 'exile all cards' false match)",
                     "board_wipe", consultation)
        t.in_set("Demonic Consultation tagged combo_piece_possible (via override)",
                 "combo_piece_possible", consultation)

    # --- Narrowed board_wipe: anthems no longer fire ---
    avatar = tags_for(scry, "Avatar of Slaughter")
    if avatar is not None:
        # Avatar of Slaughter is "all creatures have double strike..." — anthem-style
        # The narrowed pattern means it should NOT trigger board_wipe.
        # (Real wipes use "destroy all creatures" etc.)
        t.not_in_set("Avatar of Slaughter NOT tagged board_wipe (anthem, not wipe)",
                     "board_wipe", avatar)

    # --- Real board wipes still get tagged ---
    wrath = tags_for(scry, "Wrath of God")
    if wrath is not None:
        t.in_set("Wrath of God still tagged board_wipe",
                 "board_wipe", wrath)

    # --- Override module: combo pieces ---
    underworld_breach = tags_for(scry, "Underworld Breach")
    if underworld_breach is not None:
        t.in_set("Underworld Breach tagged combo_piece_possible",
                 "combo_piece_possible", underworld_breach)

    phyrexian_altar = tags_for(scry, "Phyrexian Altar")
    if phyrexian_altar is not None:
        t.in_set("Phyrexian Altar tagged combo_piece_possible (via override)",
                 "combo_piece_possible", phyrexian_altar)

    sensei = tags_for(scry, "Sensei's Divining Top")
    if sensei is not None:
        t.in_set("Sensei's Divining Top tagged combo_piece_possible (via override)",
                 "combo_piece_possible", sensei)

    led = tags_for(scry, "Lion's Eye Diamond")
    if led is not None:
        t.in_set("Lion's Eye Diamond still tagged ramp",
                 "ramp", led)
        t.in_set("Lion's Eye Diamond still tagged mana_rock",
                 "mana_rock", led)
        t.in_set("Lion's Eye Diamond tagged combo_piece_possible (via override)",
                 "combo_piece_possible", led)

    # --- Override module summary stats ---
    from analysis.role_tag_overrides import override_summary
    summary = override_summary()
    t.true("Override module reports >= 40 curated cards",
           summary["override_count"] >= 40,
           f"got {summary['override_count']}")
    t.true("Override module reports >= 100 tag additions",
           summary["tag_additions"] >= 100,
           f"got {summary['tag_additions']}")

    t.report_and_exit()


if __name__ == "__main__":
    main()
