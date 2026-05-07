# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

## User Skills

| Trigger | Skill | Path |
|---------|-------|------|
| When creating a pull request, opening a PR, or preparing changes for review | branch-pr | C:\Users\Jesus\.claude\skills\branch-pr\SKILL.md |
| When a PR would exceed 400 changed lines, when planning chained PRs, stacked PRs, or reviewable slices | chained-pr | C:\Users\Jesus\.claude\skills\chained-pr\SKILL.md |
| When writing guides, READMEs, RFCs, onboarding docs, architecture docs, or review-facing documentation | cognitive-doc-design | C:\Users\Jesus\.claude\skills\cognitive-doc-design\SKILL.md |
| When drafting or posting feedback, review comments, maintainer replies, Slack messages, or GitHub comments | comment-writer | C:\Users\Jesus\.claude\skills\comment-writer\SKILL.md |
| When writing Go tests, using teatest, or adding test coverage | go-testing | C:\Users\Jesus\.claude\skills\go-testing\SKILL.md |
| When creating a GitHub issue, reporting a bug, or requesting a feature | issue-creation | C:\Users\Jesus\.claude\skills\issue-creation\SKILL.md |
| When user says "judgment day", "judgment-day", "review adversarial", "dual review", "doble review", "juzgar", "que lo juzguen" | judgment-day | C:\Users\Jesus\.claude\skills\judgment-day\SKILL.md |
| When user asks to create a new skill, add agent instructions, or document patterns for AI | skill-creator | C:\Users\Jesus\.claude\skills\skill-creator\SKILL.md |
| When implementing a change, preparing commits, splitting PRs, or planning chained or stacked PRs | work-unit-commits | C:\Users\Jesus\.claude\skills\work-unit-commits\SKILL.md |

## Compact Rules

Pre-digested rules per skill. Delegators copy matching blocks into sub-agent prompts as `## Project Standards (auto-resolved)`.

### branch-pr
- Every PR MUST link an approved issue (`status:approved`) — blank PRs are blocked by CI
- Branch naming: `type/description` (lowercase, `a-z0-9._-` only — e.g. `feat/user-login`)
- PR requires exactly one `type:*` label: type:bug, type:feature, type:docs, type:refactor, type:chore, type:breaking-change
- PR body MUST include: `Closes #N`, PR type checkbox, summary, changes table, test plan, contributor checklist
- Conventional commits: `type(scope): description` — no `Co-Authored-By` trailers
- Run shellcheck on all modified scripts before pushing

### chained-pr
- MUST split when PR exceeds 400 changed lines, unless maintainer-approved `size:exception`
- Each chained PR must be autonomous: one deliverable, CI green, clear rollback, verification included
- Every chained PR MUST include a dependency diagram with current PR marked 📍
- Chains with >2 PRs require a draft tracker PR (map only, not review surface) with `no-merge`
- Feature Branch Chain: PR #1 targets tracker branch; each later child targets its immediate parent branch
- Stacked PRs to main: after parent merges, rebase next PR on main and retarget
- Cache user's chosen chain strategy for the session — do not re-ask
- Diff hygiene: if GitHub shows previous PR changes in a child PR, retarget/rebase until diff is clean

### cognitive-doc-design
- Lead with the answer — decision or action first, context after
- Progressive disclosure: happy path first, then details, edge cases, references
- Prefer tables, checklists, and templates over prose (recognition over recall)
- PR docs: state what to review first, what is out of scope, link previous/next PR when chained
- Default structure: outcome-oriented title → one-para summary → quick path → details table → checklist → next step

### comment-writer
- Start with the actionable point — no recap before feedback
- 1-3 short paragraphs or a tight bullet list maximum
- Explain the technical WHY when requesting a change
- No em dashes — use commas, periods, or parentheses
- Match thread language; Spanish → Rioplatense voseo (`podés`, `tenés`, `fijate`, `dale`)
- Comment on the highest-value issue, not every preference

### go-testing
- Use table-driven tests: `tests []struct{ name, input, expected, wantErr }` + `for _, tt := range tests { t.Run(tt.name, ...) }`
- Bubbletea state changes: test `Model.Update()` directly with `tea.KeyMsg`
- Full TUI flows: `teatest.NewTestModel(t, m)` → `tm.Send(key)` → `tm.WaitFinished` → `tm.FinalModel`
- Visual output: golden files in `testdata/*.golden`, update with `-update` flag
- File I/O in tests: use `t.TempDir()`; skip integration tests with `go test -short`
- Test file mirrors source: `model.go` → `model_test.go` in the same package directory

### issue-creation
- Use templates ONLY: `bug_report.yml` or `feature_request.yml` (blank issues disabled)
- Bug creation auto-labels: `bug`, `status:needs-review`; feature auto-labels: `enhancement`, `status:needs-review`
- Maintainer MUST add `status:approved` before any PR can be opened — this is enforced by CI
- Questions go to Discussions, NOT issues
- Issue titles follow conventional commit style: `fix(scope): desc` or `feat(scope): desc`

### judgment-day
- Launch TWO judge sub-agents in parallel (async) — orchestrator NEVER reviews code itself
- Neither judge knows about the other — identical prompts, independent blind review
- Every WARNING must be classified: `real` (normal user can trigger) or `theoretical` (contrived/edge case)
- Theoretical warnings = INFO only — do NOT fix, do NOT re-judge, do NOT count toward threshold
- Round 1: present verdict table, ask user before fixing any confirmed issues
- Re-judge with full parallel judges only if confirmed CRITICALs remain after fix
- APPROVED = 0 confirmed CRITICALs + 0 confirmed real WARNINGs (theoretical warnings may remain)
- After 2 fix iterations, ASK user whether to continue — never auto-escalate

### skill-creator
- Frontmatter MUST include: `name` (lowercase-hyphens), `description` with `Trigger:` clause, `license: Apache-2.0`, `metadata.author`, `metadata.version`
- Directory structure: `skills/{name}/SKILL.md` + optional `assets/` (templates/schemas) + `references/` (local docs only)
- `references/` must point to LOCAL file paths — no web URLs
- After creating, register the skill in `AGENTS.md`
- Do NOT create a skill for one-off tasks or trivially self-explanatory patterns

### work-unit-commits
- Each commit = one deliverable behavior, fix, migration, or docs unit — NOT a file type batch
- Tests belong in the same commit as the behavior they verify
- Docs belong with the user-visible change they explain
- Each commit must leave the repo coherent on its own (standalone rollback possible)
- Conventional Commit messages describe the outcome, not the file list
- If SDD forecasts >400 changed lines: plan chained PR slices BEFORE implementing

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| — | — | No project-level convention files found (empty project) |
