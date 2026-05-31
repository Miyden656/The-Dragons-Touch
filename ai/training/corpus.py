"""Training-corpus data layer.

Reads and reasons about the JSONL file the Commander Guide panel writes (one
approved answer per line). Everything here is defensive: a corrupt line is
reported, never fatal, so a half-written file still yields its good records.

Record shape (written by ui/pages/commander_ai_panel.py:_save_training_example):
    {
      "commander":   str,   # commander name the answer was about
      "mode":        str,   # interaction mode (see ALL_MODES)
      "persona":     str,   # philosophy key (see PHILOSOPHY_PROFILES)
      "guide_style": str,   # adventurer | archivist | strategist | minimal
      "question":    str,   # the user's question
      "answer":      str,   # the model's raw answer (training target)
      "context":     str,   # serialized CommanderAIContext JSON (grounding)
      "approved":    bool,  # user marked it good
    }
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# Canonical schema. Required string fields must be present and (for question/
# answer) non-empty for a record to be training-usable.
REQUIRED_STRING_FIELDS = ("commander", "mode", "persona", "guide_style", "question", "answer")
NONEMPTY_FIELDS = ("question", "answer")
ALL_FIELDS = REQUIRED_STRING_FIELDS + ("context", "approved")

DEFAULT_CORPUS_NAME = "commander_ai_training_data.jsonl"


@dataclass
class LoadedCorpus:
    """The result of reading a corpus file."""

    path: Path
    records: list[dict] = field(default_factory=list)        # successfully parsed lines
    parse_errors: list[tuple[int, str]] = field(default_factory=list)  # (line_no, message)
    exists: bool = True

    def __len__(self) -> int:
        return len(self.records)


def _valid_modes() -> set[str]:
    try:
        from ai.schemas.ai_context import ALL_MODES
        return set(ALL_MODES)
    except Exception:  # noqa: BLE001
        return set()


def _valid_styles() -> set[str]:
    try:
        from ai.commander_ai_guide_styles import available_styles
        return set(available_styles())
    except Exception:  # noqa: BLE001
        return set()


def _valid_personas() -> set[str]:
    try:
        from analysis.deck_building_philosophies import PHILOSOPHY_PROFILES
        return set(PHILOSOPHY_PROFILES.keys())
    except Exception:  # noqa: BLE001
        return set()


def load_corpus(path: str | Path) -> LoadedCorpus:
    """Read a JSONL corpus. Bad lines are recorded, not raised."""
    p = Path(path)
    if not p.exists():
        return LoadedCorpus(path=p, exists=False)

    records: list[dict] = []
    errors: list[tuple[int, str]] = []
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        return LoadedCorpus(path=p, parse_errors=[(0, f"could not read file: {exc}")])

    for i, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append((i, f"invalid JSON: {exc.msg}"))
            continue
        if not isinstance(obj, dict):
            errors.append((i, "line is not a JSON object"))
            continue
        records.append(obj)
    return LoadedCorpus(path=p, records=records, parse_errors=errors)


def validate_record(rec: dict) -> list[str]:
    """Return a list of problems with one record; empty list = training-usable.

    Hard problems only (missing/empty required fields, unknown mode/style/persona,
    unparseable context). Validation degrades gracefully if the engine modules
    can't be imported (those specific checks are skipped, not failed)."""
    problems: list[str] = []
    if not isinstance(rec, dict):
        return ["record is not an object"]

    for fldname in REQUIRED_STRING_FIELDS:
        val = rec.get(fldname)
        if not isinstance(val, str):
            problems.append(f"missing or non-string field: {fldname}")
        elif fldname in NONEMPTY_FIELDS and not val.strip():
            problems.append(f"empty field: {fldname}")

    modes = _valid_modes()
    if modes and isinstance(rec.get("mode"), str) and rec["mode"] not in modes:
        problems.append(f"unknown mode: {rec['mode']!r}")

    styles = _valid_styles()
    if styles and isinstance(rec.get("guide_style"), str) and rec["guide_style"] not in styles:
        problems.append(f"unknown guide_style: {rec['guide_style']!r}")

    personas = _valid_personas()
    if personas and isinstance(rec.get("persona"), str) and rec["persona"] not in personas:
        problems.append(f"unknown persona: {rec['persona']!r}")

    ctx = rec.get("context")
    if isinstance(ctx, str) and ctx.strip():
        try:
            json.loads(ctx)
        except json.JSONDecodeError:
            problems.append("context is not valid JSON")

    return problems


def is_usable(rec: dict) -> bool:
    return not validate_record(rec)


def record_key(rec: dict) -> tuple:
    """Identity used for de-duplication: same commander+mode+persona+question+
    answer is the same training example."""
    def norm(v: object) -> str:
        return " ".join(str(v or "").split()).lower()

    return (
        norm(rec.get("commander")),
        norm(rec.get("mode")),
        norm(rec.get("persona")),
        norm(rec.get("question")),
        norm(rec.get("answer")),
    )


def dedupe(records: list[dict]) -> tuple[list[dict], int]:
    """Keep first occurrence of each record_key. Returns (unique, removed_count)."""
    seen: set[tuple] = set()
    unique: list[dict] = []
    removed = 0
    for rec in records:
        key = record_key(rec)
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        unique.append(rec)
    return unique, removed


def _count_by(records: list[dict], field_name: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for rec in records:
        val = str(rec.get(field_name, "") or "(none)")
        out[val] = out.get(val, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def corpus_stats(loaded: LoadedCorpus) -> dict:
    """Summary statistics for a loaded corpus."""
    records = loaded.records
    valid = [r for r in records if is_usable(r)]
    approved = [r for r in records if r.get("approved") is True]
    _unique, dup_removed = dedupe(records)
    return {
        "path": str(loaded.path),
        "exists": loaded.exists,
        "total_records": len(records),
        "parse_errors": len(loaded.parse_errors),
        "valid_records": len(valid),
        "invalid_records": len(records) - len(valid),
        "approved_records": len(approved),
        "duplicate_records": dup_removed,
        "by_mode": _count_by(records, "mode"),
        "by_persona": _count_by(records, "persona"),
        "by_guide_style": _count_by(records, "guide_style"),
        "by_commander": _count_by(records, "commander"),
    }


def clean_corpus(records: list[dict], *, approved_only: bool = True) -> tuple[list[dict], dict]:
    """Produce a training-ready subset: valid, de-duplicated, (optionally) approved.

    Returns (clean_records, report) where report explains what was dropped."""
    started = len(records)
    pool = [r for r in records if (r.get("approved") is True)] if approved_only else list(records)
    after_approved = len(pool)
    valid = [r for r in pool if is_usable(r)]
    after_valid = len(valid)
    unique, dup_removed = dedupe(valid)
    report = {
        "started": started,
        "dropped_unapproved": started - after_approved if approved_only else 0,
        "dropped_invalid": after_approved - after_valid,
        "dropped_duplicate": dup_removed,
        "kept": len(unique),
    }
    return unique, report


def write_corpus(path: str | Path, records: list[dict]) -> Path:
    """Write records as JSONL (UTF-8). Returns the path written."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return p


def default_corpus_path() -> Path:
    """Resolve the corpus path from the app's output folder, else Outputs/."""
    out_dir = "Outputs"
    try:
        from ui.services.user_settings import load_app_settings

        out_dir = str(load_app_settings().get("report_output_folder", "Outputs") or "Outputs")
    except Exception:  # noqa: BLE001
        pass
    return Path(out_dir) / DEFAULT_CORPUS_NAME
