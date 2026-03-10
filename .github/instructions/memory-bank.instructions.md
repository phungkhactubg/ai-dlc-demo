---
applyTo: "**"
---

# Memory Bank Context Commands

## Slash Command Handling

When user types a slash command, execute as documented in `copilot-instructions.md`:

| Command | Action |
|---------|--------|
| `/new-context <name>` | Archive current + create new context |
| `/list-contexts` | Show all available contexts |
| `/archive-context` | Archive current context |
| `/restore-context <name>` | Restore from archive |
| `/save-progress` | Save session notes to context |
| `/switch-context <name>` | Quick switch contexts |
| `/context` | Show current CONTEXT.md |
| `/decisions` | Show DECISIONS.md |
| `/progress` | Show PROGRESS.md |

## Memory Bank Location
- Context: `.github/memory-bank/CONTEXT.md`
- Decisions: `.github/memory-bank/DECISIONS.md`
- Progress: `.github/memory-bank/PROGRESS.md`
- Archive: `.github/memory-bank/archive/`

## At Session Start
Always offer to read `.github/memory-bank/CONTEXT.md` for context continuity.
