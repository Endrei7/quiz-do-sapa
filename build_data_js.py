"""Gera web/sapa_data.js com caminhos locais dos sprites (sapinho + boss) e as 10 perguntas."""

import json
import os
from questions import QUESTIONS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_JS = os.path.join(BASE_DIR, "web", "sapa_data.js")

SPRITE_NAMES = (
    "idle",
    "victory",
    "thinking",
    "sad",
    "angry",
    "waving",
    "boss_laugh",
    "boss_attack",
    "boss_angry",
    "boss_defeated",
)

payload = {
    "sprites": {name: f"assets/sprites/{name}.png" for name in SPRITE_NAMES},
    "logo": "assets/sapa_logo.png",
    "questions": QUESTIONS,
}

with open(OUT_JS, "w", encoding="utf-8") as f:
    f.write("window.__SAPA_DATA__ = ")
    json.dump(payload, f, ensure_ascii=False, indent=2)
    f.write(";\n")

print("Generated:", OUT_JS)
