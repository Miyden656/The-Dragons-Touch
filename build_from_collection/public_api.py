"""Build From Collection foundation for The Dragon's Touch v1.3.

v1.3.0 intentionally creates only the selected-commander handoff baseline.
v1.3.2 adds the build preference data shape that can travel with that handoff.
v1.3.3 adds the basic land access assumption and Build Setup Panel Preview.
v1.3.5 adds planning-only collection-first role bucket definitions.
v1.3.6 adds planning-only strategy-to-role bucket mapping preview.
v1.3.7 adds shape-only collection candidate pool data contract.
v1.3.8 adds preview-only owned card role classification.
It does not generate a 100-card deck shell, alter normal deck review, or
modify cut/replacement/scoring/combo behavior.
"""

from .basic_lands import (
    ASSUMED_AVAILABLE_BASIC_LANDS,
    BASIC_LAND_ACCESS_ASSUMPTION,
    BasicLandAccessPolicy,
    create_basic_land_access_policy,
    describe_basic_land_access_assumption,
    is_assumed_available_basic_land,
)
from .build_setup import BuildSetupPanelPreviewData, build_setup_panel_preview
from .commander_preference_preview import CommanderPreferenceHandoffPreviewData, create_commander_preference_handoff_preview
from .models import (
    BracketPreference,
    CommanderBuildScope,
    CommanderSelectionHandoff,
    DiscoveryModeSelection,
    PhilosophySelection,
    StrategySelection,
    build_commander_selection_handoff,
)
from .owned_role_classification import (
    OwnedCardRoleClassification,
    OwnedCardRoleClassificationPreview,
    classify_owned_card_role_preview,
    create_owned_card_role_classification_preview,
    normalize_role_bucket_name,
)
from .candidate_pool import (
    CollectionCandidatePoolEntry,
    CollectionCandidatePoolShape,
    CollectionCandidateSource,
    create_collection_candidate_pool_entry,
    create_collection_candidate_pool_shape,
    normalize_collection_candidate_name,
)
from .strategy_role_mapping import (
    STRATEGY_TO_ROLE_BUCKET_MAPPING,
    StrategyRoleBucketMapping,
    StrategyRoleBucketMappingPreview,
    create_strategy_role_bucket_mapping,
    create_strategy_role_bucket_mapping_preview,
    normalize_strategy_key,
)
from .role_buckets import (
    COLLECTION_FIRST_ROLE_BUCKETS,
    CollectionFirstRoleBucketDefinition,
    CollectionFirstRoleBucketPlan,
    create_collection_first_role_bucket_plan,
    role_bucket_names,
)
from .preferences import (
    BuildPreferenceDataShape,
    CommanderBuildStartContext,
    build_commander_build_start_context,
    build_preferences_from_values,
    create_default_build_preferences,
)
from .scope import V1_3_SCOPE_BOUNDARY, describe_v1_3_scope

__all__ = [
    "ASSUMED_AVAILABLE_BASIC_LANDS",
    "BASIC_LAND_ACCESS_ASSUMPTION",
    "BasicLandAccessPolicy",
    "BracketPreference",
    "BuildPreferenceDataShape",
    "BuildSetupPanelPreviewData",
    "CommanderPreferenceHandoffPreviewData",
    "CommanderBuildScope",
    "CommanderBuildStartContext",
    "STRATEGY_TO_ROLE_BUCKET_MAPPING",
    "StrategyRoleBucketMapping",
    "OwnedCardRoleClassification",
    "OwnedCardRoleClassificationPreview",
    "classify_owned_card_role_preview",
    "create_owned_card_role_classification_preview",
    "normalize_role_bucket_name",
    "CollectionCandidatePoolEntry",
    "CollectionCandidatePoolShape",
    "CollectionCandidateSource",
    "create_collection_candidate_pool_entry",
    "create_collection_candidate_pool_shape",
    "normalize_collection_candidate_name",
    "StrategyRoleBucketMappingPreview",
    "create_strategy_role_bucket_mapping",
    "create_strategy_role_bucket_mapping_preview",
    "normalize_strategy_key",
    "COLLECTION_FIRST_ROLE_BUCKETS",
    "CollectionFirstRoleBucketDefinition",
    "CollectionFirstRoleBucketPlan",
    "create_collection_first_role_bucket_plan",
    "role_bucket_names",
    "CommanderSelectionHandoff",
    "DiscoveryModeSelection",
    "PhilosophySelection",
    "StrategySelection",
    "build_commander_build_start_context",
    "build_commander_selection_handoff",
    "build_preferences_from_values",
    "build_setup_panel_preview",
    "create_commander_preference_handoff_preview",
    "create_basic_land_access_policy",
    "create_default_build_preferences",
    "describe_basic_land_access_assumption",
    "is_assumed_available_basic_land",
    "V1_3_SCOPE_BOUNDARY",
    "describe_v1_3_scope",
]

# v1.3.9 — Commander Shell Skeleton Preview exports
from .shell_skeleton import (
    CommanderShellSkeletonPreview,
    CommanderShellSkeletonSection,
    SHELL_SKELETON_SECTIONS,
    create_commander_shell_skeleton_preview,
    create_commander_shell_skeleton_section,
    shell_skeleton_section_names,
)


# v1.3.11 Build From Collection Setup Summary Preview exports
try:
    from .setup_summary import (
        BuildFromCollectionSetupSummaryPreview,
        create_build_from_collection_setup_summary_preview,
        setup_summary_preview_lines,
    )
except Exception:  # pragma: no cover - keeps partial patch states import-safe
    pass


# v1.3.12 Build Depth Selection Model exports
try:
    from .build_depth import (
        BUILD_DEPTH_FULL_100_CARD_DRAFT,
        BUILD_DEPTH_OWNED_CARDS_BY_ROLE,
        BUILD_DEPTH_ROUGH_SHELL,
        BUILD_DEPTH_START_SUMMARY,
        BuildDepthOption,
        BuildDepthSelectionModel,
        build_depth_option_labels,
        build_depth_selection_lines,
        create_build_depth_selection_model,
        get_build_depth_option,
        normalize_build_depth_key,
    )
except Exception:  # pragma: no cover - keeps partial patch states import-safe
    pass

# v1.3.14 Strategy Selection / Override Preview exports
try:
    from .strategy_selection import (
        STRATEGY_SELECTION_LABELS,
        StrategySelectionOverridePreview,
        create_strategy_selection_override_preview,
        infer_strategy_candidates_from_commander,
        normalize_strategy_selection_label,
        strategy_label_for_key,
        strategy_selection_labels,
        strategy_selection_preview_lines,
    )
except Exception:  # pragma: no cover - keeps partial patch states import-safe
    pass

# v1.3.15 Philosophy + Bracket Build Preference UI exports
try:
    from .philosophy_bracket_preferences import (
        BRACKET_PREFERENCE_OPTIONS,
        MAIN_PHILOSOPHY_OPTIONS,
        SUB_PHILOSOPHY_OPTIONS,
        PhilosophyBracketBuildPreferencePreview,
        bracket_preference_options,
        create_philosophy_bracket_build_preference_preview,
        normalize_bracket_preference,
        normalize_philosophy_choice,
        normalize_sub_philosophy_choice,
        philosophy_bracket_preview_lines,
        philosophy_main_options,
        philosophy_sub_options,
    )
except Exception:  # pragma: no cover - keeps partial patch states import-safe
    pass

# v1.3.16 Collection Source Preference UI exports
try:
    from .collection_source_preferences import (
        COLLECTION_SOURCE_OWNED_MISSING,
        COLLECTION_SOURCE_OWNED_ONLY,
        COLLECTION_SOURCE_OWNED_UPGRADES,
        COLLECTION_SOURCE_PREFERENCE_OPTIONS,
        CollectionSourcePreferencePreview,
        collection_source_allows_outside_upgrades,
        collection_source_preference_label,
        collection_source_preference_labels,
        collection_source_preference_lines,
        create_collection_source_preference_preview,
        normalize_collection_source_preference,
    )
except Exception:  # pragma: no cover - keeps partial patch states import-safe
    pass

# v1.3.17 exports: Build Output Report Contract
try:
    from .build_output_contract import (
        BUILD_OUTPUT_AI_HANDOFF_PROMPT,
        BUILD_OUTPUT_HUMAN_REPORT,
        BUILD_OUTPUT_REPORT_SECTIONS,
        BUILD_OUTPUT_TARGET_LABELS,
        BuildOutputReportContract,
        BuildOutputReportSection,
        build_output_report_contract_lines,
        build_output_section_names,
        create_build_output_report_contract,
        create_build_output_report_section,
        normalize_build_output_depth_key,
    )
except Exception:  # pragma: no cover - keeps package import tolerant during patching
    pass


# v1.3.18 Build-Start Summary Output exports
try:
    from .build_start_summary import (
        BuildStartSummaryOutput,
        BUILD_START_SUMMARY_OUTPUT_NAME,
        create_build_start_summary_output,
        build_start_summary_output_lines,
    )
except Exception:  # pragma: no cover - keeps partial patch states import-safe
    pass

# v1.3.19 Build-Start Summary UI / Report Write Hook exports
try:
    from .build_start_report_writer import (
        BuildStartSummaryWriteResult,
        BUILD_START_SUMMARY_REPORT_WRITER_NAME,
        write_build_start_summary_output,
        build_start_summary_write_result_lines,
        default_build_start_summary_output_root,
    )
except Exception:  # pragma: no cover - keeps partial patch states import-safe
    pass

# v1.3.20 Owned Cards By Role Output exports.
from .owned_cards_by_role_output import (
    OwnedCardsByRoleEntry,
    OwnedCardsByRoleOutput,
    create_owned_cards_by_role_entry,
    create_owned_cards_by_role_output,
    infer_possible_roles_for_owned_card,
    owned_cards_by_role_handoff_prompt,
    owned_cards_by_role_output_lines,
)
# v1.3.21 Owned Cards By Role UI / Report Write Hook exports.
from .owned_cards_by_role_report_writer import (
    OwnedCardsByRoleWriteResult,
    write_owned_cards_by_role_output,
    owned_cards_by_role_write_result_lines,
)

# v1.3.22 Rough Shell Output Model exports
from .rough_shell_output import (
    RoughShellOutputModel,
    RoughShellSection,
    create_rough_shell_output_model,
    create_rough_shell_section,
    rough_shell_handoff_prompt,
    rough_shell_output_model_lines,
    rough_shell_section_names,
)

# v1.3.23 rough shell report writer exports
from .rough_shell_report_writer import (
    RoughShellWriteResult,
    write_rough_shell_output,
    rough_shell_write_result_lines,
)

# v1.3.24 Full 100-Card Draft Output Model exports
from .full_100_card_draft_output import (
    Full100CardDraftOutputModel,
    Full100CardDraftSection,
    create_full_100_card_draft_output_model,
    create_full_100_card_draft_section,
    full_100_card_draft_handoff_prompt,
    full_100_card_draft_output_model_lines,
    full_100_card_draft_section_names,
)

# v1.3.25 full 100-card draft report writer exports
from .full_100_card_draft_report_writer import (
    Full100CardDraftWriteResult,
    write_full_100_card_draft_output,
    full_100_card_draft_write_result_lines,
)
# v1.3.27 Build From Collection Output Selector UI exports.
from .output_selector_ui import (
    BuildFromCollectionOutputSelectorUIPreview,
    create_build_from_collection_output_selector_ui_preview,
    build_from_collection_output_selector_ui_preview_lines,
)

# v1.3.28 Build From Collection Output Selector Execution Guard exports
from .output_execution_guard import (
    BuildFromCollectionOutputExecutionGuard,
    build_from_collection_output_execution_allowed,
    build_from_collection_output_execution_guard_lines,
    create_build_from_collection_output_execution_guard,
)

# v1.3.29 Build From Collection Output Execution UI Hook exports
from .output_execution_ui import (
    BuildFromCollectionOutputExecutionUIPreview,
    create_build_from_collection_output_execution_ui_preview,
    build_from_collection_output_execution_ui_preview_lines,
)

# v1.3.30 Build From Collection Output Execute Selected Report Button exports
from .output_selected_report_executor import (
    BuildFromCollectionSelectedReportExecutionResult,
    execute_build_from_collection_selected_report,
    build_from_collection_selected_report_execution_lines,
)
# v1.3.31 Build From Collection Execute Selected Report UI Polish exports
from .output_execution_ui_polish import (
    BuildFromCollectionExecuteSelectedReportUIPolish,
    create_build_from_collection_execute_selected_report_ui_polish,
    build_from_collection_execute_selected_report_ui_polish_lines,
)

# v1.3.32 Build From Collection Report Output Smoke Test exports
from .report_output_smoke_test import (
    BuildFromCollectionReportOutputSmokeTestItem,
    BuildFromCollectionReportOutputSmokeTestResult,
    build_from_collection_report_output_smoke_test_lines,
    run_build_from_collection_report_output_smoke_test,
)

# v1.3.26 Build From Collection Output Selector / Routing exports
from .output_router import (
    BuildFromCollectionOutputRoute,
    build_from_collection_output_route_lines,
    build_from_collection_output_route_names,
    build_from_collection_output_routes,
    create_build_from_collection_output_route,
)

# v1.5.30 facade split foundation: moved implementation body from build_from_collection/__init__.py to build_from_collection/public_api.py.
