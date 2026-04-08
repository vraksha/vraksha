from src.utils.base_loop import run_loop
from src.skills.slop_detector.llm import detector_agent

def run_detector():
    run_loop(
        title="SLOP DETECTOR",
        input_prompt="Repo URL or Question",
        llm_fn=detector_agent,
        verify_always=True
    )

