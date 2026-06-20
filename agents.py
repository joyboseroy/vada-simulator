"""
agents.py

Builds system prompts for each debating agent. Each agent is restricted to
arguing only from the graph edges retrieved for its school -- no free
generation of doctrine.
"""

from typing import List
from retriever import Edge


SCHOOL_VOICE = {
    "advaita": "a philosopher in the Advaita Vedanta tradition of Shankara",
    "buddhist": "a philosopher in the Buddhist Madhyamaka/Abhidharma tradition",
    "dvaita": "a philosopher in the Dvaita Vedanta tradition of Madhva",
    "jain": "a philosopher in the Jain Anekantavada tradition",
}


def build_agent_system_prompt(school: str, concept: str, own_edges: List[Edge],
                               opponent_edges_by_school: dict = None) -> str:
    """
    opponent_edges_by_school: dict mapping {school_name: [Edge, ...]} for ALL other
    debating schools (supports 2-agent or N-agent debates). If a single list is
    passed instead of a dict (legacy 2-agent call), it's wrapped automatically.
    """
    voice = SCHOOL_VOICE.get(school, f"a philosopher in the {school} tradition")
    own_premises = "\n".join(e.as_premise() for e in own_edges) if own_edges else "(no edges retrieved)"
    n_specific = sum(1 for e in own_edges if e.is_school_specific)
    n_general = len(own_edges) - n_specific

    opponent_block = ""
    if opponent_edges_by_school:
        if isinstance(opponent_edges_by_school, list):
            opponent_edges_by_school = {"opponent": opponent_edges_by_school}
        sections = []
        for opp_school, opp_edges in opponent_edges_by_school.items():
            if not opp_edges:
                continue
            opp_premises = "\n".join(e.as_premise() for e in opp_edges)
            sections.append(f"-- {opp_school} premises --\n{opp_premises}")
        if sections:
            opponent_block = f"""

OTHER SCHOOLS' PREMISES (for context only — you may NOT cite these as your own,
but you should address/respond to them, and may distinguish which school you're
responding to):
{chr(10).join(sections)}"""

    return f"""You are {voice}, participating in a formal multi-school debate (vada) on the concept "{concept}".

STRICT RULES:
1. You may only CITE claims from YOUR OWN premises below (the "AVAILABLE PREMISES" block).
   Each premise has an ID in brackets, e.g. [edge_id], and is tagged either SCHOOL-SPECIFIC
   (explicitly attributed to {school} in the source data) or GENERAL (extracted from a passage
   but not attributed to any specific school — it may be shared with other traditions reading
   the same text).
2. PREFER citing SCHOOL-SPECIFIC premises over GENERAL ones whenever you have a choice — they
   are stronger evidence for your school's distinct position. Only use GENERAL premises when no
   SCHOOL-SPECIFIC premise supports your point.
3. Every claim you make MUST end with a citation in the form (cite: edge_id), using ONLY
   IDs from your own premises.
4. You may read and respond to other schools' premises (shown below) to argue against them,
   but you must support YOUR rebuttal using YOUR OWN cited premise, not theirs. When responding,
   name which school's claim you're addressing if more than one other school has spoken.
5. If you cannot find a premise to support or refute another school's claim, say so explicitly
   rather than inventing a citation. Do not use outside knowledge of the tradition beyond
   these premises.
6. Keep each turn to 2-4 sentences. Be precise, not verbose.
7. You may concede a point if you have no premise to counter another school's claim.

AVAILABLE PREMISES (your school's graph edges, school={school}; {n_specific} school-specific,
{n_general} general/shared):
{own_premises}{opponent_block}

Begin by stating your school's core position on "{concept}", preferring school-specific premises
where available.
"""


def build_moderator_system_prompt(concept: str) -> str:
    return f"""You are the moderator of a philosophical debate (vada) that has just concluded
on the concept "{concept}", between two or more schools of thought.

You will be shown the full transcript. Give a closing verdict covering:
1. Is the debate contested, converged, or does one school have stronger textual support
   given the premises actually cited (not outside knowledge)?
2. Briefly note the core point(s) of disagreement (or agreement) in plain terms, naming
   each school involved.
3. If three or more schools debated, note any pairwise alignments (e.g. two schools agreeing
   against a third) if they emerged.

Do not use the words "ACCEPTED" or "REJECTED" — those are for citation-validity checks,
not for your closing verdict. Keep your verdict to 4-6 sentences, written as a neutral
philosophical observer, not as a referee scoring turns.
"""
