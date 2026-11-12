"""file_reader: one test per format, error cases, unit-ID stability, and the real sample PRD.

Format fixtures use a generic domain (a library catalogue) unrelated to the sample PRD.
"""

import re

import pytest

from schemas import UnitKind
from tools.file_reader import PRDReadError, iter_sections, load_prd, normalize_markdown, split_sentences

GENERIC_MD = """# **Library Catalogue**

## Overview

A catalogue for a small library. Members can browse books.

## Features

- Search books by author.
- **Reserve** a book.
  Reservations expire after 3 days.
* Return a book.

| Field | Type |
|---|---|
| ISBN | string |
"""


def _texts(parsed):
    return [u.text for u in parsed.units]


# --------------------------------------------------------------------------- formats


def test_markdown(tmp_path):
    f = tmp_path / "prd.md"
    f.write_text(GENERIC_MD, encoding="utf-8")
    parsed = load_prd(f)
    titles = [s.title for s in iter_sections(parsed.root)]
    assert titles == ["prd", "Library Catalogue", "Overview", "Features"]
    texts = _texts(parsed)
    assert "A catalogue for a small library." in texts
    assert "Members can browse books." in texts
    assert "Reserve a book. Reservations expire after 3 days." in texts  # continuation joined, emphasis removed
    assert "Return a book." in texts  # '*' bullet normalized
    assert "ISBN | string" in texts
    kinds = {u.text: u.kind for u in parsed.units}
    assert kinds["Search books by author."] is UnitKind.bullet
    assert kinds["Members can browse books."] is UnitKind.sentence
    assert kinds["ISBN | string"] is UnitKind.table_row
    assert "Field | Type" in texts  # header row kept, separator row dropped
    assert "**" not in parsed.markdown


def test_txt(tmp_path):
    f = tmp_path / "prd.txt"
    f.write_text(
        "Library Catalogue\n=================\n\nOVERVIEW\nA catalogue for a small library.\n\n"
        "FEATURES:\n- Search books by author.\n- Reserve a book.\n",
        encoding="utf-8",
    )
    parsed = load_prd(f)
    titles = [s.title for s in iter_sections(parsed.root)]
    assert titles == ["prd", "Library Catalogue", "OVERVIEW", "FEATURES"]
    feature_units = [u.text for u in parsed.units if u.section_path[-1] == "FEATURES"]
    assert feature_units == ["Search books by author.", "Reserve a book."]


def test_docx(tmp_path):
    docx = pytest.importorskip("docx")
    doc = docx.Document()
    doc.add_heading("Library Catalogue", level=1)
    doc.add_heading("Features", level=2)
    doc.add_paragraph("Search books by author.", style="List Bullet")
    doc.add_paragraph("Reserve a book.", style="List Bullet")
    doc.add_paragraph("Members must be signed in. Guests can only browse.")
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text, table.cell(0, 1).text = "Field", "Type"
    table.cell(1, 0).text, table.cell(1, 1).text = "ISBN", "string"
    f = tmp_path / "prd.docx"
    doc.save(f)

    parsed = load_prd(f)
    assert [s.title for s in iter_sections(parsed.root)] == ["prd", "Library Catalogue", "Features"]
    by_text = {u.text: u for u in parsed.units}
    assert by_text["Search books by author."].kind is UnitKind.bullet
    assert by_text["Members must be signed in."].kind is UnitKind.sentence
    assert "Guests can only browse." in by_text
    assert by_text["ISBN | string"].kind is UnitKind.table_row


def test_pdf(tmp_path):
    pymupdf = pytest.importorskip("pymupdf")
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Library Catalogue", fontsize=22)
    page.insert_text((72, 110), "Members can reserve a book for three days.", fontsize=11)
    f = tmp_path / "prd.pdf"
    doc.save(f)
    doc.close()

    parsed = load_prd(f)
    joined = " ".join(_texts(parsed)) + " " + " ".join(s.title for s in iter_sections(parsed.root))
    assert "Members can reserve a book for three days." in joined
    assert "Library Catalogue" in joined


# --------------------------------------------------------------------------- errors


def test_missing_file(tmp_path):
    with pytest.raises(PRDReadError, match="not found"):
        load_prd(tmp_path / "nope.md")


def test_empty_file(tmp_path):
    f = tmp_path / "empty.md"
    f.write_text("", encoding="utf-8")
    with pytest.raises(PRDReadError, match="empty"):
        load_prd(f)


def test_whitespace_only_file(tmp_path):
    f = tmp_path / "blank.txt"
    f.write_text("   \n\n  \n", encoding="utf-8")
    with pytest.raises(PRDReadError):
        load_prd(f)


def test_headings_only(tmp_path):
    f = tmp_path / "h.md"
    f.write_text("# Title\n\n## Section\n", encoding="utf-8")
    with pytest.raises(PRDReadError, match="no requirement text"):
        load_prd(f)


def test_unsupported_format(tmp_path):
    f = tmp_path / "prd.rtf"
    f.write_text("hello", encoding="utf-8")
    with pytest.raises(PRDReadError, match="Unsupported"):
        load_prd(f)


def test_corrupt_pdf(tmp_path):
    f = tmp_path / "bad.pdf"
    f.write_bytes(b"this is not a pdf")
    with pytest.raises(PRDReadError, match="Could not read"):
        load_prd(f)


def test_invalid_utf8(tmp_path):
    f = tmp_path / "bad.md"
    f.write_bytes(b"# T\n\n\xff\xfe\xfa bad")
    with pytest.raises(PRDReadError, match="UTF-8"):
        load_prd(f)


# --------------------------------------------------------------------------- stability


def test_unit_ids_stable_across_runs(tmp_path):
    f = tmp_path / "prd.md"
    f.write_text(GENERIC_MD, encoding="utf-8")
    a, b = load_prd(f), load_prd(f)
    assert [u.id for u in a.units] == [u.id for u in b.units]
    assert a.prd_hash == b.prd_hash


def test_inserting_a_unit_keeps_other_ids(tmp_path):
    f1, f2 = tmp_path / "a.md", tmp_path / "b.md"
    f1.write_text(GENERIC_MD, encoding="utf-8")
    f2.write_text(GENERIC_MD.replace("- Search books", "- Rate a book.\n- Search books"), encoding="utf-8")
    ids1 = {u.text: u.id for u in load_prd(f1).units}
    ids2 = {u.text: u.id for u in load_prd(f2).units}
    assert set(ids2) - set(ids1) == {"Rate a book."}
    for text, uid in ids1.items():
        assert ids2[text] == uid


def test_formatting_does_not_change_unit_id(tmp_path):
    f1, f2 = tmp_path / "a.md", tmp_path / "b.md"
    f1.write_text("# T\n\n- Reserve a book.\n", encoding="utf-8")
    f2.write_text("# **T**\n\n*   **Reserve** a book.   \n", encoding="utf-8")
    assert [u.id for u in load_prd(f1).units] == [u.id for u in load_prd(f2).units]


def test_duplicate_units_in_section_get_suffix(tmp_path):
    f = tmp_path / "d.md"
    f.write_text("# T\n\n- Same line.\n- Same line.\n", encoding="utf-8")
    ids = [u.id for u in load_prd(f).units]
    assert len(set(ids)) == 2 and ids[1] == ids[0] + "-2"


def test_same_text_in_different_sections_differs(tmp_path):
    f = tmp_path / "d.md"
    f.write_text("# A\n\n- Same line.\n\n# B\n\n- Same line.\n", encoding="utf-8")
    ids = [u.id for u in load_prd(f).units]
    assert ids[0] != ids[1]


def test_normalize_and_sentences():
    assert normalize_markdown("## **Bold**  \r\n\r\n\r\n• item") == "## Bold\n\n- item\n"
    assert split_sentences("One thing. Two things! Three, e.g. this one.") == [
        "One thing.", "Two things!", "Three, e.g. this one.",  # no split before a lowercase word
    ]


# --------------------------------------------------------------------------- real sample PRD


def test_sample_prd_loads(sample_prd):
    parsed = load_prd(sample_prd)
    assert len(list(iter_sections(parsed.root))) > 1
    assert parsed.units
    assert len({u.id for u in parsed.units}) == len(parsed.units)
    assert [u.order for u in parsed.units] == list(range(len(parsed.units)))
    assert "**" not in parsed.markdown


def test_sample_prd_every_bullet_is_a_unit(sample_prd):
    parsed = load_prd(sample_prd)
    texts = set(_texts(parsed))
    bullets = [m.group(1).strip() for m in re.finditer(r"^\s*- (.+)$", parsed.markdown, re.MULTILINE)]
    assert bullets
    assert all(b in texts for b in bullets)


def test_sample_prd_section_unit_links(sample_prd):
    parsed = load_prd(sample_prd)
    by_id = {u.id: u for u in parsed.units}
    linked = [uid for s in iter_sections(parsed.root) for uid in s.unit_ids]
    assert sorted(linked) == sorted(by_id)
    for section in iter_sections(parsed.root):
        for uid in section.unit_ids:
            assert by_id[uid].section_path == section.path


def test_sample_prd_deterministic(sample_prd):
    a, b = load_prd(sample_prd), load_prd(sample_prd)
    assert a.prd_hash == b.prd_hash
    assert a.model_dump() == b.model_dump()
