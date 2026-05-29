from __future__ import annotations

from pathlib import Path
import textwrap


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = PROJECT_ROOT / "docs"
SOURCE_MD = DOCS_DIR / "GDD.md"
OUTPUT_PDF = DOCS_DIR / "GDD_Lighthouse_of_Alexandria.pdf"

PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT_MARGIN = 54
RIGHT_MARGIN = 54
TOP_MARGIN = 60
BOTTOM_MARGIN = 54

BODY_SIZE = 11
H1_SIZE = 20
H2_SIZE = 15
H3_SIZE = 12
LINE_GAP = 5


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap(text: str, width: int) -> list[str]:
    return textwrap.wrap(
        text,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    ) or [""]


def _font_for_line(line: str) -> tuple[str, int, int]:
    if line.startswith("# "):
        return "Helvetica-Bold", H1_SIZE, 52
    if line.startswith("## "):
        return "Helvetica-Bold", H2_SIZE, 30
    if line.startswith("### "):
        return "Helvetica-Bold", H3_SIZE, 22
    return "Helvetica", BODY_SIZE, 17


def _text_for_line(line: str) -> tuple[str, int]:
    if line.startswith("# "):
        return line[2:].strip(), 72
    if line.startswith("## "):
        return line[3:].strip(), 84
    if line.startswith("### "):
        return line[4:].strip(), 94
    if line.startswith("- "):
        return f"- {line[2:].strip()}", 86
    if line[:2].isdigit() and line[1:3] == ". ":
        return line.strip(), 82
    return line.strip(), 88


def _paginate(lines: list[str]) -> list[list[tuple[str, str, int, int]]]:
    pages: list[list[tuple[str, str, int, int]]] = []
    current_page: list[tuple[str, str, int, int]] = []
    current_y = PAGE_HEIGHT - TOP_MARGIN

    for raw_line in lines:
        font_name, font_size, spacing_after = _font_for_line(raw_line)
        text, wrap_width = _text_for_line(raw_line)

        if not text:
            current_y -= BODY_SIZE + LINE_GAP
            if current_y < BOTTOM_MARGIN:
                pages.append(current_page)
                current_page = []
                current_y = PAGE_HEIGHT - TOP_MARGIN
            continue

        wrapped_lines = _wrap(text, wrap_width)
        line_height = font_size + LINE_GAP
        needed_height = len(wrapped_lines) * line_height + spacing_after

        if current_y - needed_height < BOTTOM_MARGIN:
            pages.append(current_page)
            current_page = []
            current_y = PAGE_HEIGHT - TOP_MARGIN

        for wrapped in wrapped_lines:
            current_page.append((wrapped, font_name, font_size, current_y))
            current_y -= line_height

        current_y -= spacing_after

    if current_page:
        pages.append(current_page)

    return pages


def _page_stream(page_lines: list[tuple[str, str, int, int]]) -> bytes:
    commands: list[str] = []
    for text, font_name, font_size, y in page_lines:
        font_alias = "F1" if font_name == "Helvetica" else "F2"
        escaped = _escape_pdf_text(text)
        commands.append("BT")
        commands.append(f"/{font_alias} {font_size} Tf")
        commands.append(f"1 0 0 1 {LEFT_MARGIN} {y} Tm")
        commands.append(f"({escaped}) Tj")
        commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def build_pdf(markdown_text: str) -> bytes:
    raw_lines = markdown_text.splitlines()
    pages = _paginate(raw_lines)

    objects: list[bytes] = []

    def add_object(data: bytes) -> int:
        objects.append(data)
        return len(objects)

    font_helvetica = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_bold = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    page_object_ids: list[int] = []
    content_object_ids: list[int] = []

    pages_tree_id = 0

    for page_lines in pages:
        stream = _page_stream(page_lines)
        content_id = add_object(
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"
        )
        content_object_ids.append(content_id)
        page_object_ids.append(0)

    kids_placeholders = " ".join("0 0 R" for _ in pages).encode("ascii")
    pages_tree_id = add_object(
        b"<< /Type /Pages /Kids [" + kids_placeholders + b"] /Count " + str(len(pages)).encode("ascii") + b" >>"
    )

    for index, content_id in enumerate(content_object_ids):
        page_id = add_object(
            (
                f"<< /Type /Page /Parent {pages_tree_id} 0 R "
                f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                f"/Resources << /Font << /F1 {font_helvetica} 0 R /F2 {font_bold} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        page_object_ids[index] = page_id

    kids_ref = " ".join(f"{page_id} 0 R" for page_id in page_object_ids).encode("ascii")
    objects[pages_tree_id - 1] = (
        b"<< /Type /Pages /Kids [" + kids_ref + b"] /Count " + str(len(page_object_ids)).encode("ascii") + b" >>"
    )

    catalog_id = add_object(f"<< /Type /Catalog /Pages {pages_tree_id} 0 R >>".encode("ascii"))

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    output = bytearray(header)
    offsets = [0]

    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{idx} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")

    xref_start = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(output)


def main() -> None:
    markdown_text = SOURCE_MD.read_text(encoding="utf-8")
    OUTPUT_PDF.write_bytes(build_pdf(markdown_text))
    print(f"Generated {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
