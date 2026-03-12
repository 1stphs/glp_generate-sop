from typing import Dict, Any

class ApprovalInterceptor:
    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve

    def request_approval(self, new_rule: Dict[str, Any]) -> bool:
        if self.auto_approve:
            return True
            
        print("\n" + "!" * 20 + " 发现新经验 " + "!" * 20)
        print(f"建议规则: {new_rule['content']}")
        print(f"建议标签: {new_rule.get('tags', [])}")
        print("!" * 50)
        
        while True:
            val = input("是否将此规则加入本地经验库？(y/n/a): ").strip().lower()
            if val == 'y':
                return True
            elif val == 'n':
                return False
            elif val == 'a':
                self.auto_approve = True
                return True
