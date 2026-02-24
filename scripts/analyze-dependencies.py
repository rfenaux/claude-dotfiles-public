#!/usr/bin/env python3
"""
Dependency Analyzer for Multi-File Refactoring Pipeline.

Analyzes a codebase to find all files referencing a target name,
builds a dependency graph, and returns topologically sorted batches
for safe parallel renaming.

Supports: .py, .ts, .tsx, .js, .jsx, .json, .md
Uses only stdlib (ast for Python, regex for everything else).

Usage:
    python3 analyze-dependencies.py <root_dir> <target_name> [--json]
"""

import ast
import json
import os
import re
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple


# File extensions to scan
SUPPORTED_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md"}

# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    ".rag", ".claude", "dist", "build", ".next", ".cache"
}


def find_files(root_dir: str, target_name: str) -> List[str]:
    """Find all files containing the target name."""
    matches = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, "r", errors="ignore") as f:
                    content = f.read()
                if target_name in content:
                    matches.append(filepath)
            except (IOError, OSError):
                continue

    return matches


def extract_imports_python(filepath: str) -> List[str]:
    """Extract import targets from a Python file using ast."""
    imports = []
    try:
        with open(filepath, "r") as f:
            tree = ast.parse(f.read(), filename=filepath)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
                for alias in node.names:
                    imports.append(alias.name)
    except (SyntaxError, UnicodeDecodeError, IOError):
        pass
    return imports


def extract_imports_typescript(filepath: str) -> List[str]:
    """Extract import targets from a TypeScript/JavaScript file using regex."""
    imports = []
    try:
        with open(filepath, "r", errors="ignore") as f:
            content = f.read()

        # import X from 'Y'
        for m in re.finditer(r"import\s+(?:\{[^}]+\}|[\w*]+)\s+from\s+['\"]([^'\"]+)['\"]", content):
            imports.append(m.group(1))

        # require('Y')
        for m in re.finditer(r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", content):
            imports.append(m.group(1))

        # export * from 'Y'
        for m in re.finditer(r"export\s+(?:\{[^}]+\}|\*)\s+from\s+['\"]([^'\"]+)['\"]", content):
            imports.append(m.group(1))

    except (IOError, OSError):
        pass
    return imports


def build_import_graph(files: List[str], root_dir: str) -> Dict[str, Set[str]]:
    """
    Build a dependency graph: file -> set of files it imports from.

    Returns dict mapping each file to the set of files it depends on.
    """
    graph = defaultdict(set)

    # Build a lookup from module/path fragments to actual files
    file_lookup = {}
    for f in files:
        rel = os.path.relpath(f, root_dir)
        # Store by stem and various path forms
        stem = os.path.splitext(rel)[0]
        file_lookup[stem] = f
        file_lookup[rel] = f
        file_lookup[stem.replace(os.sep, ".")] = f  # Python dotted paths
        file_lookup[stem.replace(os.sep, "/")] = f   # Unix paths

    for filepath in files:
        ext = os.path.splitext(filepath)[1]

        if ext == ".py":
            imports = extract_imports_python(filepath)
        elif ext in (".ts", ".tsx", ".js", ".jsx"):
            imports = extract_imports_typescript(filepath)
        else:
            continue

        for imp in imports:
            # Try to resolve import to a file in our set
            # Remove leading ./ or ../
            clean_imp = re.sub(r"^\.+/?", "", imp)
            for key, target_file in file_lookup.items():
                if target_file == filepath:
                    continue
                if clean_imp in key or key.endswith(clean_imp):
                    graph[filepath].add(target_file)
                    break

    return dict(graph)


def topological_sort(files: List[str], graph: Dict[str, Set[str]]) -> List[List[str]]:
    """
    Topological sort into batches for parallel processing.

    Files in the same batch have no dependencies on each other
    and can be processed in parallel.

    Returns list of batches (each batch is a list of files).
    """
    # Build in-degree map (only for files in our set)
    file_set = set(files)
    in_degree = {f: 0 for f in files}
    reverse_graph = defaultdict(set)  # file -> files that depend on it

    for src, deps in graph.items():
        if src not in file_set:
            continue
        for dep in deps:
            if dep in file_set:
                in_degree[src] = in_degree.get(src, 0)  # ensure exists
                # src depends on dep, so dep must come first
                reverse_graph[dep].add(src)
                in_degree[src] += 1

    # Kahn's algorithm for batched topological sort
    batches = []
    remaining = set(files)

    while remaining:
        # Find all files with no unresolved dependencies
        batch = [f for f in remaining if in_degree.get(f, 0) == 0]

        if not batch:
            # Cycle detected — put all remaining in one batch
            batch = list(remaining)

        batches.append(sorted(batch))

        # Remove processed files and update degrees
        for f in batch:
            remaining.discard(f)
            for dependent in reverse_graph.get(f, set()):
                if dependent in remaining:
                    in_degree[dependent] = max(0, in_degree[dependent] - 1)

    return batches


def build_dependency_graph(root_dir: str, target_name: str) -> Dict:
    """
    Main entry point: analyze dependencies for a target name.

    Returns:
        {
            "target": str,
            "root_dir": str,
            "files_to_update": [str],
            "file_count": int,
            "dependency_order": [[str]],  # batches
            "import_graph": {str: [str]},
            "batch_count": int
        }
    """
    root_dir = os.path.abspath(root_dir)

    # Find all files referencing the target
    files = find_files(root_dir, target_name)

    if not files:
        return {
            "target": target_name,
            "root_dir": root_dir,
            "files_to_update": [],
            "file_count": 0,
            "dependency_order": [],
            "import_graph": {},
            "batch_count": 0
        }

    # Build import graph
    graph = build_import_graph(files, root_dir)

    # Topological sort into batches
    batches = topological_sort(files, graph)

    # Convert sets to lists for JSON serialization
    import_graph = {k: sorted(v) for k, v in graph.items()}

    return {
        "target": target_name,
        "root_dir": root_dir,
        "files_to_update": sorted(files),
        "file_count": len(files),
        "dependency_order": batches,
        "import_graph": import_graph,
        "batch_count": len(batches)
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: analyze-dependencies.py <root_dir> <target_name> [--json]")
        print("  Analyzes files referencing <target_name> in <root_dir>")
        print("  Returns dependency-ordered batches for safe renaming")
        sys.exit(1)

    root_dir = sys.argv[1]
    target_name = sys.argv[2]
    output_json = "--json" in sys.argv

    if not os.path.isdir(root_dir):
        print(f"Error: {root_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    result = build_dependency_graph(root_dir, target_name)

    if output_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Target: {result['target']}")
        print(f"Root:   {result['root_dir']}")
        print(f"Files:  {result['file_count']}")
        print(f"Batches: {result['batch_count']}")
        print()
        for i, batch in enumerate(result["dependency_order"], 1):
            print(f"Batch {i} ({len(batch)} files):")
            for f in batch:
                rel = os.path.relpath(f, root_dir)
                deps = result["import_graph"].get(f, [])
                dep_str = f" <- {', '.join(os.path.relpath(d, root_dir) for d in deps)}" if deps else ""
                print(f"  {rel}{dep_str}")
            print()


if __name__ == "__main__":
    main()
