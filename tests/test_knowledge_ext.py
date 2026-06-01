from pathlib import Path

from zemax_agent.knowledge.models import KnowledgeSource, KnowledgeSourceType, DocumentChunk
from zemax_agent.knowledge.document import DocumentParser, DocumentChunker


class TestDocumentParser:
    def test_parse_markdown(self, tmp_path: Path):
        md = tmp_path / "test.md"
        md.write_text("# Title\n\nParagraph text here.", encoding="utf-8")
        parser = DocumentParser()
        result = parser.parse(md)
        assert "Title" in result
        assert "Paragraph text" in result

    def test_parse_text(self, tmp_path: Path):
        txt = tmp_path / "test.txt"
        txt.write_text("plain text content", encoding="utf-8")
        parser = DocumentParser()
        result = parser.parse(txt)
        assert result == "plain text content"

    def test_parse_html(self, tmp_path: Path):
        html = tmp_path / "test.html"
        html.write_text("<html><body><p>Hello World</p><script>alert('x')</script></body></html>", encoding="utf-8")
        parser = DocumentParser()
        result = parser.parse(html)
        assert "Hello World" in result
        assert "alert" not in result


class TestDocumentChunker:
    def test_chunk_short_text(self):
        source = KnowledgeSource(title="Test Doc", source_type=KnowledgeSourceType.MANUAL)
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
        chunks = chunker.chunk("Short document.", source)
        assert len(chunks) == 1
        assert chunks[0].text == "Short document."

    def test_chunk_long_text(self):
        source = KnowledgeSource(title="Long Doc", source_type=KnowledgeSourceType.OFFICIAL_DOC)
        chunker = DocumentChunker(chunk_size=10, chunk_overlap=2)
        text = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15"
        chunks = chunker.chunk(text, source)
        assert len(chunks) > 1

    def test_chunk_multiple_paragraphs(self):
        source = KnowledgeSource(title="Multi", source_type=KnowledgeSourceType.DESIGN_SPEC)
        chunker = DocumentChunker()
        text = "First paragraph.\n\nSecond paragraph."
        chunks = chunker.chunk(text, source)
        assert len(chunks) == 2

    def test_chunk_metadata(self):
        source = KnowledgeSource(title="Meta Test", source_type=KnowledgeSourceType.OFFICIAL_DOC)
        chunker = DocumentChunker()
        chunks = chunker.chunk("Test content.", source)
        assert chunks[0].source_id == source.id
        assert chunks[0].metadata["source_title"] == "Meta Test"
