"""scenes.py — builds the six shots of "Why Is The Sky Blue?" with the layered rig."""
import math
import random
from PIL import Image, ImageDraw, ImageFilter
import art
import rig

W, H, FPS, TOTAL = 1080, 1920, 30, 900
GROUND = 1520.0

C = art.C


# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else (b if x > b else x)


def seg(t, a, b):
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def eo(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ei(x):
    x = clamp(x)
    return x ** 3


def eio(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def back(x, s=1.9):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def pulse(t, sp=2.0, amp=1.0, ph=0.0):
    return math.sin(t * sp + ph) * amp


# ------------------------------------------------------------------ sky
def sky_gradient(w, h, stops):
    """Vertical multi-stop gradient."""
    img = Image.new("RGB", (1, h))
    d = ImageDraw.Draw(img)
    n = len(stops) - 1
    for y in range(h):
        k = y / (h - 1) * n
        i = min(n - 1, int(k))
        f = k - i
        c0, c1 = stops[i], stops[i + 1]
        d.point((0, y), tuple(int(c0[j] + (c1[j] - c0[j]) * f) for j in range(3)))
    return img.resize((w, h), Image.BILINEAR).convert("RGBA")


def hill(w, h, y, amp, color, seed=1, freq=0.004, phase=0.0):
    """A soft rolling hill mask drawn as a filled silhouette."""
    rnd = random.Random(seed)
    pts = []
    for x in range(0, w + 8, 8):
        yy = y + math.sin(x * freq + phase) * amp + math.sin(x * freq * 2.3 + phase * 1.7) * amp * 0.35
        pts.append((x, yy))
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon(pts + [(w, h), (0, h)], fill=color)
    return img


def tree_sprite(scale=1.0, leaf=(38, 128, 76, 255), trunk=(96, 66, 42, 255)):
    w = int(230 * scale)
    h = int(310 * scale)
    c = art.Canvas(w, h)
    ox = w / 2
    c.round_rect((ox - 11 * scale, 168 * scale, ox + 11 * scale, 292 * scale), 6 * scale, trunk)
    for dx, dy, r in [(-44, 150, 50), (0, 112, 66), (46, 142, 48), (0, 160, 58), (-20, 96, 40)]:
        c.circle(ox + dx * scale, dy * scale, r * scale, leaf)
    c.circle(ox - 14 * scale, 118 * scale, 26 * scale, C(leaf, 150))
    return c.result()


# ------------------------------------------------------------------ sky box
def make_day():
    bg = sky_gradient(W, H, [(86, 186, 246), (128, 210, 250), (186, 232, 252), (214, 240, 252)])
    # sun glow behind the horizon
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-260, 120, 1180, 1180), fill=(255, 246, 200, 40))
    gd.ellipse((60, 300, 900, 1060), fill=(255, 250, 220, 46))
    bg = Image.alpha_composite(bg, glow.filter(ImageFilter.GaussianBlur(60)))
    # far hills
    bg = Image.alpha_composite(bg, hill(W, H, 1330, 46, (98, 178, 148, 255), 3, 0.0022))
    bg = Image.alpha_composite(bg, hill(W, H, 1425, 34, (72, 156, 122, 255), 7, 0.0031))
    bg = Image.alpha_composite(bg, hill(W, H, 1516, 22, (52, 132, 96, 255), 11, 0.0038))
    # trees
    for x, s, y in [(120, 0.62, 1345), (900, 0.5, 1330), (520, 0.38, 1350)]:
        t = tree_sprite(s, (58, 150, 92, 255), (86, 60, 40, 255))
        bg.alpha_composite(t, (int(x), int(y)))
    # grass speckles
    d = ImageDraw.Draw(bg)
    rnd = random.Random(5)
    for _ in range(220):
        x = rnd.uniform(0, W)
        y = rnd.uniform(1450, H)
        r = rnd.uniform(1.5, 4)
        col = (120, 196, 120, 140) if rnd.random() < 0.5 else (230, 246, 170, 130)
        d.ellipse((x, y, x + r * 2, y + r * 1.4), fill=col)
    return bg


def make_night():
    bg = sky_gradient(W, H, [(22, 20, 66), (40, 30, 96), (70, 44, 120), (100, 60, 138)])
    d = ImageDraw.Draw(bg)
    rnd = random.Random(9)
    for _ in range(170):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H * 0.8)
        r = rnd.uniform(1.2, 3.4)
        a = rnd.randint(120, 255)
        d.ellipse((x, y, x + r * 2, y + r * 2), fill=(255, 255, 240, a))
    for _ in range(14):  # twinkle stars
        x, y = rnd.uniform(40, W - 40), rnd.uniform(60, H * 0.7)
        s = rnd.uniform(6, 14)
        d.polygon([(x, y - s), (x + s * 0.28, y - s * 0.28), (x + s, y),
                   (x + s * 0.28, y + s * 0.28), (x, y + s),
                   (x - s * 0.28, y + s * 0.28), (x - s, y),
                   (x - s * 0.28, y - s * 0.28)], fill=(255, 246, 180, 235))
    # moon
    d.ellipse((80, 120, 260, 300), fill=(255, 250, 214, 255))
    d.ellipse((120, 100, 300, 280), fill=(40, 30, 96, 255))
    bg = Image.alpha_composite(bg, hill(W, H, 1450, 40, (28, 26, 58, 255), 4, 0.0026))
    bg = Image.alpha_composite(bg, hill(W, H, 1540, 26, (18, 18, 42, 255), 8, 0.0034))
    return bg


def make_sunset():
    bg = sky_gradient(W, H, [(40, 26, 74), (108, 40, 96), (196, 66, 92),
                             (246, 122, 72), (255, 186, 96)])
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((W * 0.5 - 700, 900, W * 0.5 + 700, 2200), fill=(255, 200, 110, 90))
    bg = Image.alpha_composite(bg, glow.filter(ImageFilter.GaussianBlur(90)))
    bg = Image.alpha_composite(bg, hill(W, H, 1300, 30, (94, 44, 92, 255), 6, 0.0024))
    bg = Image.alpha_composite(bg, hill(W, H, 1450, 24, (58, 26, 62, 255), 10, 0.0032))
    bg = Image.alpha_composite(bg, hill(W, H, 1560, 18, (34, 16, 42, 255), 14, 0.0041))
    # clouds catching fire
    cl = art.draw_cloud(460, 200).result()
    tint = cl.copy()
    tint.putalpha(cl.split()[3].point(lambda v: int(v * 0.55)))
    sol = Image.new("RGBA", tint.size, (255, 168, 120, 255))
    tint = Image.composite(sol, tint, tint.split()[3])
    for (x, y, s) in [(120, 460, 1.0), (640, 330, 0.8), (420, 700, 0.55)]:
        t = tint.resize((int(tint.width * s), int(tint.height * s)))
        bg.alpha_composite(t, (int(x), int(y)))
    return bg


def make_space():
    bg = sky_gradient(W, H, [(6, 8, 30), (16, 20, 58), (30, 30, 86), (46, 42, 110)])
    d = ImageDraw.Draw(bg)
    rnd = random.Random(21)
    for _ in range(240):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        r = rnd.uniform(1, 3.6)
        d.ellipse((x, y, x + r * 2, y + r * 2), fill=(235, 240, 255, rnd.randint(90, 255)))
    return bg


# ------------------------------------------------------------------ overlays
def vignette(w, h, strength=90):
    v = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(v)
    d.ellipse((-w * 0.35, -h * 0.25, w * 1.35, h * 1.25), fill=255)
    v = v.filter(ImageFilter.GaussianBlur(140))
    out = Image.new("RGBA", (w, h), (12, 16, 40, strength))
    out.putalpha(Image.eval(v, lambda p: int((255 - p) * strength / 255)))
    return out


def grain(w, h, amount=8):
    rnd = random.Random(77)
    n = Image.new("L", (w // 4, h // 4))
    n.putdata([rnd.randint(0, 255) for _ in range((w // 4) * (h // 4))])
    n = n.resize((w, h), Image.BILINEAR)
    g = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    g.putalpha(n.point(lambda p: int(abs(p - 128) * amount / 128)))
    return g


# ------------------------------------------------------------------ text
def banner(text, fsize=58, pad=44, fill=(20, 24, 46, 236), edge=(120, 190, 255, 255)):
    f = art.font("Baloo2", fsize)
    lines = text.split("\n")
    tw = max(f.getbbox(l)[2] - f.getbbox(l)[0] for l in lines)
    lh = fsize * 1.22
    w = int(tw + pad * 2)
    h = int(lh * len(lines) + pad * 1.1)
    c = art.Canvas(w, h)
    c.round_rect((6, 6, w - 6, h - 6), min(h / 2.2, 40), fill, None, 0)
    c.round_rect((6, 6, w - 6, h - 6), min(h / 2.2, 40), None, edge, 5)
    for i, l in enumerate(lines):
        c.text((w / 2, h / 2 - (len(lines) - 1) * lh / 2 + i * lh), l, f, (255, 255, 255, 255))
    return c.result()


def title_card():
    f1 = art.font("Baloo2", 100)
    f2 = art.font("Baloo2", 146)
    w, h = 1080, 400
    c = art.Canvas(w, h)

    def outlined(xy, s, f, fills, stroke=16):
        c.text((xy[0] + 8, xy[1] + 12), s, f, (10, 14, 32, 120), "mm")
        c.text(xy, s, f, fills, "mm", stroke, (26, 28, 46, 255))

    outlined((w / 2, 104), "WHY IS THE", f1, (255, 255, 255, 255))
    outlined((w / 2, 250), "SKY BLUE?", f2, (255, 206, 42, 255))
    return c.result()
