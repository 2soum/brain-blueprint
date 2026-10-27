# The agent memory landscape (October 2026)

A short field guide to the systems this blueprint borrows from. Licences and facts were checked against each project's own docs or paper; anything I could not confirm is marked *unverified*.

## Letta (formerly MemGPT)
- **Idea:** treat the context window like an operating system's RAM. Editable *memory blocks* stay in context, while older messages (recall memory) and a vector store (archival memory) sit outside and are searched with tools the agent calls itself.
- **2026:** memory moves to a git-backed file system ("context repositories"), with background agents that consolidate memory between turns.
- **Licence:** Apache-2.0. github.com/letta-ai/letta

## mem0
- **Idea:** an LLM extracts candidate facts from the conversation. For each one, it compares against the closest existing memories and picks **ADD, UPDATE, DELETE or NOOP**. The graph variant (Mem0g) marks outdated relations invalid instead of deleting them.
- **Scope:** memories are scoped to a user, a session or an agent.
- **Licence:** Apache-2.0. github.com/mem0ai/mem0

## Graphiti / Zep
- **Idea:** a **bi-temporal knowledge graph** of episodes (raw input, for provenance), entities and facts. Each fact carries a validity window. When a fact is contradicted, its window is closed rather than the fact deleted.
- **Recall:** embeddings + BM25 + graph traversal, with reranking, and no LLM call at query time.
- **Licence:** Graphiti is Apache-2.0 (github.com/getzep/graphiti); Zep Cloud is commercial. Its reference MCP server ships **without authentication**.

## cognee
- **Idea:** an Extract → Cognify → Load pipeline that builds a knowledge graph plus vector indexes, with `remember / recall / improve / forget` on top.
- **Licence:** Apache-2.0. github.com/topoteretes/cognee

## A-MEM
- **Idea:** Zettelkasten for agents. Each memory becomes a structured note (content, context, keywords, tags, embedding). On insert, an LLM decides which existing notes to link, and can rewrite the context of older notes ("memory evolution").
- **Paper:** arXiv:2502.12110. Licence *unverified*.

## LangMem (LangChain)
- **Idea:** semantic memory as a collection of facts or a single profile; episodic memory as successful examples; procedural memory as **prompt optimization**.
- **Writing:** either on the hot path (during the conversation) or in the background after it.
- **Licence:** *unverified* (likely MIT).

## MCP reference `memory` server
- **Idea:** the simplest possible knowledge graph: entities with observations, and directed relations, stored in a JSONL file.
- **Recall:** string matching, no embeddings. Forgetting means manual deletes.
- **Licence:** MIT.

## Claude Code
- **CLAUDE.md files** at managed, user, project and local scope, plus path-scoped rules in `.claude/rules/`. `@path` imports are allowed, up to four hops deep.
- **Auto memory:** one file per topic under `~/.claude/projects/<project>/memory/`, with an index (`MEMORY.md`) whose first 200 lines are loaded every session. Notes carry a `type` (user, feedback, project, reference).
- **API memory tool:** a client-side `/memories` directory with `view`, `create`, `str_replace`, `insert`, `delete` and `rename`.

## Basic Memory
- **Idea:** Markdown files are the source of truth, synced to a local SQLite (or Postgres) index. Observations are written as `- [category] fact #tag`, relations as `relation [[Target]]`.
- **Recall:** hybrid full-text + vector search, with graph context.
- **Licence:** AGPL-3.0. github.com/basicmachines-co/basic-memory

## Hindsight (Vectorize, 2025)
- **Idea:** four networks (world facts, agent experiences, entity summaries, evolving beliefs) behind three operations: **retain, recall, reflect**.
- **Paper:** arXiv:2512.12818.

## A word on benchmark numbers

- **LoCoMo**, as reported in the mem0 paper (LLM judge, GPT-4o-mini):

  | System | Score |
  |---|---|
  | Full context | 72.9 |
  | Mem0g | 68.4 |
  | Mem0 | 66.9 |
  | Zep | 66.0 |
  | Best RAG | 61.0 |
  | LangMem | 58.1 |
  | A-Mem | 48.4 |

- **mem0's own README (2026):** 92.5 on LoCoMo for its **managed platform**, with optimizations that are not in the open-source SDK.
- **The Zep paper:** 94.8% on DMR, against 93.4% for MemGPT.

The same system can land 30 points apart depending on who runs it and how. Use these figures to understand the field, not to choose a winner.
