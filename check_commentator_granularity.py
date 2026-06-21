"""
check_commentator_granularity.py

Before building a "concept genealogy across commentators" tool, this
checks whether the graph actually has commentator-level attribution
(Shankara vs Ramanuja vs Madhva vs Nimbarka, etc.) or only school-level
attribution (just "advaita", which could be any of several Advaita
commentators merged together).

If this script finds no commentator field, genealogy across NAMED
individuals isn't buildable from the current graph; only genealogy across
SOURCE TEXTS (which do have a real chronological order, e.g. Upanishads
predate the Gita commentaries) would be possible instead.

Usage:
    python3 check_commentator_granularity.py
"""

from retriever import connect


def main():
    graph = connect()

    print("=== Checking for a 'commentator' or similar property on RELATION edges ===\n")
    # try a few plausible property names
    candidate_fields = ["commentator", "author", "commentary", "tagged_from_file"]
    for field in candidate_fields:
        query = f"""
        MATCH ()-[r:RELATION]->()
        WHERE r.{field} IS NOT NULL
        RETURN r.{field} AS value, count(*) AS c
        ORDER BY c DESC
        LIMIT 10
        """
        try:
            result = graph.query(query, {})
            if result.result_set:
                print(f"Field '{field}' EXISTS with values:")
                for row in result.result_set:
                    print(f"  {row[0]!r}: {row[1]} edges")
                print()
            else:
                print(f"Field '{field}': no non-null values found.\n")
        except Exception as e:
            print(f"Field '{field}': query failed ({e})\n")

    print("=== Checking tagged_from_file specifically (may encode commentator via filename) ===\n")
    query = """
    MATCH ()-[r:RELATION]->()
    RETURN DISTINCT r.tagged_from_file AS f
    LIMIT 30
    """
    try:
        result = graph.query(query, {})
        for row in result.result_set:
            print(f"  {row[0]}")
    except Exception as e:
        print(f"  Query failed: {e}")


if __name__ == "__main__":
    main()
