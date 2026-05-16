"""
The Dragon's Touch - UI constants for v0.7 alpha hardening.

This module intentionally stores stable labels, dropdown choices, and default staged
values only. It must not run backend logic, touch main.py, inspect decks, create
outputs, or replace the guarded CLI bridge.
"""

APP_VERSION = "v0.8.8.6-dev"
APP_PHASE = "Modular Alpha / Settings and Collection Source Navigation Review"
BACKEND_STATUS = "Stable v0.6.8.5 workflow preserved — guarded UI bridge uses CLI/main.py as source of truth"
LOCKED_BACKEND_VERSION = "v0.6.8.5"

OUTPUT_MODE_OPTIONS = ["Normal User Mode", "Debug / Stress-Test Mode", "Both"]
REVIEW_DIRECTION_OPTIONS = ["Build up", "Cut down", "Auto batch"]
REVIEW_INTENSITY_OPTIONS = ["Light", "Normal", "Strict", "Brutal / Deep Review", "Rebuild"]
BUILD_UP_MODE_OPTIONS = [
    "Build from Scratch — Commander(s) only",
    "Point me in the right direction — 30+ cards needed",
    "Help me get there — 11 to 30 cards needed",
    "Finalize — 10 or fewer cards needed",
]
PROMPT_MODE_OPTIONS = ["Interactive AI chat", "One-shot worksheet"]
INTENDED_BRACKET_OPTIONS = ["Not sure yet", "Bracket 1", "Bracket 2", "Bracket 3", "Bracket 4", "Bracket 5"]
GUIDE_PRESENTATION_OPTIONS = ["Masculine guide", "Feminine guide", "Either / random", "No named guide, just philosophy labels"]
PHILOSOPHY_SUBTYPE_OPTIONS = [
    "None / top-level only",
    "Michael / Michelle — Big Moment",
    "Alexander / Alexandria — Big Creature / Stompy",
    "Benjamin / Bethany — Theme / Vibe",
    "Milo / Mia — Pet Card",
    "William / Willow — Let Me Do My Thing",
    "Aaron / Ariana — Battlecruiser",
    "Brad / Bria — Engine Builder",
    "Kyle / Katie — Commander Exploiter",
    "Elund / Emily — Weird Card Rescuer",
    "Brandon / Brenda — Theme Mechanic Inventor",
    "Clark / Clarissa — Self-Imposed Constraint Builder",
    "Jasper / Jennifer — Combo Builder",
    "Avery — Consistency Maximizer",
    "Jordan — Efficiency Optimizer",
    "River — Curve and Mana Discipline",
    "Charlie — Competitive Closer",
    "Kai — Power-Level Calibrator",
    "Riley — Interaction Controller",
]
RUN_DETAIL_OPTIONS = [
    "Runtime Contract",
    "Bridge Preview",
    "Combo Tracker",
    "Guarded Execution",
    "Run Output / Result",
    "Report Output",
    "Safety Boundary",
]
COLLECTION_MODE_OPTIONS = ["No collection", "Prefer collection first", "Collection only", "Collection shakeup"]
COLLECTION_SOURCE_OPTIONS = ["Entire collection folder", "Select collection files"]
COMBO_AWARENESS_OPTIONS = ["Disabled", "Report section only", "Full debug breakdown only", "Both report section and breakdown"]

DEFAULT_SELECTED_PHILOSOPHY = "Balanced / Unknown"
DEFAULT_PHILOSOPHY_SUBTYPE = "None / top-level only"
DEFAULT_GUIDE_PRESENTATION = "Either / random"
DEFAULT_OUTPUT_MODE = "Both"
DEFAULT_REVIEW_DIRECTION = "Cut down"
DEFAULT_REVIEW_INTENSITY = "Normal"
DEFAULT_BUILD_UP_MODE = "Finalize — 10 or fewer cards needed"
DEFAULT_PROMPT_MODE = "Interactive AI chat"
DEFAULT_INTENDED_BRACKET = "Not sure yet"
DEFAULT_COLLECTION_MODE = "No collection"
DEFAULT_COLLECTION_SOURCE_MODE = "Entire collection folder"
DEFAULT_COMBO_AWARENESS_MODE = "Disabled"

# User-facing navigation labels introduced during alpha-feedback cleanup.
BATCH_NAV_LABEL = "Batch Tools"
BATCH_NAV_HELP = "Batch Tools are for later multi-deck or aggregate workflows. Single-deck reviews should use Run Analysis."
ARCHIDEKT_EXPORT_HELP = "Archidekt export tip: export or copy your decklist as plain text, save it as a .txt file, then select it on Deck Selection."

ARCHIDEKT_EXPORT_HELP_TEXT = (
    "Archidekt setup: open your deck on Archidekt, use Export / Download, "
    "copy or save the plain-text decklist, then choose that .txt file here. "
    "The Dragon's Touch works best when the commander is clearly listed and non-deck sections "
    "such as maybeboard, tokens, and considering are kept under their own headings."
)

BATCH_TOOLS_HELP_TEXT = (
    "Batch Tools are future / not active yet. This area is reserved for later multi-deck, "
    "aggregate report, and folder-level workflows. Current alpha testing should use single-deck Run Analysis."
)

# Alpha navigation clarity notes introduced in v0.8.8.6-dev.
COLLECTION_SOURCE_HELP_TEXT = (
    "Collection Source is optional. Use it when you want The Dragon's Touch to prefer, limit, "
    "or compare against cards from your collection. Leave it alone for normal deck reviews."
)
PHILOSOPHY_LENS_HELP_TEXT = (
    "Philosophy Lens is playstyle guidance. It helps shape tone and priorities, but it does not override "
    "commander legality, deck strategy, bracket, budget, or explicit user intent."
)
SETTINGS_HELP_TEXT = (
    "Settings are for app preferences and future utilities. Normal single-deck reviews do not require changing Settings."
)
