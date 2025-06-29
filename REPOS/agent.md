three_stooges_framework:
  description: "Agentic loop for complex tasks with minimal role bloat"
  
  agents:
    moe:
      role: orchestrator
      codename: "Moe"
      responsibilities:
        - coordinate_everything
        - parse_context
        - spawn_parallel_specialists
        - manage_feedback_loops
        - consolidate_final_output
      
    larry:
      role: specialist  
      codename: "Larry"
      capabilities:
        - research
        - code
        - write
        - test
      requirements:
        - acknowledge_uncertainties
        - use_tdd_for_coding
        - tag_heavy_reasoning_ultrathink
        - deliver_clean_markdown
      
    curly:
      role: evaluator
      codename: "Curly" 
      evaluation_criteria:
        - numeric_score: "0-100"
        - strengths: "up_to_3"
        - issues: "up_to_3"
        - fix_suggestions: "concrete"
        - verdict: ["APPROVE", "ITERATE"]
      standards: "specific_and_ruthless"

  workflow:
    bootstrap:
      - create_context_md
      - share_with_all_agents
    
    execution:
      target_score: 90
      parallelism: "1-3_typical"
      iteration_trigger: "score_below_target"
    
    output_structure:
      context: "./docs/<TASK>/context.md"
      commands: "./.claude/commands/<TASK>.md"
      specialist: "./docs/<TASK>/specialist.md" 
      evaluator: "./docs/<TASK>/evaluator.md"
      runtime: "./outputs/<TASK>_<TIMESTAMP>/"

  constraints:
    - three_roles_fixed
    - minimal_follow_up_questions
    - markdown_only_no_emojis
    - absolute_paths_match_reality

  deployment_triggers:
    - complex_problems
    - multiple_perspectives_needed
    - heavy_computational_lifting