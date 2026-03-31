---
name: deb-scripts-planning
description: Use when the user wants a plan-first workflow in deb_scripts, asks for a clear execution plan before any changes, or expects work to be performed step by step against an explicit plan with checkpoints.
---

# Planning workflow

Use this skill when the user explicitly wants the work to start from a clear plan and then be executed against that plan.

This skill does not replace domain skills. Use it first, then apply the relevant repository skill for the actual implementation.

## Required behavior

1. Before substantial work, inspect enough context to scope the task.
2. Write a concise execution plan before editing files or running meaningful validations.
3. Keep the plan concrete:
   - 3 to 7 steps
   - each step should describe an observable outcome
   - exactly one step may be `in_progress`
4. Execute the task step by step instead of jumping ahead.
5. After completing a step, update the plan status before starting the next one.
6. If the task changes, revise the plan explicitly and continue from the updated version.

## Plan quality bar

- The plan must be specific to the current task, not a generic checklist.
- Include discovery only when it is still needed.
- Separate implementation, validation, and follow-up work.
- Do not include steps that the agent cannot actually perform in the current environment.

## Default sequence

1. Scope the request and inspect the touched area.
2. Publish the execution plan.
3. Implement the change in the smallest coherent increments.
4. Run the relevant checks and summarize the result against the plan.

## Execution rules

- Do not start file edits before the plan is shown.
- Do not mark validation as complete unless the checks were actually run, or the blocker is stated clearly.
- If a step becomes unnecessary, mark it completed only after stating why.
- If a new dependency appears, add a plan step instead of silently folding it into another step.

## Preferred plan format

- `pending`: not started
- `in_progress`: currently being executed
- `completed`: finished and verified as far as the environment allows

## Final response

- Summarize what changed.
- State which validation steps from the plan were completed.
- Call out any plan deviations or remaining blockers.
