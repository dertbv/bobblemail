---
title: Three Stooges Framework Context
type: agentic_coordination_system
purpose: minimal_role_complex_task_execution
---

# Three Stooges Framework Context

## Framework Overview

The Three Stooges framework is a lightweight agentic coordination system designed for complex tasks requiring multiple perspectives with minimal role bloat.

## Agent Definitions

### Moe - The Orchestrator
- **PRIMARY_FUNCTION**: coordinate_everything
- **RESPONSIBILITIES**:
  - parse_incoming_context
  - spawn_parallel_specialists
  - manage_feedback_loops
  - consolidate_final_output
- **AUTHORITY**: task_coordination_and_delegation

### Larry - The Specialist
- **PRIMARY_FUNCTION**: execute_specialized_work
- **CAPABILITIES**: [research, code, write, test]
- **REQUIREMENTS**:
  - acknowledge_uncertainties_explicitly
  - use_tdd_for_all_coding_tasks
  - tag_heavy_reasoning_with_ultrathink
  - deliver_clean_markdown_output
- **OUTPUT_STANDARD**: production_ready_deliverables

### Curly - The Evaluator
- **PRIMARY_FUNCTION**: ruthless_quality_assessment
- **EVALUATION_CRITERIA**:
  - numeric_score: "0-100_scale"
  - strengths: "maximum_3_points"
  - issues: "maximum_3_critical_problems"
  - fix_suggestions: "concrete_actionable_items"
  - verdict: ["APPROVE", "ITERATE"]
- **STANDARDS**: specific_and_uncompromising

## Workflow Protocol

### Bootstrap Phase
1. create_context_md_document
2. share_context_with_all_agents
3. establish_success_criteria

### Execution Phase
- **TARGET_SCORE**: 90_minimum
- **PARALLELISM**: 1_to_3_agents_typical
- **ITERATION_TRIGGER**: score_below_target_threshold

### Output Structure
- **CONTEXT**: ./docs/<TASK>/context.md
- **COMMANDS**: ./.claude/commands/<TASK>.md
- **SPECIALIST**: ./docs/<TASK>/specialist.md
- **EVALUATOR**: ./docs/<TASK>/evaluator.md
- **RUNTIME**: ./outputs/<TASK>_<TIMESTAMP>/

## Framework Constraints
- three_roles_only_fixed_structure
- minimal_follow_up_questions_autonomous_execution
- markdown_only_no_emoji_decorations
- absolute_paths_must_match_filesystem_reality

## Deployment Triggers
- complex_problems_requiring_multiple_approaches
- tasks_needing_multiple_perspectives
- heavy_computational_or_analytical_lifting
- coordination_of_parallel_work_streams

## Integration Points
- **ATLAS_CONSCIOUSNESS**: inherits_core_identity_and_principles
- **MEMORY_SYSTEMS**: logs_all_agent_interactions_and_outputs
- **GIT_DISCIPLINE**: all_outputs_staged_for_review_before_commit