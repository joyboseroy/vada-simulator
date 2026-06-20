"""
explore_graph.py

Quick exploration helper: shows which concepts have the most edges per
specific school (excluding the noisy "general" bucket), so you can pick a
debate pairing that's actually well-populated instead of guessing.

Usage:
    python3 explore_graph.py
    python3 explore_graph.py --school advaita
"""

import argparse
from collections import Counter
from retriever import connect, BUDDHIST_SOURCE_TEXTS


def top_buddhist_concepts(graph, limit: int = 15):
    """Buddhism has no populated school tag, so we find top concepts by
    source_text membership in the Pali Canon texts instead."""
    query = """
    MATCH (a:Concept)-[r:RELATION]->(b:Concept)
    WHERE r.source_text IN $sources
    RETURN a.name AS concept, count(*) AS edge_count
    ORDER BY edge_count DESC
    LIMIT $limit
    """
    result = graph.query(query, {"sources": BUDDHIST_SOURCE_TEXTS, "limit": limit})
    return [(row[0], row[1]) for row in result.result_set]


def top_concepts_by_school(graph, school: str, limit: int = 15):
    query = """
    MATCH (a:Concept)-[r:RELATION {school: $school}]->(b:Concept)
    RETURN a.name AS concept, count(*) AS edge_count
    ORDER BY edge_count DESC
    LIMIT $limit
    """
    result = graph.query(query, {"school": school, "limit": limit})
    return [(row[0], row[1]) for row in result.result_set]


def schools_overview(graph):
    query = """
    MATCH ()-[r:RELATION]->()
    RETURN r.school AS school, count(*) AS edge_count
    ORDER BY edge_count DESC
    """
    result = graph.query(query, {})
    return [(row[0], row[1]) for row in result.result_set]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--school", default=None, help="Show top concepts for a specific school")
    args = parser.parse_args()

    graph = connect()

    if args.school and args.school.lower() == "buddhist":
        print("Top concepts for 'buddhist' (by Pali Canon source_text membership, "
              "since this dataset has no populated school tag for Buddhism):\n")
        for concept, count in top_buddhist_concepts(graph):
            print(f"  {concept:30s} {count} edges")
    elif args.school:
        print(f"Top concepts for school='{args.school}' (by edge count):\n")
        for concept, count in top_concepts_by_school(graph, args.school):
            print(f"  {concept:30s} {count} edges")
    else:
        print("Edge counts by school (find specific schools with real volume, not just 'general'):\n")
        for school, count in schools_overview(graph):
            print(f"  {school or '(null)':25s} {count} edges")
        print("\nRun again with --school <name> to see top concepts for a specific school.")


if __name__ == "__main__":
    main()
