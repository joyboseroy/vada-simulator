"""
graph_state.py

LangGraph state machine for the multi-agent vada (debate).

Flow per round:
    Agent A speaks -> Moderator checks citation -> (retry if rejected)
    Agent B speaks -> Moderator checks citation -> (retry if rejected)
    repeat for N rounds
"""

import os
import re
from typing import TypedDict, List, Literal
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from agents import build_agent_system_prompt, build_moderator_system_prompt
from retriever import connect, get_edges_for_concept, get_buddhist_edges_for_concept, Edge

from langgraph.graph import StateGraph, END

# Set GROQ_API_KEY in your environment: export GROQ_API_KEY=gsk_...
MODEL_NAME = "llama-3.3-70b-versatile"  # good cost/quality balance; swap to llama-3.1-8b-instant for cheaper/faster
MAX_RETRIES_PER_TURN = 2
CITE_PATTERN = re.compile(r"\(cite:\s*\[?([^\])]+)\]?\)")


class DebateState(TypedDict):
    concept: str
    concept_a: str
    concept_b: str
    school_a: str
    school_b: str
    edges_a: List[Edge]
    edges_b: List[Edge]
    transcript: List[dict]   # list of {speaker, text, accepted}
    round: int
    max_rounds: int
    last_speaker: Literal["a", "b", "none"]
    verdict: str


def make_llm():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set. Run: export GROQ_API_KEY=your_key")
    return ChatGroq(model=MODEL_NAME, temperature=0.3, api_key=api_key)


def _speak(state: DebateState, speaker: Literal["a", "b"]) -> DebateState:
    llm = make_llm()
    school = state["school_a"] if speaker == "a" else state["school_b"]
    own_concept = state["concept_a"] if speaker == "a" else state["concept_b"]
    own_edges = state["edges_a"] if speaker == "a" else state["edges_b"]
    opponent_edges = state["edges_b"] if speaker == "a" else state["edges_a"]
    valid_ids = {e.edge_id for e in own_edges}

    system_prompt = build_agent_system_prompt(school, own_concept, own_edges, opponent_edges)

    history_text = "\n".join(
        f"{t['speaker'].upper()}: {t['text']}" for t in state["transcript"]
    )
    user_msg = (
        f"Debate so far:\n{history_text}\n\nYour turn ({speaker.upper()}, school={school}, "
        f"your concept={own_concept}):"
        if history_text else f"Open the debate as school={school}, arguing from the concept '{own_concept}'."
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

    state["transcript"].append({"speaker": speaker, "text": text, "accepted": cited_ids_valid})
    state["last_speaker"] = speaker
    return state


def agent_a_node(state: DebateState) -> DebateState:
    return _speak(state, "a")


def agent_b_node(state: DebateState) -> DebateState:
    return _speak(state, "b")


def round_tracker_node(state: DebateState) -> DebateState:
    state["round"] += 1
    return state


def moderator_verdict_node(state: DebateState) -> DebateState:
    llm = make_llm()
    concept_label = (
        state["concept"] if state["concept_a"] == state["concept_b"]
        else f"{state['concept_a']} ({state['school_a']}) vs {state['concept_b']} ({state['school_b']})"
    )
    system_prompt = build_moderator_system_prompt(concept_label)
    transcript_text = "\n\n".join(
        f"{t['speaker'].upper()} ({'valid citation' if t['accepted'] else 'INVALID citation'}): {t['text']}"
        for t in state["transcript"]
    )
    user_msg = (
        f"Full debate transcript on '{concept_label}' between "
        f"{state['school_a']} (A) and {state['school_b']} (B):\n\n{transcript_text}\n\n"
        f"Give your closing verdict: is this contested, converged, or does one side have "
        f"stronger textual support given the premises actually cited? 3-4 sentences max."
    )
    resp = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_msg)])
    state["verdict"] = resp.content
    return state


def should_continue(state: DebateState) -> str:
    if state["round"] >= state["max_rounds"]:
        return "verdict"
    return "agent_a"


def build_graph() -> StateGraph:
    g = StateGraph(DebateState)
    g.add_node("agent_a", agent_a_node)
    g.add_node("agent_b", agent_b_node)
    g.add_node("round_tracker", round_tracker_node)
    g.add_node("verdict", moderator_verdict_node)

    g.set_entry_point("agent_a")
    g.add_edge("agent_a", "agent_b")
    g.add_edge("agent_b", "round_tracker")
    g.add_conditional_edges("round_tracker", should_continue, {"agent_a": "agent_a", "verdict": "verdict"})
    g.add_edge("verdict", END)

    return g.compile()


def run_debate(concept: str, school_a: str, school_b: str, max_rounds: int = 3,
               concept_a: str = None, concept_b: str = None) -> DebateState:
    """
    concept: the displayed/shared concept label (and default for both sides if
    concept_a/concept_b aren't given).
    concept_a / concept_b: override to let each school argue from a DIFFERENT
    graph node -- e.g. school_a="buddhist", concept_a="anatta" vs
    school_b="advaita", concept_b="atman", for a true mirror-concept debate.
    """
    graph = connect()

    def _get_edges(school, c):
        if school.lower() == "buddhist":
            return get_buddhist_edges_for_concept(graph, c)
        return get_edges_for_concept(graph, c, school)

    concept_a = concept_a or concept
    concept_b = concept_b or concept
    edges_a = _get_edges(school_a, concept_a)
    edges_b = _get_edges(school_b, concept_b)

    state: DebateState = {
        "concept": concept,
        "concept_a": concept_a,
        "concept_b": concept_b,
        "school_a": school_a,
        "school_b": school_b,
        "edges_a": edges_a,
        "edges_b": edges_b,
        "transcript": [],
        "round": 0,
        "max_rounds": max_rounds,
        "last_speaker": "none",
        "verdict": "",
    }

    app = build_graph()
    final_state = app.invoke(state)
    return final_state
