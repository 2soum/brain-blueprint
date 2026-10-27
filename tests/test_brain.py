from datetime import date, timedelta

import pytest

from brain_blueprint.note import Note
from brain_blueprint.store import Brain


@pytest.fixture
def brain(tmp_path):
    return Brain(tmp_path / "brain")


def make(title, body, cortex="engineering", **kw):
    return Note(title=title, body=body, cortex=cortex, **kw)


def test_roundtrip_preserves_frontmatter(brain):
    note = brain.encode(make("Base64 the service account key", "> Raw newlines break in prod.",
                             tags=["firebase", "env"], confidence=0.9))
    again = brain.read(note.id)
    assert again.title == note.title
    assert again.tags == ["firebase", "env"]
    assert again.confidence == 0.9
    assert (brain.root / "engineering" / f"{note.id}.md").exists()


def test_encode_never_overwrites(brain):
    a = brain.encode(make("Same title", "first"))
    b = brain.encode(make("Same title", "second"))
    assert a.id != b.id
    assert brain.read(a.id).body.strip() == "first"


def test_search_ranks_title_matches_first(brain):
    brain.encode(make("Postgres connection pooling", "Use pgbouncer in transaction mode."))
    brain.encode(make("Deploy checklist", "Remember postgres migrations before deploy."))
    hits = brain.search("postgres pooling")
    assert hits[0].title == "Postgres connection pooling"


def test_superseded_notes_are_hidden_by_default(brain):
    old = brain.encode(make("Use region us-central1", "Old choice."))
    new = brain.encode(make("Use region europe-west1", "EU data must stay in the EU."))
    brain.supersede(old.id, new.id, "EU prospects data")
    ids = [h.id for h in brain.search("region")]
    assert old.id not in ids and new.id in ids
    assert old.id in [h.id for h in brain.search("region", include_superseded=True)]
    assert brain.read(old.id).superseded_by == new.id
    assert [(link.to, link.rel) for link in brain.read(old.id).links] == [(new.id, "superseded-by")]
    assert [(link.to, link.rel) for link in brain.read(new.id).links] == [(old.id, "supersedes")]


def test_links_are_bidirectional_and_idempotent(brain):
    a = brain.encode(make("Agent drift", "Agents drift on long tasks.", cortex="agents"))
    b = brain.encode(make("Checklist prompts", "A checklist keeps agents on task.", cortex="prompting"))
    brain.link(a.id, b.id)
    brain.link(a.id, b.id)
    assert [link.to for link in brain.read(a.id).links] == [b.id]
    assert [link.to for link in brain.read(b.id).links] == [a.id]


def test_stale_low_confidence_notes_rank_lower(brain):
    fresh = brain.encode(make("Cache invalidation rule", "Invalidate on write.", confidence=0.9))
    stale = brain.encode(make("Cache invalidation rule old", "Invalidate on write.", confidence=0.4,
                              last_validated=date.today() - timedelta(days=720)))
    hits = brain.search("cache invalidation")
    assert hits[0].id == fresh.id
    assert hits[-1].id == stale.id


def test_hand_edits_are_picked_up_on_reindex(brain):
    note = brain.encode(make("Hand edited", "before"))
    path = brain.root / "engineering" / f"{note.id}.md"
    path.write_text(path.read_text().replace("before", "zeppelin"))
    brain.reindex()
    assert brain.search("zeppelin")[0].id == note.id


def test_rejects_unknown_type():
    with pytest.raises(ValueError):
        Note(title="x", body="y", type="rumor")
