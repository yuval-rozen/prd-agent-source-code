# PRD → GitHub Issues Agent: Pipeline Spec

## 1. Goal
A reusable CLI agent that runs on any PRD (PDF / DOCX / MD / TXT) and:
1. Extracts every requirement from the document.
2. Generates a ticket tree: Parent Project (Epic) → User Stories → Technical Tasks (Frontend / Backend / QA-General).
3. Validates its own output (full coverage, no hallucinated features, testable ACs, clear titles, valid dependencies, clean labels) and repairs what fails.
4. Pauses for human review and shows a preview (table / Markdown / JSON + raw GitHub API payloads).
5. Publishes to GitHub idempotently. Re-running on a modified PRD updates the existing issues (create / update / close), with no duplicates.

Required ticket content:
- Parent Project: scope, business goals, list of linked stories.
- User Story: As a / I want / So that, business description & value, ACs strictly in Given-When-Then (no vague ACs), edge cases, dependencies, Definition of Done.
- Technical Task: child of a story, track = frontend | backend | qa_general, description, "Blocked by" dependencies written in the body.
- Titles: clear and specific (rules in S5 and P11). Tickets are appropriately sized (P10).
- Labels: automatic, from a fixed vocabulary, no duplicate or redundant labels.

## 2. Input PRD
- Before writing any pipeline code, create the folder `prd/` in the project root, tell me, and STOP until I confirm that I placed the real sample PRD there.
- Never write, invent, or reconstruct the sample PRD. All development, tests, and examples use the file I provide.
- Once it exists, create `examples/todo_prd_v2.<ext>`: a copy of the real PRD with a few realistic changes (one requirement added, one modified, one removed). Keep the same format when it can be edited reliably (MD, TXT, or DOCX via python-docx). If the original is a PDF, write v2 as Markdown and note the format change in the README.

## 3. Design principles
- Code orchestrates the pipeline; the LLM only performs narrow steps, each bound to a Pydantic schema.
- Every stage that generates content is followed by a check stage. Nothing moves forward unchecked.
- The LLM generates ticket content as structured data only. It has no GitHub tools; its only tools are the read-only PRD lookups used by the critic (Section 12). All GitHub API calls are made by deterministic code in the publish stage, after validation and human approval.
- PRD-agnostic: nothing in the code, prompts, or validators is specific to the sample PRD, including the examples inside prompts.
- Deterministic where possible: no sampling parameters are sent (current models reject them); repeatability comes from the LLM response cache; Jinja rendering (the LLM never writes the final issue Markdown).
- Secrets never appear in code, logs, outputs, or the repository.

## 4. Stack
Python 3.11+, uv, LangGraph (StateGraph, conditional edges for the repair loops, interrupt() + MemorySaver for the human gates, a prebuilt ReAct agent for the critic: `langchain.agents.create_agent` with `response_format=ProviderStrategy(ReviewReport)`, the successor of the deprecated `create_react_agent`), langchain-anthropic (`with_structured_output(PydanticModel, method="json_schema")` for every LLM call — native structured outputs, because current models reject forced `tool_choice`), Pydantic v2, Typer + Rich, Jinja2, pymupdf4llm (PDF→Markdown), python-docx, rapidfuzz, httpx + tenacity, python-dotenv, pytest.
Model IDs come from config: GENERATION_MODEL and a stronger CRITIC_MODEL. Verify current model IDs and LangGraph/LangChain APIs in the official docs.

## 5. Pipeline overview

  S1 load_prd → S2 extract_requirements → S3 check_requirements ⇄ repair_requirements
     → S4 plan_stories → S5 detail_stories → S6 map_dependencies → S7 check_plan ⇄ repair_plan
     → S8 render_preview → G1 approve_plan
     → [only with --publish] S9 sync_diff → G2 confirm_diff → S10 publish
     → S11 summary → END

(⇄ = review/repair loop, Section 7. G = human gate.)

## 6. Stages

S1 load_prd (code: tools/file_reader.py + tools/state_store.py)
- Input: file path. Output: normalized Markdown, a section tree, atomic Units (each bullet / sentence, with a stable ID = section path + content hash), and prd_hash.
- Load the previous plan from out/plan.json if it exists (this makes the run an update run).
- Checks: the file is readable and non-empty, and at least one section was produced.
- On failure: abort with a clear error.

S2 extract_requirements (LLM, structured → RequirementList, one call per section)
- Input: the units of one section. Output: Requirements { id, unit_ids, verbatim source_quote, section_path, kind, statement }.
- IDs are content-derived: R-<short hash of the normalized source_quote> (lowercased, whitespace collapsed, bullets and punctuation stripped), so they stay stable across runs and file formats. Identical quotes in different sections get a suffix (-2, -3) by order of appearance. Never use sequential numbering.
- kind ∈ functional | data_model | validation_rule | frontend | backend | non_functional | constraint | decision_open | context_only.
- A cross-cutting rule that applies to several features (e.g. "all forms show inline validation errors", "no third-party tracking") → constraint. A choice explicitly left to the team (e.g. "the team may use library X or library Y") → decision_open.

S3 check_requirements (code: validators R1–R2)
- Every quote is grounded in the PRD, and every unit is covered (or marked context_only with a reason).
- Fail → repair_requirements re-extracts only the failing sections, with the findings attached (Section 7).

S4 plan_stories (LLM, structured → ParentProject + story skeletons + constraint scopes)
- Input: all requirements, plus the previous plan as an anchor in an update run ("reuse existing keys for unchanged or modified scope; create new keys only for new scope").
- Output:
  - The Epic (scope, and business goals grounded in the PRD overview).
  - Stories with stable keys (US-<slug>), titles, and requirement_ids.
  - For every constraint, applies_to_requirement_ids (empty = applies globally).
- Stories must be logically scoped: not one per bullet, not one giant story.
- After the LLM call, a deterministic reconcile maps any new key to an old key when requirement overlap + title similarity pass a threshold.
- Incremental update: a story is unchanged when its requirements AND its applicable constraints are unchanged. Unchanged stories are carried over from the previous plan with their tasks and skip S5. This prevents noisy updates caused by LLM rephrasing.

S5 detail_stories (LLM, structured → UserStory + TechnicalTask[], one call per new or affected story)
- Input: the story skeleton, its requirements, and the constraints that apply to it.
- Output: the full story (As a / I want / So that, business description & value, ACs, edge cases, dependencies, DoD) and its tasks split by track, each with size S/M/L and the flags consumes_api and touches_db. A task without a direct requirement needs a derived_reason ∈ testing | migration | scaffolding | decision_spike.
- Titles: imperative, specific, ≤ 80 chars, and naming the object.
  - Story titles describe a user-visible capability.
  - Task titles start with [FE] / [BE] / [QA] and name the concrete artifact (endpoint, model, component, test suite).
  - No generic titles such as "Backend work" or "Implement feature".
- Every decision_open requirement becomes a type:spike task. Its DoD requires a documented decision with rationale and trade-offs, plus any specific aspects the PRD says must be documented.

S6 map_dependencies (LLM proposes, code verifies)
- For new and affected tasks, the LLM proposes blocked_by within and across stories:
  - A task with consumes_api=true is blocked by the BE task that provides that API.
  - A task with touches_db=true is blocked by the DB/migration task.
- Carried-over tasks keep their existing blocked_by. The LLM may add edges from carried-over tasks to new tasks, but may not remove edges between carried-over tasks. Code removes edges that point to keys that no longer exist.
- Code then checks that all keys exist and that there are no cycles.

S7 check_plan (code validators P1–P11 + LLM critic)
- The critic is a bounded ReAct agent (CRITIC_MODEL, the read-only PRD tools from Section 12, response_format = ReviewReport, recursion limit ~10). Per PRD section it looks for missing or misrepresented requirements, unrequested features, untestable ACs, and constraints that are cited but not reflected in the ACs.
- Deterministic findings and critic findings are merged into one ReviewReport.
- Fail → repair_plan regenerates ONLY the failing stories/tasks, using their findings, and merges them back by key.

S8 render_preview (code: tools/renderer.py)
- Writes to out/:
  - plan.json
  - plan.md
  - requirements.md: a table grouped by kind and coverage counts. In an update run, it also shows the requirement diff: added / changed / removed.
  - validation_report.md: a coverage matrix (requirement → tickets), the findings per round, and the final status.
  - payloads/*.json
- Also prints a Rich tree.

G1 approve_plan (human, interrupt)
- Show the requirements summary (and the requirement diff in an update run), the ticket tree, the status, and the findings.
- Answers: approve | feedback (sent to repair_plan as extra findings) | abort.
- `--yes` auto-approves only when the status is PASS.

S9 sync_diff (code: github_tool read-only)
- Lists the existing issues that carry the prd-agent label and marker, and compares them with the plan → SyncActions (create / update / close / unchanged). See Section 10.

G2 confirm_diff (human, interrupt)
- Shows the counts and the list of create / update / close actions. `--yes` skips it. Refused when the status is NEEDS_REVIEW, unless `--force` is passed.

S10 publish (code: github_tool write)
- Pass 1: ensure labels, then create/update issues in topological order (Epic → stories → tasks, blockers first).
- Pass 2: re-render the bodies with real issue numbers ("Parent: #N", "Blocked by: #N") and add child checklists ("- [ ] #N") to the Epic and the Stories.
- Close removed issues with a comment. Never delete issues.

S11 summary (code)
- Counts, final status, issue links, and where the outputs were saved. Every stage logs its progress to the console (Rich); `--debug` adds details and tracebacks.

## 7. Review/repair loop (shared by S3 and S7)
- check → if pass: continue.
- If fail: repair only the failing items → check again.
- Stop the loop when rounds = MAX_REPAIR_ROUNDS (3), OR when the number of blocking findings did not decrease since the last round (the agent is not improving).
- Final status: PASS | NEEDS_REVIEW (items flagged in the report; the pipeline continues to the gate) | ABORTED.

## 8. Validation checks (tools/validators.py; each returns ReviewFindings with check_id + severity)
All checks are blocking unless marked (warning).
- R1 grounding: every source_quote fuzzy-matches the PRD (≥ 90).
- R2 unit coverage: every unit is in a requirement, or that requirement is context_only with a reason.
- P1 every non-context requirement is cited by ≥ 1 story or task.
- P2 every story/task cites existing requirement_ids; a task without one has an allowed derived_reason.
- P3 ACs: ≥ 2 per story, given/when/then all non-empty, and no vague words ("works", "correctly", "properly", "as expected", "user-friendly", "fast", "etc.") unless quantified.
- P4 tracks:
  - backend/data_model requirements → a backend task.
  - frontend requirements → a frontend task.
  - every story has ≥ 1 qa_general task.
- P5 labels: from the enum, exactly one type:* per issue, exactly one area:* per task, no duplicates.
- P6 no near-duplicate titles (rapidfuzz ≥ 90).
- P7 dependencies: blocked_by keys exist and there are no cycles (graphlib). Warnings only:
  - a task with consumes_api=true has no backend blocker.
  - a task with touches_db=true has no area:db blocker.
- P8 constraints: for each constraint with a non-empty applies_to_requirement_ids, every story that cites one of those requirements also cites the constraint. Global constraints (empty applies_to) are checked by the critic only.
- P9 every decision_open requirement has a spike task whose DoD requires a documented rationale.
- P10 (warning) a story with > 8 tasks, or a task of size L, gets a split suggestion.
- P11 titles:
  - non-empty and ≤ 80 chars.
  - task titles start with the prefix that matches their track ([FE] / [BE] / [QA]).
  - no title consists only of a generic phrase ("Implement feature", "Backend work", "Frontend work", "Testing", "Misc").

## 9. Data contracts (schemas.py)
Enums: ReqKind, Track, Label (type:epic|story|task|spike, area:frontend|backend|qa|db|infra, plus the fixed label prd-agent), Size, Severity (blocking|warning), Status.
Models:
- Unit
- Requirement{id = R-<hash>, unit_ids, source_quote, section_path, kind, statement, applies_to_requirement_ids}
- RequirementList
- AcceptanceCriterion{given, when, then}
- UserStory
- TechnicalTask{key, title, track, description, size, consumes_api, touches_db, blocked_by, requirement_ids, derived_reason, labels}
- ParentProject
- TicketPlan{prd_hash, project, stories, tasks, requirements}
- ReviewFinding{check_id, severity, item_key, requirement_ids, message, suggested_fix}
- ReviewReport{stage, round, verdict, blocking_count, warning_count, findings}
- RequirementDiff{added, changed, removed}
- SyncAction{key, action, issue_number, payload}

Pydantic validators enforce the local rules: key formats, non-empty GWT, unique labels, non-empty titles. Title length is checked by P11 only, so a long title is repaired instead of failing the whole response.
AgentState (agent.py): prd_path, units, requirements, requirement_diff, req_report, previous_plan, plan, plan_report, rounds, blocking_history, sync_actions, publish, auto_yes, force, status.

## 10. GitHub idempotency & update flow
- Every issue body ends with `<!-- prd-agent:key=<KEY>;hash=<content_hash> -->` and gets the label prd-agent. The key → issue mapping is read from GitHub. Issues without the marker are never touched.
- content_hash is computed from the ticket's plan data (title, content fields, labels, parent key, blocked_by keys), NOT from the rendered body, so real issue numbers do not affect it.
- Diff:
  - key missing → create.
  - hash differs → update.
  - key not in the plan → close.
  - same → unchanged.
- Running twice therefore produces 0 changes.
- RequirementDiff: a removed requirement and an added one whose normalized quotes fuzzy-match (≥ 85) are reported as "changed".
- A PRD update is just another run:
  1. S1 loads the previous plan.
  2. S4 anchors and reconciles the keys.
  3. S5 regenerates only the affected stories.
  4. S6 and S7 run on the whole plan.
  5. G2 shows the diff before anything is written.
- If out/plan.json is missing, the anchor is rebuilt from the existing issues' keys and titles.
- Known limitation (document in the README): manual edits to an issue in GitHub are kept while its ticket is unchanged, and overwritten when the PRD changes that ticket.

## 11. Secrets & configuration
- config.py reads the environment / .env: ANTHROPIC_API_KEY, GITHUB_TOKEN, GITHUB_REPO, GENERATION_MODEL, CRITIC_MODEL, and the thresholds. .env is in .gitignore from the first commit; .env.example ships with empty values.
- ANTHROPIC_API_KEY is required unless --replay is used. GITHUB_TOKEN is required only with --publish; dry runs work without it. If a required key is missing, fail with a clear message.
- Recommended token: fine-grained, limited to the test repo, Issues read/write only, short expiry.
- `--replay` runs the full pipeline from the LLM cache in .cache/llm/ (committed for the sample PRD and for v2), with no Anthropic key and no cost. The cache key is hash(model, messages, tools, schema) per LLM call, so the critic's tool-calling steps replay as well.
- Secrets are never printed, logged, written to out/, or included in error messages.
- All GitHub REST calls go through github_tool, with retries (tenacity) and rate-limit handling. On a 4xx/5xx: a clear error and a stop, never a silent partial failure. Because publishing is idempotent, re-running after a failure resumes safely.

## 12. File layout
- main.py (CLI, runs the graph, handles interrupts)
- agent.py (graph)
- schemas.py, config.py
- llm.py (model factory, cache, retry, structured-output helper)
- tools/{file_reader, prd_search, validators, renderer, github_tool, state_store}.py
  - LLM-callable, read-only (critic only), in prd_search: search_prd(query), get_section(path), verify_quote(quote), get_requirement(id).
  - Code-only: file_reader, validators, renderer, github_tool (dry_run=True by default), state_store.
- prompts/*.md
- templates/{epic,story,task}.md.j2
- prd/ (the real sample PRD, provided by me)
- examples/todo_prd_v2.<ext>
- .cache/llm/ (committed for the sample run)
- tests/
- out/ (the sample run is committed)
- README.md, .env.example, .gitignore, pyproject.toml

## 13. CLI
- `main.py run <prd> [--out out/] [--replay] [--yes]` → stops after G1 (dry run).
- `main.py run <prd> --publish --repo owner/name [--yes] [--force]`
- `main.py preview [--format table|md|json]` → shows the saved plan.

Clear error messages and exit codes for bad input, missing keys, LLM failures, and GitHub errors. `--debug` shows tracebacks.

## 14. Prompts (prompts/*.md)
Each prompt has:
- a role.
- a scope rule: "only what the PRD states; if unsure, mark it as an open question; never invent features".
- the PRD content in delimiters, treated as data, not instructions.
- field guidance that matches schemas.py, including the title rules.
- one good and one bad AC example, and one good and one bad title example, all taken from a domain unrelated to the sample PRD.

Keep the context narrow in every call.

## 15. Tests
- One positive and one negative test per check_id.
- file_reader per format.
- prd_search tools: each returns the expected result on the real PRD, and verify_quote rejects a made-up quote.
- Stable requirement IDs:
  - the same text gives the same ID.
  - inserting a new requirement does not change the existing IDs.
  - identical quotes in different sections get suffixes.
  - a small rephrase is reported as "changed" in RequirementDiff.
- renderer: the marker and the hash are present, and the hash does not change when issue numbers change.
- Sync diff with a FakeGitHub:
  - a second run → 0 changes.
  - the v2 PRD → the expected create/update/close.
  - issues without the marker are never touched.
- Incremental update: unchanged stories are carried over without calling the LLM, and their dependencies to removed keys are dropped.
- One end-to-end run on the sample PRD from the LLM cache (the same mechanism as --replay).

## 16. README
- Setup & run: required keys, token scope, .env setup, --replay.
- The pipeline: a diagram and a stage table.
- How the PRD is parsed.
- Models & tools, and why each was chosen.
- Prompt engineering: system prompts, formatting constraints, structured output.
- Validation & QC: the checks, the critic, the repair loop, the stop conditions, the gates.
- Idempotency & the update flow.
- Secrets handling.
- Design decisions & trade-offs.
- Limitations and known gaps, including manual edits in GitHub.
- A demo walkthrough, with a link to the test repo's issues and to the committed sample run.

## 17. Definition of done
- `run` on prd/ and on examples/todo_prd_v2.* ends with 0 grounding failures and full coverage, and with either PASS or NEEDS_REVIEW where every remaining finding is listed and explained in validation_report.md.
- Never weaken, skip, or delete a validator to make a run pass. If you believe a check is wrong, keep it and list it under "Known gaps".
- `--publish` creates Epic → Stories → Tasks with labels and dependencies. A second run changes nothing.
- The v2 PRD produces a correct diff and applies it without duplicates; issues of unchanged stories are not modified.
- `--replay` runs end-to-end without any API key.
- No secrets in the repository or in its git history. All tests pass.

## 18. Build order
Build in milestones. Each milestone ends with its tests passing and a git commit (git init in milestone 1).
1. Skeleton: pyproject, config, schemas, file_reader + its tests, a CLI stub, .gitignore, .env.example. Also create .env (gitignored) as a copy of .env.example, for me to fill in. Create prd/ and stop until I confirm (Section 2).
2. Core path: S1 → S2 → S4 → S5 → S8 on the real PRD, producing plan.md and payloads (no checks yet).
3. Quality: S3, S6, S7, the validators with their tests, the repair loop, the critic, and G1.
4. GitHub: the renderer marker and hash, sync_diff with FakeGitHub tests, S9–S10, and G2. Publish to the test repo.
5. Update flow: v2, RequirementDiff, reconcile, incremental update, the committed cache, --replay, and the end-to-end test.
6. The README and the committed sample run.

After each milestone, give me a short status. If you need an API key, a token, or the test repo name, ask me; never stub around a missing one silently.
When everything is done:
1. Run on prd/ and publish to the test repo.
2. Run again and confirm 0 changes.
3. Run on examples/todo_prd_v2.* and publish the update.
4. Report the results and any known gaps.
