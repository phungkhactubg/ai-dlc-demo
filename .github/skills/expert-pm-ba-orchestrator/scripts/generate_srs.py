#!/usr/bin/env python3
import os
import re
import sys
import argparse
from pathlib import Path

def parse_modules_from_prd(prd_path):
    """
    Parses the PRD to identify modules.
    Assumes modules are headers like "### 4.1 Module 1: Name"
    """
    modules = []
    try:
        with open(prd_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Regex to find modules (e.g., "### 4.1 Module 1: Vehicle Management System")
        # Adjust regex based on standard PRD template
        matches = re.findall(r'### \d+\.\d+ Module \d+: (.+)', content)
        if not matches:
             # Fallback: Try finding simple Level 3 headers if "Module" keyword missing
             matches = re.findall(r'### \d+\.\d+ (.+)', content)
        
        for m in matches:
            # Clean name for file usage
            clean_name = m.strip().replace(" ", "_").replace("&", "and").replace("/", "_")
            modules.append((m.strip(), clean_name))
            
    except Exception as e:
        print(f"Error reading PRD: {e}")
        
    return modules

def parse_modules_from_master_plan(plan_path):
    """
    Parses the Master Plan to identify Work Packages.
    Assumes packages are like "### 3.1 Module 1: Name" or contain "WP-XXX"
    """
    modules = []
    try:
        with open(plan_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Capture the entire line after the numbering
        matches = re.findall(r'### \d+\.\d+(?:[A-Z])?\s+(.+)', content)
        
        for m in matches:
            # m could be "WP-010: Authentication Service (SSC)" 
            # or "Module 1: Vehicle Management System"
            
            # 1. Extract WP-ID
            wp_id_match = re.search(r'WP-\d+', m)
            wp_id = wp_id_match.group(0) if wp_id_match else "WP-TBD"
            
            # 2. Extract Name (Clean up WP-ID, Module prefixes and trailing info)
            name = re.sub(r'(?:WP-\d+|Module \d+):\s*', '', m)
            name = re.split(r'\s*\(', name)[0].strip()
            
            # 3. Clean for filename
            clean_name = name.strip().replace(" ", "_").replace("&", "and").replace("/", "_").replace(":", "")
            
            modules.append((name, clean_name, wp_id))
            
    except Exception as e:
        print(f"Error reading Master Plan at {plan_path}: {e}")
        
    return modules

def create_srs_template(module_name, wp_id="WP-TBD"):
    return f"""# Software Requirements Specification (SRS): {module_name}

## 1. Introduction
*   **Module**: {module_name}
*   **Parent Work Package**: {wp_id}
*   **Source**: Derived from MASTER_PLAN.md and PRD.md

## 2. Functional Flow Diagrams
(Use Mermaid to visualize the happy path and error paths)
```mermaid
graph TD
    A[Start] --> B{{Decision}}
    B -->|Yes| C[Action]
    B -->|No| D[Error]
```

## 3. Detailed Requirement Specifications
(Decompose the PRD requirements into atomic functional units)

### 3.1 Feature: [Feature Name]
*   **Description**: [Detailed description]
*   **User Story**: As a [Role], I want to [Action], so that [Benefit].
*   **Pre-conditions**: [State required before start]
*   **Post-conditions**: [State after completion]

#### 3.1.1 Inputs & Validations
| Field | Type | Required | Validation Rules | Error Message |
|-------|------|----------|------------------|---------------|
| [Field] | String | Yes | Min 5 chars | "Too short" |

#### 3.1.2 Business Logic & Rules
1.  [Rule 1]: IF [Condition] THEN [Action]
2.  [Rule 2]: MUST [Requirement]

#### 3.1.3 Edge Cases & Error Handling
*   [Scenario 1]: [System Behavior]
*   [Scenario 2]: [System Behavior]

## 4. API & Data Interactions
*   **Read**: [Data Entities accessed]
*   **Write**: [Data Entities modified]
*   **Events Emitted**: [Events]

## 5. UI/UX Requirements (if applicable)
*   **Screen**: [Name]
*   **Elements**: [List of buttons, inputs]
*   **Interactions**: [Click flows]

"""

def main():
    parser = argparse.ArgumentParser(description="Generate SRS skeletons from PRD/Master Plan")
    parser.add_argument("--prd", default="project-documentation/PRD.md", help="Path to PRD")
    parser.add_argument("--master-plan", default=None, help="Path to Master Plan")
    parser.add_argument("--output", default="project-documentation/srs", help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.master_plan:
        plan_path = Path(args.master_plan)
        if not plan_path.exists():
            print(f"❌ Master Plan not found at {plan_path}")
            sys.exit(1)
        print(f"🔍 Analyzing Master Plan {plan_path} for work packages...")
        modules = parse_modules_from_master_plan(plan_path)
        if not modules:
             print(f"❌ FAILED to find any Work Packages in {plan_path}. Check your header formats (e.g., '### 3.1 WP-001: Name').")
             sys.exit(1)
    else:
        prd_path = Path(args.prd)
        if not prd_path.exists():
            print(f"❌ PRD not found at {prd_path}")
            sys.exit(1)
        print(f"🔍 Analyzing PRD {prd_path} for modules...")
        modules = [(name, clean, "WP-TBD") for name, clean in parse_modules_from_prd(prd_path)]

    if not modules:
        print("⚠️ No modules found. Check your search patterns.")
        # Create a generic one if parsing fails
        modules = [("Generic Module", "Generic_Module", "WP-TBD")]

    print(f"📝 Found {len(modules)} modules. Generating SRS scaffolds...")

    for human_name, file_name, wp_id in modules:
        target_file = output_dir / f"SRS_{file_name}.md"
        if not target_file.exists():
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(create_srs_template(human_name, wp_id))
            print(f"   ✅ Created {target_file} (Linked to {wp_id})")
        else:
            print(f"   ⚠️  Skipped {target_file} (Already exists)")

    print("\n✅ SRS Generation Complete.")
    print(f"📂 Output location: {output_dir}/")

if __name__ == "__main__":
    main()
