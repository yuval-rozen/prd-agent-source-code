"""Read-only PRD lookups (SPEC §12): search_prd, get_section, verify_quote, get_requirement.

These are plain code helpers; no LLM calls them. They started as tools for a planned ReAct critic; the critic is
now one structured call that receives the whole PRD and plan. The R1 grounding check uses verify_quote.
"""

from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz

from schemas import ParsedPRD, Requirement, Section, normalize_quote
from tools.file_reader import iter_sections

DEFAULT_GROUNDING_THRESHOLD = 90.0


@dataclass(frozen=True)
class SearchHit:
    unit_id: str
    section_path: tuple[str, ...]
    text: str
    score: float


@dataclass(frozen=True)
class QuoteCheck:
    grounded: bool
    score: float
    best_unit_id: str | None


class PRDIndex:
    def __init__(self, parsed: ParsedPRD, requirements: list[Requirement] | None = None):
        self.parsed = parsed
        self._requirements = {r.id: r for r in requirements or []}
        self._normalized_doc = normalize_quote(parsed.markdown)
        self._units = [(u, normalize_quote(u.text)) for u in parsed.units]

    def search_prd(self, query: str, limit: int = 5) -> list[SearchHit]:
        """Units ranked by fuzzy similarity to the query (best first, ties in document order)."""
        q = normalize_quote(query)
        if not q:
            return []
        scored = [(fuzz.token_set_ratio(q, norm), u.order, u) for u, norm in self._units]
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [SearchHit(u.id, tuple(u.section_path), u.text, s) for s, _, u in scored[:limit] if s > 0]

    def get_section(self, path: list[str] | str) -> Section | None:
        """A section by its path (list of titles, or ' > '-joined); the last title alone also matches."""
        parts = [p.strip() for p in path.split(">")] if isinstance(path, str) else list(path)
        for section in iter_sections(self.parsed.root):
            if section.path == parts:
                return section
        matches = [s for s in iter_sections(self.parsed.root) if s.path and s.path[-1] == parts[-1]]
        return matches[0] if len(matches) == 1 else None

    def verify_quote(self, quote: str, threshold: float = DEFAULT_GROUNDING_THRESHOLD) -> QuoteCheck:
        """Is the quote (after normalization) present in the PRD? Fuzzy partial match against the document."""
        q = normalize_quote(quote)
        if not q:
            return QuoteCheck(False, 0.0, None)
        score = fuzz.partial_ratio(q, self._normalized_doc)
        best = max(self._units, key=lambda un: fuzz.partial_ratio(q, un[1]))[0].id if self._units else None
        return QuoteCheck(score >= threshold, float(score), best)

    def get_requirement(self, requirement_id: str) -> Requirement | None:
        return self._requirements.get(requirement_id)
