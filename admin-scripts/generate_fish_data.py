#!/usr/bin/env python3
"""Generate _data/fish.json for the docs site from fishing_game_config.json.

Usage:
  python admin-scripts/generate_fish_data.py

This reads fishing_game_config.json, extracts fish entries and writes a
Jekyll data file with:
  - rarity_order (manual canonical ordering)
  - rarity_labels (title-cased labels)
  - items (fish + special items)

It converts `description` -> `blurb` and preserves numeric ranges:
  min_size_cm, max_size_cm, min_weight_kg, max_weight_kg

It also appends a synthetic special entry for "No-Fish" if not present.

Run this whenever the runtime config fish list changes to keep the docs synced.
"""

from __future__ import annotations
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "fishing_game_config.json"
DATA_PATH = REPO_ROOT / "_data" / "fish.json"

RARITY_ORDER = [
    "mythic",
    "ultra-legendary",
    "legendary",
    "epic",
    "rare",
    "uncommon",
    "common",
    "junk",
]

def title_label(rarity: str) -> str:
    return rarity.replace("-", " ").title().replace(" ", "-") if rarity != "ultra-legendary" else "Ultra-Legendary"

def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def build_items(cfg: dict) -> list[dict]:
    items = []
    for entry in cfg.get("fish", []):
        items.append({
            "name": entry["name"],
            "rarity": entry["rarity"],
            "blurb": shorten(entry.get("description", "")),
            "min_size_cm": entry.get("min_size_cm"),
            "max_size_cm": entry.get("max_size_cm"),
            "min_weight_kg": entry.get("min_weight_kg"),
            "max_weight_kg": entry.get("max_weight_kg"),
        })
    # Append special placeholder if missing
    if not any(i["name"] == "No-Fish" for i in items):
        items.append({
            "name": "No-Fish",
            "rarity": "special",
            "blurb": "Shown when nothing bites.",
        })
    return items

def shorten(desc: str, limit: int = 70) -> str:
    d = desc.strip()
    if len(d) <= limit:
        return d
    # Try cut at last space before limit
    cut = d[:limit].rsplit(" ", 1)[0]
    return cut + "…"

def main():
    cfg = load_config()
    data = {
        "rarity_order": RARITY_ORDER,
        "rarity_labels": {r: title_label(r) for r in RARITY_ORDER},
        "items": build_items(cfg),
    }
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"Wrote {DATA_PATH.relative_to(REPO_ROOT)} with {len(data['items'])} items")

if __name__ == "__main__":
    main()
