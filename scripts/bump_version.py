# scripts/bump_version.py  (no tomlkit, no regex)
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"


def bump_semver(ver: str, kind: str) -> str:
    core = ver.split("-", 1)[0].split("+", 1)[0]
    parts = core.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        print(f"Unsupported version format '{ver}'. Expected X.Y.Z", file=sys.stderr)
        sys.exit(5)
    major, minor, patch = map(int, parts)
    if kind == "major":
        major, minor, patch = major + 1, 0, 0
    elif kind == "minor":
        minor, patch = minor + 1, 0
    elif kind == "patch":
        patch += 1
    else:
        print("Usage: bump_version.py [major|minor|patch]", file=sys.stderr)
        sys.exit(6)
    return f"{major}.{minor}.{patch}"


def read_and_bump_pyproject(kind: str) -> str:
    lines = PYPROJECT.read_text(encoding="utf-8").splitlines(keepends=True)
    in_project = False
    current = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project = stripped == "[project]"
        elif in_project and stripped.startswith("version"):
            # Expect: version = "X.Y.Z"
            before, sep, after = line.partition("=")
            val = after.strip()
            if val.startswith('"') and '"' in val[1:]:
                end = val[1:].index('"') + 2
                cur = val[1 : end - 1]
                new = bump_semver(cur, kind)
                lines[i] = f'{before}{sep} "{new}"\n'
                current = new
                break
            else:
                print("Could not parse version line under [project]", file=sys.stderr)
                sys.exit(7)
    if current is None:
        print("Did not find [project].version", file=sys.stderr)
        sys.exit(4)
    PYPROJECT.write_text("".join(lines), encoding="utf-8")
    return current


def sync_addon_json(new_ver: str) -> None:
    override = os.environ.get("ADDON_JSON_PATH")
    paths = (
        [ROOT / override]
        if override
        else [*(ROOT.glob("addon.json")), *(ROOT.glob("*/addon.json"))]
    )
    for p in paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            data["version"] = new_ver
            p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"major", "minor", "patch"}:
        print("Usage: bump_version.py [major|minor|patch]", file=sys.stderr)
        sys.exit(1)
    new_ver = read_and_bump_pyproject(sys.argv[1])
    sync_addon_json(new_ver)
    print(new_ver)
