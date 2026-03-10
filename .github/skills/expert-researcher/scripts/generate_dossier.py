#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

INDEX_TEMPLATE = """# Research Dossier: {topic_name}

## 📌 Executive Summary
> [High-level overview of the researched platform/system/technology.]

## 🗺️ Dossier Roadmap
- [Architecture & Internal Modules](ARCHITECTURE.md)
- [Financial Analysis & Business Model](FINANCIALS.md)
- [Regulatory & Legal Roadmap](REGULATORY.md)
- [Ecosystem, Comparisons & Maintenance](ECOSYSTEM.md)
- [Implementation & Deployment Guides](IMPLEMENTATION.md)
- [Risk Audit (Security, Scaling, Geopolitical)](RISKS.md)

### 📦 Deep-Dive Modules (Recursive Analysis)
{module_links}

---

## 🏛️ Strategic Conclusion
> [The final expert verdict. Should we adopt it? What is the primary trade-off?]
"""

ARCH_TEMPLATE = """# Architecture Deep-Dive: {topic_name}
> **⚠️ Technical Forensics Mandate**: All claims must be cited with `file:line` or `function_name` references.

## 🧱 Core Component Architecture

### [Module 1 Name]
- **Source Location**: `path/to/source` (REQUIRED)
- **Primary Interface**: 
  ```go
  // Paste the core interface definition here
  type Service interface {{
      ...
  }}
  ```
- **Internal Logic Flow**:
  1. Input `X` received via `func HandleX()`
  2. Processed by `processor.go` using Algorithm `Y`
  3. Stored in DB via `repo.Save()`

### [Module 2 Name]
...

## 🔄 Critical Data Flows (Trace Analysis)
> [Trace a single request from Entrypoint to Exit.]

1. **Ingress**: `main.go` initializes...
2. **Routing**: `router.go` dispatches to...
3. **Processing**: `service.go` executes...
"""

MODULE_TEMPLATE = """# Module Deep-Dive: {module_name} ({topic_name})
> **⚠️ Engineer-Grade Analysis**: No high-level summaries. Stick to the code.
> **Requirement**: At least 5 specific code citations (file:line) and proof of a **Local Forensic Scan** are required.

## 🔍 Local Scanning Proof
- **Scanner Used**: `scan-project` / `codebase-scanner` / `grep -r`
- **Scan Status**: ✅ COMPLETE
- **Entry Points Identified**: 
    - `file:line` -> `FunctionName()`

## 📂 Source Code Map
- **Directory**: `path/to/module`
- **Key Files**:
    - `core_logic.ext`: Does X... (Cite specific logic lines)
    - `config.ext`: Defines Y... (Cite specific parameters)

## 🧠 Critical Logic & Algorithms
> [Extract the actual algorithm. Don't describe it; show how it works.]

### 1. [Algorithm/Process Name]
- **File**: `path/to/file.ext:L123`
- **Function**: `FunctionName()`
- **Logic Breakdown**:
  ```python
  # Paste ACTUAL source code or Pseudo-code of the critical loop
  while condition:
      process_data()
  ```
- **Edge Case Handling**: Cite the specific lines that handle nulls/timeouts.

## 💾 Core Data Structures
> [What do the major objects look like? Paste the actual code.]

```go
// Paste the struct/class definition from the source
type MajorEntity struct {{
    ID string `json:"id"`
    // ...
}}
```

## ⚙️ Configuration & Tuning
> [What knobs can we turn? Cite the config file.]

| Parameter | Default | Impact | File:Line |
|-----------|---------|--------|-----------|
| `max_connections` | 100 | ... | `config.yaml:12` |
"""

ECOSYSTEM_TEMPLATE = """# Ecosystem & Comparative Analysis: {topic_name}

## 📊 Comparative Landscape
| Aspect | {topic_name} | Candidate B | Candidate C |
|--------|--------------|-------------|-------------|
| **Perf** | | | |
| **Open Source**| | | |
| **Maturity** | | | |

## 👥 Community & Support
- **Maintainer Health**: 
- **GitHub Pulse**: 
- **Bus Factor**: 

## 📈 Alternative Paradigms
- **Option A**: 
- **Option B**: 
"""

IMPL_TEMPLATE = """# Implementation & Deployment Guide: {topic_name}

## 🚀 Quick Setup (The Frictionless Path)
> [Atomic steps to get a "Hello World" or Prototype running.]

## 🔧 Production Configuration
> [Critical settings for performance and stability.]

## 💻 Integration Snippets
> [Mock code or real API examples.]

---

## 🏗️ Architectural Fit (A-Z)
> [How does this integrate into our specific project context?]
"""

RISKS_TEMPLATE = """# Risk & Security Audit: {topic_name}

## 🚨 Critical Risks
- **Risk 1**: 
- **Mitigation**: 

## 🛡️ Security Posture
- **Vulnerability History**: 
- **Auth/AuthZ Model**: 

## ⚖️ Geopolitical & Regulatory
> [Is this technology restricted? Are there GDPR/CFIUS concerns?]

## 📈 Scalability Bottlenecks
> [Where does it break at 10x load?]
"""

FINANCIAL_TEMPLATE = """# Financial Analysis & Business Model: {topic_name}

## 💰 Business Model
- **Revenue Streams**: 
- **Pricing Tiers**: 
- **Funding/Backing**: 

## 📊 Cost Analysis
- **Setup Costs**: 
- **Operational Costs (Cloud/GPU/Ops)**: 
- **Maintenance Overheads**: 

## 📉 ROI & Value Proposition
> [Why does this make financial sense?]
"""

REGULATORY_TEMPLATE = """# Regulatory & Legal Roadmap: {topic_name}

## ⚖️ Legal Status
- **Licensing**: 
- **IP Ownership/Restrictions**: 

## 🛡️ Compliance & Standards
- **GDPR/Data Privacy**: 
- **Regional Restrictions (CFIUS, etc.)**: 
- **Industry Standards**: 

## 🚦 Roadmap to Compliance
> [Steps required for legal readiness in target regions.]
"""

def main():
    parser = argparse.ArgumentParser(description="Generate a Comprehensive Research Dossier Structure")
    parser.add_argument("topic", help="Topic name for the research dossier")
    parser.add_argument("--modules", nargs="+", help="Optional list of modules to deep-dive into initially", default=[])
    parser.add_argument("--dir", default="project-documentation/research", help="Root directory for dossiers")
    
    args = parser.parse_args()
    
    topic_slug = args.topic.lower().replace(" ", "_").replace("-", "_")
    
    # PATH HARDENING (Workspace Sovereignty)
    dossier_path = Path(args.dir) / topic_slug
    if "project-documentation" not in str(dossier_path):
        dossier_path = Path("project-documentation/research") / topic_slug
    
    # Ensure it's absolute so logs are clear
    dossier_path = dossier_path.absolute()
    print(f"🔒 Workspace Sovereignty: Saving research to {dossier_path}")

    if dossier_path.exists():
        print(f"❌ Error: Dossier directory already exists at {dossier_path}")
        sys.exit(1)
        
    dossier_path.mkdir(parents=True, exist_ok=True)
    
    module_links = ""
    for module in args.modules:
        module_slug = module.upper().replace(" ", "_").replace("-", "_")
        module_links += f"- [{module}](MODULE_{module_slug}.md)\n"

    files = {
        "INDEX.md": INDEX_TEMPLATE.format(topic_name=args.topic, module_links=module_links),
        "ARCHITECTURE.md": ARCH_TEMPLATE.format(topic_name=args.topic),
        "FINANCIALS.md": FINANCIAL_TEMPLATE.format(topic_name=args.topic),
        "REGULATORY.md": REGULATORY_TEMPLATE.format(topic_name=args.topic),
        "ECOSYSTEM.md": ECOSYSTEM_TEMPLATE.format(topic_name=args.topic),
        "IMPLEMENTATION.md": IMPL_TEMPLATE.format(topic_name=args.topic),
        "RISKS.md": RISKS_TEMPLATE.format(topic_name=args.topic)
    }
    
    for filename, content in files.items():
        file_path = dossier_path / filename
        file_path.write_text(content, encoding="utf-8")
        print(f"✅ Created: {file_path}")
        
    for module in args.modules:
        module_slug = module.upper().replace(" ", "_").replace("-", "_")
        filename = f"MODULE_{module_slug}.md"
        file_path = dossier_path / filename
        content = MODULE_TEMPLATE.format(module_name=module, topic_name=args.topic)
        file_path.write_text(content, encoding="utf-8")
        print(f"✅ Created Module Report: {file_path}")
        
    print(f"\n🚀 Dossier structure generated successfully for '{args.topic}' at {dossier_path}")

if __name__ == "__main__":
    main()
