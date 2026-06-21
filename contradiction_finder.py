"""
contradiction_finder.py

Finds concept pairs where two or more schools assert DIFFERENT relation
types for the same pair of concepts, e.g. school A says "atman
IS_IDENTICAL_TO brahman" while school B says "atman IS_DISTINCT_FROM
brahman" for the exact same concept pair.

This reuses retriever.py's connect() against the same darshana_graph
FalkorDB instance used by the rest of vada-simulator. No new data, no new
agents, just a different query shape over data you already have loaded.

Usage:
    python3 contradiction_finder.py                  # top 20 contradictions
    python3 contradiction_finder.py --top 50
    python3 contradiction_finder.py --concept atman   # contradictions involving a specific concept
"""

import argparse
from collections import defaultdict
from retriever import connect


def find_contradictions(graph, concept_filter: str = None, limit: int = 20):
    """
    For every (concept_a, concept_b) pair, collect the set of distinct
    relation types asserted by SCHOOL-SPECIFIC edges (school != 'general').
    A pair is "contradicted" if 2+ schools assert different relation types
    for it.
    """
    query = """
    MATCH (a:Concept)-[r:RELATION]->(b:Concept)
    WHERE r.school <> 'general'
    """
    if concept_filter:
        query += " AND (toLower(a.name) = toLower($concept) OR toLower(b.name) = toLower($concept))"
    query += """
    RETURN a.name AS concept_a, b.name AS concept_b, r.school AS school,
           r.relation AS relation, r.edge_id AS edge_id, r.evidence_quote AS evidence_quote
    """
    params = {"concept": concept_filter} if concept_filter else {}
    result = graph.query(query, params)

    # group by (concept_a, concept_b), collecting {school: (relation, edge_id, quote)}
    pairs = defaultdict(dict)
    for row in result.result_set:
        concept_a, concept_b, school, relation, edge_id, evidence_quote = row
        key = tuple(sorted([concept_a, concept_b]))
        # keep the first edge seen per (pair, school); a pair can have many
        # edges per school, we just need one representative disagreement
        if school not in pairs[key]:
            pairs[key][school] = (relation, edge_id, evidence_quote)

    contradictions = []
    for (concept_a, concept_b), school_relations in pairs.items():
        distinct_relations = set(r for r, _, _ in school_relations.values())
        if len(distinct_relations) > 1 and len(school_relations) > 1:
            contradictions.append((concept_a, concept_b, school_relations))

    # sort by number of schools involved, descending (most contested first)
    contradictions.sort(key=lambda c: -len(c[2]))
    return contradictions[:limit]


def print_contradictions(contradictions):
    if not contradictions:
        print("No contradictions found with the current filter.")
        return

    print(f"\nFound {len(contradictions)} contested concept pairs:\n")
    for concept_a, concept_b, school_relations in contradictions:
        print(f"=== {concept_a} <-> {concept_b} ({len(school_relations)} schools) ===")
        for school, (relation, edge_id, quote) in sorted(school_relations.items()):
            quote_preview = (quote[:80] + "...") if quote and len(quote) > 80 else quote
            print(f"  {school:20s} asserts {relation:30s} [{edge_id}]")
            print(f"  {'':20s} evidence: \"{quote_preview}\"")
        print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=20, help="Number of contradictions to show")
    parser.add_argument("--concept", default=None, help="Filter to contradictions involving this concept")
    args = parser.parse_args()

    graph = connect()
    contradictions = find_contradictions(graph, concept_filter=args.concept, limit=args.top)
    print_contradictions(contradictions)


if __name__ == "__main__":
    main()
