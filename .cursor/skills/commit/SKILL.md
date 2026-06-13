---
name: commit
description: >-
  Analyze git changes, write a concise commit message with one bullet per work
  item, stage relevant files, and commit locally without pushing. Use when the
  user asks to commit, create a commit, or invokes the commit skill.
disable-model-invocation: true
---

# Commit

Create a local git commit from current changes. Never push unless explicitly requested.

## Message format

```
<concise subject — why/outcome in one line>

- <work item 1>
- <work item 2>
```

- Subject: imperative, focused on outcome; keep under ~72 characters when possible.
- Body: one bullet per logical change (group related file edits into one bullet).
- Match recent commit tone from `git log`.

## Workflow

1. Run in parallel: `git status`, `git diff`, `git diff --staged`, `git log -5 --format='%s%n%b'`.
2. Analyze changes; list work items (not raw file names unless each file is its own change).
3. Stage relevant files. Exclude secrets (`.env`, credentials). Warn if user asked to commit secrets.
4. Commit with HEREDOC (subject + blank line + bullets).
5. Run `git status` to verify success.
6. Do not run `git push`.

## Safety

- Never update git config.
- Never use `--no-verify`, force push, or destructive resets unless explicitly requested.
- Never amend unless user requested amend AND HEAD was your commit AND not pushed.
- If pre-commit hook fails, fix and create a new commit (do not amend a failed commit).
- If there is nothing to commit, say so; do not create an empty commit.

## Examples

**Input:** Stage 1 prompt tightened; validation updated; example fixture refreshed.

**Output:**

```
Tighten Stage 1 aptitude profile prompt and validation.

- Clarify resume-to-profile instructions in stage1 prompt
- Align validate.py checks with updated profile schema
- Refresh career-changer Stage 1 example fixture
```
