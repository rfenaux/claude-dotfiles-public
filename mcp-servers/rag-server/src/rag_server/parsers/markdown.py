"""Markdown parser."""
from pathlib import Path
from typing import Dict, Any
import re
from . import register_parser

class MarkdownParser:
    extensions = [".md", ".markdown", ".mdown"]

    def parse(self, file_path: Path) -> str:
        """Read markdown file as plain text (preserves structure)."""
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return content

    def get_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata including headers."""
        content = file_path.read_text(encoding="utf-8", errors="replace")
        stat = file_path.stat()

        # Extract title from first H1
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else file_path.stem

        # Extract all headers for structure
        headers = re.findall(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE)

        return {
            "filename": file_path.name,
            "extension": file_path.suffix,
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime,
            "title": title,
            "headers": [{"level": len(h[0]), "text": h[1]} for h in headers],
        }

# Register the parser
register_parser(MarkdownParser())
