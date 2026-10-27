# The blueprint

How to give a coding agent a long-term memory that stays useful after six months, not just after six days.

## 1. What kind of memory this is

The CoALA paper (Sumers et al., *Cognitive Architectures for Language Agents*, 2023) splits agent memory into four kinds:

| Kind | What it holds | Where it lives for a coding agent |
|---|---|---|
| Working | The current task | The context window |
| Episodic | What happened before | Session transcripts, git history |
| Semantic | What is true | **This brain** |
| Procedural | How to do things | `CLAUDE.md`, rules, skills, prompts |

A brain is **semantic memory, with a bridge to procedural**. A note can be a fact ("this key must be base64"), a decision and its reason, a user preference, a procedure, an episode worth keeping, or an insight. If it is derivable from the repo, it does not belong here: the repo already remembers it.

## 2. Layout

```
brain/
  infra/
    base64-encode-service-account-keys-in-env-vars.md
    firestore-region-europe-west1-for-eu-prospect-data.md
  user/
    user-prefers-silent-memory-operations.md
  agents/
    long-agent-tasks-drift-without-a-checklist.md
  .index.sqlite          # derived, git-ignored
```

- **Cortex = folder = one theme.** Keep the number of cortices small (five to fifteen). An agent must reuse an existing cortex before creating one.
- **The file name is the id.** Ids are slugs of the title, stable for life. Links point at ids.
- **Put the brain in git.** You get review, blame and rollback for free. Letta's 2026 "context repositories" make the same choice: every memory change is a commit.

## 3. The note schema

| Field | Why it exists |
|---|---|
| `id`, `title` | Stable handle, human name. |
| `type` | `fact`, `decision`, `preference`, `procedure`, `episode`, `insight`. Lets the agent weigh a note: a preference is about the user, a decision has a reason that may expire. |
| `cortex` | The theme folder. |
| `description` | **The most important line.** One sentence that lets an agent decide whether to open the note. Search results show it. |
| `tags` | Extra search terms, synonyms, product names. |
| `confidence` | 0 to 1. How sure the writer was. Ranking uses it. |
| `created`, `last_validated` | Age vs. last confirmation. Ranking decays on `last_validated`, not on `created`. |
| `status`, `superseded_by` | `active` or `superseded`, and by what. |
| `links` | `{to, rel}` pairs. `rel` is free text: `related`, `supersedes`, `applies-to`, `contradicts`... |

The body starts with a two or three sentence blockquote **addressed to the next agent**: what to do or avoid, in the imperative. Then the detail, usually *Why* and *How to apply*. Writing for a reader who has none of your context is what keeps a note useful six months later.

## 4. The lifecycle

```
          task arrives
               │
       ┌───────▼────────┐
       │ recall         │  brain_search → read 1-3 hits → verify before relying
       └───────┬────────┘
               │ work
       ┌───────▼────────┐
       │ encode         │  something durable was learned → one note
       └───────┬────────┘
       ┌───────▼────────┐
       │ link           │  1-3 neighbours, prefer other cortices
       └───────┬────────┘
       ┌───────▼────────┐
       │ supersede      │  new note contradicts an old one → retire the old one
       │ / validate     │  old note confirmed → bump last_validated
       └────────────────┘
```

### Recall
Before any non-trivial step, search with words from the task. Open only the best one to three hits. A note is context, not an order: if it names a file, a flag or an API, check that it still exists before acting on it.

### Encode
Write when you learn something a future session would need and could not get from the code: a fix that worked, a constraint, a preference, the reason behind a decision. One idea per note. Do not store secrets, and do not store things that only matter to the current conversation.

### Link
After every encode, link to one to three neighbours. A link inside a cortex is cheap; a link across cortices ("this infra rule applies to that deploy procedure") is what turns a pile of notes into a model of the project.

### Supersede, don't overwrite
When new knowledge contradicts a note, write the new note, then supersede the old one with a reason. The old note stays on disk, marked and linked both ways (`supersedes` / `superseded-by`), and disappears from default search. This is the same principle as Graphiti's bi-temporal facts and mem0's graph variant: invalidate, don't delete, so you can always answer "what did we believe, and when did that change?"

### Validate
When a session confirms an old note still holds, record it. Validation is what keeps a correct but old note from sinking in the ranking.

## 5. Ranking

```
score = relevance × (0.5 + 0.5 × confidence) × (0.5 + 0.5 × freshness)
freshness = 0.5 ^ (days since last_validated / 180)
```

- **Relevance** is SQLite FTS5 BM25, with fields weighted title 4 > description 3 > tags 2 > body 1.
- Confidence and freshness **can only halve** a score, never zero it: an old but highly relevant note still surfaces.
- Superseded notes are filtered out unless asked for.

Every factor is a plain number, returned with the hit. When recall is wrong you can see why.

**Where to go next.** BM25 catches exact identifiers and rare terms but misses paraphrase. The standard upgrade is hybrid search: run BM25 and embeddings side by side and merge the two ranked lists with Reciprocal Rank Fusion (score = Σ 1/(60 + rank), Cormack et al., SIGIR 2009), optionally followed by a cross-encoder reranker. Graph expansion (also returning the linked neighbours of the top hits) is the other cheap win.

## 6. The protocol you give the agent

Memory only works if the agent uses it without being asked. Put the rules in the always-loaded instructions (`CLAUDE.md`, `AGENTS.md`). The ready-to-paste version is [templates/AGENTS.md](../templates/AGENTS.md). Its core:

- recall before non-trivial steps;
- encode durable learnings immediately, one idea per note;
- reuse cortices, link after encoding, supersede instead of editing history;
- treat recalled notes as possibly stale, and verify before acting;
- work silently.

Anthropic's own memory tool injects a similar protocol ("always view your memory directory before doing anything else"), and Claude Code's auto memory keeps an always-loaded index (`MEMORY.md`) with one file per topic. Same pattern: a small index in context, details read on demand.

## 7. Safety

- **Never store secrets.** Notes are plain files and often end up in git.
- **Confine paths.** Ids are slugified, so a note can't escape the brain folder.
- **Don't expose an MCP memory server to the network without authentication.** Run it over stdio locally.
- **Treat memory as untrusted input.** A note can be wrong or outdated; the protocol says to verify before acting.

## 8. Evaluating a brain

Public benchmarks measure conversational memory:

- **LoCoMo** (Maharana et al., ACL 2024): long multi-session dialogues.
- **LongMemEval** (Wu et al., ICLR 2025): 500 questions covering extraction, multi-session reasoning, temporal reasoning, **knowledge updates** and **abstention**.

For a coding agent, build a small private set in the same spirit:

| Check | Question |
|---|---|
| Recall | Given a task, is the right note in the top 3? |
| Update | After a supersede, does search return the new note and hide the old one? |
| Abstention | For a question the brain can't answer, does the agent say so instead of inventing? |
| Precision | Of what the agent encoded this week, how much is still true and useful? |

Published scores vary wildly with the protocol: the same system appears anywhere from the low 60s to above 90% on LoCoMo depending on who ran it. Trust your own eval over a leaderboard.

## Sources

- Sumers et al., *Cognitive Architectures for Language Agents*, arXiv:2309.02427
- Packer et al., *MemGPT*, arXiv:2310.08560 · Letta context repositories: letta.com/blog/context-repositories
- Chhikara et al., *Mem0*, arXiv:2504.19413
- Rasmussen et al., *Zep: a temporal knowledge graph architecture for agent memory*, arXiv:2501.13956 · github.com/getzep/graphiti
- Xu et al., *A-MEM: Agentic Memory for LLM Agents*, arXiv:2502.12110
- Maharana et al., *LoCoMo*, arXiv:2402.17753 · Wu et al., *LongMemEval*, arXiv:2410.10813
- Claude Code memory: code.claude.com/docs/en/memory · Anthropic memory tool: platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
- Basic Memory: github.com/basicmachines-co/basic-memory · MCP reference memory server: github.com/modelcontextprotocol/servers/tree/main/src/memory
- Cormack, Clarke, Büttcher, *Reciprocal Rank Fusion*, SIGIR 2009
