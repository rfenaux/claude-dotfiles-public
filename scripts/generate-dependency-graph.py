#!/usr/bin/env python3
"""
generate-dependency-graph.py - Produce a JSON dependency graph of the Claude Code config.

Scans settings.json, hooks, scripts, agents, config files, and launchd plists
to build a directed graph of nodes (components) and edges (references).

Output: ~/.claude/dependency-graph.json

Usage:
    python3 ~/.claude/scripts/generate-dependency-graph.py
    python3 ~/.claude/scripts/generate-dependency-graph.py --stats  # Summary only
"""

import json
import os
import re
import glob
import sys
from datetime import datetime, timezone
from pathlib import Path

CLAUDE_DIR = os.path.expanduser("~/.claude")
LAUNCH_DIR = os.path.expanduser("~/Library/LaunchAgents")
OUTPUT_FILE = os.path.join(CLAUDE_DIR, "dependency-graph.json")


def discover_nodes():
    """Discover all components as graph nodes."""
    nodes = []

    # Agents
    for f in sorted(glob.glob(os.path.join(CLAUDE_DIR, "agents", "*.md"))):
        name = os.path.basename(f).replace(".md", "")
        model, async_mode = parse_agent_frontmatter(f)
        nodes.append({
            "id": f"agent:{name}",
            "type": "agent",
            "name": name,
            "path": f,
            "model": model,
            "async": async_mode,
        })

    # Skills
    for f in sorted(glob.glob(os.path.join(CLAUDE_DIR, "skills", "*", "SKILL.md"))):
        name = os.path.basename(os.path.dirname(f))
        nodes.append({
            "id": f"skill:{name}",
            "type": "skill",
            "name": name,
            "path": f,
        })

    # Hooks (registered in settings.json)
    for f in sorted(glob.glob(os.path.join(CLAUDE_DIR, "hooks", "*.sh")) +
                    glob.glob(os.path.join(CLAUDE_DIR, "hooks", "*.py")) +
                    glob.glob(os.path.join(CLAUDE_DIR, "hooks", "*.mjs")) +
                    glob.glob(os.path.join(CLAUDE_DIR, "hooks", "ctm", "*.sh"))):
        name = os.path.basename(f).rsplit(".", 1)[0]
        nodes.append({
            "id": f"hook:{name}",
            "type": "hook",
            "name": name,
            "path": f,
        })

    # Scripts
    for f in sorted(glob.glob(os.path.join(CLAUDE_DIR, "scripts", "*"))):
        if os.path.isfile(f) and not f.endswith("__pycache__"):
            name = os.path.basename(f).rsplit(".", 1)[0]
            nodes.append({
                "id": f"script:{name}",
                "type": "script",
                "name": name,
                "path": f,
            })

    # Config files
    for f in sorted(glob.glob(os.path.join(CLAUDE_DIR, "config", "*.json"))):
        name = os.path.basename(f).replace(".json", "")
        nodes.append({
            "id": f"config:{name}",
            "type": "config",
            "name": name,
            "path": f,
        })

    # Rules
    for f in sorted(glob.glob(os.path.join(CLAUDE_DIR, "rules", "*.md"))):
        name = os.path.basename(f).replace(".md", "")
        nodes.append({
            "id": f"rule:{name}",
            "type": "rule",
            "name": name,
            "path": f,
        })

    # Core files
    for name, path in [
        ("CLAUDE.md", os.path.join(CLAUDE_DIR, "CLAUDE.md")),
        ("settings.json", os.path.join(CLAUDE_DIR, "settings.json")),
        ("inventory.json", os.path.join(CLAUDE_DIR, "inventory.json")),
        ("AGENTS_INDEX.md", os.path.join(CLAUDE_DIR, "AGENTS_INDEX.md")),
        ("SKILLS_INDEX.md", os.path.join(CLAUDE_DIR, "SKILLS_INDEX.md")),
        ("agent-clusters.json", os.path.join(CLAUDE_DIR, "config", "agent-clusters.json")),
    ]:
        if os.path.exists(path):
            nodes.append({
                "id": f"core:{name}",
                "type": "core",
                "name": name,
                "path": path,
            })

    # LaunchAgent services
    if os.path.isdir(LAUNCH_DIR):
        for f in sorted(glob.glob(os.path.join(LAUNCH_DIR, "com.claude.*.plist")) +
                        glob.glob(os.path.join(LAUNCH_DIR, "com.raphael.*.plist"))):
            name = os.path.basename(f).replace(".plist", "")
            nodes.append({
                "id": f"service:{name}",
                "type": "service",
                "name": name,
                "path": f,
            })

    return nodes


def parse_agent_frontmatter(filepath):
    """Extract model and async mode from agent YAML frontmatter."""
    model = "unknown"
    async_mode = "auto"
    try:
        with open(filepath, "r") as f:
            content = f.read(2000)
        if content.startswith("---"):
            fm = content.split("---", 2)[1]
            m = re.search(r"^model:\s*(\S+)", fm, re.MULTILINE)
            if m:
                model = m.group(1)
            a = re.search(r"mode:\s*(\S+)", fm, re.MULTILINE)
            if a:
                async_mode = a.group(1)
    except Exception:
        pass
    return model, async_mode


def discover_edges(nodes):
    """Discover all reference edges between nodes."""
    edges = []
    node_map = {n["id"]: n for n in nodes}
    node_paths = {n["path"]: n["id"] for n in nodes if "path" in n}

    # 1. settings.json -> hooks (REGISTERED_IN)
    settings_path = os.path.join(CLAUDE_DIR, "settings.json")
    if os.path.exists(settings_path):
        try:
            with open(settings_path) as f:
                settings = json.load(f)
            for event, entries in settings.get("hooks", {}).items():
                for entry in entries:
                    for hook in entry.get("hooks", []):
                        cmd = hook.get("command", "")
                        script_path = cmd.split()[0] if cmd else ""
                        script_path = os.path.expanduser(script_path)
                        if script_path in node_paths:
                            edges.append({
                                "from": "core:settings.json",
                                "to": node_paths[script_path],
                                "type": "REGISTERED_IN",
                                "event": event,
                                "matcher": entry.get("matcher", ""),
                            })
        except Exception:
            pass

    # 2. Hook/script files -> other scripts/configs (CALLS, READS_CONFIG)
    claude_pattern = re.compile(r'["\']?(?:\$HOME|~|/Users/\w+)/\.claude/(scripts|config|hooks)/([^"\';\s]+)')
    # Also match config filenames loaded via variable paths (e.g. f"{config_dir}/name.json")
    config_name_pattern = re.compile(r'["\']([a-z][a-z0-9_-]+)\.json["\']')
    for node in nodes:
        if node["type"] not in ("hook", "script"):
            continue
        try:
            with open(node["path"], "r") as f:
                content = f.read()
        except Exception:
            continue

        for match in claude_pattern.finditer(content):
            category = match.group(1)
            filename = match.group(2)
            basename = filename.rsplit(".", 1)[0]

            if category == "scripts":
                target_id = f"script:{basename}"
                edge_type = "CALLS"
            elif category == "config":
                target_id = f"config:{basename}"
                edge_type = "READS_CONFIG"
            elif category == "hooks":
                target_id = f"hook:{basename}"
                edge_type = "CALLS"
            else:
                continue

            if target_id in node_map and target_id != node["id"]:
                edges.append({
                    "from": node["id"],
                    "to": target_id,
                    "type": edge_type,
                })

        # Match config names referenced by filename (variable path patterns)
        for match in config_name_pattern.finditer(content):
            config_name = match.group(1)
            target_id = f"config:{config_name}"
            if target_id in node_map and target_id != node["id"]:
                edges.append({
                    "from": node["id"],
                    "to": target_id,
                    "type": "READS_CONFIG",
                })

        # Match script/hook basenames via $SCRIPT_DIR, $DIR, or similar variable paths
        for other_node in nodes:
            if other_node["type"] not in ("script", "hook"):
                continue
            other_basename = os.path.basename(other_node["path"])
            if other_basename in content and other_node["id"] != node["id"]:
                edges.append({
                    "from": node["id"],
                    "to": other_node["id"],
                    "type": "CALLS",
                })

    # 3. Agent frontmatter -> other agents (DELEGATES_TO)
    delegates_pattern = re.compile(r"delegates_to:\s*\n((?:\s+-\s+\S+\n)*)", re.MULTILINE)
    for node in nodes:
        if node["type"] != "agent":
            continue
        try:
            with open(node["path"], "r") as f:
                content = f.read(3000)
        except Exception:
            continue

        m = delegates_pattern.search(content)
        if m:
            for line in m.group(1).strip().split("\n"):
                delegate = line.strip().lstrip("- ").strip()
                target_id = f"agent:{delegate}"
                if delegate and target_id in node_map:
                    edges.append({
                        "from": node["id"],
                        "to": target_id,
                        "type": "DELEGATES_TO",
                    })

    # 4. agent-clusters.json -> agents (CLUSTER_MEMBER)
    clusters_path = os.path.join(CLAUDE_DIR, "config", "agent-clusters.json")
    if os.path.exists(clusters_path):
        try:
            with open(clusters_path) as f:
                clusters = json.load(f)
            for cluster_name, cluster_data in clusters.get("clusters", {}).items():
                for member in cluster_data.get("members", []):
                    target_id = f"agent:{member}"
                    if target_id in node_map:
                        edges.append({
                            "from": "config:agent-clusters",
                            "to": target_id,
                            "type": "CLUSTER_MEMBER",
                            "cluster": cluster_name,
                        })
                orchestrator = cluster_data.get("orchestrator")
                if orchestrator:
                    orch_id = f"agent:{orchestrator}"
                    if orch_id in node_map:
                        edges.append({
                            "from": "config:agent-clusters",
                            "to": orch_id,
                            "type": "CLUSTER_ORCHESTRATOR",
                            "cluster": cluster_name,
                        })
        except Exception:
            pass

    # 5. CLAUDE.md routing tables -> agents (ROUTED_IN)
    claude_md_path = os.path.join(CLAUDE_DIR, "CLAUDE.md")
    if os.path.exists(claude_md_path):
        try:
            with open(claude_md_path, "r") as f:
                claude_md = f.read()
            # Match backtick-wrapped agent names in routing tables: `agent-name`
            backtick_refs = re.findall(r'`([a-z][a-z0-9-]+)`', claude_md)
            for ref in backtick_refs:
                target_id = f"agent:{ref}"
                if target_id in node_map:
                    edges.append({
                        "from": "core:CLAUDE.md",
                        "to": target_id,
                        "type": "ROUTED_IN",
                    })
                # Also check skills
                skill_id = f"skill:{ref}"
                if skill_id in node_map:
                    edges.append({
                        "from": "core:CLAUDE.md",
                        "to": skill_id,
                        "type": "ROUTED_IN",
                    })
        except Exception:
            pass

    # 6. AGENTS_INDEX.md -> agents (INDEXED_IN)
    agents_index_path = os.path.join(CLAUDE_DIR, "AGENTS_INDEX.md")
    if os.path.exists(agents_index_path):
        try:
            with open(agents_index_path, "r") as f:
                agents_index = f.read()
            for ref in re.findall(r'`([a-z][a-z0-9-]+)`', agents_index):
                target_id = f"agent:{ref}"
                if target_id in node_map:
                    edges.append({
                        "from": "core:AGENTS_INDEX.md",
                        "to": target_id,
                        "type": "INDEXED_IN",
                    })
        except Exception:
            pass

    # 7. SKILLS_INDEX.md -> skills (INDEXED_IN)
    skills_index_path = os.path.join(CLAUDE_DIR, "SKILLS_INDEX.md")
    if os.path.exists(skills_index_path):
        try:
            with open(skills_index_path, "r") as f:
                skills_index = f.read()
            for ref in re.findall(r'`([a-z][a-z0-9-]+)`', skills_index):
                skill_id = f"skill:{ref}"
                if skill_id in node_map:
                    edges.append({
                        "from": "core:SKILLS_INDEX.md",
                        "to": skill_id,
                        "type": "INDEXED_IN",
                    })
                # Some skills share names with agents
                agent_id = f"agent:{ref}"
                if agent_id in node_map:
                    edges.append({
                        "from": "core:SKILLS_INDEX.md",
                        "to": agent_id,
                        "type": "INDEXED_IN",
                    })
        except Exception:
            pass

    # 8. Rules auto-loaded from rules/ directory (AUTO_LOADED)
    for node in nodes:
        if node["type"] == "rule":
            edges.append({
                "from": "core:CLAUDE.md",
                "to": node["id"],
                "type": "AUTO_LOADED",
            })

    # 9. inventory.json -> agents/skills/hooks/scripts (INVENTORIED)
    inventory_path = os.path.join(CLAUDE_DIR, "inventory.json")
    if os.path.exists(inventory_path):
        try:
            with open(inventory_path, "r") as f:
                inventory = json.load(f)
            for category in inventory.get("components", {}).values():
                if isinstance(category, dict):
                    for item_name in category.get("items", []):
                        for prefix in ("agent", "skill", "hook", "script", "config", "rule"):
                            target_id = f"{prefix}:{item_name}"
                            if target_id in node_map:
                                edges.append({
                                    "from": "core:inventory.json",
                                    "to": target_id,
                                    "type": "INVENTORIED",
                                })
                                break
        except Exception:
            pass

    # 10. Skill/Agent body -> configs/scripts/other skills (REFERENCES)
    # Scans agent and skill markdown for references to config files, scripts, or skills
    for node in nodes:
        if node["type"] not in ("agent", "skill"):
            continue
        try:
            with open(node["path"], "r") as f:
                content = f.read()
        except Exception:
            continue
        # Match config file references: config-name.json or `config-name`
        for config_node in nodes:
            if config_node["type"] != "config":
                continue
            cname = config_node["name"]
            if cname in content and cname != node["name"]:
                edges.append({
                    "from": node["id"],
                    "to": config_node["id"],
                    "type": "REFERENCES",
                })
        # Match script references by basename (with extension to avoid false positives)
        for script_node in nodes:
            if script_node["type"] != "script":
                continue
            sname = script_node["name"]
            spath = os.path.basename(script_node["path"])
            if spath in content and sname != node["name"]:
                edges.append({
                    "from": node["id"],
                    "to": script_node["id"],
                    "type": "REFERENCES",
                })
            # Also match script name without extension in backticks
            if f"`{sname}`" in content and sname != node["name"]:
                edges.append({
                    "from": node["id"],
                    "to": script_node["id"],
                    "type": "REFERENCES",
                })

    # 10b. Skill SKILL.md companion files -> scripts/configs
    # Skills often have helper scripts in their directory that call ~/.claude/scripts/
    for node in nodes:
        if node["type"] != "skill":
            continue
        skill_dir = os.path.dirname(node["path"])
        for helper in glob.glob(os.path.join(skill_dir, "*.sh")) + \
                       glob.glob(os.path.join(skill_dir, "*.py")):
            try:
                with open(helper, "r") as f:
                    hcontent = f.read()
            except Exception:
                continue
            for match in claude_pattern.finditer(hcontent):
                category = match.group(1)
                filename = match.group(2)
                basename = filename.rsplit(".", 1)[0]
                if category == "scripts":
                    target_id = f"script:{basename}"
                    edge_type = "CALLS"
                elif category == "config":
                    target_id = f"config:{basename}"
                    edge_type = "READS_CONFIG"
                else:
                    continue
                if target_id in node_map:
                    edges.append({
                        "from": node["id"],
                        "to": target_id,
                        "type": edge_type,
                    })

    # 11. README/index files that document other scripts (DOCUMENTED_IN)
    # scripts/README.md lists scripts by their filename
    readme_path = os.path.join(CLAUDE_DIR, "scripts", "README.md")
    if os.path.exists(readme_path):
        try:
            with open(readme_path, "r") as f:
                readme_content = f.read()
            for node in nodes:
                if node["type"] != "script" or node["name"] == "README":
                    continue
                basename = os.path.basename(node["path"])
                if basename in readme_content:
                    edges.append({
                        "from": "script:README",
                        "to": node["id"],
                        "type": "DOCUMENTED_IN",
                    })
        except Exception:
            pass

    # 11b. CONFIGURATION_GUIDE.md -> scripts/configs/hooks (DOCUMENTED_IN)
    config_guide_path = os.path.join(CLAUDE_DIR, "CONFIGURATION_GUIDE.md")
    if os.path.exists(config_guide_path):
        try:
            with open(config_guide_path, "r") as f:
                config_guide = f.read()
            for node in nodes:
                if node["type"] in ("core",):
                    continue
                # Check for basename reference
                basename = os.path.basename(node["path"])
                if basename in config_guide:
                    edges.append({
                        "from": "core:CLAUDE.md",  # Treat as part of core docs
                        "to": node["id"],
                        "type": "DOCUMENTED_IN",
                    })
        except Exception:
            pass

    # 12. settings.json statusLine -> script (STATUSLINE)
    if os.path.exists(settings_path):
        try:
            with open(settings_path) as f:
                settings = json.load(f)
            sl = settings.get("statusLine", {})
            if isinstance(sl, dict):
                cmd = sl.get("command", "")
                script_path = cmd.split()[0] if cmd else ""
                script_path = os.path.expanduser(script_path)
                if script_path in node_paths:
                    edges.append({
                        "from": "core:settings.json",
                        "to": node_paths[script_path],
                        "type": "STATUSLINE",
                    })
            # Also check settings.local.json
            local_settings_path = os.path.join(CLAUDE_DIR, "settings.local.json")
            if os.path.exists(local_settings_path):
                with open(local_settings_path) as f:
                    local_content = f.read()
                for node in nodes:
                    if node["type"] in ("core",):
                        continue
                    if node["name"] in local_content:
                        edges.append({
                            "from": "core:settings.json",
                            "to": node["id"],
                            "type": "REGISTERED_IN",
                        })
        except Exception:
            pass

    # 13. LaunchAgent plists -> scripts (TRIGGERS)
    if os.path.isdir(LAUNCH_DIR):
        prog_pattern = re.compile(r"<string>([^<]*\.claude/[^<]+)</string>")
        for node in nodes:
            if node["type"] != "service":
                continue
            try:
                with open(node["path"], "r") as f:
                    content = f.read()
            except Exception:
                continue
            for match in prog_pattern.finditer(content):
                ref_path = match.group(1)
                ref_base = os.path.basename(ref_path).rsplit(".", 1)[0]
                for target_type in ("script", "hook"):
                    target_id = f"{target_type}:{ref_base}"
                    if target_id in node_map:
                        edges.append({
                            "from": node["id"],
                            "to": target_id,
                            "type": "TRIGGERS",
                        })

    # Deduplicate edges
    seen = set()
    unique_edges = []
    for edge in edges:
        key = (edge["from"], edge["to"], edge["type"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(edge)

    return unique_edges


def discover_ghosts(nodes):
    """Find references to components that don't exist on disk (ghost references)."""
    ghosts = []
    node_ids = {n["id"] for n in nodes}
    agent_names = {n["name"] for n in nodes if n["type"] == "agent"}
    skill_names = {n["name"] for n in nodes if n["type"] == "skill"}

    # 1. agent-clusters.json members → check agent exists
    clusters_path = os.path.join(CLAUDE_DIR, "config", "agent-clusters.json")
    if os.path.exists(clusters_path):
        try:
            with open(clusters_path) as f:
                data = json.load(f)
            clusters = data if isinstance(data, list) else data.get("clusters", [])
            for cluster in clusters:
                if not isinstance(cluster, dict):
                    continue
                for member in cluster.get("members", []):
                    m = member if isinstance(member, str) else str(member)
                    if m not in agent_names:
                        ghosts.append({
                            "source": "config/agent-clusters.json",
                            "target": f"agent:{m}",
                            "type": "GHOST_CLUSTER_MEMBER",
                        })
        except Exception:
            pass

    # 2. settings.json hook commands → check script exists on disk
    settings_path = os.path.join(CLAUDE_DIR, "settings.json")
    if os.path.exists(settings_path):
        try:
            with open(settings_path) as f:
                settings = json.load(f)
            for event, entries in settings.get("hooks", {}).items():
                for entry in entries:
                    for hook in entry.get("hooks", []):
                        cmd = hook.get("command", "")
                        script_path = cmd.split()[0] if cmd else ""
                        script_path = os.path.expanduser(script_path)
                        # Skip bare commands (echo, python3, etc.) — only check file paths
                        if script_path and "/" in script_path and not os.path.exists(script_path):
                            ghosts.append({
                                "source": "settings.json",
                                "target": script_path,
                                "type": "GHOST_HOOK_COMMAND",
                                "event": event,
                            })
        except Exception:
            pass

    # 3. Agent delegates_to → check target agent exists
    for node in nodes:
        if node["type"] != "agent" or "path" not in node:
            continue
        try:
            with open(node["path"]) as f:
                content = f.read()
            m = re.search(r"delegates_to:\s*\n((?:\s+-\s+\S+\n)*)", content)
            if m:
                for line in m.group(1).strip().split("\n"):
                    delegate = line.strip().lstrip("- ").strip()
                    if delegate and delegate not in agent_names:
                        ghosts.append({
                            "source": node["id"],
                            "target": f"agent:{delegate}",
                            "type": "GHOST_DELEGATE",
                        })
        except Exception:
            pass

    # 4. CLAUDE.md routing tables → check backtick refs exist
    #    Only check actual routing rows (trigger → agent/skill), not example/config tables
    claude_md = os.path.join(CLAUDE_DIR, "CLAUDE.md")
    if os.path.exists(claude_md):
        try:
            with open(claude_md) as f:
                content = f.read()
            # Extract routing sections (between "### ... Routing" headers)
            routing_sections = re.findall(
                r"###[^#]*(?:Routing|Auto-Invoke)[^#]*\n((?:.*\n)*?)(?=\n##|\n---|\Z)",
                content
            )
            routing_text = "\n".join(routing_sections)
            # Match: | trigger | `agent-name` | in routing sections only
            for match in re.finditer(r"\|\s*`([a-z][a-z0-9_-]+)`\s*\|", routing_text):
                name = match.group(1)
                if name not in agent_names and name not in skill_names:
                    ghosts.append({
                        "source": "CLAUDE.md",
                        "target": name,
                        "type": "GHOST_ROUTING",
                    })
        except Exception:
            pass

    return ghosts


def compute_stats(nodes, edges):
    """Compute summary statistics."""
    type_counts = {}
    for n in nodes:
        type_counts[n["type"]] = type_counts.get(n["type"], 0) + 1

    edge_type_counts = {}
    for e in edges:
        edge_type_counts[e["type"]] = edge_type_counts.get(e["type"], 0) + 1

    # Allowlist: components with no programmatic consumer (CLI utilities, skill-runtime companions)
    # These are legitimate but untraceable via static analysis
    ORPHAN_ALLOWLIST = {
        "script:claude-pick":            "Standalone CLI utility — user-invoked from terminal",
        "script:install-menubar":        "One-time setup script — run manually once",
        "script:session-context":        "Skill-runtime companion — invoked by session-context skill at runtime",
        "script:generate-usage-report":  "Standalone CLI utility — user-invoked for usage analytics",
        "config:research-loop":          "Skill-runtime companion — consumed by research-loop skill at runtime",
    }

    # Find orphans (nodes with zero incoming edges)
    has_incoming = set()
    for e in edges:
        has_incoming.add(e["to"])

    orphans = [n["id"] for n in nodes if n["id"] not in has_incoming
               and n["type"] not in ("core", "service")
               and n["id"] not in ORPHAN_ALLOWLIST]

    return {
        "node_counts": type_counts,
        "edge_counts": edge_type_counts,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "potential_orphans": len(orphans),
        "orphan_ids": orphans,
        "allowlisted": len(ORPHAN_ALLOWLIST),
        "allowlist": ORPHAN_ALLOWLIST,
    }


def main():
    stats_only = "--stats" in sys.argv

    nodes = discover_nodes()
    edges = discover_edges(nodes)
    ghosts = discover_ghosts(nodes)
    stats = compute_stats(nodes, edges)
    stats["ghost_references"] = len(ghosts)
    stats["ghosts"] = ghosts

    if stats_only:
        print(f"Nodes: {stats['total_nodes']} ({', '.join(f'{k}:{v}' for k,v in sorted(stats['node_counts'].items()))})")
        print(f"Edges: {stats['total_edges']} ({', '.join(f'{k}:{v}' for k,v in sorted(stats['edge_counts'].items()))})")
        print(f"Potential orphans: {stats['potential_orphans']} ({stats['allowlisted']} allowlisted)")
        if stats["orphan_ids"]:
            for oid in stats["orphan_ids"]:
                print(f"  - {oid}")
        print(f"Ghost references: {stats['ghost_references']}")
        if ghosts:
            for g in ghosts:
                print(f"  - {g['type']}: {g['source']} -> {g['target']}")
        return

    graph = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "version": "3.0",
        "stats": stats,
        "nodes": nodes,
        "edges": edges,
        "ghosts": ghosts,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(graph, f, indent=2)

    print(f"Dependency graph written to {OUTPUT_FILE}")
    print(f"  Nodes: {stats['total_nodes']}, Edges: {stats['total_edges']}, Potential orphans: {stats['potential_orphans']}")


if __name__ == "__main__":
    main()
