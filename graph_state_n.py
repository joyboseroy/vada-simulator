"""
graph_state_n.py

Generalized N-agent version of the vada simulator. Supports 2+ schools
debating in round-robin order, reusing the same citation-validation and
moderator-verdict pattern as graph_state.py (the 2-agent original).

Use this when you want 3+ schools (e.g. advaita vs dvaita vs vishishtadvaita)
instead of the fixed two-agent graph_state.py.
"""

import os
import re
from typing import TypedDict, List, Dict
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from agents import build_agent_system_prompt, build_moderator_system_prompt
from retriever import connect, get_edges_for_concept, get_buddhist_edges_for_concept, Edge

from langgraph.graph import StateGraph, END

MODEL_NAME = "llama-3.3-70b-versatile"
MAX_RETRIES_PER_TURN = 2
CITE_PATTERN = re.compile(r"\(cite:\s*\[?([^\])]+)\]?\)")


class NAgentDebateState(TypedDict):
    concept: str
    schools: List[str]               # e.g. ["advaita", "dvaita", "vishishtadvaita"]
    edges_by_school: Dict[str, List[Edge]]
    transcript: List[dict]           # {speaker: school_name, text, accepted}
    round: int
    max_rounds: int
    verdict: str


def make_llm():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set. Run: export GROQ_API_KEY=your_key")
    return ChatGroq(model=MODEL_NAME, temperature=0.3, api_key=api_key)


def _speak(state: NAgentDebateState, school: str) -> NAgentDebateState:
    llm = make_llm()
    own_edges = state["edges_by_school"].get(school, [])
    valid_ids = {e.edge_id for e in own_edges}

    opponent_edges_by_school = {
        s: edges for s, edges in state["edges_by_school"].items() if s != school
    }
    system_prompt = build_agent_system_prompt(school, state["concept"], own_edges, opponent_edges_by_school)

    history_text = "\n".join(
        f"{t['speaker'].upper()}: {t['text']}" for t in state["transcript"]
    )
    user_msg = (
        f"Debate so far:\n{history_text}\n\nYour turn ({school.upper()}):"
        if history_text else f"Open the debate as school={school}."
    )

    text = ""
    cited_ids_valid = False
    for attempt in range(MAX_RETRIES_PER_TURN + 1):
        resp = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_msg)])
        text = resp.content
        cited_ids = {c.strip() for c in CITE_PATTERN.findall(text)}
        cited_ids_valid = bool(cited_ids) and cited_ids.issubset(valid_ids)
        if cited_ids_valid:
            break
        user_msg += (
            f"\n\n(Reminder: you may ONLY cite edge_ids from YOUR premises: "
            f"{sorted(valid_ids)}. You cited something else or nothing. Retry.)"
        )

    state["transcript"].append({"speaker": school, "text": text, "accepted": cited_ids_valid})
    return state


def round_tracker_node(state: NAgentDebateState) -> NAgentDebateState:
    state["round"] += 1
    return state


def moderator_verdict_node(state: NAgentDebateState) -> NAgentDebateState:
    llm = make_llm()
    system_prompt = build_moderator_system_prompt(state["concept"])
    transcript_text = "\n\n".join(
        f"{t['speaker'].upper()} ({'valid citation' if t['accepted'] else 'INVALID citation'}): {t['text']}"
        for t in state["transcript"]
    )
    schools_list = ", ".join(state["schools"])
    user_msg = (
        f"Full debate transcript on '{state['concept']}' between schools: {schools_list}.\n\n"
        f"{transcript_text}\n\n"
        f"Give your closing verdict covering convergence/contestation, core disagreements per "
        f"school, and any pairwise alignments you observe."
    )
    resp = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_msg)])
    state["verdict"] = resp.content
    return state


def should_continue(state: NAgentDebateState) -> str:
    if state["round"] >= state["max_rounds"]:
        return "verdict"
    return state["schools"][0]  # loop back to first speaker


def build_graph(schools: List[str]) -> StateGraph:
    g = StateGraph(NAgentDebateState)

    # one node per school, chained in round-robin order
    for school in schools:
        g.add_node(school, lambda state, s=school: _speak(state, s))
    g.add_node("round_tracker", round_tracker_node)
    g.add_node("verdict", moderator_verdict_node)

    g.set_entry_point(schools[0])
    for i in range(len(schools) - 1):
        g.add_edge(schools[i], schools[i + 1])
    g.add_edge(schools[-1], "round_tracker")

    routing = {s: s for s in schools}
    routing["verdict"] = "verdict"
    g.add_conditional_edges("round_tracker", should_continue, routing)
    g.add_edge("verdict", END)

    return g.compile()


def run_debate_n(concept: str, schools: List[str], max_rounds: int = 3) -> NAgentDebateState:
    if len(schools) < 2:
        raise ValueError("Need at least 2 schools for a debate.")

    graph_db = connect()
    edges_by_school = {}
    for school in schools:
        if school.lower() == "buddhist":
            edges_by_school[school] = get_buddhist_edges_for_concept(graph_db, concept)
        else:
            edges_by_school[school] = get_edges_for_concept(graph_db, concept, school)

    state: NAgentDebateState = {
        "concept": concept,
        "schools": schools,
        "edges_by_school": edges_by_school,
        "transcript": [],
        "round": 0,
        "max_rounds": max_rounds,
        "verdict": "",
    }

    app = build_graph(schools)
    final_state = app.invoke(state)
    return final_state
