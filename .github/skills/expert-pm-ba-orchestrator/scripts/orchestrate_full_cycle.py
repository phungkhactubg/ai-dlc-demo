import os
import sys
import subprocess
import argparse
import io

# Fix for Windows console encoding issues
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

def run_command(command):
    print(f"🚀 Running: {' '.join(command)}")
    # Force UTF-8 encoding for subprocess communication
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', env=env)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False, result.stderr
    print(result.stdout)
    return True, result.stdout

def orchestrate_full_cycle(input_req, project_name):
    script_dir = os.path.dirname(__file__)
    # Enable auto-naming for sub-scripts
    os.environ["SDLC_AUTO"] = "true"
    
    # 0. Input Pre-processing & Project Detection
    req_file = None
    req_text = None
    if os.path.exists(input_req):
        req_file = input_req
        print(f"📄 Using requirement file: {req_file}")
    else:
        req_text = input_req
        print(f"✍️  Using direct text requirements.")

    # Heuristic for project mode
    is_existing = any(os.path.exists(f) for f in ["go.mod", "package.json", "apps", "features", "OVERVIEW.md"])
    mode = "EXISTING" if is_existing else "NEW"
    os.environ["SDLC_MODE"] = mode
    
    print(f"🎬 Starting Autonomous SDLC for: {project_name} (Mode: {mode})")
    
    # Check for existing work (Resume Capability)
    has_prd = os.path.exists("PRD.md")
    has_arch = os.path.exists("ARCHITECTURE_SPEC.md")
    has_plan = os.path.exists("MASTER_PLAN.md")
    
    # 1. Initialize & PRD
    if not has_prd:
        print("\n--- Phase 1: Ingestion & PRD Generation ---")
        init_cmd = [sys.executable, os.path.join(script_dir, "initialize_project.py"), project_name]
        prd_cmd = [sys.executable, os.path.join(script_dir, "generate_prd.py"), project_name]
        
        if req_file:
            init_cmd += ["--req-file", req_file]
            prd_cmd += ["--req-file", req_file]
        else:
            init_cmd += ["--req-text", req_text]
            prd_cmd += ["--req-text", req_text]
            
        success, _ = run_command(init_cmd)
        if not success: return
        
        # Refine PRD with categorized injection
        success, _ = run_command(prd_cmd)
        if not success: return
    else:
        print("\n⏭️  Skipping Phase 1: PRD.md already exists.")

    # 2. Validate PRD
    print("\n--- Phase 1.5: PRD Validation ---")
    success, _ = run_command([sys.executable, os.path.join(script_dir, "validate_prd.py"), "PRD.md"])
    if not success:
        print("⚠️  PRD validation failed. Please review PRD.md and fix inconsistencies before proceeding.")
        return

    # 3. Architecture Spec (Instruction)
    if not has_arch:
        print("\n--- Phase 2: Architecture Spec ---")
        if mode == "NEW":
            print("🤖 ACTION REQUIRED: Please ask the Expert Solutions Architect (expert-solutions-architect) to:")
            print(f"   'Generate a NEW system ARCHITECTURE_SPEC.md for {project_name} based on PRD.md'")
        else:
            print("🤖 ACTION REQUIRED: Please ask the Expert Solutions Architect (expert-solutions-architect) to:")
            print(f"   'Analyze existing codebase and Update ARCHITECTURE_SPEC.md for {project_name} based on new PRD.md'")
        print("   Once ARCHITECTURE_SPEC.md is created/updated, run this command again to proceed.")
        return
    else:
        print("\n⏭️  Phase 2: ARCHITECTURE_SPEC.md found.")

    # 4. Master Plan Generation
    if not has_plan:
        print("\n--- Phase 3: Master Plan Generation ---")
        success, _ = run_command([sys.executable, os.path.join(script_dir, "generate_master_plan.py"), project_name])
        if not success: return
    else:
        print("\n⏭️  Phase 3: MASTER_PLAN.md found.")

    # 5. Task Spec Generation
    print("\n--- Phase 4: Initial Task Specs ---")
    # Detect if TASK-001 exists
    task_dir = "tasks"
    if not os.path.exists(task_dir): os.makedirs(task_dir)
    
    if not any(f.startswith("TASK-001") for f in os.listdir(task_dir) if os.path.isfile(os.path.join(task_dir, f))):
        task_name = "Foundation & Infrastructure Setup" if mode == "NEW" else f"Impact Analysis & Integration for {project_name}"
        success, _ = run_command([sys.executable, os.path.join(script_dir, "generate_task_spec.py"), "TASK-001", task_name])
    else:
        print("⏭️  TASK-001 already exists in /tasks folder.")

    print(f"\n✅ SDLC Orchestration for {mode} project is up-to-date.")
    print("🚀 Next Steps: Call specialized developer agents to implement the tasks in the /tasks directory.")

def main():
    parser = argparse.ArgumentParser(description="Orchestrate full SDLC cycle from requirements")
    parser.add_argument("input_req", help="Path to the requirements file OR raw requirements text")
    parser.add_argument("--name", default="MyFeature", help="Name of the project/feature")
    args = parser.parse_args()
    
    orchestrate_full_cycle(args.input_req, args.name)

if __name__ == "__main__":
    main()
