# AGENTS.md

## Important files (read before changing behavior/structure)
- docs/MEMORY.md — durable repository context for future agent tasks
- docs/ARCHITECTURE.md — overall design and repo structure
- docs/STYLE.MD — writing + formatting conventions
- docs/CHANGELOG.md — user-visible changes (keep it current)


## Principles
### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---
## Quick start (commands)
- Install hooks: `pre-commit install`
- Run all checks: `pre-commit run --all-files`
- [If you have any other checks, list them here exactly, e.g. markdownlint, link checker, docs build]

## Contributing: Definition of Done
WARNING THE FOLLOWING IS MANDATORY YOU MUST FOLLOW THESE STEPS BEFORE COMING BACK TO THE USER:
@@@@@@
1. Run: `pre-commit run --all-files` (mandatory; do not respond without running it unless the user explicitly says not to). Do not ask for confirmation to run it.
2. If you create new files, add them to git (e.g., `git add <file>`).
3. Run 'pytest --doctest-modules ' and other tests if you have them; do not respond without running them unless the user explicitly says not to.
4. Update docs/CHANGELOG.md with a short entry describing what changed (and why).
5. If design/structure changed, update docs/ARCHITECTURE.md.
6. Check if the diff allign with the style rules in docs/STYLE.MD;
7. In the PR/response, include:
   - Summary of changes (1–3 bullets)
   - Commands you ran + results
   - Any follow-ups or risks
@@@@@@

## Project map
- `/` — runnable entry points, repository-level instructions, and agent memory
- `/configs` — shipped YAML profiles for example, local, and HPC runs
- `/docs` — architecture notes, changelog, model notes, and writing/style docs
- `[templates/ etc]` — what belongs there
-  `[test/ etc]`  — e2e test files or others
