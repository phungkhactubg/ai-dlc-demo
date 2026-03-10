# CI/CD Workflows

This directory contains GitHub Actions workflows for the AV Platform project.

## Workflows Overview

### 1. CI/CD Pipeline (`ci.yml`)

Main CI/CD pipeline that runs on every push and pull request to `main` or `develop` branches.

**Jobs:**

1. **Build and Test**
   - Checks out code
   - Sets up Go 1.25.5
   - Installs dependencies
   - Builds all packages
   - Runs tests with race detection
   - Uploads coverage to Codecov

2. **Validate Routes (Prevents Duplicates - BUG-008)** ⚠️ CRITICAL
   - Runs after build job
   - Validates all route definitions across the codebase
   - Detects duplicate route paths
   - Ensures all routes have corresponding controllers
   - **FAILS** the pipeline if duplicates found
   - **Blocks deployment** until issues resolved

3. **Security Scan**
   - Runs Gosec security scanner
   - Runs custom security validator on all features
   - Continues on warning (non-blocking for now)

4. **Code Quality Checks**
   - Validates Go formatting (gofmt)
   - Runs `go vet`
   - Checks production readiness
   - **FAILS** on `context.TODO()` in production code
   - Warns on TODOs and placeholders

5. **Deploy**
   - Runs only on `main` branch push
   - Depends on all previous jobs passing
   - Deploys to staging
   - Runs smoke tests

### 2. Route Validation (`route-validation.yml`)

Dedicated workflow for route validation. Can be triggered manually or runs automatically.

**Purpose:**
- Prevents BUG-008 (duplicate route definitions)
- Validates all routes before deployment
- Provides detailed failure messages

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`
- Manual trigger (workflow_dispatch)

**Steps:**
1. Validates routes using `validate_route_controller_mismatch_v2.py`
2. Fails if duplicates found with detailed fix instructions
3. Uploads validation results as artifacts
4. Comments on PR with results (for pull requests)

## Route Validation Details

### What It Checks

1. **Duplicate Route Paths**: Detects multiple handlers for same HTTP method + path
   - Example: Two `GET /api/users` definitions will FAIL

2. **Missing Controllers**: Ensures every route has a corresponding controller handler
   - Routes without handlers will be flagged

3. **Route-to-Controller Mapping**: Verifies correct variable mapping in route definitions

### How It Prevents Future Duplicates

The validation script `validate_route_controller_mismatch_v2.py`:

1. **Scans all features**: Recursively searches `features/` directory
2. **Extracts routes**: Parses all route definitions (Echo, Gin, etc.)
3. **Extracts controllers**: Identifies all controller types
4. **Compares**: Checks for duplicates and missing mappings
5. **Reports**: Provides detailed list of issues with file locations

### Fixing Duplicate Routes

If validation fails:

1. **Review the output** to see exact duplicate paths and file locations
2. **Search for duplicates**:
   ```bash
   grep -r 'Route.*"/path"' features/
   ```
3. **Remove duplicates**: Keep only one handler per unique route path
4. **Verify ownership**: Ensure the correct controller owns the route
5. **Re-run validation**: Push changes to trigger validation again

### Exit Codes

- `0`: Success - No issues found
- `1`: Failure - Duplicate routes or missing controllers detected

### Deployment Blocker

The route validation job is **required** for deployment. The deploy job in `ci.yml` has:

```yaml
needs: [build, validate-routes, security-scan, code-quality]
```

This means deployment will NOT happen unless `validate-routes` passes.

## Local Validation

You can run route validation locally before pushing:

```bash
python .claude/skills/expert-go-backend-developer/scripts/validate_route_controller_mismatch_v2.py
```

## Quality Gates

The following checks are **mandatory** and will block deployment:

1. ✅ Build passes
2. ✅ Tests pass
3. ✅ Route validation passes (no duplicates)
4. ✅ No `context.TODO()` in production code
5. ✅ Security scan passes (critical issues)
6. ✅ Code quality checks pass

## References

- **BUG-008**: Duplicate route definitions issue
- **Validation Script**: `.claude/skills/expert-go-backend-developer/scripts/validate_route_controller_mismatch_v2.py`
- **Documentation**: `AGENTS.md` - Expert Go Backend Developer section
