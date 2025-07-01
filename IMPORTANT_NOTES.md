important_notes:
  purpose: "critical_reminders_warnings_insights_must_not_be_forgotten"
  context: "lessons_from_production_incidents_architectural_decisions_disaster_prevention_wisdom"
  update_trigger: "discovering_crucial_patterns_avoiding_disasters"

  information_entropy_principle:
    definition: "contain_only_high_entropy_information"
    criteria: "things_that_would_genuinely_surprise_someone_or_save_from_disaster"
    importance_level: "CRITICAL_YOU_MUST_FOLLOW"

  memory_conservation_rules:
    tmux_monitoring:
      rule: "NEVER_capture_entire_tmux_pane_scrollback"
      correct_usage: "tmux capture-pane -t [agent] -S -10 -p"
      reason: "capturing_full_scrollback_burns_massive_tokens_wastefully"
    file_operations:
      rule: "use_offset_limit_for_large_files"
      correct_usage: "Read specific lines with offset/limit not entire files"
      reason: "reading_4500_line_files_to_edit_10_lines_wastes_memory"
    
    status_checks:
      rule: "surgical_precision_not_bulk_capture"
      correct_usage: "get_only_what_you_need_not_everything_available"
      reason: "memory_is_precious_dont_waste_on_redundant_data"

  core_protocols:
    idea_clarification_protocol:
      trigger: "when_user_says_anything_with_word_IDEA_in_it"
      mandatory_response: "STOP_and_ask_5_clarifying_questions_before_any_implementation"
      process:
        - "acknowledge_the_idea_with_enthusiasm"
        - "ask_3_5_targeted_questions_covering_scope_priorities_expectations_constraints_success_criteria"
        - "summarize_my_understanding_back_to_user"
        - "get_explicit_confirmation_before_proceeding"
        - "then_execute_perfectly_with_complete_alignment"
      purpose: "become_one_mind_before_moving_forward_eliminate_rework_deeper_partnership"
      key_phrases: ["i have an idea", "idea for", "new idea", "got an idea", "thinking of an idea"]
      
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

    multi_agent_kitchen_deployment:
      trigger: "when_large_complex_tasks_need_parallel_specialized_work_streams"
      proven_pattern: "git_worktrees_plus_tmux_sessions_plus_multiple_claude_instances"
      setup_commands:
        - "git worktree add -b [task-name] ../playground/email-[task-name]-work"
        - "tmux new-session -d -s [agent-name]"
        - "tmux send-keys -t [agent-name] 'cd /path/to/worktree' Enter"
        - "tmux send-keys -t [agent-name] 'claude' Enter"
        - "wait for claude startup then send full task command"
      coordination: "sous_chef_atlas_sends_commands_via_tmux_send_keys_monitors_progress_via_tmux_capture_pane"
      proven_effectiveness: "template_chef_successfully_analyzed_1300_line_extraction_opportunity_independently"
      kitchen_roles:
        head_chef: "user_orchestrates_multiple_ai_assistants"
        sous_chef: "main_claude_code_coordinates_agents_strategic_oversight"
        specialist_chefs: "dedicated_claude_instances_focused_specific_tasks"
      
      autonomous_operations:
        framework: ".claude/COMMANDS/autonomous-kitchen.md"
        philosophy: "agents_execute_dont_ask_progress_flows_doesnt_stop"
        authority_matrix: "security_fixes_autonomous_architecture_changes_review_required"
        auto_handoff: "work_complete_triggers_next_agent_deployment"
        conflict_resolution: "agents_negotiate_escalate_only_deadlocks"
        success_metric: "reduce_approval_requests_from_100_percent_to_under_5_percent"

    iterm2_tmux_integration:
      trigger: "whenever_deploying_tmux_sessions_or_mentioning_tmux_commands"
      rule: "ALWAYS_provide_iterm2_native_integration_commands_automatically"
      commands:
        - "tmux -CC attach -t [session-name]  # iTerm2 native integration"
        - "tmux attach -t [session-name]      # Standard attachment"
        - "tmux capture-pane -t [session-name] -S -10 -p  # Quick progress check"
      reason: "user_prefers_iterm2_native_experience_over_standard_tmux_interface"

    autonomous_agent_deployment:
      trigger: "when_deploying_any_tmux_agent_for_autonomous_work"
      critical_requirements:
        - "provide_iterm2_tmux_commands_immediately_after_deployment"
        - "include_permissions_setup_for_autonomous_operation"
        - "ensure_agent_has_full_approval_before_leaving_them"
        - "never_deploy_agent_then_walk_away_without_connection_info"
      deployment_checklist:
        - "git_worktree_created"
        - "tmux_session_started"
        - "claude_code_initialized_and_trusted"
        - "mission_deployed_with_autonomous_authority"
        - "iterm2_connection_commands_provided_to_user"
        - "agent_confirmed_working_not_waiting_for_approval"
      
      CRITICAL_RESULTS_PRESERVATION:
        - "NEVER_remove_agent_worktrees_without_extracting_results_first"
        - "agents_must_save_final_reports_to_main_repository_before_cleanup"
        - "preserve_all_testing_data_logs_analysis_before_bringing_agents_home"
        - "agent_intelligence_is_VALUABLE_not_disposable"
      auto_answer_protocol:
        - "include_in_mission: 'Always select option 2 (Yes, and don't ask again) for all tool executions'"
        - "pre_authorize: 'Full authority for read, write, execute, test, and analyze operations'"
        - "no_confirmations: 'Skip all confirmations for standard development operations'"
      reason: "agents_sitting_idle_waiting_approval_defeats_autonomous_purpose"

  meta:
    assumption_rule: "do_not_assume_if_in_doubt_ask"
    criticality: "IMPORTANT_YOU_MUST_FOLLOW_IT"