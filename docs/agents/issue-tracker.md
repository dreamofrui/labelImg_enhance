# Issue Tracker

Issues for this repo are tracked in **GitHub Issues**.

## Commands

- **Create an issue**: `gh issue create --title "..." --body "..."`
- **List open issues**: `gh issue list`
- **View an issue**: `gh issue view <number>`
- **Close an issue**: `gh issue close <number>`

## PRs as a request surface

**Disabled.** External PRs are not treated as incoming work requests by the `triage` skill.

If you want external PRs to appear in the triage queue, change this flag to **Enabled** and the `triage` skill will label and route them alongside issues.
