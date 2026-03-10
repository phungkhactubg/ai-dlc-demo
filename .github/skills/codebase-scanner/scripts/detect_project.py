#!/usr/bin/env python3
"""
Project Detector

Detects project type, languages, frameworks, and architecture patterns.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class ProjectDetector:
    """Detects project characteristics from file patterns and config files."""
    
    # Language detection by file extension
    LANGUAGE_EXTENSIONS = {
        ".go": "Go",
        ".py": "Python",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".java": "Java",
        ".kt": "Kotlin",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".cs": "C#",
        ".cpp": "C++",
        ".c": "C",
        ".swift": "Swift",
        ".scala": "Scala",
        ".ex": "Elixir",
        ".exs": "Elixir",
    }
    
    # Framework detection by config files
    FRAMEWORK_CONFIGS = {
        # Go
        "go.mod": ("Go", "Go Modules"),
        
        # JavaScript/TypeScript
        "package.json": ("JavaScript", None),  # Need to parse content
        "tsconfig.json": ("TypeScript", None),
        "next.config.js": ("JavaScript", "Next.js"),
        "next.config.mjs": ("JavaScript", "Next.js"),
        "next.config.ts": ("TypeScript", "Next.js"),
        "vite.config.ts": ("TypeScript", "Vite"),
        "vite.config.js": ("JavaScript", "Vite"),
        "angular.json": ("TypeScript", "Angular"),
        "vue.config.js": ("JavaScript", "Vue"),
        "nuxt.config.js": ("JavaScript", "Nuxt"),
        "remix.config.js": ("JavaScript", "Remix"),
        "astro.config.mjs": ("JavaScript", "Astro"),
        
        # Python
        "requirements.txt": ("Python", None),
        "pyproject.toml": ("Python", None),
        "setup.py": ("Python", None),
        "Pipfile": ("Python", "Pipenv"),
        "poetry.lock": ("Python", "Poetry"),
        "manage.py": ("Python", "Django"),
        
        # Java
        "pom.xml": ("Java", "Maven"),
        "build.gradle": ("Java", "Gradle"),
        "build.gradle.kts": ("Kotlin", "Gradle"),
        
        # Ruby
        "Gemfile": ("Ruby", "Bundler"),
        "Rakefile": ("Ruby", "Rake"),
        
        # Rust
        "Cargo.toml": ("Rust", "Cargo"),
        
        # PHP
        "composer.json": ("PHP", "Composer"),
        
        # .NET
        "*.csproj": ("C#", ".NET"),
        "*.fsproj": ("F#", ".NET"),
        "*.sln": ("C#", ".NET Solution"),
        
        # C/C++
        "CMakeLists.txt": ("C++", "CMake"),
        "Makefile": (None, "Make"),
        "conanfile.txt": ("C++", "Conan"),
        "vcpkg.json": ("C++", "vcpkg"),
        
        # Docker/Container
        "Dockerfile": (None, "Docker"),
        "docker-compose.yml": (None, "Docker Compose"),
        "docker-compose.yaml": (None, "Docker Compose"),
    }
    
    # Architecture patterns
    ARCHITECTURE_PATTERNS = {
        "clean_architecture": [
            ("features/*/models", "features/*/services", "features/*/repositories", "features/*/controllers"),
            ("domain", "application", "infrastructure", "presentation"),
            ("entities", "use_cases", "interface_adapters", "frameworks"),
        ],
        "mvc": [
            ("models", "views", "controllers"),
            ("Models", "Views", "Controllers"),
        ],
        "mvvm": [
            ("models", "views", "viewmodels"),
            ("Models", "Views", "ViewModels"),
        ],
        "hexagonal": [
            ("domain", "ports", "adapters"),
            ("core", "ports", "adapters"),
        ],
        "ddd": [
            ("domain", "application", "infrastructure"),
            ("Domain", "Application", "Infrastructure"),
        ],
        "feature_sliced": [
            ("app", "processes", "pages", "widgets", "features", "entities", "shared"),
            ("src/app", "src/features", "src/shared"),
        ],
        "microservices": [
            ("services/*", "api-gateway"),
            ("cmd/*", "internal/*", "pkg/*"),
        ],
    }
    
    def __init__(self, root_dir: Path, excludes: List[str], verbose: bool = False):
        self.root_dir = Path(root_dir)
        self.excludes = excludes
        self.verbose = verbose
    
    def log(self, message: str):
        if self.verbose:
            print(f"   [detect] {message}")
    
    def detect(self) -> Dict:
        """Detect all project characteristics."""
        result = {
            "type": "unknown",
            "languages": [],
            "frameworks": [],
            "architecture": None,
            "build_system": None,
            "package_manager": None,
            "test_framework": None,
            "ci_cd": None,
            "database": None,
            "config_files": [],
        }
        
        # Detect languages from file extensions
        languages = self._detect_languages()
        result["languages"] = list(languages)
        
        # Detect frameworks from config files
        frameworks, configs = self._detect_frameworks()
        result["frameworks"] = list(frameworks)
        result["config_files"] = configs
        
        # Detect architecture pattern
        result["architecture"] = self._detect_architecture()
        
        # Detect project type
        result["type"] = self._determine_project_type(result)
        
        # Detect additional tools
        result["build_system"] = self._detect_build_system()
        result["package_manager"] = self._detect_package_manager()
        result["test_framework"] = self._detect_test_framework()
        result["ci_cd"] = self._detect_ci_cd()
        result["database"] = self._detect_database()
        
        # Parse package.json for more details if exists
        self._parse_package_json(result)
        
        # Parse go.mod for more details if exists
        self._parse_go_mod(result)
        
        return result
    
    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded."""
        path_str = str(path)
        for pattern in self.excludes:
            if pattern in path_str:
                return True
        return False
    
    def _detect_languages(self) -> Set[str]:
        """Detect languages from file extensions."""
        languages = set()
        
        for ext, language in self.LANGUAGE_EXTENSIONS.items():
            # Quick check - just find if any file exists with this extension
            for path in self.root_dir.rglob(f"*{ext}"):
                if not self._should_exclude(path):
                    languages.add(language)
                    self.log(f"Found {language} (from {path.name})")
                    break
        
        return languages
    
    def _detect_frameworks(self) -> Tuple[Set[str], List[Dict]]:
        """Detect frameworks from config files."""
        frameworks = set()
        configs = []
        
        for config_file, (lang, framework) in self.FRAMEWORK_CONFIGS.items():
            # Handle glob patterns
            if "*" in config_file:
                matches = list(self.root_dir.glob(config_file))
            else:
                match = self.root_dir / config_file
                matches = [match] if match.exists() else []
            
            for match in matches:
                if match.exists() and not self._should_exclude(match):
                    if framework:
                        frameworks.add(framework)
                        self.log(f"Found {framework} (from {match.name})")
                    configs.append({
                        "file": str(match.relative_to(self.root_dir)),
                        "language": lang,
                        "framework": framework,
                    })
        
        return frameworks, configs
    
    def _detect_architecture(self) -> Optional[str]:
        """Detect architecture pattern from directory structure."""
        for arch_name, patterns in self.ARCHITECTURE_PATTERNS.items():
            for pattern_set in patterns:
                match_count = 0
                for pattern in pattern_set:
                    if "*" in pattern:
                        matches = list(self.root_dir.glob(pattern))
                        if matches:
                            match_count += 1
                    else:
                        if (self.root_dir / pattern).exists():
                            match_count += 1
                
                # If most patterns match, consider it a match
                if match_count >= len(pattern_set) * 0.7:
                    self.log(f"Detected architecture: {arch_name}")
                    return arch_name
        
        return None
    
    def _determine_project_type(self, info: Dict) -> str:
        """Determine overall project type."""
        languages = info.get("languages", [])
        frameworks = info.get("frameworks", [])
        
        # Check for specific project types
        if "Next.js" in frameworks or "React" in frameworks:
            if "Go" in languages:
                return "Full-Stack (Go + React)"
            elif "Python" in languages:
                return "Full-Stack (Python + React)"
            return "React Frontend"
        
        if "Vue" in frameworks or "Angular" in frameworks:
            return "Frontend SPA"
        
        if "Django" in frameworks or "Flask" in frameworks or "FastAPI" in frameworks:
            return "Python Backend"
        
        if "Go" in languages and len(languages) == 1:
            return "Go Backend"
        
        if "Spring" in frameworks:
            return "Java Backend"
        
        if "Rust" in languages:
            return "Rust Application"
        
        if len(languages) > 1:
            return "Multi-Language Project"
        
        if len(languages) == 1:
            return f"{languages[0]} Project"
        
        return "Unknown"
    
    def _detect_build_system(self) -> Optional[str]:
        """Detect build system."""
        checks = [
            ("Makefile", "Make"),
            ("CMakeLists.txt", "CMake"),
            ("build.gradle", "Gradle"),
            ("build.gradle.kts", "Gradle"),
            ("pom.xml", "Maven"),
            ("meson.build", "Meson"),
            ("BUILD", "Bazel"),
            ("WORKSPACE", "Bazel"),
        ]
        
        for file, system in checks:
            if (self.root_dir / file).exists():
                return system
        return None
    
    def _detect_package_manager(self) -> Optional[str]:
        """Detect package manager."""
        checks = [
            ("pnpm-lock.yaml", "pnpm"),
            ("yarn.lock", "yarn"),
            ("package-lock.json", "npm"),
            ("bun.lockb", "bun"),
            ("poetry.lock", "poetry"),
            ("Pipfile.lock", "pipenv"),
            ("go.sum", "go modules"),
            ("Cargo.lock", "cargo"),
        ]
        
        for file, manager in checks:
            if (self.root_dir / file).exists():
                return manager
        return None
    
    def _detect_test_framework(self) -> Optional[str]:
        """Detect test framework."""
        frameworks = []
        
        # JavaScript/TypeScript
        if (self.root_dir / "jest.config.js").exists() or (self.root_dir / "jest.config.ts").exists():
            frameworks.append("Jest")
        if (self.root_dir / "vitest.config.ts").exists():
            frameworks.append("Vitest")
        if (self.root_dir / "cypress.config.js").exists() or (self.root_dir / "cypress.config.ts").exists():
            frameworks.append("Cypress")
        if (self.root_dir / "playwright.config.ts").exists():
            frameworks.append("Playwright")
        
        # Python
        if (self.root_dir / "pytest.ini").exists() or (self.root_dir / "conftest.py").exists():
            frameworks.append("pytest")
        
        # Go - check for *_test.go files
        if any(self.root_dir.rglob("*_test.go")):
            frameworks.append("Go testing")
        
        return ", ".join(frameworks) if frameworks else None
    
    def _detect_ci_cd(self) -> Optional[str]:
        """Detect CI/CD system."""
        checks = [
            (".github/workflows", "GitHub Actions"),
            (".gitlab-ci.yml", "GitLab CI"),
            ("Jenkinsfile", "Jenkins"),
            (".circleci", "CircleCI"),
            (".travis.yml", "Travis CI"),
            ("azure-pipelines.yml", "Azure DevOps"),
            ("bitbucket-pipelines.yml", "Bitbucket Pipelines"),
        ]
        
        systems = []
        for path, system in checks:
            full_path = self.root_dir / path
            if full_path.exists():
                systems.append(system)
        
        return ", ".join(systems) if systems else None
    
    def _detect_database(self) -> Optional[str]:
        """Detect database from config or code patterns."""
        databases = []
        
        # Check for common database config files
        if (self.root_dir / "prisma").exists():
            databases.append("Prisma")
        
        # Check docker-compose for database services
        compose_files = ["docker-compose.yml", "docker-compose.yaml"]
        for compose_file in compose_files:
            compose_path = self.root_dir / compose_file
            if compose_path.exists():
                content = compose_path.read_text()
                if "mongo" in content.lower():
                    databases.append("MongoDB")
                if "postgres" in content.lower() or "postgresql" in content.lower():
                    databases.append("PostgreSQL")
                if "mysql" in content.lower():
                    databases.append("MySQL")
                if "redis" in content.lower():
                    databases.append("Redis")
        
        return ", ".join(databases) if databases else None
    
    def _parse_package_json(self, result: Dict):
        """Parse package.json for additional details."""
        package_path = self.root_dir / "package.json"
        if not package_path.exists():
            return
        
        try:
            with open(package_path, "r", encoding="utf-8") as f:
                package = json.load(f)
            
            deps = {}
            deps.update(package.get("dependencies", {}))
            deps.update(package.get("devDependencies", {}))
            
            # Detect frameworks from dependencies
            framework_deps = {
                "react": "React",
                "react-dom": "React",
                "next": "Next.js",
                "vue": "Vue",
                "nuxt": "Nuxt",
                "@angular/core": "Angular",
                "svelte": "Svelte",
                "express": "Express",
                "fastify": "Fastify",
                "koa": "Koa",
                "hapi": "Hapi",
                "nestjs": "NestJS",
                "@nestjs/core": "NestJS",
            }
            
            for dep, framework in framework_deps.items():
                if dep in deps and framework not in result["frameworks"]:
                    result["frameworks"].append(framework)
            
            # Detect UI libraries
            ui_deps = {
                "@mui/material": "MUI",
                "@chakra-ui/react": "Chakra UI",
                "antd": "Ant Design",
                "@mantine/core": "Mantine",
                "tailwindcss": "Tailwind CSS",
            }
            
            for dep, ui in ui_deps.items():
                if dep in deps and ui not in result["frameworks"]:
                    result["frameworks"].append(ui)
            
            # Detect state management
            state_deps = {
                "zustand": "Zustand",
                "redux": "Redux",
                "@reduxjs/toolkit": "Redux Toolkit",
                "mobx": "MobX",
                "jotai": "Jotai",
                "recoil": "Recoil",
            }
            
            for dep, state in state_deps.items():
                if dep in deps and state not in result["frameworks"]:
                    result["frameworks"].append(state)
            
        except Exception as e:
            self.log(f"Error parsing package.json: {e}")
    
    def _parse_go_mod(self, result: Dict):
        """Parse go.mod for additional details."""
        go_mod_path = self.root_dir / "go.mod"
        if not go_mod_path.exists():
            return
        
        try:
            content = go_mod_path.read_text()
            
            # Detect frameworks from require statements
            framework_patterns = {
                r"github\.com/labstack/echo": "Echo",
                r"github\.com/gin-gonic/gin": "Gin",
                r"github\.com/go-chi/chi": "Chi",
                r"github\.com/gorilla/mux": "Gorilla Mux",
                r"github\.com/gofiber/fiber": "Fiber",
                r"github\.com/grpc/grpc-go": "gRPC",
                r"gorm\.io/gorm": "GORM",
                r"go\.mongodb\.org/mongo-driver": "MongoDB Driver",
                r"github\.com/jmoiron/sqlx": "sqlx",
            }
            
            for pattern, framework in framework_patterns.items():
                if re.search(pattern, content) and framework not in result["frameworks"]:
                    result["frameworks"].append(framework)
            
        except Exception as e:
            self.log(f"Error parsing go.mod: {e}")


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Detect project characteristics")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    detector = ProjectDetector(Path.cwd(), [], args.verbose)
    result = detector.detect()
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"Saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))
