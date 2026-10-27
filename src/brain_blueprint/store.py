"""The brain: a folder of Markdown notes plus a disposable SQLite search index.

Layout on disk:

    brain/
      <cortex>/<note-id>.md     source of truth, human-editable, git-friendly
      .index.sqlite             derived; delete it any time, it rebuilds

Ranking = BM25 relevance x confidence x freshness, with superseded notes hidden
by default. Every factor is a plain number you can inspect, so a bad recall can
be debugged instead of guessed at.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .note import Link, Note

FRESHNESS_HALF_LIFE_DAYS = 180


@dataclass
class Hit:
    id: str
    title: str
    description: str
    cortex: str
    score: float
    status: str


class Brain:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / ".index.sqlite")
        self.db.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS notes USING fts5("
            "id UNINDEXED, cortex UNINDEXED, status UNINDEXED, confidence UNINDEXED, "
            "last_validated UNINDEXED, mtime UNINDEXED, title, description, tags, body, "
            "tokenize='porter unicode61 remove_diacritics 2')"
        )
        self.reindex()

    # ---- files -------------------------------------------------------------

    def _path(self, note: Note) -> Path:
        return self.root / note.cortex / f"{note.id}.md"

    def _find(self, note_id: str) -> Path:
        matches = list(self.root.glob(f"*/{note_id}.md"))
        if not matches:
            raise KeyError(f"no note with id {note_id!r}")
        return matches[0]

    def _unique_id(self, base: str) -> str:
        candidate, n = base, 2
        while list(self.root.glob(f"*/{candidate}.md")):
            candidate, n = f"{base}-{n}", n + 1
        return candidate

    def _write(self, note: Note) -> Path:
        path = self._path(note)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(note.to_markdown(), encoding="utf-8")
        self._index(note, path)
        return path

    # ---- index -------------------------------------------------------------

    def _index(self, note: Note, path: Path) -> None:
        self.db.execute("DELETE FROM notes WHERE id = ?", (note.id,))
        self.db.execute(
            "INSERT INTO notes VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                note.id, note.cortex, note.status, note.confidence,
                note.last_validated.isoformat(), path.stat().st_mtime,
                note.title, note.description, " ".join(note.tags), note.body,
            ),
        )
        self.db.commit()

    def reindex(self) -> int:
        """Bring the index in line with the files. Returns how many notes changed."""
        known = dict(self.db.execute("SELECT id, mtime FROM notes"))
        seen, changed = set(), 0
        for path in self.root.glob("*/*.md"):
            note_id = path.stem
            seen.add(note_id)
            if known.get(note_id) == path.stat().st_mtime:
                continue
            self._index(Note.from_markdown(path.read_text(encoding="utf-8")), path)
            changed += 1
        for gone in set(known) - seen:
            self.db.execute("DELETE FROM notes WHERE id = ?", (gone,))
            changed += 1
        self.db.commit()
        return changed

    # ---- operations ----------------------------------------------------------

    def encode(self, note: Note) -> Note:
        """Store a new note. Never overwrites: a clashing id gets a numeric suffix."""
        note.id = self._unique_id(note.id)
        self._write(note)
        return note

    def read(self, note_id: str) -> Note:
        return Note.from_markdown(self._find(note_id).read_text(encoding="utf-8"))

    def list(self, cortex: str | None = None) -> list[Hit]:
        sql = "SELECT id, title, description, cortex, status FROM notes"
        rows = self.db.execute(sql + (" WHERE cortex = ?" if cortex else "") + " ORDER BY cortex, id",
                               (cortex,) if cortex else ())
        return [Hit(r[0], r[1], r[2], r[3], 0.0, r[4]) for r in rows]

    def cortices(self) -> dict[str, int]:
        return dict(self.db.execute("SELECT cortex, count(*) FROM notes GROUP BY cortex ORDER BY 2 DESC"))

    def search(self, query: str, k: int = 5, cortex: str | None = None,
               include_superseded: bool = False, today: date | None = None) -> list[Hit]:
        today = today or date.today()
        terms = " OR ".join(f'"{t}"' for t in query.replace('"', " ").split() if t)
        if not terms:
            return []
        where = ["notes MATCH ?"]
        params: list[object] = [terms]
        if cortex:
            where.append("cortex = ?")
            params.append(cortex)
        if not include_superseded:
            where.append("status = 'active'")
        rows = self.db.execute(
            "SELECT id, title, description, cortex, status, confidence, last_validated, "
            "bm25(notes, 0, 0, 0, 0, 0, 0, 4.0, 3.0, 2.0, 1.0) FROM notes WHERE "
            + " AND ".join(where) + " LIMIT 200",
            params,
        ).fetchall()
        hits = []
        for note_id, title, desc, ctx, status, conf, validated, bm25 in rows:
            age = (today - date.fromisoformat(validated)).days
            freshness = 0.5 ** (max(age, 0) / FRESHNESS_HALF_LIFE_DAYS)
            relevance = -bm25  # SQLite returns lower-is-better
            score = relevance * (0.5 + 0.5 * float(conf)) * (0.5 + 0.5 * freshness)
            hits.append(Hit(note_id, title, desc, ctx, round(score, 4), status))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:k]

    def link(self, a: str, b: str, rel: str = "related", inverse: str | None = None) -> None:
        """Connect two notes in both directions. Idempotent.

        `inverse` names the relation from b back to a; it defaults to `rel` (symmetric).
        """
        for src, dst, r in ((a, b, rel), (b, a, inverse or rel)):
            note = self.read(src)
            if not any(link.to == dst for link in note.links):
                note.links.append(Link(dst, r))
                self._write(note)

    def supersede(self, old_id: str, new_id: str, reason: str) -> None:
        """Retire a note in favour of a newer one. The old note stays, marked and linked."""
        old = self.read(old_id)
        self.read(new_id)  # must exist
        old.status = "superseded"
        old.superseded_by = new_id
        old.body = f"{old.body.rstrip()}\n\n> Superseded by [[{new_id}]] on {date.today().isoformat()}: {reason}\n"
        self._write(old)
        self.link(new_id, old_id, "supersedes", inverse="superseded-by")

    def validate(self, note_id: str, confidence: float | None = None) -> Note:
        """Record that a note was checked and still holds."""
        note = self.read(note_id)
        note.last_validated = date.today()
        if confidence is not None:
            note.confidence = confidence
        self._write(note)
        return note
