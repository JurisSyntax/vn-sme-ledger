import json, os, sys

def _base_path():
    return getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))

def get_vas_rules(niche="default"):
    p = os.path.join(_base_path(), "presets", "niche_vas.json")
    if not os.path.exists(p): return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f).get(niche, {})
