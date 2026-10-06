import heapq


def topological_order(
    slugs: dict[int, str], prerequisites: dict[int, set[int]]
) -> list[int]:
    """Kahn's algorithm; pick the smallest slug from all currently ready nodes."""
    dependents: dict[int, list[int]] = {concept_id: [] for concept_id in slugs}
    indegree = {concept_id: 0 for concept_id in slugs}
    for concept_id, required in prerequisites.items():
        if concept_id not in slugs or not required.issubset(slugs):
            raise ValueError("Prerequisite graph references an unknown concept.")
        indegree[concept_id] = len(required)
        for prerequisite_id in required:
            dependents[prerequisite_id].append(concept_id)

    ready = [(slugs[node], node) for node, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    ordered = []
    while ready:
        _, node = heapq.heappop(ready)
        ordered.append(node)
        for dependent in dependents[node]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, (slugs[dependent], dependent))
    if len(ordered) != len(slugs):
        raise ValueError("Prerequisite graph must be acyclic.")
    return ordered
