"""
Intelligent PDF / text extractor for Policy RAG.

Pipeline:
  1. Parse PDF with pypdf (page-aware, handles Thai Unicode).
  2. Detect structure: numbered headings, ALL-CAPS titles, Thai-style section markers.
  3. Group text into sections (heading + body).
  4. Auto-tag each section by keyword matching.
  5. Note image/figure presence on each page.
  6. Return list of ExtractedSection for policy_rag to store.

For plain-text (.txt / .md) files a lightweight heading detector is used instead.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field


# ──────────────────────────────────────────────────────────────────────────────
# Keyword taxonomy for auto-tagging
# ──────────────────────────────────────────────────────────────────────────────

KEYWORD_TAGS: dict[str, list[str]] = {
    "refund":        ["คืนเงิน", "refund", "เงินคืน", "ชำระคืน", "คืนชำระ"],
    "return":        ["คืนสินค้า", "return", "ส่งคืน", "รับคืน"],
    "shipping":      ["จัดส่ง", "shipping", "ขนส่ง", "พัสดุ", "delivery", "ส่งของ", "ส่งสินค้า"],
    "compensation":  ["ชดเชย", "compensation", "ค่าชดเชย", "ชดใช้", "compensate"],
    "sla":           ["sla", "service level", "ระยะเวลา", "กำหนดเวลา", "deadline"],
    "fraud":         ["ฉ้อโกง", "fraud", "ปลอม", "หลอก", "ทุจริต"],
    "seller":        ["ร้านค้า", "seller", "ผู้ขาย", "merchant", "shop"],
    "penalty":       ["บทลงโทษ", "penalty", "ปรับ", "ระงับ", "fine", "suspension"],
    "approval":      ["อนุมัติ", "approval", "approve", "ผู้อนุมัติ", "supervisor"],
    "policy":        ["นโยบาย", "policy", "ข้อกำหนด", "เงื่อนไข", "condition", "term"],
    "image":         ["[image]", "[figure]", "[chart]", "[graph]", "[table]"],
}


# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ExtractedSection:
    heading: str          # detected heading (empty string if none)
    text: str             # body text of the section
    page_number: int      # 1-based page number (0 for plain text)
    tags: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Heading detection
# ──────────────────────────────────────────────────────────────────────────────

_NUMBERED_HEADING = re.compile(
    r'^(\d+\.|[ก-ฮ]\.|[IVXivx]+\.|ข้อ\s*\d+|หัวข้อ\s*\d*|หมวด\s*\d*)\s+',
    re.UNICODE,
)

_THAI_SECTION_PREFIX = re.compile(
    r'^(นโยบาย|เงื่อนไข|ขั้นตอน|กรณี|ระยะเวลา|ผู้|การ|สิทธิ์|ค่า)',
    re.UNICODE,
)


def _is_heading(line: str) -> bool:
    """Return True if the line looks like a section heading."""
    line = line.strip()
    if not line or len(line) > 120:
        return False
    # Numbered: "1.", "1.1", "ข้อ 3", "หมวด 2"
    if _NUMBERED_HEADING.match(line):
        return True
    # ALL CAPS English headings (short)
    if line.isupper() and 3 < len(line) < 80 and not line.isdigit():
        return True
    # Ends with colon and is short → likely a label/heading
    if line.endswith(":") and len(line) < 70:
        return True
    # Thai short lines starting with common section words
    if _THAI_SECTION_PREFIX.match(line) and len(line) < 60:
        return True
    return False


# ──────────────────────────────────────────────────────────────────────────────
# Auto-tagging
# ──────────────────────────────────────────────────────────────────────────────

def _auto_tag(text: str, heading: str) -> list[str]:
    """Return list of matching tag labels from KEYWORD_TAGS."""
    combined = (heading + " " + text).lower()
    return [tag for tag, kws in KEYWORD_TAGS.items() if any(kw.lower() in combined for kw in kws)]


# ──────────────────────────────────────────────────────────────────────────────
# Text → sections (used for both plain text and pypdf-extracted text)
# ──────────────────────────────────────────────────────────────────────────────

def _lines_to_sections(lines: list[str], page_number: int = 0) -> list[ExtractedSection]:
    """Group lines into sections by heading detection."""
    sections: list[ExtractedSection] = []
    current_heading = ""
    current_lines: list[str] = []

    def _flush() -> None:
        body = "\n".join(current_lines).strip()
        if body or current_heading:
            tags = _auto_tag(body, current_heading)
            sections.append(ExtractedSection(
                heading=current_heading,
                text=body,
                page_number=page_number,
                tags=tags,
            ))

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_lines.append("")
            continue
        if _is_heading(stripped):
            _flush()
            current_heading = stripped
            current_lines = []
        else:
            current_lines.append(stripped)

    _flush()
    return [s for s in sections if s.text.strip() or s.heading.strip()]


# ──────────────────────────────────────────────────────────────────────────────
# PDF extraction (pypdf)
# ──────────────────────────────────────────────────────────────────────────────

def _describe_images_on_page(page) -> list[str]:
    """Return placeholder descriptions for images/figures found on the page."""
    descriptions: list[str] = []
    try:
        images = page.images
        for i, img in enumerate(images, 1):
            w = getattr(img, "width", "?")
            h = getattr(img, "height", "?")
            descriptions.append(f"[image-{i}: {w}×{h}px — visual content, see original PDF page {page.page_number + 1}]")
    except Exception:
        pass
    return descriptions


def extract_from_pdf(data: bytes) -> list[ExtractedSection]:
    """
    Extract structured sections from a PDF file using pypdf.
    Returns list of ExtractedSection, one per detected section.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        # Fall back to plain text parsing if pypdf not available
        text = data.decode("utf-8", errors="replace")
        return extract_from_text(text)

    sections: list[ExtractedSection] = []

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        # Corrupted PDF — return single section with raw bytes decoded
        raw = data.decode("latin-1", errors="replace")
        return [ExtractedSection(
            heading="[PDF parse error]",
            text=raw[:5000],
            page_number=1,
            tags=["policy"],
        )]

    for page_num, page in enumerate(reader.pages, start=1):
        # Extract text
        try:
            raw_text = page.extract_text(extraction_mode="layout") or ""
        except Exception:
            try:
                raw_text = page.extract_text() or ""
            except Exception:
                raw_text = ""

        # Describe images on this page
        img_descriptions = _describe_images_on_page(page)

        lines = raw_text.splitlines()
        page_sections = _lines_to_sections(lines, page_number=page_num)

        # Attach image descriptions to last section on the page (or create one)
        if img_descriptions:
            img_text = "\n".join(img_descriptions)
            if page_sections:
                page_sections[-1].text += "\n" + img_text
                if "image" not in page_sections[-1].tags:
                    page_sections[-1].tags.append("image")
            else:
                page_sections.append(ExtractedSection(
                    heading=f"[Page {page_num} — Visual Content]",
                    text=img_text,
                    page_number=page_num,
                    tags=["image"],
                ))

        sections.extend(page_sections)

    # If pypdf extracted nothing useful, try raw decode
    if not sections:
        all_text = "\n".join(
            (page.extract_text() or "") for page in reader.pages
        )
        if all_text.strip():
            return extract_from_text(all_text)
        return [ExtractedSection(
            heading="[No readable text]",
            text="This PDF may contain only scanned images. Please provide a text version.",
            page_number=1,
            tags=["policy"],
        )]

    return sections


# ──────────────────────────────────────────────────────────────────────────────
# Plain text / Markdown extraction
# ──────────────────────────────────────────────────────────────────────────────

def extract_from_text(text: str) -> list[ExtractedSection]:
    """
    Extract structured sections from plain text or Markdown.
    Markdown headings (# / ## / ###) are treated as headings.
    """
    lines: list[str] = []
    for raw_line in text.splitlines():
        # Convert Markdown headings to plain heading style
        md_match = re.match(r'^(#{1,4})\s+(.*)', raw_line.strip())
        if md_match:
            lines.append(md_match.group(2).strip())
        else:
            lines.append(raw_line)

    sections = _lines_to_sections(lines, page_number=0)

    # If no structure detected, treat entire text as one section
    if not sections:
        tags = _auto_tag(text, "")
        sections = [ExtractedSection(heading="", text=text.strip(), page_number=0, tags=tags or ["policy"])]

    return sections


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────────────────

def extract_sections(data: bytes, filename: str) -> list[ExtractedSection]:
    """
    Auto-detect format from filename and extract sections.
    Supported: .pdf, .txt, .md (anything else treated as text).
    """
    name_lower = filename.lower()
    if name_lower.endswith(".pdf"):
        return extract_from_pdf(data)
    else:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1", errors="replace")
        return extract_from_text(text)


def sections_to_full_text(sections: list[ExtractedSection]) -> str:
    """
    Flatten sections back to a single string for storing as Policy.content.
    """
    parts: list[str] = []
    for section in sections:
        if section.heading:
            parts.append(section.heading)
        if section.text:
            parts.append(section.text)
        parts.append("")  # blank line between sections
    return "\n".join(parts).strip()
