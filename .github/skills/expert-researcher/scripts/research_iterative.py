import argparse
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Set
from urllib.parse import urlparse

class ResearchState:
    def __init__(self, task_name: str, complexity: int = 3, repo_root: str = None):
        self.task_name = task_name
        self.complexity = int(complexity)
        self.repo_root = repo_root
        self.timestamp = datetime.now().isoformat()
        self.queries: List[str] = []
        self.findings: List[Dict[str, Any]] = []
        self.deductions: List[Dict[str, Any]] = []
        self.pending_modules: List[str] = [] # Modules identified but not deep-dived
        self.scanners_run: List[str] = [] # Modules audited via local scanning tools
        self.candidates: List[Dict[str, Any]] = []
        self.uncertainties: List[str] = []
        self.loops_completed = 0

    def register_module(self, module_name: str):
        if module_name not in self.pending_modules:
            self.pending_modules.append(module_name)

    def log_scan(self, module_name: str):
        if module_name not in self.scanners_run:
            self.scanners_run.append(module_name)

    def add_query(self, query: str):
        self.queries.append(query)
        self.loops_completed += 0.5 

    def add_finding(self, source: str, detail: str, evaluation: str = "Neutral", module: str = "Global"):
        self.findings.append({
            "source": source,
            "detail": detail,
            "evaluation": evaluation,
            "module": module,
            "timestamp": datetime.now().isoformat()
        })
        self.loops_completed += 0.5

    def add_deduction(self, deduction: str, module: str = "Global"):
        self.deductions.append({
            "detail": deduction,
            "module": module,
            "timestamp": datetime.now().isoformat()
        })
        self.loops_completed += 0.5

    def save(self, output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.__dict__, f, indent=2)

    def _get_unique_domains(self) -> Set[str]:
        domains = set()
        for f in self.findings:
            source = f.get("source", "")
            if source.startswith("http"):
                parsed = urlparse(source)
                domains.add(parsed.netloc)
            elif source: # Treat non-URL strings as distinct local sources
                domains.add(source.lower())
        return domains

    def get_status_report(self) -> str:
        report = []
        report.append(f"\n╔════ 🎖️ EXPERT RESEARCH STATUS: {self.task_name} ════")
        report.append(f"║ Loops Completed (Est): {int(self.loops_completed)}")
        report.append(f"║ Queries Run: {len(self.queries)}")
        report.append(f"║ Findings Logged: {len(self.findings)}")
        report.append(f"║ Deductions Made: {len(self.deductions)}")
        
        # Module Coverage
        modules = set(f.get("module", "Global") for f in self.findings) | set(d.get("module", "Global") for d in self.deductions)
        report.append(f"║ Module Coverage: {', '.join(modules)}")
        
        unique_domains = self._get_unique_domains()
        report.append(f"║ Source Diversity: {len(unique_domains)} domains")
        report.append("╠════════════════════════════════════════════════════")
        
        # 20-Year Expert Validation Logic
        warnings = []
        
        # New Pillar: Module Exhaustion Lock (Self-Expanding Discovery)
        active_modules = set(f.get("module", "Global") for f in self.findings) | set(d.get("module", "Global") for d in self.deductions)
        unresearched = [m for m in self.pending_modules if m not in active_modules]
        if unresearched:
            warnings.append(f"[!] MODULE EXHAUSTION FAILED: {len(unresearched)} modules in inventory have 0 findings/deductions.")
            warnings.append(f"    -> ACTION: You MUST deep-dive into: {', '.join(unresearched)}.")

        # New Pillar: Absolute Repository Mirror Mandate (Horizontal Exhaustion)
        if self.repo_root and os.path.exists(self.repo_root):
            repo_path = Path(self.repo_root)
            # Find all potential module dirs (e.g., top-level folders in modules/ or root)
            potential_module_dirs = [d.name for d in repo_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
            if (repo_path / "modules").exists():
                 potential_module_dirs += [d.name for d in (repo_path / "modules").iterdir() if d.is_dir() and not d.name.startswith('.')]
            
            potential_module_dirs = sorted(list(set(potential_module_dirs)))
            missing_repo_modules = [m for m in potential_module_dirs if m not in active_modules]
            
            if missing_repo_modules:
                warnings.append(f"[!] REPOSITORY MIRROR FAILED: {len(missing_repo_modules)} folders in repository have not been researched.")
                warnings.append(f"    -> ACTION: Absolute Exhaustion requires deep-dives into: {', '.join(missing_repo_modules)}.")
            
            # Sub-Pillar: Local Scan Exhaustion (DISABLED - Now Conditional)
            # unscanned = [m for m in potential_module_dirs if m not in self.scanners_run]
            # if unscanned:
            #     warnings.append(f"[!] LOCAL SCAN MANDATE FAILED: {len(unscanned)} repository modules have NOT been scanned with local tools.")
            #     warnings.append(f"    -> ACTION: You MUST use scan-project or codebase-scanner on: {', '.join(unscanned)}.")

        # Pillar 1: Triangulation (Expert requires 3+ domains)
        if len(unique_domains) < 3:
            warnings.append(f"[!] TRIANGULATION FAILED: Only {len(unique_domains)}/3 source domains found.")
            warnings.append("    -> ACTION: You MUST find independent community views (Reddit/HN) or Source Code (GitHub).")
        
        # Pillar 2: Friction & Edge Cases
        negatives = [f for f in self.findings if f.get("evaluation") == "Negative"]
        if not negatives:
            warnings.append("[!] FRICTION AUDIT MISSING: No negative findings logged.")
            warnings.append("    -> ACTION: Search for '[candidate] issues' or 'why NOT to use [candidate]'.")
        
        # Pillar 3: Code Reference Audit (Forensic Evidence)
        import re
        code_pattern = re.compile(r"`[^`]+`|\b(func|class|struct|interface|def|return)\b|\.[a-z]{1,4}\b|[a-zA-Z0-9_]+\(\)", re.IGNORECASE)
        technical_findings = [f for f in self.findings if "source code" in f.get("source", "").lower() or "github" in f.get("source", "").lower()]
        if technical_findings:
            code_backed_findings = [f for f in technical_findings if code_pattern.search(f.get("detail", ""))]
            if len(code_backed_findings) < len(technical_findings) * 0.5:
                warnings.append(f"[!] CODE AUDIT WEAK: Only {len(code_backed_findings)}/{len(technical_findings)} technical findings reference actual code.")
                warnings.append("    -> ACTION: Quote specific file paths, function signatures, or struct definitions.")
        
        # New Pillar: Strategic Reasoning
        if len(self.deductions) < 3:
            warnings.append(f"[!] REASONING GAP: Only {len(self.deductions)}/3 strategic deductions logged. (Diligent research requires more synthesis).")
            warnings.append("    -> ACTION: Use --deduction to log insights that connect multiple modules or findings.")

        # Mandatory Domain Audit (Absolute Exhaustion Mandate)
        all_details_lower = " ".join([f.get("detail", "") for f in self.findings]).lower()
        all_deductions_lower = " ".join([d.get("detail", "") for d in self.deductions]).lower()
        
        mandatory_checks = {
            "Financial": ["pricing", "cost", "revenue", "funding", "business model", "financial"],
            "Regulatory": ["legal", "compliance", "regulation", "license", "gdpr", "cfius", "policy"],
            "Forensic Trace": ["main.", "app.", "init", "file:", "line:", "(", ")"],
            "Self-Audit": ["compliance", "audit", "verified", "skill check", "internal review"]
        }
        for domain, keywords in mandatory_checks.items():
            content_to_check = all_details_lower if domain != "Self-Audit" else all_deductions_lower
            if not any(k in content_to_check for k in keywords):
                warnings.append(f"[!] {domain.upper()} AUDIT FAILED: {domain} analysis missing or not logged as a deduction.")
                warnings.append(f"    -> ACTION: {domain} aspects must be explicitly researched and verified against SKILL.md.")

        # The Exponential Diligence Floor
        loop_floor = {1: 10, 2: 20, 3: 30}.get(self.complexity, 30)
        if self.loops_completed < loop_floor:
            warnings.append(f"[!] DILIGENCE FLOOR NOT REACHED: (Tier {self.complexity} Complexity).")
            warnings.append(f"    -> ACTION: Current: {int(self.loops_completed)}/{loop_floor} required iterations. Research is TOO FAST.")
        
        # Source Saturation Check (Synthesis must continue late-game)
        if self.loops_completed > (loop_floor * 0.7):
            recent_deductions = [d for d in self.deductions if d.get("timestamp", "") > (self.findings[-1].get("timestamp", "") if self.findings else "")]
            if not recent_deductions:
                warnings.append("[!] SOURCE SATURATION NOT REACHED: No new deductions found in late-stage loops.")
                warnings.append("    -> ACTION: You haven't found new patterns lately. Dig deeper into sub-modules or benchmarks.")
        
        # Skill Compliance Lock
        if "compliance" not in all_deductions_lower:
            warnings.append("[!] SKILL COMPLIANCE LOCK: No explicit 'Skill Compliance Audit' found in deductions.")
            warnings.append("    -> ACTION: Log a deduction using --deduction that explicitly confirms your work meets all SKILL.md requirements.")

        if not warnings:
             report.append("║ ✅ STATUS: SUFFICIENT DEPTH (Human-Expert Grade).")
             report.append("║ Ready to generate the final Architecture Spec / Implementation Plan.")
        else:
             report.append("║ ❌ STATUS: INSUFFICIENT DEPTH (Further Investigation Required)")
             for w in warnings:
                 report.append(f"║ {w}")
        
        report.append("╚════════════════════════════════════════════════════\n")
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="Manage Recursive Research State (Expert Standard)")
    parser.add_argument("task", help="Name of the research task")
    parser.add_argument("--repo_root", help="Local path to the cloned repository for forensic scanning")
    parser.add_argument("--register_module", help="Identify a new system module for mandatory deep-dive")
    parser.add_argument("--scanned_module", help="Log that a module has been audited via local scan-project/scanner")
    parser.add_argument("--complexity", type=int, choices=[1, 2, 3], default=3, help="Complexity Tier (1:10, 2:20, 3:30+ loops)")
    parser.add_argument("--query", help="Add a search query used")
    parser.add_argument("--finding", help="Add a technical finding")
    parser.add_argument("--deduction", help="Add a strategic deduction/insight")
    parser.add_argument("--module", default="Global", help="Scope finding/deduction to a specific module")
    parser.add_argument("--source", help="Source for the finding (URL or description)")
    parser.add_argument("--eval", choices=["Positive", "Neutral", "Negative"], default="Neutral", help="Evaluation of the finding")
    parser.add_argument("--status", action="store_true", help="Show current research summary")
    parser.add_argument("--output", default=os.path.join("project-documentation", "RESEARCH_STATE.json"), help="Path to state file")

    args = parser.parse_args()

    # PATH HARDENING (Workspace Sovereignty)
    output_path = Path(args.output).resolve()
    if "project-documentation" not in str(output_path):
        output_path = (Path("project-documentation") / "RESEARCH_STATE.json").resolve()
    
    print(f"🔒 Workspace Sovereignty: Research State at {output_path}")

    # Load or create state
    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                state = ResearchState(
                    data.get('topic_name', args.task), 
                    data.get('complexity', args.complexity),
                    data.get('repo_root', args.repo_root)
                )
                # Restore dict
                state.__dict__.update(data)
                # Ensure args override if provided
                if args.repo_root:
                    state.repo_root = args.repo_root
        except Exception:
             state = ResearchState(args.task, args.complexity, args.repo_root)
    else:
        state = ResearchState(args.task, args.complexity, args.repo_root)

    if args.register_module:
        state.register_module(args.register_module)
        print(f"✅ Registered Module for Deep-Dive: {args.register_module}")

    if args.scanned_module:
        state.log_scan(args.scanned_module)
        print(f"✅ Logged Local Scan for Module: {args.scanned_module}")

    if args.query:
        state.add_query(args.query)
        print(f"✅ Logged Query: {args.query}")

    if args.finding and args.source:
        state.add_finding(args.source, args.finding, args.eval, args.module)
        print(f"✅ Logged Finding [{args.module}] from: {args.source}")

    if args.deduction:
        state.add_deduction(args.deduction, args.module)
        print(f"✅ Logged Deduction [{args.module}]: {args.deduction}")

    state.save(str(output_path))

    if args.status or args.query or args.finding or args.deduction:
        print(state.get_status_report())

if __name__ == "__main__":
    main()
