"""
seed_demo_graph.py

Populates a tiny hand-written graph in FalkorDB so you can test the vada
simulator without needing the full darshana-graph / emptiness-graph dataset.
Just enough edges on "atman" (Advaita vs Buddhist) to run an end-to-end demo.

Run this AFTER installing FalkorDB and BEFORE run_debate.py.
"""

from falkordb import FalkorDB

GRAPH_NAME = "darshana_graph"  # must match retriever.py's GRAPH_NAME

SEED_EDGES = [
    # (relation, source_concept, target_concept, school, source_text, passage_ref)
    ("IS_IDENTICAL_TO", "atman", "brahman", "advaita",
     "Chandogya Upanishad", "6.8.7 (tat tvam asi)"),
    ("IS_IDENTICAL_TO", "atman", "brahman", "advaita",
     "Brahma Sutra Bhashya", "Shankara, 1.1.1"),
    ("IS_UNCHANGING", "atman", "atman", "advaita",
     "Brahma Sutra Bhashya", "Shankara, 2.3.7"),

    ("IS_DISTINCT_FROM", "atman", "anatman", "buddhist",
     "Anattalakkhana Sutta", "SN 22.59"),
    ("REFUTES", "anatman", "atman", "buddhist",
     "Anattalakkhana Sutta", "SN 22.59"),
    ("IS_IMPERMANENT", "skandha", "skandha", "buddhist",
     "Anattalakkhana Sutta", "SN 22.59"),
]


def seed():
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph(GRAPH_NAME)

    # clear any prior demo data in this graph (safe for a fresh demo graph only!)
    graph.query("MATCH (n) DETACH DELETE n")

    for relation, src, tgt, school, source_text, passage_ref in SEED_EDGES:
        query = f"""
        MERGE (a:Concept {{name: $src}})
        MERGE (b:Concept {{name: $tgt}})
        CREATE (a)-[r:{relation} {{
            school: $school,
            source_text: $source_text,
            passage_ref: $passage_ref
        }}]->(b)
        """
        graph.query(query, {
            "src": src, "tgt": tgt, "school": school,
            "source_text": source_text, "passage_ref": passage_ref,
        })

    print(f"Seeded {len(SEED_EDGES)} edges into graph '{GRAPH_NAME}'")


if __name__ == "__main__":
    seed()
