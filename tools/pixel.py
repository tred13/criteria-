"""
tools/pixel.py — pixel-art authoring for "RAYLEIGH RUN".

Draws every sprite pixel by pixel (no vector shapes, no anti-aliasing) and
writes:

  art/pixel/*.png            game-ready sprite sheets + parallax layers
  art/pixelorama/*.pxo       layered Pixelorama projects (pxo_version 8, zip)
  art/pixel/preview.png      contact sheet for review

Palette is limited on purpose (18 colours) so the art reads as one game.
"""
import json
import math
import os
import zipfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "art", "pixel")
PXO = os.path.join(ROOT, "art", "pixelorama")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PXO, exist_ok=True)

# ------------------------------------------------------------------ palette
INK = (27, 27, 46)          # 1b1b2e
INK_SOFT = (52, 54, 78)
SKIN = (255, 207, 168)
SKIN_SH = (224, 163, 124)
SKIN_LT = (255, 232, 208)
HAIR = (91, 53, 33)
HAIR_LT = (138, 82, 51)
HOOD = (63, 127, 224)
HOOD_D = (43, 87, 168)
HOOD_L = (106, 166, 255)
PACK = (255, 194, 46)
PACK_D = (219, 154, 18)
WHITE = (255, 255, 255)
SOCK = (238, 242, 255)
SHOE = (57, 65, 94)
SHOE_L = (86, 95, 128)
GOLD = (255, 214, 64)
RED = (232, 84, 84)
GREEN = (110, 196, 104)
GREEN_D = (66, 143, 74)
DIRT = (138, 96, 62)
DIRT_D = (104, 70, 46)
STONE = (108, 118, 150)
STONE_D = (78, 86, 114)
SKY_TOP = (48, 118, 214)
SKY_MID = (110, 186, 246)
SKY_LOW = (186, 232, 255)

TRANSPARENT = (0, 0, 0, 0)


class Pix:
    """A tiny pixel canvas: every call writes exact pixels, antialiasing off."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [[TRANSPARENT for _ in range(w)] for _ in range(h)]

    # -- primitives ------------------------------------------------
    def set(self, x, y, c):
        if c is None or not (0 <= x < self.w and 0 <= y < self.h):
            return
        self.px[int(y)][int(x)] = c if len(c) == 4 else (c[0], c[1], c[2], 255)

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[int(y)][int(x)]
        return TRANSPARENT

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.set(x, y, c)

    def hline(self, x0, x1, y, c):
        for x in range(int(x0), int(x1) + 1):
            self.set(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(int(y0), int(y1) + 1):
            self.set(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                dx = (x - cx) / max(0.5, rx)
                dy = (y - cy) / max(0.5, ry)
                if dx * dx + dy * dy <= 1.0:
                    self.set(x, y, c)

    def ellipse_line(self, cx, cy, rx, ry, c):
        """1px elliptical ring — used for glasses and outlines."""
        steps = max(24, int((rx + ry) * 6))
        for i in range(steps):
            a = math.pi * 2 * i / steps
            self.set(round(cx + math.cos(a) * rx), round(cy + math.sin(a) * ry), c)

    def disc(self, cx, cy, r, c):
        self.ellipse(cx, cy, r, r, c)

    def ring(self, cx, cy, r, c):
        self.ellipse_line(cx, cy, r, r, c)

    def copy_from(self, src, dx=0, dy=0):
        for y in range(src.h):
            for x in range(src.w):
                p = src.get(x, y)
                if p[3]:
                    self.set(x + dx, y + dy, p)

    # -- helpers ---------------------------------------------------
    def outline(self, c=INK, only_alpha=True):
        """1px silhouette outline — the single biggest readability win in pixel art."""
        add = []
        for y in range(self.h):
            for x in range(self.w):
                if self.get(x, y)[3] != 0:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.w and 0 <= ny < self.h:
                        p = self.get(nx, ny)
                        if p[3] and (not only_alpha or p[:3] != INK[:3]):
                            add.append((x, y))
                            break
        for x, y in add:
            self.set(x, y, c)
        return self

    def shade_right(self, x0, x1, y0, y1, c):
        """Vertical shading ramp on the right side of a shape."""
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                if self.get(x, y)[3]:
                    self.set(x, y, c)

    def image(self):
        im = Image.new("RGBA", (self.w, self.h))
        im.putdata([self.px[y][x] for y in range(self.h) for x in range(self.w)])
        return im


# ------------------------------------------------------------------ the kid
def _line(c, x0, y0, x1, y1, thick=1, col=SKIN):
    """Thick pixel line — keeps limbs connected to the body (no floating arms)."""
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        for oy in range(thick):
            for ox in range(thick):
                c.set(x0 + ox - thick // 2, y0 + oy - thick // 2, col)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def draw_kid(frame="idle0"):
    """32x32 chibi: big head, round glasses, blue hoodie, yellow pack."""
    c = Pix(32, 32)

    # ---- pose table: hands, feet, bob (hand-keyed on 1px steps) ------
    if frame == "idle0":
        bob, lean = 0, 0
        hl, hr = (7, 22), (24, 22)
        fl, fr = (12, 30), (19, 30)
    elif frame == "idle1":
        bob, lean = 1, 0
        hl, hr = (7, 23), (24, 23)
        fl, fr = (12, 31), (19, 31)
    elif frame == "run0":
        bob, lean = 0, 1
        hl, hr = (5, 20), (25, 25)
        fl, fr = (9, 29), (21, 28)
    elif frame == "run1":
        bob, lean = -1, 1
        hl, hr = (6, 24), (24, 20)
        fl, fr = (13, 27), (18, 30)
    elif frame == "run2":
        bob, lean = 0, 1
        hl, hr = (25, 20), (5, 25)
        fl, fr = (21, 29), (9, 28)
    elif frame == "run3":
        bob, lean = -1, 1
        hl, hr = (24, 24), (6, 20)
        fl, fr = (18, 27), (13, 30)
    elif frame == "jump":
        bob, lean = -3, 0
        hl, hr = (5, 15), (26, 15)
        fl, fr = (11, 27), (20, 26)
    elif frame == "fall":
        bob, lean = 1, 0
        hl, hr = (5, 21), (26, 21)
        fl, fr = (11, 30), (20, 29)
    else:
        raise ValueError(frame)

    B = bob
    hip_y = 24 + B
    sh_y = 17 + B
    head_y = 9 + B + lean   # centre of the face

    # ---- legs: hip -> foot, then a shoe slab ------------------------
    for (fx, fy), hipx in ((fl, 12), (fr, 19)):
        _line(c, hipx, hip_y, fx, fy - 2, 2, SKIN)
        c.rect(min(fx, fx + 1), fy - 2, max(fx, fx + 1) + 1, fy - 1, SOCK)
        c.rect(fx - 1, fy, fx + 2, fy + 1, SHOE)
        c.hline(fx - 1, fx + 2, fy + 1, SHOE_L)

    # ---- backpack (behind torso) -----------------------------------
    c.rect(5, sh_y - 1, 9, hip_y - 1, PACK)
    c.hline(5, 9, sh_y - 1, PACK_D)
    c.vline(5, sh_y - 1, hip_y - 1, PACK_D)
    c.rect(7, sh_y + 3, 8, sh_y + 5, PACK_D)

    # ---- torso: hoodie ---------------------------------------------
    c.rect(10, sh_y, 21, hip_y, HOOD)
    c.hline(10, 21, sh_y, HOOD_L)
    c.vline(21, sh_y, hip_y, HOOD_D)
    c.vline(10, sh_y, hip_y, HOOD_D)
    c.rect(9, hip_y - 2, 22, hip_y + 1, HOOD_D)      # shorts
    c.hline(9, 22, hip_y + 1, INK_SOFT)
    c.vline(15, sh_y + 2, sh_y + 5, HOOD_L)          # drawstring
    c.set(15, sh_y + 5, WHITE)
    c.rect(13, hip_y - 4, 18, hip_y - 3, INK_SOFT)   # pocket
    c.rect(11, sh_y + 2, 12, sh_y + 4, HOOD_L)       # chest highlight

    # ---- arms: shoulder -> hand, hand pixel in skin ----------------
    for (hx, hy), shx in ((hl, 11), (hr, 20)):
        _line(c, shx, sh_y + 1, hx, hy - 1, 2, HOOD_D)
        c.rect(hx, hy, hx + 1, hy + 1, SKIN)
        c.set(hx + 1, hy + 1, SKIN_SH)

    # ---- neck + head ------------------------------------------------
    c.rect(14, head_y + 6, 17, sh_y + 1, SKIN_SH)
    c.ellipse(15.5, head_y, 8.6, 7.6, SKIN)
    c.ellipse(17.2, head_y + 2.2, 6.4, 4.6, SKIN)               # cheek volume
    c.hline(9, 22, head_y + 6, SKIN_SH)                         # jaw shade
    c.set(8, head_y + 2, SKIN_SH)
    c.set(23, head_y + 2, SKIN_SH)

    # ---- hair: dome + fringe spikes (sits above the brow line) -------
    c.ellipse(15.5, head_y - 4.6, 9.0, 5.0, HAIR)
    c.rect(7, head_y - 5, 24, head_y - 3, HAIR)
    for sx in (8, 12, 16, 20, 23):
        c.set(sx, head_y - 2, HAIR)
    c.set(9, head_y - 7, HAIR)
    c.set(20, head_y - 8, HAIR)
    c.set(21, head_y - 7, HAIR)
    c.set(22, head_y - 6, HAIR)
    c.hline(11, 19, head_y - 7, HAIR_LT)                        # sheen
    c.set(12, head_y - 6, HAIR_LT)
    c.set(18, head_y - 6, HAIR_LT)

    # ---- glasses: 7px lens, 3px pupil, 2px bridge -------------------
    blink = frame == "idle1"
    for gx in (11.5, 20.5):
        c.ellipse_line(gx, head_y + 1, 3.6, 3.4, INK)
        c.ellipse(gx, head_y + 1, 2.7, 2.5, WHITE)
        if blink:
            c.hline(int(gx) - 2, int(gx) + 2, head_y + 1, INK)
            c.set(int(gx), head_y + 2, INK)
        else:
            c.rect(int(gx) - 1, head_y, int(gx) + 1, head_y + 2, INK)
            c.set(int(gx) - 1, head_y, WHITE)
    c.hline(15, 17, head_y + 1, INK)
    c.set(7, head_y + 1, INK)
    c.set(25, head_y + 1, INK)

    # ---- mouth / brows / cheeks ------------------------------------
    if frame in ("jump", "run1", "run3"):
        c.rect(15, head_y + 5, 17, head_y + 6, INK)
        c.set(16, head_y + 6, (168, 66, 78))
    else:
        c.hline(15, 17, head_y + 5, INK)
        c.set(14, head_y + 5, INK)
        c.set(18, head_y + 5, INK)
    c.set(10, head_y + 4, (255, 158, 148))
    c.set(21, head_y + 4, (255, 158, 148))

    c.outline(INK)
    return c


# ------------------------------------------------------------------ tiles
def draw_tiles(name):
    c = Pix(16, 16)
    if name == "grass":
        c.rect(0, 0, 15, 4, GREEN)
        c.hline(0, 15, 0, (140, 220, 128))
        for x in (2, 6, 11, 14):
            c.set(x, 0, GREEN_D)
        c.rect(0, 5, 15, 15, DIRT)
        for x in range(16):
            for y in range(6, 16):
                if (x * 7 + y * 13) % 11 == 0:
                    c.set(x, y, DIRT_D)
        c.hline(0, 15, 5, GREEN_D)
        c.set(3, 8, DIRT_D)
        c.set(12, 11, DIRT_D)
    elif name == "dirt":
        c.rect(0, 0, 15, 15, DIRT)
        for x in range(16):
            for y in range(16):
                if (x * 5 + y * 7) % 9 == 0:
                    c.set(x, y, DIRT_D)
        c.hline(0, 15, 0, (158, 114, 76))
    elif name == "stone":
        c.rect(0, 0, 15, 15, STONE)
        c.hline(0, 15, 0, (132, 142, 176))
        c.hline(0, 15, 15, STONE_D)
        for x in range(16):
            for y in range(16):
                if (x * 11 + y * 3) % 17 == 0:
                    c.set(x, y, STONE_D)
        c.vline(8, 2, 12, STONE_D)
    elif name == "cloud":
        c.ellipse(5, 9, 5, 5, WHITE)
        c.ellipse(11, 9, 5, 5, WHITE)
        c.rect(3, 9, 13, 13, WHITE)
        c.set(6, 12, (206, 226, 248))
        c.set(10, 13, (206, 226, 248))
        c.outline((166, 196, 232))
    return c


# ------------------------------------------------------------------ props
def draw_orb(t):
    c = Pix(12, 12)
    c.disc(5.5, 5.5, 4.6, GOLD)
    c.disc(5.5, 5.5, 3.0, (255, 240, 150))
    c.set(4, 4, WHITE)
    c.set(7, 7, (226, 176, 24))
    if t:
        for a in range(4):
            ang = math.pi / 2 * a + math.pi / 4
            c.set(round(5.5 + math.cos(ang) * 5.4), round(5.5 + math.sin(ang) * 5.4), WHITE)
    c.outline(INK)
    return c


def draw_spike():
    c = Pix(16, 12)
    for y in range(12):
        half = int(y * 7 / 11)
        c.hline(7 - half, 8 + half, y, RED)
    c.vline(7, 1, 11, (255, 140, 140))
    c.outline(INK)
    return c


def draw_heart(full=True):
    c = Pix(9, 9)
    col = RED if full else (120, 70, 80)
    c.rect(1, 2, 3, 3, col)
    c.rect(5, 2, 7, 3, col)
    c.rect(0, 3, 8, 4, col)
    c.rect(1, 5, 7, 5, col)
    c.rect(2, 6, 6, 6, col)
    c.rect(3, 7, 5, 7, col)
    c.set(2, 3, (255, 170, 170) if full else col)
    c.outline(INK)
    return c


# ------------------------------------------------------------------ parallax
def draw_sky(w=320, h=180):
    c = Pix(w, h)
    for y in range(h):
        t = y / (h - 1)
        if t < 0.55:
            k = t / 0.55
            col = tuple(round(SKY_TOP[i] + (SKY_MID[i] - SKY_TOP[i]) * k) for i in range(3))
        else:
            k = (t - 0.55) / 0.45
            col = tuple(round(SKY_MID[i] + (SKY_LOW[i] - SKY_MID[i]) * k) for i in range(3))
        c.hline(0, w - 1, y, col)
    # dithered banding keeps the gradient in the 18-colour look
    for y in range(0, h, 2):
        for x in range((y // 2) % 3, w, 3):
            p = c.get(x, y)
            c.set(x, y, tuple(max(0, v - 4) for v in p[:3]))
    # sun
    c.disc(258, 40, 16, (255, 224, 120))
    c.disc(258, 40, 12, (255, 244, 180))
    for i in range(8):
        a = math.pi * 2 * i / 8
        c.set(round(258 + math.cos(a) * 20), round(40 + math.sin(a) * 20), (255, 236, 150))
    return c


def draw_hills(w=320, h=180, far=True):
    c = Pix(w, h)
    col = (120, 176, 208) if far else (86, 158, 128)
    base = 118 if far else 140
    for x in range(w):
        y = base + int(14 * math.sin(x / 46.0 + (0.0 if far else 2.0)) +
                       8 * math.sin(x / 17.0))
        c.vline(x, y, h - 1, col)
    if not far:
        for x in range(w):
            y = base + int(14 * math.sin(x / 46.0 + 2.0) + 8 * math.sin(x / 17.0))
            c.set(x, y, (120, 196, 152))
    return c


def draw_clouds(w=320, h=180):
    c = Pix(w, h)
    for (cx, cy, s) in ((40, 46, 1.0), (150, 30, 0.8), (250, 62, 0.6), (300, 40, 0.9)):
        rx, ry = 18 * s, 8 * s
        c.ellipse(cx, cy, rx, ry, WHITE)
        c.ellipse(cx - rx * 0.6, cy + 2, rx * 0.55, ry * 0.8, WHITE)
        c.ellipse(cx + rx * 0.6, cy + 2, rx * 0.5, ry * 0.7, WHITE)
        c.ellipse(cx, cy - ry * 0.5, rx * 0.6, ry * 0.7, WHITE)
        for x in range(int(cx - rx), int(cx + rx)):
            c.set(x, int(cy + ry), (206, 226, 248))
    return c


# ------------------------------------------------------------------ sheets
KID_FRAMES = ["idle0", "idle1", "run0", "run1", "run2", "run3", "jump", "fall"]


def write_sheets():
    # character sheet: 8 frames, 32px each
    sheet = Image.new("RGBA", (32 * len(KID_FRAMES), 32), TRANSPARENT)
    for i, f in enumerate(KID_FRAMES):
        sheet.alpha_composite(draw_kid(f).image(), (i * 32, 0))
    sheet.save(os.path.join(OUT, "kid.png"))

    # tileset: 16px grid, 4 tiles
    names = ["grass", "dirt", "stone", "cloud"]
    ts = Image.new("RGBA", (16 * len(names), 16), TRANSPARENT)
    for i, n in enumerate(names):
        ts.alpha_composite(draw_tiles(n).image(), (i * 16, 0))
    ts.save(os.path.join(OUT, "tiles.png"))

    # props
    props = Image.new("RGBA", (64, 32), TRANSPARENT)
    props.alpha_composite(draw_orb(0).image(), (0, 0))
    props.alpha_composite(draw_orb(1).image(), (14, 0))
    props.alpha_composite(draw_spike().image(), (28, 0))
    props.alpha_composite(draw_heart(True).image(), (46, 2))
    props.alpha_composite(draw_heart(False).image(), (46, 14))
    props.save(os.path.join(OUT, "props.png"))

    draw_sky().image().save(os.path.join(OUT, "bg_sky.png"))
    draw_hills(320, 180, True).image().save(os.path.join(OUT, "bg_hills_far.png"))
    draw_hills(320, 180, False).image().save(os.path.join(OUT, "bg_hills_near.png"))
    draw_clouds(320, 180).image().save(os.path.join(OUT, "bg_clouds.png"))
    return sheet


# ------------------------------------------------------------------ pixelorama
def write_pxo(path, size, fps, layers, frames, name):
    """Write a Pixelorama 1.x project: a zip with data.json + image_data/."""
    layer_meta = []
    for i, (lname, visible) in enumerate(layers):
        layer_meta.append({
            "name": lname,
            "visible": visible,
            "locked": False,
            "blend_mode": 0,
            "clipping_mask": False,
            "opacity": 1,
            "parent": -1,
            "effects": [],
            "type": 0,
            "new_cels_linked": False,
            "animated_params": "{}",
            "metadata": {},
        })

    frame_meta = []
    for fr in frames:                       # list of list-of-Pix (one per layer)
        cels = []
        for _ in fr:
            cels.append({"opacity": 1, "z_index": 0,
                         "image_size": "(%d, %d)" % (size, size), "metadata": {}})
        frame_meta.append({"cels": cels, "duration": 1.0, "metadata": {}})

    data = {
        "pixelorama_version": "v1.0.4-stable",
        "pxo_version": 8,
        "size_x": size,
        "size_y": size,
        "color_mode": "RGBA8",
        "tile_mode_x_basis_x": size, "tile_mode_x_basis_y": 0,
        "tile_mode_y_basis_x": 0, "tile_mode_y_basis_y": size,
        "layers": layer_meta,
        "next_keyframe_id": 0,
        "tags": [{"name": name, "color": (0.4, 0.8, 1.0, 1.0),
                  "from": 0, "to": len(frames) - 1}],
        "guides": [],
        "symmetry_points": [size - 1, size - 1],
        "frames": frame_meta,
        "current_frame": 0,
        "current_layer": 0,
        "brushes": [],
        "palettes": [{"Default": json.dumps({
            "name": "RAYLEIGH 18",
            "colors": [list(c) for c in PALETTE]})}],
        "project_current_palette_name": "Default",
        "reference_images": [],
        "tilesets": [],
        "vanishing_points": [],
        "fps": fps,
        "include_blended_images": False,
        "license": "",
        "user_data": "",
        "author_display_name": "RAYLEIGH RUN",
        "author_real_name": "",
        "author_contact": "",
        "author_company": "",
        "metadata": {},
        "export_profile": {},
    }

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("data.json", json.dumps(data, indent=1))
        for fi, fr in enumerate(frames, start=1):
            for li, pix in enumerate(fr, start=1):
                buf = b"".join(bytes(pix.px[y][x]) for y in range(size) for x in range(size))
                z.writestr("image_data/frames/%d/layer_%d" % (fi, li), buf)


PALETTE = [INK, INK_SOFT, SKIN, SKIN_SH, SKIN_LT, HAIR, HAIR_LT, HOOD, HOOD_D, HOOD_L,
           PACK, PACK_D, WHITE, SOCK, SHOE, SHOE_L, GOLD, RED, GREEN, GREEN_D]


def kid_layers(frame):
    """Split a frame into Pixelorama layers: legs / body / hair / glasses."""
    full = draw_kid(frame)
    legs = Pix(32, 32)
    body = Pix(32, 32)
    hair = Pix(32, 32)
    eyes = Pix(32, 32)
    for y in range(32):
        for x in range(32):
            p = full.get(x, y)
            if not p[3]:
                continue
            if p[:3] == HAIR[:3] or p[:3] == HAIR_LT[:3]:
                hair.set(x, y, p)
            elif p[:3] == WHITE[:3] and 4 <= y <= 11 and 7 <= x <= 24:
                eyes.set(x, y, p)
            elif y >= 24 or p[:3] in (SOCK[:3], SHOE[:3], SHOE_L[:3]):
                legs.set(x, y, p)
            else:
                body.set(x, y, p)
    return [legs, body, hair, eyes]


def build_pxo():
    frames = [kid_layers(f) for f in KID_FRAMES]
    write_pxo(os.path.join(PXO, "kid.pxo"), 32, 10,
              [("legs", True), ("body", True), ("hair", True), ("glasses", True)],
              frames, "kid")

    # tiles project: one layer per tile, single frame
    tiles = [draw_tiles(n) for n in ("grass", "dirt", "stone", "cloud")]
    write_pxo(os.path.join(PXO, "tiles.pxo"), 16, 10,
              [("tile_%d" % i, True) for i in range(4)],
              [[t] for t in tiles], "tiles")


def preview(sheet):
    w, h = 760, 300
    im = Image.new("RGBA", (w, h), (34, 36, 56, 255))
    big = sheet.resize((sheet.width * 5, sheet.height * 5), Image.NEAREST)
    im.alpha_composite(big, (8, 8))
    ts = Image.open(os.path.join(OUT, "tiles.png"))
    ts = ts.resize((ts.width * 5, ts.height * 5), Image.NEAREST)
    im.alpha_composite(ts, (8, 190))
    pr = Image.open(os.path.join(OUT, "props.png"))
    pr = pr.resize((pr.width * 4, pr.height * 4), Image.NEAREST)
    im.alpha_composite(pr, (340, 190))
    im.convert("RGB").save(os.path.join(OUT, "preview.png"))


if __name__ == "__main__":
    sheet = write_sheets()
    build_pxo()
    preview(sheet)
    print("wrote", len(os.listdir(OUT)), "files to", OUT)
    print("wrote", os.listdir(PXO), "to", PXO)
