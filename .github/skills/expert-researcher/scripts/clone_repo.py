#!/usr/bin/env python3
"""
Standardized Repo Cloner for Expert Researcher.
Clones repositories into `project-documentation/repos/<repo_name>`.
"""
import argparse
import os
import sys
import subprocess
from pathlib import Path

def resolve_repo_name(repo_input: str) -> str:
    """Extract repo name from URL or owner/repo string."""
    if repo_input.endswith(".git"):
        repo_input = repo_input[:-4]
    
    parts = repo_input.split("/")
    return parts[-1]

def resolve_repo_url(repo_input: str) -> str:
    """Ensure we have a valid git URL."""
    if "github.com" in repo_input or "gitlab.com" in repo_input:
        return repo_input
    # Assume owner/repo format for GitHub
    return f"https://github.com/{repo_input}"

def main():
    parser = argparse.ArgumentParser(description="Clone repo to standardized Expert Researcher location")
    parser.add_argument("repo", help="Repository URL or owner/repo string")
    parser.add_argument("--branch", help="Specific branch to clone")
    
    args = parser.parse_args()
    
    repo_name = resolve_repo_name(args.repo)
    repo_url = resolve_repo_url(args.repo)
    
    # workspace sovereignty - output path
    # We assume this script is run from project root or checks relative to it.
    # Best practice: anchor to cwd if it looks like project root, or find it.
    # For simplicity in this env, we assume cwd is project root.
    
    base_dir = Path("project-documentation/repos")
    target_dir = base_dir / repo_name
    
    print(f"🔒 Workspace Sovereignty: Target Directory -> {target_dir}")
    
    if target_dir.exists():
        print(f"✅ Repository '{repo_name}' already exists at {target_dir}")
        print("   Checking for updates...")
        try:
            # Attempt git pull
            subprocess.run(["git", "pull"], cwd=target_dir, check=False)
        except Exception as e:
            print(f"⚠️  Git pull failed: {e}")
    else:
        print(f"📥 Cloning {repo_url}...")
        base_dir.mkdir(parents=True, exist_ok=True)
        
        cmd = ["git", "clone", repo_url, str(target_dir)]
        if args.branch:
            cmd.extend(["-b", args.branch])
            
        try:
            subprocess.run(cmd, check=True)
            print("✅ Clone successful.")
        except subprocess.CalledProcessError:
            print("❌ Clone failed.")
            sys.exit(1)
            
    # Output the absolute path for other tools to consume
    print(f"OUTPUT_PATH={target_dir.absolute()}")

if __name__ == "__main__":
    main()
