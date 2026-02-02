"""Code file parser with syntax awareness."""
from pathlib import Path
from typing import Dict, Any
import re
from . import register_parser

class CodeParser:
    extensions = [
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".java", ".go", ".rs", ".rb", ".php",
        ".c", ".cpp", ".h", ".hpp", ".cs",
        ".swift", ".kt", ".scala", ".r",
        ".sh", ".bash", ".zsh",
        ".sql", ".graphql",
        ".yaml", ".yml", ".json", ".toml",
        ".css", ".scss", ".less",
        ".vue", ".svelte",
    ]

    def parse(self, file_path: Path) -> str:
        """Read code file with some structure annotation."""
        content = file_path.read_text(encoding="utf-8", errors="replace")

        # Add file path as context
        header = f"# File: {file_path.name}\n"

        return header + content

    def get_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from code file."""
        content = file_path.read_text(encoding="utf-8", errors="replace")
        stat = file_path.stat()

        # Count lines
        lines = content.split("\n")

        # Try to extract some structure based on language
        ext = file_path.suffix.lower()
        functions = []
        classes = []

        if ext in [".py"]:
            functions = re.findall(r"^def\s+(\w+)", content, re.MULTILINE)
            classes = re.findall(r"^class\s+(\w+)", content, re.MULTILINE)
        elif ext in [".js", ".ts", ".jsx", ".tsx"]:
            functions = re.findall(r"(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\()", content, re.MULTILINE)
            functions = [f[0] or f[1] for f in functions]
            classes = re.findall(r"class\s+(\w+)", content, re.MULTILINE)
        elif ext in [".go"]:
            functions = re.findall(r"func\s+(?:\([^)]+\)\s*)?(\w+)", content, re.MULTILINE)
        elif ext in [".rs"]:
            functions = re.findall(r"fn\s+(\w+)", content, re.MULTILINE)
            classes = re.findall(r"(?:struct|enum|trait)\s+(\w+)", content, re.MULTILINE)

        return {
            "filename": file_path.name,
            "extension": file_path.suffix,
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime,
            "language": ext.lstrip("."),
            "lines": len(lines),
            "functions": functions[:20],  # Limit to first 20
            "classes": classes[:10],
        }

# Register the parser
register_parser(CodeParser())
