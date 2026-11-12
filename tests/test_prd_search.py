"""prd_search helpers on the real sample PRD (SPEC §15). Expectations are derived from the parsed PRD itself."""

import pytest

from schemas import ReqKind, Requirement, requirement_id_base
from tools.file_reader import iter_sections, load_prd
from tools.prd_search import PRDIndex


@pytest.fixture(scope="module")
def index(sample_prd):
    return PRDIndex(load_prd(sample_prd))


def test_search_prd_finds_each_unit_by_its_own_text(index):
    for unit in index.parsed.units[:10]:
        hits = index.search_prd(unit.text, limit=3)
        assert unit.id in [h.unit_id for h in hits]


def test_get_section_by_path_and_by_title(index):
    sections = [s for s in iter_sections(index.parsed.root) if s.unit_ids]
    target = sections[-1]
    assert index.get_section(target.path).unit_ids == target.unit_ids
    assert index.get_section(" > ".join(target.path)).path == target.path
    assert index.get_section(["No such section"]) is None


def test_verify_quote_accepts_real_quotes(index):
    for unit in index.parsed.units:
        assert index.verify_quote(unit.text).grounded, unit.text


def test_verify_quote_rejects_made_up_quote(index):
    check = index.verify_quote("Users can pay for premium plans with cryptocurrency and earn loyalty points.")
    assert not check.grounded and check.score < 90


def test_get_requirement(index):
    unit = index.parsed.units[0]
    req = Requirement(id=requirement_id_base(unit.text), unit_ids=[unit.id], source_quote=unit.text,
                      section_path=unit.section_path, kind=ReqKind.functional, statement=unit.text)
    idx = PRDIndex(index.parsed, [req])
    assert idx.get_requirement(req.id) == req
    assert idx.get_requirement("R-00000000") is None
