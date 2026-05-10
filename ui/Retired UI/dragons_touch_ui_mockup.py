"""
Dragon's Touch UI Mockup
Standalone Tkinter desktop prototype.

This is a visual/workflow test version only:
- No Scryfall connection
- No Commander Spellbook connection
- No real deck analysis
- No real saved deck system

Run:
    python dragons_touch_ui_mockup.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass, field


# -----------------------------
# Theme Definitions
# -----------------------------

DRAGON_FORGE = {
    "name": "Dragon Forge",
    "bg": "#0f0d0b",
    "bg_alt": "#171310",
    "panel": "#1f1a16",
    "panel_alt": "#2a211b",
    "card": "#211811",
    "card_hover": "#332318",
    "accent": "#e86a24",
    "accent_2": "#d8a642",
    "accent_3": "#8f2f22",
    "success": "#78b159",
    "warning": "#c5533d",
    "text": "#f2e6d0",
    "muted": "#b8afa3",
    "border": "#7a4424",
    "button_bg": "#2b1c13",
    "button_fg": "#f2e6d0",
    "input_bg": "#15110e",
    "input_fg": "#f2e6d0",
    "disabled": "#5f554f",
}

ADVENTURERS_MAP = {
    "name": "Adventurer's Map",
    "bg": "#d8c394",
    "bg_alt": "#e8d7b4",
    "panel": "#f4e7c5",
    "panel_alt": "#e2cc9d",
    "card": "#f8edcf",
    "card_hover": "#efe0b9",
    "accent": "#3e6b3a",
    "accent_2": "#b88a2e",
    "accent_3": "#8a5a2d",
    "success": "#3e7a3a",
    "warning": "#a14a32",
    "text": "#3b2a1a",
    "muted": "#6e5b45",
    "border": "#8a6a3d",
    "button_bg": "#ead9ad",
    "button_fg": "#3b2a1a",
    "input_bg": "#fff7df",
    "input_fg": "#3b2a1a",
    "disabled": "#96846a",
}


# -----------------------------
# App State
# -----------------------------

@dataclass
class AppState:
    theme_name: str = "Dragon Forge"
    mode: str = "Home"
    deck_name: str = "Untitled Deck"
    commanders: str = "No commander selected"
    selected_persona: str = "The Sage"
    workflow_step: int = 1
    warnings: int = 0
    last_screen: str = "home"


# -----------------------------
# Main Application
# -----------------------------

class DragonsTouchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dragon's Touch")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        self.state_data = AppState()
        self.theme = DRAGON_FORGE

        self.configure(bg=self.theme["bg"])

        self.style = ttk.Style()
        self._configure_ttk_style()

        self.top_bar = None
        self.status_bar = None
        self.content = None

        self._build_shell()
        self.show_home()

    # -----------------------------
    # Theme / Styling
    # -----------------------------

    def _configure_ttk_style(self):
        self.style.theme_use("clam")
        self.style.configure(
            "TCombobox",
            fieldbackground=self.theme["input_bg"],
            background=self.theme["panel"],
            foreground=self.theme["text"],
            arrowcolor=self.theme["accent"],
        )
        self.style.configure(
            "Horizontal.TProgressbar",
            troughcolor=self.theme["panel_alt"],
            background=self.theme["accent"],
            bordercolor=self.theme["border"],
            lightcolor=self.theme["accent_2"],
            darkcolor=self.theme["accent"],
        )

    def switch_theme(self):
        if self.theme["name"] == "Dragon Forge":
            self.theme = ADVENTURERS_MAP
            self.state_data.theme_name = "Adventurer's Map"
        else:
            self.theme = DRAGON_FORGE
            self.state_data.theme_name = "Dragon Forge"

        self.configure(bg=self.theme["bg"])
        self._configure_ttk_style()

        # Re-render current screen.
        last = self.state_data.last_screen
        if last == "home":
            self.show_home()
        elif last == "workflow":
            self.show_workflow(self.state_data.mode)
        elif last == "persona":
            self.show_persona_selection()
        elif last == "processing":
            self.show_processing()
        elif last == "report":
            self.show_report()
        elif last == "placeholder":
            self.show_placeholder(self.state_data.mode)
        else:
            self.show_home()

    # -----------------------------
    # Shell
    # -----------------------------

    def _build_shell(self):
        self._clear_root()

        self.top_bar = tk.Frame(self, bg=self.theme["bg"], height=86)
        self.top_bar.pack(side="top", fill="x")

        self.content = tk.Frame(self, bg=self.theme["bg"])
        self.content.pack(side="top", fill="both", expand=True)

        self.status_bar = tk.Frame(self, bg=self.theme["bg_alt"], height=30)
        self.status_bar.pack(side="bottom", fill="x")

        self._build_top_bar()
        self._build_status_bar()

    def _clear_root(self):
        for child in self.winfo_children():
            child.destroy()

    def _clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()
        self._build_top_bar()
        self._build_status_bar()

    def _build_top_bar(self):
        for child in self.top_bar.winfo_children():
            child.destroy()

        left = tk.Frame(self.top_bar, bg=self.theme["bg"])
        left.pack(side="left", fill="y", padx=18)

        logo = tk.Label(
            left,
            text="🐉",
            font=("Georgia", 32, "bold"),
            fg=self.theme["accent_2"],
            bg=self.theme["bg"],
        )
        logo.pack(side="left", padx=(0, 10))

        title_block = tk.Frame(left, bg=self.theme["bg"])
        title_block.pack(side="left")

        title = tk.Label(
            title_block,
            text="DRAGON'S TOUCH",
            font=("Georgia", 30, "bold"),
            fg=self.theme["text"],
            bg=self.theme["bg"],
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            title_block,
            text="Forge Insight. Refine Power. Play Your Legend.",
            font=("Georgia", 11, "italic"),
            fg=self.theme["accent_2"],
            bg=self.theme["bg"],
        )
        subtitle.pack(anchor="w")

        right = tk.Frame(self.top_bar, bg=self.theme["bg"])
        right.pack(side="right", fill="y", padx=18)

        mascot = tk.Label(
            right,
            text="☕🐲",
            font=("Georgia", 24),
            fg=self.theme["accent"],
            bg=self.theme["bg"],
        )
        mascot.pack(side="left", padx=8)

        theme_btn = self.make_button(
            right,
            text=f"Theme: {self.theme['name']}",
            command=self.switch_theme,
            compact=True,
        )
        theme_btn.pack(side="left", padx=6)

        persona_btn = self.make_button(
            right,
            text=f"Persona: {self.state_data.selected_persona}",
            command=self.show_persona_selection,
            compact=True,
        )
        persona_btn.pack(side="left", padx=6)

        home_btn = self.make_button(
            right,
            text="Home",
            command=self.show_home,
            compact=True,
        )
        home_btn.pack(side="left", padx=6)

    def _build_status_bar(self):
        for child in self.status_bar.winfo_children():
            child.destroy()

        text = (
            f"Single Desktop Experience  •  Built for Focus  •  "
            f"Python + Tkinter Prototype  •  Current Theme: {self.theme['name']}"
        )
        label = tk.Label(
            self.status_bar,
            text=text,
            font=("Georgia", 9),
            fg=self.theme["muted"],
            bg=self.theme["bg_alt"],
        )
        label.pack(side="left", padx=16)

        version = tk.Label(
            self.status_bar,
            text="UI Mockup v0.1",
            font=("Georgia", 9),
            fg=self.theme["muted"],
            bg=self.theme["bg_alt"],
        )
        version.pack(side="right", padx=16)

    # -----------------------------
    # Reusable Components
    # -----------------------------

    def make_panel(self, parent, bg=None, border=True):
        bg = bg or self.theme["panel"]
        frame = tk.Frame(
            parent,
            bg=bg,
            highlightthickness=1 if border else 0,
            highlightbackground=self.theme["border"],
            highlightcolor=self.theme["accent"],
        )
        return frame

    def make_button(self, parent, text, command=None, compact=False, selected=False):
        bg = self.theme["accent"] if selected else self.theme["button_bg"]
        fg = self.theme["bg"] if selected else self.theme["button_fg"]
        padx = 10 if compact else 16
        pady = 5 if compact else 10
        font_size = 9 if compact else 11

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=self.theme["accent_2"],
            activeforeground=self.theme["bg"],
            relief="flat",
            bd=0,
            padx=padx,
            pady=pady,
            cursor="hand2",
            font=("Georgia", font_size, "bold"),
        )
        return btn

    def make_title(self, parent, text, size=18, accent=False):
        return tk.Label(
            parent,
            text=text,
            font=("Georgia", size, "bold"),
            fg=self.theme["accent_2"] if accent else self.theme["text"],
            bg=parent["bg"],
        )

    def make_body_label(self, parent, text, size=10, muted=False, wrap=600, justify="left"):
        return tk.Label(
            parent,
            text=text,
            font=("Georgia", size),
            fg=self.theme["muted"] if muted else self.theme["text"],
            bg=parent["bg"],
            wraplength=wrap,
            justify=justify,
        )

    def make_entry(self, parent):
        entry = tk.Entry(
            parent,
            bg=self.theme["input_bg"],
            fg=self.theme["input_fg"],
            insertbackground=self.theme["accent"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.theme["border"],
            highlightcolor=self.theme["accent"],
            font=("Georgia", 10),
        )
        return entry

    def make_textbox(self, parent, height=5):
        box = tk.Text(
            parent,
            height=height,
            bg=self.theme["input_bg"],
            fg=self.theme["input_fg"],
            insertbackground=self.theme["accent"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.theme["border"],
            highlightcolor=self.theme["accent"],
            font=("Georgia", 10),
            wrap="word",
        )
        return box

    def make_dashboard_card(self, parent, icon, title, desc, command):
        card = self.make_panel(parent, bg=self.theme["card"])
        card.configure(cursor="hand2")

        icon_lbl = tk.Label(
            card,
            text=icon,
            font=("Georgia", 32),
            fg=self.theme["accent_2"],
            bg=self.theme["card"],
        )
        icon_lbl.pack(pady=(18, 4))

        title_lbl = tk.Label(
            card,
            text=title,
            font=("Georgia", 13, "bold"),
            fg=self.theme["text"],
            bg=self.theme["card"],
        )
        title_lbl.pack()

        desc_lbl = tk.Label(
            card,
            text=desc,
            font=("Georgia", 9),
            fg=self.theme["muted"],
            bg=self.theme["card"],
            wraplength=140,
            justify="center",
        )
        desc_lbl.pack(pady=(5, 16), padx=10)

        def on_enter(_):
            card.configure(bg=self.theme["card_hover"])
            for child in card.winfo_children():
                child.configure(bg=self.theme["card_hover"])

        def on_leave(_):
            card.configure(bg=self.theme["card"])
            for child in card.winfo_children():
                child.configure(bg=self.theme["card"])

        def on_click(_):
            command()

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        card.bind("<Button-1>", on_click)
        for child in card.winfo_children():
            child.bind("<Button-1>", on_click)
            child.configure(cursor="hand2")

        return card

    # -----------------------------
    # Screens
    # -----------------------------

    def show_home(self):
        self.state_data.mode = "Home"
        self.state_data.last_screen = "home"
        self._clear_content()

        outer = tk.Frame(self.content, bg=self.theme["bg"])
        outer.pack(fill="both", expand=True, padx=22, pady=16)

        hero = self.make_panel(outer, bg=self.theme["bg_alt"])
        hero.pack(fill="x", pady=(0, 14))

        hero_left = tk.Frame(hero, bg=self.theme["bg_alt"])
        hero_left.pack(side="left", fill="x", expand=True, padx=24, pady=18)

        self.make_title(hero_left, "Home Dashboard", size=22, accent=True).pack(anchor="w")
        self.make_body_label(
            hero_left,
            "Choose how you want Dragon’s Touch to help forge your next Commander deck.",
            size=11,
            muted=True,
            wrap=760,
        ).pack(anchor="w", pady=(4, 0))

        hero_right = tk.Frame(hero, bg=self.theme["bg_alt"])
        hero_right.pack(side="right", padx=24, pady=12)

        tk.Label(
            hero_right,
            text="☕🐲",
            font=("Georgia", 42),
            fg=self.theme["accent"],
            bg=self.theme["bg_alt"],
        ).pack()

        self.make_body_label(
            hero_right,
            "Your deck.\nYour legend.\nGuided by dragons.",
            size=10,
            muted=False,
            wrap=200,
            justify="center",
        ).pack()

        grid_panel = self.make_panel(outer, bg=self.theme["panel"])
        grid_panel.pack(fill="both", expand=True)

        cards = [
            ("⚒", "Build Up", "Create and refine your deck.", lambda: self.show_workflow("Build Up")),
            ("🔍", "Deck Review /\nClean Up", "Analyze and improve your deck.", lambda: self.show_workflow("Deck Review / Clean Up")),
            ("📥", "Import Deck", "Bring in a deck from file or source.", lambda: self.show_placeholder("Import Deck")),
            ("📖", "Saved Decks /\nHistory", "Open past decks and view history.", lambda: self.show_placeholder("Saved Decks / History")),
            ("🧭", "Combo Finder", "Discover powerful interactions.", lambda: self.show_placeholder("Combo Finder")),
            ("🃏", "Card Suggestions", "Find cards that fit your strategy.", lambda: self.show_placeholder("Card Suggestions")),
            ("📝", "Worksheet /\nGuided Questions", "Answer questions to sharpen your plan.", lambda: self.show_workflow("Worksheet / Guided Questions")),
            ("⚙", "Settings", "Customize the app and preferences.", lambda: self.show_placeholder("Settings")),
        ]

        grid = tk.Frame(grid_panel, bg=self.theme["panel"])
        grid.pack(expand=True, padx=28, pady=28)

        for idx, (icon, title, desc, cmd) in enumerate(cards):
            row = idx // 4
            col = idx % 4
            card = self.make_dashboard_card(grid, icon, title, desc, cmd)
            card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew", ipadx=18, ipady=10)

        for i in range(4):
            grid.columnconfigure(i, weight=1)

    def build_sidebar(self, parent):
        sidebar = self.make_panel(parent, bg=self.theme["panel_alt"])
        sidebar.pack(side="left", fill="y", padx=(0, 12))

        inner = tk.Frame(sidebar, bg=self.theme["panel_alt"])
        inner.pack(fill="both", expand=True, padx=14, pady=14)

        self.make_title(inner, "Current Mode", size=12, accent=True).pack(anchor="w")
        self.make_body_label(inner, self.state_data.mode, size=11).pack(anchor="w", pady=(0, 12))

        self.make_title(inner, "Deck", size=12, accent=True).pack(anchor="w")
        self.make_body_label(inner, self.state_data.deck_name, size=10).pack(anchor="w")
        self.make_body_label(inner, self.state_data.commanders, size=9, muted=True, wrap=190).pack(anchor="w", pady=(0, 12))

        self.make_title(inner, "Selected Persona", size=12, accent=True).pack(anchor="w")
        self.make_body_label(inner, self.state_data.selected_persona, size=10).pack(anchor="w", pady=(0, 8))
        self.make_button(inner, "Change Persona", self.show_persona_selection, compact=True).pack(anchor="w", pady=(0, 12), fill="x")

        self.make_title(inner, "Workflow Steps", size=12, accent=True).pack(anchor="w")
        steps = [
            "Deck Identity",
            "Strategy & Game Plan",
            "Key Cards & Synergies",
            "Strengths & Weaknesses",
            "Meta & Playgroup",
            "Review & Confirm",
        ]
        for i, step in enumerate(steps, 1):
            marker = "➤" if i == self.state_data.workflow_step else "○"
            color = self.theme["accent_2"] if i == self.state_data.workflow_step else self.theme["muted"]
            tk.Label(
                inner,
                text=f"{marker} {i}. {step}",
                font=("Georgia", 9),
                fg=color,
                bg=self.theme["panel_alt"],
                anchor="w",
            ).pack(anchor="w", pady=2)

        tk.Frame(inner, bg=self.theme["border"], height=1).pack(fill="x", pady=14)

        self.make_title(inner, "Deck Status", size=12, accent=True).pack(anchor="w")
        self.make_body_label(
            inner,
            f"Warnings: {self.state_data.warnings}\nSaved progress: Demo only",
            size=9,
            muted=True,
            wrap=190,
        ).pack(anchor="w", pady=(0, 12))

        self.make_button(inner, "Import", lambda: self.show_placeholder("Import Deck"), compact=True).pack(fill="x", pady=3)
        self.make_button(inner, "Export", self.placeholder_action, compact=True).pack(fill="x", pady=3)
        self.make_button(inner, "Forge Report", self.show_processing, compact=True, selected=True).pack(fill="x", pady=(12, 3))

        return sidebar

    def show_workflow(self, mode="Build Up"):
        self.state_data.mode = mode
        self.state_data.last_screen = "workflow"
        self._clear_content()

        outer = tk.Frame(self.content, bg=self.theme["bg"])
        outer.pack(fill="both", expand=True, padx=18, pady=14)

        self.build_sidebar(outer)

        workspace = self.make_panel(outer, bg=self.theme["panel"])
        workspace.pack(side="left", fill="both", expand=True)

        header = tk.Frame(workspace, bg=self.theme["panel"])
        header.pack(fill="x", padx=22, pady=(18, 8))

        self.make_title(header, "Step 1 of 6  •  Deck Identity", size=20, accent=True).pack(anchor="w")
        self.make_body_label(
            header,
            "Let’s begin by understanding the heart of your deck. Answer a few questions to help your guide see your vision.",
            size=10,
            muted=True,
            wrap=850,
        ).pack(anchor="w", pady=(4, 0))

        form = tk.Frame(workspace, bg=self.theme["panel"])
        form.pack(fill="both", expand=True, padx=22, pady=8)

        # Deck name
        self.make_title(form, "Deck Name", size=12).pack(anchor="w", pady=(8, 2))
        deck_entry = self.make_entry(form)
        deck_entry.insert(0, self.state_data.deck_name)
        deck_entry.pack(fill="x", pady=(0, 8))

        # Commander
        self.make_title(form, "Commander / Commanders", size=12).pack(anchor="w", pady=(8, 2))
        commander_entry = self.make_entry(form)
        commander_entry.insert(0, "" if self.state_data.commanders == "No commander selected" else self.state_data.commanders)
        commander_entry.pack(fill="x", pady=(0, 8))

        # Core identity
        self.make_title(form, "Core Identity", size=12).pack(anchor="w", pady=(8, 2))
        self.make_body_label(form, "What is the primary goal or win condition of your deck?", size=10, muted=True).pack(anchor="w")
        goal_box = self.make_textbox(form, height=4)
        goal_box.insert("1.0", "Overwhelm opponents with token armies and value.")
        goal_box.pack(fill="x", pady=(4, 8))

        # Strategy chips
        self.make_title(form, "Strategy Tags", size=12).pack(anchor="w", pady=(8, 2))
        chips = tk.Frame(form, bg=self.theme["panel"])
        chips.pack(anchor="w", pady=(0, 10))

        for name in ["Aggro", "Midrange", "Control", "Combo", "Ramp", "Tokens", "Aristocrats", "Other"]:
            self.make_button(chips, name, compact=True, selected=(name in ["Ramp", "Tokens"])).pack(side="left", padx=3)

        # Playgroup/meta
        row = tk.Frame(form, bg=self.theme["panel"])
        row.pack(fill="x", pady=10)

        left = tk.Frame(row, bg=self.theme["panel"])
        left.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self.make_title(left, "Playgroup / Meta", size=12).pack(anchor="w")
        playgroup = ttk.Combobox(left, values=["Casual / Friendly", "Upgraded Casual", "High Power", "Bracket 3", "Bracket 4"], state="readonly")
        playgroup.set("Casual / Friendly")
        playgroup.pack(fill="x", pady=(4, 0))

        right = tk.Frame(row, bg=self.theme["panel"])
        right.pack(side="left", fill="x", expand=True)

        self.make_title(right, "Budget Target", size=12).pack(anchor="w")
        budget = self.make_entry(right)
        budget.insert(0, "$200")
        budget.pack(fill="x", pady=(4, 0))

        mentor = self.make_panel(form, bg=self.theme["panel_alt"])
        mentor.pack(fill="x", pady=16)

        tk.Label(
            mentor,
            text=f"{self.state_data.selected_persona} says:",
            font=("Georgia", 11, "bold"),
            fg=self.theme["accent_2"],
            bg=self.theme["panel_alt"],
        ).pack(anchor="w", padx=14, pady=(10, 0))

        self.make_body_label(
            mentor,
            "The clearer your goal, the better I can protect the cards that matter. "
            "Advanced edit is available, but skipping guided context may reduce report quality.",
            size=10,
            wrap=820,
        ).pack(anchor="w", padx=14, pady=(4, 10))

        buttons = tk.Frame(workspace, bg=self.theme["panel"])
        buttons.pack(fill="x", padx=22, pady=(8, 18))

        def save_demo_state():
            self.state_data.deck_name = deck_entry.get().strip() or "Untitled Deck"
            self.state_data.commanders = commander_entry.get().strip() or "No commander selected"
            self._build_top_bar()
            self.show_workflow(self.state_data.mode)

        self.make_button(buttons, "Previous", self.placeholder_action, compact=True).pack(side="left")
        self.make_button(buttons, "Save Progress", save_demo_state, compact=True).pack(side="left", padx=8)
        self.make_button(buttons, "Skip to Advanced Edit", self.advanced_warning, compact=True).pack(side="right", padx=8)
        self.make_button(buttons, "Next", self.next_step, compact=True, selected=True).pack(side="right")

    def next_step(self):
        self.state_data.workflow_step += 1
        if self.state_data.workflow_step > 6:
            self.state_data.workflow_step = 1
        self.show_workflow(self.state_data.mode)

    def show_persona_selection(self):
        self.state_data.last_screen = "persona"
        self._clear_content()

        outer = tk.Frame(self.content, bg=self.theme["bg"])
        outer.pack(fill="both", expand=True, padx=22, pady=16)

        header = self.make_panel(outer, bg=self.theme["bg_alt"])
        header.pack(fill="x", pady=(0, 14))

        self.make_title(header, "Select Your Guide", size=22, accent=True).pack(anchor="w", padx=22, pady=(18, 4))
        self.make_body_label(
            header,
            "Choose the persona who will guide, narrate, and present your deck report.",
            size=11,
            muted=True,
            wrap=900,
        ).pack(anchor="w", padx=22, pady=(0, 18))

        body = self.make_panel(outer, bg=self.theme["panel"])
        body.pack(fill="both", expand=True)

        core = tk.Frame(body, bg=self.theme["panel"])
        core.pack(fill="x", padx=22, pady=(18, 8))

        self.make_title(core, "Core Philosophies", size=14, accent=True).pack(anchor="w")

        core_buttons = tk.Frame(core, bg=self.theme["panel"])
        core_buttons.pack(anchor="w", pady=8)

        for text in ["Timmy / Tammy", "Johnny / Jenny", "Spike", "Adventurer"]:
            self.make_button(core_buttons, text, compact=True, selected=(text == "Adventurer")).pack(side="left", padx=4)

        cards_frame = tk.Frame(body, bg=self.theme["panel"])
        cards_frame.pack(fill="both", expand=True, padx=22, pady=10)

        personas = [
            {
                "name": "The Sage",
                "icon": "🧙",
                "theme": "Balance • Wisdom • Growth",
                "desc": "Sees the whole picture. Guides with patience and deep understanding.",
                "traits": ["Balanced", "Educational", "Methodical"],
            },
            {
                "name": "The Warlord",
                "icon": "🐲",
                "theme": "Power • Aggression • Domination",
                "desc": "Seeks victory through strength, speed, and decisive action.",
                "traits": ["Aggressive", "Competitive", "Results-Driven"],
            },
            {
                "name": "The Artisan",
                "icon": "🛠",
                "theme": "Creativity • Synergy • Ingenuity",
                "desc": "Finds beauty in synergy. Loves clever interactions and unique builds.",
                "traits": ["Creative", "Synergistic", "Innovative"],
            },
            {
                "name": "The Adventurer",
                "icon": "🧭",
                "theme": "Discovery • Flexibility • Fun",
                "desc": "Explores the unknown path and helps unsure players find direction.",
                "traits": ["Curious", "Flexible", "Friendly"],
            },
        ]

        for i, p in enumerate(personas):
            card = self.make_persona_card(cards_frame, p)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            cards_frame.columnconfigure(i, weight=1)

        footer = tk.Frame(body, bg=self.theme["panel"])
        footer.pack(fill="x", padx=22, pady=(8, 20))

        self.make_body_label(
            footer,
            f"Current selected guide: {self.state_data.selected_persona}",
            size=11,
            muted=False,
        ).pack(side="left")

        self.make_button(footer, "Continue", lambda: self.show_workflow("Build Up"), compact=True, selected=True).pack(side="right")

    def make_persona_card(self, parent, persona):
        selected = persona["name"] == self.state_data.selected_persona
        bg = self.theme["card_hover"] if selected else self.theme["card"]
        card = self.make_panel(parent, bg=bg)
        card.configure(cursor="hand2")

        tk.Label(
            card,
            text=persona["icon"],
            font=("Georgia", 42),
            fg=self.theme["accent_2"],
            bg=bg,
        ).pack(pady=(22, 6))

        tk.Label(
            card,
            text=persona["name"],
            font=("Georgia", 16, "bold"),
            fg=self.theme["text"],
            bg=bg,
        ).pack()

        tk.Label(
            card,
            text=persona["theme"],
            font=("Georgia", 9, "italic"),
            fg=self.theme["accent_2"],
            bg=bg,
            wraplength=190,
            justify="center",
        ).pack(pady=(2, 8))

        tk.Label(
            card,
            text=persona["desc"],
            font=("Georgia", 10),
            fg=self.theme["muted"],
            bg=bg,
            wraplength=190,
            justify="center",
        ).pack(padx=12, pady=(0, 12))

        traits = tk.Frame(card, bg=bg)
        traits.pack(pady=(0, 16))

        for trait in persona["traits"]:
            tk.Label(
                traits,
                text=trait,
                font=("Georgia", 8, "bold"),
                fg=self.theme["bg"] if selected else self.theme["text"],
                bg=self.theme["accent_2"] if selected else self.theme["panel_alt"],
                padx=6,
                pady=3,
            ).pack(side="left", padx=2)

        def choose(_=None):
            self.state_data.selected_persona = persona["name"]
            self._build_top_bar()
            self.show_persona_selection()

        card.bind("<Button-1>", choose)
        for child in card.winfo_children():
            child.bind("<Button-1>", choose)
            child.configure(cursor="hand2")

        return card

    def show_processing(self):
        self.state_data.last_screen = "processing"
        self._clear_content()

        outer = tk.Frame(self.content, bg=self.theme["bg"])
        outer.pack(fill="both", expand=True, padx=18, pady=14)

        self.build_sidebar(outer)

        workspace = self.make_panel(outer, bg=self.theme["panel"])
        workspace.pack(side="left", fill="both", expand=True)

        self.make_title(workspace, "Forging Your Deck Report...", size=22, accent=True).pack(anchor="w", padx=24, pady=(22, 6))
        self.make_body_label(
            workspace,
            "This prototype shows the future analysis experience. No real deck analysis is running yet.",
            size=10,
            muted=True,
            wrap=850,
        ).pack(anchor="w", padx=24, pady=(0, 14))

        main = tk.Frame(workspace, bg=self.theme["panel"])
        main.pack(fill="both", expand=True, padx=24, pady=10)

        left = self.make_panel(main, bg=self.theme["panel_alt"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        self.make_title(left, f"{self.state_data.selected_persona} Speaks", size=14, accent=True).pack(anchor="w", padx=16, pady=(16, 6))
        narration = (
            "I am checking what your deck is truly trying to do. "
            "Then I will separate cards that support the plan from cards that merely look powerful."
        )
        self.make_body_label(left, narration, size=11, wrap=380).pack(anchor="w", padx=16, pady=(0, 16))

        checklist = [
            "Understanding deck identity",
            "Mapping key themes and mechanics",
            "Analyzing card relationships",
            "Evaluating mana base and curve",
            "Scanning for synergy depth",
            "Checking for weaknesses",
            "Comparing to playgroup meta",
            "Forging final report",
        ]
        for idx, item in enumerate(checklist):
            mark = "✓" if idx < 5 else "•"
            color = self.theme["success"] if idx < 5 else self.theme["muted"]
            tk.Label(
                left,
                text=f"{mark} {item}",
                font=("Georgia", 10),
                fg=color,
                bg=self.theme["panel_alt"],
            ).pack(anchor="w", padx=22, pady=3)

        time_row = tk.Frame(left, bg=self.theme["panel_alt"])
        time_row.pack(side="bottom", fill="x", padx=16, pady=16)

        self.make_body_label(time_row, "Elapsed Time\n00:01:48", size=10, muted=True, wrap=120, justify="center").pack(side="left")
        self.make_body_label(time_row, "Estimated Remaining\n00:01:12", size=10, muted=True, wrap=160, justify="center").pack(side="right")

        center = self.make_panel(main, bg=self.theme["bg_alt"])
        center.pack(side="left", fill="both", expand=True, padx=12)

        tk.Label(
            center,
            text="✦  🃏  ✦\n\n🔥  DRAGON FORGE  🔥\n\n☕🐲\n\nForging insight into legend...",
            font=("Georgia", 22, "bold"),
            fg=self.theme["accent_2"],
            bg=self.theme["bg_alt"],
            justify="center",
        ).pack(expand=True)

        right = self.make_panel(main, bg=self.theme["panel_alt"])
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))

        self.make_title(right, "Analysis Status", size=14, accent=True).pack(anchor="w", padx=16, pady=(16, 10))

        statuses = [
            ("Deck Identity", 100),
            ("Themes & Strategy", 100),
            ("Card Synergy", 86),
            ("Mana & Curve", 72),
            ("Strengths", 44),
            ("Weaknesses", 22),
            ("Meta Analysis", 18),
            ("Report Assembly", 8),
        ]

        for label, value in statuses:
            row = tk.Frame(right, bg=self.theme["panel_alt"])
            row.pack(fill="x", padx=16, pady=7)
            tk.Label(
                row,
                text=label,
                font=("Georgia", 9),
                fg=self.theme["text"],
                bg=self.theme["panel_alt"],
                width=18,
                anchor="w",
            ).pack(side="left")
            bar = ttk.Progressbar(row, orient="horizontal", mode="determinate", value=value, length=130)
            bar.pack(side="left", padx=6)
            tk.Label(
                row,
                text=f"{value}%",
                font=("Georgia", 9),
                fg=self.theme["muted"],
                bg=self.theme["panel_alt"],
                width=5,
                anchor="e",
            ).pack(side="right")

        footer = tk.Frame(workspace, bg=self.theme["panel"])
        footer.pack(fill="x", padx=24, pady=(8, 18))
        self.make_body_label(footer, "Great decks are forged, not found.", size=11, muted=True).pack(side="left")
        self.make_button(footer, "View Demo Report", self.show_report, compact=True, selected=True).pack(side="right")

    def show_report(self):
        self.state_data.last_screen = "report"
        self._clear_content()

        outer = tk.Frame(self.content, bg=self.theme["bg"])
        outer.pack(fill="both", expand=True, padx=18, pady=14)

        self.build_sidebar(outer)

        workspace = self.make_panel(outer, bg=self.theme["panel"])
        workspace.pack(side="left", fill="both", expand=True)

        header = tk.Frame(workspace, bg=self.theme["panel"])
        header.pack(fill="x", padx=22, pady=(18, 8))

        self.make_title(header, "Final Report / Results", size=22, accent=True).pack(side="left")
        self.make_button(header, "Copy", self.placeholder_action, compact=True).pack(side="right", padx=4)
        self.make_button(header, "Save", self.placeholder_action, compact=True).pack(side="right", padx=4)
        self.make_button(header, "Export Report", self.placeholder_action, compact=True, selected=True).pack(side="right", padx=4)

        body = tk.Frame(workspace, bg=self.theme["panel"])
        body.pack(fill="both", expand=True, padx=22, pady=10)

        nav = self.make_panel(body, bg=self.theme["panel_alt"])
        nav.pack(side="left", fill="y", padx=(0, 12))

        tk.Label(
            nav,
            text="Report Overview",
            font=("Georgia", 12, "bold"),
            fg=self.theme["accent_2"],
            bg=self.theme["panel_alt"],
        ).pack(anchor="w", padx=14, pady=(14, 8))

        for item in [
            "Deck Identity / Strategy",
            "Synergy Overview",
            "Strengths",
            "Possible Issues",
            "Suggested Cuts",
            "Recommendations",
            "Next Steps",
        ]:
            self.make_button(nav, item, compact=True).pack(fill="x", padx=12, pady=3)

        report = self.make_panel(body, bg=self.theme["card"])
        report.pack(side="left", fill="both", expand=True)

        report_title = tk.Label(
            report,
            text=f"Presented by {self.state_data.selected_persona}",
            font=("Georgia", 18, "bold"),
            fg=self.theme["accent_2"],
            bg=self.theme["card"],
        )
        report_title.pack(anchor="w", padx=24, pady=(22, 8))

        report_text = tk.Text(
            report,
            bg=self.theme["card"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Georgia", 11),
            wrap="word",
            padx=18,
            pady=12,
        )
        report_text.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        demo_report = f"""
DECK IDENTITY / STRATEGY

This is a demo report. In the final Dragon's Touch build, this area will contain the report generated by your deck helper logic.

Primary Strategy:
A focused Commander deck that uses its commander as the central engine and builds around synergy rather than raw card power.

Secondary Strategy:
A supportive value plan that keeps the deck moving when the commander is unavailable.

SYNERGY OVERVIEW

• Commander support appears clear.
• Several cards appear to advance the deck's main plan.
• Some cards may be generically strong but not ideal for this shell.
• Future versions will separate "bad card" from "wrong card for this deck."

STRENGTHS

✓ Clear deck identity.
✓ Strong potential for thematic cohesion.
✓ Good room for guided improvement.
✓ Persona-guided explanations make the report easier to understand.

POSSIBLE ISSUES

⚠ Some sections are placeholder only.
⚠ Real card analysis is not connected yet.
⚠ Import, export, and combo tools are currently visual mockups.

SUGGESTED CUTS OR IMPROVEMENTS

These are example entries only:

• Review off-plan cards that do not support the primary strategy.
• Protect cards that are low raw power but high synergy.
• Add interaction only if it supports the deck's bracket and playgroup.
• Keep pet cards visible so the tool does not accidentally treat joy as inefficiency.

RECOMMENDATIONS / NEXT STEPS

1. Connect this UI to the current deck_helper.py workflow.
2. Add a real deck import parser.
3. Add persona-specific narration rules.
4. Connect report output to this report viewer.
5. Add Scryfall local database support.
6. Add Commander Spellbook support later.

FINAL PERSONA SUMMARY

"{self.state_data.selected_persona} would say: A deck is not only a list of cards. It is a promise about the kind of game you want to play."
"""
        report_text.insert("1.0", demo_report.strip())
        report_text.configure(state="disabled")

        mascot = tk.Label(
            workspace,
            text="☕🐲  Report forged. Wisdom served warm.",
            font=("Georgia", 11, "italic"),
            fg=self.theme["accent_2"],
            bg=self.theme["panel"],
        )
        mascot.pack(anchor="e", padx=28, pady=(0, 16))

    def show_placeholder(self, mode):
        self.state_data.mode = mode
        self.state_data.last_screen = "placeholder"
        self._clear_content()

        outer = tk.Frame(self.content, bg=self.theme["bg"])
        outer.pack(fill="both", expand=True, padx=18, pady=14)

        self.build_sidebar(outer)

        workspace = self.make_panel(outer, bg=self.theme["panel"])
        workspace.pack(side="left", fill="both", expand=True)

        center = tk.Frame(workspace, bg=self.theme["panel"])
        center.pack(expand=True)

        self.make_title(center, mode, size=24, accent=True).pack(pady=(0, 8))
        self.make_body_label(
            center,
            "This screen is a placeholder in the UI mockup. "
            "The layout is ready for future functionality, but nothing is connected yet.",
            size=12,
            muted=True,
            wrap=520,
            justify="center",
        ).pack(pady=(0, 18))

        tk.Label(
            center,
            text="☕🐲",
            font=("Georgia", 52),
            fg=self.theme["accent"],
            bg=self.theme["panel"],
        ).pack(pady=10)

        self.make_button(center, "Back to Home", self.show_home, selected=True).pack(pady=10)

    # -----------------------------
    # Dialogs / Placeholder Actions
    # -----------------------------

    def placeholder_action(self):
        messagebox.showinfo(
            "Prototype Placeholder",
            "This is a visual UI mockup. This action is not connected yet.",
        )

    def advanced_warning(self):
        messagebox.showwarning(
            "Advanced Edit Warning",
            "Advanced edit will eventually let experienced users skip guided questions.\n\n"
            "Skipping guided context may reduce report quality.",
        )


if __name__ == "__main__":
    app = DragonsTouchApp()
    app.mainloop()
