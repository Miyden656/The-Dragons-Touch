"""Dev-mode "Training Review" page — curate training candidates with buttons.

The generator (ai.cli.generate_corpus / generate_teacher) appends UNAPPROVED
candidates to Outputs/commander_ai_training_data.jsonl. This page is the
maintainer's GUI for turning those into approved training data: one candidate at
a time, read it, click Keep / Reject / Skip. It's the in-app equivalent of the
ai.cli.review_corpus terminal tool and writes the same file (with a .bak first).

Dev-mode only — it's a maintainer tool, not part of the community user flow.
Multiple people (e.g. a friend who cloned the repo) can each review on their own
machine, which is how the corpus grows in quality.

build_training_review_page() is bulletproof: any construction error returns a
small label instead of breaking the app. All corpus logic lives in
ai/training/corpus.py (pure + tested); this file is only the screen.
"""

from __future__ import annotations

try:
    from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget
    from ui.widgets import ReportCard
except ImportError:  # running from inside ui/
    from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget
    from widgets import ReportCard


def _load():
    """Load the corpus + the indices of unapproved candidates. Never raises."""
    from ai.training.corpus import default_corpus_path, load_corpus

    path = default_corpus_path()
    loaded = load_corpus(path)
    review_indices = [
        i for i, r in enumerate(loaded.records)
        if isinstance(r, dict) and r.get("approved") is not True
    ]
    return path, loaded, review_indices


def build_training_review_page(window) -> QWidget:
    """Full, scrollable dev-only review page. Returns a fallback on any error."""
    page, layout = window.page_container(
        "Training Review (Dev)",
        "Curate auto-generated training candidates into approved training data. "
        "Read each answer, then Keep, Reject, or Skip. Saves to the same corpus file "
        "the CLI uses (a .bak backup is written first). Generate candidates with the "
        "generate_corpus / generate_teacher tools.",
    )
    scroll, content = window.scroll_content()
    try:
        content.addWidget(_build_review(window))
    except Exception as exc:  # noqa: BLE001 - the page must always render.
        label = QLabel(f"Training Review unavailable: {exc}")
        label.setWordWrap(True)
        content.addWidget(label)
    content.addStretch(1)
    layout.addWidget(scroll, stretch=1)
    return page


def _build_review(window) -> QWidget:
    card = ReportCard("Training Review", window.theme, badges=[("Dev", "manual"), ("Curation", "primary")])
    card.body.addWidget(window.default_note(
        "Review unapproved candidates one at a time. Keep = mark approved (goes into training). "
        "Reject = remove from the corpus. Skip = leave for later. Click Save to write your "
        "decisions (a .bak backup is made first). Reload picks up newly generated candidates."
    ))

    # --- mutable review state (held in a dict so the button closures can mutate it) ---
    path, loaded, review_indices = _load()
    store = {"path": path, "loaded": loaded, "review": review_indices, "pos": 0, "decisions": {}}

    counter = QLabel("")
    counter.setObjectName("helperText")
    card.body.addWidget(counter)

    meta = QLabel("")
    meta.setObjectName("mutedText")
    meta.setWordWrap(True)
    card.body.addWidget(meta)

    question = QLabel("")
    question.setObjectName("sectionTitle")
    question.setWordWrap(True)
    card.body.addWidget(question)

    answer = window.readonly_text_box("The candidate answer will appear here.", min_height=260, max_height=560)
    card.body.addWidget(answer)

    status = QLabel("")
    status.setObjectName("mutedText")
    status.setWordWrap(True)

    def _record_label(rec: dict) -> str:
        return (f"Commander: {rec.get('commander', '?')}    Mode: {rec.get('mode', '?')}    "
                f"Persona: {rec.get('persona', '?')}    Source: {rec.get('source', 'panel')}    "
                f"Decision: {store['decisions'].get(_cur_idx(), '(none)')}")

    def _cur_idx():
        rv = store["review"]
        pos = store["pos"]
        return rv[pos] if 0 <= pos < len(rv) else -1

    def _render():
        rv = store["review"]
        if not rv:
            counter.setText("No candidates to review.")
            meta.setText("Generate some with the generate_corpus or generate_teacher tools, then click Reload.")
            question.setText("")
            answer.setPlainText("Nothing to review right now.")
            return
        store["pos"] = max(0, min(store["pos"], len(rv) - 1))
        idx = _cur_idx()
        rec = store["loaded"].records[idx]
        kept = sum(1 for v in store["decisions"].values() if v == "keep")
        rejected = sum(1 for v in store["decisions"].values() if v == "reject")
        counter.setText(f"Candidate {store['pos'] + 1} of {len(rv)}   "
                        f"(decided: {kept} keep, {rejected} reject)")
        meta.setText(_record_label(rec))
        question.setText("Q:  " + str(rec.get("question", "")))
        answer.setPlainText(str(rec.get("answer", "")))

    def _decide(action: str):
        if not store["review"]:
            return
        store["decisions"][_cur_idx()] = action
        store["pos"] += 1
        if store["pos"] >= len(store["review"]):
            store["pos"] = len(store["review"]) - 1
        _render()

    def _nav(delta: int):
        store["pos"] += delta
        _render()

    def _save():
        from ai.training.corpus import apply_review_decisions, write_corpus

        if not store["decisions"]:
            status.setText("No decisions yet — Keep or Reject some candidates first.")
            return
        try:
            records = store["loaded"].records
            backup = store["path"].with_suffix(store["path"].suffix + ".bak")
            write_corpus(backup, records)
            updated, summary = apply_review_decisions(records, store["decisions"])
            write_corpus(store["path"], updated)
            status.setText(f"Saved: kept {summary['kept']}, rejected {summary['rejected']}. "
                           f"Backup: {backup.name}. Reloading...")
            _reload()
        except Exception as exc:  # noqa: BLE001
            status.setText(f"Could not save: {exc}")

    def _reload():
        p, loaded2, rv2 = _load()
        store.update({"path": p, "loaded": loaded2, "review": rv2, "pos": 0, "decisions": {}})
        _render()

    # --- buttons ---
    nav_row = QHBoxLayout()
    nav_row.setSpacing(8)
    prev_btn = QPushButton("← Prev"); prev_btn.setObjectName("utilityButton")
    next_btn = QPushButton("Next →"); next_btn.setObjectName("utilityButton")
    prev_btn.clicked.connect(lambda: _nav(-1))
    next_btn.clicked.connect(lambda: _nav(1))
    nav_row.addWidget(prev_btn); nav_row.addWidget(next_btn); nav_row.addStretch(1)
    card.body.addLayout(nav_row)

    decide_row = QHBoxLayout()
    decide_row.setSpacing(8)
    keep_btn = QPushButton("✓ Keep"); keep_btn.setObjectName("primaryButton"); keep_btn.setMinimumHeight(38)
    reject_btn = QPushButton("✗ Reject"); reject_btn.setObjectName("utilityButton"); reject_btn.setMinimumHeight(38)
    skip_btn = QPushButton("Skip"); skip_btn.setObjectName("utilityButton"); skip_btn.setMinimumHeight(38)
    keep_btn.clicked.connect(lambda: _decide("keep"))
    reject_btn.clicked.connect(lambda: _decide("reject"))
    skip_btn.clicked.connect(lambda: _nav(1))
    decide_row.addWidget(keep_btn); decide_row.addWidget(reject_btn); decide_row.addWidget(skip_btn)
    decide_row.addStretch(1)
    card.body.addLayout(decide_row)

    action_row = QHBoxLayout()
    action_row.setSpacing(8)
    save_btn = QPushButton("Save decisions"); save_btn.setObjectName("primaryButton"); save_btn.setMinimumHeight(38)
    reload_btn = QPushButton("Reload"); reload_btn.setObjectName("utilityButton"); reload_btn.setMinimumHeight(38)
    save_btn.clicked.connect(_save)
    reload_btn.clicked.connect(_reload)
    save_btn.setToolTip("Apply your Keep/Reject decisions to the corpus file (writes a .bak first).")
    reload_btn.setToolTip("Re-read the corpus file to pick up newly generated candidates.")
    action_row.addWidget(save_btn); action_row.addWidget(reload_btn); action_row.addStretch(1)
    card.body.addLayout(action_row)

    card.body.addWidget(status)

    _render()
    return card
