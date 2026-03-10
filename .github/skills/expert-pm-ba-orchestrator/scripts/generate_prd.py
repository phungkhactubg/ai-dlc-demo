import os
import sys
import argparse
import io

# Fix for Windows console encoding issues
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

def generate_prd(feature_name, req_file=None, req_text=None):
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "PRD_TEMPLATE.md")
    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}")
        return

    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Load requirements if provided
    functional_reqs = []
    non_functional_reqs = []
    raw_reqs = ""
    lines = []
    
    if req_file and os.path.exists(req_file):
        with open(req_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            raw_reqs = "".join(lines)
    elif req_text:
        raw_reqs = req_text
        lines = req_text.splitlines()

    if lines:
        # Simple categorization logic
        nf_keywords = ['latency', 'rps', 'ms', 'concurrent', 'security', 'rbac', 'jwt', 'isolation', 'uptime', 'performance', 'throughput']
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'): continue
            
            if any(kw in line.lower() for kw in nf_keywords):
                non_functional_reqs.append(line)
            else:
                functional_reqs.append(line)

    content = content.replace("[Project/Feature Name]", feature_name)
    
    # Inject Functional Requirements
    if functional_reqs:
        formatted_func = "\n".join([f"- {r}" for r in functional_reqs])
        content = content.replace("- **[Feature 1]**: [Detailed description]", f"{formatted_func}\n- **[Feature 1]**: [Detailed description]")

    # Inject Non-Functional Requirements
    if non_functional_reqs:
        formatted_nf = "\n".join([f"- {r}" for r in non_functional_reqs])
        content = content.replace("## 5. Non-Functional Requirements", f"## 5. Non-Functional Requirements\n{formatted_nf}")

    output_dir = "project-documentation"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    base_filename = f"PRD_{feature_name.lower().replace(' ', '_')}.md"
    # Fallback to generic PRD.md if orchestration script expects it
    if os.environ.get("SDLC_AUTO") == "true":
        base_filename = "PRD.md"
    
    output_filename = os.path.join(output_dir, base_filename)

    # Only write if it doesn't exist (unless forced, but here we favor existing PRD)
    if not os.path.exists(output_filename):
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Created PRD: {output_filename}")
        if lines:
            print(f"📈 Categorized {len(functional_reqs)} functional and {len(non_functional_reqs)} non-functional requirements.")
    else:
        print(f"⏭️  PRD {output_filename} already exists. Skipping generation.")

def main():
    parser = argparse.ArgumentParser(description="Generate PRD with requirement ingestion")
    parser.add_argument("name", help="Name of the feature or project")
    parser.add_argument("--req-file", help="Path to raw requirements file")
    parser.add_argument("--req-text", help="Raw requirements text")
    args = parser.parse_args()
    generate_prd(args.name, args.req_file, args.req_text)

if __name__ == "__main__":
    main()
