# CLAUDE.md

This project is a PRD → GitHub Issues CLI agent. **[SPEC.md](SPEC.md) is the source of truth** — read it before any work and follow it exactly.

Key rules (details in SPEC.md):
- Build in the milestones of SPEC §18; each ends with passing tests, a git commit, and a short status to the user.
- Never write, invent, or reconstruct the sample PRD in `prd/` (§2). Code, prompts, and validators stay PRD-agnostic (§3).
- Never weaken, skip, or delete a validator to make a run pass (§17).
- Secrets never go in code, logs, `out/`, or git (§11). Ask for keys/tokens/repo name; never stub around a missing one.
- Verify current model IDs and LangGraph/LangChain APIs in official docs (§4).
