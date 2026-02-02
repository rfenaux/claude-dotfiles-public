"""HTML parser using BeautifulSoup."""
from pathlib import Path
from typing import Dict, Any
from . import register_parser

class HTMLParser:
    extensions = [".html", ".htm", ".xhtml"]

    def parse(self, file_path: Path) -> str:
        """Extract text from HTML."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return file_path.read_text(encoding="utf-8", errors="replace")

        content = file_path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(content, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Get text with some structure preserved
        text = soup.get_text(separator="\n", strip=True)
        return text

    def get_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from HTML."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return {"filename": file_path.name, "extension": file_path.suffix}

        content = file_path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(content, "html.parser")
        stat = file_path.stat()

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else file_path.stem

        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        description = meta_desc.get("content", "") if meta_desc else ""

        return {
            "filename": file_path.name,
            "extension": file_path.suffix,
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime,
            "title": title,
            "description": description,
        }

# Register the parser
register_parser(HTMLParser())
