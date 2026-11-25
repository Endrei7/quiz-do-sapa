"""Fatia equipes_spritesheet.jpg (grade 5x2) em 10 sprites PNG com fundo transparente."""

from collections import deque
import os
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_IMAGE = os.path.join(BASE_DIR, "equipes_spritesheet.jpg")
OUT_DIR = os.path.join(BASE_DIR, "web", "assets", "avatars")

AVATAR_GRID_NAMES = [
    ["boto", "ariranha", "peixe_boi", "tartaruga", "onca"],
    ["preguica", "tucano", "arara", "pirarucu", "sapo"],
]

TARGET_INNER_SIZE = 304
BORDER_PAD = 8


def is_bg_pixel(r: int, g: int, b: int, min_val: int = 232, max_spread: int = 22) -> bool:
    return min(r, g, b) >= min_val and (max(r, g, b) - min(r, g, b)) <= max_spread


def find_spans_1d(flags: list[bool], min_len: int = 20, merge_gap: int = 12) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = None
    for i, active in enumerate(flags):
        if active and start is None:
            start = i
        elif not active and start is not None:
            if not spans or (start - spans[-1][1]) > merge_gap:
                spans.append((start, i))
            else:
                spans[-1] = (spans[-1][0], i)
            start = None
    if start is not None:
        if not spans or (start - spans[-1][1]) > merge_gap:
            spans.append((start, len(flags)))
        else:
            spans[-1] = (spans[-1][0], len(flags))
    return [(a, b) for (a, b) in spans if (b - a) >= min_len]


def compute_row_bounds(rgb: Image.Image) -> list[tuple[int, int]]:
    w, h = rgb.size
    px = rgb.load()
    row_has_fg = []
    for y in range(h):
        count = 0
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if not is_bg_pixel(r, g, b, min_val=238, max_spread=18):
                count += 1
        row_has_fg.append(count >= 4)
    spans = find_spans_1d(row_has_fg, min_len=120, merge_gap=18)
    if len(spans) == 2:
        mid = (spans[0][1] + spans[1][0]) // 2
        return [(0, mid), (mid, h)]
    return [(0, h // 2), (h // 2, h)]


def compute_col_bounds(rgb_row: Image.Image) -> list[tuple[int, int]]:
    w, h = rgb_row.size
    px = rgb_row.load()
    col_has_fg = []
    for x in range(w):
        count = 0
        for y in range(0, h, 2):
            r, g, b = px[x, y]
            if not is_bg_pixel(r, g, b, min_val=238, max_spread=18):
                count += 1
        col_has_fg.append(count >= 3)
    spans = find_spans_1d(col_has_fg, min_len=80, merge_gap=10)
    if len(spans) == 5:
        bounds: list[tuple[int, int]] = []
        for idx, (sx, ex) in enumerate(spans):
            left = 0 if idx == 0 else (spans[idx - 1][1] + sx) // 2
            right = w if idx == 4 else (ex + spans[idx + 1][0]) // 2
            bounds.append((left, right))
        return bounds
    # Fallback uniforme caso o detector nao encontre 5 blocos exatos
    return [(int(round(i * w / 5)), int(round((i + 1) * w / 5))) for i in range(5)]


def flood_remove_white_bg(cell_rgba: Image.Image) -> Image.Image:
    w, h = cell_rgba.size
    # Adiciona anel branco de 2px em volta para garantir que o flood-fill alcance toda a borda
    padded = Image.new("RGBA", (w + 4, h + 4), (255, 255, 255, 255))
    padded.paste(cell_rgba, (2, 2))
    pw, ph = padded.size
    px = padded.load()

    visited = [[False] * pw for _ in range(ph)]
    queue = deque([(0, 0)])
    visited[0][0] = True

    while queue:
        cx, cy = queue.popleft()
        r, g, b, a = px[cx, cy]
        if a > 0 and is_bg_pixel(r, g, b, min_val=232, max_spread=22):
            px[cx, cy] = (255, 255, 255, 0)
            for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                if 0 <= nx < pw and 0 <= ny < ph and not visited[ny][nx]:
                    visited[ny][nx] = True
                    queue.append((nx, ny))

    # Suavizacao leve apenas na franja externa em contato com pixels ja transparentes
    fringe_updates: list[tuple[int, int, int]] = []
    for y in range(1, ph - 1):
        for x in range(1, pw - 1):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            has_transparent_neighbor = any(
                px[nx, ny][3] == 0
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
            )
            if has_transparent_neighbor:
                mn = min(r, g, b)
                spread = max(r, g, b) - mn
                if mn >= 205 and spread <= 26:
                    # Fades near-white JPEG halo pixels while keeping dark outline intact
                    new_a = max(0, min(220, int((234 - mn) * 7.5)))
                    fringe_updates.append((x, y, new_a))
    for x, y, new_a in fringe_updates:
        r, g, b, _ = px[x, y]
        px[x, y] = (r, g, b, new_a)

    return padded.crop((2, 2, pw - 2, ph - 2))


def count_opaque_border_pixels(img: Image.Image) -> int:
    w, h = img.size
    px = img.load()
    count = 0
    for x in range(w):
        if px[x, 0][3] > 0:
            count += 1
        if px[x, h - 1][3] > 0:
            count += 1
    for y in range(1, h - 1):
        if px[0, y][3] > 0:
            count += 1
        if px[w - 1, y][3] > 0:
            count += 1
    return count


def flood_remove_enclosed_pocket(
    rgba: Image.Image, x0_frac: float, y0_frac: float, x1_frac: float, y1_frac: float
) -> Image.Image:
    """Remove bolsao branco de fundo enclausurado em regiao especifica (ex: entre patas da arara)."""
    w, h = rgba.size
    px = rgba.load()
    visited = [[False] * w for _ in range(h)]
    queue: deque[tuple[int, int]] = deque()
    for y in range(int(h * y0_frac), min(h, int(h * y1_frac))):
        for x in range(int(w * x0_frac), min(w, int(w * x1_frac))):
            r, g, b, a = px[x, y]
            if a > 0 and is_bg_pixel(r, g, b, min_val=238, max_spread=18):
                queue.append((x, y))
                visited[y][x] = True
                break
        if queue:
            break

    while queue:
        cx, cy = queue.popleft()
        r, g, b, a = px[cx, cy]
        if a > 0 and is_bg_pixel(r, g, b, min_val=228, max_spread=24):
            px[cx, cy] = (255, 255, 255, 0)
            for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx]:
                    visited[ny][nx] = True
                    queue.append((nx, ny))
    return rgba


def slice_avatars() -> None:
    if not os.path.exists(SRC_IMAGE):
        raise FileNotFoundError(f"Sprite sheet nao encontrada: {SRC_IMAGE}")

    os.makedirs(OUT_DIR, exist_ok=True)
    src = Image.open(SRC_IMAGE).convert("RGB")
    row_bounds = compute_row_bounds(src)
    print(f"Fonte: {src.size}, linhas={row_bounds}")

    for row_idx, (y0, y1) in enumerate(row_bounds):
        row_rgb = src.crop((0, y0, src.width, y1))
        col_bounds = compute_col_bounds(row_rgb)
        print(f"Linha {row_idx} colunas={col_bounds}")

        for col_idx, (x0, x1) in enumerate(col_bounds):
            name = AVATAR_GRID_NAMES[row_idx][col_idx]
            cell = src.crop((x0, y0, x1, y1)).convert("RGBA")
            clean = flood_remove_white_bg(cell)
            bbox = clean.getbbox()
            if not bbox:
                raise RuntimeError(f"Avatar vazio detectado: {name}")
            cropped = clean.crop(bbox)
            if name == "arara":
                cropped = flood_remove_enclosed_pocket(cropped, 0.50, 0.80, 0.72, 0.92)
            cropped.thumbnail((TARGET_INNER_SIZE, TARGET_INNER_SIZE), Image.Resampling.LANCZOS)

            canvas = Image.new(
                "RGBA",
                (cropped.width + BORDER_PAD * 2, cropped.height + BORDER_PAD * 2),
                (0, 0, 0, 0),
            )
            canvas.paste(cropped, (BORDER_PAD, BORDER_PAD), cropped)

            out_path = os.path.join(OUT_DIR, f"{name}.png")
            canvas.save(out_path, "PNG", optimize=True)
            border_px = count_opaque_border_pixels(canvas)
            print(f"  {name}.png -> {canvas.size}, border_px={border_px}")
            if border_px != 0:
                raise AssertionError(f"{name}.png tem pixels opacos na borda: {border_px}")

            if name == "tucano":
                # Verifica opacidade do peito branco do Tucano (regiao centro-inferior)
                px = canvas.load()
                cw, ch = canvas.size
                opaque_white = 0
                for yy in range(int(ch * 0.35), int(ch * 0.65)):
                    for xx in range(int(cw * 0.25), int(cw * 0.60)):
                        r, g, b, a = px[xx, yy]
                        if a >= 250 and r >= 230 and g >= 230 and b >= 230:
                            opaque_white += 1
                print(f"    tucano_white_chest_opaque_px={opaque_white}")
                if opaque_white < 50:
                    raise AssertionError("Peito branco do Tucano perdeu opacidade!")


if __name__ == "__main__":
    slice_avatars()
