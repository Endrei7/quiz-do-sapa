"""Fatia boss_spritesheet.jpg (grade 2x2) removendo apenas o fundo branco externo."""

from collections import deque
import os
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_BOSS = os.path.join(BASE_DIR, "boss_spritesheet.jpg")
OUT_DIR = os.path.join(BASE_DIR, "web", "assets", "sprites")

BOSS_GRID = [
    ("boss_laugh", 0, 0),
    ("boss_attack", 1, 0),
    ("boss_angry", 0, 1),
    ("boss_defeated", 1, 1),
]


def is_near_white(r: int, g: int, b: int) -> bool:
    return r > 232 and g > 232 and b > 232 and (max(r, g, b) - min(r, g, b)) < 24


def remove_outer_white(cell: Image.Image) -> Image.Image:
    """Flood-fill a partir das bordas da celula mantendo olhos, dentes e estrelas 100% opacos."""
    rgba = cell.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()

    bg_vis = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))

    while q:
        cx, cy = q.popleft()
        if not (0 <= cx < w and 0 <= cy < h) or bg_vis[cy][cx]:
            continue
        r, g, b, _ = px[cx, cy]
        if is_near_white(r, g, b):
            bg_vis[cy][cx] = True
            q.append((cx + 1, cy))
            q.append((cx - 1, cy))
            q.append((cx, cy + 1))
            q.append((cx, cy - 1))

    # Tambem torna transparentes os pequenos rasgos brancos na capa esfarrapada (parte inferior)
    island_vis = [[False] * w for _ in range(h)]
    for y in range(int(h * 0.65), h):
        for x in range(w):
            if bg_vis[y][x] or island_vis[y][x]:
                continue
            r, g, b, _ = px[x, y]
            if is_near_white(r, g, b):
                iq = deque([(x, y)])
                island_vis[y][x] = True
                pts = []
                while iq:
                    cx, cy = iq.popleft()
                    pts.append((cx, cy))
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < w and 0 <= ny < h and not bg_vis[ny][nx] and not island_vis[ny][nx]:
                            if is_near_white(*px[nx, ny][:3]):
                                island_vis[ny][nx] = True
                                iq.append((nx, ny))
                if len(pts) < 1200 and all(py > int(h * 0.62) for _, py in pts):
                    for px_x, px_y in pts:
                        bg_vis[px_y][px_x] = True

    for y in range(h):
        for x in range(w):
            if bg_vis[y][x]:
                px[x, y] = (255, 255, 255, 0)
            else:
                r, g, b, _ = px[x, y]
                lum = (r + g + b) / 3.0
                if lum > 195 and (max(r, g, b) - min(r, g, b)) < 26:
                    near_bg = any(
                        0 <= x + dx < w and 0 <= y + dy < h and bg_vis[y + dy][x + dx]
                        for dx in (-1, 0, 1)
                        for dy in (-1, 0, 1)
                    )
                    if near_bg:
                        alpha = int(max(0, min(255, (242 - lum) / 47.0 * 255)))
                        px[x, y] = (r, g, b, alpha)

    bbox = rgba.getbbox()
    if bbox:
        rgba = rgba.crop(bbox)
    rgba.thumbnail((504, 504), Image.Resampling.LANCZOS)
    padded = Image.new("RGBA", (rgba.width + 16, rgba.height + 16), (0, 0, 0, 0))
    padded.paste(rgba, (8, 8))
    return padded


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sheet = Image.open(SRC_BOSS).convert("RGB")
    sw, sh = sheet.size
    cw = sw / 2.0
    ch = sh / 2.0

    for name, col, row in BOSS_GRID:
        x0 = int(round(col * cw))
        y0 = int(round(row * ch))
        x1 = int(round((col + 1) * cw))
        y1 = int(round((row + 1) * ch))
        cell = sheet.crop((x0, y0, x1, y1))
        sprite = remove_outer_white(cell)
        out_path = os.path.join(OUT_DIR, f"{name}.png")
        sprite.save(out_path, "PNG")
        print(f"Saved {name}.png: {sprite.size}")


if __name__ == "__main__":
    main()
