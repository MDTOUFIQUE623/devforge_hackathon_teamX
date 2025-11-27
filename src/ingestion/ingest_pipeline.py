"""
Ingestion Pipeline using Docling
--------------------------------
Extracts:
- Metadata
- Paragraphs
- Tables (if present)
- Placeholder for entity extraction

Supported formats: txt, pdf, docx, csv
"""

from pathlib import Path
from typing import Dict, Any, List
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import ConversionStatus


class IngestionPipeline:
    SUPPORTED_EXT = {".txt", ".pdf", ".docx", ".csv"}

    def __init__(self):
        """
        Initialize the Docling document converter
        """
        # Use default pipeline options from the installed Docling version.
        # The constructor signature may change across versions, so we avoid
        # passing deprecated/removed keyword arguments like `pipeline_options`.
        self.converter = DocumentConverter()

    def run(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single document and return structured JSON.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"No such file: {file_path}")

        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_EXT:
            raise ValueError(f"Unsupported file extension: {ext}")

        # For plain text files, bypass Docling and read directly.
        if ext == ".txt":
            raw_text = path.read_text(encoding="utf-8", errors="ignore")
            tables = []
        else:
            # Convert document using Docling for supported rich formats
            result = self.converter.convert(str(path))
            if result.status != ConversionStatus.SUCCESS:
                raise RuntimeError(f"Docling conversion failed for {file_path}")

            doc = result.document

            # Extract raw text
            raw_text = getattr(doc, "text", "") or ""

            # Extract tables if available
            tables = getattr(doc, "tables", [])

        # Split text into paragraphs
        paragraphs = self._split_into_paragraphs(raw_text)

        # Placeholder for future entity extraction
        entities = []

        # Metadata
        metadata = {
            "filename": path.name,
            "filesize": path.stat().st_size,
            "extension": path.suffix
        }

        return {
            "source": path.name,
            "type": ext.replace(".", ""),
            "metadata": metadata,
            "paragraphs": paragraphs,
            "tables": tables,
            "entities": entities,
        }

    # -------------------- Internal Methods --------------------
    def _split_into_paragraphs(self, raw_text: str) -> List[Dict[str, Any]]:
        paragraphs = []
        for idx, block in enumerate(raw_text.split("\n\n")):
            block = block.strip()
            if block:
                paragraphs.append({
                    "id": f"p{idx+1}",
                    "text": block
                })
        return paragraphs
