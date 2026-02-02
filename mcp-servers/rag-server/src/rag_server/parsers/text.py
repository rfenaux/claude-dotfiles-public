"""Plain text parser."""
from pathlib import Path
from typing import Dict, Any
from . import register_parser

class TextParser:
    extensions = [".txt", ".log", ".ini", ".cfg", ".conf"]

    def parse(self, file_path: Path) -> str:
        """Read plain text file."""
        return file_path.read_text(encoding="utf-8", errors="replace")

    def get_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Get file metadata."""
        stat = file_path.stat()
        return {
            "filename": file_path.name,
            "extension": file_path.suffix,
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime,
        }

# Register the parser
register_parser(TextParser())
