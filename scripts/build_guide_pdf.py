"""Build a simple PDF guide using only the Python standard library."""

from __future__ import annotations

import re
import textwrap
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "beginner_guide.md"
OUTPUT = ROOT / "docs" / "pediatric_variant_prioritizer_beginner_guide.pdf"

PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT = 54
TOP = 740
LINE_HEIGHT = 14
BODY_SIZE = 10
TITLE_SIZE = 20
H1_SIZE = 15


def main() -> None:
    blocks = parse_markdown(SOURCE.read_text(encoding="utf-8"))
    pages = paginate(blocks)
    pdf = build_pdf(pages)
    OUTPUT.write_bytes(pdf)
    print(f"Wrote {OUTPUT}")


def parse_markdown(markdown: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(("p", " ".join(paragraph)))
            paragraph.clear()

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if not line:
            flush_paragraph()
            blocks.append(("blank", ""))
        elif line.startswith("# "):
            flush_paragraph()
            blocks.append(("title", line[2:].strip()))
        elif line.startswith("## "):
            flush_paragraph()
            blocks.append(("h1", line[3:].strip()))
        elif line.startswith("- "):
            flush_paragraph()
            blocks.append(("bullet", line[2:].strip()))
        elif re.match(r"^\d+\. ", line):
            flush_paragraph()
            blocks.append(("number", line.strip()))
        elif line.startswith("  ->") or line.startswith("data/") or line.startswith("src/"):
            flush_paragraph()
            blocks.append(("mono", line))
        else:
            paragraph.append(line.strip())
    flush_paragraph()
    return blocks


def paginate(blocks: list[tuple[str, str]]) -> list[list[tuple[str, str, int]]]:
    pages: list[list[tuple[str, str, int]]] = [[]]
    y = TOP

    for kind, text in blocks:
        if kind == "blank":
            needed = LINE_HEIGHT
            lines = [""]
            size = BODY_SIZE
        else:
            size = font_size(kind)
            width = line_width(kind)
            prefix = "- " if kind == "bullet" else ""
            lines = wrap_text(prefix + text, width)
            needed = len(lines) * LINE_HEIGHT + extra_space(kind)

        if y - needed < 54:
            pages.append([])
            y = TOP

        for line in lines:
            pages[-1].append((kind, line, size))
            y -= LINE_HEIGHT
        y -= extra_space(kind)

    return pages


def font_size(kind: str) -> int:
    if kind == "title":
        return TITLE_SIZE
    if kind == "h1":
        return H1_SIZE
    return BODY_SIZE


def line_width(kind: str) -> int:
    if kind in {"title", "h1"}:
        return 62
    if kind == "mono":
        return 78
    return 88


def extra_space(kind: str) -> int:
    if kind == "title":
        return 12
    if kind == "h1":
        return 8
    if kind == "blank":
        return 0
    return 2


def wrap_text(text: str, width: int) -> list[str]:
    if not text:
        return [""]
    return textwrap.wrap(
        text,
        width=width,
        break_long_words=False,
        replace_whitespace=True,
    ) or [""]


def build_pdf(pages: list[list[tuple[str, str, int]]]) -> bytes:
    objects: list[bytes] = []

    def add_object(data: bytes) -> int:
        objects.append(data)
        return len(objects)

    catalog_id = add_object(b"<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object(b"")
    font_regular_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_bold_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    page_ids: list[int] = []
    for index, page in enumerate(pages, start=1):
        stream = page_stream(page, index, len(pages))
        compressed = zlib.compress(stream)
        content_id = add_object(
            b"<< /Length "
            + str(len(compressed)).encode()
            + b" /Filter /FlateDecode >>\nstream\n"
            + compressed
            + b"\nendstream"
        )
        page_id = add_object(
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 {font_regular_id} 0 R /F2 {font_bold_id} 0 R >> >> "
            f"/Contents {content_id} 0 R >>".encode()
        )
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()
    assert catalog_id == 1

    return assemble_pdf(objects)


def page_stream(page: list[tuple[str, str, int]], page_number: int, page_count: int) -> bytes:
    commands = ["BT"]
    y = TOP
    for kind, text, size in page:
        font = "F2" if kind in {"title", "h1"} else "F1"
        commands.append(f"/{font} {size} Tf")
        commands.append(f"{LEFT} {y} Td")
        commands.append(f"({escape_pdf_text(text)}) Tj")
        commands.append(f"{-LEFT} {-LINE_HEIGHT} Td")
        y -= LINE_HEIGHT
    commands.append("/F1 9 Tf")
    commands.append(f"{LEFT} 32 Td")
    commands.append(
        f"(Pediatric Variant Prioritizer Beginner Guide - page {page_number} of {page_count}) Tj"
    )
    commands.append("ET")
    return "\n".join(commands).encode("utf-8")


def escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def assemble_pdf(objects: list[bytes]) -> bytes:
    chunks = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets: list[int] = []
    current_offset = len(chunks[0])

    for object_id, data in enumerate(objects, start=1):
        offsets.append(current_offset)
        chunk = f"{object_id} 0 obj\n".encode() + data + b"\nendobj\n"
        chunks.append(chunk)
        current_offset += len(chunk)

    xref_offset = current_offset
    xref = [f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()]
    for offset in offsets:
        xref.append(f"{offset:010d} 00000 n \n".encode())
    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()
    chunks.extend(xref)
    chunks.append(trailer)
    return b"".join(chunks)


if __name__ == "__main__":
    main()
