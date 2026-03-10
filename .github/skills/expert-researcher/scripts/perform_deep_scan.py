#!/usr/bin/env python3
import argparse
import sys
import os
import subprocess
import json
from pathlib import Path

def find_scanner_script():
    """
    Locate the scan_codebase.py script in the sibling codebase-scanner skill.
    Assumes standard structure: .github/skills/expert-researcher/scripts/../.. /codebase-scanner/scripts/scan_codebase.py
    """
    current_script_dir = Path(__file__).parent.resolve()
    # Go up to .github/skills
    skills_dir = current_script_dir.parent.parent
    scanner_path = skills_dir / "codebase-scanner" / "scripts" / "scan_codebase.py"
    
    if not scanner_path.exists():
        print(f"❌ Error: Could not locate codebase scanner at {scanner_path}")
        print("   Please ensure the 'codebase-scanner' skill is installed in .github/skills/")
        sys.exit(1)
        
    return scanner_path

def update_research_state(task_name, module_path):
    """
    Call research_iterative.py to log that this module has been scanned.
    """
    iterative_script = Path(__file__).parent / "research_iterative.py"
    if not iterative_script.exists():
        print("⚠️ Warning: Could not find research_iterative.py to update state.")
        return

    module_name = Path(module_path).name
    cmd = [
        sys.executable, str(iterative_script),
        task_name,
        "--scanned_module", module_name
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Research State updated: Marked '{module_name}' as scanned.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Failed to update research state: {e}")

def main():
    parser = argparse.ArgumentParser(description="Bridge: Execute Codebase Scanner and Log to Research State")
    parser.add_argument("task_name", help="Name of the current research task")
    parser.add_argument("module_path", help="Local path to the module/repository to scan")
    parser.add_argument("--output_dir", default="project-documentation/research", help="Root directory for research output")
    
    args = parser.parse_args()
    
    # Intelligent Path Resolution
    input_path = Path(args.module_path)
    
    # Case 1: Full path provided (and exists)
    if input_path.exists():
        target_path = input_path.resolve()
        
    # Case 2: Just a repo name provided (look in standard repos dir)
    else:
        standard_repo_path = Path("project-documentation/repos") / args.module_path
        if standard_repo_path.exists():
            target_path = standard_repo_path.resolve()
        else:
            print(f"❌ Error: Could not find module at '{input_path}' OR '{standard_repo_path}'")
            print("   Did you run 'scripts/clone_repo.py' first?")
            sys.exit(1)

    # 1. Locate Scanner
    scanner_script = find_scanner_script()
    print(f"🔍 Found Codebase Scanner: {scanner_script}")
    
    # 2. Prepare Output Path
    # Save output to project-documentation/research/<task>/scans/<module_name>
    task_slug = args.task_name.lower().replace(" ", "_")
    output_base = Path(args.output_dir) / task_slug / "scans" / target_path.name
    output_base.mkdir(parents=True, exist_ok=True)
    
    print(f"📂 Scanning '{target_path.name}'...")
    print(f"   -> Source: {target_path}")
    print(f"   -> Output: {output_base}")

    # 3. Execute Scanner
    # Usage: scan_codebase.py <path> --output <dir> --format markdown
    cmd = [
        sys.executable, str(scanner_script),
        str(module_path),
        "--output", str(output_base),
        "--format", "markdown"
    ]
    
    try:
        # Stream output to console so user sees progress
        result = subprocess.run(cmd, check=True, text=True)
        if result.returncode == 0:
            print(f"✅ Scan Complete.")
            
            # 4. Update Research State
            update_research_state(args.task_name, str(module_path))
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Scanner failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
