"""
ingest_darshana_graph.py

Downloads darshana_graph.jsonl from the real HuggingFace dataset
(joyboseroy/darshana-graph) and loads it into FalkorDB, replacing the need
for seed_demo_graph.py.

Real schema (from https://huggingface.co/datasets/joyboseroy/darshana-graph):
{
  "edge_id": "edge_000123",
  "concept_a": "atman",
  "concept_b": "brahman",
  "relation": "IS_IDENTICAL_TO",
  "school": "advaita",
  "confidence": "high",
  "evidence_quote": "the Self is verily Brahman",
  "source_record_id": "bg_2_20",
  "source_text": "bhagavad_gita",
  "tagged_from_file": "bg.jsonl"
}

Note: per the dataset card, only the graph file (28,322 edges) is needed for
this tool -- darshana_corpus.jsonl (125,040 records, the raw text corpus) is
NOT required since we only debate over the typed concept relationships, not
the raw passages. Skipping it saves a large download.
"""

import json
import os
from huggingface_hub import hf_hub_download
from falkordb import FalkorDB

GRAPH_NAME = "darshana_graph"
REPO_ID = "joyboseroy/darshana-graph"
GRAPH_FILE = "darshana_graph.jsonl"

BATCH_SIZE = 500  # edges per Cypher batch, keeps memory/latency reasonable


def download_graph_file() -> str:
    print(f"Downloading {GRAPH_FILE} from {REPO_ID} (this may take a moment)...")
    path = hf_hub_download(repo_id=REPO_ID, filename=GRAPH_FILE, repo_type="dataset")
    print(f"Downloaded to {path}")
    return path


def load_edges(jsonl_path: str):
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph(GRAPH_NAME)

    # WARNING: this clears any existing data in this graph name. Comment out
    # if you want to append instead of replace.
    graph.query("MATCH (n) DETACH DELETE n")

    batch = []
    total = 0
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            batch.append(row)
            if len(batch) >= BATCH_SIZE:
                _insert_batch(graph, batch)
                total += len(batch)
                print(f"  ...inserted {total} edges")
                batch = []

    if batch:
        _insert_batch(graph, batch)
        total += len(batch)

    print(f"Done. Inserted {total} edges into graph '{GRAPH_NAME}'.")


def _insert_batch(graph, rows):
    query = """
    UNWIND $rows AS row
    MERGE (a:Concept {name: toLower(row.concept_a)})
    MERGE (b:Concept {name: toLower(row.concept_b)})
    CREATE (a)-[r:RELATION {
        edge_id: row.edge_id,
        relation: row.relation,
        school: row.school,
        confidence: row.confidence,
        evidence_quote: row.evidence_quote,
        source_record_id: row.source_record_id,
        source_text: row.source_text
    }]->(b)
    """
    graph.query(query, {"rows": rows})


if __name__ == "__main__":
    path = download_graph_file()
    load_edges(path)
