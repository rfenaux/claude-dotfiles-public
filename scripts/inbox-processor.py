#!/usr/bin/env python3
"""
inbox-processor.py - File inbox routing processor with smart renaming

Parses INBOX_RULES.md and routes files to appropriate destinations.
Phase 2: Content detection + Smart renaming for better RAG indexing.
Phase 3: RAG integration for automatic indexing after move.

Usage:
    inbox-processor.py <inbox_path> [--dry-run] [--file <specific_file>] [--no-rename] [--no-rag]
    inbox-processor.py --show-rules <inbox_path>
    inbox-processor.py --show-log <inbox_path>
"""

import os
import sys
import json
import re
import shutil
import fnmatch
import unicodedata
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, List
import argparse


class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    RED = '\033[0;31m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    NC = '\033[0m'  # No Color


def print_header(msg: str):
    print(f"{Colors.BLUE}═══ {msg} ═══{Colors.NC}")


def print_success(msg: str):
    print(f"{Colors.GREEN}✓{Colors.NC} {msg}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}→{Colors.NC} {msg}")


def print_error(msg: str):
    print(f"{Colors.RED}✗{Colors.NC} {msg}")


# =============================================================================
# CONTENT DETECTION (Phase 2)
# =============================================================================

# Semantic content patterns for file type detection
CONTENT_PATTERNS = {
    'transcript': {
        'keywords': [
            'transcript', 'attendees', 'speaker', 'meeting notes',
            'recorded by', 'fathom', 'zoom', 'teams meeting',
            'action items', 'discussed', 'call recording'
        ],
        'prefix': 'TRANSCRIPT',
        'confidence_boost': 0.20
    },
    'specification': {
        'keywords': [
            'specification', 'requirements', 'functional spec',
            'technical spec', 'system design', 'architecture',
            'data model', 'ERD', 'entity relationship'
        ],
        'prefix': 'SPEC',
        'confidence_boost': 0.15
    },
    'requirements': {
        'keywords': [
            'requirements', 'user story', 'acceptance criteria',
            'FR-', 'NFR-', 'functional requirement', 'non-functional',
            'must have', 'should have', 'could have'
        ],
        'prefix': 'REQ',
        'confidence_boost': 0.15
    },
    'meeting_notes': {
        'keywords': [
            'meeting notes', 'minutes', 'agenda', 'attendees',
            'decisions made', 'next steps', 'follow-up'
        ],
        'prefix': 'NOTES',
        'confidence_boost': 0.15
    },
    'data_export': {
        'keywords': [
            'export', 'report', 'data extract', 'analytics',
            'dashboard', 'metrics', 'KPI'
        ],
        'prefix': 'DATA',
        'confidence_boost': 0.10
    },
    'hubspot': {
        'keywords': [
            'hubspot', 'workflow', 'custom object', 'pipeline',
            'deal stage', 'contact property', 'automation',
            'crm', 'marketing hub', 'sales hub'
        ],
        'prefix': None,  # No special prefix, just boost
        'confidence_boost': 0.15
    },
    'integration': {
        'keywords': [
            'integration', 'api', 'endpoint', 'webhook',
            'sync', 'middleware', 'ETL', 'data flow'
        ],
        'prefix': 'INT',
        'confidence_boost': 0.10
    },
    'sow': {
        'keywords': [
            'statement of work', 'scope of work', 'deliverables',
            'milestones', 'payment terms', 'project timeline'
        ],
        'prefix': 'SOW',
        'confidence_boost': 0.20
    }
}

# File extension to text-readable mapping
TEXT_EXTENSIONS = {
    '.txt', '.md', '.json', '.yaml', '.yml', '.py', '.js', '.ts',
    '.html', '.css', '.xml', '.csv', '.rst', '.tex', '.log'
}


def detect_content_type(filepath: str) -> Tuple[Optional[str], float, List[str]]:
    """
    Analyze file content to detect semantic type.
    Returns: (content_type, confidence_boost, matched_keywords)
    """
    # Skip large files (> 10MB)
    try:
        if os.path.getsize(filepath) > 10_000_000:
            return None, 0.0, []
    except OSError:
        return None, 0.0, []

    ext = os.path.splitext(filepath)[1].lower()

    # Only analyze text files
    if ext not in TEXT_EXTENSIONS:
        return None, 0.0, []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            # Read first 50KB for analysis (enough for detection)
            content = f.read(50000).lower()
    except Exception:
        return None, 0.0, []

    best_match = None
    best_boost = 0.0
    best_keywords = []

    for content_type, config in CONTENT_PATTERNS.items():
        keywords = config['keywords']
        matched = [kw for kw in keywords if kw.lower() in content]

        if matched:
            # More matches = higher confidence
            match_ratio = len(matched) / len(keywords)
            boost = config['confidence_boost'] * (0.5 + 0.5 * match_ratio)

            if boost > best_boost:
                best_match = content_type
                best_boost = boost
                best_keywords = matched[:5]  # Keep top 5

    return best_match, best_boost, best_keywords


def analyze_content(filepath: str, keywords: list) -> bool:
    """Check if file content contains any keywords (text files only)."""
    try:
        if os.path.getsize(filepath) > 10_000_000:
            return False
    except OSError:
        return False

    ext = os.path.splitext(filepath)[1].lower()
    if ext not in TEXT_EXTENSIONS:
        return False

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(50000).lower()
            return any(kw.lower() in content for kw in keywords)
    except Exception:
        return False


# =============================================================================
# SMART FILE RENAMING (Phase 2)
# =============================================================================

def normalize_filename(filename: str) -> str:
    """
    Normalize filename to kebab-case for better indexing.
    - Remove special characters
    - Convert spaces/underscores to hyphens
    - Lowercase
    - Remove duplicate hyphens
    - Handle version suffixes (v2, V3, etc.)
    """
    base, ext = os.path.splitext(filename)

    # Preserve version numbers
    version_match = re.search(r'[_\s-]?[vV](\d+(?:\.\d+)?)\s*(?:FINAL)?$', base, re.IGNORECASE)
    version_suffix = ''
    if version_match:
        version_suffix = f'-v{version_match.group(1)}'
        base = base[:version_match.start()]

    # Remove common noise words
    noise_words = ['final', 'draft', 'copy', 'new', 'old', 'updated']
    for word in noise_words:
        base = re.sub(rf'\b{word}\b', '', base, flags=re.IGNORECASE)

    # Normalize unicode characters
    base = unicodedata.normalize('NFKD', base)
    base = base.encode('ascii', 'ignore').decode('ascii')

    # Replace special characters and spaces with hyphens
    base = re.sub(r'[^\w\s-]', '', base)
    base = re.sub(r'[\s_]+', '-', base)

    # Lowercase and clean up hyphens
    base = base.lower().strip('-')
    base = re.sub(r'-+', '-', base)

    # Add version back
    base = base + version_suffix

    return base + ext.lower()


def extract_date_from_filename(filename: str) -> Optional[str]:
    """Try to extract date from filename patterns."""
    patterns = [
        # YYYY-MM-DD
        r'(\d{4})-(\d{2})-(\d{2})',
        # MM-DD-YYYY or DD-MM-YYYY
        r'(\d{2})-(\d{2})-(\d{4})',
        # Month name patterns: "Jan 23", "January 23", "23 Jan"
        r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s-]+(\d{1,2})\b',
        r'\b(\d{1,2})[\s-]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b',
    ]

    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            # Return indication that date was found (we'll use today's date anyway)
            return "found"

    return None


def detect_semantic_prefix(filename: str, content_type: Optional[str], filepath: str) -> Optional[str]:
    """Determine semantic prefix based on filename patterns and content."""
    filename_lower = filename.lower()

    # Check filename patterns first
    if 'transcript' in filename_lower:
        return 'TRANSCRIPT'
    if filename_lower.startswith('sow') or 'statement of work' in filename_lower:
        return 'SOW'
    if 'spec' in filename_lower or 'specification' in filename_lower:
        return 'SPEC'
    if 'requirement' in filename_lower:
        return 'REQ'
    if 'meeting' in filename_lower or 'notes' in filename_lower or 'minutes' in filename_lower:
        return 'NOTES'
    if 'invoice' in filename_lower or 'receipt' in filename_lower:
        return 'FIN'
    if 'contract' in filename_lower:
        return 'CONTRACT'

    # Fall back to content-detected type
    if content_type and CONTENT_PATTERNS.get(content_type, {}).get('prefix'):
        return CONTENT_PATTERNS[content_type]['prefix']

    return None


def smart_rename(
    filename: str,
    filepath: str,
    content_type: Optional[str] = None,
    add_date: bool = True,
    add_prefix: bool = True,
    normalize: bool = True
) -> Tuple[str, Dict]:
    """
    Generate smart filename for better RAG indexing.

    Returns: (new_filename, rename_info)
    """
    original = filename
    base, ext = os.path.splitext(filename)

    rename_info = {
        'original': original,
        'date_added': False,
        'prefix_added': None,
        'normalized': False
    }

    # Step 1: Normalize the base name
    if normalize:
        base = normalize_filename(base + ext)
        base = os.path.splitext(base)[0]  # Remove ext added by normalize
        rename_info['normalized'] = True

    # Step 2: Detect and add semantic prefix
    prefix = None
    if add_prefix:
        prefix = detect_semantic_prefix(original, content_type, filepath)
        if prefix:
            # Don't add prefix if already present
            if not base.upper().startswith(prefix):
                rename_info['prefix_added'] = prefix

    # Step 3: Add date prefix
    date_str = ''
    if add_date:
        date_str = datetime.now().strftime('%Y-%m-%d')
        rename_info['date_added'] = True

    # Build final filename
    parts = []
    if date_str:
        parts.append(date_str)
    if prefix and rename_info['prefix_added']:
        parts.append(prefix)
    parts.append(base)

    new_filename = '-'.join(parts) + ext.lower()

    # Clean up any double hyphens
    new_filename = re.sub(r'-+', '-', new_filename)

    return new_filename, rename_info


# =============================================================================
# RULE PARSING AND CLASSIFICATION
# =============================================================================

def load_rules(inbox_path: str) -> dict:
    """Load and parse INBOX_RULES.md from the inbox directory."""
    rules_file = os.path.join(inbox_path, 'INBOX_RULES.md')

    default_config = {
        'auto_move': True,
        'confidence_threshold': 0.9,
        'logging': True,
        'renaming': {
            'enabled': True,
            'date_prefix': True,
            'normalize_case': 'kebab',
            'semantic_prefix': True
        },
        'patterns': [],
        'extensions': [],
        'content': [],
        'fallback': {
            'destination': '06-staging/to-review/',
            'action': 'move_to_staging'
        }
    }

    if not os.path.exists(rules_file):
        return default_config

    with open(rules_file, 'r') as f:
        content = f.read()

    config = default_config.copy()

    # Extract YAML blocks
    yaml_blocks = re.findall(r'```yaml\s*\n(.*?)\n```', content, re.DOTALL)

    for block in yaml_blocks:
        lines = block.strip().split('\n')
        current_section = None
        current_rule = {}

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # Top-level config
            if not line.startswith(' ') and ':' in stripped and not stripped.startswith('-'):
                key, val = stripped.split(':', 1)
                key = key.strip()
                val = val.strip()

                if key in ['auto_move', 'logging']:
                    config[key] = val.lower() == 'true'
                elif key == 'confidence_threshold':
                    try:
                        config[key] = float(val)
                    except ValueError:
                        pass
                elif key in ['patterns', 'extensions', 'content', 'fallback', 'renaming']:
                    current_section = key

            # Rule item
            elif stripped.startswith('- '):
                if current_rule and current_section in ['patterns', 'extensions', 'content']:
                    config[current_section].append(current_rule)
                current_rule = {}

                item = stripped[2:].strip()
                if ':' in item:
                    key, val = item.split(':', 1)
                    key = key.strip()
                    val = val.strip().strip('"\'')

                    if val.startswith('[') and val.endswith(']'):
                        items = val[1:-1].split(',')
                        current_rule[key] = [i.strip().strip('"\'') for i in items]
                    else:
                        current_rule[key] = val

            # Continuation of rule
            elif current_rule and ':' in stripped:
                key, val = stripped.split(':', 1)
                key = key.strip()
                val = val.strip().strip('"\'')

                if val.startswith('[') and val.endswith(']'):
                    items = val[1:-1].split(',')
                    current_rule[key] = [i.strip().strip('"\'') for i in items]
                elif val.lower() == 'true':
                    current_rule[key] = True
                elif val.lower() == 'false':
                    current_rule[key] = False
                else:
                    try:
                        current_rule[key] = float(val)
                    except ValueError:
                        current_rule[key] = val

        # Save last rule
        if current_rule:
            if current_section in ['patterns', 'extensions', 'content']:
                config[current_section].append(current_rule)
            elif current_section == 'fallback':
                config['fallback'].update(current_rule)
            elif current_section == 'renaming':
                config['renaming'].update(current_rule)

    return config


def match_pattern(filename: str, pattern: str) -> bool:
    """Match filename against glob pattern."""
    return fnmatch.fnmatch(filename, pattern)


def match_extension(filename: str, extensions: list) -> bool:
    """Check if file extension matches any in the list."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in [e.lower() if e.startswith('.') else f'.{e.lower()}' for e in extensions]


def classify_file(filepath: str, rules: dict) -> Tuple[str, float, str, str, Optional[str], List[str]]:
    """
    Classify a file and return routing info.
    Returns: (destination, confidence, rule_matched, action, content_type, matched_keywords)
    """
    filename = os.path.basename(filepath)

    # Detect content type first (for confidence boosting and prefixes)
    content_type, content_boost, matched_keywords = detect_content_type(filepath)

    # Try pattern rules first (highest priority)
    for rule in rules.get('patterns', []):
        pattern = rule.get('pattern', '')
        if match_pattern(filename, pattern):
            conf = float(rule.get('confidence', 0.9))
            if content_boost > 0:
                conf = min(1.0, conf + content_boost * 0.5)  # Partial boost for patterns
            return (
                rule.get('destination', rules['fallback']['destination']),
                conf,
                f"pattern:{pattern}",
                rule.get('action', 'suggest'),
                content_type,
                matched_keywords
            )

    # Try extension rules
    best_ext_match = None
    for rule in rules.get('extensions', []):
        extensions = rule.get('extensions', [])
        if match_extension(filename, extensions):
            confidence = float(rule.get('confidence', 0.7))
            if best_ext_match is None or confidence > best_ext_match[1]:
                best_ext_match = (
                    rule.get('destination', rules['fallback']['destination']),
                    confidence,
                    f"extension:{','.join(extensions)}",
                    rule.get('action', 'suggest')
                )

    # Try content rules from config (boost confidence)
    config_content_boost = 0
    config_content_rule = None
    for rule in rules.get('content', []):
        keywords = rule.get('contains', [])
        if analyze_content(filepath, keywords):
            boost = float(rule.get('confidence_boost', 0.1))
            if boost > config_content_boost:
                config_content_boost = boost
                config_content_rule = f"content:[{','.join(keywords[:3])}...]"

    # Combine boosts
    total_boost = max(content_boost, config_content_boost)

    # Return best extension match with content boost
    if best_ext_match:
        dest, conf, rule_str, action = best_ext_match
        if total_boost > 0:
            conf = min(1.0, conf + total_boost)
            if config_content_rule:
                rule_str = f"{rule_str}+{config_content_rule}"
            elif content_type:
                rule_str = f"{rule_str}+content:{content_type}"
        return (dest, conf, rule_str, action, content_type, matched_keywords)

    # Fallback
    return (
        rules['fallback']['destination'],
        0.0,
        'fallback',
        rules['fallback'].get('action', 'move_to_staging'),
        content_type,
        matched_keywords
    )


# =============================================================================
# RAG INTEGRATION (Phase 3)
# =============================================================================

# Extensions that can be indexed by RAG
RAG_INDEXABLE_EXTENSIONS = {
    '.md', '.txt', '.json', '.pdf', '.docx', '.html', '.yaml', '.yml',
    '.sql', '.graphql', '.toml', '.csv', '.py', '.js', '.ts', '.tsx', '.jsx'
}


def find_rag_dir(filepath: str) -> Optional[str]:
    """Find the .rag directory for a given file path."""
    check_path = os.path.dirname(os.path.abspath(filepath))
    while check_path != '/':
        rag_dir = os.path.join(check_path, '.rag')
        if os.path.isdir(rag_dir):
            return check_path  # Return project path, not rag dir
        check_path = os.path.dirname(check_path)
    return None


def is_rag_indexable(filepath: str) -> bool:
    """Check if file can be indexed by RAG."""
    ext = os.path.splitext(filepath)[1].lower()
    return ext in RAG_INDEXABLE_EXTENSIONS


def index_to_rag(filepath: str, project_path: str) -> Tuple[bool, str]:
    """
    Index a file to RAG using the MCP server.
    Returns: (success, message)
    """
    if not os.path.exists(filepath):
        return False, "File not found"

    if not is_rag_indexable(filepath):
        return False, "File type not indexable"

    rag_dir = os.path.join(project_path, '.rag')
    if not os.path.isdir(rag_dir):
        return False, "No .rag directory found"

    try:
        # Use the RAG server directly via uv
        result = subprocess.run(
            [
                os.path.expanduser('~/.local/bin/uv'),
                'run',
                '--directory', os.path.expanduser('~/.claude/mcp-servers/rag-server'),
                'python', '-c',
                f'''
import sys
sys.path.insert(0, '${HOME}/.claude/mcp-servers/rag-server/src')
from rag_server.server import rag_index
result = rag_index("{filepath}", "{project_path}")
print("OK" if result else "FAIL")
'''
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and 'OK' in result.stdout:
            return True, "Indexed successfully"
        else:
            return False, result.stderr or "Index failed"

    except subprocess.TimeoutExpired:
        return False, "Indexing timed out"
    except FileNotFoundError:
        return False, "uv not found - RAG indexing unavailable"
    except Exception as e:
        return False, str(e)


# =============================================================================
# FILE PROCESSING
# =============================================================================

def get_unique_dest_path(dest_dir: str, filename: str) -> str:
    """Get a unique destination path, appending timestamp if needed."""
    dest_path = os.path.join(dest_dir, filename)

    if not os.path.exists(dest_path):
        return dest_path

    # Append timestamp
    base, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime('%H%M%S')
    new_filename = f"{base}-{timestamp}{ext}"
    return os.path.join(dest_dir, new_filename)


def log_action(inbox_path: str, entry: dict):
    """Append action to .inbox_log.json."""
    log_file = os.path.join(inbox_path, '.inbox_log.json')

    try:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_data = json.load(f)
        else:
            log_data = {'version': '1.0', 'entries': []}

        log_data['entries'].append(entry)

        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
    except Exception as e:
        print_warning(f"Failed to update log: {e}")


def process_inbox(
    inbox_path: str,
    dry_run: bool = False,
    specific_file: str = None,
    no_rename: bool = False,
    no_rag: bool = False,
    force_auto: bool = False
) -> dict:
    """Process files in inbox and return results."""
    results = {
        'auto_moved': [],
        'suggestions': [],
        'skipped': [],
        'fallback': [],
        'errors': [],
        'rag_indexed': []
    }

    inbox_path = os.path.abspath(inbox_path)
    project_root = os.path.dirname(inbox_path)

    # Check if project has RAG enabled
    rag_enabled = os.path.isdir(os.path.join(project_root, '.rag')) and not no_rag

    if not os.path.exists(inbox_path):
        print_error(f"Inbox not found: {inbox_path}")
        print_warning("Run /inbox init to create one.")
        return results

    rules = load_rules(inbox_path)
    threshold = rules.get('confidence_threshold', 0.9)
    rename_config = rules.get('renaming', {})
    do_rename = rename_config.get('enabled', True) and not no_rename

    # Get files to process
    if specific_file:
        files = [os.path.join(inbox_path, specific_file)] if os.path.exists(os.path.join(inbox_path, specific_file)) else []
    else:
        files = [
            os.path.join(inbox_path, f)
            for f in os.listdir(inbox_path)
            if os.path.isfile(os.path.join(inbox_path, f))
            and not f.startswith('.')
            and f != 'INBOX_RULES.md'
        ]

    if not files:
        print_warning("Inbox is empty.")
        return results

    print_header(f"Processing {len(files)} file(s)")
    if do_rename:
        print(f"{Colors.CYAN}Smart renaming: enabled{Colors.NC}")
    if rag_enabled:
        print(f"{Colors.CYAN}RAG indexing: enabled{Colors.NC}")
    print()

    for filepath in files:
        filename = os.path.basename(filepath)
        dest, confidence, rule_matched, action, content_type, keywords = classify_file(filepath, rules)

        # Smart rename
        new_filename = filename
        rename_info = None
        if do_rename:
            new_filename, rename_info = smart_rename(
                filename,
                filepath,
                content_type=content_type,
                add_date=rename_config.get('date_prefix', True),
                add_prefix=rename_config.get('semantic_prefix', True),
                normalize=rename_config.get('normalize_case', 'kebab') != 'none'
            )

        # Resolve destination path
        if dest.startswith('~'):
            dest_dir = os.path.expanduser(dest)
        elif not os.path.isabs(dest):
            dest_dir = os.path.join(project_root, dest)
        else:
            dest_dir = dest

        # Determine what to do
        if action == 'skip':
            results['skipped'].append({
                'file': filename,
                'reason': f"Rule {rule_matched} specifies skip"
            })
            print(f"  {Colors.YELLOW}SKIP{Colors.NC}: {filename}")
            continue

        # Show content detection info
        content_info = ""
        if content_type:
            content_info = f" [{Colors.MAGENTA}{content_type}{Colors.NC}]"

        # In force_auto mode, move everything (even suggestions)
        should_auto_move = (
            (action == 'auto_move' and confidence >= threshold and rules.get('auto_move', True))
            or force_auto
        )

        if should_auto_move and action != 'skip':
            if not dry_run:
                try:
                    os.makedirs(dest_dir, exist_ok=True)
                    dest_path = get_unique_dest_path(dest_dir, new_filename)
                    shutil.move(filepath, dest_path)

                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'file': filename,
                        'renamed_to': new_filename if new_filename != filename else None,
                        'source': filepath,
                        'destination': dest_path,
                        'rule_matched': rule_matched,
                        'content_type': content_type,
                        'confidence': confidence,
                        'action': 'auto_move',
                        'status': 'success'
                    }
                    if rename_info:
                        log_entry['rename_info'] = rename_info
                    log_action(inbox_path, log_entry)

                    results['auto_moved'].append({
                        'file': filename,
                        'renamed_to': new_filename if new_filename != filename else None,
                        'destination': os.path.relpath(dest_path, project_root),
                        'confidence': confidence,
                        'content_type': content_type,
                        'rule': rule_matched
                    })

                    print(f"  {Colors.GREEN}AUTO-MOVED{Colors.NC}: {filename}{content_info}")
                    if new_filename != filename:
                        print(f"       {Colors.CYAN}Renamed:{Colors.NC} {new_filename}")
                    print(f"       → {os.path.relpath(dest_path, project_root)} ({int(confidence*100)}%)")

                    # RAG indexing (Phase 3)
                    if rag_enabled and is_rag_indexable(dest_path):
                        rag_success, rag_msg = index_to_rag(dest_path, project_root)
                        if rag_success:
                            print(f"       {Colors.MAGENTA}RAG:{Colors.NC} Indexed")
                            results['rag_indexed'].append(new_filename)
                        else:
                            print(f"       {Colors.YELLOW}RAG:{Colors.NC} {rag_msg}")

                except Exception as e:
                    results['errors'].append({'file': filename, 'error': str(e)})
                    print_error(f"Failed to move {filename}: {e}")
            else:
                print(f"  {Colors.CYAN}[DRY-RUN]{Colors.NC} AUTO-MOVE: {filename}{content_info}")
                if new_filename != filename:
                    print(f"       {Colors.CYAN}Would rename:{Colors.NC} {new_filename}")
                print(f"       → {dest} ({int(confidence*100)}%)")
                print(f"       Rule: {rule_matched}")
                results['auto_moved'].append({
                    'file': filename,
                    'renamed_to': new_filename if new_filename != filename else None,
                    'destination': dest,
                    'confidence': confidence,
                    'content_type': content_type,
                    'rule': rule_matched
                })

        elif rule_matched == 'fallback':
            if not dry_run:
                try:
                    os.makedirs(dest_dir, exist_ok=True)
                    dest_path = get_unique_dest_path(dest_dir, new_filename)
                    shutil.move(filepath, dest_path)

                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'file': filename,
                        'renamed_to': new_filename if new_filename != filename else None,
                        'source': filepath,
                        'destination': dest_path,
                        'rule_matched': 'fallback',
                        'content_type': content_type,
                        'confidence': 0,
                        'action': 'fallback',
                        'status': 'success'
                    }
                    log_action(inbox_path, log_entry)

                    results['fallback'].append({
                        'file': filename,
                        'renamed_to': new_filename if new_filename != filename else None,
                        'destination': os.path.relpath(dest_path, project_root),
                        'content_type': content_type
                    })

                    print(f"  {Colors.YELLOW}FALLBACK{Colors.NC}: {filename}{content_info}")
                    if new_filename != filename:
                        print(f"       {Colors.CYAN}Renamed:{Colors.NC} {new_filename}")
                    print(f"       → {os.path.relpath(dest_path, project_root)}")

                    # RAG indexing (Phase 3) - also for fallback files
                    if rag_enabled and is_rag_indexable(dest_path):
                        rag_success, rag_msg = index_to_rag(dest_path, project_root)
                        if rag_success:
                            print(f"       {Colors.MAGENTA}RAG:{Colors.NC} Indexed")
                            results['rag_indexed'].append(new_filename)
                        else:
                            print(f"       {Colors.YELLOW}RAG:{Colors.NC} {rag_msg}")

                except Exception as e:
                    results['errors'].append({'file': filename, 'error': str(e)})
                    print_error(f"Failed to move {filename}: {e}")
            else:
                print(f"  {Colors.CYAN}[DRY-RUN]{Colors.NC} FALLBACK: {filename}{content_info}")
                if new_filename != filename:
                    print(f"       {Colors.CYAN}Would rename:{Colors.NC} {new_filename}")
                print(f"       → {dest}")
                results['fallback'].append({
                    'file': filename,
                    'renamed_to': new_filename if new_filename != filename else None,
                    'destination': dest,
                    'content_type': content_type
                })

        else:
            # Suggestion (needs user confirmation)
            results['suggestions'].append({
                'file': filename,
                'new_filename': new_filename,
                'filepath': filepath,
                'destination': dest,
                'dest_dir': dest_dir,
                'confidence': confidence,
                'content_type': content_type,
                'keywords': keywords,
                'rule': rule_matched,
                'action': action,
                'rename_info': rename_info
            })

            if dry_run:
                print(f"  {Colors.CYAN}[DRY-RUN]{Colors.NC} SUGGEST: {filename}{content_info}")
                if new_filename != filename:
                    print(f"       {Colors.CYAN}Would rename:{Colors.NC} {new_filename}")
                print(f"       → {dest} ({int(confidence*100)}%)")
                print(f"       Rule: {rule_matched}")
            else:
                print(f"  {Colors.YELLOW}SUGGESTION{Colors.NC}: {filename}{content_info}")
                if new_filename != filename:
                    print(f"       {Colors.CYAN}Suggested name:{Colors.NC} {new_filename}")
                print(f"       → {dest} ({int(confidence*100)}%)")

        print()

    return results


def show_rules(inbox_path: str):
    """Display current routing rules."""
    rules = load_rules(inbox_path)

    print_header("Current Inbox Rules")
    print()
    print(f"Source: {inbox_path}/INBOX_RULES.md")
    print(f"Auto-move threshold: {int(rules.get('confidence_threshold', 0.9) * 100)}%")
    print(f"Auto-move enabled: {rules.get('auto_move', True)}")

    rename = rules.get('renaming', {})
    print(f"\nRenaming: {rename.get('enabled', True)}")
    if rename.get('enabled', True):
        print(f"  • Date prefix: {rename.get('date_prefix', True)}")
        print(f"  • Semantic prefix: {rename.get('semantic_prefix', True)}")
        print(f"  • Normalize: {rename.get('normalize_case', 'kebab')}")
    print()

    patterns = rules.get('patterns', [])
    if patterns:
        print(f"Pattern Rules ({len(patterns)}):")
        for r in patterns[:5]:
            action = r.get('action', 'suggest')
            dest = r.get('destination', 'unknown')
            print(f"  • {r.get('pattern', '?')} → {dest} ({action})")
        if len(patterns) > 5:
            print(f"  ... and {len(patterns) - 5} more")
        print()

    extensions = rules.get('extensions', [])
    if extensions:
        print(f"Extension Rules ({len(extensions)}):")
        for r in extensions[:5]:
            action = r.get('action', 'suggest')
            dest = r.get('destination', 'unknown')
            exts = ', '.join(r.get('extensions', []))
            print(f"  • {exts} → {dest} ({action})")
        if len(extensions) > 5:
            print(f"  ... and {len(extensions) - 5} more")
        print()

    content = rules.get('content', [])
    if content:
        print(f"Content Rules ({len(content)}):")
        for r in content[:3]:
            keywords = r.get('contains', [])[:3]
            boost = r.get('confidence_boost', 0.1)
            print(f"  • [{', '.join(keywords)}...] → confidence +{int(boost*100)}%")
        print()

    print(f"Built-in Content Detection ({len(CONTENT_PATTERNS)} types):")
    for ctype, config in list(CONTENT_PATTERNS.items())[:4]:
        prefix = config.get('prefix', '-')
        boost = config.get('confidence_boost', 0)
        print(f"  • {ctype}: prefix={prefix}, boost=+{int(boost*100)}%")
    print(f"  ... and {len(CONTENT_PATTERNS) - 4} more")
    print()

    print(f"Fallback: {rules['fallback']['destination']}")


def show_log(inbox_path: str, limit: int = 10):
    """Display recent inbox actions."""
    log_file = os.path.join(inbox_path, '.inbox_log.json')

    if not os.path.exists(log_file):
        print_warning("No log file found.")
        return

    with open(log_file, 'r') as f:
        log_data = json.load(f)

    entries = log_data.get('entries', [])

    print_header(f"Recent Inbox Actions (last {limit})")
    print()

    for entry in entries[-limit:]:
        ts = entry.get('timestamp', '?')[:19]
        file = entry.get('file', '?')
        renamed = entry.get('renamed_to')
        action = entry.get('action', '?')
        dest = entry.get('destination', '?')
        ctype = entry.get('content_type', '')

        if action == 'auto_move':
            symbol = Colors.GREEN + '✓' + Colors.NC
        elif action == 'user_confirmed':
            symbol = Colors.BLUE + '✓' + Colors.NC
        elif action == 'fallback':
            symbol = Colors.YELLOW + '→' + Colors.NC
        else:
            symbol = '?'

        type_str = f" [{ctype}]" if ctype else ""
        print(f"{symbol} [{ts}] {file}{type_str}")
        if renamed and renamed != file:
            print(f"   Renamed: {renamed}")
        print(f"   → {dest}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='File inbox routing processor with smart renaming',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 00-inbox                      # Process all files
  %(prog)s 00-inbox --dry-run            # Preview without moving
  %(prog)s 00-inbox --no-rename          # Move without renaming
  %(prog)s --show-rules 00-inbox         # Display current rules
  %(prog)s --show-log 00-inbox           # Show recent actions
        """
    )
    parser.add_argument('inbox_path', nargs='?', default='00-inbox',
                        help='Path to inbox directory')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview without moving files')
    parser.add_argument('--file', type=str,
                        help='Process specific file only')
    parser.add_argument('--no-rename', action='store_true',
                        help='Disable smart renaming')
    parser.add_argument('--no-rag', action='store_true',
                        help='Disable RAG indexing after move')
    parser.add_argument('--force-auto', action='store_true',
                        help='Auto-move ALL files (skip confirmation)')
    parser.add_argument('--show-rules', action='store_true',
                        help='Display current routing rules')
    parser.add_argument('--show-log', action='store_true',
                        help='Display recent actions')
    parser.add_argument('--json', action='store_true',
                        help='Output results as JSON')

    args = parser.parse_args()

    if args.show_rules:
        show_rules(args.inbox_path)
    elif args.show_log:
        show_log(args.inbox_path)
    else:
        results = process_inbox(
            args.inbox_path,
            dry_run=args.dry_run,
            specific_file=args.file,
            no_rename=args.no_rename,
            no_rag=args.no_rag,
            force_auto=args.force_auto
        )

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print()
            print_header("Summary")
            print()
            print(f"Auto-moved: {len(results['auto_moved'])} files")
            print(f"Suggestions: {len(results['suggestions'])} files (need confirmation)")
            print(f"Fallback: {len(results['fallback'])} files")
            print(f"Skipped: {len(results['skipped'])} files")
            if results['rag_indexed']:
                print(f"RAG indexed: {len(results['rag_indexed'])} files")
            if results['errors']:
                print(f"Errors: {len(results['errors'])} files")


if __name__ == '__main__':
    main()
