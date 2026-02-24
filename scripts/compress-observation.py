#!/usr/bin/env python3
"""R5: AI-powered observation compression using Ollama.

Called by observation-logger.sh after capturing raw JSONL.
Compresses raw tool observations into structured summaries
with type classification, extracted facts, and concepts.

Input: JSON on stdin with tool_name, tool_input, tool_output
Output: Compressed observation appended to compressed-observations.jsonl

Runs in background, never blocks tool execution.
"""
import json
import sys
import os
from datetime import datetime

OBS_DIR = os.path.expanduser("~/.claude/observations")
COMPRESSED_FILE = os.path.join(OBS_DIR, "compressed-observations.jsonl")
CONFIG_FILE = os.path.expanduser("~/.claude/config/observation-config.json")

PROMPT = """Compress this tool observation into a structured summary.
Tool: {tool_name}
Input: {tool_input}
Output: {tool_output}

Return ONLY valid JSON:
{{
  "title": "brief 5-8 word title",
  "type": "discovery|decision|modification|investigation",
  "facts": ["key fact 1", "key fact 2"],
  "files_touched": ["file1.py"],
  "concepts": ["concept1", "concept2"]
}}

JSON:"""


def check_config():
    """Check if compression is enabled."""
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        return config.get("compression", {}).get("enabled", False)
    except Exception:
        return False


def check_ollama(base_url="http://localhost:11434"):
    """Quick check if Ollama is responsive."""
    try:
        import urllib.request
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def compress_observation(tool_name, tool_input, tool_output,
                         model="llama3.2:3b",
                         base_url="http://localhost:11434"):
    """Compress a single observation using Ollama."""
    # Truncate inputs
    tool_input_str = str(tool_input)[:300]
    tool_output_str = str(tool_output)[:300]

    prompt = PROMPT.format(
        tool_name=tool_name,
        tool_input=tool_input_str,
        tool_output=tool_output_str,
    )

    try:
        import urllib.request
        data = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
        }).encode()
        req = urllib.request.Request(
            f"{base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())

        raw = result.get("response", "").strip()
        # Extract JSON from possible markdown wrapping
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        compressed = json.loads(raw)
        compressed["ts"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        compressed["tool"] = tool_name
        compressed["project"] = os.getcwd()
        return compressed

    except Exception:
        # Fallback: minimal structure without LLM
        return {
            "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "title": f"{tool_name} operation",
            "type": "investigation",
            "tool": tool_name,
            "facts": [],
            "files_touched": [],
            "concepts": [],
            "fallback": True,
        }


def main():
    if not check_config():
        return

    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    tool_name = data.get("tool_name", "")
    if not tool_name:
        return

    # Read model from config
    model = "llama3.2:3b"
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        model = config.get("compression_model", model)
    except Exception:
        pass

    if not check_ollama():
        return

    compressed = compress_observation(
        tool_name=tool_name,
        tool_input=data.get("tool_input", ""),
        tool_output=data.get("tool_output", ""),
        model=model,
    )

    if compressed:
        os.makedirs(OBS_DIR, exist_ok=True)
        with open(COMPRESSED_FILE, "a") as f:
            f.write(json.dumps(compressed, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
