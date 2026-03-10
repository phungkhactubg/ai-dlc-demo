import argparse
import os

CHECKLIST = """# Remote Repo Health & Architecture Scan: {repo_name}

## 📊 Repo Vital Signs
- **Stars/Forks**: 
- **Last Commit**: (Is it maintained?)
- **Open Issues**: (Ratio of bug vs feature)
- **Contributors**: (Bus factor check)

## 🏗️ Architecture Analysis (L3 External)
- **Main Interface/Entrypoint**: (Where does the logic start?)
- **Core Dependencies**: (Does it pull in heavy libs?)
- **Concurrency Handling**: (How does it use goroutines/locks?)
- **Error Propagation Pattern**: (Custom errors vs standard?)

## 🧩 Integration Feasibility
- **Go Context Propagation**: (Does it support context.Context?)
- **Dependency Conflicts**: (Version clashes with our modules?)
- **Memory Footprint**: (Any known leaks in issues?)

## 📝 Verdict
[ ] Highly Feasible
[ ] Feasible with wrappers
[ ] High Risk
"""

def main():
    parser = argparse.ArgumentParser(description="Deep Source Verification Guide")
    parser.add_argument("repo", help="GitHub repo name (e.g. owner/repo)")
    parser.add_argument("--output", default="REPO_VERIFICATION.md", help="Output path")

    args = parser.parse_args()

    content = CHECKLIST.format(repo_name=args.repo)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Generated repo verification checklist for {args.repo} at: {args.output}")

if __name__ == "__main__":
    main()
