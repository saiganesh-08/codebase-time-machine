"""
Combines git history signals (change frequency, bug-fix frequency) with
static dependency graph signals (fan-in / how many things depend on this)
into a single risk score per function.
"""
from typing import Dict, List


def compute_risk_scores(
    functions_calls: Dict[str, List[str]],
    functions_called_by: Dict[str, List[str]],
    change_counts: Dict[str, int],
    bugfix_counts: Dict[str, int],
) -> Dict[str, float]:
    """
    risk = normalized(change_count) * 0.35
         + normalized(bugfix_count) * 0.35
         + normalized(fan_in)       * 0.30

    fan_in = number of other functions that depend on this one --
    a proxy for blast radius if this function breaks.
    """
    max_change = max(change_counts.values(), default=0) or 1
    max_bugfix = max(bugfix_counts.values(), default=0) or 1
    max_fanin = max((len(v) for v in functions_called_by.values()), default=0) or 1

    scores = {}
    for qname in functions_calls:
        change = change_counts.get(qname, 0) / max_change
        bugfix = bugfix_counts.get(qname, 0) / max_bugfix
        fanin = len(functions_called_by.get(qname, [])) / max_fanin

        score = round((change * 0.35 + bugfix * 0.35 + fanin * 0.30) * 100, 2)
        scores[qname] = score

    return scores


def transitive_blast_radius(
    target: str,
    called_by: Dict[str, List[str]],
    max_depth: int = 5,
) -> List[str]:
    """BFS over the 'called_by' graph to find everything transitively affected."""
    visited = set()
    frontier = [target]
    depth = 0

    while frontier and depth < max_depth:
        next_frontier = []
        for node in frontier:
            for caller in called_by.get(node, []):
                if caller not in visited and caller != target:
                    visited.add(caller)
                    next_frontier.append(caller)
        frontier = next_frontier
        depth += 1

    return sorted(visited)
