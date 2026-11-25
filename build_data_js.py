"""Gera web/sapa_data.js com sprites em Base64 (100% off-line e sem flicker) e as 10 perguntas."""

import base64
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

AVATAR_NAMES = (
    "boto",
    "ariranha",
    "peixe_boi",
    "tartaruga",
    "onca",
    "preguica",
    "tucano",
    "arara",
    "pirarucu",
    "sapo",
)


def encode_png_data_uri(rel_path: str) -> str:
    full_path = os.path.join(BASE_DIR, "web", rel_path.replace("/", os.sep))
    if not os.path.exists(full_path):
        return rel_path
    with open(full_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def build():
    payload = {
        "sprites": {
            name: encode_png_data_uri(f"assets/sprites/{name}.png")
            for name in SPRITE_NAMES
        },
        "avatars": {
            name: encode_png_data_uri(f"assets/avatars/{name}.png")
            for name in AVATAR_NAMES
        },
        "logo": encode_png_data_uri("assets/sapa_logo.png"),
        "questions": QUESTIONS,
    }

    with open(OUT_JS, "w", encoding="utf-8") as f:
        f.write("window.__SAPA_DATA__ = ")
        json.dump(payload, f, ensure_ascii=False)
        f.write(";\n")

    size_kb = os.path.getsize(OUT_JS) / 1024
    print(f"Generated {OUT_JS} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    build()
