#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

TEMPLATE = """# Research Thinking Log: {task_name}

## 🎯 Current Hypothesis
> [What am I trying to prove or disprove right now? What is the core assumption?]

- **Hypothesis**: 
- **Confidence**: (Low/Medium/High)
- **Primary Goal**: 

---

## 🧠 Deductions & Insights
> [Don't just list facts. Connect the dots. If A is true and B is true, then C must be...]

1. **Deduction**: 
   - **Evidence**: 
   - **Impact**: 

---

## 🤨 Strategic Skepticism (The Friction Audit)
> [Why might the current results be "too good to be true"? Look for the catch.]

- **Known Unknowns**: 
- **Suspicious Claims**: 

---

## 🔄 Pivot Logic
> [Why are we changing our search direction? What gap was identified?]

- **Current Gap**: 
- **New Direction**: 

---

## 🎖️ Skill Compliance & Diligence Log
**MANDATORY CHECKLIST (Expert-Researcher SKILL.md):**
- [ ] **Recursive Depth**: Have I identified and deep-dived ALL sub-modules? (Phase 4)
- [ ] **Forensic Tracing**: Have I cited specific files/line numbers for all logic? (Phase 5/6)
- [ ] **Absolute Exhaustion**: Have I covered Financials & Regulatory without being asked? (Phase 3)
- [ ] **Diligence Floor**: Have I completed at least 10 research loops? (Phase 6)
- [ ] **Final Self-Audit**: Does this result satisfy a 20-year Senior Principal Engineer? (Phase 7)

---
**Compliance Verification Statement**: 
> I confirm absolute compliance with SKILL.md and verify that no instructions were skimmed or skipped.
"""

def main():
    parser = argparse.ArgumentParser(description="Scaffold a Research Thinking Log (Expert Standard)")
    parser.add_argument("task", help="Name of the research task")
    parser.add_argument("--output", default="project-documentation/RESEARCH_THINKING.md", help="Output path (default: project-documentation/RESEARCH_THINKING.md)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing file")

    args = parser.parse_args()

    output_path = Path(args.output)
    
    if output_path.exists() and not args.overwrite:
        print(f"❌ Error: {output_path} already exists. Use --overwrite to replace it.")
        sys.exit(1)

    # Ensure standardized directory path if default not used
    if not output_path.parts[0] == "project-documentation":
         # Force standardization if needed, but here we trust the default and the user override
         pass

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = TEMPLATE.format(task_name=args.task)
    output_path.write_text(content, encoding="utf-8")
    
    print(f"✅ Generated Research Thinking Log at: {output_path}")

if __name__ == "__main__":
    main()
