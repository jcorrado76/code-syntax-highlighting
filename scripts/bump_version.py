# scripts/bump_version.py
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"


def read_version() -> str:
    txt = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"\s*$', txt)
    if not m:
        print("Version not found in pyproject.toml", file=sys.stderr)
        sys.exit(2)
    return m.group(1)


def write_version(new_ver: str) -> None:
    txt = PYPROJECT.read_text(encoding="utf-8")
    txt = re.sub(r'(?m)^(\s*version\s*=\s*")([^"]+)(")', rf"\1{new_ver}\3", txt)
    PYPROJECT.write_text(txt, encoding="utf-8")


def bump(ver: str, kind: str) -> str:
    try:
        major, minor, patch = map(int, ver.split("."))
    except Exception:
        print(f"Invalid version '{ver}' (expected X.Y.Z)", file=sys.stderr)
        sys.exit(3)
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    if kind == "patch":
        return f"{major}.{minor}.{patch + 1}"
    print(f"Unknown bump kind: {kind}", file=sys.stderr)
    sys.exit(4)


def maybe_sync_addon_json(new_ver: str) -> None:
    # Optional override: set ADDON_JSON_PATH to a specific file if you want.
    override = os.environ.get("ADDON_JSON_PATH")
    if override:
        candidates = [ROOT / override]
    else:
        # Default: look for an addon.json at repo depth 1–2
        candidates = list(ROOT.glob("addon.json")) + list(ROOT.glob("*/addon.json"))

    updated = False
    for p in candidates:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "version" in data:
                data["version"] = new_ver
                p.write_text(json.dumps(data, indent=2), encoding="utf-8")
                updated = True
        except Exception:
            pass
    if not updated:
        print(
            "Note: addon.json not found or no 'version' field to sync", file=sys.stderr
        )


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"major", "minor", "patch"}:
        print("usage: bump_version.py [major|minor|patch]", file=sys.stderr)
        sys.exit(1)
    kind = sys.argv[1]
    cur = read_version()
    new = bump(cur, kind)
    write_version(new)
    maybe_sync_addon_json(new)
    print(new)
