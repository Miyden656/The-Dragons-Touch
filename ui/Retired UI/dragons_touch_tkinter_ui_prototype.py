"""
The Dragon's Touch - Standalone Tkinter UI Prototype
Version: UI Prototype v0.1

Purpose:
    A local desktop UI shell for testing workflow, layout, and user experience
    before wiring in The Dragon's Touch deck-building logic.

How to run:
    python dragons_touch_tkinter_ui_prototype.py

Notes:
    - This file intentionally does not depend on the current Dragon's Touch backend.
    - Backend connection points are marked with TODO comments.
    - Built using only Python standard library modules.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


APP_TITLE = "The Dragon's Touch"
APP_VERSION = "UI Prototype v0.1"


@dataclass
class DeckRequest:
    mode: str
    commander: str
    partner_commander: str
    decklist: str
    strategy_notes: str
    power_level: str
    budget: str
    output_style: str
    exact_cards_allowed: bool
    combos_allowed: str


class DragonsTouchApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title(f"{APP_TITLE} - {APP_VERSION}")
        self.geometry("1200x780")
        self.minsize(1050, 680)

        self.current_file: Optional[Path] = None

        self._configure_style()
        self._build_variables()
        self._build_layout()
        self._set_status("Ready. Load a decklist or start entering deck details.")

    # ---------------------------------------------------------------------
    # Setup
    # ---------------------------------------------------------------------

    def _configure_style(self) -> None:
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.colors = {
            "bg": "#1f1b24",
            "panel": "#2b2235",
            "panel_alt": "#342941",
            "text": "#f4edf7",
            "muted": "#cbbfd6",
            "accent": "#b36bff",
            "accent_dark": "#7c3bd1",
            "danger": "#d45555",
        }

        self.configure(bg=self.colors["bg"])

        self.style.configure(
            ".",
            background=self.colors["bg"],
            foreground=self.colors["text"],
            fieldbackground=self.colors["panel"],
            font=("Segoe UI", 10),
        )
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("Panel.TFrame", background=self.colors["panel"])
        self.style.configure("AltPanel.TFrame", background=self.colors["panel_alt"])
        self.style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"])
        self.style.configure("Panel.TLabel", background=self.colors["panel"], foreground=self.colors["text"])
        self.style.configure("Muted.Panel.TLabel", background=self.colors["panel"], foreground=self.colors["muted"])
        self.style.configure("Header.TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 20, "bold"))
        self.style.configure("Subheader.TLabel", background=self.colors["bg"], foreground=self.colors["muted"], font=("Segoe UI", 10))
        self.style.configure("Section.TLabel", background=self.colors["panel"], foreground=self.colors["text"], font=("Segoe UI", 12, "bold"))

        self.style.configure(
            "Accent.TButton",
            background=self.colors["accent_dark"],
            foreground="white",
            padding=(12, 8),
            font=("Segoe UI", 10, "bold"),
        )
        self.style.map(
            "Accent.TButton",
            background=[("active", self.colors["accent"]), ("pressed", self.colors["accent_dark"])],
        )
        self.style.configure("TButton", padding=(10, 6))
        self.style.configure("TNotebook", background=self.colors["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", padding=(14, 8), font=("Segoe UI", 10, "bold"))
        self.style.configure("TCombobox", padding=5)

    def _build_variables(self) -> None:
        self.mode_var = tk.StringVar(value="Build-Up Mode")
        self.commander_var = tk.StringVar()
        self.partner_var = tk.StringVar()
        self.power_var = tk.StringVar(value="Casual")
        self.budget_var = tk.StringVar(value="No budget set")
        self.output_style_var = tk.StringVar(value="Full diagnostic report")
        self.exact_cards_var = tk.BooleanVar(value=True)
        self.combos_var = tk.StringVar(value="Welcome if they fit the deck")
        self.partner_enabled_var = tk.BooleanVar(value=False)

    def _build_layout(self) -> None:
        self._build_menu()
        self._build_header()
        self._build_main_area()
        self._build_status_bar()

    # ---------------------------------------------------------------------
    # UI construction
    # ---------------------------------------------------------------------

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="New Session", command=self.new_session)
        file_menu.add_command(label="Open Decklist...", command=self.open_decklist)
        file_menu.add_command(label="Save Report Draft...", command=self.save_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)

        tools_menu = tk.Menu(menubar, tearoff=False)
        tools_menu.add_command(label="Validate Inputs", command=self.validate_inputs)
        tools_menu.add_command(label="Generate Preview Report", command=self.generate_preview_report)
        tools_menu.add_command(label="Clear Report Output", command=self.clear_report)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About", command=self.show_about)

        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _build_header(self) -> None:
        header = ttk.Frame(self, padding=(18, 16, 18, 10))
        header.pack(fill="x")

        title = ttk.Label(header, text=APP_TITLE, style="Header.TLabel")
        title.pack(anchor="w")

        subtitle = ttk.Label(
            header,
            text="Standalone desktop UI prototype for Commander deck building, cut review, and report generation.",
            style="Subheader.TLabel",
        )
        subtitle.pack(anchor="w", pady=(2, 0))

    def _build_main_area(self) -> None:
        main = ttk.Frame(self, padding=(18, 0, 18, 10))
        main.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill="both", expand=True)

        self.workflow_tab = ttk.Frame(self.notebook)
        self.deck_tab = ttk.Frame(self.notebook)
        self.preferences_tab = ttk.Frame(self.notebook)
        self.report_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.workflow_tab, text="1. Workflow")
        self.notebook.add(self.deck_tab, text="2. Deck Input")
        self.notebook.add(self.preferences_tab, text="3. Preferences")
        self.notebook.add(self.report_tab, text="4. Report Output")

        self._build_workflow_tab()
        self._build_deck_tab()
        self._build_preferences_tab()
        self._build_report_tab()

    def _build_workflow_tab(self) -> None:
        container = ttk.Frame(self.workflow_tab, padding=16)
        container.pack(fill="both", expand=True)

        left = ttk.Frame(container, style="Panel.TFrame", padding=16)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        right = ttk.Frame(container, style="Panel.TFrame", padding=16)
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        ttk.Label(left, text="Deck Mode", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            left,
            text="Choose whether the tool is helping build a deck from scratch or clean up an existing list.",
            style="Muted.Panel.TLabel",
            wraplength=480,
        ).pack(anchor="w", pady=(2, 12))

        modes = [
            "Build-Up Mode",
            "Cut-Down / Cleanup Mode",
            "Completion Mode",
            "Diagnostic Review Mode",
        ]
        for mode in modes:
            rb = ttk.Radiobutton(left, text=mode, value=mode, variable=self.mode_var)
            rb.pack(anchor="w", pady=3)

        ttk.Separator(left).pack(fill="x", pady=16)

        ttk.Checkbutton(
            left,
            text="This deck uses partner / background / paired command zone cards",
            variable=self.partner_enabled_var,
            command=self._toggle_partner_field,
        ).pack(anchor="w")

        command_grid = ttk.Frame(left, style="Panel.TFrame")
        command_grid.pack(fill="x", pady=(12, 0))

        ttk.Label(command_grid, text="Primary Commander", style="Panel.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        commander_entry = ttk.Entry(command_grid, textvariable=self.commander_var)
        commander_entry.grid(row=0, column=1, sticky="ew", pady=4, padx=(10, 0))

        ttk.Label(command_grid, text="Partner / Second Commander", style="Panel.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        self.partner_entry = ttk.Entry(command_grid, textvariable=self.partner_var, state="disabled")
        self.partner_entry.grid(row=1, column=1, sticky="ew", pady=4, padx=(10, 0))

        command_grid.columnconfigure(1, weight=1)

        ttk.Label(right, text="Prototype Workflow", style="Section.TLabel").pack(anchor="w")
        workflow_text = (
            "1. Select the deck workflow mode.\n"
            "2. Enter commander information.\n"
            "3. Paste or load a decklist.\n"
            "4. Add strategy notes and player preferences.\n"
            "5. Generate a preview report.\n\n"
            "Later, the Generate button will call the Dragon's Touch backend instead of creating a placeholder report."
        )
        ttk.Label(right, text=workflow_text, style="Muted.Panel.TLabel", justify="left", wraplength=500).pack(anchor="nw", pady=(8, 16))

        button_row = ttk.Frame(right, style="Panel.TFrame")
        button_row.pack(anchor="w", pady=(4, 0))

        ttk.Button(button_row, text="Validate Inputs", command=self.validate_inputs).pack(side="left", padx=(0, 8))
        ttk.Button(button_row, text="Generate Preview", style="Accent.TButton", command=self.generate_preview_report).pack(side="left")

    def _build_deck_tab(self) -> None:
        container = ttk.Frame(self.deck_tab, padding=16)
        container.pack(fill="both", expand=True)

        top = ttk.Frame(container, style="Panel.TFrame", padding=12)
        top.pack(fill="x", pady=(0, 12))

        ttk.Label(top, text="Decklist", style="Section.TLabel").pack(side="left")
        ttk.Button(top, text="Load .txt / .dec", command=self.open_decklist).pack(side="right")

        body = ttk.Frame(container)
        body.pack(fill="both", expand=True)

        self.deck_text = tk.Text(
            body,
            wrap="none",
            undo=True,
            bg=self.colors["panel"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            padx=12,
            pady=12,
            font=("Consolas", 10),
        )
        self.deck_text.pack(side="left", fill="both", expand=True)

        y_scroll = ttk.Scrollbar(body, orient="vertical", command=self.deck_text.yview)
        y_scroll.pack(side="right", fill="y")
        self.deck_text.configure(yscrollcommand=y_scroll.set)

        x_scroll = ttk.Scrollbar(container, orient="horizontal", command=self.deck_text.xview)
        x_scroll.pack(fill="x")
        self.deck_text.configure(xscrollcommand=x_scroll.set)

        self.deck_text.insert(
            "1.0",
            "# Paste decklist here. Example:\n"
            "# 1 Sol Ring\n"
            "# 1 Arcane Signet\n"
            "# 1 Command Tower\n",
        )

    def _build_preferences_tab(self) -> None:
        container = ttk.Frame(self.preferences_tab, padding=16)
        container.pack(fill="both", expand=True)

        left = ttk.Frame(container, style="Panel.TFrame", padding=16)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        right = ttk.Frame(container, style="Panel.TFrame", padding=16)
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        ttk.Label(left, text="Strategy Notes", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            left,
            text="Describe what the deck is trying to do. This is where the pilot's intent goes.",
            style="Muted.Panel.TLabel",
            wraplength=500,
        ).pack(anchor="w", pady=(2, 8))

        self.strategy_text = tk.Text(
            left,
            height=14,
            wrap="word",
            undo=True,
            bg=self.colors["panel_alt"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            padx=10,
            pady=10,
            font=("Segoe UI", 10),
        )
        self.strategy_text.pack(fill="both", expand=True)
        self.strategy_text.insert(
            "1.0",
            "Example: This deck wants to create artifact tokens, sacrifice them for value, and win through artifact leave triggers / aristocrat-style damage.",
        )

        ttk.Label(right, text="Report Preferences", style="Section.TLabel").pack(anchor="w")

        form = ttk.Frame(right, style="Panel.TFrame")
        form.pack(fill="x", pady=(12, 0))

        self._labeled_combo(form, "Power Level", self.power_var, [
            "Precon / Beginner",
            "Casual",
            "Upgraded Casual",
            "High-Power Casual",
            "Fringe Competitive",
        ], 0)

        self._labeled_combo(form, "Budget", self.budget_var, [
            "No budget set",
            "$50 total",
            "$100 total",
            "$200 total",
            "$400 total",
            "Individual cards under $25",
            "Custom / explain in notes",
        ], 1)

        self._labeled_combo(form, "Output Style", self.output_style_var, [
            "Full diagnostic report",
            "Recommended cuts only",
            "Upgrade path only",
            "Quick summary",
            "Testing checklist",
        ], 2)

        self._labeled_combo(form, "Combos", self.combos_var, [
            "Avoid combos",
            "Welcome if they fit the deck",
            "Only 3+ card combos",
            "Only 4+ card combos",
            "Combo-friendly",
        ], 3)

        ttk.Checkbutton(
            form,
            text="Exact replacement cards are allowed",
            variable=self.exact_cards_var,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 4))

        form.columnconfigure(1, weight=1)

    def _build_report_tab(self) -> None:
        container = ttk.Frame(self.report_tab, padding=16)
        container.pack(fill="both", expand=True)

        toolbar = ttk.Frame(container, style="Panel.TFrame", padding=12)
        toolbar.pack(fill="x", pady=(0, 12))

        ttk.Label(toolbar, text="Report Output", style="Section.TLabel").pack(side="left")
        ttk.Button(toolbar, text="Clear", command=self.clear_report).pack(side="right", padx=(8, 0))
        ttk.Button(toolbar, text="Save Report", command=self.save_report).pack(side="right")

        body = ttk.Frame(container)
        body.pack(fill="both", expand=True)

        self.report_text = tk.Text(
            body,
            wrap="word",
            undo=True,
            bg=self.colors["panel"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            padx=12,
            pady=12,
            font=("Consolas", 10),
        )
        self.report_text.pack(side="left", fill="both", expand=True)

        y_scroll = ttk.Scrollbar(body, orient="vertical", command=self.report_text.yview)
        y_scroll.pack(side="right", fill="y")
        self.report_text.configure(yscrollcommand=y_scroll.set)

        self.report_text.insert(
            "1.0",
            "Report output will appear here.\n\n"
            "Use Tools > Generate Preview Report to test the UI flow before wiring in the real Dragon's Touch logic.",
        )

    def _build_status_bar(self) -> None:
        self.status_var = tk.StringVar()
        status = ttk.Label(self, textvariable=self.status_var, anchor="w", padding=(12, 6), style="Subheader.TLabel")
        status.pack(fill="x", side="bottom")

    def _labeled_combo(self, parent: ttk.Frame, label: str, variable: tk.StringVar, values: list[str], row: int) -> None:
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=6, padx=(0, 12))
        combo = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly")
        combo.grid(row=row, column=1, sticky="ew", pady=6)

    # ---------------------------------------------------------------------
    # Actions
    # ---------------------------------------------------------------------

    def _toggle_partner_field(self) -> None:
        if self.partner_enabled_var.get():
            self.partner_entry.configure(state="normal")
        else:
            self.partner_var.set("")
            self.partner_entry.configure(state="disabled")

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)

    def new_session(self) -> None:
        if not messagebox.askyesno("New Session", "Clear the current UI fields and start a new session?"):
            return

        self.current_file = None
        self.mode_var.set("Build-Up Mode")
        self.commander_var.set("")
        self.partner_var.set("")
        self.partner_enabled_var.set(False)
        self._toggle_partner_field()
        self.power_var.set("Casual")
        self.budget_var.set("No budget set")
        self.output_style_var.set("Full diagnostic report")
        self.exact_cards_var.set(True)
        self.combos_var.set("Welcome if they fit the deck")
        self.deck_text.delete("1.0", "end")
        self.strategy_text.delete("1.0", "end")
        self.report_text.delete("1.0", "end")
        self._set_status("New session started.")

    def open_decklist(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Open Decklist",
            filetypes=[
                ("Deck/Text files", "*.txt *.dec *.dek *.csv"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        path = Path(file_path)
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="latin-1")
        except OSError as exc:
            messagebox.showerror("Open Failed", f"Could not open file:\n{exc}")
            return

        self.current_file = path
        self.deck_text.delete("1.0", "end")
        self.deck_text.insert("1.0", content)
        self._set_status(f"Loaded decklist: {path.name}")
        self.notebook.select(self.deck_tab)

    def save_report(self) -> None:
        content = self.report_text.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("Nothing to Save", "There is no report content to save yet.")
            return

        default_name = "dragons_touch_report.md"
        file_path = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".md",
            initialfile=default_name,
            filetypes=[
                ("Markdown files", "*.md"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        try:
            Path(file_path).write_text(content, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Save Failed", f"Could not save report:\n{exc}")
            return

        self._set_status(f"Saved report: {Path(file_path).name}")

    def validate_inputs(self) -> bool:
        request = self._collect_request()
        issues: list[str] = []

        if not request.commander.strip():
            issues.append("Primary commander is missing.")

        if self.partner_enabled_var.get() and not request.partner_commander.strip():
            issues.append("Partner / second commander is enabled but empty.")

        clean_decklist = self._clean_text(request.decklist)
        if not clean_decklist:
            issues.append("Decklist is empty.")

        if not self._clean_text(request.strategy_notes):
            issues.append("Strategy notes are empty. The real tool will need pilot intent to avoid bad recommendations.")

        if issues:
            messagebox.showwarning("Validation Issues", "\n".join(f"- {issue}" for issue in issues))
            self._set_status("Validation found issues.")
            return False

        messagebox.showinfo("Validation Passed", "Inputs look ready for a prototype report.")
        self._set_status("Validation passed.")
        return True

    def generate_preview_report(self) -> None:
        request = self._collect_request()

        if not request.commander.strip():
            proceed = messagebox.askyesno(
                "Missing Commander",
                "No primary commander is entered. Generate the preview anyway?",
            )
            if not proceed:
                return

        deck_count = self._estimate_deck_count(request.decklist)
        partner_line = f"Partner / Second Commander: {request.partner_commander}\n" if request.partner_commander.strip() else ""

        report = f"""# The Dragon's Touch - Prototype Report

## Session Summary

Mode: {request.mode}
Primary Commander: {request.commander or "Not provided"}
{partner_line}Estimated deck entries: {deck_count}
Power Level: {request.power_level}
Budget: {request.budget}
Output Style: {request.output_style}
Exact Replacement Cards Allowed: {"Yes" if request.exact_cards_allowed else "No"}
Combos: {request.combos_allowed}

## Pilot Strategy Notes

{self._clean_text(request.strategy_notes) or "No strategy notes provided."}

## Prototype Strategy Read

This is placeholder text for UI testing. Later, this section should be generated by the Dragon's Touch strategy engine.

Expected backend responsibilities:
- identify primary and secondary strategy
- identify commander support level
- detect core synergy packages
- detect off-plan cards
- protect context-dependent synergy pieces
- separate mandatory cuts from optional optimization cuts
- recommend replacement categories or exact cards when allowed

## Prototype Cut / Build Guidance

No real card analysis has been performed yet.

When the backend is connected, this section should display:
- required cuts, if deck size is over 100
- optional optimization cuts, even when the deck is legal
- cards protected from cut
- manual review cards
- replacement categories
- exact upgrades, if allowed by settings

## Raw Deck Input Preview

```text
{self._clean_text(request.decklist)[:5000] or "No decklist provided."}
```
"""

        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", report)
        self.notebook.select(self.report_tab)
        self._set_status("Generated prototype report. Backend is not connected yet.")

    def clear_report(self) -> None:
        self.report_text.delete("1.0", "end")
        self._set_status("Report output cleared.")

    def show_about(self) -> None:
        messagebox.showinfo(
            "About The Dragon's Touch",
            f"{APP_TITLE}\n{APP_VERSION}\n\n"
            "Standalone Tkinter UI prototype for local Commander deck-building workflows.\n\n"
            "This prototype is designed to test the desktop layout before connecting the Dragon's Touch backend.",
        )

    # ---------------------------------------------------------------------
    # Data helpers
    # ---------------------------------------------------------------------

    def _collect_request(self) -> DeckRequest:
        return DeckRequest(
            mode=self.mode_var.get(),
            commander=self.commander_var.get().strip(),
            partner_commander=self.partner_var.get().strip(),
            decklist=self.deck_text.get("1.0", "end"),
            strategy_notes=self.strategy_text.get("1.0", "end"),
            power_level=self.power_var.get(),
            budget=self.budget_var.get(),
            output_style=self.output_style_var.get(),
            exact_cards_allowed=self.exact_cards_var.get(),
            combos_allowed=self.combos_var.get(),
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        return text.strip().replace("\r\n", "\n")

    @staticmethod
    def _estimate_deck_count(decklist: str) -> int:
        count = 0
        for raw_line in decklist.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue
            count += 1
        return count


# -------------------------------------------------------------------------
# Backend integration placeholder
# -------------------------------------------------------------------------


def run_dragons_touch_backend(request: DeckRequest) -> str:
    """
    Future backend hook.

    This function is where the UI should eventually call the real Dragon's Touch
    workflow. For now, it is intentionally unused.

    Possible future flow:
        1. Convert DeckRequest into the backend's expected input structure.
        2. Call deck_helper.py or the new Dragon's Touch engine module.
        3. Capture the generated markdown report.
        4. Return the report string to the UI.
    """
    raise NotImplementedError("Dragon's Touch backend is not connected in this UI prototype.")


if __name__ == "__main__":
    app = DragonsTouchApp()
    app.mainloop()
