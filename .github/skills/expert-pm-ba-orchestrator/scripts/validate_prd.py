import os
import sys
import argparse
import re
import io

# Fix for Windows console encoding issues
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

def validate_prd(prd_path):
    if not os.path.exists(prd_path):
        print(f"Error: PRD not found at {prd_path}")
        return False

    with open(prd_path, 'r', encoding='utf-8') as f:
        content = f.read()

    errors = []
    
    # Check for mandatory sections
    mandatory_sections = [
        "Functional Requirements",
        "Logic Validation Checklist",
        "Edge Case Matrix",
        "Non-Functional Requirements",
        "Acceptance Criteria"
    ]
    
    for section in mandatory_sections:
        if section not in content:
            errors.append(f"Missing mandatory section: {section}")

    # Check for un-filled placeholders
    placeholders = re.findall(r'\[.*?\]', content)
    if placeholders:
        # Filter out common markdown patterns like [x]
        real_placeholders = [p for p in placeholders if len(p) > 3 and p not in ["[ ]", "[x]"]]
        if real_placeholders:
            errors.append(f"Unfilled placeholders found: {', '.join(real_placeholders)}")

    # Check Logic Validation Checklist completion
    logic_section = re.search(r'## 7\. Logic Validation Checklist.*?(?=##|$)', content, re.S)
    if logic_section:
        unchecked = re.findall(r'- \[ \]', logic_section.group(0))
        if unchecked:
            errors.append(f"Logic Validation Checklist has {len(unchecked)} unchecked items.")

    if errors:
        print("❌ PRD Validation Failed:")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("✅ PRD Validation Passed! Ready for Architecture Design.")
        return True

def main():
    parser = argparse.ArgumentParser(description="Validate PRD completeness and logic")
    parser.add_argument("path", help="Path to the PRD.md file")
    args = parser.parse_args()
    validate_prd(args.path)

if __name__ == "__main__":
    main()
