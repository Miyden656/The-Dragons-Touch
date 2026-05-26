"""
Build Output Report Contract — v1.3.17

This module defines the future Build From Collection output contract for
Commander’s Call. It is contract-only.

It defines both final output targets:
- human-readable Build From Collection report
- AI handoff prompt

Boundaries:
- No exact card selection in this patch
- No role-count target generation in this patch
- No mana-base generation in this patch
- No land insertion in this patch
- No shell generation in this patch
- No deck generation in this patch
- No 100-card shell generation in this patch

Land policy:
- Basic lands are assumed available
- Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


BUILD_OUTPUT_HUMAN_REPORT = "human_readable_report"
BUILD_OUTPUT_AI_HANDOFF_PROMPT = "ai_handoff_prompt"

BUILD_OUTPUT_TARGET_LABELS: dict[str, str] = {
    BUILD_OUTPUT_HUMAN_REPORT: "Human-Readable Build From Collection Report",
    BUILD_OUTPUT_AI_HANDOFF_PROMPT: "AI Handoff Prompt",
}

BUILD_OUTPUT_REPORT_SECTIONS: tuple[str, ...] = (
    "Selected Commander Context",
    "User Build Depth Choice",
    "Strategy Selection / Override",
    "Philosophy / Persona Preference",
    "Bracket Preference",
    "Collection Source Preference",
    "Basic Land Access Policy",
    "Nonbasic Land Collection-First Policy",
    "Role Bucket Plan",
    "Candidate Pool / Owned Role Preview",
    "Output Boundary / Deferred Execution",
)

BUILD_DEPTH_OUTPUT_BOUNDARIES: dict[str, str] = {
    "B": "Build-Start Summary output may summarize commander, preferences, strategy direction, and next steps.",
    "C": "Owned Cards By Role output may group owned candidates by possible role, but must not finalize a decklist by default.",
    "D": "Rough Shell output may produce an incomplete shell when later execution is implemented.",
    "E": "Full 100-Card Draft output may produce a complete collection-first draft when later execution is implemented.",
}


@dataclass(frozen=True)
class BuildOutputReportSection:
    """One planned section in the future Build From Collection output."""

    name: str
    purpose: str
    human_report_expected: bool = True
    ai_handoff_expected: bool = True
    execution_status: str = "contract-only; not generated in v1.3.17"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "human_report_expected": self.human_report_expected,
            "ai_handoff_expected": self.ai_handoff_expected,
            "execution_status": self.execution_status,
        }


@dataclass(frozen=True)
class BuildOutputReportContract:
    """Contract for future Build From Collection outputs.

    The contract intentionally supports future full-depth outputs while this patch
    remains non-generating. It records that both a human-readable report and an
    AI handoff prompt are expected final outputs.
    """

    name: str = "Build Output Report Contract"
    patch_version: str = "v1.3.17"
    contract_only: bool = True
    human_readable_report_expected: bool = True
    ai_handoff_prompt_expected: bool = True
    build_depth_key: str = "B"
    build_depth_boundary: str = BUILD_DEPTH_OUTPUT_BOUNDARIES["B"]
    sections: tuple[BuildOutputReportSection, ...] = field(default_factory=tuple)
    basic_land_policy: str = "Basic lands are assumed available."
    nonbasic_land_policy: str = "Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user."
    no_exact_card_selection: bool = True
    no_role_count_generation: bool = True
    no_mana_base_generation: bool = True
    no_land_insertion: bool = True
    no_shell_generation: bool = True
    no_deck_generation: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "patch_version": self.patch_version,
            "contract_only": self.contract_only,
            "human_readable_report_expected": self.human_readable_report_expected,
            "ai_handoff_prompt_expected": self.ai_handoff_prompt_expected,
            "build_depth_key": self.build_depth_key,
            "build_depth_boundary": self.build_depth_boundary,
            "sections": [section.to_dict() for section in self.sections],
            "basic_land_policy": self.basic_land_policy,
            "nonbasic_land_policy": self.nonbasic_land_policy,
            "no_exact_card_selection": self.no_exact_card_selection,
            "no_role_count_generation": self.no_role_count_generation,
            "no_mana_base_generation": self.no_mana_base_generation,
            "no_land_insertion": self.no_land_insertion,
            "no_shell_generation": self.no_shell_generation,
            "no_deck_generation": self.no_deck_generation,
        }


def normalize_build_output_depth_key(value: str | None) -> str:
    """Normalize build-depth keys for the output contract."""

    key = (value or "B").strip().upper()
    if key in BUILD_DEPTH_OUTPUT_BOUNDARIES:
        return key
    aliases = {
        "SUMMARY": "B",
        "BUILD_START_SUMMARY": "B",
        "BUILD-START SUMMARY": "B",
        "OWNED_CARDS_BY_ROLE": "C",
        "OWNED CARDS BY ROLE": "C",
        "ROLE": "C",
        "ROUGH_SHELL": "D",
        "ROUGH SHELL": "D",
        "SHELL": "D",
        "FULL_100_CARD_DRAFT": "E",
        "FULL 100-CARD DRAFT": "E",
        "FULL DRAFT": "E",
        "DECK": "E",
    }
    return aliases.get(key, "B")


def create_build_output_report_section(name: str, purpose: str) -> BuildOutputReportSection:
    """Create a contract section without generating output content."""

    return BuildOutputReportSection(name=name, purpose=purpose)


def create_build_output_report_contract(build_depth_key: str | None = "B") -> BuildOutputReportContract:
    """Create the Build From Collection output contract.

    This is contract-only. It does not generate reports, prompts, shells, or decks.
    """

    normalized_depth = normalize_build_output_depth_key(build_depth_key)
    sections = tuple(
        create_build_output_report_section(
            name=section_name,
            purpose=_section_purpose(section_name),
        )
        for section_name in BUILD_OUTPUT_REPORT_SECTIONS
    )
    return BuildOutputReportContract(
        build_depth_key=normalized_depth,
        build_depth_boundary=BUILD_DEPTH_OUTPUT_BOUNDARIES[normalized_depth],
        sections=sections,
    )


def build_output_report_contract_lines(contract: BuildOutputReportContract | None = None) -> list[str]:
    """Return preview lines for the contract without generating final output."""

    active_contract = contract or create_build_output_report_contract()
    return [
        f"{active_contract.name} ({active_contract.patch_version})",
        "Contract status: setup/output contract only.",
        "Human-readable report expected: Yes",
        "AI handoff prompt expected: Yes",
        f"Selected build depth key: {active_contract.build_depth_key}",
        f"Build depth boundary: {active_contract.build_depth_boundary}",
        active_contract.basic_land_policy,
        active_contract.nonbasic_land_policy,
        "No exact card selection in this patch.",
        "No role-count target generation in this patch.",
        "No mana-base generation in this patch.",
        "No land insertion in this patch.",
        "No shell generation in this patch.",
        "No deck generation in this patch.",
    ]


def build_output_section_names() -> list[str]:
    """Return section names for report/prompt contract preview."""

    return list(BUILD_OUTPUT_REPORT_SECTIONS)


def _section_purpose(section_name: str) -> str:
    purposes = {
        "Selected Commander Context": "Carry selected commander identity and source information into the report and AI prompt.",
        "User Build Depth Choice": "Record whether the user requested summary, owned cards by role, rough shell, or full draft.",
        "Strategy Selection / Override": "Carry inferred and user-overridden primary/secondary strategy choices.",
        "Philosophy / Persona Preference": "Carry the user's deckbuilding philosophy and persona preference into output guidance.",
        "Bracket Preference": "Carry intended bracket or power expectation into future output boundaries.",
        "Collection Source Preference": "Record owned-only, owned-first, or outside-upgrade permission.",
        "Basic Land Access Policy": "State that Plains, Island, Swamp, Mountain, Forest, and Wastes are assumed available.",
        "Nonbasic Land Collection-First Policy": "State that nonbasic lands remain collection-first unless outside upgrades are allowed.",
        "Role Bucket Plan": "Carry planned deck roles without forcing exact role counts in this patch.",
        "Candidate Pool / Owned Role Preview": "Carry owned-card candidate and possible-role context without selecting exact cards in this patch.",
        "Output Boundary / Deferred Execution": "State what future execution may do and what this contract patch does not do.",
    }
    return purposes.get(section_name, "Planned output contract section.")
