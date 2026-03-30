---
name: deb-scripts-commits
description: Use when writing Git commit messages or PR titles for changes in deb_scripts. Covers conventional commits, raw plain-text output, English-only output, and the supported modes single_commit, squash_commit, pr_title, and commit_with_body.
---

# Commit and PR messages

Use this skill when the user asks for a commit message, squash commit, PR title, or commit body.

## Output contract

- Output raw plain text only.
- Output in English only.
- Do not use Markdown.
- Do not use code fences.
- Do not use bullets, quotes, or explanations.
- Write exactly one result.

## Modes

The requested mode should be one of:

- `single_commit`
- `squash_commit`
- `pr_title`
- `commit_with_body`

## Mode rules

### `single_commit`

- Use Conventional Commits format: `<type>: <subject>`
- Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `build`, `ci`
- Keep subject under `50` characters
- Use imperative mood
- Do not end subject with punctuation
- Do not include a body unless it adds useful context

### `squash_commit`

- Use Conventional Commits format: `<type>: <subject>`
- Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `build`, `ci`
- Keep subject under `50` characters
- Use imperative mood
- Do not end subject with punctuation
- Summarize the final combined result, not intermediate steps
- Do not include a body unless it adds useful context

### `pr_title`

- Write a short PR title
- Keep it under `72` characters
- Use imperative mood
- Do not end with punctuation
- Make it specific and outcome-focused

### `commit_with_body`

- Use Conventional Commits format
- Format:

```text
<type>: <subject>

<body>
```

- Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `build`, `ci`
- Keep subject under `50` characters
- Use imperative mood
- Do not end subject with punctuation
- Include a concise body only when it adds useful context
- Focus on what changed and why, not low-level implementation details

## Selection rules

- Base the message only on the provided diff or commit list.
- Prefer the smallest accurate commit type.
- For squash commits, describe the net result.
- For PR titles, optimize for fast comprehension rather than strict Conventional Commits formatting.
- When creating commits, keep each commit as small as possible while staying logically complete.
- Group only files that belong to the same change.
- A commit may include source changes plus the tests and helper updates required for that exact behavior.
- Do not mix unrelated docs, refactors, logging changes, and feature work in the same commit.

## Versioning and tags

- When a logically complete change set should produce a release version bump, update the project version with `uv version`.
- Use semantic versioning logic:
  - patch: fixes, small compatible improvements, docs-only releases only if the project policy requires it
  - minor: backward-compatible features or meaningful user-visible additions
  - major: breaking changes
- Keep the version bump in the same logical commit set or release step as the change it represents.
- When a release bump is made, create a matching Git tag for that version unless the user explicitly does not want tagging.
- Do not bump the version for every commit by default; do it only when the change logically represents a release-worthy increment.
