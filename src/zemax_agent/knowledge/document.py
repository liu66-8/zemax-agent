from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from zemax_agent.knowledge.models import DocumentChunk, KnowledgeSource


class DocumentParser:
    def parse(self, path: str | Path) -> str:
        path = Path(path)
        suffix = path.suffix.lower()

        if suffix == ".md":
            return path.read_text(encoding="utf-8")
        elif suffix == ".txt":
            return path.read_text(encoding="utf-8")
        elif suffix == ".html":
            return self._parse_html(path.read_text(encoding="utf-8"))
        elif suffix == ".pdf":
            return self._parse_pdf(path)
        else:
            return path.read_text(encoding="utf-8")

    def _parse_html(self, content: str) -> str:
        clean = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r"<style[^>]*>.*?</style>", "", clean, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r"<[^>]+>", " ", clean)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    def _parse_pdf(self, path: Path) -> str:
        try:
            import fitz
            doc = fitz.open(str(path))
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            return text
        except ImportError:
            raise ImportError("PyMuPDF (fitz) is required for PDF parsing. Install with: pip install pymupdf")


class DocumentChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk(self, text: str, source: KnowledgeSource) -> list[DocumentChunk]:
        paragraphs = self._split_paragraphs(text)
        chunks: list[DocumentChunk] = []

        for para_idx, para in enumerate(paragraphs):
            words = para.split()
            if not words:
                continue
            if len(words) <= self._chunk_size:
                chunks.append(DocumentChunk(
                    text=para.strip(),
                    metadata={"paragraph_index": para_idx, "source_title": source.title},
                    chunk_index=para_idx,
                    source_id=source.id,
                ))
                continue

            start = 0
            chunk_idx = 0
            while start < len(words):
                end = min(start + self._chunk_size, len(words))
                chunk_text = " ".join(words[start:end])
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    metadata={
                        "paragraph_index": para_idx,
                        "source_title": source.title,
                        "word_start": start,
                        "word_end": end,
                    },
                    chunk_index=para_idx * 1000 + chunk_idx,
                    source_id=source.id,
                ))
                start += self._chunk_size - self._chunk_overlap
                chunk_idx += 1

        return chunks

    def _split_paragraphs(self, text: str) -> list[str]:
        paras = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paras if p.strip()]
