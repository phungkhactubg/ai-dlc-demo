# Expert Java Backend Developer - Scripts

This folder contains utility scripts to automate common Java backend development tasks following the Expert Java Backend Developer skill guidelines.

## Available Scripts (16 total)

### 1. `scaffold_feature.py` (Recommended)
**Purpose:** Scaffold a complete feature module with all layers (model, repository, service, controller, adapter, config, exception).

```bash
# Usage
python scaffold_feature.py <feature_name>

# Example
python scaffold_feature.py notifications
python scaffold_feature.py user_management
```

**Output:** Creates a complete feature structure:
```
src/main/java/com/example/<feature_name>/
├── model/
│   ├── <Feature>Entity.java
│   ├── Create<Feature>Request.java
│   └── <Feature>Response.java
├── repository/
│   └── <Feature>Repository.java
├── service/
│   ├── <Feature>Service.java (interface)
│   └── impl/
│       └── <Feature>ServiceImpl.java
├── controller/
│   └── <Feature>Controller.java
├── adapter/
│   └── <Feature>ExternalAdapter.java
├── config/
│   └── <Feature>Config.java
└── exception/
    └── <Feature>Exception.java
```

### 2. `validate_production_ready.py` ⚠️ MANDATORY
**Purpose:** Validate that code is production-ready with NO TODOs, placeholders, or missing error handling.

**THIS SCRIPT MUST BE RUN BEFORE MARKING ANY TASK COMPLETE.**

```bash
# Validate a feature directory
python validate_production_ready.py src/main/java/com/example/notifications

# Strict mode (additional checks)
python validate_production_ready.py src/main/java/com/example/notifications --strict

# JSON output for CI/CD
python validate_production_ready.py src/main/java/com/example/notifications --json
```

**Checks performed:**
- 🚨 **CRITICAL**: TODOs, FIXMEs, XXX, HACK comments
- 🚨 **CRITICAL**: Placeholder/stub comments
- 🚨 **CRITICAL**: Empty catch blocks
- 🚨 **CRITICAL**: Empty method bodies
- ❌ **ERROR**: Throwing generic `Exception`
- ❌ **ERROR**: Field injection with `@Autowired`
- ❌ **ERROR**: Missing `@Transactional` on data-modifying methods
- ⚠️ **WARNING**: Very short method bodies
- ⚠️ **WARNING**: Returning `null` instead of `Optional<T>`

**Exit codes:**
- `0`: All checks passed
- `1`: Errors found
- `2`: Critical violations found (blocking)

### 3. `validate_exception_handling.py`
**Purpose:** Specialized validator for exception handling issues.

```bash
# Validate a feature
python validate_exception_handling.py src/main/java/com/example/notifications

# Strict mode
python validate_exception_handling.py src/main/java/com/example/notifications --strict

# JSON output
python validate_exception_handling.py src/main/java/com/example/notifications --json
```

**Checks performed:**
- 🚨 **CRITICAL**: Empty catch blocks
- 🚨 **CRITICAL**: Catching generic `Exception` without rethrowing
- 🚨 **CRITICAL**: Throwing generic `Exception`
- ⚠️ **WARNING**: Logging exceptions without context
- ⚠️ **WARNING**: Missing custom exceptions

### 4. `validate_transaction_boundary.py`
**Purpose:** Verify `@Transactional` usage on service methods.

```bash
# Validate service layer
python validate_transaction_boundary.py src/main/java/com/example/notifications/service

# JSON output
python validate_transaction_boundary.py src/main/java/com/example/notifications/service --json
```

**Checks performed:**
- 🚨 **CRITICAL**: Data-modifying methods without `@Transactional`
- ⚠️ **WARNING**: `@Transactional` on controllers (should be in services)
- ⚠️ **WARNING**: Read operations without `readOnly = true`

### 5. `validate_security.py` 🔒 SECURITY SCANNER
**Purpose:** Detect common security vulnerabilities in Java code.

```bash
python validate_security.py src/main/java/com/example/notifications
python validate_security.py src/main/java/com/example/notifications --strict
python validate_security.py src/main/java/com/example/notifications --json
```

**Checks performed:**
- 🔴 **SQL Injection**: String concatenation in queries
- 🔴 **Hardcoded Secrets**: Passwords, API keys, tokens
- 🔴 **Command Injection**: Runtime.exec with user input
- 🟠 **Weak Crypto**: MD5, SHA1, DES, RC4
- 🟠 **SSRF**: User-controlled URLs in HTTP requests

### 6. `validate_function_size.py`
**Purpose:** Check for methods exceeding 50 lines and classes exceeding 500 lines.

```bash
# Validate a feature
python validate_function_size.py src/main/java/com/example/notifications

# Custom thresholds
python validate_function_size.py src/main/java/com/example/notifications --max-method 60 --max-class 600

# JSON output
python validate_function_size.py src/main/java/com/example/notifications --json
```

**Checks performed:**
- 🔴 **CRITICAL**: Methods > 70 lines
- 🔶 **WARNING**: Methods > 50 lines
- 🔴 **CRITICAL**: Classes > 700 lines
- 🔶 **WARNING**: Classes > 500 lines

### 7. `validate_lombok_usage.py`
**Purpose:** Verify Lombok annotation best practices.

```bash
# Validate a feature
python validate_lombok_usage.py src/main/java/com/example/notifications

# JSON output
python validate_lombok_usage.py src/main/java/com/example/notifications --json
```

**Checks performed:**
- ⚠️ **WARNING**: Field injection with `@Autowired`
- ⚠️ **WARNING**: `@Getter`/`@Setter` when `@Data` would suffice
- ⚠️ **WARNING**: Missing `@RequiredArgsConstructor` for constructor injection

### 8. `validate_null_safety.py` 🆕 NULL SAFETY CHECKER
**Purpose:** Check for null safety issues and Optional<T> usage.

```bash
# Validate a feature
python validate_null_safety.py src/main/java/com/example/notifications

# JSON output
python validate_null_safety.py src/main/java/com/example/notifications --json
```

**Checks performed:**
- 🔴 **ERROR**: Unsafe `.get()` calls without `isPresent()` check
- 🔴 **ERROR**: Unsafe Optional dereference chains
- ⚠️ **WARNING**: Returning `null` directly (use `Optional<T>`)
- ⚠️ **WARNING**: Methods missing Optional return types
- ℹ️ **INFO**: Missing `@NonNull`/`@Nullable` annotations

### 9. `analyze_code.py`
**Purpose:** Analyze Java source code for architecture compliance and code quality.

```bash
# Analyze a single file
python analyze_code.py src/main/java/com/example/notifications/service/NotificationService.java

# Analyze a directory
python analyze_code.py src/main/java/com/example/notifications

# JSON output (for CI/CD)
python analyze_code.py src/main/java/com/example/ --json
```

**Checks performed:**
- Forbidden patterns (global state, direct driver imports in services)
- Required patterns per file type (interfaces in services, validation in controllers)
- Method complexity (warns if > 50 lines)
- Sensitive data logging (passwords, tokens)

### 10. `analyze_cyclomatic_complexity.py` 🧮 COMPLEXITY METRICS
**Purpose:** Measure cyclomatic complexity to identify overly complex methods.

```bash
python analyze_cyclomatic_complexity.py src/main/java/com/example/notifications
python analyze_cyclomatic_complexity.py src/main/java/com/example/notifications --threshold 10
python analyze_cyclomatic_complexity.py src/main/java/com/example/notifications --json
```

**Guidelines:**
- ≤ 10: ✅ Good
- 11-15: ⚠️ Consider refactoring
- > 15: 🔴 Must refactor

### 11. `analyze_dependencies.py` 🔗 DEPENDENCY ANALYZER
**Purpose:** Analyze package dependencies and detect architectural issues.

```bash
python analyze_dependencies.py src/main/java/com/example/
python analyze_dependencies.py src/main/java/com/example/ --graph deps.dot
python analyze_dependencies.py src/main/java/com/example/ --metrics
```

### 12. `detect_dead_code.py` 💀 DEAD CODE DETECTOR
**Purpose:** Find unused methods, variables, and classes.

```bash
python detect_dead_code.py src/main/java/com/example/notifications
python detect_dead_code.py src/main/java/com/example/notifications --include-exports
python detect_dead_code.py src/main/java/com/example/notifications --json
```

### 13. `generate_unit_tests.py` 🧪 TEST GENERATOR
**Purpose:** Generate JUnit 5 test stubs for Java classes.

```bash
# Generate tests for a directory
python generate_unit_tests.py src/main/java/com/example/notifications/service

# Specify output directory
python generate_unit_tests.py src/main/java/com/example/notifications --output src/test/java

# Overwrite existing tests
python generate_unit_tests.py src/main/java/com/example/notifications --force
```

**Features:**
- Generates test classes with `@ExtendWith(MockitoExtension.class)`
- Creates `@Mock` for dependencies
- Creates test methods for public methods
- Proper setup for Spring Boot testing

### 14. `extract_api_contract.py` 📋 API CONTRACT EXTRACTOR
**Purpose:** Extract OpenAPI 3.0 specification from Spring Boot controllers.

```bash
# Extract from controller directory
python extract_api_contract.py src/main/java/com/example/notifications/controller

# Save to file
python extract_api_contract.py src/main/java/com/example/notifications/controller --output api.yaml

# JSON output
python extract_api_contract.py src/main/java/com/example/notifications/controller --json
```

**Features:**
- Extracts endpoints from `@RestController` classes
- Parses `@GetMapping`, `@PostMapping`, etc.
- Includes `@Operation` summaries
- Generates OpenAPI 3.0 JSON/YAML

### 15. `update_progress.py` 📊 PROGRESS TRACKER
**Purpose:** Track implementation progress for features.

```bash
# Check feature progress
python update_progress.py src/main/java/com/example/notifications

# Update status
python update_progress.py src/main/java/com/example/notifications --status in-progress

# Add note
python update_progress.py src/main/java/com/example/notifications --note "Need to add tests"

# Don't update PROGRESS.md file
python update_progress.py src/main/java/com/example/notifications --no-update
```

**Features:**
- Detects required components (model, repository, service, controller, etc.)
- Calculates progress percentage
- Generates PROGRESS.md file with status summary

### 16. `generate_quality_report.py` 📊 QUALITY REPORT (ONE-STOP CHECK)
**Purpose:** Run ALL validation scripts and generate a comprehensive quality score.

```bash
python generate_quality_report.py src/main/java/com/example/notifications
python generate_quality_report.py src/main/java/com/example/notifications --html report.html
python generate_quality_report.py src/main/java/com/example/notifications --json
```

**Features:**
- Runs all validators automatically
- Calculates overall quality score (0-100)
- Generates HTML/JSON reports
- Perfect for CI/CD integration

## Quick Start Workflow

1. **Create a new feature:**
   ```bash
   cd /path/to/project
   python .claude/skills/expert-java-backend-developer/scripts/scaffold_feature.py notifications
   ```

2. **Implement your business logic** in the generated files.

3. **Generate test stubs:**
   ```bash
   python .claude/skills/expert-java-backend-developer/scripts/generate_unit_tests.py src/main/java/com/example/notifications/service
   ```

4. **Run ALL validation scripts (MANDATORY):**
   ```bash
   # ONE-STOP QUALITY CHECK (RECOMMENDED)
   python .claude/skills/expert-java-backend-developer/scripts/generate_quality_report.py src/main/java/com/example/notifications

   # OR run individual validators
   python .claude/skills/expert-java-backend-developer/scripts/validate_production_ready.py src/main/java/com/example/notifications
   python .claude/skills/expert-java-backend-developer/scripts/validate_exception_handling.py src/main/java/com/example/notifications
   python .claude/skills/expert-java-backend-developer/scripts/validate_transaction_boundary.py src/main/java/com/example/notifications/service
   python .claude/skills/expert-java-backend-developer/scripts/validate_security.py src/main/java/com/example/notifications
   python .claude/skills/expert-java-backend-developer/scripts/validate_null_safety.py src/main/java/com/example/notifications
   ```

5. **Extract API documentation:**
   ```bash
   python .claude/skills/expert-java-backend-developer/scripts/extract_api_contract.py src/main/java/com/example/notifications/controller --output api.yaml
   ```

6. **Update progress:**
   ```bash
   python .claude/skills/expert-java-backend-developer/scripts/update_progress.py src/main/java/com/example/notifications --status completed
   ```

7. **Build and verify:**
   ```bash
   mvn clean compile
   mvn test
   ```

## Requirements

- Python 3.8+ (No external dependencies required)
- Java 17+ (for building the generated code)
- Maven 3.9+ or Gradle 8.x (for building)

## Script Categories

### 🔒 Security (CRITICAL)
- `validate_security.py` - SQL injection, secrets, weak crypto

### ✅ Quality (MANDATORY before completion)
- `validate_production_ready.py` - TODOs, empty catches, placeholders
- `validate_exception_handling.py` - Exception patterns
- `validate_transaction_boundary.py` - @Transactional checks
- `validate_null_safety.py` - Optional<T> usage

### 📏 Code Style
- `validate_function_size.py` - Method/class size limits
- `validate_lombok_usage.py` - Lombok best practices

### 🔍 Analysis
- `analyze_code.py` - Architecture compliance
- `analyze_cyclomatic_complexity.py` - Complexity metrics
- `analyze_dependencies.py` - Dependency analysis
- `detect_dead_code.py` - Dead code detection

### 🛠️ Utilities
- `scaffold_feature.py` - Feature scaffolding
- `generate_unit_tests.py` - Test generation
- `extract_api_contract.py` - OpenAPI extraction
- `update_progress.py` - Progress tracking
- `generate_quality_report.py` - Aggregate quality score
