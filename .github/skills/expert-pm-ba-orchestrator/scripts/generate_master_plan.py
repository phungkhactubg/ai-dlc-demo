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

def generate_master_plan(feature_name):
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "MASTER_PLAN_TEMPLATE.md")
    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}")
        return

    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse Architecture Spec for components if it exists
    # Parse Architecture Spec for components if it exists
    components = []
    arch_file = "project-documentation/ARCHITECTURE_SPEC.md"
    if not os.path.exists(arch_file):
        arch_file = "ARCHITECTURE_SPEC.md"  # Fallback
    
    if os.path.exists(arch_file):
        with open(arch_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Look for headers like "### [Component Name]" or "#### [Component Name]"
            for line in lines:
                if line.startswith("###") or line.startswith("####"):
                    comp = line.strip("#").strip()
                    if comp.lower() not in ["overview", "infrastructure", "context", "deliverables", "components"]:
                        components.append(comp)

    content = content.replace("[Project/Feature Name]", feature_name)
    content = content.replace("[Timestamp]", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    # Inject Component-specific tasks
    if components:
        be_tasks = "\n".join([f"- [ ] [BE] Implement Core Logic for {c}" for c in components])
        fe_tasks = "\n".join([f"- [ ] [FE] Implement UI for {c}" for c in components])
        
        content = content.replace("- [ ] Scaffold Feature Module (`/add-feature`)", f"- [ ] Scaffold Feature Module (`/add-feature`)\n{be_tasks}")
        content = content.replace("- [ ] Scaffold Feature Slice in Frontend", f"- [ ] Scaffold Feature Slice in Frontend\n{fe_tasks}")

    # Output directory
    docs_dir = "project-documentation"
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)

    base_filename = "MASTER_PLAN.md" if os.environ.get("SDLC_AUTO") == "true" else f"MASTER_PLAN_{feature_name.lower().replace(' ', '_')}.md"
    output_filename = os.path.join(docs_dir, base_filename)
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created Master Plan: {output_filename}")
    if components:
        print(f"📦 Identified {len(components)} components from architecture spec: {', '.join(components)}")

def main():
    parser = argparse.ArgumentParser(description="Generate component-aware Master Plan")
    parser.add_argument("name", help="Name of the feature or project")
    args = parser.parse_args()
    generate_master_plan(args.name)

if __name__ == "__main__":
    main()
