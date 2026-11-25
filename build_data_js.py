"""Gera web/sapa_data.js com caminhos relativos dentro de web/ e as 10 perguntas do S.A.P.A."""

import json
import os
from questions import QUESTIONS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_JS = os.path.join(BASE_DIR, "web", "sapa_data.js")

payload = {
    "sprites": {
        name: f"assets/sprites/{name}.png"
        for name in ("idle", "victory", "thinking", "sad", "angry", "waving")
    },
    "logo": "assets/sapa_logo.png",
    "questions": QUESTIONS,
}

with open(OUT_JS, "w", encoding="utf-8") as f:
    f.write("window.__SAPA_DATA__ = ")
    json.dump(payload, f, ensure_ascii=False, indent=2)
    f.write(";\n")

print("Generated:", OUT_JS)
