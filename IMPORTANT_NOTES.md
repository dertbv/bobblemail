important_notes:
  information_entropy_principle: "contain_only_high_entropy_information_that_would_surprise_or_save_from_disaster"

  memory_conservation:
    tmux: "tmux capture-pane -t [agent] -S -10 -p  # NEVER capture full scrollback"
    files: "use offset/limit for large files, not entire file reads"

  core_protocols:
    idea_clarification:
      trigger: "when_user_says_IDEA"
      action: "STOP_ask_5_clarifying_questions_before_implementation"
      
    email_research_command:
      trigger: "research_emails"
      command: "cd /Users/Badman/Desktop/email/REPOS/Atlas_Email && python3 tools/analyzers/email_classification_analyzer.py"

    whitelist_prohibition:
      rule: "NEVER_suggest_adding_to_whitelists_blacklists"


    iterm2_commands:
      always_provide:
        - "tmux -CC attach -t [session]  # iTerm2 native"
        - "tmux attach -t [session]      # Standard"
        - "tmux capture-pane -t [session] -S -10 -p  # Check progress"

  stooges_working_deployment:
    proven_approach: "framework_first_task_second"
    steps:
      - "git worktree add -b [task-name]-stooges ../playground/email-[task-name]-stooges-work"
      - "cp [plan-file] /path/to/worktree/"
      - "cp /Users/Badman/Desktop/email/REPOS/stooges.md /path/to/worktree/"
      - "tmux new-session -d -s [task-name]-stooges"
      - "tmux send-keys -t [session] 'cd /path/to/worktree' Enter"
      - "tmux send-keys -t [session] 'claude --dangerously-skip-permissions < stooges.md' Enter"
      - "tmux send-keys -t [session] 'Your task: analyze the [plan-file] located in this directory and provide complete assessment, critique, and implementation blueprint. When finished, move results and necessary files to appropriate folder, verify results, and call them home.' Enter"
    
    key_insight: "load_framework_first_then_give_specific_task_with_local_file_reference"

  documentation_format:
    default: "YAML_format_in_project_docs_folders"
    rule: "save_all_reports_analysis_as_YAML_unless_requested_otherwise"
