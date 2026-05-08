import re
from typing import Any

import frontmatter
import mistune


REQUIRED_SECTIONS = {
    "project-title": {"level": 1},
    "team-members": {"level": 2, "type": "table"},
    "abstract": {"level": 2},
    "problem-statement": {"level": 2},
    "domain--ieee-alignment": {"level": 2},
    "objectives": {"level": 2, "type": "list"},
    "methodology": {"level": 2},
    "work-breakdown-structure-wbs": {"level": 2, "type": "table"},
    "resource-management-matrix": {"level": 2, "type": "table"},
    "success-metrics": {"level": 2, "type": "table"},
    "declaration": {"level": 2, "type": "checkboxes"},
}


def heading_to_slug(text: str) -> str:
    clean = re.sub(r"[^a-z0-9\s-]", "", text.lower())
    return re.sub(r"\s+", "-", clean).strip("-")


def flatten_text(node: Any) -> str:
    node_type = node.get("type")
    if node_type == "text":
        return node.get("raw", "")
    children = node.get("children", [])
    return "".join(flatten_text(child) for child in children)


def extract_text(nodes: list[dict]) -> str:
    parts = []
    for node in nodes:
        if node.get("type") == "blank_line":
            continue
        parts.append(flatten_text(node).strip())
    return "\n".join(part for part in parts if part).strip()


def parse_table(nodes: list[dict]) -> list[dict]:
    table_node = next((n for n in nodes if n.get("type") == "table"), None)
    if not table_node:
        return []
    header_cells = table_node.get("children", [{}])[0].get("children", [])
    headers = [flatten_text(c).strip().lower() for c in header_cells]
    rows = []
    for row in table_node.get("children", [])[1:]:
        vals = [flatten_text(c).strip() for c in row.get("children", [])]
        if not any(vals):
            continue
        rows.append({headers[i] if i < len(headers) else str(i): v for i, v in enumerate(vals)})
    return rows


def parse_checkboxes(text: str) -> list[bool]:
    checks = re.findall(r"- \[(x|X| )\]", text)
    return [c.lower() == "x" for c in checks]


def parse_domain(text: str) -> str:
    selected = re.findall(r"- \[(x|X)\]\s+(.+)", text)
    if selected:
        return selected[0][1].strip()
    return "Unspecified"


def extract_title(ast: list[dict]) -> str:
    for node in ast:
        if node.get("type") == "heading" and node.get("attrs", {}).get("level") == 1:
            t = flatten_text(node).strip()
            if t.lower() == "project title":
                continue
            return t
    return "Untitled Project"


def split_sections(ast: list[dict]) -> dict:
    sections = {}
    current_slug = None
    bucket = []
    for node in ast:
        if node.get("type") == "heading":
            if current_slug:
                sections[current_slug] = bucket
            current_slug = heading_to_slug(flatten_text(node))
            bucket = []
        elif current_slug:
            bucket.append(node)
    if current_slug:
        sections[current_slug] = bucket
    return sections


def is_effectively_empty(text: str) -> bool:
    stripped = re.sub(r"[`*_>\-|]", " ", text)
    words = [w for w in re.split(r"\s+", stripped) if w]
    return len(words) == 0


def validate_sections(sections: dict) -> dict:
    errors = []
    warnings = []
    for slug in REQUIRED_SECTIONS:
        if slug not in sections:
            errors.append({"section": slug, "message": f'Required section "{slug}" is missing.'})
            continue
        txt = extract_text(sections[slug])
        if is_effectively_empty(txt):
            errors.append({"section": slug, "message": f'Required section "{slug}" has no content.'})

    abstract_words = len(re.findall(r"\b\w+\b", extract_text(sections.get("abstract", []))))
    if abstract_words < 150:
        errors.append({"section": "abstract", "message": f"Abstract is too short ({abstract_words} words). Minimum: 150."})
    if abstract_words > 350:
        warnings.append({"section": "abstract", "message": f"Abstract may be too long ({abstract_words} words). Target: 200-300."})

    team_rows = parse_table(sections.get("team-members", []))
    valid_team_rows = [r for r in team_rows if r.get("name", "").strip() and r.get("student id", "").strip()]
    if len(valid_team_rows) < 1:
        errors.append({"section": "team-members", "message": "Team table requires at least one valid member row."})

    milestones = parse_table(sections.get("work-breakdown-structure-wbs", []))
    if len(milestones) < 3:
        errors.append({"section": "work-breakdown-structure-wbs", "message": "WBS must contain at least 3 milestones."})

    declaration_checks = parse_checkboxes(extract_text(sections.get("declaration", [])))
    if not declaration_checks or not all(declaration_checks):
        errors.append({"section": "declaration", "message": "All declaration checkboxes must be checked."})

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def parse_proposal(md_text: str) -> dict:
    post = frontmatter.loads(md_text)
    content = post.content
    markdown = mistune.create_markdown(renderer="ast", plugins=["table"])
    ast = markdown(content)
    sections = split_sections(ast)
    title = extract_title(ast)
    return {
        "frontmatter": post.metadata,
        "title": title,
        "sections": sections,
        "validation": validate_sections(sections),
        "abstract": extract_text(sections.get("abstract", [])),
        "problem_statement": extract_text(sections.get("problem-statement", [])),
        "methodology": extract_text(sections.get("methodology", [])),
        "objectives": extract_text(sections.get("objectives", [])),
        "domain": parse_domain(extract_text(sections.get("domain--ieee-alignment", []))),
        "team": parse_table(sections.get("team-members", [])),
        "milestones": parse_table(sections.get("work-breakdown-structure-wbs", [])),
        "resources": parse_table(sections.get("resource-management-matrix", [])),
        "success_metrics": parse_table(sections.get("success-metrics", [])),
    }
