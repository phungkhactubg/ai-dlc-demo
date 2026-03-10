import argparse
import sys

TEMPLATE = """# Architectural Impact Analysis: {feature_name}

## 🏗️ Structural Changes
- **Existing Files Modified**: (e.g., routers/constant.go, middleware/auth.go)
- **New Core Dependencies**: (e.g., github.com/nats-io/nats.go)
- **Breaking Changes**: [ ] Yes [ ] No (If yes, describe mitigation)

## ⚖️ Pro/Con vs. Current Patterns
| Aspect | Current Pattern | Proposed Change | Impact |
|--------|-----------------|-----------------|--------|
| **Data Access** | | | |
| **Logic Flow** | | | |
| **Testing** | | | |

## 🚨 Risk Evaluation
- **Complexity**: (1-10)
- **Performance Impact**: (High/Medium/Low)
- **Learning Curve for Team**: (Steep/Moderate/Easy)

## 💡 Recommendation
[ ] Proceed with proposed architecture
[ ] Proceed with modifications
[ ] Reject: Complexity outweighs benefits
"""

def main():
    parser = argparse.ArgumentParser(description="Analyze Architectural Impact of a Research Decision")
    parser.add_argument("feature", help="Name of the feature/technology")
    parser.add_argument("--output", default=os.path.join("project-documentation", "IMPACT_ANALYSIS.md"), help="Output path")

    args = parser.parse_args()

    content = TEMPLATE.format(feature_name=args.feature)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Generated architectural impact analysis template for {args.feature} at: {args.output}")

if __name__ == "__main__":
    main()
