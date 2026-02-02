"""Document parsers for various file formats."""
from pathlib import Path
from typing import Protocol, Dict, Any, Optional

class DocumentParser(Protocol):
    """Protocol for document parsers."""
    extensions: list[str]

    def parse(self, file_path: Path) -> str:
        """Extract text content from file."""
        ...

    def get_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from file."""
        ...

# Parser registry
PARSERS: Dict[str, "DocumentParser"] = {}

def register_parser(parser: DocumentParser) -> None:
    """Register a parser for its supported extensions."""
    for ext in parser.extensions:
        PARSERS[ext.lower()] = parser

def get_parser(file_path: Path) -> Optional["DocumentParser"]:
    """Get the appropriate parser for a file."""
    ext = file_path.suffix.lower()
    return PARSERS.get(ext)

def parse_file(file_path: Path) -> tuple[str, Dict[str, Any]]:
    """Parse a file and return content and metadata."""
    parser = get_parser(file_path)
    if parser is None:
        raise ValueError(f"No parser available for {file_path.suffix}")
    return parser.parse(file_path), parser.get_metadata(file_path)

# Import and register all parsers
from . import text, markdown, html, pdf, docx, code

__all__ = ["parse_file", "get_parser", "PARSERS"]
