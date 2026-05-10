import importlib.util as util
from pathlib import Path


SKILLS_DIR = Path(__file__).parent

def discover_skills():
    for skill_file in SKILLS_DIR.rglob("*/skill.py"):
        yield skill_file

def register_skills():
    for skill_file in SKILLS_DIR.rglob("*/skill.py"):
        rel_name = f"skill_{skill_file.parent.stem}"
        
        spec = util.spec_from_file_location(rel_name, skill_file)
        if spec and spec.loader:
            module = util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            md_path = skill_file.parent / "SKILL.md"
            
            yield {
                "module": module,
                "instruction_path": md_path if md_path.exists() else None
            }

            