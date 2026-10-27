"""MCP server exposing the brain to any agent (Claude Code, Claude Desktop, Cursor...).

Run:  BRAIN_DIR=~/brain uv run brain-mcp
"""

from __future__ import annotations

import os
from dataclasses import asdict

from mcp.server import MCPServer

from .note import Note
from .store import Brain

mcp = MCPServer("brain")
_brain: Brain | None = None


def brain() -> Brain:
    global _brain
    if _brain is None:
        _brain = Brain(os.path.expanduser(os.environ.get("BRAIN_DIR", "~/brain")))
    _brain.reindex()  # pick up notes a human edited by hand
    return _brain


@mcp.tool()
def brain_search(query: str, k: int = 5, cortex: str | None = None,
                 include_superseded: bool = False) -> list[dict]:
    """Recall notes relevant to a task. Call this before any non-trivial step.

    Returns id, title, description and score; open the promising ones with brain_read.
    """
    return [asdict(h) for h in brain().search(query, k, cortex, include_superseded)]


@mcp.tool()
def brain_read(id: str) -> str:
    """Return the full Markdown of one note, frontmatter included."""
    return brain().read(id).to_markdown()


@mcp.tool()
def brain_list(cortex: str | None = None) -> dict:
    """List cortices with their note counts, or the notes of one cortex."""
    b = brain()
    if cortex is None:
        return {"cortices": b.cortices()}
    return {"cortex": cortex, "notes": [asdict(h) for h in b.list(cortex)]}


@mcp.tool()
def brain_encode(title: str, body: str, cortex: str, type: str = "fact",
                 description: str = "", tags: list[str] | None = None,
                 confidence: float = 0.7) -> dict:
    """Store one durable learning: a fix that worked, a constraint, a preference, a decision.

    Start the body with a 2-3 sentence blockquote addressed to the next agent.
    Pick an existing cortex when one fits (see brain_list); create a new one only for a new theme.
    """
    note = brain().encode(Note(title=title, body=body, cortex=cortex, type=type,
                               description=description, tags=tags or [], confidence=confidence))
    return {"id": note.id, "cortex": note.cortex}


@mcp.tool()
def brain_link(a: str, b: str, rel: str = "related") -> str:
    """Link two notes both ways. Links across cortices are the most valuable."""
    brain().link(a, b, rel)
    return f"linked {a} <-> {b} ({rel})"


@mcp.tool()
def brain_supersede(old: str, new: str, reason: str) -> str:
    """Retire an outdated note in favour of a newer one. Never edit history in place."""
    brain().supersede(old, new, reason)
    return f"{old} superseded by {new}"


@mcp.tool()
def brain_validate(id: str, confidence: float | None = None) -> str:
    """Mark a note as re-checked today, optionally with a new confidence."""
    note = brain().validate(id, confidence)
    return f"{note.id} validated on {note.last_validated} (confidence {note.confidence})"


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
