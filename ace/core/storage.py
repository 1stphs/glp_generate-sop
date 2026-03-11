import os
import json
from typing import List, Dict, Any

class LocalPlaybookStorage:
    def __init__(self, playbook_path: str):
        self.playbook_path = playbook_path
        if not os.path.exists(self.playbook_path):
            self._init_empty()

    def _init_empty(self):
        os.makedirs(os.path.dirname(self.playbook_path), exist_ok=True)
        with open(self.playbook_path, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)

    def load_all(self) -> List[Dict[str, Any]]:
        try:
            with open(self.playbook_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def save_all(self, rules: List[Dict[str, Any]]):
        with open(self.playbook_path, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)

    def add_rule(self, rule: Dict[str, Any]):
        rules = self.load_all()
        rules.append(rule)
        self.save_all(rules)

    def update_metrics(self, bullet_tags: List[Dict[str, str]]):
        rules = self.load_all()
        # Create tag lookup map
        tag_map = {}
        for tag in bullet_tags:
             bullet_id = tag.get('id') or tag.get('bullet', '')
             tag_value = tag.get('tag', 'neutral')
             if bullet_id:
                 tag_map[bullet_id] = tag_value
        
        changed = False
        for rule in rules:
            if rule['id'] in tag_map:
                val = tag_map[rule['id']]
                if val == 'helpful':
                    rule['metrics']['helpful'] += 1
                    changed = True
                elif val == 'harmful':
                    rule['metrics']['harmful'] += 1
                    changed = True
        if changed:
            self.save_all(rules)

    def get_stats(self) -> Dict[str, Any]:
        rules = self.load_all()
        stats = {
            'total_bullets': len(rules),
            'high_performing': sum(1 for r in rules if r.get('metrics', {}).get('helpful', 0) > 5 and r.get('metrics', {}).get('harmful', 0) < 2),
            'problematic': sum(1 for r in rules if r.get('metrics', {}).get('harmful', 0) >= r.get('metrics', {}).get('helpful', 0) and r.get('metrics', {}).get('harmful', 0) > 0),
            'unused': sum(1 for r in rules if r.get('metrics', {}).get('helpful', 0) + r.get('metrics', {}).get('harmful', 0) == 0)
        }
        return stats
