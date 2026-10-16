"""Initialize private role credentials and copy reproducible demo fixtures. Never overwrite."""
import argparse
import json
from pathlib import Path
import secrets
import shutil

parser = argparse.ArgumentParser()
parser.add_argument("--root", type=Path, default=Path("workspace"))
parser.add_argument("--runtime", type=Path, default=Path(".runtime"))
args = parser.parse_args()
project = Path(__file__).resolve().parents[1]
if args.root.exists() and any(args.root.iterdir()):
    raise SystemExit("Workspace is not empty. Choose a new --root; initialization never overwrites.")
shutil.copytree(project/"fixtures", args.root, dirs_exist_ok=True)
args.runtime.mkdir(parents=True, exist_ok=True)
config = args.runtime/"secrets.json"
if not config.exists():
    with config.open("x", encoding="utf-8") as f:
        json.dump({"tokens": {role: secrets.token_urlsafe(36) for role in ["admin", "inspector", "cleaner"]}}, f, indent=2)
print("Demo workspace initialized. Private role tokens saved locally; no tokens printed.")
