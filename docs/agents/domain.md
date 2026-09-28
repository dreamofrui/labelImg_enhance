# Domain Documentation

## Layout

**Single-context** — this repo has one shared domain vocabulary.

- `CONTEXT.md` at the repo root — the project glossary
- `docs/adr/` — architectural decision records

## Consumer rules

When a skill or agent needs domain context:

1. **Read `CONTEXT.md` first** if it exists — it's the authoritative glossary.
2. **Search `docs/adr/` for relevant decisions** when working on architecture, data models, or cross-cutting concerns.
3. **Update `CONTEXT.md`** when introducing new domain terms or clarifying existing ones.
4. **Create an ADR** when making architectural decisions that future work should know about.
