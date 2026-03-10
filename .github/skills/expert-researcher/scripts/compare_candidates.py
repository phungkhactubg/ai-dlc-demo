import argparse
import os

TEMPLATE = """# Comparative Analysis: {title}

## Summary Table

| Criteria | {candidate_a} | {candidate_b} | {candidate_c} |
|----------|---------------|---------------|---------------|
| **Version/Maturity** | | | |
| **Performance** | | | |
| **Go Integration** | | | |
| **Maintenance** | | | |
| **License** | | | |

## Detailed Analysis

### 1. {candidate_a}
- **Pros**:
- **Cons**:
- **Known Issues**:

### 2. {candidate_b}
- **Pros**:
- **Cons**:
- **Known Issues**:

## Final Recommendation
**Winner**: {candidate_a} (Example)
**Rationale**:
1. ...
2. ...
3. ...

**Alternative Context**: Use {candidate_b} if ...
"""

def main():
    parser = argparse.ArgumentParser(description="Generate Comparative Analysis Template")
    parser.add_argument("title", help="Title of the comparison")
    parser.add_argument("--a", required=True, help="Candidate A")
    parser.add_argument("--b", required=True, help="Candidate B")
    parser.add_argument("--c", default="N/A", help="Candidate C (Optional)")
    parser.add_argument("--output", default=os.path.join("project-documentation", "COMPARATIVE_ANALYSIS.md"), help="Output path")

    args = parser.parse_args()

    content = TEMPLATE.format(
        title=args.title,
        candidate_a=args.a,
        candidate_b=args.b,
        candidate_c=args.c
    )

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Generated comparison template at: {args.output}")

if __name__ == "__main__":
    main()
