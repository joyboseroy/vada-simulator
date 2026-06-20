"""
run_debate.py

CLI entrypoint.

Usage:
    python run_debate.py --concept atman --school_a advaita --school_b buddhist --rounds 3
"""

import argparse
import json
from graph_state import run_debate
from render import render_html


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--concept", default="atman")
    parser.add_argument("--concept_a", default=None, help="Override concept for school_a (cross-concept debate)")
    parser.add_argument("--concept_b", default=None, help="Override concept for school_b (cross-concept debate)")
    parser.add_argument("--school_a", default="advaita")
    parser.add_argument("--school_b", default="buddhist")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--out", default="debate_output")
    args = parser.parse_args()

    final_state = run_debate(
        concept=args.concept,
        school_a=args.school_a,
        school_b=args.school_b,
        max_rounds=args.rounds,
        concept_a=args.concept_a,
        concept_b=args.concept_b,
    )

    json_path = f"{args.out}.json"
    with open(json_path, "w") as f:
        json.dump({
            "concept": final_state["concept"],
            "concept_a": final_state["concept_a"],
            "concept_b": final_state["concept_b"],
            "school_a": final_state["school_a"],
            "school_b": final_state["school_b"],
            "transcript": final_state["transcript"],
            "verdict": final_state.get("verdict", ""),
        }, f, indent=2)
    print(f"Transcript JSON written to {json_path}")

    html_path = f"{args.out}.html"
    render_html(final_state, html_path)
    print(f"Transcript HTML written to {html_path}")
    print(f"\n--- Moderator's verdict ---\n{final_state.get('verdict', '')}")


if __name__ == "__main__":
    main()

