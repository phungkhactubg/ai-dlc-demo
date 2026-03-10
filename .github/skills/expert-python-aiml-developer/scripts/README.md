# Expert Python AI/ML Developer - Scripts

This folder contains utility scripts to automate common Python AI/ML development tasks following the Expert Python AI/ML Developer skill guidelines.

## Available Scripts

### 1. `scaffold_project.py`
**Purpose:** Scaffold a complete ML project with all directories and boilerplate files.

```bash
# Usage
python scaffold_project.py <project_name>

# Example
python scaffold_project.py image_classifier
python scaffold_project.py sentiment_analyzer
```

**Output:** Creates a complete project structure:
```
<project_name>/
├── pyproject.toml
├── requirements.txt
├── README.md
├── .env.example
├── configs/
│   ├── model_config.yaml
│   ├── training_config.yaml
│   └── inference_config.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   ├── features/
│   └── external/
├── models/
│   ├── checkpoints/
│   └── production/
├── src/
│   ├── __init__.py
│   ├── config/
│   ├── data/
│   ├── features/
│   ├── models/
│   ├── training/
│   ├── inference/
│   ├── agents/
│   ├── api/
│   └── utils/
├── notebooks/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── scripts/
└── Dockerfile
```

---

### 2. `validate_production_ready.py` ⚠️ MANDATORY
**Purpose:** Validate that code is production-ready with NO TODOs, placeholders, or missing documentation.

**THIS SCRIPT MUST BE RUN BEFORE MARKING ANY TASK COMPLETE.**

```bash
# Validate the src directory
python validate_production_ready.py src/

# Strict mode (additional checks)
python validate_production_ready.py src/ --strict

# JSON output for CI/CD
python validate_production_ready.py src/ --json
```

**Checks performed:**
- 🚨 **CRITICAL**: TODOs, FIXMEs, XXX, HACK comments
- 🚨 **CRITICAL**: Placeholder/stub comments
- 🚨 **CRITICAL**: Empty function bodies (`pass` statements)
- 🚨 **CRITICAL**: Hardcoded secrets/API keys
- ❌ **ERROR**: Missing type hints
- ❌ **ERROR**: Missing docstrings
- ❌ **ERROR**: Print statements (should use logging)
- ❌ **ERROR**: Bare exception handling
- ⚠️ **WARNING**: Magic numbers without constants
- ⚠️ **WARNING**: Very short function bodies

**Exit codes:**
- `0`: All checks passed
- `1`: Errors found
- `2`: Critical violations found (blocking)

---

### 3. `validate_type_hints.py` 🆕
**Purpose:** Check for missing type annotations in Python code.

```bash
# Validate a directory
python validate_type_hints.py src/

# Include return type checks
python validate_type_hints.py src/ --check-returns

# JSON output
python validate_type_hints.py src/ --json
```

**Checks performed:**
- 🚨 **CRITICAL**: Functions without parameter type hints
- 🚨 **CRITICAL**: Functions without return type hints
- ⚠️ **WARNING**: Variables without type annotations in complex cases
- ⚠️ **WARNING**: Generic `Any` type usage

**Exit codes:**
- `0`: All functions have type hints
- `1`: Missing type hints found
- `2`: Critical violations (public API without types)

---

### 4. `validate_security.py` 🔒 SECURITY SCANNER
**Purpose:** Detect common security vulnerabilities in Python ML code.

```bash
python validate_security.py src/
python validate_security.py src/ --strict
python validate_security.py src/ --json
```

**Checks performed:**
- 🔴 **Hardcoded Secrets**: API keys, passwords, tokens
- 🔴 **Pickle Loading**: `pickle.load` without safe_load
- 🔴 **Unsafe Deserialization**: `torch.load` without `weights_only=True`
- 🟠 **Eval Usage**: `eval()` and `exec()` calls
- 🟠 **subprocess Calls**: Shell injection risks
- 🟠 **Path Traversal**: Unsanitized file paths
- 🟡 **HTTP without TLS**: Unencrypted connections
- 🟡 **Debug Mode**: Flask/FastAPI debug=True in production

---

### 5. `analyze_code_quality.py` 📊 CODE QUALITY
**Purpose:** Run comprehensive code quality checks.

```bash
python analyze_code_quality.py src/
python analyze_code_quality.py src/ --fix  # Auto-fix where possible
python analyze_code_quality.py src/ --full-report
```

**Checks performed:**
- **PEP 8 Compliance**: Style guide violations
- **Complexity**: Cyclomatic complexity per function
- **Dead Code**: Unused imports, variables, functions
- **Duplication**: Repeated code blocks
- **Magic Numbers**: Hardcoded values without constants

**Output:**
- Overall code quality score (0-100)
- Issue breakdown by category
- Suggestions for improvement

---

### 6. `validate_model_reproducibility.py` 🔄 REPRODUCIBILITY
**Purpose:** Check for reproducibility best practices in ML code.

```bash
python validate_model_reproducibility.py src/
python validate_model_reproducibility.py src/ --strict
python validate_model_reproducibility.py src/ --json
```

**Checks performed:**
- 🔴 **Missing Seed Setting**: No `random.seed()`, `np.random.seed()`, `torch.manual_seed()`
- 🔴 **Non-deterministic Operations**: Operations that may vary across runs
- 🟠 **Missing CUDA Seed**: `torch.cuda.manual_seed_all()` not called
- 🟠 **CuDNN Benchmark Enabled**: May cause non-determinism
- 🟡 **Missing Environment Logging**: Version tracking not implemented

---

### 7. `validate_data_pipeline.py` 📊 DATA VALIDATION
**Purpose:** Validate data processing pipelines and schemas.

```bash
python validate_data_pipeline.py src/data/
python validate_data_pipeline.py src/data/ --check-schemas
python validate_data_pipeline.py src/data/ --json
```

**Checks performed:**
- **Schema Definitions**: Pandera/Pydantic schemas present
- **Validation Calls**: Data validated at boundaries
- **Error Handling**: Data loading errors handled
- **Null Handling**: Missing value strategies defined
- **Type Casting**: Explicit dtype conversions

---

### 8. `generate_api_schema.py` 📋 API SCHEMA GENERATOR
**Purpose:** Generate OpenAPI schema from FastAPI applications.

```bash
python generate_api_schema.py src/api/main.py
python generate_api_schema.py src/api/main.py --output openapi.json
python generate_api_schema.py src/api/main.py --format yaml
```

**Output:**
- OpenAPI 3.0 specification (JSON/YAML)
- TypeScript interfaces (optional)
- Request/Response examples

---

### 9. `generate_quality_report.py` 📊 QUALITY REPORT
**Purpose:** Run ALL validation scripts and generate a comprehensive quality score.

```bash
python generate_quality_report.py src/
python generate_quality_report.py src/ --html report.html
python generate_quality_report.py src/ --json
```

**Features:**
- Runs all validators automatically
- Calculates overall quality score (0-100)
- Generates HTML/JSON reports
- Perfect for CI/CD integration

**Quality Score Breakdown:**
- Type hints coverage: 25%
- Docstring coverage: 15%
- Error handling: 20%
- Security: 15%
- Reproducibility: 10%
- Code quality (linting): 15%

---

### 10. `scaffold_model.py` 🏗️ MODEL SCAFFOLDER
**Purpose:** Generate model architecture boilerplate.

```bash
python scaffold_model.py --type transformer --name MyTransformer
python scaffold_model.py --type cnn --name ImageClassifier
python scaffold_model.py --type mlp --name Regressor
```

**Supported model types:**
- `transformer`: Transformer architecture
- `cnn`: Convolutional neural network
- `rnn`: Recurrent neural network
- `mlp`: Multi-layer perceptron
- `autoencoder`: Autoencoder architecture

---

### 11. `scaffold_agent.py` 🤖 AGENT SCAFFOLDER
**Purpose:** Generate LangChain/LlamaIndex agent boilerplate.

```bash
python scaffold_agent.py --type react --name ResearchAgent
python scaffold_agent.py --type rag --name DocumentQA
python scaffold_agent.py --type tool-use --name DataAnalyst
```

**Supported agent types:**
- `react`: ReAct agent pattern
- `rag`: RAG-based QA agent
- `tool-use`: Tool-calling agent
- `multi-agent`: Multi-agent system

---

### 12. `validate_notebook.py` 📓 NOTEBOOK VALIDATOR
**Purpose:** Validate Jupyter notebooks for production readiness.

```bash
python validate_notebook.py notebooks/
python validate_notebook.py notebooks/01_exploration.ipynb
python validate_notebook.py notebooks/ --convert-to-script
```

**Checks performed:**
- Cell execution order
- Cleared outputs (for git)
- Magic commands usage
- Import statements at top
- No hardcoded paths

---

### 13. `validate_cv_pipeline.py` 🖼️ COMPUTER VISION VALIDATOR
**Purpose:** Validate Computer Vision code for best practices.

```bash
python validate_cv_pipeline.py src/
python validate_cv_pipeline.py src/ --strict
python validate_cv_pipeline.py src/ --json
```

**Checks performed:**
- 🚨 **CRITICAL**: Random augmentation on validation/test data
- ⚠️ **COLOR_SPACE**: cv2.imread() without BGR to RGB conversion
- ⚠️ **NORMALIZATION**: Generic `[0.5, 0.5, 0.5]` instead of ImageNet values
- ℹ️ **LIBRARY_MIX**: Mixing OpenCV and PIL for image loading
- ℹ️ **HARDCODED_SIZE**: Hardcoded image sizes in resize operations

**Best Practices Checked:**
- Proper color space handling (BGR vs RGB)
- Dataset-specific normalization (ImageNet, CIFAR, etc.)
- Augmentation only applied to training data
- Inference mode usage for prediction
- Consistent image loading library usage

---

## Quick Start Workflow

1. **Create a new ML project:**
   ```bash
   cd c:\Developer\GitHub\av-platform
   python .github/skills/expert-python-aiml-developer/scripts/scaffold_project.py my_project
   ```

2. **Implement your model and training logic**

3. **Run ALL validation scripts (MANDATORY):**
   ```bash
   # Option A: ONE-STOP QUALITY CHECK (RECOMMENDED)
   python .github/skills/expert-python-aiml-developer/scripts/generate_quality_report.py src/

   # Option B: Individual checks
   python .github/skills/expert-python-aiml-developer/scripts/validate_production_ready.py src/
   python .github/skills/expert-python-aiml-developer/scripts/validate_type_hints.py src/
   python .github/skills/expert-python-aiml-developer/scripts/validate_security.py src/
   python .github/skills/expert-python-aiml-developer/scripts/validate_model_reproducibility.py src/
   python .github/skills/expert-python-aiml-developer/scripts/analyze_code_quality.py src/
   ```

4. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

5. **Run type checker:**
   ```bash
   mypy src/
   ```

6. **Run linter:**
   ```bash
   ruff check src/
   ```

---

## Requirements

- Python 3.10+
- Standard library only (no external dependencies for scripts)

## Optional Dependencies (for enhanced functionality)

```bash
# For code quality analysis
pip install ruff mypy black

# For notebook validation
pip install nbformat nbconvert

# For API schema generation
pip install fastapi pydantic
```
