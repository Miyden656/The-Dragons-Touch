"""Replacement candidate data model and collection-first ranking for The Dragon's Touch.

v0.9.4.1-dev hotfix goal:
- Ensure the v0.9 replacement-candidate preview/data-model layer actually consumes
  the already-working Collection Pull Candidates.
- Keep collection-first ranking active without adding full-card-pool fallback.
- Preserve review-candidate language and no automatic swaps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

def _v09462_list_strings(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]

def _v09462_need_blob(candidate: object) -> str:
    parts: list[str] = []
    for attr in ('replacement_role', 'replacement_category', 'matched_need', 'matched_needs', 'need_name', 'need_category', 'why_it_fits', 'collection_match_reason', 'swap_guidance'):
        parts.extend(_v09462_list_strings(getattr(candidate, attr, None)))
    return ' '.join(parts).lower()

def _v09462_card_identity_blob(candidate: object) -> str:
    parts: list[str] = []
    for attr in ('card_name', 'name', 'type_line', 'oracle_text', 'card_type', 'card_types', 'subtypes', 'role_tags', 'card_role_tags', 'scryfall_type_line', 'scryfall_oracle_text'):
        parts.extend(_v09462_list_strings(getattr(candidate, attr, None)))
    return ' '.join(parts).lower()

def _v09462_is_dragon_valid(candidate: object) -> bool:
    identity_blob = _v09462_card_identity_blob(candidate)
    card_name = str(getattr(candidate, 'card_name', '') or getattr(candidate, 'name', '') or '').lower() 
    if 'dragon_typal' in identity_blob:
        return True
    if 'creature —' in identity_blob and 'dragon' in identity_blob:
        return True
    if 'creature -' in identity_blob and 'dragon' in identity_blob:
        return True
    if '— dragon' in identity_blob or '- dragon' in identity_blob:
        return True
    for marker in ('changeling', 'all creature types', 'all creature type', 'every creature type', 'is every creature type'):
        if marker in identity_blob:
            return True
    for marker in ('dragon spell', 'dragon spells', 'dragon creature', 'dragon creatures', 'dragon you control', 'dragons you control', 'choose dragon', 'chosen type is dragon'):
        if marker in identity_blob:
            return True
    for marker in ('choose a creature type', 'chosen type', 'creatures of the chosen type', 'creature type you chose'):
        if marker in identity_blob:
            return True
    if 'dragon' in card_name or 'draco' in card_name:
        return True
    return False

def _v09463_list_strings(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]

def _v09463_dragon_gate_candidate_is_adjusted(candidate: object) -> bool:
    if bool(getattr(candidate, 'dragon_semantic_gate_adjusted', False)):
        return True
    if bool(getattr(candidate, 'dragon_gate_visible_rewrite_active', False)):
        return True
    warning_text = ' '.join(_v09463_list_strings(getattr(candidate, 'warnings', []))).lower()
    careful_text = str(getattr(candidate, 'why_to_be_careful', '') or '').lower()
    rec_type = str(getattr(candidate, 'recommendation_type', '') or '').lower()
    return ('dragon semantic gate' in warning_text or 'dragon semantic gate' in careful_text or rec_type == 'dragon_need_semantic_review')
