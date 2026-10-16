"""Run modules with normal installed packages, or an explicitly supplied dependency folder."""
import os
from pathlib import Path
import runpy
import site
import sys

if os.environ.get("DATAWAIS_DEPS"):
    site.addsitedir(os.environ["DATAWAIS_DEPS"])
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
module = sys.argv.pop(1)
runpy.run_module(module, run_name="__main__")
