"""
inspect_sources.py

Diagnostic: lists all distinct source_text values actually present in the
graph, with edge counts. Use this to find the real naming convention for
Pali Canon sources instead of guessing (my earlier guess of
"digha_nikaya" etc. in retriever.py's BUDDHIST_SOURCE_TEXTS was wrong --
returned zero results).
"""

from retriever import connect


def main():
    graph = connect()
    query = """
    MATCH ()-[r:RELATION]->()
    RETURN r.source_text AS source_text, count(*) AS edge_count
    ORDER BY edge_count DESC
    """
    result = graph.query(query, {})
    print("All distinct source_text values in the graph:\n")
    for row in result.result_set:
        print(f"  {row[0]!r:50s} {row[1]} edges")


if __name__ == "__main__":
    main()
