import os
import sys
import argparse

import os
import sys
import argparse
import subprocess
import io

# Fix for Windows console encoding issues
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

def search_keywords(keywords):
    """Search for keywords in the codebase."""
    results = []
    # Simplified search: look for keyword in filenames and common source dirs
    search_dirs = ["features", "apps/frontend/src", "internal", "pkg"]
    
    # Using 'grep' via subprocess (cross-platform if ripgrep or git grep is available)
    # Falling back to simple os.walk if needed
    for root_dir in search_dirs:
        if not os.path.exists(root_dir): continue
        
        for root, dirs, files in os.walk(root_dir):
            if any(d in root for d in [".git", "node_modules", "vendor"]): continue
            
            for file in files:
                if any(kw.lower() in file.lower() for kw in keywords):
                    results.append(os.path.join(root, file))
                    continue
                
                # Sample check content (optional, might be slow)
                # try:
                #     with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                #         content = f.read()
                #         if any(kw.lower() in content.lower() for kw in keywords):
                #             results.append(os.path.join(root, file))
                # except: pass
    return list(set(results))

def analyze_impact(change_description):
    print(f"🔍 Analyzing impact for: {change_description}")
    
    # Extract keywords from description
    keywords = [kw.strip() for kw in change_description.split() if len(kw) > 3]
    
    print("📂 Searching codebase for affected components...")
    affected_src = search_keywords(keywords)
    
    affected_docs = []
    for doc in ["PRD.md", "ARCHITECTURE_SPEC.md", "MASTER_PLAN.md", "OVERVIEW.md"]:
        if os.path.exists(doc):
            affected_docs.append(doc)
    
    print("\n📄 Affected Documents:")
    for d in affected_docs:
        print(f"  - {d}")
        
    if affected_src:
        print("\n💻 Potentially Affected Source Code:")
        for s in sorted(affected_src)[:15]: # Limit output
            print(f"  - {s}")
        if len(affected_src) > 15:
            print(f"  ... and {len(affected_src) - 15} more files.")
    else:
        print("\nℹ️ No specific source code files matched the keywords automatically.")
    
    print("\n📝 Proposed Synchronization Steps:")
    print("1. Update PRD.md with the new requirement specification.")
    print("2. Update ARCHITECTURE_SPEC.md if structural changes are needed.")
    print("3. Add specific implementation tasks to MASTER_PLAN.md.")
    print("4. Call expert developer agents for the affected source files.")

def main():
    parser = argparse.ArgumentParser(description="Analyze impact of a Change Request")
    parser.add_argument("description", help="Description of the change")
    args = parser.parse_args()
    analyze_impact(args.description)

if __name__ == "__main__":
    main()
