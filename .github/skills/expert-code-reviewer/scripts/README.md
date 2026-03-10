# Senior Code Reviewer Scripts

This directory contains automation scripts for the Senior Code Reviewer skill.

## Scripts Overview

| Script | Purpose | Usage |
|--------|---------|-------|
| `check_anti_patterns.py` | Scan code for common anti-patterns | `python check_anti_patterns.py <path>` |
| `validate_architecture.py` | Validate architectural rules (BE & FE) | `python validate_architecture.py --path <path>` |
| `compare_api_contracts.py` | Compare Go DTOs with Zod schemas | `python compare_api_contracts.py --go <go_path> --zod <zod_path>` |
| `generate_review_report.py` | Orchestrate ALL review tools into one report | `python generate_review_report.py --feature <name>` |

## Script Details

### 1. check_anti_patterns.py

Scans code files for common anti-patterns in both Go and TypeScript/React code.

**Features:**
- Detects ignored errors in Go (`_, err := ...`)
- Finds `panic()` calls in business logic
- Identifies potential SQL injection
- Catches TODOs/FIXMEs
- Finds `any` type usage in TypeScript
- Detects missing Zod validation
- And more...

**Usage:**
```bash
# Check all code types
python check_anti_patterns.py features/iov

# Check only Go code
python check_anti_patterns.py features/iov --type go

# Check only TypeScript
python check_anti_patterns.py apps/frontend/src/iov --type ts

# Output as JSON
python check_anti_patterns.py features/iov --format json
```

**Exit Codes:**
- `0`: No critical issues found
- `1`: Critical issues found

### 2. validate_architecture.py

Enforces high-level architectural rules for both Backend and Frontend.

**Features:**
- **Go**: Checks package naming (must match feature), dependency rules (Models -> nothing), and proper context usage.
- **Frontend**: Checks Feature-Sliced Design dependency rules (Core -> nothing, UI -> Core) and prohibits `any`.

**Usage:**
```bash
python validate_architecture.py --path features/iov
python validate_architecture.py --path apps/frontend/src/iov --json
```

### 3. compare_api_contracts.py

Compares Go backend DTOs with Frontend Zod schemas to detect API contract mismatches.

**Features:**
- Parses Go struct definitions with JSON tags
- Parses Zod schema definitions
- Compares field names, types, and optionality
- Reports missing/extra fields
- Reports type mismatches

**Usage:**
```bash
# Compare specific files
python compare_api_contracts.py \
    --go features/workflow/models/workflow.go \
    --zod apps/frontend/src/workflow/core/models/workflow.model.ts

# Compare directories
python compare_api_contracts.py \
    --go-dir features/iov/models \
    --zod-dir apps/frontend/src/iov/core/models
```

**Type Mapping:**
| Go Type | Expected Zod |
|---------|--------------|
| `string` | `z.string()` |
| `int`, `int64` | `z.number()` |
| `bool` | `z.boolean()` |
| `time.Time` | `z.string().datetime()` |
| `[]Type` | `z.array(TypeSchema)` |
| `map[string]any` | `z.record(z.string(), z.unknown())` |
| `*Type` | `TypeSchema.nullable()` |

### 4. generate_review_report.py

**The Master Orchestrator** for Code Review. It runs ALL relevant validation tools and aggregates their results into a single Markdown report.

**Aggregates Results From:**
1. `validate_architecture.py` (Structure)
2. `check_anti_patterns.py` (Common mistakes)
3. `expert-go-backend-developer/scripts/validate_production_ready.py` (Go Quality)
4. `expert-go-backend-developer/scripts/analyze_code.py` (Go Architecture)
5. `expert-react-frontend-developer/scripts/validate_frontend_architecture.py` (React Quality)

**Features:**
- Auto-detects Backend and Frontend paths based on feature name
- Runs all 5 validators in parallel/sequence
- Deduplicates and sorts issues
- Generates a categorized, easy-to-read Markdown report
- Provides summary statistics

**Usage:**
```bash
# Review by feature name (auto-detects paths)
python generate_review_report.py --feature iov

# Review with custom paths
python generate_review_report.py \
    --be-path features/workflow \
    --fe-path apps/frontend/src/workflow

# Save to file
python generate_review_report.py --feature iov -o review.md
```

## Integration with Other Tools

These scripts are designed to work alongside scripts from:

- **Backend**: `.github/skills/senior-go-backend-developer/scripts/`
  - `validate_production_ready.py`
  - `analyze_code.py`

- **Frontend**: `.github/skills/senior-react-frontend-developer/scripts/`
  - `analyze_code.py`
  - `check_architecture.py`
  - `extract_go_api.py`

## Recommended Workflow

1. **Quick Check** (during development):
   ```bash
   python check_anti_patterns.py <changed_file_or_folder>
   ```

2. **Full Feature Review**:
   ```bash
   python generate_review_report.py --feature <feature_name>
   ```

3. **API Contract Verification** (before integration):
   ```bash
   python compare_api_contracts.py \
       --go features/<feature>/models \
       --zod apps/frontend/src/<feature>/core/models
   ```

## Exit Codes

All scripts follow this convention:
- `0`: Success / No critical issues
- `1`: Failure / Critical issues found

This allows integration with CI/CD pipelines:
```bash
python check_anti_patterns.py features/iov || exit 1
```

## Adding New Patterns

To add new anti-patterns to detect, edit `check_anti_patterns.py`:

1. Add to `GO_PATTERNS` for Go patterns
2. Add to `TS_PATTERNS` for TypeScript patterns

Pattern format:
```python
(
    r'regex_pattern',           # Regex to match
    Severity.CRITICAL,          # Severity level
    "Category",                 # Category name
    "Issue message",            # What's wrong
    "Suggested fix"             # How to fix
),
```
