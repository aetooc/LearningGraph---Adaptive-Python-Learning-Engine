from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_engine
from app.graph import topological_order
from app.models import Concept, Prerequisite

CONCEPTS = [
    ("variables", "Variables", "Bind names to values; assign and reassign variables."),
    ("data-types", "Data Types", "Use integers, floats, strings, booleans, and None."),
    ("operators", "Operators", "Apply arithmetic, comparison, and boolean operators."),
    ("conditionals", "Conditionals", "Choose branches with if, elif, and else."),
    ("loops", "Loops", "Repeat work with for, while, and range."),
    ("functions", "Functions", "Define reusable functions with parameters and return values."),
    ("lists", "Lists", "Store, index, slice, and iterate over ordered collections."),
    ("dictionaries", "Dictionaries", "Store and retrieve values by key."),
    ("exceptions", "Exceptions", "Handle failures with try, except, and finally."),
    ("classes", "Classes", "Group state and behavior using classes and instances."),
    ("modules", "Modules", "Organize Python code into modules and use imports."),
]

# Each key depends on the slugs listed in its value.
PREREQUISITES = {
    "data-types": ["variables"],
    "operators": ["data-types"],
    "conditionals": ["variables", "operators"],
    "loops": ["conditionals"],
    "functions": ["variables", "data-types"],
    "lists": ["variables", "loops"],
    "dictionaries": ["lists"],
    "exceptions": ["functions"],
    "classes": ["functions"],
    "modules": ["functions"],
}


def seed_curriculum(db: Session) -> None:
    """Insert missing controlled curriculum data; reruns preserve learner progress."""
    concepts = {concept.slug: concept for concept in db.scalars(select(Concept))}
    for slug, name, description in CONCEPTS:
        if slug not in concepts:
            concept = Concept(slug=slug, name=name, description=description)
            db.add(concept)
            concepts[slug] = concept
    db.flush()
    existing = {(edge.concept_id, edge.prerequisite_id) for edge in db.scalars(select(Prerequisite))}
    for slug, required in PREREQUISITES.items():
        for prerequisite_slug in required:
            pair = (concepts[slug].id, concepts[prerequisite_slug].id)
            if pair not in existing:
                db.add(Prerequisite(concept_id=pair[0], prerequisite_id=pair[1]))
    db.flush()
    edges: dict[int, set[int]] = {}
    for edge in db.scalars(select(Prerequisite)):
        edges.setdefault(edge.concept_id, set()).add(edge.prerequisite_id)
    topological_order({concept.id: concept.slug for concept in concepts.values()}, edges)


def main() -> None:
    with Session(get_engine()) as db, db.begin():
        seed_curriculum(db)
    print("Python Fundamentals curriculum seeded (11 concepts).")


if __name__ == "__main__":
    main()
