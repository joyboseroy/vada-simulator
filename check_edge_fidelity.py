"""
check_edge_fidelity.py

Looks up the REAL evidence_quote, relation type, and source text for a
specific edge_id, so you can check whether an agent's paraphrase in a
debate transcript was actually faithful to the underlying graph data, or
whether the LLM drifted from what the cited evidence actually says.

This exists because citation-VALIDITY (does this edge_id exist and belong
to this school) is not the same thing as citation-FIDELITY (does the
agent's sentence accurately represent what the edge says). The vada
simulator only checks the former. This script lets you manually audit the
latter for any specific claim that looks questionable.

Usage:
    python3 check_edge_fidelity.py edge_018408
    python3 check_edge_fidelity.py edge_018408 edge_018915 edge_018922
"""

import sys
from retriever import connect


def lookup_edge(graph, edge_id: str):
    query = """
    MATCH (a:Concept)-[r:RELATION {edge_id: $edge_id}]->(b:Concept)
    RETURN a.name AS source_concept, r.relation AS relation, b.name AS target_concept,
           r.school AS school, r.confidence AS confidence,
           r.evidence_quote AS evidence_quote,
           r.source_text AS source_text, r.source_record_id AS source_record_id
    """
    result = graph.query(query, {"edge_id": edge_id})
    if not result.result_set:
        print(f"  edge_id '{edge_id}' not found in graph.")
        return
    row = result.result_set[0]
    print(f"\n  edge_id: {edge_id}")
    print(f"  claim:   {row[0]} --{row[1]}--> {row[2]}")
    print(f"  school:  {row[3]}  (confidence: {row[4]})")
    print(f"  source:  {row[6]} / {row[7]}")
    print(f"  EVIDENCE QUOTE (the actual passage this edge was extracted from):")
    print(f"    \"{row[5]}\"")
    print()
    print(f"  >> Compare this quote against the debate transcript's paraphrase for this")
    print(f"     citation. Does the quote actually support the claim the agent made,")
    print(f"     or did the agent's interpretation go beyond what the quote says?")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 check_edge_fidelity.py <edge_id> [edge_id2 ...]")
        sys.exit(1)

    graph = connect()
    for edge_id in sys.argv[1:]:
        lookup_edge(graph, edge_id)
