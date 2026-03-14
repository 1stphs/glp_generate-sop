import json
import logging
from typing import Dict, Any
from deepagent_sop.core.base_agent import DeepAgent
from deepagent_sop.core.utils.prompt_manager import SKILL_BUILDER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class SkillBuilderAgent(DeepAgent):
    """
    Skill Builder Agent responsible for generating Python tools (skills) 
    when text-based logic reaches its limits.
    """
    
    def forge_skill(self, technical_bottleneck: str) -> Dict[str, Any]:
        """
        Forges a new Python tool based on a described bottleneck.
        """
        logger.info(f"Forging skill for bottleneck: {technical_bottleneck}")
        
        user_prompt = f"""技术瓶颈描述: {technical_bottleneck}
请锻造一个对应的 Python 工具。"""
        
        response = self.run(user_prompt)
        
        try:
            skill_data = json.loads(response)
            return skill_data
        except Exception as e:
            logger.error(f"Failed to parse SkillBuilder output: {str(e)}")
            return {"error": "Invalid JSON output from SkillBuilder", "raw": response}
