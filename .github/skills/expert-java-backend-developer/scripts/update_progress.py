#!/usr/bin/env python3
"""
update_progress.py

Track and update implementation progress for Java backend features.
Maintains a PROGRESS.md file with completion status.

Usage:
    python update_progress.py <path> [--status STATUS] [--note NOTE]
    python update_progress.py src/main/java/com/example/notifications --status in-progress
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class FeatureStatus:
    name: str
    path: str
    status: str  # pending, in-progress, completed, blocked
    progress: int  # 0-100
    components: Dict[str, bool] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    last_updated: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "status": self.status,
            "progress": self.progress,
            "components": self.components,
            "notes": self.notes,
            "last_updated": self.last_updated
        }


class ProgressTracker:
    """Tracks implementation progress for Java features."""

    REQUIRED_COMPONENTS = [
        "model",
        "repository",
        "service_interface",
        "service_impl",
        "controller",
        "exception",
        "config",
        "tests"
    ]

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.progress_file = self.base_path / "PROGRESS.md"

    def analyze_feature(self) -> FeatureStatus:
        """Analyze a feature directory and determine its status."""
        feature_name = self.base_path.name
        java_path = self.base_path / "src/main/java"
        test_path = self.base_path / "src/test/java"

        # Determine package structure
        packages = self._find_packages(java_path)

        status = FeatureStatus(
            name=feature_name,
            path=str(self.base_path),
            status="pending",
            progress=0,
            components={},
            notes=[],
            last_updated=datetime.now().isoformat()
        )

        # Check for required components
        for component in self.REQUIRED_COMPONENTS:
            status.components[component] = self._has_component(component, java_path, test_path, packages)

        # Calculate progress
        completed = sum(1 for has in status.components.values() if has)
        status.progress = int((completed / len(self.REQUIRED_COMPONENTS)) * 100)

        # Determine status
        if status.progress == 100:
            status.status = "completed"
        elif status.progress > 0:
            status.status = "in-progress"

        # Add notes based on what's missing
        missing = [c for c, has in status.components.items() if not has]
        if missing:
            status.notes.append(f"Missing components: {', '.join(missing)}")

        # Check for quality issues
        status.notes.extend(self._check_quality(java_path))

        return status

    def _find_packages(self, java_path: Path) -> List[str]:
        """Find all packages in the Java source directory."""
        packages = []

        if not java_path.exists():
            return packages

        for item in java_path.rglob("*"):
            if item.is_dir():
                # Check if it contains Java files
                java_files = list(item.glob("*.java"))
                if java_files:
                    rel_path = item.relative_to(java_path)
                    package = str(rel_path).replace(os.sep, '.')
                    packages.append(package)

        return packages

    def _has_component(self, component: str, java_path: Path,
                       test_path: Path, packages: List[str]) -> bool:
        """Check if a required component exists."""
        if not java_path.exists():
            return False

        package_name = self.base_path.name.lower()

        if component == "model":
            return self._has_files_with_suffix(java_path, package_name, "Entity.java") or \
                   self._has_files_with_suffix(java_path, package_name, "Request.java") or \
                   self._has_files_with_suffix(java_path, package_name, "Response.java")

        elif component == "repository":
            return self._has_files_with_suffix(java_path, package_name, "Repository.java")

        elif component == "service_interface":
            return any(f.name.endswith("Service.java") and "Impl" not in f.name
                      for f in java_path.rglob("*.java"))

        elif component == "service_impl":
            return any("Impl" in f.name and f.name.endswith("Service.java")
                      for f in java_path.rglob("*.java"))

        elif component == "controller":
            return any("Controller" in f.name for f in java_path.rglob("*.java"))

        elif component == "exception":
            return self._has_files_with_suffix(java_path, package_name, "Exception.java")

        elif component == "config":
            return any("Config" in f.name or "ExceptionHandler" in f.name
                      for f in java_path.rglob("*.java"))

        elif component == "tests":
            if not test_path.exists():
                return False
            test_files = list(test_path.rglob("*Test.java"))
            return len(test_files) > 0

        return False

    def _has_files_with_suffix(self, java_path: Path, package: str, suffix: str) -> bool:
        """Check if files with specific suffix exist."""
        for f in java_path.rglob("*.java"):
            if package in str(f).lower() and f.name.endswith(suffix):
                return True
        return False

    def _check_quality(self, java_path: Path) -> List[str]:
        """Check for quality issues."""
        notes = []

        if not java_path.exists():
            return notes

        # Check for TODOs
        for java_file in java_path.rglob("*.java"):
            try:
                with open(java_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'TODO' in content:
                    notes.append(f"Contains TODOs (e.g., {java_file.name})")
                    break

                if 'FIXME' in content:
                    notes.append(f"Contains FIXMEs (e.g., {java_file.name})")
                    break

            except:
                pass

        return notes

    def update_progress_file(self, status: FeatureStatus) -> None:
        """Update the PROGRESS.md file."""
        existing_data = self._load_progress_file()

        # Update or add this feature
        existing_data[status.name] = status.to_dict()

        # Write updated file
        self._write_progress_file(existing_data)

    def _load_progress_file(self) -> Dict[str, Any]:
        """Load existing progress file."""
        if not self.progress_file.exists():
            return {}

        try:
            with open(self.progress_file, 'r') as f:
                content = f.read()

            # Try to parse JSON data embedded in markdown
            match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except:
            pass

        return {}

    def _write_progress_file(self, data: Dict[str, Any]) -> None:
        """Write progress file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Implementation Progress

Last updated: {timestamp}

## Feature Status Summary

| Feature | Status | Progress | Components |
|---------|--------|----------|------------|
"""

        for name, status_data in data.items():
            status_emoji = {
                "completed": "✅",
                "in-progress": "🔄",
                "pending": "⏳",
                "blocked": "🚫"
            }.get(status_data.get("status", "pending"), "⏳")

            components = status_data.get("components", {})
            completed = sum(1 for v in components.values() if v)
            total = len(components) if components else 1

            content += f"| {name} | {status_emoji} {status_data.get('status', 'pending')} | {status_data.get('progress', 0)}% | {completed}/{total} |\n"

        content += "\n## Detailed Status\n\n"

        for name, status_data in data.items():
            content += f"### {name}\n\n"
            content += f"- **Status**: {status_data.get('status', 'pending')}\n"
            content += f"- **Progress**: {status_data.get('progress', 0)}%\n"
            content += f"- **Last Updated**: {status_data.get('last_updated', 'N/A')}\n\n"

            components = status_data.get("components", {})
            if components:
                content += "**Components:**\n"
                for comp, has in components.items():
                    emoji = "✅" if has else "❌"
                    content += f"- {emoji} {comp}\n"
                content += "\n"

            notes = status_data.get("notes", [])
            if notes:
                content += "**Notes:**\n"
                for note in notes:
                    content += f"- {note}\n"
                content += "\n"

        content += "\n## Raw Data\n\n```json\n"
        content += json.dumps(data, indent=2)
        content += "\n```\n"

        self.progress_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.progress_file, 'w') as f:
            f.write(content)

        print(f"📄 Updated: {self.progress_file}")


def print_status(status: FeatureStatus) -> None:
    """Print feature status to console."""
    print("\n" + "=" * 60)
    print(f"FEATURE STATUS: {status.name.upper()}")
    print("=" * 60)

    status_emoji = {
        "completed": "✅",
        "in-progress": "🔄",
        "pending": "⏳",
        "blocked": "🚫"
    }.get(status.status, "⏳")

    print(f"\nStatus: {status_emoji} {status.status}")
    print(f"Progress: {status.progress}%")

    print("\nComponents:")
    for component, has in status.components.items():
        emoji = "✅" if has else "❌"
        print(f"  {emoji} {component}")

    if status.notes:
        print("\nNotes:")
        for note in status.notes:
            print(f"  • {note}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Track and update implementation progress for Java features"
    )
    parser.add_argument("path", help="Path to feature directory")
    parser.add_argument("--status", "-s",
                        choices=["pending", "in-progress", "completed", "blocked"],
                        help="Override status")
    parser.add_argument("--note", "-n", help="Add a note")
    parser.add_argument("--no-update", action="store_true",
                        help="Don't update PROGRESS.md file")

    args = parser.parse_args()

    tracker = ProgressTracker(args.path)
    status = tracker.analyze_feature()

    # Override status if specified
    if args.status:
        status.status = args.status

    # Add note if specified
    if args.note:
        status.notes.append(args.note)

    # Update progress file
    if not args.no_update:
        tracker.update_progress_file(status)

    # Print status
    print_status(status)

    return 0


if __name__ == "__main__":
    sys.exit(main())
