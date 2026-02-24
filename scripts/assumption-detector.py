#!/usr/bin/env python3
"""
Assumption Detector - Scans text for unmarked assumptions

Detects assumption indicators that aren't explicitly marked with
[ASSUMED], [OPEN], or [MISSING] tags.

Usage:
    assumption-detector.py [file_path]
    cat file.txt | assumption-detector.py

Output: JSON to stdout
Exit code: Always 0 (violations reported in JSON)
"""

import sys
import json
import re
from typing import List, Dict, Tuple


# Assumption indicator patterns
ASSUMPTION_PATTERNS = [
    # Direct assumption phrases
    (r"\bI'll assume\b", "I'll assume"),
    (r"\bI'm assuming\b", "I'm assuming"),
    (r"\bassuming that\b", "assuming that"),
    (r"\blet's assume\b", "let's assume"),
    (r"\bpresumably\b", "presumably"),
    (r"\bprobably\b", "probably"),
    (r"\blikely means\b", "likely means"),
    (r"\blikely refers to\b", "likely refers to"),
    (r"\bI think this means\b", "I think this means"),
    (r"\bthis probably means\b", "this probably means"),
    (r"\bthis suggests\b", "this suggests"),
    (r"\bit seems like\b", "it seems like"),
    (r"\bit appears that\b", "it appears that"),
    (r"\bapparently\b", "apparently"),
    (r"\bmy understanding is\b", "my understanding is"),
    (r"\bas far as I can tell\b", "as far as I can tell"),

    # Gap-filling phrases
    (r"\bbased on the context\b", "based on the context"),
    (r"\bfrom what I can gather\b", "from what I can gather"),
    (r"\bin the absence of\b", "in the absence of"),
    (r"\bsince no .+ was specified\b", "since no X was specified"),
    (r"\bdefaulting to\b", "defaulting to"),
    (r"\bfalling back to\b", "falling back to"),
    (r"\binterpreting this as\b", "interpreting this as"),
    (r"\breading this as\b", "reading this as"),
]

# Markers that indicate assumption is already tagged
EXISTING_MARKERS = [
    r"\[ASSUMED:",
    r"\[OPEN:",
    r"\[MISSING:",
]

# Question pattern to exclude
QUESTION_PATTERN = r"should\s+I\s+assume"


def is_in_code_block(line_num: int, lines: List[str]) -> bool:
    """Check if line is inside a code fence (```)"""
    in_block = False
    for i in range(line_num):
        if lines[i].strip().startswith("```"):
            in_block = not in_block
    return in_block


def is_quoted_line(line: str) -> bool:
    """Check if line is a quote (starts with >)"""
    return line.strip().startswith(">")


def is_already_marked(line: str) -> bool:
    """Check if line contains existing assumption markers"""
    return any(re.search(marker, line, re.IGNORECASE) for marker in EXISTING_MARKERS)


def is_question_context(line: str) -> bool:
    """Check if 'assume' appears in a question context"""
    return re.search(QUESTION_PATTERN, line, re.IGNORECASE) is not None


def extract_assumption_summary(line: str, indicator: str) -> str:
    """Extract a summary of the assumption for suggested marker"""
    # Remove the indicator phrase and clean up
    cleaned = re.sub(re.escape(indicator), "", line, flags=re.IGNORECASE).strip()
    # Remove common prefixes and leading punctuation/whitespace
    cleaned = re.sub(r"^[,.\s]+", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)  # Collapse multiple spaces
    cleaned = re.sub(r"^(that|the)\s+", "", cleaned, flags=re.IGNORECASE)
    # Capitalize first letter
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    # Truncate if too long
    if len(cleaned) > 80:
        cleaned = cleaned[:77] + "..."
    return cleaned


def scan_text(text: str) -> Dict:
    """Scan text for unmarked assumptions"""
    lines = text.split("\n")
    violations = []

    for line_num, line in enumerate(lines, start=1):
        # Skip code blocks
        if is_in_code_block(line_num - 1, lines):
            continue

        # Skip quoted lines
        if is_quoted_line(line):
            continue

        # Skip already marked assumptions
        if is_already_marked(line):
            continue

        # Skip question contexts
        if is_question_context(line):
            continue

        # Check for assumption indicators
        for pattern, indicator_name in ASSUMPTION_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                assumption_summary = extract_assumption_summary(line, match.group(0))
                suggested_marker = f"[ASSUMED: {assumption_summary}] - verify accuracy"

                violations.append({
                    "line": line_num,
                    "text": line.strip(),
                    "indicator": match.group(0),
                    "suggested_marker": suggested_marker
                })
                break  # Only report first match per line

    total = len(violations)
    summary = f"{total} unmarked assumption{'s' if total != 1 else ''} detected" if total > 0 else "Clean - no unmarked assumptions"

    return {
        "violations": violations,
        "total_violations": total,
        "scan_summary": summary
    }


def main():
    """Main entry point"""
    try:
        # Read input from file or stdin
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            text = sys.stdin.read()

        # Scan and output results
        result = scan_text(text)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except FileNotFoundError:
        error_result = {
            "violations": [],
            "total_violations": 0,
            "scan_summary": f"Error: File not found - {sys.argv[1]}"
        }
        print(json.dumps(error_result, indent=2))
    except Exception as e:
        error_result = {
            "violations": [],
            "total_violations": 0,
            "scan_summary": f"Error: {str(e)}"
        }
        print(json.dumps(error_result, indent=2))

    # Always exit 0
    sys.exit(0)


if __name__ == "__main__":
    main()
