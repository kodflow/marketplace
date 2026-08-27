---
name: implement-issue
description: Implement a GitLab issue draft step by step, with a per-step commit gate and a review panel scaled to what the step touched. Use when asked to implement an issue file under .drafts/.
argument-hint: issue-file-path [extra-instructions...]
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Skill, Agent, TodoWrite
---
Arguments ($ARGUMENTS): the first token is the path to the issue file to implement. Any remaining text after that first token is a set of issue-specific instructions that apply ONLY to this invocation : treat them as additional constraints layered on top of the general rules below. If no extra instructions are provided, ignore this and just implement the issue.

Implement the requirements described in the issue file (first argument).

**First, check for a checkpoint.** Let `<issue>` be the basename of the issue file without its extension. The ledger is `.claude/progress/<issue>.md`. If it exists, this is a RESUMED run:

- Read the ledger in full.
- Read `.claude/progress/<issue>-step-<N>.md` for the step in flight ONLY. Do not read the notes of completed steps; they stay on disk for the rare case you need them.
- Read `git log --oneline` and the diff for the steps already landed.
- Continue from the next step. Skip the planning step below: do NOT re-derive the plan, and do NOT replay completed steps.

If the ledger does not exist, this is a fresh run: start at the numbered flow below.

1. Provide a step by step implementation plan and ask for user approval.
2. When executing the plan, ALWAYS STOP after each completed step and ONLY suggest a short commit message BEFORE proceeding to the next step, so that I can ALWAYS review the changes before committing MYSELF. DO NOT try to git add or git commit. DO NOT proceed to next step until I say so.
3. At that same stop, update the checkpoint file (see "Checkpoint" below) so the step boundary is also a safe place to clear the context.

You MUST always enforce the following rules:

- DO NOT make any assumptions, DO NOT remove any features, we need 100% functional parity with the reference issue, ask for clarifications if needed.
- Improve godoc when it is too minimal and test coverage if needed. DO NOT use mocking frameworks in the tests, ALWAYS prefer manual mocks.
- ALWAYS use table-driven tests whenever possible.
- ALWAYS be critical and suggest alternatives if you find some inconsistencies in the requirements.
- ALWAYS enforce the coding style by invoking the `coding-style` skill if it is available (ships with the `go-review-panel` plugin).
- ALWAYS run the linter at the project root when all steps are complete and fix the errors if any. Prefer `golangci-lint run` from `PATH`; fall back to `~/go/bin/golangci-lint run` if the binary isn't on `PATH`.
- Commits follow the project's own commit convention (Conventional-Commits-style header, per its `CONTRIBUTING.md`/`docs/commit-format.md` if it defines one) — this skill does not prescribe a language for commit messages, that is a per-project choice.
- Deliver each step at the scope the plan specifies. Do not widen it with unrequested refactors, helpers or abstractions, and match the length of anything written to disk to what the step actually needs.

Implement each step yourself in this context, with the `pragmatic-coder` skill loaded. Do NOT delegate the implementation to a subagent: the repo context is already loaded here, and a coder agent would spend most of its cost rediscovering it.

After each completed step, review it. Reviews DO run as subagents: independent judgement on the diff is the point, and a reviewer that shares your context is not independent. Scale the review to what the step touched:

- If the step touched architecturally significant code (domain/business logic, a public interface, a 3GPP surface, or a type claimed protocol-neutral), and the `go-review-panel` plugin is installed: run its 3 Go review agents (`dogmatic-go-reviewer`, `annoying-product-owner`, `paranoid-perf-gopher`).
  - **In addition**, if the step touches a 3GPP/telecom surface AND the `3gpp-expert` plugin is installed: run ONE more subagent for the 3GPP conformance audit, briefed to load the `3gpp-expert` skill first (and the project's own `neutrality-audit` skill, if it has one, when a type is claimed neutral). Do NOT use the generic `3gpp` MCP server for this.
    - Brief that audit as **two passes, and name them**. First completeness: are the types, IEs, messages and procedures the spec mandates present and reachable? Then compliance, as a **literal table walk**: pull the spec's per-message IE tables and check every row, requests **and** responses. Per IE: does the presence condition (Mandatory / Conditional / Optional) match the code, and does that IE even apply on **this** interface? An IE valid on one interface can be invalid on another. Also check validation ranges, spec-mandated normalisation (case, BCD/TBCD nibble order, byte ordering), and the cause codes returned on each rejection path.
    - A concern-driven pass ("is this mapping sound?", "is delete-and-recreate conformant?") is NOT the audit. Asking those questions instead of walking the tables is what lets presence-condition bugs reach interop testing.
  - If `go-review-panel` isn't installed, review the diff yourself inline instead of skipping review entirely.
- Otherwise (tests, infrastructure plumbing, pure refactor): run `dogmatic-go-reviewer` only, if `go-review-panel` is installed; otherwise review inline.
- **Run the architecture and style check yourself, inline**, by loading `coding-style` (if `go-review-panel` is installed) and, if the project defines its own architecture/conventions skill or doc, that too — this skill does not presume its name. Do NOT delegate it: it is a conventions checklist with no bulk source to fetch, and you already hold the diff.
- The 3GPP audit, when it runs, is the one check that stays delegated, because it pulls spec text into its context that must not enter yours.
- Consolidate all findings into ONE fix plan and apply it yourself, still under the `pragmatic-coder` posture.
- Do not spawn any agent beyond the ones named here.

**Brief each reviewer with the diff itself, not a pointer to it.** Reviewers that have to reconstruct the change burn most of their turns fetching instead of judging. Each brief carries: what the step was meant to do, the list of files touched, and the actual `git diff` output pasted inline when it is under roughly 600 lines. Above that, and for the final whole-MR review, give the commit range and the file list instead of pasting. State in the brief that the diff is provided and they must not re-run `git diff`; they may still read surrounding code where judging a hunk needs it.

At the final step, run the full panel over the whole MR regardless of what the last step touched. If the `go-review-panel` plugin is installed, its own `review-mr` skill is the more thorough way to do this final pass — invoke it instead of hand-rolling the panel here.

## Checkpoint

Two files per issue, both under `.claude/progress/` — exclude this directory from git in the consuming project (e.g. via `.git/info/exclude`) so neither file reaches the MR. **Nothing in either file is ever summarised, rewritten or deleted.** Content that stops being relevant stops being *loaded*, which is not the same thing.

### The ledger, `<issue>.md`

Append-only, and always read in full on resume. It stays small by construction, so it never needs trimming. Exactly five sections:

- `## State` : five to ten lines, which step is next and what is uncommitted. The ONLY section you overwrite, because it is current-state by definition and `git status` is authoritative if it ever drifts.
- `## Decisions that bind` : each decision and why, especially where the implementation deviated from the plan.
- `## Findings REJECTED (do not re-open)` : each rejected review finding, and the reason it was rejected.
- `## Deferrals` : tracked artifacts, per the project's own Definition of Done if it has one.
- `## Learned, not visible in the diff` : facts about the codebase the code itself does not show.

If an entry belongs in one of those five sections it goes in the ledger, even when it came out of a step review. **When in doubt, ledger:** an entry filed wrongly into a step note drops out of the resume path, which is the one failure mode that actually loses information.

### Step notes, `<issue>-step-<N>.md`

One per step: the review panel output, step narration, acceptance-test notes, working detail. Written while the step is in flight, not edited afterwards, never deleted. Only the in-flight step's file is read on resume; earlier ones remain on disk, complete, for the rare case you want to know what a panel actually said.

Do NOT restate the diff in either file. The commit and `git diff` are authoritative for what changed.

Then tell the user the checkpoint is written and they can `/clear` before the next step. Prefer that over `/compact`: re-reading these files is lossless, whereas a compaction summary silently drops the rejected findings and the reasons behind decisions. If you must compact mid-step instead, name what to keep (open findings, decisions, remaining work in the current step) rather than leaving the choice open.

When all steps are complete, explain in French what this merge request does and why, especially if there are differences with the reference implementation.
Please use VERY natural oral-like language and be concise.

At the end, when all developments are validated by the user, suggest a merge commit message for the whole MR. If the `issue-workflow` plugin's `post-issue` command was used to publish this issue, or the project has its own commit convention, follow that; otherwise Conventional Commits.
