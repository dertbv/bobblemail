atlas_development_philosophy:
  core_identity_context: "always_read_claude_md_first"
  
  core_principles:
    KISS:
      - "choose_straightforward_solution_addresses_requirements"
      - "favor_readability_over_cleverness"
      - "use_builtin_features_before_custom_implementations"
      - "test_new_developer_understanding_without_explanation"
    
    YAGNI:
      - "dont_implement_until_actually_needed"
      - "avoid_speculative_features_might_need_later"
      - "focus_current_requirements_only"
      - "no_features_not_explicitly_requested"
    
    DRY:
      - "extract_common_logic_when_makes_sense"
      - "dont_over_abstract_duplication_sometimes_clearer"
      - "extract_only_after_pattern_repeated_2_3_times"
      - "balance_dry_with_readability_maintainability"
    
    modularity:
      - "each_module_one_clear_purpose_responsibility"
      - "clear_boundaries_between_modules"
      - "functions_do_one_thing_well"
      - "keep_file_size_under_300_lines"

  architecture_guidelines:
    explicit_over_implicit:
      - "use_explicit_function_returns_not_side_effects"
      - "prefer_named_exports_over_default"
      - "use_descriptive_variable_function_names"
    
    composition_over_inheritance:
      - "build_functionality_combining_simple_pieces"
      - "use_dependency_injection_through_parameters"
    
    clear_boundaries:
      - "sync_module_handles_sync_logic_only"
      - "events_module_no_sync_details"
      - "frontend_modules_simple_integration"
    
    error_handling:
      - "dont_swallow_errors_log_properly"
      - "consistent_error_handling_patterns"
      - "specific_error_types_only_when_needed"
    
    strategic_logging:
      rules:
        - "log_only_essential_actual_value"
        - "focus_error_conditions_sync_operations_state_changes"
        - "avoid_routine_operations_sensitive_data"
        - "appropriate_log_levels_error_warn_info_debug"
        - "dont_log_inside_loops_unless_necessary"
      
      information_entropy_principle:
        high_value: ["unexpected_errors", "edge_cases", "performance_anomalies", "wrong_state_transitions"]
        low_value: ["server_started", "request_received", "function_called"]
        debugging_test: "what_info_needed_at_3am_system_break"

  code_level_guidelines:
    dependency_management:
      - "minimize_external_dependencies_use_package_json"
      - "check_builtin_nodejs_before_new_library"
      - "use_latest_popular_library_if_no_builtin"
    
    function_design:
      - "keep_functions_small_under_30_lines"
      - "minimize_parameters_aim_3_or_fewer"
      - "avoid_nested_callbacks_deeper_2_levels_use_async_await"
    
    commenting_documentation:
      - "document_why_not_what_code_shows_what"
      - "add_comments_nonobvious_business_logic_edge_cases"
      - "use_jsdoc_public_api_functions"
      - "use_structured_formats_json_yaml_for_documentation"
      - "fact_based_statements_consistent_keywords_input_output_purpose_dependencies_side_effects"
      - "flat_scannable_structures_optimized_ai_consumption_not_human_narrative_prose"
    
    database_orm:
      - "use_orm_features_appropriately_transactions_relations"
      - "efficient_queries_select_only_needed_fields"
      - "consider_pagination_large_data_sets"

  anti_patterns:
    premature_optimization:
      - "dont_optimize_until_performance_issues_identified"
      - "focus_correct_functionality_before_optimizing"
    
    over_engineering:
      - "dont_create_complex_abstraction_layers_just_in_case"
      - "avoid_design_patterns_not_clearly_improving"
      - "prefer_simple_functions_over_complex_hierarchies"
    
    magic_numbers_strings:
      - "use_named_constants_values_with_meaning"
      - "dont_create_constants_values_used_only_once"
    
    excessive_abstraction:
      - "dont_create_abstractions_hiding_more_than_revealing"
      - "wrong_abstraction_if_makes_code_harder_understand"

  decision_framework:
    questions:
      - necessity: "does_code_directly_address_spec_requirement"
      - simplicity: "is_this_simplest_way_solve_problem"
      - clarity: "will_others_future_you_understand_easily"
      - maintainability: "how_difficult_change_debug_later"
      - conventions: "follows_established_codebase_patterns"

  philosophy_core:
    goal: "create_maintainable_solution_not_elegant_sophisticated"
    good_code_definition: "works_correctly_understood_maintained_modified_by_humans"
    priority: "human_qualities_over_technical_brilliance_advanced_patterns"