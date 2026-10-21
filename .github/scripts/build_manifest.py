"""Generate builds.json for the GitHub Pages viewer.

Scans the repo root for *.DDOBuild files and writes a summary per file so the
viewer can render the build list without downloading every XML file.
"""
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def text(parent, tag):
    if parent is None:
        return ""
    el = parent.find(tag)
    return (el.text or "").strip() if el is not None else ""


def class_line(build):
    counts = {}
    for lt in build.iter("LevelTraining"):
        cls = text(lt, "Class")
        if not cls or cls in ("Epic", "Legendary"):
            continue
        counts[cls] = counts.get(cls, 0) + 1
    return " / ".join(f"{c} {n}" for c, n in counts.items())


def last_modified(path):
    out = subprocess.run(
        ["git", "log", "-1", "--format=%cI", "--", path.name],
        capture_output=True, text=True, cwd=path.parent,
    ).stdout.strip()
    return out or None


def summarize(path):
    entry = {"file": path.name, "updated": last_modified(path)}
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        entry["error"] = str(e)
        return entry
    character = root.find("Character")
    lives = character.findall("Life") if character is not None else []
    life = lives[0] if lives else None
    build = life.find("Build") if life is not None else None
    entry.update({
        "name": text(life, "Name"),
        "race": text(life, "Race"),
        "level": text(build, "Level"),
        "classes": class_line(build) if build is not None else "",
        "lives": len(lives),
        "builds": sum(len(l.findall("Build")) for l in lives),
    })
    return entry


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "builds.json"
    entries = [summarize(p) for p in sorted(root.glob("*.DDOBuild"))]
    entries.sort(key=lambda e: e.get("updated") or "", reverse=True)
    out.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(entries)} builds to {out}")


if __name__ == "__main__":
    main()
