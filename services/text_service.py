import re
from typing import List
from models.schemas import StructuredBlock

class TextService:
    # Character confusion matrix common in OCR of cursive / messy handwriting
    OCR_CORRECTIONS = {
        r'(?<=[a-zA-Z])0(?=[a-zA-Z])': 'o',
        r'(?<=[a-zA-Z])1(?=[a-zA-Z])': 'i',
        r'(?<=[a-zA-Z])5(?=[a-zA-Z])': 's',
        r'\b5(?=[a-zA-Z])': 's',
        r'(?<=[a-zA-Z])2(?=[a-zA-Z])': 'z',
        r'(?<=[a-zA-Z])8(?=[a-zA-Z])': 'B',
        r'(?<=[a-zA-Z])\|(?=[a-zA-Z])': 'I',
    }

    @classmethod
    def clean_ocr_text(cls, raw: str) -> str:
        """Cleans stray HTML, normalizes line breaks, and applies character heuristics."""
        if not raw:
            return ""

        # Remove stray HTML tags
        cleaned = re.sub(r'<[^>]*>', '', raw)

        # Apply internal word corrections
        for pattern, replacement in cls.OCR_CORRECTIONS.items():
            cleaned = re.sub(pattern, replacement, cleaned)

        # Normalize multiple blank lines to double newlines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()

    @classmethod
    def structure_text(cls, raw: str) -> List[StructuredBlock]:
        """Parses cleaned text into typed structural blocks."""
        cleaned = cls.clean_ocr_text(raw)
        lines = cleaned.split('\n')
        blocks: List[StructuredBlock] = []

        current_paragraph: List[str] = []

        def flush_paragraph():
            if current_paragraph:
                content = " ".join(current_paragraph).strip()
                if content:
                    blocks.append(StructuredBlock(type="paragraph", content=content))
                current_paragraph.clear()

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                flush_paragraph()
                continue

            # Check markdown heading
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', trimmed)
            if heading_match:
                flush_paragraph()
                level = len(heading_match.group(1))
                blocks.append(StructuredBlock(type="heading", content=trimmed, level=level))
                continue

            # Check numbered or uppercase heading heuristic
            if (trimmed.isupper() and len(trimmed) > 3 and len(trimmed) < 60) or re.match(r'^\d+\.\s+[A-Z]', trimmed):
                flush_paragraph()
                blocks.append(StructuredBlock(type="heading", content=f"## {trimmed}", level=2))
                continue

            # Check bullet list item
            if re.match(r'^[-*•]\s+(.+)$', trimmed):
                flush_paragraph()
                # Normalize bullets to '-'
                normalized_bullet = re.sub(r'^[*•]\s+', '- ', trimmed)
                blocks.append(StructuredBlock(type="list-item", content=normalized_bullet))
                continue

            # Check numbered list item
            if re.match(r'^\d+[.)]\s+(.+)$', trimmed):
                flush_paragraph()
                blocks.append(StructuredBlock(type="list-item", content=trimmed))
                continue

            # Check blockquote
            if trimmed.startswith('>'):
                flush_paragraph()
                blocks.append(StructuredBlock(type="blockquote", content=trimmed))
                continue

            # Otherwise, regular paragraph text
            current_paragraph.append(trimmed)

        flush_paragraph()
        return blocks

    @classmethod
    def blocks_to_markdown(cls, blocks: List[StructuredBlock]) -> str:
        """Serializes blocks into standard Markdown."""
        rendered = []
        for block in blocks:
            rendered.append(block.content)
        return "\n\n".join(rendered)
