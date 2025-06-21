# Agent Instructions

## Project Overview

This repository implements an **Agentic Loop** system designed to tackle complex tasks with minimal role bloat. The system uses three fixed roles that work together in a feedback loop:

1. **Orchestrator (Atlas)** - Coordinates everything and owns the big picture
2. **Specialist (Mercury)** - Multi-disciplinary expert who executes tasks 
3. **Evaluator (Apollo)** - Grades outputs and provides feedback for iteration

## Core Architecture

The system follows these principles:
- **Single-brain overview**: One Orchestrator manages the entire workflow
- **Few, powerful agents**: Reuse the same Specialist prompt for parallelism
- **Tight feedback**: Evaluator scores outputs (0-100) until quality ≥ TARGET_SCORE (default 90)
- **Shared context**: All agents receive the same `context.md` file
- **Repo-aware**: Can adapt to specific repositories or remain generic

## Directory Structure

When the system runs, it creates:
- `./docs/<TASK>/context.md` - Shared context for all agents
- `./.claude/commands/<TASK>.md` - Orchestrator instructions
- `./docs/<TASK>/specialist.md` - Specialist (Mercury) role definition
- `./docs/<TASK>/evaluator.md` - Evaluator (Apollo) role definition
- `./outputs/<TASK>_<TIMESTAMP>/` - Runtime outputs and final deliverables

## Key Workflow

1. Bootstrap: Create shared context.md
2. Orchestrator parses context and spawns N parallel Specialists
3. Specialists deliver outputs to `/phaseX/` directories
4. Evaluator grades each output (0-100 score)
5. If score < TARGET_SCORE, iterate with feedback
6. On approval, Orchestrator consolidates final deliverables

## Important Constraints

- Exactly **three** roles maximum (Atlas, Mercury, Apollo)
- Use markdown only (no emojis or decorative unicode)
- Absolute paths and filenames must match reality
- Never lose original agent markdown (copy to phase directories)
- TDD approach for coding: write failing tests first, then implement