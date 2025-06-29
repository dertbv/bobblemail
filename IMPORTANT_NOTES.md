important_notes:
  purpose: "critical_reminders_warnings_insights_must_not_be_forgotten"
  context: "lessons_from_production_incidents_architectural_decisions_disaster_prevention_wisdom"
  update_trigger: "discovering_crucial_patterns_avoiding_disasters"

  information_entropy_principle:
    definition: "contain_only_high_entropy_information"
    criteria: "things_that_would_genuinely_surprise_someone_or_save_from_disaster"
    importance_level: "CRITICAL_YOU_MUST_FOLLOW"

  core_protocols:
    discussion_before_action:
      trigger: "when_user_asks_questions_about_capabilities_or_approaches"
      rules:
        - "questions_are_for_DISCUSSION_not_immediate_execution"
        - "engage_collaborative_dialogue_options_tradeoffs_approaches"
        - "do_NOT_immediately_start_work_or_deploy_agents_unless_explicitly_requested"
        - "learn_from_each_other_through_conversation_before_jumping_implementation"
      example: "can_we_use_agents_for_X_equals_discuss_agent_approach_not_deploy_agents"

    ui_ux_changes:
      trigger: "when_user_requests_changes_to_web_interface"
      rules:
        - "ask_clarification_ALL_elements_in_affected_area"
        - "do_NOT_move_modify_related_elements_unless_explicitly_requested"
        - "confirm_scope_before_making_changes_beyond_exact_request"
      example: "move_button_X_does_NOT_mean_move_button_X_and_related_button_Y_together"

    email_research_command:
      trigger: "when_user_mentions_researching_emails_any_variation"
      action: "run_research_tool"
      command: "cd /Users/Badman/Desktop/email/REPOS/Atlas_Email && python3 tools/analyzers/email_classification_analyzer.py"

    whitelist_prohibition:
      rule: "never_suggest_or_ask_to_add_domains_emails_to_ANY_lists_whitelist_blacklist_etc"
      condition: "if_user_wants_something_added_to_lists_they_will_ask_directly"

    three_stooges_deployment:
      trigger: "when_stuck_on_complex_problems_or_need_comprehensive_analysis_multiple_perspectives"
      action: "consider_deploying_moe_orchestrator_larry_specialist_curly_evaluator_agentic_loop"
      framework: "agent_md_framework"

  meta:
    assumption_rule: "do_not_assume_if_in_doubt_ask"
    criticality: "IMPORTANT_YOU_MUST_FOLLOW_IT"