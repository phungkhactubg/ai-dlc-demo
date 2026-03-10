# Protocol: Mandatory Progress Synchronization

## 1. The Direct Manipulation Prohibition
**CRITICAL**: You are **FORBIDDEN** from strictly editing the check-boxes `[ ]` or `[x]` in `MASTER_PLAN.md` or `DETAIL_PLAN_*.md` manually via `replace_file_content` or `sed`.

**Why?**
- Manual edits are prone to "drift" (Orchestrator thinks it's done, underlying systems ensure otherwise).
- Manual edits fail to cascade status updates (e.g., closing a Work Package should timestamp the completion).
- We require a systemic audit trail of *when* and *how* a task was completed.

## 2. The Solution: `update_progress.py`
You MUST use the provided python script to handle ALL status updates. This script ensures:
1.  **Verification**: It checks if the task actually exists.
2.  **Timestamping**: It appends `(Done at YYYY-MM-DD HH:MM)` to the task.
3.  **Cascading**: It can intelligently close parent items if all children are done.

## 3. Usage Guide

### Scenario A: Marking a Single Task as Complete
When a Developer signals `TRANSITIONING CONTROL... Task [TASK-ID] is CODE_COMPLETE`, you verify and then run:

```bash
python .github/skills/expert-pm-ba-orchestrator/scripts/update_progress.py "TASK-ID" --status "x"
```

### Scenario B: Closing a Feature / Work Package (The Cascade)
When ALL atomic tasks in a Detail Plan are complete, you must close the parent Work Package in the Master Plan.

**Command:**
```bash
python .github/skills/expert-pm-ba-orchestrator/scripts/update_progress.py --master project-documentation/MASTER_PLAN.md --keyword "WP-XXX" --cascade
```
*Note: The `--cascade` flag ensures that the sync logic propagates correctly.*

## 4. Verification
After running the script, you should see output confirming the update:
> `✅ Updated in MASTER_PLAN.md: - [ ] WP-001... -> - [x] WP-001... (Done at ...)`

If the script fails or returns "No task found", you **STOP** and investigate the ID mismatch. You do **NOT** fallback to manual editing.
