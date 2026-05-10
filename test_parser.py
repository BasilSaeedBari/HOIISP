import sys
import json
from app.services.project_parser import parse_project_md, validate_project_md

def test(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
        
    print(f"--- Parsing {file_path} ---")
    parsed = parse_project_md(md_text)
    
    print("\nParsed Data:")
    print(json.dumps(parsed, indent=2, ensure_ascii=False))
    
    print("\n--- Validating ---")
    validation = validate_project_md(parsed)
    
    print(f"Valid: {validation['valid']}")
    if validation['errors']:
        print("Errors:")
        for e in validation['errors']:
            print(f"  - {e}")
    if validation['warnings']:
        print("Warnings:")
        for w in validation['warnings']:
            print(f"  - {w}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_parser.py <path_to_project.md>")
    else:
        test(sys.argv[1])
