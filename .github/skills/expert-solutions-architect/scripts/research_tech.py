#!/usr/bin/env python3
"""
Technology Research Script
===========================

Search GitHub for relevant projects, analyze tech stacks, and compare options.

Usage:
    python research_tech.py "workflow engine" --lang go
    python research_tech.py "redis cache" --lang go --limit 10
    python research_tech.py info owner/repo
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote


def get_github_token() -> Optional[str]:
    """Get GitHub token from environment."""
    return os.environ.get("GITHUB_TOKEN")


def github_api_request(endpoint: str, token: Optional[str] = None) -> dict:
    """Make a request to GitHub API."""
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "tech-research-script",
    }
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        if e.code == 403:
            print("⚠️  Rate limit exceeded. Set GITHUB_TOKEN environment variable.")
        elif e.code == 404:
            print(f"❌ Not found: {endpoint}")
        else:
            print(f"❌ HTTP Error {e.code}: {e.reason}")
        return {}
    except URLError as e:
        print(f"❌ Network error: {e.reason}")
        return {}


def search_repositories(query: str, language: Optional[str] = None, limit: int = 10) -> list:
    """Search GitHub repositories."""
    search_query = quote(query)
    if language:
        search_query += f"+language:{language}"
    
    endpoint = f"/search/repositories?q={search_query}&sort=stars&order=desc&per_page={limit}"
    result = github_api_request(endpoint, get_github_token())
    
    return result.get("items", [])


def get_repo_info(owner: str, repo: str) -> dict:
    """Get detailed repository information."""
    endpoint = f"/repos/{owner}/{repo}"
    return github_api_request(endpoint, get_github_token())


def get_repo_languages(owner: str, repo: str) -> dict:
    """Get repository language breakdown."""
    endpoint = f"/repos/{owner}/{repo}/languages"
    return github_api_request(endpoint, get_github_token())


def format_number(n: int) -> str:
    """Format large numbers with K/M suffix."""
    if n >= 1000000:
        return f"{n/1000000:.1f}M"
    if n >= 1000:
        return f"{n/1000:.1f}K"
    return str(n)


def format_date(date_str: str) -> str:
    """Format ISO date to readable format."""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except:
        return date_str[:10] if date_str else "N/A"


def print_search_results(repos: list, query: str):
    """Print search results in a table format."""
    if not repos:
        print(f"No repositories found for '{query}'")
        return
    
    print(f"\n🔍 Search Results for '{query}'\n")
    print("=" * 100)
    print(f"{'Repository':<40} {'Stars':<10} {'Forks':<10} {'Language':<15} {'Updated':<12}")
    print("-" * 100)
    
    for repo in repos:
        name = repo["full_name"][:38]
        stars = format_number(repo["stargazers_count"])
        forks = format_number(repo["forks_count"])
        lang = (repo.get("language") or "N/A")[:13]
        updated = format_date(repo.get("pushed_at", ""))
        
        print(f"{name:<40} {stars:<10} {forks:<10} {lang:<15} {updated:<12}")
    
    print("=" * 100)
    print(f"\nTotal: {len(repos)} repositories\n")
    
    # Print detailed info for top 3
    print("📋 Top 3 Details:\n")
    for i, repo in enumerate(repos[:3], 1):
        print(f"{i}. **{repo['full_name']}**")
        print(f"   ⭐ {format_number(repo['stargazers_count'])} stars | "
              f"🍴 {format_number(repo['forks_count'])} forks | "
              f"👀 {format_number(repo.get('watchers_count', 0))} watchers")
        if repo.get("description"):
            desc = repo["description"][:100]
            print(f"   📝 {desc}{'...' if len(repo['description']) > 100 else ''}")
        print(f"   🔗 {repo['html_url']}")
        print(f"   📜 License: {repo.get('license', {}).get('name', 'Not specified')}")
        print()


def print_repo_info(info: dict, languages: dict):
    """Print detailed repository information."""
    if not info:
        return
    
    print(f"\n📦 Repository: {info['full_name']}\n")
    print("=" * 60)
    
    print(f"📝 Description: {info.get('description', 'No description')}")
    print(f"🔗 URL: {info['html_url']}")
    print()
    
    print("📊 Statistics:")
    print(f"   ⭐ Stars: {format_number(info['stargazers_count'])}")
    print(f"   🍴 Forks: {format_number(info['forks_count'])}")
    print(f"   👀 Watchers: {format_number(info['subscribers_count'])}")
    print(f"   🐛 Open Issues: {info['open_issues_count']}")
    print()
    
    print("📅 Dates:")
    print(f"   Created: {format_date(info['created_at'])}")
    print(f"   Updated: {format_date(info['updated_at'])}")
    print(f"   Pushed: {format_date(info['pushed_at'])}")
    print()
    
    if languages:
        total = sum(languages.values())
        print("💻 Languages:")
        for lang, bytes_count in sorted(languages.items(), key=lambda x: -x[1]):
            pct = (bytes_count / total) * 100
            if pct >= 1:
                print(f"   {lang}: {pct:.1f}%")
    print()
    
    print(f"📜 License: {info.get('license', {}).get('name', 'Not specified')}")
    print(f"🏷️  Topics: {', '.join(info.get('topics', [])) or 'None'}")
    print()
    
    if info.get("homepage"):
        print(f"🌐 Homepage: {info['homepage']}")


def analyze_for_adoption(repos: list):
    """Analyze repositories for adoption suitability."""
    if not repos:
        return
    
    print("\n📈 Adoption Analysis\n")
    print("-" * 60)
    
    for repo in repos[:5]:
        score = 0
        notes = []
        
        # Stars (max 30 points)
        stars = repo["stargazers_count"]
        if stars >= 10000:
            score += 30
            notes.append("✅ Very popular (10K+ stars)")
        elif stars >= 1000:
            score += 20
            notes.append("✅ Popular (1K+ stars)")
        elif stars >= 100:
            score += 10
            notes.append("⚠️ Moderate popularity")
        else:
            notes.append("⚠️ Low popularity")
        
        # Recent activity (max 20 points)
        pushed = repo.get("pushed_at", "")
        if pushed:
            pushed_date = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
            days_ago = (datetime.now(pushed_date.tzinfo) - pushed_date).days
            if days_ago <= 30:
                score += 20
                notes.append("✅ Active (updated <30 days)")
            elif days_ago <= 180:
                score += 10
                notes.append("⚠️ Moderately active")
            else:
                notes.append("❌ Stale (>6 months)")
        
        # License (max 20 points)
        license_name = repo.get("license", {}).get("spdx_id", "")
        if license_name in ["MIT", "Apache-2.0", "BSD-3-Clause"]:
            score += 20
            notes.append(f"✅ Permissive license ({license_name})")
        elif license_name:
            score += 10
            notes.append(f"⚠️ License: {license_name}")
        else:
            notes.append("❌ No license specified")
        
        # Issues ratio (max 15 points)
        open_issues = repo.get("open_issues_count", 0)
        if stars > 0:
            ratio = open_issues / stars
            if ratio < 0.01:
                score += 15
                notes.append("✅ Low issue ratio")
            elif ratio < 0.05:
                score += 10
                notes.append("⚠️ Moderate issues")
            else:
                notes.append("❌ High issue count")
        
        # Forks (max 15 points)
        forks = repo["forks_count"]
        if forks >= 500:
            score += 15
            notes.append("✅ Well-forked (community)")
        elif forks >= 50:
            score += 10
        
        print(f"\n**{repo['full_name']}** - Score: {score}/100")
        for note in notes:
            print(f"   {note}")
    
    print("\n" + "-" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Research technologies and GitHub repositories"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search repositories")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--lang", "-l", help="Programming language filter")
    search_parser.add_argument("--limit", "-n", type=int, default=10, help="Number of results")
    search_parser.add_argument("--analyze", "-a", action="store_true", help="Include adoption analysis")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get repository details")
    info_parser.add_argument("repo", help="Repository (owner/repo)")
    
    # Default to search if no command
    args, remaining = parser.parse_known_args()
    
    if args.command == "search":
        repos = search_repositories(args.query, args.lang, args.limit)
        print_search_results(repos, args.query)
        if args.analyze:
            analyze_for_adoption(repos)
    
    elif args.command == "info":
        parts = args.repo.split("/")
        if len(parts) != 2:
            print("❌ Repository must be in format: owner/repo")
            sys.exit(1)
        
        owner, repo = parts
        info = get_repo_info(owner, repo)
        languages = get_repo_languages(owner, repo)
        print_repo_info(info, languages)
    
    elif remaining:
        # Default to search if query provided without command
        repos = search_repositories(remaining[0], None, 10)
        print_search_results(repos, remaining[0])
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
