#!/usr/bin/env python3
import os
import sys
import glob
import re
import argparse
from pathlib import Path

def extract_wp_id_from_srs(srs_path):
    """
    Attempts to extract the Parent Work Package ID from the SRS file.
    """
    try:
        with open(srs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r'\*   \*\*Parent Work Package\*\*: (WP-\d+)', content)
        return match.group(1) if match else "WP-TBD"
    except:
        return "WP-TBD"

def create_detail_plan_template(module_name, srs_path, wp_id="WP-TBD"):
    return f"""# Detail Implementation Plan: {module_name}

## Source Documents
*   **SRS**: {srs_path}
*   **Master Plan Reference**: {wp_id}
*   **Architecture**: project-documentation/ARCHITECTURE_SPEC.md

## ⚠️ The 2-Hour Atomic Rule
**Constraint**: Every single task below MUST be executable in **2 hours or less**.
If a task seems larger, **Break It Down** into sub-tasks (Part 1, Part 2, etc.).

## 1. Development Sequence

### Feature Set 1: [Name from SRS]

- [ ] `TASK-{module_name[:3].upper()}-001`: **[Action]** [Component/Function]
    - **Detail**: Implement [Specific Logic] handling [Inputs].
    - **Parent Work Package**: {wp_id}
    - **Dependencies**: None
    - **Est. Time**: 1.5h
    - **Verification**: Unit Test passes

- [ ] `TASK-{module_name[:3].upper()}-002`: **[Action]** [Component/Function]
    - **Detail**: Handle Edge Case [X].
    - **Parent Work Package**: {wp_id}
    - **Dependencies**: TASK-{module_name[:3].upper()}-001
    - **Est. Time**: 1h
    - **Verification**: Test Case X passes

### Feature Set 2: [Name from SRS]

- [ ] `TASK-{module_name[:3].upper()}-003`: ...

## 2. Integration & Verification

### 2.1 Integration Steps
1.  Step 1...
2.  Step 2...

### 2.2 Acceptance Checklist
- [ ] Feature 1 works as defined in SRS 3.1
- [ ] Feature 2 works as defined in SRS 3.2
"""

def main():
    parser = argparse.ArgumentParser(description="Generate Detail Plan skeletons from SRS")
    parser.add_argument("--srs_dir", default="project-documentation/srs", help="Directory containing SRS files")
    parser.add_argument("--output", default="project-documentation/plans", help="Output directory")
    args = parser.parse_args()

    srs_dir = Path(args.srs_dir)
    if not srs_dir.exists():
        print(f"❌ SRS directory not found at {srs_dir}")
        print("   Did you run 'generate_srs.py' first?")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    srs_files = list(srs_dir.glob("SRS_*.md"))
    
    if not srs_files:
        print("⚠️ No SRS files found.")
        sys.exit(0)

    print(f"📝 Found {len(srs_files)} SRS files. Generating Detail Plans...")

    for srs_file in srs_files:
        # Extract module name from "SRS_ModuleName.md"
        module_name = srs_file.stem.replace("SRS_", "")
        target_file = output_dir / f"DETAIL_PLAN_{module_name}.md"
        
        if not target_file.exists():
            wp_id = extract_wp_id_from_srs(srs_file)
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(create_detail_plan_template(module_name, str(srs_file), wp_id))
            print(f"   ✅ Created {target_file} (Linked to {wp_id})")
        else:
            print(f"   ⚠️  Skipped {target_file} (Already exists)")

    print("\n✅ Detail Plan Scaffolding Complete.")
    print(f"📂 Output location: {output_dir}/")
    print("👉 Use the Orchestrator to fill these plans adhering to the 2-Hour Rule.")

if __name__ == "__main__":
    main()
