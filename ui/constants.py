APP_PHASE = 'Modular Alpha / User-Dev Mode Import Cleanup Hotfix'
APP_VERSION = 'v0.8.10.1-alpha'
"""
The Dragon's Touch - UI constants for v0.7 alpha hardening.

This module intentionally stores stable labels, dropdown choices, and default staged
values only. It must not run backend logic, touch main.py, inspect decks, create
outputs, or replace the guarded CLI bridge.
"""

APP_VERSION = 'v0.8.10.1-alpha'
APP_PHASE = 'Modular Alpha / User-Dev Mode Import Cleanup Hotfix'
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
GUIDE_PRESENTATION_OPTIONS = ["Masculine guide", "Feminine guide", "Either / random", "Neither / no named guide"]
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
COLLECTION_MODE_OPTIONS = [
    "Collection first, then full card pool",
    "Collection only",
    "Full card pool only",
    "No replacement suggestions",
]
COLLECTION_SOURCE_OPTIONS = ["Entire collection folder", "Select collection files"]
COMBO_AWARENESS_OPTIONS = ["Always included"]
INTERFACE_MODE_OPTIONS = ["User Mode", "Developer Mode"]

DEFAULT_SELECTED_PHILOSOPHY = "Balanced / Unknown"
DEFAULT_PHILOSOPHY_SUBTYPE = "None / top-level only"
DEFAULT_GUIDE_PRESENTATION = "Either / random"
DEFAULT_OUTPUT_MODE = "Both"
DEFAULT_REVIEW_DIRECTION = "Cut down"
DEFAULT_REVIEW_INTENSITY = "Normal"
DEFAULT_BUILD_UP_MODE = "Finalize — 10 or fewer cards needed"
DEFAULT_PROMPT_MODE = "Interactive AI chat"
DEFAULT_INTENDED_BRACKET = "Not sure yet"
DEFAULT_COLLECTION_MODE = "Collection first, then full card pool"
DEFAULT_COLLECTION_SOURCE_MODE = "Entire collection folder"
DEFAULT_COMBO_AWARENESS_MODE = "Always included"
DEFAULT_INTERFACE_MODE = "User Mode"

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
    "Batch Tools are removed from UI navigation for v0.10.5. This area is reserved for later multi-deck, "
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

# User/dev interface mode notes introduced in v0.8.9.6-dev.
INTERFACE_MODE_HELP_TEXT = (
    "User Mode is the clean default for normal deck reviews. Developer Mode is for development, "
    "diagnostics, stress testing, and troubleshooting while The Dragon's Touch is still being built."
)


DEV_MODE_PROTECTION_NOTE = (
    "Developer Mode is currently available for active development and trusted alpha testing. Before beta, public preview, "
    "or v1.0, this mode should be hidden, gated, or otherwise protected so normal users cannot accidentally open "
    "developer-only diagnostics."
)

USER_MODE_RUN_ANALYSIS_NOTE = (
    'User Mode keeps Run Analysis focused on the normal player workflow. Advanced diagnostics stay hidden unless Developer Mode is selected.'
)

DEV_MODE_RUN_ANALYSIS_NOTE = (
    'Developer Mode is for development and testing. It exposes advanced run details, bridge/runtime previews, diagnostics, and breakdown visibility for QA.'
)

USER_MODE_REPORT_VIEWER_NOTE = (
    'User Mode focuses Report Viewer on normal player-facing reports.'
)

DEV_MODE_REPORT_VIEWER_NOTE = (
    'Developer Mode shows breakdown/debug reports for development and QA.'
)

DEV_FACING_PROTECTION_NOTE = (
    'Developer Mode is intended for development/testing and should be hidden, gated, or protected before beta, public preview, or v1.0 release.'
)

USER_FACING_MODE_HELP_TEXT = (
    'User Mode keeps the main workflow focused on Deck Selection, Review Setup, optional Collection Source, Run Analysis, and the normal deck report. Advanced details can still be opened when needed, but they are not the default view.'
)

DEV_FACING_MODE_HELP_TEXT = (
    'Developer Mode is for development/testing. It keeps advanced run details, runtime contracts, bridge previews, diagnostics, breakdown reports, and combo breakdown artifacts visible for QA.'
)

USER_DEV_REGRESSION_NOTE = (
    'User/Dev mode regression note: User Mode remains the default clean workflow; Developer Mode remains available for active development and QA until it is gated before beta/public release.'
)

DEV_MODE_PROTECTION_NOTE = (
    'Developer Mode is currently available for active development and trusted alpha testing. Before beta, public preview, or v1.0, this mode should be hidden, gated, or otherwise protected so normal users cannot accidentally open developer-only diagnostics.'
)

USER_MODE_RUN_ANALYSIS_NOTE = (
    'User Mode keeps Run Analysis focused on the normal player workflow. Advanced diagnostics stay hidden unless Developer Mode is selected.'
)

DEV_MODE_RUN_ANALYSIS_NOTE = (
    'Developer Mode is for development and testing. It exposes advanced run details, bridge/runtime previews, diagnostics, and breakdown visibility for QA.'
)

USER_MODE_REPORT_VIEWER_NOTE = (
    'User Mode focuses Report Viewer on normal player-facing reports.'
)

DEV_MODE_REPORT_VIEWER_NOTE = (
    'Developer Mode shows breakdown/debug reports for development and QA.'
)

DEV_FACING_PROTECTION_NOTE = (
    'Developer Mode is intended for development/testing and should be hidden, gated, or protected before beta, public preview, or v1.0 release.'
)



# v0.10.5.1 persistent app setting options.
APP_COLLECTION_SOURCE_DEFAULT_OPTIONS = [
    "Local collection folder",
    "Specific local collection files",
    "CardMill CSV/export placeholder",
    "Moxfield export placeholder",
    "Future source placeholder",
]

UI_DENSITY_OPTIONS = ["Comfortable", "Normal", "Compact"]
REPORT_VIEWER_DEV_VIEW_OPTIONS = ["User View", "Dev View"]

# v0.10.6.1: combo awareness is no longer optional.
COMBO_AWARENESS_ALWAYS_ON = True
COMBO_AWARENESS_ARTIFACT_MODE = "both"
