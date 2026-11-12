"""S1 load_prd, part 1: read a PRD (PDF / DOCX / MD / TXT) into normalized Markdown, a section tree,
and atomic Units with stable IDs (SPEC §6 S1).

Deterministic code only - no LLM. Unit IDs are `U-<hash(section path)>-<hash(normalized text)>`,
so they are stable across runs and do not shift when other content is inserted.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import re
import unicodedata
from pathlib import Path

from schemas import ParsedPRD, Section, Unit, UnitKind, normalize_quote, short_hash

SUPPORTED_SUFFIXES = {".pdf", ".docx", ".md", ".markdown", ".txt"}


class PRDReadError(Exception):
    """The PRD file cannot be read or produced no usable content."""


# --------------------------------------------------------------------------- format readers


def _read_pdf(path: Path) -> str:
    import logging

    import pymupdf
    import pymupdf4llm

    # pymupdf prints parser notices (e.g. OCR availability) to stdout; route them to Python logging
    # (visible with --debug) so the console stays clean.
    pymupdf.set_messages(pylogging=True, pylogging_name="pymupdf", pylogging_level=logging.DEBUG)
    with contextlib.redirect_stdout(io.StringIO()):
        return pymupdf4llm.to_markdown(str(path), show_progress=False)


def _docx_list_level(paragraph) -> int | None:
    """Return the list nesting level if the paragraph is a list item, else None."""
    p_pr = paragraph._p.pPr
    if p_pr is not None and p_pr.numPr is not None:
        ilvl = p_pr.numPr.ilvl
        return int(ilvl.val) if ilvl is not None else 0
    style = (paragraph.style.name or "").lower() if paragraph.style is not None else ""
    if "list" in style:
        match = re.search(r"(\d+)$", style)
        return int(match.group(1)) - 1 if match else 0
    return None


def _read_docx(path: Path) -> str:
    import docx
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    document = docx.Document(str(path))
    lines: list[str] = []
    body = document.element.body
    for child in body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            para = Paragraph(child, document)
            text = para.text.strip()
            if not text:
                lines.append("")
                continue
            style = (para.style.name or "") if para.style is not None else ""
            heading = re.match(r"Heading\s*(\d+)", style, re.IGNORECASE)
            if style.lower() == "title":
                lines += [f"# {text}", ""]
            elif heading:
                lines += [f"{'#' * min(int(heading.group(1)), 6)} {text}", ""]
            elif (level := _docx_list_level(para)) is not None:
                lines.append(f"{'  ' * level}- {text}")
            else:
                lines += [text, ""]
        elif tag == "tbl":
            table = Table(child, document)
            rows = [[cell.text.strip().replace("\n", " ") for cell in row.cells] for row in table.rows]
            if rows:
                lines.append("| " + " | ".join(rows[0]) + " |")
                lines.append("|" + "---|" * len(rows[0]))
                lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
                lines.append("")
    return "\n".join(lines)


_SETEXT = re.compile(r"^(=+|-+)\s*$")


def _txt_to_markdown(text: str) -> str:
    """Plain text has no markup: promote setext-underlined and ALL-CAPS lines to headings."""
    raw = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(raw):
        line = raw[i].rstrip()
        nxt = raw[i + 1].strip() if i + 1 < len(raw) else ""
        if line.strip() and _SETEXT.match(nxt) and len(nxt) >= 3:
            out.append(("# " if nxt.startswith("=") else "## ") + line.strip())
            i += 2
            continue
        stripped = line.strip()
        letters = [c for c in stripped if c.isalpha()]
        if (
            letters
            and len(stripped) <= 80
            and stripped.upper() == stripped
            and sum(c.isupper() for c in letters) >= 3
            and not re.match(r"^[-*•]\s", stripped)
        ):
            out.append("## " + stripped.rstrip(":"))
        else:
            out.append(line)
        i += 1
    return "\n".join(out)


def read_document(path: str | Path) -> str:
    """Read a PRD file into (un-normalized) Markdown."""
    path = Path(path)
    if not path.is_file():
        raise PRDReadError(f"PRD file not found: {path}")
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise PRDReadError(f"Unsupported PRD format {suffix!r}. Supported: PDF, DOCX, MD, TXT.")
    if path.stat().st_size == 0:
        raise PRDReadError(f"PRD file is empty: {path}")
    try:
        if suffix == ".pdf":
            return _read_pdf(path)
        if suffix == ".docx":
            return _read_docx(path)
        text = path.read_text(encoding="utf-8-sig")
        return _txt_to_markdown(text) if suffix == ".txt" else text
    except PRDReadError:
        raise
    except UnicodeDecodeError as exc:
        raise PRDReadError(f"PRD file is not valid UTF-8 text: {path}") from exc
    except Exception as exc:  # corrupt PDF/DOCX etc.
        raise PRDReadError(f"Could not read PRD file {path}: {type(exc).__name__}: {exc}") from exc


# --------------------------------------------------------------------------- normalization

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_BULLET = re.compile(r"^(\s*)(?:[-*+•▪◦●]|\d+[.)])\s+(.*)$")
_EMPHASIS = re.compile(r"(\*\*|__)(.+?)\1|(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])")
_TABLE_SEP = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?$")


def _strip_emphasis(text: str) -> str:
    prev = None
    while prev != text:
        prev = text
        text = _EMPHASIS.sub(lambda m: m.group(2) or m.group(3), text)
    return text


def normalize_markdown(markdown: str) -> str:
    """Canonical Markdown: NFKC, emphasis removed, '- ' bullets, no trailing spaces, single blank lines."""
    text = unicodedata.normalize("NFKC", markdown).replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace(" ", " ").replace("​", "")
    out: list[str] = []
    for line in text.split("\n"):
        line = line.rstrip()
        if m := _HEADING.match(line):
            title = _strip_emphasis(m.group(2)).strip()
            line = f"{m.group(1)} {title}" if title else ""
        elif m := _BULLET.match(line):
            indent = len(m.group(1).expandtabs(2)) // 2
            line = f"{'  ' * indent}- {_strip_emphasis(m.group(2)).strip()}"
        else:
            line = _strip_emphasis(line)
        out.append(line)
    collapsed = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
    return collapsed + "\n"


# --------------------------------------------------------------------------- sections and units

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[\"'(\[]?[A-Z0-9])")


def split_sentences(paragraph: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(paragraph.strip()) if s.strip()]


def _path_hash(path: list[str]) -> str:
    return hashlib.sha256(" > ".join(path).encode("utf-8")).hexdigest()[:6]


def _blocks(lines: list[str]) -> list[tuple[UnitKind, str]]:
    """Group a section's body lines into (kind, text) units: bullets, table rows, paragraph sentences."""
    units: list[tuple[UnitKind, str]] = []
    paragraph: list[str] = []
    bullet: list[str] | None = None

    def flush_paragraph() -> None:
        if paragraph:
            units.extend((UnitKind.sentence, s) for s in split_sentences(" ".join(paragraph)))
            paragraph.clear()

    def flush_bullet() -> None:
        nonlocal bullet
        if bullet:
            units.append((UnitKind.bullet, " ".join(bullet)))
        bullet = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            flush_bullet()
            continue
        if m := _BULLET.match(line):
            flush_paragraph()
            flush_bullet()
            bullet = [m.group(2).strip()]
        elif stripped.startswith("|"):
            flush_paragraph()
            flush_bullet()
            if not _TABLE_SEP.match(stripped):
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                if any(cells):
                    units.append((UnitKind.table_row, " | ".join(cells)))
        elif bullet is not None and line.startswith((" ", "\t")):
            bullet.append(stripped)  # wrapped continuation of a bullet
        else:
            flush_bullet()
            paragraph.append(stripped)
    flush_paragraph()
    flush_bullet()
    return units


def build_sections(markdown: str, root_title: str) -> tuple[Section, list[Unit]]:
    """Build the section tree and the ordered unit list from normalized Markdown."""
    root = Section(path=[], title=root_title, level=0)
    stack: list[Section] = [root]
    bodies: dict[int, list[str]] = {id(root): []}
    ordered: list[Section] = [root]

    for line in markdown.split("\n"):
        if m := _HEADING.match(line):
            level, title = len(m.group(1)), m.group(2).strip()
            while stack[-1].level >= level:
                stack.pop()
            parent = stack[-1]
            section = Section(path=[*parent.path, title], title=title, level=level)
            parent.children.append(section)
            stack.append(section)
            bodies[id(section)] = []
            ordered.append(section)
        else:
            bodies[id(stack[-1])].append(line)

    units: list[Unit] = []
    for section in ordered:
        body = bodies[id(section)]
        section.text = "\n".join(body).strip()
        path_hash = _path_hash(section.path)
        counts: dict[str, int] = {}
        for kind, text in _blocks(body):
            base = f"U-{path_hash}-{short_hash(normalize_quote(text) or text)}"
            counts[base] = counts.get(base, 0) + 1
            unit_id = base if counts[base] == 1 else f"{base}-{counts[base]}"
            units.append(Unit(id=unit_id, section_path=section.path, kind=kind, text=text, order=len(units)))
            section.unit_ids.append(unit_id)
    return root, units


def iter_sections(section: Section):
    yield section
    for child in section.children:
        yield from iter_sections(child)


def load_prd(path: str | Path) -> ParsedPRD:
    """Read, normalize and segment a PRD. Raises PRDReadError with a clear message on failure."""
    path = Path(path)
    markdown = normalize_markdown(read_document(path))
    if not markdown.strip():
        raise PRDReadError(f"PRD file has no text content: {path}")
    root, units = build_sections(markdown, root_title=path.stem)
    if not root.children and not units:
        raise PRDReadError(f"No sections or content could be extracted from: {path}")
    if not units:
        raise PRDReadError(f"PRD has headings but no requirement text: {path}")
    prd_hash = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    return ParsedPRD(source_path=str(path), markdown=markdown, prd_hash=prd_hash, root=root, units=units)
