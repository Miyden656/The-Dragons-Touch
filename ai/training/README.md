# Commander AI — training track

This folder holds the data-curation + eval tooling for the eventual **custom
fine-tuned Commander model** (the north star). The base-model + grounding +
safety layer that ships today is the foundation; the fine-tune is a capstone on
top of it, not a replacement. Card facts and per-format legality always stay
grounded in Scryfall (so the model is current without retraining); the fine-tune
only bakes in Commander *judgment* and voice.

## The pipeline (each step is headless / `py -3`)

```
Commander Guide panel ──"Save as training example"──▶ Outputs/commander_ai_training_data.jsonl
        (one approved {question, answer, context, ...} per line)
                                   │
   py -3 -m ai.cli.manage_corpus            ── inspect / validate / dedupe / export-clean
                                   │
   py -3 -m ai.cli.prepare_training_data    ── rebuild the EXACT inference prompt
                                   │            triple, emit chat JSONL
                                   ▼
        Outputs/commander_ai_training_dataset.jsonl   ←── feed this to QLoRA
                                   │
                          (rent GPU, train LoRA)
                                   │
   py -3 -m ai.cli.run_eval --models <new-model>,qwen2.5:7b   ── measure the gain
```

## Why the dataset looks the way it does

`prepare_training_data` rebuilds, for each approved answer, the **same prompt the
live layer produces at inference**: a `system` message (identity + hallucination
guardrails + mode + persona + guide style) and a `user` message (verified context
JSON + warnings + uncertainties + mode focus/allow-list + verified card facts +
the question), paired with the approved `assistant` answer. Output is chat-format
JSONL, one object per line:

```json
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

Train on the grounded prompt or the fine-tune won't transfer to the grounded
inference path. Consequence: **examples are long** — the `user` turn carries the
full deck context. MEASURED on the real corpus (`--with-facts`, after the 4-player
pod grounding was added): ~14k tokens median per example, **~17.4k at the max**.
Plan `max_seq_len` ≈ **20480** (NOT 16384 — that would truncate the longest
examples and break grounding fidelity) and size the GPU for it.

`--with-facts` reloads Scryfall and rebuilds the verified-card-facts block per
example (closest to inference; recommended). Without it, that block is omitted.

## Recommended setup (spend the budget here)

- **Base model:** **Qwen3 8B (`qwen3:8b`) is the recommended base** — the newest
  in the Qwen family, still **Apache 2.0** (so the fine-tuned derivative is yours
  to name, run, and redistribute — important for a free community release), and
  best-in-class small-model tool-calling / structured-output reliability, which
  directly helps the cut-review + JSON-emission tasks. It supersedes `qwen2.5:7b`,
  which benchmarked stronger than llama3.1:8b here (legality accuracy +
  hallucination resistance — see `eval.py`) and stays the proven fallback.
  - **Pick the base BEFORE the fine-tune, by measuring — the dataset is
    base-agnostic.** `prepare_training_data` emits grounded prompt→answer pairs
    that don't depend on the base, so you can eval candidate bases for free, pick
    the winner, and fine-tune that one WITHOUT re-buying teacher data. Run e.g.
    `py -3 -m ai.cli.run_eval --models qwen3:8b,qwen2.5:7b --repeat 3` and keep
    whichever beats the 17/21 baseline on YOUR legality / structured / allow-list
    checks.
  - **Other permissive bake-off options:** DeepSeek small (MIT) and Mistral Small
    (Apache 2.0, but larger — heavier to run on an 8 GB card). Gemma 3 is very
    RAM-efficient but **verify its license before redistributing** — it has
    historically shipped under Google's custom *Gemma Terms*, not Apache 2.0.
    Avoid Llama as the base for a *redistributed* model: its community license adds
    naming/usage conditions Apache 2.0 doesn't.
- **Method:** QLoRA (4-bit) LoRA adapters. Tooling options, easiest first:
  **Unsloth** (single-GPU, memory-efficient, qwen2.5 supported) → Axolotl →
  LLaMA-Factory. Follow the chosen tool's chat-format dataset docs; this JSONL
  (a `messages` array per line) is the format they expect.
- **GPU:** the local RTX 5060 (8 GB) is **inference-only** at this seq length —
  it cannot train it. Rent a cloud GPU (A100 40/80 GB or H100). A run is a few
  hours; budget ≈ **$10–30 per run** at typical hourly rates. Expect to iterate
  several runs, so budget for ~3–6 runs total for a first good model.
- **Starting hyperparameters (tune, not gospel):** LoRA r=16–32, alpha=16–32,
  dropout=0.05; lr≈2e-4 cosine; 2–3 epochs; effective batch via gradient
  accumulation; `max_seq_len`≈20480 (measured: longest examples ~17.4k tokens);
  bf16. Watch eval loss for overfit on a small corpus.

## How much data

The corpus has only a handful of examples today. A rough proof-of-concept wants
**~500–1000 vetted examples**; a genuinely good v1 is more, curated over time.
Grow it by using the Guide and clicking **Save as training example** (vary
commander / mode / persona / question), then `manage_corpus --export-clean`.
Quality and diversity beat raw count.

## Measuring success

The eval harness is the yardstick. Today's **baseline to beat (qwen3:8b + layer):
20/22 cases stable over 3 runs, 96% checks** (`run_eval --repeat 3`; bake-off
2026-06-03 — qwen3:8b 20/22 beat qwen2.5:7b 17/22 at equal 96% checks, and
gemma3:4b lost badly at 4/22). After a fine-tune, register the model in Ollama
(build a Modelfile from the merged/adapter weights per Ollama's import docs),
point `commander_ai_model` at it, and run `run_eval --models <new>,qwen3:8b
--repeat 3`. A successful fine-tune should match or beat the baseline **and**
harden qwen3:8b's two remaining misses (combo-hallucination bait,
commander-eligibility) plus any flaky legality/structured cases — while still
relying on the grounding + safety layer underneath.

## Files

- `corpus.py` / `ai.cli.manage_corpus` — load, validate, dedupe, stats, clean-export.
- `prepare_dataset.py` / `ai.cli.prepare_training_data` — corpus → chat JSONL.
- `eval.py` / `ai.cli.run_eval` — objective scoring + `--repeat N` consistency.
