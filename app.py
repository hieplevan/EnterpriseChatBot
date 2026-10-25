import runpy
from pathlib import Path

# Chuyen tiep tu dong sang frontend/app.py theo kien truc SDLC
target_path = Path(__file__).resolve().parent / "frontend" / "app.py"
runpy.run_path(str(target_path), run_name="__main__")
