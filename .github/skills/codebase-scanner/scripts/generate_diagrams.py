#!/usr/bin/env python3
"""
Diagram Generator - Generates Mermaid diagrams from scan data.
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class DiagramGenerator:
    """Generates Mermaid diagrams from scan results."""
    
    def __init__(self, output_dir: Path, verbose: bool = False):
        self.output_dir = Path(output_dir)
        self.verbose = verbose
    
    def log(self, message: str):
        if self.verbose:
            print(f"   [diagrams] {message}")
    
    def generate(self, scan_data: Dict) -> List[str]:
        """Generate all diagram files."""
        generated = []
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate architecture diagram
        self._generate_architecture_diagram(scan_data)
        generated.append("architecture.mmd")
        
        # Generate dependency diagram
        if scan_data.get("dependencies"):
            self._generate_dependency_diagram(scan_data)
            generated.append("dependencies.mmd")
        
        # Generate data flow diagram
        if scan_data.get("apis"):
            self._generate_data_flow_diagram(scan_data)
            generated.append("data-flow.mmd")
        
        return generated
    
    def _generate_architecture_diagram(self, scan_data: Dict):
        """Generate architecture overview diagram."""
        project = scan_data.get("project_info", {})
        structure = scan_data.get("structure", {})
        
        content = """%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#4f46e5'}}}%%
graph TB
    subgraph Project["📦 Project Architecture"]
"""
        # Add layers based on detected architecture
        arch = project.get("architecture", "")
        
        if arch == "clean_architecture":
            content += """        subgraph Presentation["🎨 Presentation Layer"]
            Controllers[Controllers]
            Routes[Routes]
        end
        subgraph Application["⚙️ Application Layer"]
            Services[Services]
            UseCases[Use Cases]
        end
        subgraph Domain["🏛️ Domain Layer"]
            Models[Models]
            Entities[Entities]
        end
        subgraph Infrastructure["🔧 Infrastructure Layer"]
            Repositories[Repositories]
            External[External Services]
        end
        
        Presentation --> Application
        Application --> Domain
        Application --> Infrastructure
        Infrastructure --> Domain
"""
        elif arch == "feature_sliced":
            content += """        subgraph App["📱 App"]
            AppLayer[App Layer]
        end
        subgraph Features["✨ Features"]
            FeatureModules[Feature Modules]
        end
        subgraph Shared["🔄 Shared"]
            SharedLib[Shared Libraries]
        end
        
        App --> Features
        Features --> Shared
"""
        else:
            # Generic structure based on detected modules
            modules = structure.get("modules", [])[:8]
            for i, mod in enumerate(modules):
                name = mod.get("name", f"Module{i}")
                safe_name = name.replace("-", "_").replace(".", "_")
                content += f"        {safe_name}[{name}]\n"
        
        content += "    end\n"
        
        # Add external dependencies
        frameworks = project.get("frameworks", [])[:5]
        if frameworks:
            content += "\n    subgraph External[\"🌐 External\"]\n"
            for fw in frameworks:
                safe_fw = fw.replace("-", "_").replace(".", "_").replace(" ", "_")
                content += f"        {safe_fw}[{fw}]\n"
            content += "    end\n"
        
        self._write_file("architecture.mmd", content)
    
    def _generate_dependency_diagram(self, scan_data: Dict):
        """Generate module dependency diagram."""
        deps = scan_data.get("dependencies", {})
        graph = deps.get("dependency_graph", {})
        
        content = """%%{init: {'theme': 'base'}}%%
graph LR
    subgraph Dependencies["🔗 Module Dependencies"]
"""
        # Add nodes
        nodes = graph.get("nodes", [])[:15]
        for node in nodes:
            node_id = self._safe_id(node.get("id", ""))
            name = node.get("name", node_id)[:20]
            content += f"        {node_id}[\"{name}\"]\n"
        
        content += "    end\n\n"
        
        # Add edges
        edges = graph.get("edges", [])[:30]
        for edge in edges:
            source = self._safe_id(edge.get("source", ""))
            target = self._safe_id(edge.get("target", ""))
            if source and target and source != target:
                content += f"    {source} --> {target}\n"
        
        self._write_file("dependencies.mmd", content)
    
    def _generate_data_flow_diagram(self, scan_data: Dict):
        """Generate data flow diagram based on APIs."""
        apis = scan_data.get("apis", {})
        endpoints = apis.get("endpoints", [])[:20]
        
        content = """%%{init: {'theme': 'base'}}%%
sequenceDiagram
    participant Client
    participant API
    participant Service
    participant Database
    
"""
        # Group endpoints by method
        for ep in endpoints[:10]:
            method = ep.get("method", "GET")
            path = ep.get("path", "/")[:30]
            handler = ep.get("handler", "handler")[:15]
            
            content += f"    Client->>API: {method} {path}\n"
            content += f"    API->>Service: {handler}()\n"
            content += f"    Service->>Database: Query\n"
            content += f"    Database-->>Service: Result\n"
            content += f"    Service-->>API: Response\n"
            content += f"    API-->>Client: JSON\n"
            content += "    \n"
        
        self._write_file("data-flow.mmd", content)
    
    def _safe_id(self, id_str: str) -> str:
        """Convert string to safe Mermaid ID."""
        if not id_str:
            return "unknown"
        safe = id_str.replace("/", "_").replace("\\", "_")
        safe = safe.replace(".", "_").replace("-", "_")
        safe = safe.replace(" ", "_").replace(":", "_")
        # Ensure it starts with a letter
        if safe and safe[0].isdigit():
            safe = "m_" + safe
        return safe[:30] if safe else "unknown"
    
    def _write_file(self, filename: str, content: str):
        """Write content to file."""
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        self.log(f"Generated: {filepath}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True, help="Input directory with JSON files")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    scan_data = {}
    
    for json_file in ["project_info.json", "structure.json", "dependencies.json", "apis.json"]:
        path = input_dir / json_file
        if path.exists():
            with open(path) as f:
                key = json_file.replace(".json", "")
                scan_data[key] = json.load(f)
    
    gen = DiagramGenerator(Path(args.output), args.verbose)
    gen.generate(scan_data)
