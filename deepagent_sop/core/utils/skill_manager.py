import os
import logging
import importlib.util
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SkillManager:
    """
    Utility for managing, saving, and executing dynamically generated Python tools (skills).
    """
    
    def __init__(self, skill_dir: str):
        self.skill_dir = skill_dir
        if not os.path.exists(self.skill_dir):
            os.makedirs(self.skill_dir)
            
    def save_skill(self, experiment_type: str, skill_name: str, code: str) -> str:
        """
        Saves a generated skill to the filesystem.
        """
        target_dir = os.path.join(self.skill_dir, experiment_type)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            
        file_path = os.path.join(target_dir, f"{skill_name}.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        
        logger.info(f"Skill saved to: {file_path}")
        return file_path
        
    def execute_skill(self, experiment_type: str, skill_name: str, input_data: Any) -> Any:
        """
        Executes a skill using exec() within a controlled namespace.
        """
        target_dir = os.path.join(self.skill_dir, experiment_type)
        file_path = os.path.join(target_dir, f"{skill_name}.py")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Skill {skill_name} not found at {file_path}")
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            
            # Context for execution
            namespace = {"__name__": "__main__"}
            
            # Execute the code in the namespace
            exec(code, namespace)
            
            # Look for entry point
            if "main" in namespace and callable(namespace["main"]):
                return namespace["main"](input_data)
            
            # Fallback: look for any function if main isn't there
            for name, val in namespace.items():
                if callable(val) and not name.startswith("_"):
                    return val(input_data)
                    
            raise AttributeError(f"No entry point function found in skill {skill_name}")
                
        except Exception as e:
            logger.error(f"Error executing skill {skill_name}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": f"Execution failed: {str(e)}"}

    def list_skills(self, experiment_type: str) -> list:
        target_dir = os.path.join(self.skill_dir, experiment_type)
        if not os.path.exists(target_dir):
            return []
        return [f.replace(".py", "") for f in os.listdir(target_dir) if f.endswith(".py")]
