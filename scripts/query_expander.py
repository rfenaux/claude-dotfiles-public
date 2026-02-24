#!/usr/bin/env python3
"""
Query Expander for RAG Search
Expands search queries into variants using synonyms, acronyms, and reformulations.

Usage:
    python3 query_expander.py "how does auth work?"
    echo '{"query": "API auth", "context": {...}}' | python3 query_expander.py
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional


def load_config() -> Dict:
    """Load RAG retrieval configuration."""
    config_path = Path.home() / ".claude" / "config" / "rag-retrieval.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {
        "expansion": {
            "enabled": True,
            "max_variants": 3,
            "strategies": ["synonym", "acronym", "reformulate"],
            "min_query_length": 3
        }
    }


def load_synonyms() -> Dict[str, List[str]]:
    """Load synonym dictionary from config."""
    synonyms_path = Path.home() / ".claude" / "config" / "rag-synonyms.json"
    if synonyms_path.exists():
        with open(synonyms_path) as f:
            data = json.load(f)
            return data.get("synonyms", {})

    # Fallback: built-in curated synonyms (~100 entries)
    return {
        "auth": ["authentication", "authorization", "OAuth", "login", "credentials"],
        "authentication": ["auth", "OAuth", "login", "verify", "identity"],
        "API": ["endpoint", "interface", "service", "REST", "integration"],
        "endpoint": ["API", "service", "route", "URL", "interface"],
        "CRM": ["customer-relationship-management", "HubSpot", "Salesforce", "contacts"],
        "HubSpot": ["HS", "CRM", "portal", "hub"],
        "deploy": ["deployment", "release", "rollout", "publish", "ship"],
        "deployment": ["deploy", "release", "production", "launch"],
        "database": ["DB", "datastore", "storage", "persistence", "data-layer"],
        "DB": ["database", "datastore", "SQL", "storage"],
        "bug": ["defect", "issue", "error", "problem", "fault"],
        "issue": ["bug", "ticket", "problem", "defect", "task"],
        "PR": ["pull-request", "merge-request", "code-review", "MR"],
        "pull-request": ["PR", "merge-request", "MR", "code-review"],
        "CI": ["continuous-integration", "pipeline", "automation", "build"],
        "CD": ["continuous-deployment", "continuous-delivery", "pipeline"],
        "pipeline": ["CI/CD", "workflow", "automation", "build-process"],
        "config": ["configuration", "settings", "options", "preferences"],
        "configuration": ["config", "settings", "setup", "options"],
        "workflow": ["process", "automation", "flow", "pipeline", "sequence"],
        "integration": ["connector", "sync", "bridge", "interface", "middleware"],
        "sync": ["synchronization", "integration", "mirror", "replicate"],
        "migration": ["import", "transfer", "ETL", "data-import", "move"],
        "contact": ["person", "lead", "prospect", "customer", "user"],
        "company": ["organization", "account", "business", "firm", "enterprise"],
        "deal": ["opportunity", "sale", "pipeline-item", "prospect"],
        "ticket": ["case", "support-request", "issue", "help-request"],
        "property": ["field", "attribute", "column", "data-point", "custom-field"],
        "field": ["property", "attribute", "column", "data-field"],
        "record": ["object", "entity", "item", "row", "entry"],
        "automation": ["workflow", "trigger", "rule", "sequence", "bot"],
        "report": ["dashboard", "analytics", "metrics", "insights", "visualization"],
        "dashboard": ["report", "analytics", "overview", "summary", "metrics"],
        "error": ["exception", "failure", "bug", "issue", "problem"],
        "permission": ["access", "role", "privilege", "authorization", "rights"],
        "webhook": ["callback", "hook", "event-listener", "notification"],
        "template": ["blueprint", "pattern", "skeleton", "boilerplate"],
        "module": ["component", "package", "library", "plugin", "extension"],
        "function": ["method", "procedure", "routine", "operation", "call"],
        "variable": ["parameter", "attribute", "value", "setting", "option"],
        "cache": ["buffer", "temporary-storage", "memory", "store"],
        "queue": ["buffer", "pipeline", "backlog", "waiting-list"],
        "session": ["connection", "context", "state", "instance"],
        "token": ["credential", "key", "auth-token", "access-token"],
        "schema": ["structure", "model", "definition", "blueprint", "format"],
        "validation": ["verification", "check", "test", "sanity-check"],
        "test": ["check", "validation", "verification", "QA", "testing"],
        "production": ["prod", "live", "release", "deployment"],
        "development": ["dev", "local", "staging", "test-environment"],
        "staging": ["pre-prod", "UAT", "test-environment", "preview"],
        "environment": ["env", "context", "setup", "infrastructure"],
        "server": ["instance", "host", "node", "machine", "backend"],
        "client": ["frontend", "user-interface", "UI", "application"],
        "user": ["customer", "contact", "person", "account", "end-user"],
        "admin": ["administrator", "superuser", "owner", "manager"],
        "role": ["permission", "privilege", "access-level", "authorization"],
        "log": ["record", "trace", "history", "audit-trail", "event-log"],
        "metric": ["KPI", "measurement", "stat", "indicator", "analytics"],
        "performance": ["speed", "optimization", "efficiency", "throughput"],
        "security": ["protection", "safety", "authorization", "encryption"],
        "backup": ["archive", "snapshot", "copy", "restore-point"],
        "restore": ["recovery", "rollback", "revert", "undo"],
    }


def load_acronyms() -> Dict[str, str]:
    """Load acronym expansion map from config."""
    synonyms_path = Path.home() / ".claude" / "config" / "rag-synonyms.json"
    if synonyms_path.exists():
        with open(synonyms_path) as f:
            data = json.load(f)
            return data.get("acronyms", {})

    # Fallback: built-in acronym map (~50 entries)
    return {
        "API": "Application Programming Interface",
        "CRM": "Customer Relationship Management",
        "DB": "Database",
        "PR": "Pull Request",
        "CI": "Continuous Integration",
        "CD": "Continuous Deployment",
        "SaaS": "Software as a Service",
        "SDK": "Software Development Kit",
        "CLI": "Command Line Interface",
        "MCP": "Model Context Protocol",
        "RAG": "Retrieval Augmented Generation",
        "CTM": "Cognitive Task Management",
        "CDP": "Cognitive Delegation Protocol",
        "CSB": "Content Security Buffer",
        "SONA": "Self-Optimizing Neural Archive",
        "SSOT": "Single Source of Truth",
        "ETL": "Extract Transform Load",
        "JWT": "JSON Web Token",
        "OAuth": "Open Authorization",
        "GDPR": "General Data Protection Regulation",
        "SLA": "Service Level Agreement",
        "KPI": "Key Performance Indicator",
        "ROI": "Return on Investment",
        "UAT": "User Acceptance Testing",
        "BPM": "Business Process Management",
        "ERD": "Entity Relationship Diagram",
        "RACI": "Responsible Accountable Consulted Informed",
        "SOW": "Statement of Work",
        "RFP": "Request for Proposal",
        "MVP": "Minimum Viable Product",
        "QA": "Quality Assurance",
        "UI": "User Interface",
        "UX": "User Experience",
        "REST": "Representational State Transfer",
        "JSON": "JavaScript Object Notation",
        "XML": "Extensible Markup Language",
        "SQL": "Structured Query Language",
        "NoSQL": "Not Only SQL",
        "CRUD": "Create Read Update Delete",
        "MR": "Merge Request",
        "AWS": "Amazon Web Services",
        "DNS": "Domain Name System",
        "URL": "Uniform Resource Locator",
        "HTTP": "Hypertext Transfer Protocol",
        "HTTPS": "HTTP Secure",
        "SSL": "Secure Sockets Layer",
        "TLS": "Transport Layer Security",
        "VPN": "Virtual Private Network",
        "SSH": "Secure Shell",
        "FTP": "File Transfer Protocol",
        "SMTP": "Simple Mail Transfer Protocol",
    }


def question_to_keywords(query: str) -> Optional[str]:
    """Convert question format to keywords."""
    question_words = r'\b(how|what|where|when|why|who|does|is|are|can|should|will)\b'

    if re.search(question_words, query.lower()):
        # Remove question words and punctuation
        cleaned = re.sub(question_words, '', query, flags=re.IGNORECASE)
        cleaned = re.sub(r'[?.,!]', '', cleaned)
        cleaned = ' '.join(cleaned.split())  # Normalize whitespace
        return cleaned.strip() if cleaned else None

    return None


def add_context_terms(query: str, context: Optional[Dict]) -> Optional[str]:
    """Add domain context terms if CTM context provided."""
    if not context:
        return None

    domain_terms = []
    if 'domain' in context:
        domain_terms.append(context['domain'])
    if 'tags' in context and isinstance(context['tags'], list):
        domain_terms.extend(context['tags'][:2])  # Max 2 tags

    if domain_terms:
        return f"{query} {' '.join(domain_terms)}"

    return None


def split_compound(query: str) -> Optional[str]:
    """Split compound terms with hyphens/underscores."""
    if '-' in query or '_' in query:
        return re.sub(r'[-_]', ' ', query)
    return None


def expand_acronyms(query: str, acronym_map: Dict[str, str]) -> Optional[str]:
    """Expand known acronyms."""
    words = query.split()
    expanded = []
    changed = False

    for word in words:
        # Check both exact match and uppercase version
        upper_word = word.upper()
        if upper_word in acronym_map:
            expanded.append(acronym_map[upper_word])
            changed = True
        else:
            expanded.append(word)

    return ' '.join(expanded) if changed else None


def synonym_swap(query: str, synonym_map: Dict[str, List[str]]) -> Optional[str]:
    """Replace terms with top synonym."""
    words = query.lower().split()
    swapped = []
    changed = False

    for word in words:
        if word in synonym_map and synonym_map[word]:
            swapped.append(synonym_map[word][0])  # Use first synonym
            changed = True
        else:
            swapped.append(word)

    return ' '.join(swapped) if changed else None


def expand(query: str, context: Optional[Dict] = None) -> Dict:
    """
    Expand query into variants using multiple strategies.

    Args:
        query: Search query string
        context: Optional context dict with domain/tags

    Returns:
        Dict with original query, variants list, and strategy used
    """
    config = load_config()
    expansion_config = config.get("expansion", {})

    # Check if expansion is enabled
    if not expansion_config.get("enabled", True):
        return {
            "original": query,
            "variants": [],
            "strategy": "disabled"
        }

    # Check minimum query length
    min_length = expansion_config.get("min_query_length", 3)
    if len(query.strip()) < min_length:
        return {
            "original": query,
            "variants": [],
            "strategy": "too_short"
        }

    # Load resources
    synonyms = load_synonyms()
    acronyms = load_acronyms()

    # Generate variants using enabled strategies
    strategies = expansion_config.get("strategies", ["synonym", "acronym", "reformulate"])
    max_variants = expansion_config.get("max_variants", 3)

    variants = []

    if "reformulate" in strategies:
        # Question to keywords
        kw_variant = question_to_keywords(query)
        if kw_variant and kw_variant not in variants:
            variants.append(kw_variant)

        # Add context
        ctx_variant = add_context_terms(query, context)
        if ctx_variant and ctx_variant not in variants:
            variants.append(ctx_variant)

        # Split compounds
        split_variant = split_compound(query)
        if split_variant and split_variant not in variants:
            variants.append(split_variant)

    if "acronym" in strategies:
        # Expand acronyms
        acr_variant = expand_acronyms(query, acronyms)
        if acr_variant and acr_variant not in variants:
            variants.append(acr_variant)

    if "synonym" in strategies:
        # Synonym swap
        syn_variant = synonym_swap(query, synonyms)
        if syn_variant and syn_variant not in variants:
            variants.append(syn_variant)

    # Limit to max_variants
    variants = variants[:max_variants]

    return {
        "original": query,
        "variants": variants,
        "strategy": "multi-strategy" if variants else "no_expansion"
    }


def main():
    """Main CLI entry point."""
    try:
        # Check if input is from CLI args first
        if len(sys.argv) > 1:
            # Read query from command line
            query = " ".join(sys.argv[1:])
            context = None
        elif not sys.stdin.isatty():
            # Read JSON from stdin
            input_data = json.load(sys.stdin)
            query = input_data.get("query", "")
            context = input_data.get("context")
        else:
            print(json.dumps({
                "error": "No query provided. Usage: query_expander.py 'query' or pipe JSON to stdin"
            }))
            sys.exit(0)

        # Expand query
        result = expand(query, context)

        # Output JSON
        print(json.dumps(result, indent=2))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "original": "",
            "variants": [],
            "strategy": "error"
        }))
        sys.exit(0)


if __name__ == "__main__":
    main()
