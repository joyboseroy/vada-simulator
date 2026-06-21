"""
retriever.py

Pulls all graph edges touching a given concept for a given school/tradition
from FalkorDB, loaded via ingest_darshana_graph.py from the real
joyboseroy/darshana-graph dataset.

Real schema reference (https://huggingface.co/datasets/joyboseroy/darshana-graph):
  concept_a, concept_b, relation, school, confidence, evidence_quote,
  source_record_id, source_text, edge_id

Relation vocabulary (closed set): IS_IDENTICAL_TO, IS_DISTINCT_FROM,
IS_QUALIFIED_ASPECT_OF, IS_SIMULTANEOUSLY_ONE_AND_DIFFERENT, PRESUPPOSES,
SUBLATES, LEADS_TO, OBSTRUCTS, IS_CAUSE_OF, IS_MANIFESTATION_OF, RECONCILES,
CONTRADICTS_IN_SCHOOL, DEFINED_AS.

Known dataset limitation: ~70% of edges are tagged school="general" rather
than a specific school (an artifact of the 8B tagging model, not the source
text). get_edges_for_concept() falls back to "general" automatically so you
still get usable results, but specific-school edges (advaita, dvaita,
vishishtadvaita, achintya_bhedabheda -- ~7,600 edges total) are the more
reliable subset for genuine cross-school debate.
"""

from dataclasses import dataclass
from typing import List
import os


GRAPH_NAME = "darshana_graph"

# Persistent file location for FalkorDBLite (no Docker, survives reboots).
# Change this if you want the data file somewhere else.
FALKORDBLITE_PATH = os.path.join(os.path.expanduser("~"), ".vada-simulator", "falkordb.db")


@dataclass
class Edge:
    edge_id: str
    relation: str
    source_concept: str
    target_concept: str
    school: str
    confidence: str
    evidence_quote: str
    source_record_id: str
    source_text: str

    @property
    def is_school_specific(self) -> bool:
        """True if this edge is tagged with the actual requested school, not the
        'general' fallback. Use this to distinguish genuinely school-specific
        evidence from the dataset's ~70% general-attribution gap."""
        return self.school != "general"

    def as_premise(self) -> str:
        """Render as a short citable premise string for use in agent prompts."""
        tag = "SCHOOL-SPECIFIC" if self.is_school_specific else "GENERAL (not school-attributed)"
        return (
            f"[{self.edge_id}] ({tag}) {self.source_concept} --{self.relation}--> "
            f"{self.target_concept} (school={self.school}, confidence={self.confidence}, "
            f"evidence: \"{self.evidence_quote}\", source={self.source_text}/{self.source_record_id})"
        )


def connect(host: str = None, port: int = None, use_docker: bool = False):
    """
    By default, connects via FalkorDBLite: an embedded, file-based FalkorDB
    that requires no Docker and persists data permanently at
    FALKORDBLITE_PATH. This is the recommended path for a personal laptop
    setup with no Docker dependency.

    Pass use_docker=True (and optionally host/port) to instead connect to a
    Docker-based FalkorDB instance the old way, if you still have one
    running and want to use it.
    """
    if use_docker:
        from falkordb import FalkorDB as DockerFalkorDB
        db = DockerFalkorDB(host=host or "localhost", port=port or 6379)
        return db.select_graph(GRAPH_NAME)

    from redislite.falkordb_client import FalkorDB as LiteFalkorDB
    os.makedirs(os.path.dirname(FALKORDBLITE_PATH), exist_ok=True)
    db = LiteFalkorDB(FALKORDBLITE_PATH)
    return db.select_graph(GRAPH_NAME)


# Buddhism has essentially no populated `school` tag in this dataset (the Buddhist
# subset of the corpus is mostly attributed school="general" -- see dataset card
# known limitations). To debate "Buddhist" as a position, we instead filter by
# SOURCE TEXT, pulling only edges whose source_text comes from the Pali Canon,
# rather than relying on a school field that doesn't exist for this tradition.
BUDDHIST_SOURCE_TEXTS = [
    "sn_nikaya", "kn_udana_nikaya", "kn_itivuttaka_nikaya",
    "kn_dhammapada_nikaya", "kn_khuddakapatha_nikaya", "kn_sutta_nipata_nikaya",
]


def get_buddhist_edges_for_concept(graph, concept: str, limit: int = 30) -> List[Edge]:
    """
    Special-case retrieval for the Buddhist 'school': since the dataset doesn't
    populate a school tag for Buddhism, this filters by source_text belonging to
    known Pali Canon texts instead. All matched edges will show as school=general
    in the rendered premise (because that's the dataset's literal field value),
    but they are still genuinely Buddhist-sourced material, not arbitrary general
    edges from other traditions.
    """
    query = """
    MATCH (a:Concept)-[r:RELATION]->(b:Concept)
    WHERE (toLower(a.name) = toLower($concept) OR toLower(b.name) = toLower($concept))
      AND r.source_text IN $sources
    RETURN r.edge_id AS edge_id, r.relation AS relation,
           a.name AS source_concept, b.name AS target_concept,
           r.school AS school, r.confidence AS confidence,
           r.evidence_quote AS evidence_quote,
           r.source_record_id AS source_record_id, r.source_text AS source_text
    LIMIT $limit
    """
    result = graph.query(query, {
        "concept": concept, "sources": BUDDHIST_SOURCE_TEXTS, "limit": limit,
    })

    edges = []
    for row in result.result_set:
        edges.append(Edge(
            edge_id=row[0],
            relation=row[1],
            source_concept=row[2],
            target_concept=row[3],
            school="buddhist (pali canon, source-filtered)",  # override for clarity in prompts
            confidence=row[5] or "unknown",
            evidence_quote=row[6] or "",
            source_record_id=row[7] or "unknown",
            source_text=row[8] or "unknown",
        ))
    return edges


def get_edges_for_concept(graph, concept: str, school: str, limit: int = 30,
                           min_confidence: str = None) -> List[Edge]:
    """
    Returns edges touching `concept` where the edge's school matches `school`
    (falls back to school="general" per the dataset's known attribution gap).

    min_confidence: if set to "high", only returns high-confidence edges --
    useful since this dataset has no human review (estimated 70-85% precision).
    """
    query = """
    MATCH (a:Concept)-[r:RELATION]->(b:Concept)
    WHERE (toLower(a.name) = toLower($concept) OR toLower(b.name) = toLower($concept))
      AND toLower(r.school) IN [toLower($school), 'general']
      AND ($min_confidence IS NULL OR r.confidence = $min_confidence)
    RETURN r.edge_id AS edge_id, r.relation AS relation,
           a.name AS source_concept, b.name AS target_concept,
           r.school AS school, r.confidence AS confidence,
           r.evidence_quote AS evidence_quote,
           r.source_record_id AS source_record_id, r.source_text AS source_text
    ORDER BY CASE WHEN toLower(r.school) = toLower($school) THEN 0 ELSE 1 END
    LIMIT $limit
    """
    result = graph.query(query, {
        "concept": concept, "school": school, "limit": limit,
        "min_confidence": min_confidence,
    })

    edges = []
    for row in result.result_set:
        edges.append(Edge(
            edge_id=row[0],
            relation=row[1],
            source_concept=row[2],
            target_concept=row[3],
            school=row[4] or "general",
            confidence=row[5] or "unknown",
            evidence_quote=row[6] or "",
            source_record_id=row[7] or "unknown",
            source_text=row[8] or "unknown",
        ))
    return edges


if __name__ == "__main__":
    # quick smoke test
    g = connect()
    edges = get_edges_for_concept(g, concept="atman", school="advaita")
    print(f"Found {len(edges)} edges")
    for e in edges[:5]:
        print(e.as_premise())
