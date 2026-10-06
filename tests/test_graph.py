import pytest
from sqlalchemy import func, select

from app.db.seed import seed_curriculum
from app.graph import topological_order
from app.models import Concept, Prerequisite


def test_seed_is_idempotent_and_graph_is_acyclic(db):
    seed_curriculum(db)
    db.commit()
    assert db.scalar(select(func.count()).select_from(Concept)) == 11
    assert db.scalar(select(func.count()).select_from(Prerequisite)) == 13
    concepts = {c.id: c.slug for c in db.scalars(select(Concept))}
    edges = {}
    for edge in db.scalars(select(Prerequisite)):
        edges.setdefault(edge.concept_id, set()).add(edge.prerequisite_id)
    ordered = topological_order(concepts, edges)
    assert concepts[ordered[0]] == "variables"
    assert len(ordered) == 11


def test_cycle_is_rejected():
    with pytest.raises(ValueError, match="acyclic"):
        topological_order({1: "a", 2: "b"}, {1: {2}, 2: {1}})
