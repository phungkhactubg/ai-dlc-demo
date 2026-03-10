#!/usr/bin/env python3
"""
Expert Java Backend Developer Skill Entry Point

This is the Python entry point for the expert-java-backend-developer skill.
While Claude Code primarily uses SKILL.md as the main interface,
this file provides additional functionality for Claude Desktop integration
and potential future extensions.
"""

import sys
import os
from pathlib import Path

def main():
    """Main entry point for the skill."""

    # Get the skill directory
    skill_dir = Path(__file__).parent
    skill_md = skill_dir / "SKILL.md"

    # Ensure SKILL.md exists
    if not skill_md.exists():
        print(f"ERROR: SKILL.md not found in {skill_dir}", file=sys.stderr)
        sys.exit(1)

    # Read skill metadata from SKILL.md frontmatter
    metadata = {}
    with open(skill_md, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract frontmatter (between --- markers)
    if content.startswith('---'):
        lines = content.split('\n')
        in_frontmatter = False
        frontmatter_lines = []

        for line in lines[1:]:
            if line.strip() == '---':
                break
            frontmatter_lines.append(line)

        # Parse frontmatter
        try:
            import yaml
            metadata = yaml.safe_load('\n'.join(frontmatter_lines)) or {}
        except:
            # Fallback to simple parsing
            for line in frontmatter_lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()

    # Print skill info (for debugging)
    print(f"Skill Name: {metadata.get('name', 'Unknown')}")
    print(f"Description: {metadata.get('description', 'No description')}")
    print(f"Skill Directory: {skill_dir}")

    # This file can be extended with additional functionality
    # such as validation, preprocessing, or custom commands

    return 0

if __name__ == "__main__":
    sys.exit(main())
