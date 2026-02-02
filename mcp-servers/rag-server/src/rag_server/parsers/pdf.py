"""PDF parser using pymupdf4llm."""
from pathlib import Path
from typing import Dict, Any
from . import register_parser

class PDFParser:
    extensions = [".pdf"]

    def parse(self, file_path: Path) -> str:
        """Extract text from PDF as markdown."""
        try:
            import pymupdf4llm
            return pymupdf4llm.to_markdown(str(file_path))
        except ImportError:
            # Fallback to basic pymupdf if pymupdf4llm fails
            try:
                import fitz  # pymupdf
                doc = fitz.open(str(file_path))
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
                return text
            except ImportError:
                raise ImportError("PDF parsing requires pymupdf4llm or pymupdf")

    def get_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from PDF."""
        stat = file_path.stat()
        metadata = {
            "filename": file_path.name,
            "extension": file_path.suffix,
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime,
        }

        try:
            import fitz
            doc = fitz.open(str(file_path))
            pdf_meta = doc.metadata
            metadata.update({
                "title": pdf_meta.get("title", file_path.stem),
                "author": pdf_meta.get("author", ""),
                "pages": doc.page_count,
            })
            doc.close()
        except ImportError:
            metadata["title"] = file_path.stem

        return metadata

# Register the parser
register_parser(PDFParser())
