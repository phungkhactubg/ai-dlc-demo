import os
import sys
import argparse
import datetime
import io

# Fix for Windows console encoding issues
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

def initialize_project(project_name, req_file=None, req_text=None):
    # Load requirements if provided
    req_content = ""
    if req_file and os.path.exists(req_file):
        with open(req_file, 'r', encoding='utf-8') as f:
            req_content = f.read()
            print(f"📖 Loaded requirements from {req_file}")
    elif req_text:
        req_content = req_text
        print(f"📖 Using requirements from provided text")

    # Ensure project-documentation directory exists
    docs_dir = "project-documentation"
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
        print(f"✅ Created {docs_dir} directory")

    # 1. Create OVERVIEW.md
    overview_tpl_path = os.path.join(os.path.dirname(__file__), "..", "templates", "OVERVIEW_TEMPLATE.md")
    target_overview = os.path.join(docs_dir, "OVERVIEW.md")
    if os.path.exists(overview_tpl_path) and not os.path.exists(target_overview):
        with open(overview_tpl_path, 'r', encoding='utf-8') as f:
            overview_content = f.read()
        
        overview_content = overview_content.replace("[Project/Feature Name]", project_name)
        overview_content = overview_content.replace("[YYYY-MM-DD HH:MM]", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        if req_content:
            source = f"`{req_file}`" if req_file else "direct prompt"
            overview_content += f"\n\n## 📄 Original Requirements Source\nLoaded from {source}"

        with open(target_overview, 'w', encoding='utf-8') as f:
            f.write(overview_content)
        print(f"✅ Created {target_overview}")
    else:
        print("⏭️  Skipping OVERVIEW.md: already exists or not in new project mode.")

    # 2. Create initial PRD.md
    prd_tpl_path = os.path.join(os.path.dirname(__file__), "..", "templates", "PRD_TEMPLATE.md")
    target_prd = os.path.join(docs_dir, "PRD.md")
    if os.path.exists(prd_tpl_path) and not os.path.exists(target_prd):
        with open(prd_tpl_path, 'r', encoding='utf-8') as f:
            prd_content = f.read()
        
        prd_content = prd_content.replace("[Project/Feature Name]", project_name)
        
        if req_content:
            # Inject requirement content into the User Stories or Functional section if tags exist, 
            # otherwise append
            if "## 3. Functional Requirements" in prd_content:
                 prd_content = prd_content.replace("## 3. Functional Requirements", f"## 3. Functional Requirements\n\n### 📝 Raw Requirements (Input)\n{req_content}\n")
            else:
                 prd_content += f"\n\n## 📝 Raw Requirements (Input)\n{req_content}"
        
        with open(target_prd, 'w', encoding='utf-8') as f:
            f.write(prd_content)
        print(f"✅ Created initial {target_prd}")
    else:
        print("⏭️  Skipping PRD.md: already exists.")

    # 3. Create tasks directory
    tasks_dir = os.path.join(docs_dir, "tasks")
    if not os.path.exists(tasks_dir):
        os.makedirs(tasks_dir)
        print(f"✅ Created {tasks_dir} directory for detailed specifications")

def main():
    parser = argparse.ArgumentParser(description="Initialize project documentation structure")
    parser.add_argument("name", help="Name of the project or feature")
    parser.add_argument("--req-file", help="Path to the initial requirements file")
    parser.add_argument("--req-text", help="Raw requirements text")
    args = parser.parse_args()
    initialize_project(args.name, args.req_file, args.req_text)

if __name__ == "__main__":
    main()
