#!/usr/bin/env python3
"""
Incremental Scanner - Only scan changed files for faster updates.
Supports: file mtime diff, git diff, date-based scanning.
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import argparse


class IncrementalScanner:
    """Scans only changed files for faster documentation updates."""
    
    METADATA_FILE = ".scan_metadata.json"
    
    def __init__(self, root_dir: Path, output_dir: Path, verbose: bool = False):
        self.root_dir = Path(root_dir).absolute()
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        self.metadata_path = self.output_dir / self.METADATA_FILE
        self.metadata: Dict = self._load_metadata()
    
    def log(self, msg: str):
        if self.verbose:
            print(f"   [incremental] {msg}")
    
    def _load_metadata(self) -> Dict:
        """Load scan metadata from previous run."""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path) as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_scan": None,
            "file_hashes": {},
            "scanned_files": [],
        }
    
    def _save_metadata(self):
        """Save scan metadata for next run."""
        self.metadata["last_scan"] = datetime.now().isoformat()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)
    
    def scan_diff(self) -> List[str]:
        """Find files changed since last scan using mtime."""
        changed = []
        last_scan = self.metadata.get("last_scan")
        
        if not last_scan:
            print("⚠️  No previous scan found. Running full scan...")
            return self._get_all_source_files()
        
        last_time = datetime.fromisoformat(last_scan)
        print(f"📊 Finding files changed since {last_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        for path in self._get_all_source_files():
            full_path = self.root_dir / path
            if full_path.exists():
                mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
                if mtime > last_time:
                    changed.append(path)
                    self.log(f"Changed: {path}")
        
        print(f"✅ Found {len(changed)} changed files")
        return changed
    
    def scan_since(self, since_date: str) -> List[str]:
        """Find files changed since a specific date."""
        changed = []
        try:
            since_time = datetime.fromisoformat(since_date)
        except ValueError:
            # Try parsing common formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"]:
                try:
                    since_time = datetime.strptime(since_date, fmt)
                    break
                except:
                    continue
            else:
                print(f"❌ Could not parse date: {since_date}")
                return []
        
        print(f"📊 Finding files changed since {since_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        for path in self._get_all_source_files():
            full_path = self.root_dir / path
            if full_path.exists():
                mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
                if mtime > since_time:
                    changed.append(path)
        
        print(f"✅ Found {len(changed)} changed files")
        return changed
    
    def scan_git_diff(self, branch: str = "main") -> List[str]:
        """Find files changed in git diff vs branch."""
        print(f"📊 Finding files different from branch: {branch}")
        
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", branch],
                capture_output=True,
                text=True,
                cwd=self.root_dir
            )
            
            if result.returncode != 0:
                print(f"❌ Git error: {result.stderr}")
                return []
            
            changed = [f for f in result.stdout.strip().split("\n") if f and self._is_source_file(f)]
            print(f"✅ Found {len(changed)} changed files")
            return changed
            
        except FileNotFoundError:
            print("❌ Git not found. Please install git.")
            return []
    
    def scan_commits(self, num_commits: int = 5) -> List[str]:
        """Find files changed in last N commits."""
        print(f"📊 Finding files changed in last {num_commits} commits")
        
        try:
            result = subprocess.run(
                ["git", "log", f"-{num_commits}", "--name-only", "--pretty=format:"],
                capture_output=True,
                text=True,
                cwd=self.root_dir
            )
            
            if result.returncode != 0:
                print(f"❌ Git error: {result.stderr}")
                return []
            
            # Deduplicate files
            files = set()
            for line in result.stdout.strip().split("\n"):
                if line and self._is_source_file(line):
                    files.add(line)
            
            changed = list(files)
            print(f"✅ Found {len(changed)} changed files")
            return changed
            
        except FileNotFoundError:
            print("❌ Git not found. Please install git.")
            return []
    
    def _get_all_source_files(self) -> List[str]:
        """Get all source files in project."""
        source_exts = {".go", ".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".cs", ".cpp", ".c", ".h", ".hpp", ".rs", ".rb"}
        exclude_dirs = {"node_modules", "vendor", ".git", "dist", "build", "__pycache__"}
        
        files = []
        for path in self.root_dir.rglob("*"):
            if path.is_file() and path.suffix in source_exts:
                # Check exclusions
                parts = path.relative_to(self.root_dir).parts
                if not any(ex in parts for ex in exclude_dirs):
                    files.append(str(path.relative_to(self.root_dir)))
        
        return files
    
    def _is_source_file(self, path: str) -> bool:
        """Check if path is a source file."""
        source_exts = {".go", ".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".cs", ".cpp", ".c", ".h", ".hpp", ".rs", ".rb"}
        return Path(path).suffix in source_exts
    
    def update_docs(self, changed_files: List[str]):
        """Update documentation for changed files."""
        if not changed_files:
            print("✅ No files changed. Documentation is up to date.")
            return
        
        print(f"\n📝 Updating documentation for {len(changed_files)} files...")
        
        # Group by domain/module
        domains: Dict[str, List[str]] = {}
        for f in changed_files:
            parts = Path(f).parts
            if len(parts) >= 2:
                domain = parts[1] if parts[0] in ["features", "apps", "lib"] else parts[0]
            else:
                domain = "root"
            
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(f)
        
        # Update L2 domain docs
        l2_dir = self.output_dir / "L2_DOMAINS"
        l2_dir.mkdir(parents=True, exist_ok=True)
        
        for domain, files in domains.items():
            self._update_domain_doc(domain, files)
        
        # Update L0 summary
        self._update_executive_summary(changed_files)
        
        # Save metadata
        self._save_metadata()
        
        print("✅ Documentation updated!")
    
    def _update_domain_doc(self, domain: str, files: List[str]):
        """Update L2 domain documentation."""
        domain_dir = self.output_dir / "L2_DOMAINS" / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        
        doc_path = domain_dir / "CHANGES.md"
        
        content = f"""# Recent Changes in {domain}

> Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Changed Files

| File | Type |
|------|------|
"""
        for f in files:
            ext = Path(f).suffix
            content += f"| `{f}` | {ext} |\n"
        
        with open(doc_path, "w") as f:
            f.write(content)
        
        self.log(f"Updated: {doc_path}")
    
    def _update_executive_summary(self, changed_files: List[str]):
        """Update L0 executive summary with change info."""
        summary_path = self.output_dir / "L0_EXECUTIVE_SUMMARY.md"
        
        # Read existing or create new
        if summary_path.exists():
            content = summary_path.read_text()
            # Add change section
            change_section = f"""

## Recent Activity

> Last scan: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**{len(changed_files)} files changed** in recent update.

"""
            # Insert after first section
            if "## Recent Activity" in content:
                # Replace existing
                import re
                content = re.sub(
                    r"## Recent Activity.*?(?=## |$)", 
                    change_section, 
                    content, 
                    flags=re.DOTALL
                )
            else:
                content += change_section
            
            with open(summary_path, "w") as f:
                f.write(content)


def main():
    parser = argparse.ArgumentParser(description="Incremental codebase scanner")
    parser.add_argument("--mode", choices=["diff", "since", "git-diff", "commits"], 
                       default="diff", help="Scan mode")
    parser.add_argument("--since", help="Date for --mode since (YYYY-MM-DD)")
    parser.add_argument("--branch", default="main", help="Branch for git-diff mode")
    parser.add_argument("--commits", type=int, default=5, help="Number of commits")
    parser.add_argument("--output", "-o", default="project-documentation/codebase-docs", help="Output dir")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Auto-append repo name if using default output path
    if args.output == "project-documentation/codebase-docs":
        repo_name = Path.cwd().name
        args.output = str(Path(args.output) / repo_name)
        if args.verbose:
            print(f"ℹ️  Output directory set to: {args.output}")

    scanner = IncrementalScanner(Path.cwd(), Path(args.output), args.verbose)
    
    if args.mode == "diff":
        changed = scanner.scan_diff()
    elif args.mode == "since":
        if not args.since:
            print("❌ --since date required for this mode")
            return 1
        changed = scanner.scan_since(args.since)
    elif args.mode == "git-diff":
        changed = scanner.scan_git_diff(args.branch)
    elif args.mode == "commits":
        changed = scanner.scan_commits(args.commits)
    else:
        changed = []
    
    scanner.update_docs(changed)
    return 0


if __name__ == "__main__":
    exit(main())
