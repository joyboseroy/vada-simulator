# Vada Simulator

Multi-agent philosophical debate engine, grounded in the [darshana-graph](https://huggingface.co/datasets/joyboseroy/darshana-graph)
knowledge graph of Indian philosophy. Agents representing different schools
of thought (Advaita Vedanta, Dvaita Vedanta, Buddhism, etc.) debate
philosophical concepts — but every claim they make must cite a real edge
from the graph, sourced back to an actual passage in a real philosophical
text. Agents cannot invent arguments or fabricate citations; if they have
no textual evidence for a point, they're required to say so.

This is a small companion project to [darshana-graph](https://github.com/joyboseroy/darshana-graph)
([dataset on HuggingFace](https://huggingface.co/datasets/joyboseroy/darshana-graph),
arXiv:2606.18222) — a demonstration that a text-grounded philosophical
knowledge graph can do more than support retrieval: it can power a
citation-disciplined multi-agent reasoning system (a *vada*, the classical
Sanskrit term for a formal philosophical debate).

**Notable finding:** running the same two schools (Buddhism vs Advaita)
across three different concept framings of the self/no-self question
produced three different debate outcomes — see [FINDINGS.md](FINDINGS.md)
(or the [Medium write-up](https://medium.com/@joyboseroy/what-2500-years-of-indian-philosophy-taught-me-about-asking-ai-the-right-question-e5fa6e0a6c8e)
for a non-technical version) for the full writeup, sample transcripts, and
what it suggests about tagging-coverage bias in LLM-extracted knowledge
graphs.

## How it works

1. A **retriever** pulls all graph edges touching a chosen concept for a
   chosen school, from a FalkorDB instance loaded with darshana-graph.
2. Each **agent** is given only its own school's edges as citable evidence,
   plus visibility (not citation rights) into the opponent's edges, so it
   can respond to them.
3. Every claim an agent makes must end in `(cite: edge_id)`. A citation is
   validated against the agent's real retrieved edges — fabricated or
   borrowed citations are rejected and the agent is asked to retry.
4. After N rounds, a **moderator** agent (not a referee scoring each turn,
   but a closing-statement judge) reads the full transcript and gives a
   verdict: contested, converged, or one side better supported, based only
   on what was actually cited.
5. The transcript renders to a styled HTML page, with citations that are
   shared between opposing schools visually flagged (a known dataset
   limitation — see below).

Supports both 2-school and N-school (3+) debates.

## Why citation-grounding matters here

This isn't a chatbot wrapper. The graph's `school` attribution is
imperfect (~70% of edges are tagged `school="general"` rather than a
specific tradition — see the
[dataset card](https://huggingface.co/datasets/joyboseroy/darshana-graph#known-limitations)).
Agents are instructed to prefer school-specific citations and flag when
they're relying on the noisier general bucket, so the debate's honesty
about its own evidence quality is part of the design, not an afterthought.

Buddhism in this dataset has **no populated school tag at all** (only a
curated 3,900-record subset of the Pali Canon was tagged into the graph).
To let Buddhism debate at all, this tool filters by *source text*
(Samyutta Nikaya, Dhammapada, Udana, Itivuttaka, Khuddakapatha, Sutta
Nipata) instead of relying on a school field that doesn't exist for this
tradition — see `retriever.py`'s `get_buddhist_edges_for_concept()`.

## Additional tools

Beyond the debate engine itself, this repo includes a few smaller tools
that reuse the same retrieval layer:

```bash
# Find concept pairs where schools assert CONTRADICTORY relations
python3 contradiction_finder.py --top 20
python3 contradiction_finder.py --concept atman

# Ask a single question, get one grounded answer (not a debate)
python3 ask_darshana.py "What does Advaita say about the self?" --school advaita
python3 ask_darshana.py "What causes dukkha?" --school buddhist

# Diagnostics used while building/debugging this project
python3 check_edge_fidelity.py edge_021445       # inspect the real evidence_quote behind a citation
python3 check_commentator_granularity.py          # check what attribution fields actually exist
python3 inspect_sources.py                        # list real source_text values in the graph
```

`ask_darshana.py` is the simpler sibling of the debate engine: single
grounded answer, not a multi-agent debate, useful as a quick "build me a
basic RAG system" demo. It ranks retrieved evidence by relevance (does the
edge connect two concepts you actually asked about, is it an
identity-defining relation type, is it school-specific) rather than
returning edges in arbitrary retrieval order.

## Setup (no Docker required)

This project runs on [FalkorDBLite](https://pypi.org/project/falkordblite/),
an embedded, file-based FalkorDB with no Docker dependency. Data persists
permanently on disk and survives reboots.

```bash
sudo apt install -y python3-dev build-essential
pip install falkordblite "redis<8.0" --break-system-packages

python3 ingest_darshana_graph.py    # one-time: downloads + loads the real dataset
python3 retriever.py                 # smoke test
```

(If you prefer Docker instead, `retriever.py`'s `connect(use_docker=True)`
still supports the original host/port path.)

## Setup (original, Docker-based)

### 1. Install

```bash
# FalkorDB
docker run -p 6379:6379 -p 3000:3000 -d --name falkordb falkordb/falkordb

# Python deps
python3 -m venv venv && source venv/bin/activate
pip install langgraph langchain-groq falkordb redis huggingface_hub

# Groq API key (free tier available at console.groq.com)
export GROQ_API_KEY=gsk_your_key_here
```

### 2. Load the real darshana-graph data

```bash
python3 ingest_darshana_graph.py
```

Downloads `darshana_graph.jsonl` (28,322 edges) directly from
[joyboseroy/darshana-graph](https://huggingface.co/datasets/joyboseroy/darshana-graph)
on HuggingFace and loads it into FalkorDB. Doesn't download the raw
125k-record text corpus — only the typed graph edges are needed.

Alternatively, for a quick offline test with no download, use:

```bash
python3 seed_demo_graph.py
```

This loads a tiny hand-written graph (6 edges) so you can verify the
pipeline works before pulling the full dataset.

### 3. Explore what's actually in the graph

Before picking a debate pairing, check what's well-populated:

```bash
python3 explore_graph.py                    # edge counts per school
python3 explore_graph.py --school advaita    # top concepts for a school
python3 explore_graph.py --school buddhist   # top concepts for Buddhism (source-filtered)
```

If you need to debug schema/field names directly:

```bash
python3 inspect_sources.py    # lists all distinct source_text values in the graph
python3 retriever.py          # smoke test on a single concept/school
```

## Usage

### Two-school debate

```bash
python3 run_debate.py --concept atman --school_a advaita --school_b dvaita --rounds 4
```

For a **cross-concept debate** (each side argues from its own native term
instead of being forced onto a foreign concept — recommended when debating
Buddhism, since it has no positive doctrine of e.g. "atman" to cite for):

```bash
python3 run_debate.py --concept_a anatta --concept_b atman \
  --school_a buddhist --school_b advaita --rounds 3
```

### N-school debate (3+)

```bash
python3 run_debate_n.py --concept atman --schools advaita dvaita vishishtadvaita --rounds 3
```

Both produce `<out>.json` (raw transcript + verdict) and `<out>.html`
(styled, citation-highlighted transcript) in the working directory.

## Files

| File | Purpose |
|---|---|
| `ingest_darshana_graph.py` | Downloads darshana-graph from HuggingFace, loads into FalkorDB |
| `seed_demo_graph.py` | Tiny offline test graph, no download needed |
| `retriever.py` | Cypher queries — pulls edges per concept/school, including Buddhist source-text filtering |
| `agents.py` | System prompt construction per school, citation rules, moderator prompt |
| `graph_state.py` | LangGraph state machine for 2-agent debates |
| `graph_state_n.py` | Generalized state machine for N-agent (3+) debates |
| `run_debate.py` | CLI entrypoint, 2-agent |
| `run_debate_n.py` | CLI entrypoint, N-agent |
| `render.py` | Transcript → styled HTML, shared-citation flagging |
| `contradiction_finder.py` | Finds concept pairs with contradictory relations across schools |
| `ask_darshana.py` | Single-answer grounded RAG tool (simpler sibling of the debate engine) |
| `check_edge_fidelity.py` | Inspects the real evidence_quote behind any citation |
| `check_commentator_granularity.py` | Diagnostic for what attribution fields exist in the graph |
| `explore_graph.py` | Inspect edge counts per school/concept before picking a debate pairing |
| `inspect_sources.py` | Diagnostic — lists real `source_text` values in the graph |
| `FINDINGS.md` | Write-up of the Buddhism-vs-Advaita concept-framing experiment |
| `debate_*.html` / `.json` | Example debate transcripts (see Example outputs above) |

## Known limitations (inherited from darshana-graph)

- No human expert review of the underlying graph; estimated 70-85%
  extraction precision (see dataset card).
- ~70% of edges fall back to `school="general"` rather than a specific
  tradition — agents are nudged to prefer school-specific evidence but
  will use general edges when nothing more specific is available.
- Buddhism's school-specific tagging is essentially absent; this tool
  works around it via source-text filtering, which is a reasonable but
  imperfect substitute for true school attribution.
- `IS_QUALIFIED_ASPECT_OF` is over-represented in the source data relative
  to other relation types, which can make debates feel repetitive if the
  same handful of high-confidence edges keep getting cited.
- **Citation-validity is not citation-fidelity.** Every citation in a
  debate transcript references a real edge with a real evidence_quote
  (validity is enforced programmatically), but the agent's paraphrase of
  what that quote means can still drift from what the quote actually
  supports. A real example caught during review: an Advaita agent cited a
  passage meaning "the self is untouched by virtue and vice" but phrased
  it as "the self is distinct from karma, which exists separately,"
  inflating a narrower claim into a stronger, actually incorrect
  metaphysical one (Advaita's non-dual position holds nothing exists
  apart from the self/Brahman at all). `agents.py` now includes an
  explicit prompt guardrail against this specific failure mode, but no
  automated check verifies content fidelity the way citation-validity is
  verified. Treat any specific debate claim as worth checking against the
  real evidence_quote (`check_edge_fidelity.py`) before citing it
  elsewhere as established philosophical fact.

## Example outputs

This repo includes real transcripts from the experiment described in
[FINDINGS.md](FINDINGS.md), so you can see actual output without running
anything yourself:

- [`debate_anatta_vs_atman.html`](debate_anatta_vs_atman.html) — Buddhism
  (arguing from `anatta`) vs Advaita Vedanta (arguing from `atman`), the
  cross-concept self/no-self debate
- [`debate_atman.html`](debate_atman.html) — same two schools, both forced
  onto the single node `atman`
- [`debate_dukkha.html`](debate_dukkha.html) — same two schools debating
  suffering/`dukkha`
- [`debate_output.html`](debate_output.html) — Advaita vs Dvaita on `atman`
- [`debate_output_n.html`](debate_output_n.html) — 3-school debate
  (Advaita vs Dvaita vs Vishishtadvaita) on `atman`

Each `.html` has a matching `.json` with the raw transcript and verdict.
Open any `.html` file directly in a browser — no server needed.

## Citation

If you use this tool, please cite the underlying dataset:

> Bose, J. *Darshana Graph: A Text-Grounded Knowledge Graph of Indian
> Philosophy.* arXiv:2606.18222 (2026).
> Code: https://github.com/joyboseroy/darshana-graph ·
> Data: https://huggingface.co/datasets/joyboseroy/darshana-graph

## License

Code in this repository: MIT (see [LICENSE](LICENSE)). Underlying graph
data retains darshana-graph's CC-BY-4.0 license; source texts retain their
original licenses as documented in the
[dataset card](https://huggingface.co/datasets/joyboseroy/darshana-graph#license).
