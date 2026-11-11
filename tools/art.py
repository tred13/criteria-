"""
art.py — layered vector-art generator for "WHY IS THE SKY BLUE?"
Everything is drawn at 4x supersampling and downsampled: crisp, anti-aliased,
print-quality flat-vector cartoon art (Krita/Inkscape-grade look), rendered
purely with code so the whole pipeline is reproducible.

Coordinate system: every part is drawn on its own local canvas with an explicit
pivot point, so Godot can rotate/scale it like a real cut-out puppet.
"""
import math
import os
from PIL import Image, ImageDraw, ImageFilter, ImageChops

S = 4  # supersample
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
FONT_DIR = os.path.join(ROOT, "art", "fonts")


# ------------------------------------------------------------------ palette
INK        = (26, 27, 38, 255)
INK_SOFT   = (58, 62, 84, 255)
SKIN       = (255, 208, 173, 255)
SKIN_SH    = (232, 168, 133, 255)
SKIN_LT    = (255, 227, 203, 255)
HAIR       = (96, 56, 34, 255)
HAIR_LT    = (134, 82, 52, 255)
HAIR_DK    = (63, 36, 22, 255)
HOOD       = (58, 118, 214, 255)
HOOD_D     = (40, 84, 168, 255)
HOOD_L     = (86, 148, 236, 255)
DENIM      = (52, 78, 128, 255)
DENIM_D    = (38, 58, 98, 255)
PACK_Y     = (255, 197, 46, 255)
PACK_Y_D   = (226, 160, 22, 255)
WHITE      = (255, 255, 255, 255)
SUN_Y      = (255, 205, 41, 255)
SUN_Y_D    = (240, 168, 16, 255)
CHEEK      = (255, 141, 133, 120)

RAINBOW = [
    (255, 61, 82, 255),    # red
    (255, 138, 41, 255),   # orange
    (255, 224, 51, 255),   # yellow
    (64, 214, 116, 255),   # green
    (46, 168, 255, 255),   # blue
    (61, 90, 254, 255),    # indigo
    (163, 92, 255, 255),   # violet
]


def C(rgb, a=255):
    return (rgb[0], rgb[1], rgb[2], a)


FONT_WEIGHT = {"Baloo2": "ExtraBold", "Fredoka": "Bold", "Bungee": None,
               "PermanentMarker": None}


def font(name, size, weight=None):
    from PIL import ImageFont
    f = ImageFont.truetype(os.path.join(FONT_DIR, name + ".ttf"), int(size * S))
    w = weight or FONT_WEIGHT.get(name)
    if w:
        try:
            f.set_variation_by_name(w)
        except Exception:
            pass
    return f


# ------------------------------------------------------------------ canvas
class Canvas:
    """Local canvas drawn at S x supersampling, exposed with a pivot."""

    def __init__(self, w, h, pivot=None, pad=0):
        self.w, self.h = int(w), int(h)
        self.pad = pad
        self.pivot = pivot if pivot else (self.w / 2.0, self.h / 2.0)
        self.img = Image.new("RGBA", (self.w * S, self.h * S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    # ---- coordinate helpers (accept floats in local units)
    def _p(self, pts):
        return [(x * S, y * S) for x, y in pts]

    def ellipse(self, box, fill=None, outline=None, width=0):
        self.d.ellipse([box[0] * S, box[1] * S, box[2] * S, box[3] * S],
                       fill=fill, outline=outline, width=int(width * S))

    def circle(self, cx, cy, r, fill=None, outline=None, width=0):
        self.ellipse((cx - r, cy - r, cx + r, cy + r), fill, outline, width)

    def round_rect(self, box, radius, fill=None, outline=None, width=0):
        self.d.rounded_rectangle([box[0] * S, box[1] * S, box[2] * S, box[3] * S],
                                 radius=radius * S, fill=fill, outline=outline,
                                 width=int(width * S))

    def rect(self, box, fill=None, outline=None, width=0):
        self.d.rectangle([box[0] * S, box[1] * S, box[2] * S, box[3] * S],
                         fill=fill, outline=outline, width=int(width * S))

    def poly(self, pts, fill=None, outline=None, width=0):
        self.d.polygon(self._p(pts), fill=fill, outline=outline,
                       width=int(width * S))

    def line(self, pts, fill, width, joint="curve"):
        self.d.line(self._p(pts), fill=fill, width=int(width * S), joint=joint)

    def arc(self, box, a0, a1, fill, width):
        self.d.arc([box[0] * S, box[1] * S, box[2] * S, box[3] * S], a0, a1,
                   fill=fill, width=int(width * S))

    def pieslice(self, box, a0, a1, fill=None, outline=None, width=0):
        self.d.pieslice([box[0] * S, box[1] * S, box[2] * S, box[3] * S], a0, a1,
                        fill=fill, outline=outline, width=int(width * S))

    def chamfer_rect(self, box, ch, fill=None, outline=None, width=0):
        x0, y0, x1, y1 = box
        pts = [(x0 + ch, y0), (x1 - ch, y0), (x1, y0 + ch), (x1, y1 - ch),
               (x1 - ch, y1), (x0 + ch, y1), (x0, y1 - ch), (x0, y0 + ch)]
        self.poly(pts, fill, outline, width)

    # ---- shading helpers
    def shade_gradient(self, box, top, bottom, radius=0, horizontal=False):
        """Soft vertical/horizontal gradient inside a rounded rect or ellipse."""
        x0, y0, x1, y1 = [v * S for v in box]
        w, h = max(1, int(x1 - x0)), max(1, int(y1 - y0))
        g = Image.new("RGBA", (w, h))
        gd = ImageDraw.Draw(g)
        n = h if not horizontal else w
        for i in range(n):
            k = i / max(1, n - 1)
            col = tuple(int(top[j] + (bottom[j] - top[j]) * k) for j in range(4))
            if horizontal:
                gd.line([(i, 0), (i, h)], fill=col)
            else:
                gd.line([(0, i), (w, i)], fill=col)
        # mask against the region AND the artwork alpha so nothing spills out
        reg = Image.new("L", (w, h), 0)
        rd = ImageDraw.Draw(reg)
        if radius:
            rd.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius * S, fill=255)
        else:
            rd.rectangle([0, 0, w - 1, h - 1], fill=255)
        art = self.img.crop((int(x0), int(y0), int(x0) + w, int(y0) + h)).split()[3]
        mask = ImageChops.multiply(reg, art)
        self.img.paste(g, (int(x0), int(y0)), mask)

    def soft_shadow(self, offset=(6, 8), blur=10, color=(20, 20, 40, 90)):
        """Adds a soft shadow derived from the current silhouette."""
        alpha = self.img.split()[3]
        sh = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        col = Image.new("RGBA", self.img.size, color)
        sh.paste(col, (int(offset[0] * S), int(offset[1] * S)), alpha)
        sh = sh.filter(ImageFilter.GaussianBlur(blur * S / 2.0))
        out = Image.alpha_composite(sh, self.img)
        self.img = out
        self.d = ImageDraw.Draw(self.img)

    # ---- clipping (keep shading inside the part silhouette)
    def clip_begin(self):
        self._snap = self.img.split()[3].copy()

    def clip_end(self):
        if not hasattr(self, "_snap"):
            return
        a = self.img.split()[3]
        self.img.putalpha(ImageChops.multiply(a, self._snap))
        self.d = ImageDraw.Draw(self.img)
        del self._snap

    # ---- text
    def text(self, xy, s, f, fill, anchor="mm", stroke=0, stroke_fill=None):
        self.d.text((xy[0] * S, xy[1] * S), s, font=f, fill=fill, anchor=anchor,
                    stroke_width=int(stroke * S), stroke_fill=stroke_fill)

    # ---- output
    def result(self):
        return self.img.resize((self.w, self.h), Image.LANCZOS)

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.result().save(path)
        return path


def new_bg(w, h):
    c = Canvas(w, h, pad=0)
    return c


# ================================================================== SUNNY
# Proportions (local units, character ~ 460 tall standing)
HEAD_R = 96
HEAD_Y = -330          # head centre relative to hips origin
SHOULDER_Y = -218
HIP_Y = -40


def draw_head(mouth="smile", eyes="open", brow="none", look=(0, 0), cx=None, cy=None):
    """Head part, pivot at the neck (bottom centre)."""
    W, H = 300, 320
    c = Canvas(W, H, pivot=(W / 2, H - 22))
    ox, oy = W / 2, 150   # head centre on the canvas

    # ears
    for sx in (-1, 1):
        ex = ox + sx * (HEAD_R - 12)
        c.circle(ex, oy + 22, 21, SKIN, INK, 6)
        c.arc((ex - 12, oy + 12, ex + 12, oy + 36),
              200 if sx < 0 else 340, 340 if sx < 0 else 480, SKIN_SH, 4)

    # neck
    c.round_rect((ox - 30, oy + HEAD_R - 40, ox + 30, oy + HEAD_R + 26), 12, SKIN)
    c.rect((ox - 30, oy + HEAD_R - 6, ox + 30, oy + HEAD_R + 20), fill=SKIN_SH)
    c.round_rect((ox - 30, oy + HEAD_R - 40, ox + 30, oy + HEAD_R + 26), 12, None, INK, 5)

    # skull
    c.circle(ox, oy, HEAD_R, SKIN, INK, 6)
    # jaw shading
    c.arc((ox - HEAD_R + 14, oy - HEAD_R + 40, ox + HEAD_R - 14, oy + HEAD_R + 6), 30, 150, SKIN_SH, 7)
    # blush
    for sx in (-1, 1):
        c.ellipse((ox + sx * 56 - 24, oy + 34, ox + sx * 56 + 24, oy + 54), CHEEK)

    # ---- ears inner done above
    # ---- hair: rounded cap with a swooping fringe
    cap = [(ox - HEAD_R - 4, oy + 6), (ox - HEAD_R - 4, oy - 34),
           (ox - 78, oy - 84), (ox - 26, oy - 104), (ox + 34, oy - 100),
           (ox + 82, oy - 72), (ox + HEAD_R + 4, oy - 18), (ox + HEAD_R + 4, oy + 6)]
    c.poly(cap, HAIR)
    c.pieslice((ox - HEAD_R - 4, oy - HEAD_R - 14, ox + HEAD_R + 4, oy + 26), 180, 360, HAIR)
    # fringe locks (three soft tufts sweeping right)
    c.pieslice((ox - 104, oy - 78, ox - 16, oy + 22), 200, 20, HAIR)
    c.pieslice((ox - 46, oy - 96, ox + 46, oy + 6), 195, 10, HAIR)
    c.pieslice((ox + 12, oy - 88, ox + 104, oy + 12), 190, 5, HAIR)
    # highlight streak
    c.arc((ox - 74, oy - 112, ox + 26, oy - 40), 205, 305, HAIR_LT, 9)
    c.circle(ox + 30, oy - 88, 10, HAIR_LT)
    # dark underside of the cap for depth
    c.arc((ox - HEAD_R + 2, oy - HEAD_R - 8, ox + HEAD_R - 2, oy + 30), 20, 160, HAIR_DK, 6)
    # outline
    c.line(cap + [cap[0]], INK, 6)
    c.arc((ox - HEAD_R - 4, oy - HEAD_R - 14, ox + HEAD_R + 4, oy + 26), 180, 360, INK, 6)

    # ---- brows
    if brow == "up":
        c.line([(ox - 66, oy - 44), (ox - 22, oy - 54)], INK, 7)
        c.line([(ox + 22, oy - 54), (ox + 66, oy - 44)], INK, 7)
    elif brow == "sad":
        c.line([(ox - 66, oy - 52), (ox - 22, oy - 40)], INK, 7)
        c.line([(ox + 22, oy - 40), (ox + 66, oy - 52)], INK, 7)

    # ---- glasses + eyes
    gr = 46
    for sx in (-1, 1):
        gx, gy = ox + sx * 47, oy + 6
        # lens
        c.circle(gx, gy, gr, (255, 255, 255, 235), INK, 7)
        if eyes == "open":
            ex = gx + look[0]
            ey = gy + look[1]
            c.circle(ex, ey, 25, WHITE)
            c.circle(ex + look[0] * 0.4, ey + look[1] * 0.4, 14, INK)
            c.circle(ex - 6 + look[0] * 0.4, ey - 7 + look[1] * 0.4, 5, WHITE)
            c.arc((ex - 25, ey - 25, ex + 25, ey + 25), 200, 260, (150, 150, 170, 255), 3)
        elif eyes == "half":
            c.ellipse((gx - 26, gy + 2, gx + 26, gy + 26), INK)
            c.arc((gx - 26, gy - 24, gx + 26, gy + 24), 180, 360, INK, 7)
        elif eyes == "closed":
            c.arc((gx - 26, gy - 14, gx + 26, gy + 22), 20, 160, INK, 8)
        elif eyes == "wide":
            c.circle(gx, gy, 30, WHITE)
            c.circle(gx + look[0], gy + look[1], 16, INK)
            c.circle(gx - 8, gy - 8, 6, WHITE)
        # glint
        c.circle(gx - 16, gy - 18, 8, (255, 255, 255, 150))
    # bridge + arms
    c.line([(ox - 6, oy + 4), (ox + 6, oy + 4)], INK, 7)
    c.line([(ox - 47 - gr, oy + 2), (ox - 88, oy - 2)], INK, 6)
    c.line([(ox + 47 + gr, oy + 2), (ox + 88, oy - 2)], INK, 6)

    # ---- mouth
    if mouth == "smile":
        c.arc((ox - 30, oy + 46, ox + 30, oy + 88), 20, 160, INK, 7)
    elif mouth == "grin":
        c.pieslice((ox - 34, oy + 44, ox + 34, oy + 94), 0, 180, (150, 52, 62, 255), INK, 5)
        c.pieslice((ox - 22, oy + 62, ox + 22, oy + 96), 0, 180, (255, 128, 138, 255))
    elif mouth == "open":
        c.ellipse((ox - 26, oy + 50, ox + 26, oy + 96), (124, 40, 52, 255), INK, 5)
        c.ellipse((ox - 14, oy + 76, ox + 14, oy + 94), (255, 120, 130, 255))
    elif mouth == "o":
        c.ellipse((ox - 18, oy + 52, ox + 18, oy + 88), (124, 40, 52, 255), INK, 5)
    # nose
    c.arc((ox - 12, oy + 26, ox + 12, oy + 48), 200, 340, SKIN_SH, 5)

    return c


def draw_body():
    """Hoodie torso + denim shorts. Pivot = hip centre (bottom of the canvas)."""
    W, H = 340, 280
    c = Canvas(W, H, pivot=(W / 2, 250))
    ox, top = W / 2, 26

    sil = [(-84, 44), (-102, 118), (-84, 236), (84, 236), (102, 118), (84, 44)]
    sil = [(ox + x, top + y) for x, y in sil]
    c.ellipse((ox - 100, top + 10, ox + 100, top + 98), HOOD)   # shoulder cap
    c.poly(sil, HOOD)
    c.rect((ox - 96, top + 86, ox + 96, 232), HOOD)

    c.clip_begin()
    c.ellipse((ox - 130, top + 30, ox + 30, 228), HOOD_D)
    c.ellipse((ox + 26, top + 24, ox + 128, 152), HOOD_L)
    c.ellipse((ox - 120, 168, ox + 120, 250), HOOD_D)
    c.clip_end()

    # hood collar behind the neck
    c.ellipse((ox - 62, top + 2, ox + 62, top + 64), HOOD_D, INK, 6)
    c.ellipse((ox - 44, top + 14, ox + 44, top + 50), (33, 70, 142, 255))

    c.line([sil[1], sil[2], sil[3], sil[4]], INK, 7)
    c.arc((ox - 100, top + 10, ox + 100, top + 98), 180, 360, INK, 7)
    c.line([(ox - 96, top + 52), sil[1]], INK, 7)
    c.line([(ox + 96, top + 52), sil[4]], INK, 7)

    c.line([(ox, top + 62), (ox, 212)], C(HOOD_D, 220), 5)
    for sx in (-1, 1):
        c.line([(ox + sx * 34, top + 56), (ox + sx * 38, top + 122)], (238, 244, 255, 255), 7)
        c.circle(ox + sx * 38, top + 126, 9, (238, 244, 255, 255), INK_SOFT, 3)
    c.poly([(ox - 64, top + 136), (ox - 64, top + 182), (ox - 30, top + 200),
            (ox + 30, top + 200), (ox + 64, top + 182), (ox + 64, top + 136)],
           None, HOOD_D, 6)

    # shorts
    c.round_rect((ox - 84, 198, ox + 84, 266), 24, DENIM, INK, 7)
    c.clip_begin()
    c.round_rect((ox - 84, 242, ox + 84, 266), 12, DENIM_D)
    c.clip_end()
    c.line([(ox, 208), (ox, 252)], C(DENIM_D, 255), 6)
    for sx in (-1, 1):
        c.arc((ox + sx * 50 - 24, 206, ox + sx * 50 + 24, 258),
              250 if sx < 0 else 290, 470 if sx < 0 else 350, C((96, 126, 186, 255)), 5)
    c.round_rect((ox - 88, 258, ox + 88, 274), 10, DENIM_D, INK, 5)
    c.circle(ox, 220, 6, (222, 186, 106, 255), INK_SOFT, 3)
    return c


def draw_arm_upper():
    """Upper arm sleeve, pivot at the shoulder (top centre)."""
    W, H = 120, 180
    c = Canvas(W, H, pivot=(W / 2, 20))
    ox = W / 2
    c.round_rect((ox - 26, 16, ox + 26, 152), 24, HOOD)
    c.clip_begin()
    c.round_rect((ox - 28, 20, ox - 4, 154), 18, HOOD_D)
    c.round_rect((ox + 8, 20, ox + 28, 110), 18, HOOD_L)
    c.clip_end()
    c.round_rect((ox - 26, 20, ox + 26, 150), 24, None, INK, 6)
    c.clip_begin(); c.round_rect((ox + 4, 24, ox + 26, 96), 18, HOOD_L); c.clip_end()
    return c


def draw_arm_fore():
    """Forearm + hand, pivot at the elbow (top centre)."""
    W, H = 120, 200
    c = Canvas(W, H, pivot=(W / 2, 22))
    ox = W / 2
    c.round_rect((ox - 26, 20, ox + 26, 96), 24, HOOD_D, INK, 6)   # cuff
    c.clip_begin()
    c.round_rect((ox - 28, 20, ox + 4, 98), 18, (32, 70, 146, 255))
    c.clip_end()
    # hand
    c.ellipse((ox - 26, 92, ox + 26, 152), SKIN, INK, 6)
    c.ellipse((ox - 32, 100, ox - 6, 136), SKIN, INK, 5)
    c.ellipse((ox - 16, 100, ox + 6, 124), SKIN_LT)
    c.arc((ox - 20, 114, ox + 18, 148), 20, 130, SKIN_SH, 4)
    return c


def draw_leg_thigh():
    """Thigh + knee, pivot at the hip (top centre)."""
    W, H = 110, 180
    c = Canvas(W, H, pivot=(W / 2, 22))
    ox = W / 2
    c.round_rect((ox - 24, 16, ox + 24, 148), 23, SKIN, INK, 6)
    c.clip_begin()
    c.round_rect((ox + 5, 20, ox + 26, 146), 18, SKIN_SH)
    c.clip_end()
    return c


def draw_leg_calf():
    """Calf + sock + sneaker, pivot at the knee (top centre)."""
    W, H = 120, 210
    c = Canvas(W, H, pivot=(W / 2, 22))
    ox = W / 2
    c.round_rect((ox - 23, 16, ox + 23, 112), 22, SKIN, INK, 6)
    c.clip_begin()
    c.round_rect((ox + 5, 20, ox + 25, 110), 16, SKIN_SH)
    c.clip_end()
    # sock
    c.round_rect((ox - 25, 100, ox + 25, 156), 11, WHITE, INK, 5)
    c.round_rect((ox - 25, 130, ox + 25, 156), 9, (216, 226, 246, 255))
    c.line([(ox - 24, 130), (ox + 24, 130)], (192, 204, 230, 255), 4)
    # sneaker
    c.round_rect((ox - 48, 148, ox + 34, 208), 24, (52, 62, 94, 255), INK, 6)
    c.clip_begin()
    c.round_rect((ox - 48, 158, ox + 34, 180), 10, (74, 86, 122, 255))
    c.round_rect((ox - 48, 194, ox + 34, 210), 8, WHITE)
    c.clip_end()
    c.round_rect((ox - 48, 194, ox + 34, 210), 8, None, INK, 5)
    c.arc((ox - 24, 156, ox + 8, 184), 200, 340, (118, 132, 164, 255), 5)
    c.circle(ox + 12, 168, 5, (255, 255, 255, 190))
    return c


def draw_pack():
    """Backpack, pivot near the top centre so it can hang off the shoulders."""
    W, H = 150, 220
    c = Canvas(W, H, pivot=(W / 2, 46))
    ox = W / 2
    c.round_rect((ox - 58, 34, ox + 58, 196), 34, PACK_Y)
    c.clip_begin()
    c.round_rect((ox - 58, 34, ox + 58, 92), 30, PACK_Y_D)
    c.round_rect((ox + 12, 92, ox + 60, 198), 26, PACK_Y_D)
    c.clip_end()
    c.round_rect((ox - 58, 34, ox + 58, 196), 34, None, INK, 7)
    c.round_rect((ox - 36, 104, ox + 36, 158), 16, PACK_Y_D, INK, 5)
    c.round_rect((ox - 20, 118, ox + 20, 126), 4, C(PACK_Y, 255))
    c.line([(ox - 44, 44), (ox - 20, 16)], PACK_Y_D, 12)
    c.line([(ox + 44, 44), (ox + 20, 16)], PACK_Y_D, 12)
    return c


def draw_sun(face=True):
    W, H = 460, 460
    c = Canvas(W, H)
    ox = oy = W / 2
    # rays (rounded capsules, drawn behind the disc)
    n = 12
    for i in range(n):
        a = math.radians(i * 360.0 / n)
        r0, r1 = 150, 205
        x0, y0 = ox + math.cos(a) * r0, oy + math.sin(a) * r0
        x1, y1 = ox + math.cos(a) * r1, oy + math.sin(a) * r1
        c.line([(x0, y0), (x1, y1)], SUN_Y_D, 34)
        c.circle(x1, y1, 17, SUN_Y_D)
    # core
    c.circle(ox, oy, 156, SUN_Y)
    c.clip_begin()
    c.circle(ox + 26, oy + 40, 152, (247, 178, 22, 255))
    c.circle(ox - 46, oy - 54, 74, (255, 238, 160, 255))
    c.clip_end()
    c.circle(ox, oy, 156, None, INK, 7)
    for i in range(n):
        a = math.radians(i * 360.0 / n)
        r1 = 205
        c.circle(ox + math.cos(a) * r1, oy + math.sin(a) * r1, 17, None, INK, 4)
    c.circle(ox, oy, 156, None, INK, 7)
    if face:
        c.arc((ox - 62, oy + 6, ox - 14, oy + 50), 20, 160, INK, 7)
        c.arc((ox + 14, oy + 6, ox + 62, oy + 50), 20, 160, INK, 7)
        c.ellipse((ox - 62, oy + 30, ox - 22, oy + 56), CHEEK)
        c.ellipse((ox + 22, oy + 30, ox + 62, oy + 56), CHEEK)
    return c


def draw_prism():
    W, H = 240, 220
    c = Canvas(W, H)
    tri = [(120, 20), (222, 196), (18, 196)]
    c.poly(tri, (186, 234, 255, 235), INK, 6)
    c.poly([(120, 20), (120, 196), (18, 196)], (255, 255, 255, 120))
    c.poly([(120, 20), (150, 196), (120, 196)], C((150, 214, 255, 160)))
    c.line([(120, 20), (120, 196)], (255, 255, 255, 190), 4)
    c.line([(60, 120), (150, 70)], (255, 255, 255, 130), 6)
    return c


def draw_cloud(w=420, h=210):
    c = Canvas(w, h)
    ox, oy = w / 2, h * 0.62
    blobs = [(-120, 6, 62), (-52, -30, 78), (26, -18, 70), (94, 12, 54), (-6, 26, 74)]
    for dx, dy, r in blobs:
        c.circle(ox + dx, oy + dy, r, WHITE)
    c.round_rect((ox - 170, oy + 6, ox + 152, oy + 78), 38, WHITE)
    return c


def draw_molecule(r=40):
    c = Canvas(r * 2 + 24, r * 2 + 24)
    ox = oy = (r * 2 + 24) / 2
    c.circle(ox, oy, r, (186, 226, 255, 235), (255, 255, 255, 170), 4)
    c.circle(ox - r * 0.3, oy - r * 0.34, r * 0.28, (255, 255, 255, 190))
    c.circle(ox + r * 0.36, oy + r * 0.24, r * 0.16, (255, 255, 255, 110))
    return c


def draw_tree(scale=1.0, leaf=(46, 138, 74, 255), trunk=(120, 78, 44, 255)):
    c = Canvas(220 * scale, 300 * scale)
    ox = 110 * scale
    c.round_rect((ox - 13 * scale, 150 * scale, ox + 13 * scale, 268 * scale), 8 * scale, trunk, INK, 5)
    for dx, dy, r in [(-46, 138, 54), (0, 104, 68), (48, 132, 50), (0, 152, 62)]:
        c.circle(ox + dx * scale, dy * scale, r * scale, leaf)
    c.circle(ox + dx * 0.4 * scale, dy * 0.9 * scale, 30 * scale, C((90, 190, 110, 120)))
    return c
