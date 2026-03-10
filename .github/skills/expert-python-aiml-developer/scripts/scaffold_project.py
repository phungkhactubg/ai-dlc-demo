#!/usr/bin/env python3
"""
Scaffold a complete ML project structure following best practices.

Usage:
    python scaffold_project.py <project_name>
    python scaffold_project.py my_classifier --path /projects
"""

import argparse
import sys
from pathlib import Path
from typing import Optional


# Directory structure
DIRECTORIES = [
    "configs",
    "data/raw", "data/processed", "data/features", "data/external",
    "models/checkpoints", "models/production",
    "src/config", "src/data", "src/features",
    "src/models/architectures", "src/training", "src/inference",
    "src/agents/tools", "src/agents/chains",
    "src/api/routes", "src/utils",
    "notebooks", "tests/unit", "tests/integration", "tests/e2e",
    "scripts", "logs",
]

PYTHON_PACKAGES = [
    "src", "src/config", "src/data", "src/features",
    "src/models", "src/models/architectures",
    "src/training", "src/inference",
    "src/agents", "src/agents/tools", "src/agents/chains",
    "src/api", "src/api/routes", "src/utils",
    "tests", "tests/unit", "tests/integration", "tests/e2e",
]

PYPROJECT_TOML = '''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "0.1.0"
description = "A production-ready ML project"
requires-python = ">=3.10"
dependencies = [
    "numpy>=1.24.0",
    "pandas>=2.0.0",
    "scikit-learn>=1.3.0",
    "torch>=2.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-dotenv>=1.0.0",
    "pyyaml>=6.0",
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.4.0", "mypy>=1.5.0", "ruff>=0.1.0", "black>=23.9.0"]

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W", "UP", "B"]

[tool.mypy]
python_version = "3.10"
strict = true
'''

GITIGNORE = '''__pycache__/
*.py[cod]
.venv/
venv/
.env
data/
models/
*.pt
*.pth
mlruns/
.coverage
.mypy_cache/
.ruff_cache/
'''

README_MD = '''# {name}

A production-ready ML project.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # or venv\\Scripts\\activate on Windows
pip install -e ".[dev]"
cp .env.example .env
```

## Usage

```bash
python scripts/train.py --config configs/training_config.yaml
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```
'''

ENV_EXAMPLE = '''APP_ENV=development
LOG_LEVEL=INFO
MODEL_PATH=models/production/model.pt
'''


def scaffold_project(name: str, base_path: Optional[Path] = None) -> Path:
    """Scaffold a complete ML project."""
    if base_path is None:
        base_path = Path.cwd()
    
    project_path = base_path / name
    
    if project_path.exists():
        raise FileExistsError(f"Directory already exists: {project_path}")
    
    print(f"Creating project: {name}")
    
    # Create directories
    for directory in DIRECTORIES:
        (project_path / directory).mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py files
    for package in PYTHON_PACKAGES:
        (project_path / package / "__init__.py").write_text('"""Package initialization."""\n')
    
    # Create project files
    (project_path / "pyproject.toml").write_text(PYPROJECT_TOML.format(name=name))
    (project_path / ".gitignore").write_text(GITIGNORE)
    (project_path / "README.md").write_text(README_MD.format(name=name))
    (project_path / ".env.example").write_text(ENV_EXAMPLE)
    
    # Create config files
    (project_path / "configs/training_config.yaml").write_text(
        "training:\n  seed: 42\n  epochs: 100\n  batch_size: 32\n  learning_rate: 0.0001\n"
    )
    
    print(f"\n✅ Project scaffolded: {project_path}")
    print(f"\nNext steps:")
    print(f"  cd {name}")
    print(f"  python -m venv venv")
    print(f"  pip install -e '.[dev]'")
    
    return project_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold ML project")
    parser.add_argument("project_name", help="Project name")
    parser.add_argument("--path", type=Path, help="Base path")
    
    args = parser.parse_args()
    
    try:
        scaffold_project(args.project_name, args.path)
    except FileExistsError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
