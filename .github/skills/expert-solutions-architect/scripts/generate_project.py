#!/usr/bin/env python3
"""
Go Project Generator
====================

Generate a complete Go project skeleton with lib drivers.

Usage:
    python generate_project.py my_project --output-dir ./projects
    python generate_project.py my_api --module github.com/company/my_api
"""

import argparse
import os
import shutil
import sys
from pathlib import Path


def get_script_dir() -> Path:
    """Get the directory containing this script."""
    return Path(__file__).parent.absolute()


def get_skeleton_dir() -> Path:
    """Get the skeleton directory."""
    return get_script_dir().parent / "skeleton" / "go-project"


def to_module_name(project_name: str, prefix: str = "") -> str:
    """Convert project name to Go module name."""
    name = project_name.lower().replace("-", "_").replace(" ", "_")
    if prefix:
        return f"{prefix}/{name}"
    return name


def process_template(content: str, replacements: dict) -> str:
    """Replace template variables in content."""
    for key, value in replacements.items():
        content = content.replace(f"{{{{.{key}}}}}", value)
    return content


def copy_and_process(src: Path, dest: Path, replacements: dict, dry_run: bool = False):
    """Copy files and process templates."""
    if src.is_file():
        # Read content
        try:
            with open(src, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Binary file, just copy
            if not dry_run:
                shutil.copy2(src, dest)
            print(f"  📄 {dest.name}")
            return

        # Process templates
        if src.suffix == ".tmpl":
            content = process_template(content, replacements)
            dest = dest.with_suffix("")  # Remove .tmpl extension
        elif src.suffix in [".go", ".yaml", ".yml", ".md"]:
            content = process_template(content, replacements)

        # Write
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)
        print(f"  ✅ {dest.name}")

    elif src.is_dir():
        if not dry_run:
            dest.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            copy_and_process(item, dest / item.name, replacements, dry_run)


def generate_project(
    project_name: str,
    output_dir: str,
    module_prefix: str = "",
    dry_run: bool = False
):
    """Generate a new Go project."""
    skeleton_dir = get_skeleton_dir()
    if not skeleton_dir.exists():
        print(f"❌ Skeleton directory not found: {skeleton_dir}")
        sys.exit(1)

    output_path = Path(output_dir) / project_name
    if output_path.exists() and not dry_run:
        print(f"❌ Directory already exists: {output_path}")
        sys.exit(1)

    module_name = to_module_name(project_name, module_prefix)

    replacements = {
        "ModuleName": module_name,
        "ProjectName": project_name,
    }

    print(f"\n🚀 Generating project: {project_name}")
    print(f"   Module: {module_name}")
    print(f"   Output: {output_path}\n")

    if dry_run:
        print("   (Dry run - no files will be created)\n")

    # Copy skeleton
    copy_and_process(skeleton_dir, output_path, replacements, dry_run)

    # Create additional directories
    extra_dirs = [
        "docs",
        "features",
        "static",
    ]
    for dir_name in extra_dirs:
        dir_path = output_path / dir_name
        if not dry_run:
            dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  📁 {dir_name}/")

    # Create .gitignore
    gitignore_content = """# Binaries
*.exe
*.exe~
*.dll
*.so
*.dylib
bin/

# Test files
*.test
coverage.out
coverage.html

# IDE
.idea/
.vscode/
*.swp
*.swo

# Env files
.env
.env.local
*.local.yaml

# Build
dist/
build/

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
"""
    gitignore_path = output_path / ".gitignore"
    if not dry_run:
        with open(gitignore_path, "w") as f:
            f.write(gitignore_content)
    print(f"  ✅ .gitignore")

    # Create README
    readme_content = f"""# {project_name}

## Getting Started

### Prerequisites
- Go 1.25+
- Docker & Docker Compose
- MongoDB
- Redis

### Setup

```bash
# Install dependencies
go mod tidy

# Start services
docker-compose up -d

# Run application
go run main.go
```

### API

- Health Check: `GET /health`
- Readiness: `GET /ready`

### Project Structure

```
{project_name}/
├── config/         # Configuration
├── middleware/     # HTTP middleware
├── routers/        # Route definitions
├── utils/          # Utilities
├── lib/            # Driver libraries
│   ├── mongodb/
│   ├── redis/
│   ├── nats/
│   ├── kafka/
│   ├── mqtt/
│   ├── s3/
│   └── postgres/
├── features/       # Feature modules
└── main.go         # Entry point
```

### Development

```bash
# Run with hot reload (install air first)
air

# Build
go build -o bin/{project_name} .
```
"""
    readme_path = output_path / "README.md"
    if not dry_run:
        with open(readme_path, "w") as f:
            f.write(readme_content)
    print(f"  ✅ README.md")

    # Create docker-compose
    docker_compose_content = """version: '3.8'

services:
  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  nats:
    image: nats:2-alpine
    ports:
      - "4222:4222"
      - "8222:8222"
    command: ["--js"]

  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

volumes:
  mongodb_data:
  minio_data:
"""
    dc_path = output_path / "docker-compose.yml"
    if not dry_run:
        with open(dc_path, "w") as f:
            f.write(docker_compose_content)
    print(f"  ✅ docker-compose.yml")

    print(f"\n✅ Project '{project_name}' generated successfully!")
    print(f"\nNext steps:")
    print(f"  cd {output_path}")
    print(f"  go mod tidy")
    print(f"  docker-compose up -d")
    print(f"  go run main.go")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a Go project skeleton"
    )
    parser.add_argument(
        "project_name",
        help="Name of the project"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=".",
        help="Output directory (default: current directory)"
    )
    parser.add_argument(
        "--module", "-m",
        default="",
        help="Go module prefix (e.g., github.com/company)"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be created without actually creating"
    )

    args = parser.parse_args()
    generate_project(
        args.project_name,
        args.output_dir,
        args.module,
        args.dry_run
    )


if __name__ == "__main__":
    main()
