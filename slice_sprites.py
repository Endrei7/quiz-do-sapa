"""Fatia spritesheet.jpeg (grade 3x2), remove textos e deixa apenas o fundo externo transparente."""

from collections import deque
import os
from PIL import Image, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_SHEET = os.path.join(BASE_DIR, "spritesheet.jpeg")
OUT_DIR = os.path.join(BASE_DIR, "web", "assets", "sprites")

GRID_SPECS = [
    ("idle", 0, 0),
    ("victory", 1, 0),
    ("thinking", 2, 0),
    ("sad", 0, 1),
    ("angry", 1, 1),
    ("waving", 2, 1),
]


def is_near_white(r: int, g: int, b: int) -> bool:
    return r > 232 and g > 232 and b > 232 and (max(r, g, b) - min(r, g, b)) < 22


def extract_frog_from_cell(cell: Image.Image) -> Image.Image:
    """Isola apenas o sapo (removendo textos), preenchendo buracos internos (olhos/garrafa) antes da mascara."""
    w, h = cell.size
    rgb = cell.convert("RGB")

    small_w, small_h = w // 2, h // 2
    small = rgb.resize((small_w, small_h), Image.Resampling.BILINEAR)
    spx = small.load()
    s_fg = [[not is_near_white(*spx[x, y]) for x in range(small_w)] for y in range(small_h)]

    visited = [[False] * small_w for _ in range(small_h)]
    best_area = 0
    best_bbox = (0, 0, small_w, small_h)
    best_mask = None

    for y in range(small_h):
        for x in range(small_w):
            if not s_fg[y][x] or visited[y][x]:
                continue
            q = deque([(x, y)])
            visited[y][x] = True
            pts = []
            minx = maxx = x
            miny = maxy = y
            while q:
                cx, cy = q.popleft()
                pts.append((cx, cy))
                if cx < minx: minx = cx
                if cx > maxx: maxx = cx
                if cy < miny: miny = cy
                if cy > maxy: maxy = cy
                for nx in range(max(0, cx - 2), min(small_w, cx + 3)):
                    for ny in range(max(0, cy - 2), min(small_h, cy + 3)):
                        if not visited[ny][nx] and s_fg[ny][nx]:
                            visited[ny][nx] = True
                            q.append((nx, ny))
            if len(pts) > best_area:
                best_area = len(pts)
                best_bbox = (minx, miny, maxx + 1, maxy + 1)
                best_mask = pts

    # Constroi mascara solida do sapo e PREENCHE buracos internos (olhos brancos, garrafa)
    frog_mask = Image.new("L", (small_w, small_h), 0)
    fpx = frog_mask.load()
    if best_mask:
        for px_x, px_y in best_mask:
            fpx[px_x, px_y] = 255
    frog_mask = frog_mask.filter(ImageFilter.MaxFilter(5))
    fpx = frog_mask.load()

    # Flood-fill do lado externo na mascara dilatada; tudo que nao for alcancado pelo exterior pertence ao sapo (incluindo olhos!)
    ext = [[False] * small_w for _ in range(small_h)]
    eq = deque()
    for x in range(small_w):
        if fpx[x, 0] == 0:
            ext[0][x] = True
            eq.append((x, 0))
        if fpx[x, small_h - 1] == 0:
            ext[small_h - 1][x] = True
            eq.append((x, small_h - 1))
    for y in range(small_h):
        if fpx[0, y] == 0:
            ext[y][0] = True
            eq.append((0, y))
        if fpx[small_w - 1, y] == 0:
            ext[y][small_w - 1] = True
            eq.append((small_w - 1, y))

    while eq:
        cx, cy = eq.popleft()
        for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
            if 0 <= nx < small_w and 0 <= ny < small_h and not ext[ny][nx] and fpx[nx, ny] == 0:
                ext[ny][nx] = True
                eq.append((nx, ny))

    for y in range(small_h):
        for x in range(small_w):
            fpx[x, y] = 0 if ext[y][x] else 255

    frog_mask_full = frog_mask.resize((w, h), Image.Resampling.NEAREST)
    mpx = frog_mask_full.load()

    pad = 8
    x0 = max(0, best_bbox[0] * 2 - pad)
    y0 = max(0, best_bbox[1] * 2 - pad)
    x1 = min(w, best_bbox[2] * 2 + pad)
    y1 = min(h, best_bbox[3] * 2 + pad)

    cropped = rgb.crop((x0, y0, x1, y1)).convert("RGBA")
    cw, ch = cropped.size
    cpx = cropped.load()

    # Remove apenas pixels fora da silhueta solida do sapo (textos externos)
    for cy in range(ch):
        oy = y0 + cy
        for cx in range(cw):
            ox = x0 + cx
            if mpx[ox, oy] == 0:
                cpx[cx, cy] = (255, 255, 255, 0)

    # Flood-fill a partir das bordas por branco externo para manter olhos e garrafa 100% opacos
    bg_vis = [[False] * cw for _ in range(ch)]
    q = deque()
    for x in range(cw):
        q.append((x, 0))
        q.append((x, ch - 1))
    for y in range(ch):
        q.append((0, y))
        q.append((cw - 1, y))

    while q:
        cx, cy = q.popleft()
        if not (0 <= cx < cw and 0 <= cy < ch) or bg_vis[cy][cx]:
            continue
        r, g, b, a = cpx[cx, cy]
        if a == 0 or is_near_white(r, g, b):
            bg_vis[cy][cx] = True
            q.append((cx + 1, cy))
            q.append((cx - 1, cy))
            q.append((cx, cy + 1))
            q.append((cx, cy - 1))

    for cy in range(ch):
        for cx in range(cw):
            if bg_vis[cy][cx]:
                cpx[cx, cy] = (255, 255, 255, 0)
            else:
                r, g, b, a = cpx[cx, cy]
                lum = (r + g + b) / 3.0
                if lum > 195 and (max(r, g, b) - min(r, g, b)) < 25:
                    near_bg = any(
                        0 <= cx + dx < cw and 0 <= cy + dy < ch and bg_vis[cy + dy][cx + dx]
                        for dx in (-1, 0, 1)
                        for dy in (-1, 0, 1)
                    )
                    if near_bg:
                        alpha = int(max(0, min(255, (242 - lum) / 47.0 * 255)))
                        cpx[cx, cy] = (r, g, b, alpha)

    final_bbox = cropped.getbbox()
    if final_bbox:
        cropped = cropped.crop(final_bbox)

    cropped.thumbnail((520, 520), Image.Resampling.LANCZOS)
    return cropped


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sheet = Image.open(SRC_SHEET).convert("RGB")
    sw, sh = sheet.size
    col_w = sw / 3.0
    row_h = sh / 2.0

    for name, col, row in GRID_SPECS:
        x0 = int(round(col * col_w))
        y0 = int(round(row * row_h))
        x1 = int(round((col + 1) * col_w))
        y1 = int(round((row + 1) * row_h))
        cell = sheet.crop((x0, y0, x1, y1))
        sprite = extract_frog_from_cell(cell)
        out_path = os.path.join(OUT_DIR, f"{name}.png")
        sprite.save(out_path, "PNG")
        print(f"Saved {name}.png: {sprite.size}")


if __name__ == "__main__":
    main()
