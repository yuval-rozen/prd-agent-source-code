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
- The LLM generates ticket content as structured data only. It has no tools at all (no GitHub tools, no PRD tools): every LLM call, the critic included, is one structured call whose input is assembled by code. All GitHub API calls are made by deterministic code in the publish stage, after validation and human approval.
- PRD-agnostic: nothing in the code, prompts, or validators is specific to the sample PRD, including the examples inside prompts.
- Deterministic where possible: no sampling parameters are sent (current models reject them); repeatability comes from the LLM response cache; Jinja rendering (the LLM never writes the final issue Markdown).
- Secrets never appear in code, logs, outputs, or the repository.

## 4. Stack
Python 3.11+, uv, LangGraph (StateGraph, conditional edges for the repair loops, interrupt() + MemorySaver for the human gates, ), langchain-anthropic and langchain-google-genai (`with_structured_output(PydanticModel, method="json_schema")` for every LLM call — native structured outputs: Anthropic `output_config.format`, Gemini `response_json_schema`; never tool-based, because current Claude models reject forced `tool_choice`), Pydantic v2, Typer + Rich, Jinja2, pymupdf4llm (PDF→Markdown), python-docx, rapidfuzz, httpx + tenacity, python-dotenv, pytest.
Provider: LLM_PROVIDER=anthropic|google (default anthropic). Both stay supported; llm.py has one factory that builds ChatAnthropic or ChatGoogleGenerativeAI behind the same cache, cost and retry layer.
Model IDs come from config, one per stage: EXTRACT_MODEL (S2 and repair_requirements), GENERATION_MODEL (S4, S5, S6 and repair_plan) and CRITIC_MODEL (S7 critic). Empty means the provider's default:
- anthropic: claude-haiku-5-5 / claude-haiku-5-5 / claude-sonnet-5-5 (a cheap model generates, a stronger model reviews). During development all three can be set to claude-haiku-5-5.
- REVISION_MODEL (default claude-sonnet-5-5; google: gemini-3.8-flash) is used only in update runs, for the targeted revisions and repairs (StoryUpdateDraft / StoryRepairDraft): the strict critic re-reviews exactly those edits, and the cheap model kept leaving gaps there. Extraction and first-pass generation stay on Haiku.
- google (free tier only): gemini-3.5-flash-lite / gemini-3.8-flash / gemini-3.8-flash.
A model must belong to the selected provider and have an entry in the price table, otherwise the run is refused.
Provider-specific features: prompt caching and reasoning effort are Anthropic-only and are not sent to Google (no clear equivalent is enabled; Gemini context caching is not used). Sampling parameters are sent to neither (for Gemini the library's temperature default is removed explicitly).
Critic (decided in M3): one structured call, not a ReAct agent, so it uses the same native structured output as every other call on both providers. A cheap model generates (Haiku) and a stronger model reviews (Sonnet): the critic must see the whole PRD and the whole plan at once to catch problems that span stories (overlapping tasks, work assumed to live in another story), which per-story generation cannot see. langchain-google-genai 4.5.0 is used (it needs tenacity < 9.2).
Request timeout: 180 s per LLM call. Google: HTTP 503 / 504 / timeout is retried twice (after 15 s and 45 s); the Anthropic SDK retries 5xx and timeouts itself. GOOGLE_THINKING_LEVEL (minimal | low | medium | high; empty = model default) sets Gemini's native thinking level for the generation and critic stages only.
Every run writes out/<dir>/run_stats.json (provider, models, time per stage, cost, calls, retries, errors; no secrets), also when it fails.
Verify current model IDs and LangGraph/LangChain APIs in the official docs.

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

S5 in an update run — task-level update rules (code decides as much as possible; the LLM decides only where an added requirement goes):
- Story level (S4 + code): unchanged requirements keep their previous story and constraint scope; removed requirements drop out; a changed requirement takes its old version's place. S4's output decides only where ADDED requirements go (an existing story or a new story key). A story whose requirements and applicable constraints are unchanged is carried over byte-for-byte without an LLM call; an unchanged story keeps its title, a story whose scope changed takes S4's new title. The epic keeps its key and text.
- Task level, for every task of an affected story, code decides:
  - KEEP: the task cites no changed or removed requirement → copied byte-for-byte by code.
  - REVISE: the task cites a changed or removed requirement → must be revised (keeps its key, story, track and blockers; removed IDs are dropped and changed IDs mapped to their new ID by code).
  - CLOSE: all of the task's requirements were removed → closed.
- The LLM (one structured call per affected story, `StoryUpdateDraft`, prompt `update_story.md`) returns the revised versions of exactly the REVISE tasks, the updated story content, and for every ADDED requirement one placement: revise one existing task of the story (KEEP or REVISE) to cover it, or add a new task.
- Code checks: a "revision" of a KEEP task that was not chosen for an added requirement is ignored (the previous version is kept); a REVISE task without a returned revision gets a deterministic fallback (same content, IDs mapped).
- Keys: a new task reuses an old task's key only if it is in the same story and track AND shares requirements with it (for tasks without requirements: the same derived_reason); title similarity is only a tie-breaker. Otherwise it gets a new key.
- Churn guard (after S5 and after every repair in an update run): a story or task may differ from its previous version only if it (before or after) cites an added / changed / removed requirement, or belongs to a story targeted by this run's G1 feedback — otherwise code restores the previous version. A previous task may disappear only if all its requirements were removed (or its story was removed) — otherwise code restores it. A new task needs an added or changed requirement, or feedback on its story — otherwise code drops it. Every restore / drop is recorded as a REF-CHURN / REF-RESTORE finding.
- Repairs and G1 feedback in an update run go through the same task-level path (one `StoryRepairDraft` call per targeted story, prompt `repair_update_story.md`), never a full regeneration: a finding or decision that names tasks (its item key, or task keys in its text) may revise only those tasks; one that names only the story lets the model revise the minimal set of the story's tasks and the story text. Every other task is kept byte-for-byte by code, and the story text changes only for a story-level finding. The story text is never returned whole: the model returns numbered edits (replace, remove or add an AC, edge case or DoD line; a new value for a user-story or business field only where the fix needs it), code applies them, and every line no edit names stays byte-for-byte. An edit with an unknown line number is ignored and logged as a reference finding. A new task is added only when the model returns one because no existing task can cover the fix; a repair may remove only tasks created in the same run (for example a duplicate), never a published one. A repair round that changes nothing skips the critic and keeps the earlier findings.
- Citations from findings and decisions: when a repair addresses a finding or a G1 decision that names an existing requirement (in its requirement_ids, by ID in its text, or by a near-verbatim quote of 4+ words), code adds that requirement ID to the story and to the tasks revised (or created) for that finding. Only IDs that exist in the requirement list; the model never adds IDs. A paraphrase alone does not count. (On a first run, where repairs regenerate the story, the IDs are added to the story skeleton before regeneration.)
- In an update run, a change a repair makes to fix a blocking finding has that finding as its cause (shown in G2 as "finding <check>"), so the churn guard keeps it.
- S6 in an update run gives blockers only to new tasks and never adds an edge to an existing task; existing tasks keep their edges (edges to closed tasks are removed). The critic's first round reviews only the stories and tasks that differ from the previous plan (nothing at all if none differ).
- G2 shows, for every create / update / close / link, the requirement change (or G1 decision) that caused it. An action without a cause is churn; the count is shown in S9 and G2 and must be zero.

S6 map_dependencies (LLM proposes, code verifies)
- For new and affected tasks, the LLM proposes blocked_by within and across stories:
  - A task with consumes_api=true is blocked by the BE task that provides that API.
  - A task with touches_db=true is blocked by the DB/migration task.
- Carried-over tasks keep their existing blocked_by. The LLM may add edges from carried-over tasks to new tasks, but may not remove edges between carried-over tasks. Code removes edges that point to keys that no longer exist.
- Code then checks that all keys exist and that there are no cycles.

S7 check_plan (code validators P1–P11 + LLM critic)
- The critic is ONE structured call (CRITIC_MODEL, response_format = ReviewReport) that receives the full PRD and the full plan in a compact form (epic; stories with ACs, edge cases and dependencies; tasks with track, area, size, flags, a short description, requirements and blocked_by; the requirement list). It runs after the deterministic validators. It looks for missing or misrepresented requirements, unrequested features, untestable ACs, constraints not reflected in the ACs, and overlapping tasks across stories (for example two migrations that add the same fields). check_ids: CRIT-MISSING, CRIT-MISREPRESENTED, CRIT-UNREQUESTED, CRIT-UNTESTABLE-AC, CRIT-CONSTRAINT, CRIT-OVERLAP (anything else becomes CRIT-OTHER); item keys that do not exist are cleared.
- Prompt caching for the critic: the system prompt and the PRD (stable across rounds) carry the cache breakpoints; the plan (new every round) is sent as ordinary input, so it is not written to the cache. The critic's cost is reported separately (S11, run_stats.json).
- In repair rounds 2-3 the critic reviews only the repaired items (the stories/tasks that repair_plan regenerated); it still receives the whole plan as context, and its findings on other items are discarded. Earlier critic findings on items that were not repaired are carried over. The deterministic validators still run on the whole plan every round.
- repair_plan routing: a finding on a story or task regenerates that story; a CRIT-OVERLAP finding also regenerates every story whose task it names; a finding with only requirement IDs (e.g. P1) adds the requirement to the story that cites most requirements of the same PRD section. A regenerated story sees its findings, its current version and the tasks of all other stories. Its new tasks get dependencies from S6 (only their edges, and new edges pointing to them, change).
- Deterministic findings and critic findings are merged into one ReviewReport.
- Open-findings ledger: every blocking critic finding gets an ID and stays open across repair rounds, keep-best restores and G1 resets until the critic explicitly confirms it is fixed. Each critic call receives the open findings and must put each ID in `resolved` (fixed in the current plan) or `still_open`; a finding the critic does not mention stays open. When keep-best restores an earlier plan, that round's open findings come back and findings raised later stay open too.
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
- A decision that names a story (or its tasks) is applied to that story: the story's ACs and every task that conflicts with it are revised, not a minimal set; tasks that do not conflict stay unchanged. A decision without a ticket key is plan-wide: it is not pushed into every story; the next critic round reviews the whole plan against it, and the conflicts it finds are repaired like other findings.
- Feedback is a reviewer decision: it stays in the state, is given to the critic and to every later repair as authoritative context (treated like PRD text), and starts a fresh repair cycle (round count, blocking history and best-round baseline reset), so a round without the decision is never restored over it. Ticket keys in the feedback target those items; feedback without a key applies to every story.
- `--yes` auto-approves only when the status is PASS.

S9 sync_diff (code: github_tool read-only)
- Lists the existing issues that carry the prd-agent label and marker, and compares them with the plan → SyncActions (create / update / close / unchanged). It also reads the current sub-issues of every managed parent (`GET .../issues/{n}/sub_issues`) and adds a `link` action for every story→epic or task→story link that is missing. See Section 10.

G2 confirm_diff (human, interrupt)
- Shows the counts and the list of create / update / close actions. `--yes` skips it. Refused when the status is NEEDS_REVIEW, unless `--force` is passed.

S10 publish (code: github_tool write)
- Pass 1: ensure labels, then create/update issues in topological order (Epic → stories → tasks, blockers first).
- Pass 2: re-render the bodies with real issue numbers ("Parent: #N", "Blocked by: #N") and add child checklists ("- [ ] #N") to the Epic and the Stories. Then build the native GitHub ticket tree with the REST sub-issues API: each story is a sub-issue of the epic and each task a sub-issue of its story (`POST /repos/{owner}/{repo}/issues/{parent_number}/sub_issues` with `sub_issue_id` = the child's issue **id**, not its number, and `replace_parent: true` so a task that moved to another story is re-parented). Required token permission: Issues: write (listing sub-issues needs Issues: read). The body checklists stay as a fallback for views that do not show sub-issues.
- Close removed issues with a comment. Never delete issues.

S11 summary (code)
- Counts, final status, issue links, where the outputs were saved, and the total LLM cost of the run. Every stage logs its progress to the console (Rich); `--debug` adds details and tracebacks.

## 7. Review/repair loop (shared by S3 and S7)
- check → if pass: continue.
- If fail: repair only the failing items → check again.
- Stop the loop when rounds = MAX_REPAIR_ROUNDS (3), OR when the number of blocking findings did not decrease since the last round (the agent is not improving), OR (S7) when no remaining blocking finding can be tied to a story or task.
- When the loop stops on a round that is worse than an earlier one, the plan of the best round (fewest blocking findings) is kept, and validation_report.md says so.
- Final status: PASS | NEEDS_REVIEW (items flagged in the report; the pipeline continues to the gate) | ABORTED.

## 8. Validation checks (tools/validators.py; each returns ReviewFindings with check_id + severity)
All checks are blocking unless marked (warning).
- REF-* (warning, recorded by S2/S4/S5 code, not a separate check stage): whenever code drops or replaces something the LLM returned, it records a finding instead of doing it silently: REF-UNIT (unknown unit ID, attached to the best-matching unit), REF-REQ (unknown requirement ID dropped), REF-CONSTRAINT (scope given for a non-constraint), REF-STORY (unknown or self dependency dropped), REF-KEY (story key normalized), REF-AREA (area that does not fit the track replaced). They appear in validation_report.md and the S11 summary.
- R1 grounding: every source_quote fuzzy-matches the PRD (≥ 90).
- R2 unit coverage: every unit is in a requirement, or that requirement is context_only with a reason. A list item (bullet or table row) covered only by context_only requirements is also flagged: list items in a PRD state requirements.
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
- P12 plain language: story and task text (titles, user story, business description and value, ACs, edge cases, descriptions, DoD) contains no requirement IDs, no ticket keys and no references to the agent's own process ("requirement ID", "reviewer decision", "finding", "critic", "the PRD text"). Requirement IDs live only in requirement_ids. An open question is stated plainly; "The PRD does not state ..." is product language and allowed. The story prompts carry the same rule. P12 is repaired field by field, in every run: one small call that names the notes to remove in each text (one retry for a text whose rewrite still has one) (`PlainRewriteDraft`, prompt `plain_language.md`, revision role) rewrites only the flagged texts (one AC part, edge case, DoD line, description, title or business field) with the same meaning; code puts each back in its place, so the rest of the item and every other item stay byte-for-byte. A requirement ID that a flagged text named is added by code to that item's requirement_ids (existing IDs only). The change cause shown at G2 is "finding P12".
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
- content_hash is computed from the ticket's plan data (title, content fields, labels, parent key, blocked_by keys, and for a story the keys of its tasks, so its checklist is refreshed when tasks change), NOT from the rendered body, so real issue numbers do not affect it.
- Listing: GET issues with state=all and label prd-agent, all pages (Link rel=next). Pull requests, issues without the marker, and a second issue repeating an already-seen key are reported and never touched. Reopening: when the agent closes an issue (its ticket left the plan) it marks the issue's marker with `;closed=agent`. A closed managed issue whose key is back in the plan is updated and reopened ONLY if it carries that mark. An issue closed by a human (for example as completed) has no mark: it is never reopened, never updated and never re-linked; S9 reports it as left closed.
- Writes are spaced at least 1 s apart (GitHub's secondary rate limits). Pass 2 patches only the bodies that change once the real issue numbers are known. Close = a comment, then state closed (state_reason not_planned).
- Diff:
  - key missing → create.
  - hash differs → update.
  - key not in the plan → close.
  - same → unchanged.
- Sub-issue links: a link that already exists is skipped, so it is never posted twice; links to sub-issues a human added are never removed.
- Running twice therefore produces 0 changes (no issue writes and no link writes).
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
- config.py reads the environment / .env: LLM_PROVIDER, ANTHROPIC_API_KEY, GOOGLE_API_KEY, GITHUB_TOKEN, GITHUB_REPO, EXTRACT_MODEL, GENERATION_MODEL, CRITIC_MODEL, MAX_RUN_COST_USD, MAX_PARALLEL_CALLS, and the thresholds.
- Cost control: MAX_RUN_COST_USD (default 0.30). The cost of every live LLM call is computed from the response usage (input, cache read, cache write, output tokens) and a per-model price table in config.py; a model without a known price is refused. No new call starts once the run has spent the limit, and the run aborts with a clear message (its own exit code) as soon as a response pushes the total over it. Calls already in flight in parallel can finish, so the overshoot is bounded by their cost. Paid responses are cached before the abort, so a re-run does not pay for them again. Cached (replayed) responses cost nothing. Free-tier Gemini models are priced at $0 (the cap stays active); Gemini models without a free tier are not in the price table and are refused. S11 shows the total.
- Prompt caching is enabled on every Anthropic call: a cache breakpoint on the system prompt plus top-level automatic caching.
- Google free tier: only free-tier models are allowed; nothing billable is enabled (no context caching, no grounding). The key's Google Cloud project should have no billing account, because the code cannot detect billing and a billed project is charged for the same models. Free-tier prompts and responses may be used by Google to improve its products, so only non-confidential PRDs should be sent. Limits are per project and small (Google publishes the exact numbers only in AI Studio): LLM calls run one at a time by default (MAX_PARALLEL_CALLS, default 4 for Anthropic and 1 for Google), a 429 is retried after the delay the API returns (RetryInfo / "retry in Ns", at most 5 times, at most 120 s each), and a per-day quota error stops the run immediately with a clear message.
- The LLM response cache key includes the provider and the exact provider request.
- .env is in .gitignore from the first commit; .env.example ships with empty values.
- The key of the selected provider (ANTHROPIC_API_KEY or GOOGLE_API_KEY) is required unless --replay is used. GITHUB_TOKEN is required only with --publish; dry runs work without it. If a required key is missing, fail with a clear message.
- Recommended token: fine-grained, limited to the test repo, Issues read/write only, short expiry.
- `--replay` runs the full pipeline from the LLM cache in .cache/llm/ (committed for the sample PRD and for v2), with no Anthropic key and no cost. The cache key is hash(provider, exact request) per LLM call (model, messages, schema, tools if any).
- Secrets are never printed, logged, written to out/, or included in error messages.
- All GitHub REST calls go through github_tool, with retries (tenacity) and rate-limit handling. On a 4xx/5xx: a clear error and a stop, never a silent partial failure. Because publishing is idempotent, re-running after a failure resumes safely.

## 12. File layout
- main.py (CLI, runs the graph, handles interrupts)
- agent.py (graph)
- schemas.py, config.py
- llm.py (model factory, cache, retry, structured-output helper)
- tools/{file_reader, prd_search, validators, renderer, github_tool, state_store}.py
  - Read-only code helpers in prd_search (not LLM tools): search_prd(query), get_section(path), verify_quote(quote) (used by R1), get_requirement(id).
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
