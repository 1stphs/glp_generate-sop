from typing import List, Dict, Any
from .storage import LocalPlaybookStorage

class ContextEnhancer:
    def __init__(self, storage: LocalPlaybookStorage):
        self.storage = storage

    def get_relevant_playbook(self, task_description: str, top_n: int = 20) -> str:
        all_rules = self.storage.load_all()
        if not all_rules:
            return "(empty playbook)"
            
        relevant_rules = []
        task_desc_lower = task_description.lower()
        
        # Simple keyword matching based on tags
        for rule in all_rules:
            is_match = False
            for tag in rule.get('tags', []):
                t = tag.lower()
                if t in task_desc_lower or t in ['通用', 'general', '基础规范']:
                    is_match = True
                    break
            
            if is_match:
                relevant_rules.append(rule)
                
        if not relevant_rules:
            # Fallback: return top_n if no tags matched to provide some context
            relevant_rules = all_rules[:top_n]
            
        # Format rules into ACE bullet strings
        # Format: [id] helpful=X harmful=Y :: content
        # It handles formatting dynamically, preventing huge payloads.
        lines = []
        for r in relevant_rules:
            h = r.get('metrics', {}).get('helpful', 0)
            hm = r.get('metrics', {}).get('harmful', 0)
            lines.append(f"[{r['id']}] helpful={h} harmful={hm} :: {r['content']}")
            
        return "\n".join(lines)
