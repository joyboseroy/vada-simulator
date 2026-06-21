"""
ask_darshana.py

A small, single-purpose RAG tool: ask a free-text question, get a single
grounded answer with real citations, no debate, no multiple schools
arguing. This is deliberately the simpler sibling of the vada simulator,
useful as a fast "can you build me a basic RAG system right now" demo,
distinct from the more elaborate multi-agent debate engine.

Usage:
    python3 ask_darshana.py "What does Advaita say about the self?"
    python3 ask_darshana.py "How does Dvaita view liberation?" --school dvaita
"""

import argparse
import os
import re
from groq import Groq
from retriever import connect, get_edges_for_concept, get_buddhist_edges_for_concept

MODEL_NAME = "llama-3.3-70b-versatile"

# Synonyms and common phrasings mapped to canonical concept names used in
# the graph. This fixes the original bug where a question like "what does
# Advaita say about the self?" found no match for "self" as a standalone
# word in KNOWN_CONCEPTS and silently fell back to an arbitrary default,
# returning whatever edges happened to be retrieved rather than the most
# relevant ones.
SYNONYM_MAP = {
    "self": "atman", "soul": "atman", "individual self": "atman",
    "ultimate reality": "brahman", "absolute": "brahman", "godhead": "brahman",
    "liberation": "moksha", "freedom": "moksha", "release": "moksha",
    "illusion": "maya", "cosmic illusion": "maya",
    "duty": "dharma", "righteousness": "dharma", "righteous action": "dharma",
    "suffering": "dukkha", "unsatisfactoriness": "dukkha",
    "action": "karma", "deeds": "karma",
    "rebirth": "samsara", "cycle of birth and death": "samsara", "reincarnation": "samsara",
    "no-self": "anatta", "not-self": "anatta",
    "consciousness": "vijnana", "awareness": "vijnana",
    "mind": "manas", "ego": "manas",
    "god": "isvara", "lord": "isvara", "supreme being": "isvara",
    "embodied soul": "jiva", "individual soul": "jiva",
}

KNOWN_CONCEPTS = [
    "atman", "brahman", "karma", "dharma", "moksha", "samsara", "maya",
    "jiva", "purusa", "pradhana", "prana", "manas", "dukkha", "anatta",
    "vijnana", "tanha", "nibbana", "rebirth", "arahant", "isvara",
]

# When a question is about a single "core identity" concept (e.g. atman)
# with no second concept named, these are the OTHER concepts worth
# prioritizing, since edges connecting two core/identity concepts (e.g.
# atman<->brahman, atman<->jiva, atman<->isvara) are far more relevant to
# an identity/nature question than high-volume but tangential edges (e.g.
# atman<->dharma, which exists in large numbers but rarely answers "what
# IS the self", just how the self relates to duty).
IDENTITY_RELATIONS = {"IS_IDENTICAL_TO", "IS_DISTINCT_FROM", "IS_QUALIFIED_ASPECT_OF"}
IDENTITY_ADJACENT_CONCEPTS = {"brahman", "jiva", "isvara", "atman", "purusa", "pradhana"}


def extract_concepts(question: str):
    q_lower = question.lower()
    found = []
    # check multi-word synonyms first (longest match wins to avoid partial overlaps)
    for phrase in sorted(SYNONYM_MAP.keys(), key=len, reverse=True):
        if phrase in q_lower and SYNONYM_MAP[phrase] not in found:
            found.append(SYNONYM_MAP[phrase])
    # then check direct concept-name matches
    for c in KNOWN_CONCEPTS:
        if c in q_lower and c not in found:
            found.append(c)
    return found or ["atman"]


def rank_edges_by_relevance(edges, concepts):
    """
    Sorts retrieved edges so the most relevant ones come first:
    1. Edges connecting two of the QUESTION's own concepts (if 2+ concepts found)
    2. Edges using an identity-defining relation type (IS_IDENTICAL_TO etc.)
       AND connecting to another identity-adjacent concept
    3. School-specific edges over general ones
    4. Everything else, by confidence
    """
    concept_set = set(concepts)

    def score(edge):
        s = 0
        if edge.source_concept in concept_set and edge.target_concept in concept_set:
            s += 100
        if edge.relation in IDENTITY_RELATIONS:
            other = edge.target_concept if edge.source_concept in concept_set else edge.source_concept
            if other in IDENTITY_ADJACENT_CONCEPTS:
                s += 50
        if edge.is_school_specific:
            s += 10
        if edge.confidence == "high":
            s += 1
        return -s  # negative for ascending sort = highest score first

    return sorted(edges, key=score)


def answer_question(question: str, school: str = None, top_k: int = 12):
    graph = connect()
    concepts = extract_concepts(question)
    candidate_pool_size = 40  # pull more than we need, then rank and trim

    all_edges = []
    for concept in concepts:
        if school and school.lower() == "buddhist":
            edges = get_buddhist_edges_for_concept(graph, concept, limit=candidate_pool_size)
        elif school:
            edges = get_edges_for_concept(graph, concept, school, limit=candidate_pool_size)
        else:
            edges = get_edges_for_concept(graph, concept, "advaita", limit=candidate_pool_size)
        all_edges.extend(edges)

    if not all_edges:
        print("No relevant graph edges found for this question. Try --school or rephrase.")
        return

    # de-duplicate by edge_id (a concept can appear in multiple extract_concepts() passes)
    seen_ids = set()
    deduped = []
    for e in all_edges:
        if e.edge_id not in seen_ids:
            seen_ids.add(e.edge_id)
            deduped.append(e)

    ranked = rank_edges_by_relevance(deduped, concepts)
    top_edges = ranked[:top_k]

    premises = "\n".join(e.as_premise() for e in top_edges)

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY not set. Showing raw retrieved evidence instead of a generated answer:\n")
        print(premises)
        return

    client = Groq(api_key=api_key)
    system_prompt = """You answer questions about Indian philosophy using ONLY the
premises provided. Every claim must end with a citation in the form (cite: edge_id),
using only edge_ids from the premises given. If the premises don't fully answer the
question, say so explicitly rather than filling gaps with outside knowledge. Stay close
to the literal evidence_quote text for each premise rather than inflating it into a
stronger claim than it actually supports. Answer in 3-5 sentences."""

    user_msg = f"Question: {question}\n\nAvailable premises:\n{premises}\n\nAnswer the question using only these premises."

    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_msg}],
        temperature=0.3,
    )
    answer = resp.choices[0].message.content

    valid_ids = {e.edge_id for e in top_edges}
    cited_ids = {m.strip() for m in re.findall(r"\(cite:\s*\[?([^\])]+)\]?\)", answer)}
    invalid = cited_ids - valid_ids
    if invalid:
        print(f"WARNING: answer cited edge_ids not in the retrieved set: {invalid}")
        print("(This means the model fabricated a citation; treat this answer with caution.)\n")

    print(f"\nQuestion: {question}\n")
    print(f"Answer:\n{answer}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question", help="Your question about Indian philosophy")
    parser.add_argument("--school", default=None, help="Restrict to a specific school (advaita, dvaita, buddhist, etc.)")
    args = parser.parse_args()

    answer_question(args.question, school=args.school)


if __name__ == "__main__":
    main()
