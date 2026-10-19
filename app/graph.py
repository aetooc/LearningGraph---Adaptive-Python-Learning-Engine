import heapq


def topological_order(
    slugs: dict[int, str], prerequisites: dict[int, set[int]]
) -> list[int]:
    """Kahn's algorithm; pick the smallest slug from all currently ready nodes."""
    # dependents: which concepts depend on this concept?
    dependents: dict[int, list[int]] = {concept_id: [] for concept_id in slugs}
    # indegree: how many prerequisites/incoming edges does this concept have?
    indegree = {concept_id: 0 for concept_id in slugs}
    for concept_id, required in prerequisites.items():
        if concept_id not in slugs or not required.issubset(slugs):
            raise ValueError("Prerequisite graph references an unknown concept.")
        indegree[concept_id] = len(required)

        # ID	Concept	indegree	dependents
        # 1	    Variables	0	    [2, 4]
        # 2	    Data Types	1	    [3, 4]
        for prerequisite_id in required:
            dependents[prerequisite_id].append(concept_id)

    #ready = [("variables", 1)]
    ready = [(slugs[node], node) for node, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    ordered = []
    while ready:
        _, node = heapq.heappop(ready)
        ordered.append(node)
        for dependent in dependents[node]:
            indegree[dependent] -= 1
            # Add a dependent when its indegree reaches zero:
            if indegree[dependent] == 0:
                heapq.heappush(ready, (slugs[dependent], dependent))
    if len(ordered) != len(slugs):
        raise ValueError("Prerequisite graph must be acyclic.")
    return ordered

# my summary:
# Put all zero-indegree nodes into ready.
# Pop one from ready and append it to ordered.
# Reduce the indegree of each of its dependents.
# Add any dependent that reaches zero to ready.
# Repeat until ready is empty.
