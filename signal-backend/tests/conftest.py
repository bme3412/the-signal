import os
import sys

# Tests import backend modules (models, prompts, services.*) as top-level.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
