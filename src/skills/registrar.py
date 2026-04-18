import importlib.util as util
from pathlib import Path


SKILLS_DIR = Path(__file__).parent

def discover_skills():
    for skill_file in SKILLS_DIR.rglob("*/skill.py"):
        yield skill_file

def register_skills():
    for skill_file in discover_skills():
        skill_name = skill_file.parent.name
        
        spec = util.spec_from_file_location(skill_name, skill_file)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)

        instruction_path = skill_file.parent / "SKILL.md"
        instruction = instruction_path.read_text(encoding="utf-8") if instruction_path.exists() else ""

        yield {
            "name": skill_name,
            "module": module,
            "instruction": instruction
        }

