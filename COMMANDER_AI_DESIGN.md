# The Dragon's Touch — Commander AI Layer

## Technical Design & Implementation Roadmap (Phase 1 deliverable)

**Status:** Design only. No code written yet. This document is the blueprint.
**Target version:** v1.7.x (additive — does not touch the v1.6 scoring chain).
**Author note:** Every integration point below was read out of the real v1.6 code, not assumed. File paths and function signatures are current as of branch `v1.6.0-community-release`.

---

## 0. The one principle that keeps this safe

> **The LLM is not the deck engine. The Dragon's Touch is the deck engine. The LLM is the guide sitting on top of the engine.**

Concretely, that means the `ai/` package is a **consumer**, never an author, of:

- card facts (oracle text, color identity, mana value, type line) → already owned by `data/card_lookup.py` + `data/scryfall_loader.py`
- legality / banned status → already owned by `legality/commander_legality.py`
- strategy detection → already owned by `analysis/strategy_scoring.py`
- combos → already owned by `combo_awareness/`
- persona priorities → already owned by `analysis/deck_building_philosophies.py`
- the entire assembled analysis → already owned by `main.build_analysis_context()`

The AI layer adds exactly **three** genuinely new things and nothing else:
1. A **local Ollama client** (greenfield — no LLM code exists anywhere today).
2. A **context serializer** that turns the existing analysis objects into a compact, LLM-safe JSON payload.
3. A **prompt + persona + guide-style system** that reuses the existing persona data and adds the net-new *guide style* (tone/format) layer.

If a future change ever makes the LLM compute a card fact itself, that change is wrong by definition.

---

## 1. What already exists (so we don't rebuild it)

This is the single most important section. The spec was written as if this were a blank slate; it is not. Here is the real ground truth.

### 1.1 The analysis spine — already a single dict

`main.py:70 build_analysis_context(parsed_deck, runtime_config, scryfall_lookup, collection_summary) -> dict`

returns (verified, main.py:116–137):

```
version_label, runtime_config, original_runtime_config, parsed_deck,
command_zone, legality, role_summary, strategy_summary, plan_fit_summary,
bracket_summary, protected_cards, replaceability, cut_pressure, possible_cuts,
replacement_needs, deck_completion, replacement_candidates,
collection_candidates, collection_summary, philosophy_context
```

**This dict is the AI context object.** The spec's 30-field context shape is essentially a flattened view of this. We do not build a parallel analysis path — we serialize *this*.

> ⚠️ **Known duplication to resolve at implementation time:** there are two `build_analysis_context` definitions — `main.py:70` and `analysis_pipeline/run_context.py:74`. Before writing the AI layer, confirm which one the UI actually calls and serialize from that one. Do **not** add a third. (Consistent with the project rule: one implementation path per feature.)

### 1.2 Personas — already deep, already 18 of them

`analysis/deck_building_philosophies.py`:

- `build_philosophy_context(key, guide_preference) -> dict` (line 737) returns:
  `key, label, guide_name, guide_role, core_question, rules_summary, protect_bias, review_bias, replacement_bias` (+ summary variants).
- `render_guide_introduction_instruction(context)` (line 888) — already produces the "introduce the guide once, then act as a practical reviewer" instruction.
- `protect_bias` / `review_bias` / `replacement_bias` are **lists of real priorities per persona** — exactly the "personas affect what gets protected / cut / preferred" behavior the spec demands. We feed these straight into the prompt.

The 18 keys: `big_moment, big_creature_stompy, theme_vibe, pet_card, let_me_do_my_thing, battlecruiser` (Timmy/Tammy) · `engine_builder, commander_exploiter, weird_card_rescuer, theme_mechanic_inventor, constraint_builder, combo_builder` (Johnny/Jenny) · `consistency_maximizer, efficiency_optimizer, curve_mana_discipline, competitive_closer, power_level_calibrator, interaction_controller` (Spike).

### 1.3 Persona-aware prompt text — already generated for an *external* AI

`analysis/philosophy_prompting.py` already builds persona-framed prompt blocks (`render_philosophy_prompt_questions`, `render_philosophy_prompt_showcase_block`), and `reports/prompt_builder.py:963 write_user_guided_prompt(...)` already writes the full 7-section handoff prompt that today is meant to be **pasted into ChatGPT/Claude**.

> **The core realization:** This project already does "generate a persona-aware Commander prompt for an external chatbot." The AI layer's job is to **redirect that same prompt to a local Ollama model and feed it structured context**, instead of asking the user to copy-paste. That reframes the whole effort from "build an AI" to "close the loop on a pipe that already exists."

### 1.4 Config / runtime

`config.py RuntimeConfig` (verified fields): `output_mode`, `philosophy_key="balanced_unknown"`, `guide_preference="either"`, `combo_awareness_enabled=False`, plus collection fields. **No `ollama_*` and no `guide_style` exist yet** — both are net-new (see §6, §4.4).

### 1.5 Card facts / legality / combos (source-of-truth modules)

- `data/scryfall_loader.py:load_scryfall_lookup(file) -> (cards, lookup_by_name)`
- `data/card_lookup.py` — face-aware `get_full_oracle_text`, mana-value parsing, type access.
- `legality/commander_legality.py:build_commander_legality_summary(...)`
- `combo_awareness/main_hook.py:write_optional_combo_awareness_artifacts(...)` (+ combo index under `data/`).

### 1.6 UI

PySide6 single-window app. `ui/dragons_touch_pyside6_workstation.py:MainWindow` with a stacked set of pages built by `ui/pages/build_*_page()` functions, barrel-exported from `ui/pages/__init__.py`. New pages register by: add page builder → export in `__init__` → add a `MainWindow` page constant → wire a sidebar entry. **User-mode vs dev-mode** gating already exists (`_commander_call_deferred_features_visible`).

---

## 2. Architecture

```
                         ┌─────────────────────────────────────────────┐
                         │  The Dragon's Touch ENGINE (unchanged)       │
                         │                                              │
  decklist / collection ─▶ build_analysis_context() ──► analysis dict   │
                         │  scryfall_loader / card_lookup               │
                         │  commander_legality / combo_awareness        │
                         │  deck_building_philosophies (18 personas)    │
                         └───────────────────────┬──────────────────────┘
                                                 │ analysis dict (read-only)
                                                 ▼
       ┌───────────────────────────────────────────────────────────────────────┐
       │  ai/  (NEW — the guide layer)                                          │
       │                                                                       │
       │  context/  ── serialize analysis dict → CommanderAIContext (compact)  │
       │  commander_ai_personas.py ── wrap build_philosophy_context + guide    │
       │  commander_ai_prompts.py  ── assemble system + mode + persona + style │
       │  commander_ai_tools.py    ── verified card-fact lookups (read-only)   │
       │  commander_ai_safety.py   ── hallucination guards + claim checking    │
       │  commander_ai_service.py  ── orchestrates one turn end-to-end         │
       │  commander_ai_sessions.py ── conversation history per deck            │
       │  ollama_client.py         ── HTTP to localhost:11434, stream/fallback │
       └───────────────────────────────────────┬───────────────────────────────┘
                                                │ request/response
                                                ▼
       ┌───────────────────────────────────────────────────────────────────────┐
       │  UI (Phase 5+, additive)                                              │
       │  "Ask the Commander Guide" panel in Report Viewer / Commander's Call  │
       └───────────────────────────────────────────────────────────────────────┘
                                                │
                                                ▼
                                  Ollama (local, user-supplied model)
```

**Dependency direction is one-way:** `ai/` imports from the engine; the engine never imports from `ai/`. This guarantees the AI layer can be deleted or disabled with zero impact on deck analysis — and that Ollama being absent never breaks a report.

---

## 3. Proposed file structure

Adjusted from the spec to fit this project's real conventions (split by responsibility, no `_impl.py`, no façades). Everything lives under a new top-level `ai/` package.

```
ai/
  __init__.py
  ollama_client.py            # HTTP client: base_url, model, temperature, stream, timeout, errors
  commander_ai_service.py     # single entry point: answer(request) -> response. Orchestrates everything.
  commander_ai_prompts.py     # loads + assembles prompt fragments from ai/prompts/*.md
  commander_ai_personas.py    # thin adapter over deck_building_philosophies.build_philosophy_context
  commander_ai_guide_styles.py# NET-NEW guide-style (Adventurer/Archivist/Strategist/Minimal) tone+format
  commander_ai_tools.py       # verified lookups the model can request (card fact, legality, combo)
  commander_ai_safety.py      # hallucination guardrails + post-response claim verification
  commander_ai_sessions.py    # per-deck conversation memory (in-memory; optional disk persistence)
  commander_ai_config.py      # reads ollama_* + guide_style from settings; defaults; "is Ollama on?"

ai/context/
  context_serializer.py       # analysis dict -> CommanderAIContext (the master assembler)
  deck_context.py             # parsed_deck + command_zone + role_summary -> compact deck view
  strategy_context.py         # strategy_summary + plan_fit_summary -> strategy view
  cut_context.py              # possible_cuts + protected_cards + replaceability -> cut view
  replacement_context.py      # replacement_needs + replacement_candidates + collection_candidates
  combo_context.py            # combo_awareness output -> combo view
  bracket_context.py          # bracket_summary -> bracket/power view
  collection_context.py       # collection_summary -> ownership view (verified ownership only)

ai/prompts/
  system_prompt.md            # the master system prompt (see §5.1)
  mode_commander_review.md    # mode-specific instruction blocks
  mode_build_from_collection.md
  mode_cut_review.md
  mode_replacement.md
  mode_strategy_tutor.md
  mode_persona_coaching.md
  persona_prompt_blocks.md    # how to render the 18 personas' bias lists into instructions
  guide_style_prompt_blocks.md# the 4 guide styles' tone/format rules
  hallucination_guardrails.md # the do-not-invent ruleset (also enforced in code by safety.py)

ai/schemas/
  ai_request.py               # CommanderAIRequest dataclass
  ai_response.py              # CommanderAIResponse dataclass (human text + structured fields)
  ai_context.py               # CommanderAIContext dataclass (the serialized payload)
  persona_profile.py          # typed view of a persona for the AI layer
  tool_result.py              # typed result of a verified lookup

ai/cli/
  ask_commander_guide.py      # headless test harness: py -3 ai/cli/ask_commander_guide.py <deck>

tests/
  test_ai_context_serializer.py   # analysis dict -> context, no card-fact invention
  test_ai_prompt_assembly.py      # system + mode + persona + style compose correctly
  test_ai_safety_guards.py        # claim-checker flags unverified card/legality/ownership claims
  test_ai_ollama_offline.py       # graceful message when Ollama is down (no exception leaks)
```

Why this shape and not the spec's exact one: the spec's `commander_ai_context.py` is here split into `ai/context/*` because the project already favors one-responsibility-per-file (e.g. `build_from_collection/` has ~40 focused modules). Guide styles get their **own** module because they are net-new and orthogonal to personas. Nothing here imports from a sibling `_impl.py` — there are none.

---

## 4. The context object (mapped to real APIs)

`ai/schemas/ai_context.py` — `CommanderAIContext`. Each field below names the **real source** it is serialized from. Fields are populated only when their source is present; absent data becomes an explicit `null` + an entry in `uncertainties`, never a guess.

| Context field | Serialized from (real source) |
|---|---|
| `user_request` | `CommanderAIRequest.user_text` |
| `selected_commander`, `partner_commander` | `command_zone` (`legality.commander_detection`) |
| `decklist` | `parsed_deck` (name + count + role tags from `role_summary.card_roles`) |
| `commander_legality`, `banned_card_warnings` | `legality` (`build_commander_legality_summary`) |
| `detected_primary_strategy`, `detected_secondary_strategies`, `strategy_confidence` | `strategy_summary` (`build_strategy_summary`) |
| `synergy_packages` | `plan_fit_summary` |
| `combo_summary` | `combo_awareness` output (only if `combo_awareness_enabled`) |
| `bracket_target`, `bracket_concerns` | `bracket_summary` (`build_bracket_analysis`) |
| `mana_curve_summary`, `land_count_summary`, `ramp_summary`, `draw_summary`, `removal_summary`, `protection_summary` | `role_summary.role_counts` + `data/card_lookup` mana values |
| `win_conditions` | `strategy_summary` + `plan_fit_summary` |
| `possible_cuts` | `possible_cuts` (`build_possible_cut_review`) |
| `protected_cards` | `protected_cards` (`build_protected_cards`) |
| `replacement_candidates`, `replacement_needs` | `replacement_candidates` + `replacement_needs` |
| `collection_summary`, `owned_cards_relevant_to_strategy`, `missing_cards` | `collection_summary` + `collection_candidates` |
| `pet_cards` | `CommanderAIRequest.pet_cards` (user-named) — never inferred |
| `persona_profile` | `philosophy_context` (`build_philosophy_context`) |
| `guide_style` | settings (`commander_ai_config`) — NET-NEW |
| `user_constraints` | `CommanderAIRequest.constraints` |
| `scryfall_card_facts` | on-demand via `commander_ai_tools` (verified lookups only) |
| `uncertainties` | filled by `context_serializer` whenever a source is missing/low-confidence |

**Compactness matters.** A 100-card deck × full Scryfall objects would blow any local model's context window. So:
- `decklist` carries `name + count + role tags` only — not full oracle text.
- Full card facts are pulled **on demand** through `commander_ai_tools` when the model (or the mode) actually needs them, and only for the handful of cards under discussion.
- Long lists (e.g. replacement candidates) are truncated with an explicit `"...and N more (ask to see them)"` marker — a **logged** cap, never a silent one.

### 4.4 Guide style (net-new) vs persona (existing)

These are deliberately separate axes:

- **Persona / philosophy** = *what to prioritize* (protect/cut/prefer). Source: existing `build_philosophy_context`. 18 values.
- **Guide style** = *how to say it* (tone + format). Net-new. 4 values:
  - **Adventurer** — warm, encouraging, accessible; minimal jargon.
  - **Archivist** — structured, thorough, record-friendly; headers and lists.
  - **Strategist** — direct, analytical, optimization-focused; assumes fluency.
  - **Minimal** — short, low-fluff, answer-first.

The prompt assembler stacks them: *persona block decides the recommendations, guide-style block decides the wording.* Example the spec calls out — a `theme_vibe`/Bethany persona + Adventurer style → warm flavor-forward advice; a `curve_mana_discipline`/River persona + Strategist style → blunt curve/land/ramp critique.

---

## 5. Prompt system

### 5.1 System prompt (lives at `ai/prompts/system_prompt.md`)

A refined version of the spec's draft, hardened with this project's vocabulary and the source-of-truth hierarchy:

```
You are The Dragon's Touch Commander Guide — a local-first Magic: The Gathering
Commander (EDH) deck-building assistant running on the user's own machine.

You are NOT the source of truth for card facts. The Dragon's Touch engine is.
When card text, color identity, mana value, type line, legality, banned status,
color-identity legality, collection ownership, combo data, strategy detection, or
bracket assessment appears in the provided CONTEXT or comes back from a TOOL, you
must use that and only that. Never override engine data with memory.

SOURCE-OF-TRUTH ORDER:
  1. Tool results (live verified lookups)
  2. The provided CONTEXT object (already engine-verified)
  3. The user's stated intent
  4. Your own MTG knowledge — ONLY for general reasoning, never for specific
     card facts, legality, ownership, or combos.

You must distinguish, and use this exact vocabulary:
  bad card · wrong card for this shell · low-synergy · replaceable · redundant ·
  off-plan · powerful-but-poor-fit · weak-alone-but-strong-in-context ·
  pet card worth protecting · strategy-critical.

Never overstate certainty. For cuts use: "possible cut", "review candidate",
"replaceable slot", "playtest before cutting" — unless the CONTEXT strongly
supports a direct call.

PERSONA: the user has a selected deck-building philosophy. It is not flavor. It
changes what you protect, what you pressure, how hard you optimize, and which
replacement types you favor. Honor its protect/review/replacement bias lists.

GUIDE STYLE: match the requested tone/format (Adventurer / Archivist /
Strategist / Minimal). Style changes wording, never the underlying call.

NEVER invent: oracle text, card names, legality, banned status, combos, or
collection ownership. If you are not certain from CONTEXT or a TOOL, say what
needs checking ("I need the local card database to confirm that") and offer to
look it up.

Your goal is not the strongest possible deck. It is the deck the user actually
wants, at the power level and play experience they intend. Assume the user has
every basic land they need unless the CONTEXT says otherwise.
```

### 5.2 Assembly order (in `commander_ai_prompts.py`)

```
[ system_prompt.md ]
+ [ hallucination_guardrails.md ]
+ [ mode_<active_mode>.md ]                # one of the 6 modes (§7)
+ [ persona block rendered from philosophy_context ]   # protect/review/replacement bias
+ [ guide_style block ]                    # tone + format
+ [ CommanderAIContext as compact JSON ]
+ [ conversation history (from sessions) ]
+ [ user_request ]
```

### 5.3 The six interaction modes (mode files in `ai/prompts/`)

1. **Commander Review** — what the commander wants, primary/secondary strategy, key synergies, traps, belongs/off-plan, likely win-cons. Consumes `strategy_summary`, `plan_fit_summary`, `role_summary`.
2. **Build From Collection** — build-start summary, owned cards by role, rough shell, optional full-100 draft, basics assumed available. Consumes `collection_candidates` + `build_from_collection/public_api`.
3. **Cut Review** — separates Required / Optional-optimization / Possible / Recommended / Protected / Manual-review. Consumes `possible_cuts`, `protected_cards`, `replaceability`. Forbidden from calling a card "bad" unless context supports it.
4. **Replacement** — leads with *categories* (more ramp / draw / removal / wipes / sac outlets / recursion / finishers / protection / lands / lower curve / more commander synergy …); names specific cards only when `replacement_candidates` or a tool verifies them.
5. **Strategy Tutor** — teaches a strategy (aristocrats, tokens, voltron, reanimator, landfall, …) in plain language; eventually backed by the Strategy Deep Dive library in `strategy_knowledge/`.
6. **Persona Coaching** — reflects the user's own build tendencies back ("your cuts read more River than Bethany; tune for attachment or for performance?").

---

## 6. Ollama integration

`ai/ollama_client.py` + `ai/commander_ai_config.py`.

**Settings block** (added to `RuntimeConfig` and the persisted settings the UI reads):

```json
{
  "ollama_enabled": false,
  "ollama_base_url": "http://localhost:11434",
  "ollama_model": "llama3.1",
  "temperature": 0.4,
  "stream": false,
  "request_timeout_seconds": 120,
  "strict_fact_check": true,
  "commander_guide_style": "adventurer"
}
```

Model name is **configurable**, never hardcoded — supports any Ollama model (Llama / Mistral / Qwen / Gemma / other). Default `llama3.1` is a starting suggestion only.

**Client responsibilities:** build the `/api/chat` (or `/api/generate`) request, inject system prompt + assembled context, stream when `stream=true`, fall back to a single non-streaming call otherwise, enforce timeout, and translate every failure into a friendly message — most importantly the offline case:

> "The local Commander AI is enabled, but Ollama doesn't appear to be running. Start Ollama (or run `ollama serve`) and try again, or disable Local Commander AI in Settings."

**Hard rule:** Ollama being down, slow, or returning garbage must never raise into the engine or crash a report. The client returns a typed `CommanderAIResponse` with an `error` field; callers render it as a calm message. This is enforced by `test_ai_ollama_offline.py`.

**Dependency note:** uses the standard library / `requests` only — no `ollama` pip package required, keeping the local-first, low-dependency posture. (Confirm `requests` vs `urllib` at build time against `requirements.txt`.)

---

## 7. Output formats

`ai/schemas/ai_response.py` — `CommanderAIResponse` carries **both**:

- `text` — the human-readable answer for the UI / report viewer.
- structured fields the app can consume:

```
summary: str
primary_recommendation: str
confidence: "low" | "medium" | "high"
persona_notes: str
possible_cuts: [ {card, reason, confidence, cut_type, replacement_category} ]
protected_cards: [ {card, reason} ]
replacement_needs: [ str ]
warnings: [ str ]
follow_up_questions: [ str ]
error: str | null            # set when Ollama failed; text falls back to a friendly note
```

**Structured-output strategy:** ask the model for a fenced JSON block *after* its prose, parse defensively, and on parse failure degrade gracefully to text-only (never crash; log a warning). `strict_fact_check` mode additionally runs `commander_ai_safety.verify_claims()` — any card name, legality claim, or ownership claim in the response that isn't backed by CONTEXT or a tool result gets flagged and softened before display.

---

## 8. Hallucination control (code-enforced, not just prompt-asked)

The prompt rules in §5 are necessary but not sufficient. `commander_ai_safety.py` adds a verification pass:

1. Extract card-name-like tokens from the response.
2. Cross-check each against `parsed_deck`, `collection_summary`, and `scryfall_lookup`.
3. Any "X is in your collection" claim not in `collection_summary` → rewritten to "I can't confirm X is in your collection."
4. Any "X is banned" claim not in `legality` → rewritten to "let me verify X's ban status."
5. Any named combo not in the combo context → softened to "possible interaction; not engine-verified."

This is the safety net that makes a small local model trustworthy enough to ship.

---

## 9. UI integration (later phases — design only here)

Per your working style, UI work is flagged as **requires-your-smoke-test** because I can't drive PySide6 from a session. Planned hooks (additive, user-mode + dev-mode once working):

1. **Report Viewer** (`ui/pages/report_viewer_page.py`) — "Ask the Commander Guide", "Explain this section", "What should I do next?"
2. **Commander's Call** (`ui/pages/commander_discovery_page.py`) — "Guide me through this build", "Explain this commander", "Build according to my persona".
3. **Cut Review** — "Explain these cuts", "Protect my pet cards", "Optimize harder", "Make this more casual".
4. **Settings** (`ui/pages/settings_page.py`) — Enable Local Commander AI · Ollama model · base URL · guide style · persona · temperature · strict fact-check toggle.

First hook (Phase 5) is a single "Ask the Commander Guide" panel in the Report Viewer, since a report's `context` dict is already in hand there — least new wiring, highest payoff.

---

## 10. Implementation roadmap

Phases are sized so each ends at a point you can verify. Phases 2–4 and 6 are **headless** — I can run them myself with `py -3` and the existing `tests/run_all.py` harness, no UI needed. Phases 5 and the Settings UI need your click-through.

| Phase | Deliverable | How it's verified | Needs your testing? |
|---|---|---|---|
| **1. Design** | *This document.* | You read it. | — (done) |
| **2. Ollama client** | `ollama_client.py`, `commander_ai_config.py`, settings block, offline handling | `test_ai_ollama_offline.py`; a live "hello" call if you have Ollama running | No (unless live-testing a model) |
| **3. Context assembly** | `ai/context/*`, `ai/schemas/*` — serialize the real analysis dict | `test_ai_context_serializer.py` against a sample deck; assert no invented facts | No |
| **4. Prompt system** | `ai/prompts/*.md`, `commander_ai_prompts.py`, `commander_ai_personas.py`, `commander_ai_guide_styles.py`, `commander_ai_safety.py` | `test_ai_prompt_assembly.py`, `test_ai_safety_guards.py` | No |
| **4.5 Service + CLI** | `commander_ai_service.py`, `commander_ai_sessions.py`, `ai/cli/ask_commander_guide.py` | Run the CLI end-to-end against a real deck file with a local model | Optional (you, if testing a real model) |
| **5. First UI hook** | "Ask the Commander Guide" panel in Report Viewer | You launch the app and click it | **Yes** |
| **6. Structured output** | JSON response parsing + UI-safe rendering + parse-failure recovery | `test_ai_response_parsing.py` | No (logic) / Yes (display) |
| **7. QA & regression** | Multi-commander, no-Ollama, no-collection, banned-card, pet-card persona, Spike persona, casual vs strict guide, hallucination-resistance suite | Extend `tests/run_all.py`; you run a few real conversations | Partial |

**Guardrail across all phases:** `py -3 tests/run_all.py` (the existing 73-assertion scoring-chain suite) must still pass after every phase. The AI layer is additive and one-directional; if that suite ever changes behavior, something leaked into the engine and is wrong.

---

## 11. What this design explicitly refuses to do

- ❌ No `_impl.py` files, no façade modules, no backwards-compat wrappers (your standing rule).
- ❌ No second analysis path — serialize `build_analysis_context()`, don't re-derive.
- ❌ No LLM-computed card facts, legality, ownership, or combos.
- ❌ No hardcoded model — `ollama_model` is config.
- ❌ No shallow personas — reuses the real `protect/review/replacement` bias lists.
- ❌ No silent truncation — capped lists are logged and disclosed to the user.
- ❌ No engine import of `ai/` — deletion of `ai/` leaves v1.6 untouched.

---

## 12. Open questions to settle before Phase 2

1. **Which `build_analysis_context` is canonical** — `main.py:70` or `analysis_pipeline/run_context.py:74`? (Determines the serializer's input.)
2. **`requests` vs stdlib `urllib`** for the Ollama HTTP call — match whatever `requirements.txt` already allows to keep the dependency footprint flat.
3. **Settings persistence mechanism** — confirm how the UI persists `RuntimeConfig`/`AppState` to disk today so the `ollama_*` + `guide_style` block lands in the same store, not a new one.
4. **Default model** — ship `llama3.1` as the suggested default, or leave blank and force the user to pick in Settings?

These are the only unknowns; none block writing the code, and all are quick to resolve at the top of Phase 2.
```
