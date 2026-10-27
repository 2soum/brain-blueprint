"""A note is one durable fact, stored as Markdown with YAML frontmatter.

One note, one idea. The frontmatter is written for machines (an agent decides
from `description` alone whether to open the note); the body is written for the
next agent that reads it.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date

import yaml

NOTE_TYPES = ("fact", "decision", "preference", "procedure", "episode", "insight")
STATUSES = ("active", "superseded")

_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:80] or "note"


@dataclass
class Link:
    to: str
    rel: str = "related"

    def as_dict(self) -> dict:
        return {"to": self.to, "rel": self.rel}


@dataclass
class Note:
    title: str
    body: str
    type: str = "fact"
    cortex: str = "general"
    description: str = ""
    tags: list[str] = field(default_factory=list)
    confidence: float = 0.7
    created: date = field(default_factory=date.today)
    last_validated: date = field(default_factory=date.today)
    status: str = "active"
    superseded_by: str | None = None
    links: list[Link] = field(default_factory=list)
    id: str = ""

    def __post_init__(self) -> None:
        if self.type not in NOTE_TYPES:
            raise ValueError(f"type must be one of {NOTE_TYPES}, got {self.type!r}")
        if self.status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}, got {self.status!r}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        self.cortex = slugify(self.cortex)
        self.id = self.id or slugify(self.title)
        if not self.description:
            self.description = self.title

    def to_markdown(self) -> str:
        meta = {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "cortex": self.cortex,
            "description": self.description,
            "tags": self.tags,
            "confidence": self.confidence,
            "created": self.created.isoformat(),
            "last_validated": self.last_validated.isoformat(),
            "status": self.status,
        }
        if self.superseded_by:
            meta["superseded_by"] = self.superseded_by
        if self.links:
            meta["links"] = [link.as_dict() for link in self.links]
        head = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).strip()
        return f"---\n{head}\n---\n\n{self.body.strip()}\n"

    @classmethod
    def from_markdown(cls, text: str) -> Note:
        match = _FRONTMATTER.match(text)
        if not match:
            raise ValueError("note has no YAML frontmatter")
        meta = yaml.safe_load(match.group(1)) or {}
        return cls(
            id=meta.get("id", ""),
            title=meta["title"],
            body=match.group(2),
            type=meta.get("type", "fact"),
            cortex=meta.get("cortex", "general"),
            description=meta.get("description", ""),
            tags=list(meta.get("tags") or []),
            confidence=float(meta.get("confidence", 0.7)),
            created=_as_date(meta.get("created")),
            last_validated=_as_date(meta.get("last_validated")),
            status=meta.get("status", "active"),
            superseded_by=meta.get("superseded_by"),
            links=[Link(**raw) for raw in meta.get("links") or []],
        )


def _as_date(value: object) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    return date.today()
