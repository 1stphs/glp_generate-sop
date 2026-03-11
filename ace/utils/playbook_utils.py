"""
==============================================================================
playbook.py
==============================================================================

This file contains functions for parsing and manipulating the playbook.

"""
import json
import re

def parse_playbook_line(line):
    """Parse a single playbook line to extract components"""
    # Pattern: [id] helpful=X harmful=Y :: content
    pattern = r'\[([^\]]+)\]\s*helpful=(\d+)\s*harmful=(\d+)\s*::\s*(.*)'
    match = re.match(pattern, line.strip())
    
    if match:
        return {
            'id': match.group(1),
            'helpful': int(match.group(2)),
            'harmful': int(match.group(3)),
            'content': match.group(4),
            'raw_line': line
        }
    return None

def format_playbook_line(bullet_id, helpful, harmful, content):
    """Format a bullet into playbook line format"""
    return f"[{bullet_id}] helpful={helpful} harmful={harmful} :: {content}"

def extract_json_from_text(text, json_key=None):
    """Extract JSON object from text, handling various formats"""
    try:
        # First, try to parse the entire response as JSON (JSON mode)
        try:
            result = json.loads(text.strip())
            return result
        except json.JSONDecodeError:
            pass
        
        # Fallback: Look for ```json blocks
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            # Try each match until we find valid JSON
            for match in matches:
                try:
                    json_str = match.strip()
                    result = json.loads(json_str)
                    return result
                except json.JSONDecodeError:
                    continue
        
        # Improved JSON extraction using balanced brace counting
        def find_json_objects(text):
            """Find JSON objects using balanced brace counting"""
            json_objects = []
            i = 0
            while i < len(text):
                if text[i] == '{':
                    # Found start of potential JSON object
                    brace_count = 1
                    start = i
                    i += 1
                    
                    while i < len(text) and brace_count > 0:
                        if text[i] == '{':
                            brace_count += 1
                        elif text[i] == '}':
                            brace_count -= 1
                        elif text[i] == '"':
                            # Handle quoted strings to avoid counting braces inside strings
                            i += 1
                            while i < len(text) and text[i] != '"':
                                if text[i] == '\\':
                                    i += 1  # Skip escaped character
                                i += 1
                        i += 1
                    
                    if brace_count == 0:
                        # Found complete JSON object
                        json_candidate = text[start:i]
                        json_objects.append(json_candidate)
                else:
                    i += 1
            
            return json_objects
        
        # Find all potential JSON objects
        json_objects = find_json_objects(text)
        
        for json_str in json_objects:
            try:
                result = json.loads(json_str)
                return result
            except json.JSONDecodeError:
                continue
                
    except Exception as e:
        print(f"Failed to extract JSON: {e}")
        if len(text) > 500:
            print(f"Raw content preview:\n{text[:500]}...")
        else:
            print(f"Raw content:\n{text}")
        
    return None

def extract_playbook_bullets(playbook_text, bullet_ids):
    """
    Extract specific bullet points from playbook based on bullet_ids.
    
    Args:
        playbook_text (str): The full playbook text
        bullet_ids (list): List of bullet IDs to extract
    
    Returns:
        str: Formatted playbook content containing only the specified bullets
    """
    if not bullet_ids:
        return "(No bullets used by generator)"
    
    lines = playbook_text.strip().split('\n')
    found_bullets = []
    
    for line in lines:
        if line.strip():  # Skip empty lines
            parsed = parse_playbook_line(line)
            if parsed and parsed['id'] in bullet_ids:
                found_bullets.append({
                    'id': parsed['id'],
                    'content': parsed['content'],
                    'helpful': parsed['helpful'],
                    'harmful': parsed['harmful']
                })
    
    if not found_bullets:
        return "(Generator referenced bullet IDs but none were found in playbook)"
    
    # Format the bullets for reflector input
    formatted_bullets = []
    for bullet in found_bullets:
        formatted_bullets.append(f"[{bullet['id']}] helpful={bullet['helpful']} harmful={bullet['harmful']} :: {bullet['content']}")
    
    return '\n'.join(formatted_bullets)
