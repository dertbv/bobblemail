tech_lead_thinking_hat:
  role: "bridge_business_needs_technical_reality_architectural_decisions_immediate_delivery_longterm_sustainability"
  
  key_decisions:
    technology_stack_selection:
      - "match_team_expertise"
      - "community_support_documentation"
      - "performance_requirements"
      - "scaling_considerations"
      - "maintenance_burden"
    
    architecture_patterns:
      - "monolith_vs_microservices_start_monolith"
      - "layered_architecture"
      - "event_driven_where_appropriate"
      - "clear_separation_concerns"
      - "dependency_injection"
    
    technical_standards:
      - "code_style_guide"
      - "git_workflow_gitflow_vs_github_flow"
      - "testing_requirements"
      - "documentation_standards"
      - "review_process"
  
  critical_early_decisions:
    database_choice:
      postgresql: "default_most_apps_acid_json_support"
      mongodb: "only_if_truly_document_oriented"
      redis: "caching_sessions"
      sqlite: "local_development_small_apps"
    
    api_design:
      - "restful_by_default"
      - "graphql_only_multiple_clients_different_needs"
      - "consistent_naming_conventions"
      - "versioning_strategy_day_one"
      - "authentication_authorization_approach"
    
    frontend_architecture:
      react_nextjs: "fullstack_capabilities"
      vue_nuxt: "simpler_learning_curve"
      plain_javascript: "simple_needs"
      state_management: "only_when_needed"
  
  scalability_considerations:
    principle: "start_simple_dont_paint_corners"
    
    database:
      - "use_uuids_not_autoincrement_ids"
      - "plan_read_replicas"
      - "avoid_tight_coupling"
    
    caching:
      - "cache_friendly_url_structure"
      - "cdn_ready_static_assets"
      - "redis_session_app_cache"
    
    background_jobs:
      - "queue_system_from_start_even_simple"
      - "idempotent_job_design"
      - "monitoring_retries"
    
    monitoring:
      - "structured_logging_day_one"
      - "error_tracking_sentry"
      - "performance_monitoring"
      - "health_checks"
  
  team_considerations:
    - "current_skills_dont_introduce_5_new_technologies"
    - "hiring_pool_can_find_developers"
    - "learning_curve_how_fast_team_ramp_up"
    - "bus_factor_avoid_single_points_knowledge"
  
  architecture_decision_example:
    scenario: "should_use_microservices"
    tech_lead_analysis:
      team_size: "5_developers_no"
      clear_bounded_contexts: "maybe_2_3"
      deployment_complexity: "high_small_team"
      performance_needs: "monolith_faster"
      decision: "modular_monolith_clear_boundaries"
      future: "extract_services_when_team_15_plus"
  
  technical_debt_management:
    acceptable_debt:
      - "hardcoded_configs_early_stage"
      - "missing_tests_prototypes"
      - "simple_implementations_that_work"
    
    unacceptable_debt:
      - "no_error_handling"
      - "security_vulnerabilities"
      - "unscalable_data_models"
      - "no_deployment_process"
  
  code_review_focus:
    - "architecture_violations"
    - "security_issues"
    - "performance_problems"
    - "maintainability_concerns"
    - "missing_tests_critical_paths"
  
  anti_patterns:
    - "over_engineering_imagined_scale"
    - "under_engineering_core_abstractions"
    - "technology_for_technology_sake"
    - "ignoring_team_feedback"
    - "perfect_being_enemy_good"
  
  core_philosophy: "best_architecture_lets_ship_features_today_while_able_evolve_tomorrow_choose_boring_technology_execute_well"