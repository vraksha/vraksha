import os
import re
from pathlib import Path

from src.llm import call_llm

user = "Change my country to USA"

print(call_llm(user))