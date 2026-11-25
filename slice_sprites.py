"""Fatia spritesheet.jpeg (grade 3x2), remove textos e deixa fundo branco transparente."""

from collections import deque
import os
from PIL import Image, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_SHEET = os.path.join(BASE_DIR, "spritesheet.jpeg")
OUT_DIR = os.path.join(BASE_DIR, "web", "assets", "sprites")

GRID_SPECS = [
    # (nome, col, row)
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
    """Mantem apenas o maior componente nao-branco (o sapo, ignorando rotulos de texto) e torna o fundo transparente."""
    # Reduz 2x durante a segmentacao para rapidez mantendo nitidez total no recorte final
    w, h = cell.size
    rgb = cell.convert("RGB")
    px = rgb.load()

    # 1. Mascara de pixels nao-brancos (desenho + letras)
    fg = [[not is_near_white(*px[x, y]) for x in range(w)] for y in range(h)]

    # 2. Encontra componentes conectados na mascara dilatada (para juntar pequenas falhas, mas manter texto separado)
    # Usamos passo em grade ou BFS direto na imagem reduzida (680x1024 -> ~0.7M px, super rapido em Pillow se usarmos miniatura para achar bbox)
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

    # Mapeia bounding box do sapo de volta para resolucao original com margem
    pad = 8
    x0 = max(0, best_bbox[0] * 2 - pad)
    y0 = max(0, best_bbox[1] * 2 - pad)
    x1 = min(w, best_bbox[2] * 2 + pad)
    y1 = min(h, best_bbox[3] * 2 + pad)

    # Limpa eventuais restos de letras que invadam a bounding box usando a mascara do maior componente
    frog_region_mask = Image.new("L", (small_w, small_h), 0)
    fpx = frog_region_mask.load()
    if best_mask:
        for px_x, px_y in best_mask:
            fpx[px_x, px_y] = 255
    frog_region_mask = frog_region_mask.filter(ImageFilter.MaxFilter(5)).resize((w, h), Image.Resampling.NEAREST)
    mpx = frog_region_mask.load()

    cropped = rgb.crop((x0, y0, x1, y1)).convert("RGBA")
    cw, ch = cropped.size
    cpx = cropped.load()

    # Zera qualquer pixel fora da mascara do sapo que seja parte de texto
    for cy in range(ch):
        oy = y0 + cy
        for cx in range(cw):
            ox = x0 + cx
            if mpx[ox, oy] == 0:
                cpx[cx, cy] = (255, 255, 255, 0)

    # Flood-fill a partir das bordas do recorte por pixels quase-brancos para preservar o branco DENTRO dos olhos e da garrafa!
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

    # Aplica transparencia com suavizacao suave na borda externa
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

    # Redimensiona para altura padrao nitida (~520px max) para carregamento instantaneo em Base64
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
