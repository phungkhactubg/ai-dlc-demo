#!/usr/bin/env python3
"""
Codebase Scanner v2.0 - Main Orchestrator

Scans any codebase and generates hierarchical documentation for AI Agents.
Supports incremental scanning, semantic analysis, and massive codebases (10M+ LOC).

Usage:
    python scan_codebase.py [options]
    
Options:
    --full              Full scan with all L0-L3 levels + semantic analysis
    --quick             Quick scan (L0 + L1 only)
    --incremental       Only scan changed files
    --git-diff BRANCH   Scan files changed vs branch
    --component PATH    Deep dive into specific component
    --semantic          Run semantic analysis only
    --output-dir DIR    Output directory (default: project-documentation/codebase-docs)
    --verbose           Verbose output
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set

# Add script directory to path for imports
SCRIPT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

from detect_project import ProjectDetector
from analyze_structure import StructureAnalyzer
from analyze_dependencies import DependencyAnalyzer
from extract_apis import APIExtractor
from generate_docs import DocumentationGenerator
from generate_diagrams import DiagramGenerator

# v2 imports
try:
    from generate_hierarchical_docs import HierarchicalDocsGenerator
    from scan_incremental import IncrementalScanner
    from scan_semantic import SemanticScanner
    HAS_V2 = True
except ImportError:
    HAS_V2 = False



class CodebaseScanner:
    """Main orchestrator for codebase scanning."""
    
    # Default exclude patterns
    DEFAULT_EXCLUDES = [
        "node_modules",
        "vendor",
        ".github",
        "project-documentation/codebase-docs",
        "__pycache__",
        ".venv",
        "venv",
        "dist",
        "build",
        ".next",
        "coverage",
        ".nyc_output",
        "*.min.js",
        "*.min.css",
        "*.map",
        ".idea",
        ".vscode",
        "*.log",
        "tmp",
        "temp",
    ]
    
    def __init__(
        self,
        root_dir: str = ".",
        output_dir: str = "project-documentation/codebase-docs",
        depth: int = 3,
        includes: Optional[List[str]] = None,
        excludes: Optional[List[str]] = None,
        quick_mode: bool = False,
        verbose: bool = False
    ):
        self.root_dir = Path(root_dir).absolute()
        self.output_dir = Path(output_dir)
        self.depth = depth
        self.includes = includes or []
        self.excludes = self.DEFAULT_EXCLUDES + (excludes or [])
        self.quick_mode = quick_mode
        self.verbose = verbose
        
        # Initialize sub-scanners
        self.detector = ProjectDetector(self.root_dir, self.excludes, self.verbose)
        self.structure_analyzer = StructureAnalyzer(self.root_dir, self.excludes, self.depth, self.verbose)
        self.dependency_analyzer = DependencyAnalyzer(self.root_dir, self.excludes, self.verbose)
        self.api_extractor = APIExtractor(self.root_dir, self.excludes, self.verbose)
        self.doc_generator = DocumentationGenerator(self.output_dir, self.verbose)
        self.diagram_generator = DiagramGenerator(self.output_dir / "diagrams", self.verbose)
        
        # Scan results storage
        self.project_info: Dict = {}
        self.structure: Dict = {}
        self.dependencies: Dict = {}
        self.apis: Dict = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode is enabled."""
        if self.verbose or level == "ERROR":
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def ensure_output_dir(self):
        """Create output directory structure."""
        dirs = [
            self.output_dir,
            self.output_dir / "components",
            self.output_dir / "diagrams",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        self.log(f"Output directory created: {self.output_dir}")
    
    def run_full_scan(self) -> Dict:
        """Run complete codebase scan."""
        print("\n" + "="*60)
        print("  CODEBASE SCANNER - Full Scan")
        print("="*60 + "\n")
        
        self.ensure_output_dir()
        
        # Phase 1: Project Detection
        print("📋 Phase 1: Project Detection...")
        self.project_info = self.detector.detect()
        self._save_json("project_info.json", self.project_info)
        self._print_project_summary()
        
        # Phase 2: Structure Analysis
        print("\n📂 Phase 2: Structure Analysis...")
        self.structure = self.structure_analyzer.analyze()
        self._save_json("structure.json", self.structure)
        print(f"   Found {self.structure.get('total_files', 0)} files in {self.structure.get('total_dirs', 0)} directories")
        
        if not self.quick_mode:
            # Phase 3: Dependency Analysis
            print("\n🔗 Phase 3: Dependency Analysis...")
            self.dependencies = self.dependency_analyzer.analyze(self.project_info)
            self._save_json("dependencies.json", self.dependencies)
            print(f"   Mapped {len(self.dependencies.get('modules', {}))} modules")
            
            # Phase 4: API Extraction
            print("\n🌐 Phase 4: API Extraction...")
            self.apis = self.api_extractor.extract(self.project_info)
            self._save_json("apis.json", self.apis)
            print(f"   Found {len(self.apis.get('endpoints', []))} API endpoints")
        
        # Phase 5: Documentation Generation
        print("\n📝 Phase 5: Documentation Generation...")
        scan_data = {
            "project_info": self.project_info,
            "structure": self.structure,
            "dependencies": self.dependencies if not self.quick_mode else {},
            "apis": self.apis if not self.quick_mode else {},
        }
        generated_files = self.doc_generator.generate(scan_data, self.quick_mode)
        print(f"   Generated {len(generated_files)} documentation files")
        
        # Phase 6: Diagram Generation
        print("\n📊 Phase 6: Diagram Generation...")
        diagram_files = self.diagram_generator.generate(scan_data)
        print(f"   Generated {len(diagram_files)} diagrams")
        
        # Summary
        self._print_summary(generated_files + diagram_files)
        
        return scan_data
    
    def run_quick_scan(self) -> Dict:
        """Run quick structure-only scan."""
        self.quick_mode = True
        return self.run_full_scan()
    
    def scan_component(self, component_path: str) -> Dict:
        """Deep dive into specific component."""
        print("\n" + "="*60)
        print(f"  CODEBASE SCANNER - Component Deep Dive")
        print(f"  Target: {component_path}")
        print("="*60 + "\n")
        
        component_full_path = self.root_dir / component_path
        if not component_full_path.exists():
            print(f"❌ Error: Component path does not exist: {component_path}")
            return {}
        
        self.ensure_output_dir()
        
        # Create component-specific analyzer
        comp_analyzer = StructureAnalyzer(
            component_full_path, 
            self.excludes, 
            depth=10,  # Deep scan for components
            verbose=self.verbose
        )
        
        print("📂 Analyzing component structure...")
        structure = comp_analyzer.analyze()
        
        print("🔗 Analyzing component dependencies...")
        # Detect project first for language info
        self.project_info = self.detector.detect()
        comp_dep_analyzer = DependencyAnalyzer(
            component_full_path,
            self.excludes,
            self.verbose
        )
        dependencies = comp_dep_analyzer.analyze(self.project_info)
        
        print("🌐 Extracting component APIs...")
        comp_api_extractor = APIExtractor(
            component_full_path,
            self.excludes,
            self.verbose
        )
        apis = comp_api_extractor.extract(self.project_info)
        
        # Generate component documentation
        print("📝 Generating component documentation...")
        component_data = {
            "name": Path(component_path).name,
            "path": component_path,
            "structure": structure,
            "dependencies": dependencies,
            "apis": apis,
        }
        
        output_file = self.output_dir / "components" / f"{component_data['name']}.md"
        self.doc_generator.generate_component_doc(component_data, output_file)
        
        print(f"\n✅ Component documentation generated: {output_file}")
        return component_data
    
    def _save_json(self, filename: str, data: Dict):
        """Save data as JSON file."""
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        self.log(f"Saved: {filepath}")
    
    def _print_project_summary(self):
        """Print detected project summary."""
        print(f"   Project Type: {self.project_info.get('type', 'Unknown')}")
        print(f"   Languages: {', '.join(self.project_info.get('languages', []))}")
        print(f"   Frameworks: {', '.join(self.project_info.get('frameworks', []))}")
        if self.project_info.get('architecture'):
            print(f"   Architecture: {self.project_info.get('architecture')}")
    
    def _print_summary(self, generated_files: List[str]):
        """Print final summary."""
        print("\n" + "="*60)
        print("  SCAN COMPLETE")
        print("="*60)
        print(f"\n📁 Output Directory: {self.output_dir}")
        print("\n📄 Generated Files:")
        for f in sorted(generated_files):
            print(f"   • {f}")
        print("\n💡 Next Steps:")
        print("   • Review ARCHITECTURE.md for high-level overview")
        print("   • Check COMPONENT_MAP.md for detailed structure")
        print("   • Use /scan-component <path> for deep dives")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Codebase Scanner v2.0 - Generate documentation for AI Agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Mode arguments (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--full",
        action="store_true",
        help="Full scan with L0-L3 levels + semantic analysis"
    )
    mode_group.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick scan (L0 + L1 only)"
    )
    mode_group.add_argument(
        "--incremental",
        action="store_true",
        help="Only scan changed files since last scan"
    )
    mode_group.add_argument(
        "--git-diff",
        metavar="BRANCH",
        help="Scan files changed vs branch"
    )
    mode_group.add_argument(
        "--component", "-c",
        metavar="PATH",
        help="Deep dive into specific component"
    )
    mode_group.add_argument(
        "--semantic",
        action="store_true",
        help="Run semantic analysis only"
    )
    
    # Other arguments
    parser.add_argument(
        "--output-dir", "-o",
        default="project-documentation/codebase-docs",
        help="Output directory (default: project-documentation/codebase-docs)"
    )
    parser.add_argument(
        "--depth", "-d",
        type=int,
        default=3,
        help="Scan depth (default: 3)"
    )
    parser.add_argument(
        "--exclude", "-e",
        action="append",
        default=[],
        help="Glob patterns to exclude"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        # Auto-append repo name if using default output path
        if args.output_dir == "project-documentation/codebase-docs":
            repo_name = Path.cwd().name
            args.output_dir = str(Path(args.output_dir) / repo_name)
            print(f"ℹ️  Auto-detected repository: {repo_name}")
            print(f"ℹ️  Output directory set to: {args.output_dir}")

        # v2 Modes
        if args.semantic:
            if not HAS_V2:
                print("❌ Semantic analysis requires v2 scripts. Run full install.")
                return 1
            print("\n🔍 Running semantic analysis...")
            scanner = SemanticScanner(Path.cwd(), Path(args.output_dir), args.verbose)
            scanner.scan_all()
            return 0
        
        if args.incremental:
            if not HAS_V2:
                print("❌ Incremental scanning requires v2 scripts.")
                return 1
            print("\n🔄 Running incremental scan...")
            scanner = IncrementalScanner(Path.cwd(), Path(args.output_dir), args.verbose)
            changed = scanner.scan_diff()
            scanner.update_docs(changed)
            return 0
        
        if args.git_diff:
            if not HAS_V2:
                print("❌ Git diff scanning requires v2 scripts.")
                return 1
            print(f"\n🔀 Scanning git diff vs {args.git_diff}...")
            scanner = IncrementalScanner(Path.cwd(), Path(args.output_dir), args.verbose)
            changed = scanner.scan_git_diff(args.git_diff)
            scanner.update_docs(changed)
            return 0
        
        # Standard scanner for other modes
        scanner = CodebaseScanner(
            root_dir=".",
            output_dir=args.output_dir,
            depth=args.depth,
            excludes=args.exclude,
            quick_mode=args.quick,
            verbose=args.verbose
        )
        
        if args.component:
            scanner.scan_component(args.component)
        elif args.quick:
            scanner.run_quick_scan()
        elif args.full:
            # Full scan: standard + hierarchical + semantic
            scan_data = scanner.run_full_scan()
            
            if HAS_V2:
                print("\n📚 Generating hierarchical documentation...")
                hier_gen = HierarchicalDocsGenerator(Path(args.output_dir), args.verbose)
                hier_gen.generate(scan_data)
                
                print("\n🔍 Running semantic analysis...")
                sem_scanner = SemanticScanner(Path.cwd(), Path(args.output_dir), args.verbose)
                sem_scanner.scan_all()
        else:
            # Default: standard scan
            scanner.run_full_scan()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Scan interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
