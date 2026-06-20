"""
render.py

Renders a debate transcript (DebateState) to a simple, readable HTML page.
"""

import re
from typing import Dict

CITE_PATTERN = re.compile(r"\(cite:\s*\[?([^\])]+)\]?\)")

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Vada: {concept}</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 720px; margin: 40px auto; background: #fdfaf5; color: #2a2a2a; }}
  h1 {{ font-size: 1.4em; border-bottom: 2px solid #7a1f1f; padding-bottom: 8px; }}
  .turn {{ margin: 18px 0; padding: 14px 18px; border-radius: 6px; }}
  .a {{ background: #f1e6e6; border-left: 4px solid #7a1f1f; }}
  .b {{ background: #e6ecf1; border-left: 4px solid #1f3f7a; }}
  .speaker {{ font-weight: bold; text-transform: uppercase; font-size: 0.85em; opacity: 0.7; }}
  .rejected {{ opacity: 0.5; font-style: italic; }}
  .cite {{ color: #7a1f1f; font-weight: bold; }}
  .cite.shared {{ color: #b8860b; border-bottom: 1px dotted #b8860b; }}
  .verdict {{ margin-top: 28px; padding: 16px 20px; background: #fff3d6; border-left: 4px solid #b8860b; border-radius: 6px; }}
  .verdict .label {{ font-weight: bold; text-transform: uppercase; font-size: 0.85em; color: #8a6500; }}
  .legend {{ font-size: 0.8em; opacity: 0.7; margin-bottom: 16px; }}
  .legend .cite {{ margin-right: 12px; }}
</style>
</head>
<body>
<h1>Vada: {school_a} vs {school_b} on "{concept}"</h1>
<div class="legend">
  <span class="cite">[cite: X]</span> = school-specific or unique citation &nbsp;&nbsp;
  <span class="cite shared">[cite: X]</span> = edge also cited by the opponent (dataset's "general"
  school-attribution gap — see README known limitations)
</div>
{turns}
<div class="verdict">
  <div class="label">Moderator's verdict</div>
  <div>{verdict}</div>
</div>
</body>
</html>
"""


def _format_text(text: str, shared_ids: set) -> str:
    def replacer(match):
        raw_id = match.group(1).strip()
        css = "cite shared" if raw_id in shared_ids else "cite"
        return f'<span class="{css}">[cite: {raw_id}]</span>'
    return CITE_PATTERN.sub(replacer, text)


NAGENT_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Vada: {concept}</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 720px; margin: 40px auto; background: #fdfaf5; color: #2a2a2a; }}
  h1 {{ font-size: 1.4em; border-bottom: 2px solid #7a1f1f; padding-bottom: 8px; }}
  .turn {{ margin: 18px 0; padding: 14px 18px; border-radius: 6px; }}
  .speaker {{ font-weight: bold; text-transform: uppercase; font-size: 0.85em; opacity: 0.7; }}
  .rejected {{ opacity: 0.5; font-style: italic; }}
  .cite {{ color: #7a1f1f; font-weight: bold; }}
  .cite.shared {{ color: #b8860b; border-bottom: 1px dotted #b8860b; }}
  .verdict {{ margin-top: 28px; padding: 16px 20px; background: #fff3d6; border-left: 4px solid #b8860b; border-radius: 6px; }}
  .verdict .label {{ font-weight: bold; text-transform: uppercase; font-size: 0.85em; color: #8a6500; }}
  .legend {{ font-size: 0.8em; opacity: 0.7; margin-bottom: 16px; }}
  .legend .cite {{ margin-right: 12px; }}
</style>
</head>
<body>
<h1>Vada: {schools_title} on "{concept}"</h1>
<div class="legend">
  <span class="cite">[cite: X]</span> = school-specific or unique citation &nbsp;&nbsp;
  <span class="cite shared">[cite: X]</span> = edge also cited by another school
</div>
{turns}
<div class="verdict">
  <div class="label">Moderator's verdict</div>
  <div>{verdict}</div>
</div>
</body>
</html>
"""

# fixed color palette, cycles if more schools than colors
SCHOOL_COLORS = [
    ("#f1e6e6", "#7a1f1f"),  # red
    ("#e6ecf1", "#1f3f7a"),  # blue
    ("#e6f1e8", "#1f7a3f"),  # green
    ("#f1ece6", "#7a5a1f"),  # brown
    ("#ece6f1", "#5a1f7a"),  # purple
]


def render_html_n(final_state: dict, out_path: str) -> None:
    """Render an N-agent (2+) debate transcript to HTML with per-school colors."""
    schools = final_state["schools"]
    color_map = {s: SCHOOL_COLORS[i % len(SCHOOL_COLORS)] for i, s in enumerate(schools)}

    # find edge IDs cited by 2+ distinct schools (shared/overlap signal)
    ids_by_school: Dict[str, set] = {s: set() for s in schools}
    for t in final_state["transcript"]:
        ids_by_school.setdefault(t["speaker"], set())
        ids_by_school[t["speaker"]] |= {m.strip() for m in CITE_PATTERN.findall(t["text"])}
    all_id_sets = list(ids_by_school.values())
    shared_ids = set()
    for i in range(len(all_id_sets)):
        for j in range(i + 1, len(all_id_sets)):
            shared_ids |= all_id_sets[i] & all_id_sets[j]

    turns_html = []
    for t in final_state["transcript"]:
        bg, border = color_map.get(t["speaker"], ("#eee", "#888"))
        rejected_class = "" if t["accepted"] else "rejected"
        turns_html.append(
            f'<div class="turn {rejected_class}" style="background:{bg}; border-left:4px solid {border};">'
            f'<div class="speaker">{t["speaker"]}</div>'
            f'<div>{_format_text(t["text"], shared_ids)}</div>'
            f'</div>'
        )

    html = NAGENT_HTML_TEMPLATE.format(
        concept=final_state["concept"],
        schools_title=" vs ".join(schools),
        turns="\n".join(turns_html),
        verdict=final_state.get("verdict", "(no verdict)"),
    )

    with open(out_path, "w") as f:
        f.write(html)


def render_html(final_state: dict, out_path: str) -> None:
    """Render a 2-agent debate transcript to HTML (school_a/school_b)."""
    # find edge IDs cited by both speakers (signal of the dataset's general-school overlap)
    a_ids = set()
    b_ids = set()
    for t in final_state["transcript"]:
        ids = {m.strip() for m in CITE_PATTERN.findall(t["text"])}
        if t["speaker"] == "a":
            a_ids |= ids
        else:
            b_ids |= ids
    shared_ids = a_ids & b_ids

    turns_html = []
    for t in final_state["transcript"]:
        css_class = t["speaker"]
        rejected_class = "" if t["accepted"] else "rejected"
        speaker_label = final_state["school_a"] if t["speaker"] == "a" else final_state["school_b"]
        turns_html.append(
            f'<div class="turn {css_class} {rejected_class}">'
            f'<div class="speaker">{speaker_label}</div>'
            f'<div>{_format_text(t["text"], shared_ids)}</div>'
            f'</div>'
        )

    concept_a = final_state.get("concept_a") or final_state["concept"]
    concept_b = final_state.get("concept_b") or final_state["concept"]
    if concept_a == concept_b:
        title_concept = concept_a
    else:
        title_concept = f"{concept_a} ({final_state['school_a']}) vs {concept_b} ({final_state['school_b']})"

    html = HTML_TEMPLATE.format(
        concept=title_concept,
        school_a=final_state["school_a"],
        school_b=final_state["school_b"],
        turns="\n".join(turns_html),
        verdict=final_state.get("verdict", "(no verdict)"),
    )

    with open(out_path, "w") as f:
        f.write(html)
