#!/usr/bin/env python3
"""
GitHub Repository Research Tool
Search for similar projects, popular libraries, and check repo stats.
Uses standard library - no pip install required.
"""
import argparse
import json
import urllib.request
import urllib.parse
import os

GITHUB_API = "https://api.github.com"

def get_headers():
    """Get headers with optional token for higher rate limits."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Senior-Researcher-Agent"
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def search_repositories(query, language=None, sort="stars", limit=10):
    """Search GitHub repositories."""
    q = query
    if language:
        q += f" language:{language}"
    
    params = {
        "q": q,
        "sort": sort,
        "order": "desc",
        "per_page": limit
    }
    
    url = f"{GITHUB_API}/search/repositories?{urllib.parse.urlencode(params)}"
    
    print(f"[*] Searching GitHub for: '{query}'...")
    if language:
        print(f"    Language filter: {language}")
    
    try:
        req = urllib.request.Request(url, headers=get_headers())
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        
        print(f"\n--- Found {data.get('total_count', 0)} repositories (showing top {limit}) ---\n")
        
        for i, repo in enumerate(data.get("items", [])[:limit], 1):
            name = repo.get("full_name")
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            desc = repo.get("description", "No description")[:80]
            url = repo.get("html_url")
            license_info = repo.get("license")
            license_name = license_info.get("spdx_id", "Unknown") if license_info else "No License"
            
            print(f"{i}. {name}")
            print(f"   ⭐ {stars:,} | 🍴 {forks:,} | 📜 {license_name}")
            print(f"   {desc}")
            print(f"   {url}\n")
            
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("[!] Rate limited. Set GITHUB_TOKEN env var for higher limits.")
        else:
            print(f"[!] HTTP Error: {e.code} - {e.reason}")
    except Exception as e:
        print(f"[!] Error: {e}")

def get_repo_info(owner, repo):
    """Get detailed info about a specific repository."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}"
    
    print(f"[*] Fetching info for: {owner}/{repo}...")
    
    try:
        req = urllib.request.Request(url, headers=get_headers())
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        
        print(f"\n=== {data.get('full_name')} ===")
        print(f"Description: {data.get('description', 'N/A')}")
        print(f"Stars: {data.get('stargazers_count', 0):,}")
        print(f"Forks: {data.get('forks_count', 0):,}")
        print(f"Open Issues: {data.get('open_issues_count', 0)}")
        print(f"Language: {data.get('language', 'N/A')}")
        print(f"License: {data.get('license', {}).get('name', 'Unknown')}")
        print(f"Created: {data.get('created_at', 'N/A')[:10]}")
        print(f"Last Push: {data.get('pushed_at', 'N/A')[:10]}")
        print(f"URL: {data.get('html_url')}")
        
        # Topics/Tags
        topics = data.get("topics", [])
        if topics:
            print(f"Topics: {', '.join(topics[:10])}")
            
    except Exception as e:
        print(f"[!] Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="GitHub Repository Research Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search repositories")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--lang", help="Filter by language (e.g., go, python, typescript)")
    search_parser.add_argument("--sort", choices=["stars", "forks", "updated"], default="stars")
    search_parser.add_argument("--limit", type=int, default=10)
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get repository details")
    info_parser.add_argument("repo", help="Repository in format owner/repo")
    
    args = parser.parse_args()
    
    if args.command == "search":
        search_repositories(args.query, args.lang, args.sort, args.limit)
    elif args.command == "info":
        parts = args.repo.split("/")
        if len(parts) == 2:
            get_repo_info(parts[0], parts[1])
        else:
            print("[!] Invalid format. Use: owner/repo")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
