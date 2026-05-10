import mistune
import frontmatter
from typing import Dict, Any, List

REQUIRED_SECTIONS = {
    'project-title':                {'level': 1, 'dbField': 'title'},
    'github-repository':            {'level': 2, 'dbField': 'github_url'},
    'team-members':                 {'level': 2, 'dbField': 'team', 'type': 'table'},
    'abstract':                     {'level': 2, 'dbField': 'abstract'},
    'problem-statement':            {'level': 2, 'dbField': 'problem_statement'},
    'domain--ieee-alignment':       {'level': 2, 'dbField': 'domain_data', 'type': 'mixed'},
    'objectives':                   {'level': 2, 'dbField': 'objectives', 'type': 'list'},
    'methodology':                  {'level': 2, 'dbField': 'methodology'},
    'work-breakdown-structure-wbs': {'level': 2, 'dbField': 'milestones', 'type': 'table'},
    'resource-management-matrix':   {'level': 2, 'dbField': 'resources', 'type': 'table'},
    'success-metrics':              {'level': 2, 'dbField': 'success_metrics', 'type': 'table'},
    'declaration':                  {'level': 2, 'dbField': 'declaration_checked', 'type': 'checkboxes'},
}

def parse_project_md(md_text: str) -> Dict[str, Any]:
    # Use frontmatter in case there is frontmatter
    post = frontmatter.loads(md_text)
    content = post.content
    
    markdown = mistune.create_markdown(renderer='ast', plugins=['table'])
    ast = markdown(content)
    
    parsed = {}
    current_section = None
    current_section_id = None
    
    def get_text(node):
        text = ""
        if 'children' in node:
            for c in node['children']:
                text += get_text(c)
                if c.get('type') in ['paragraph', 'list_item', 'block_text']:
                    text += '\n'
            return text
        if 'text' in node:
            return node['text']
        if 'raw' in node:
            return node['raw']
        return ''
        
    def parse_table(table_node):
        header_node = table_node['children'][0]
        body_node = table_node['children'][1] if len(table_node['children']) > 1 else None
        
        headers = [get_text(th).strip() for th in header_node['children']]
        
        rows = []
        if body_node:
            for tr in body_node['children']:
                row_data = {}
                for i, td in enumerate(tr['children']):
                    if i < len(headers):
                        row_data[headers[i]] = get_text(td).strip()
                rows.append(row_data)
        return rows

    def parse_list(list_node):
        items = []
        for li in list_node['children']:
            items.append(get_text(li).strip())
        return items
        
    def slugify(text):
        import re
        return re.sub(r'[^a-z0-9-]', '', text.lower().replace(' ', '-').replace('&', ''))

    # Walk AST
    for node in ast:
        if node['type'] == 'heading':
            heading_text = get_text(node)
            slug = slugify(heading_text)
            level = node.get('attrs', {}).get('level') or node.get('level')
            
            # Match to required sections
            matched = False
            for section_id, config in REQUIRED_SECTIONS.items():
                if slug.startswith(section_id) and level == config['level']:
                    current_section_id = section_id
                    current_section = config['dbField']
                    
                    if current_section not in parsed:
                        if config.get('type') == 'table' or config.get('type') == 'list':
                            parsed[current_section] = []
                        elif config.get('type') == 'mixed' or config.get('type') == 'checkboxes':
                            parsed[current_section] = {}
                        else:
                            parsed[current_section] = ''
                            
                        # Edge case for title which is just a heading
                        if section_id == 'project-title':
                            parsed[current_section] = heading_text
                    matched = True
                    break
                    
            if not matched:
                if level <= 2:
                    current_section = None
                    current_section_id = None
                elif current_section and REQUIRED_SECTIONS[current_section_id].get('type') is None:
                    # Treat sub-heading as content
                    prefix = '#' * level
                    text = f"{prefix} {heading_text}"
                    if parsed[current_section]:
                        parsed[current_section] += '\n\n' + text
                    else:
                        parsed[current_section] = text
                
        elif current_section:
            config = REQUIRED_SECTIONS[current_section_id]
            node_type = config.get('type')
            
            if node_type == 'table' and node['type'] == 'table':
                parsed[current_section] = parse_table(node)
            elif node_type == 'list' and node['type'] == 'list':
                parsed[current_section].extend(parse_list(node))
            elif node_type == 'mixed' or node_type == 'checkboxes':
                # Parse checkboxes and text manually
                text = get_text(node)
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('[x]') or line.startswith('[X]') or line.startswith('- [x]') or line.startswith('- [X]'):
                        parsed[current_section][line.split(']', 1)[1].strip()] = True
                    elif line.startswith('[ ]') or line.startswith('- [ ]'):
                        parsed[current_section][line.split(']', 1)[1].strip()] = False
                    elif ':' in line and node_type == 'mixed':
                        k, v = line.split(':', 1)
                        if k.startswith('**') and k.endswith('**'):
                            k = k[2:-2]
                        parsed[current_section][k.strip()] = v.strip()
            elif node_type is None:
                # Text content
                text = get_text(node)
                if parsed[current_section]:
                    parsed[current_section] += '\n\n' + text
                else:
                    parsed[current_section] = text
                    
    # Formatting fixes
    if 'github_url' in parsed:
        parsed['github_url'] = parsed['github_url'].strip()
        
    # Title could be heading + something, but usually just heading
    
    return parsed

def validate_project_md(parsed: Dict[str, Any]) -> Dict[str, Any]:
    errors = []
    warnings = []
    
    # Required sections check
    for key, config in REQUIRED_SECTIONS.items():
        if config['dbField'] not in parsed:
            errors.append(f"Missing required section: {key}")
            
    # Abstract >= 150 words
    abstract = parsed.get('abstract', '')
    if len(abstract.split()) < 150:
        errors.append(f"Abstract is too short ({len(abstract.split())} words, minimum 150)")
        
    # Team table 1-4 rows
    team = parsed.get('team', [])
    if not isinstance(team, list) or len(team) < 1 or len(team) > 4:
        errors.append("Team must have between 1 and 4 members")
        
    # Checkbox validations
    declarations = parsed.get('declaration_checked', {})
    if isinstance(declarations, dict):
        for k, v in declarations.items():
            if not v:
                errors.append(f"Declaration not checked: '{k}'")
                
    # WBS >= 3 rows
    milestones = parsed.get('milestones', [])
    if not isinstance(milestones, list) or len(milestones) < 3:
        errors.append("Work Breakdown Structure must have at least 3 milestones")
        
    # Metrics >= 3 rows
    metrics = parsed.get('success_metrics', [])
    if not isinstance(metrics, list) or len(metrics) < 3:
        errors.append("Success metrics must have at least 3 items")
        
    # Github URL
    gh_url = parsed.get('github_url', '')
    if 'github.com/' not in gh_url:
        errors.append("Invalid or missing GitHub URL in 'GitHub Repository' section")
        
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
