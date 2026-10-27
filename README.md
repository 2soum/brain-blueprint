# brain-blueprint

**Long-term memory for coding agents, done with files you can read.**

Agents forget everything between sessions. Most memory layers fix that with a vector database you can't open, edit or review. This repo takes the other road, the one Claude Code's auto memory, Letta's MemFS and Basic Memory have converged on in 2025-2026: **memory is a folder of Markdown notes**, and the database is only an index you can delete.

It contains two things:

1. **[The blueprint](docs/blueprint.md).** How to structure an agent's long-term memory: the note schema, the lifecycle (recall, encode, link, supersede, validate), ranking, the protocol you give the agent, and how to evaluate it.
2. **A reference implementation.** A small MCP server in Python (SQLite FTS5, ~300 lines, tested) that plugs into Claude Code, Claude Desktop, Cursor or any MCP client.

## The design in six rules

1. **One note, one idea.** A Markdown file with typed YAML frontmatter. The `description` line is written so an agent can decide to open the note without opening it.
2. **Files are the truth, the index is disposable.** Humans can edit notes by hand; the index catches up on the next call.
3. **Recall before acting.** The agent searches memory before any non-trivial step, then reads only the 1-3 best hits.
4. **Rank on more than relevance.** Score = BM25 relevance × confidence × freshness. Every factor is a number you can inspect when recall goes wrong.
5. **Supersede, never overwrite.** A contradicted note is marked `superseded`, linked to its replacement and hidden from search, but its history stays. This mirrors how Graphiti invalidates facts instead of deleting them.
6. **Link across themes.** Notes live in *cortices* (one folder per theme). Links between cortices are where the value is.

## Quickstart

```bash
git clone https://github.com/2soum/brain-blueprint && cd brain-blueprint
uv sync
BRAIN_DIR=./examples/brain uv run brain-mcp   # stdio MCP server
```

Add it to Claude Code:

```bash
claude mcp add brain -e BRAIN_DIR=$HOME/brain -- uv --directory $PWD run brain-mcp
```

Then paste [`templates/AGENTS.md`](templates/AGENTS.md) into your `CLAUDE.md` or `AGENTS.md`, so the agent knows when to recall and when to write.

## Tools

| Tool | What it does |
|---|---|
| `brain_search(query, k, cortex?, include_superseded?)` | Ranked recall. Returns id, title, description and score. |
| `brain_read(id)` | Full note, frontmatter included. |
| `brain_list(cortex?)` | Cortices with counts, or the notes of one cortex. |
| `brain_encode(title, body, cortex, type, ...)` | Store a new note. Never overwrites: a clashing id gets a suffix. |
| `brain_link(a, b, rel)` | Link two notes both ways. |
| `brain_supersede(old, new, reason)` | Retire a note in favour of a newer one. |
| `brain_validate(id, confidence?)` | Record that a note was re-checked today. |

## What a note looks like

```markdown
---
id: firestore-region-europe-west1-for-eu-prospect-data
title: Firestore region europe-west1 for EU prospect data
type: decision
cortex: infra
description: EU prospect data stays in the EU; a Firestore region cannot change after creation.
tags: [firestore, region, gdpr]
confidence: 0.95
created: 2026-10-27
last_validated: 2026-10-27
status: active
links:
  - to: firestore-region-us-central1
    rel: supersedes
---

> For the next agent: create every new Firestore database in eur3 or europe-west1.
> Moving later means a migration.
```

Browse [`examples/brain`](examples/brain) for a small brain with links and a superseded decision.

## How it compares

| | Storage | Recall | Contradictions |
|---|---|---|---|
| **brain-blueprint** | Markdown + SQLite FTS5 | BM25 × confidence × freshness | Supersede with history |
| Claude Code auto memory | Markdown + `MEMORY.md` index | Index always loaded, files on demand | Manual edits |
| Basic Memory | Markdown + SQLite/Postgres | Full-text + vectors + graph | Manual edits |
| Letta | Memory blocks + archive; git-backed MemFS (2026) | Blocks in context + search tools | Rewrite, git history |
| mem0 | Vector facts, optional graph | Vectors (+ BM25 with extras) | LLM picks ADD / UPDATE / DELETE |
| Graphiti / Zep | Bi-temporal knowledge graph | Vectors + BM25 + graph traversal | Facts invalidated with a timestamp |
| MCP reference `memory` server | JSONL entities and relations | String matching | Manual deletes |

Details, sources and caveats on published benchmark numbers are in [docs/landscape.md](docs/landscape.md).

## Roadmap

- Optional embeddings and Reciprocal Rank Fusion for paraphrase recall.
- Graph expansion: return the neighbours of the top hits.
- A background `consolidate` pass to merge duplicates and flag stale notes.
- An evaluation harness on LongMemEval-style questions (updates, abstention).

## Development

```bash
uv run pytest -q
uv run ruff check src tests
```

MIT licensed. Built by [Dayssam Bakaar](https://dayssam-bakaar.vercel.app).
