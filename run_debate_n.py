"""
run_debate_n.py

CLI entrypoint for N-agent (2+) debates.

Usage:
    python3 run_debate_n.py --concept atman --schools advaita dvaita vishishtadvaita --rounds 3
"""

import argparse
import json
from graph_state_n import run_debate_n
from render import render_html_n


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--concept", default="atman")
    parser.add_argument("--schools", nargs="+", required=True,
                         help="Two or more schools, e.g. --schools advaita dvaita vishishtadvaita")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--out", default="debate_output_n")
    args = parser.parse_args()

    final_state = run_debate_n(
        concept=args.concept,
        schools=args.schools,
        max_rounds=args.rounds,
    )

    json_path = f"{args.out}.json"
    with open(json_path, "w") as f:
        json.dump({
            "concept": final_state["concept"],
            "schools": final_state["schools"],
            "transcript": final_state["transcript"],
            "verdict": final_state.get("verdict", ""),
        }, f, indent=2)
    print(f"Transcript JSON written to {json_path}")

    html_path = f"{args.out}.html"
    render_html_n(final_state, html_path)
    print(f"Transcript HTML written to {html_path}")
    print(f"\n--- Moderator's verdict ---\n{final_state.get('verdict', '')}")


if __name__ == "__main__":
    main()
