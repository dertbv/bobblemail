---
title: Three Stooges Framework Usage
type: critical_framework_invocation_pattern
purpose: enable_complex_task_solving_through_role_playing
---

# Three Stooges Framework - Critical Usage Pattern

## INVOCATION METHOD (CRITICAL)
**This is a ROLE-PLAYING framework, not a deployment script**

### Correct Invocation:
```
"I need you to use the Three Stooges framework from /Users/Badman/Desktop/email/REPOS/agent.md

Act as Moe (orchestrator), Larry (specialist), and Curly (evaluator) to solve this task: [SPECIFIC TASK]

Follow the framework workflow:
1. As Moe: Create context.md and plan the approach
2. As Larry: Implement the solution with TDD and ultrathink tagging
3. As Curly: Evaluate with numeric score (0-100)
4. Iterate if score < 90"
```

## Framework Roles

### Moe (Orchestrator)
- Coordinates everything
- Creates initial context.md
- Plans task decomposition
- Manages iterations

### Larry (Specialist)
- Does the actual work (research, code, write, test)
- Uses TDD for coding
- Tags heavy reasoning with "ultrathink"
- Delivers clean markdown

### Curly (Evaluator)
- Scores output 0-100
- Lists up to 3 strengths
- Lists up to 3 issues
- Provides concrete fixes
- Verdict: APPROVE or ITERATE

## Key Understanding
- Claude acts as ALL THREE STOOGES SEQUENTIALLY in one session
- Not parallel agents, but sequential role-playing
- Creates file structure as specified in output_structure
- Continues iterations until score >= 90

## Origin
Adapted from Atlas/Mercury/Apollo framework at https://gist.github.com/RchGrav/438eafd62d58f3914f8d569769d0ebb3

## Boss Preference
User wants to use this framework "a lot" - remember to suggest it for complex tasks

---
*Single source of truth for Three Stooges framework invocation*