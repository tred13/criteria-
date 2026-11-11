"""renderer.py — frame-accurate compositor for the six shots of the film.

World coordinates are DESIGN UNITS on a 1080x1920 stage (SU = 1.0), so the
camera can zoom without any scale mismatches.
"""
import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter
import art
import rig
import scenes as S

W, H = 1080, 1920
FPS, TOTAL = 30, 900
SU = 1.0                 # pixels per design unit
GROUND = 1560.0          # sole line
C = art.C

HERE = os.path.dirname(os.path.abspath(__file__))
_cache = {}


# ------------------------------------------------------------------ utils
def R(v):
    return v * SU


def capsule(d, p0, p1, w, fill):
    d.line([p0, p1], fill=fill, width=max(1, int(w)))
    for p in (p0, p1):
        d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=fill)


def blob(img, xy, r, color, blur=18, a=90):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse((xy[0] - r, xy[1] - r, xy[0] + r, xy[1] + r), fill=C(color, a))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur)))
    img.alpha_composite(lay)


def glow(img, layer, blur=24, gain=1.0):
    g = layer.filter(ImageFilter.GaussianBlur(blur))
    if gain != 1.0:
        g = Image.eval(g, lambda p: min(255, int(p * gain)))
    img.alpha_composite(g)
    img.alpha_composite(layer)


def camera(img, zoom=1.0, cx=None, cy=None):
    z = max(1.0, zoom)
    vw, vh = W / z, H / z
    cx = W / 2 if cx is None else cx
    cy = H / 2 if cy is None else cy
    x0 = max(0, min(W - vw, cx - vw / 2))
    y0 = max(0, min(H - vh, cy - vh / 2))
    return img.crop((int(x0), int(y0), int(x0 + vw), int(y0 + vh))).resize((W, H), Image.LANCZOS)


def assets():
    if _cache:
        return _cache
    a = {}
    a["day"] = S.make_day()
    a["night"] = S.make_night()
    a["sunset"] = S.make_sunset()
    a["space"] = S.make_space()
    a["title"] = S.title_card()
    a["sun"] = art.draw_sun().result()
    a["cloud"] = art.draw_cloud(520, 250).result()
    a["mols"] = [art.draw_molecule(r).result() for r in (26, 34, 44, 56)]
    a["banners"] = {
        "rainbow": S.banner("Sunlight = a secret\nrainbow!"),
        "scatter": S.banner("Blue bounces\nEVERYWHERE!"),
        "eyes": S.banner("Your eyes see blue\nfrom every direction!", fsize=52),
        "sunset": S.banner("At sunset...\nreds & oranges stay!", fsize=52),
        "outro": S.banner("Mystery solved!", fsize=64),
    }
    a["vig"] = S.vignette(W, H, 70)
    a["grain"] = S.grain(W, H, 9)
    _cache.update(a)
    return _cache


BANNER_Y = 1690


def banner(img, key, t, t_in):
    k = S.back(S.seg(t, t_in, t_in + 0.40))
    if k <= 0.02:
        return
    sp = assets()["banners"][key]
    s = sp.resize((max(1, int(sp.width * k)), max(1, int(sp.height * k))), Image.LANCZOS)
    y = BANNER_Y + (1 - k) * 60
    img.alpha_composite(s, (int((W - s.width) / 2), int(y - s.height / 2)))


def facing(hand_r):
    """Return +1/-1 for a hand target's side (used for flipping the whole rig)."""
    return 1


def sunny(img, hip, unit=1.0, **kw):
    out = rig.compose(img, hip, unit, shadow=False, **kw)
    return out


def hand_world(hip, unit, hand, flip=False):
    return rig.hand_at(hip, unit, hand, flip)


# ------------------------------------------------------------------ poses
def walk_pose(phase, hip_y, stride=104, lift=66):
    """Contact-pass walk driven by IK foot targets (absolute sole-aware)."""
    out = {}
    for side, ph in (("l", phase), ("r", phase + math.pi)):
        fx = -math.cos(ph) * stride
        fy = 0.0
        if math.sin(ph) > 0:
            fy = -abs(math.sin(ph)) * lift
        out["foot_" + side] = (fx + (-30 if side == "l" else 30), GROUND - hip_y + fy + rig.SOLE * 0)
    # IK targets are hip-relative: sole sits at hy + SOLE
    for k in ("foot_l", "foot_r"):
        x, y = out[k]
        out[k] = (x, rig.SOLE + (y - (GROUND - hip_y)) + (GROUND - hip_y) - rig.SOLE)
    return out


# ================================================================ SHOT 1 — the hook
def shot1(t, lt):
    A = assets()
    img = A["day"].copy()

    for x0, y0, s, sp in [(-300, 300, 1.0, 24), (720, 190, 0.7, 40), (360, 640, 0.5, 16)]:
        x = (x0 + t * sp) % (W + 900) - 450
        cl = A["cloud"].resize((int(A["cloud"].width * s), int(A["cloud"].height * s)))
        img.alpha_composite(cl, (int(x), int(y0)))

    sun = A["sun"].resize((int(A["sun"].width * 1.1), int(A["sun"].height * 1.1)))
    sx, sy = 878, 372 + math.sin(t * 1.3) * 12
    img.alpha_composite(sun, (int(sx - sun.width / 2), int(sy - sun.height / 2)))

    unit = 1.78
    walk = S.seg(t, 0.15, 2.45)
    hip_x = 120 + (440 - 120) * S.eo(walk)
    hip_y = GROUND - rig.SOLE * unit
    kw = dict(head="head_smile")
    if walk < 1.0:
        ph = (t - 0.15) * 2 * math.pi * 1.4
        for side, pp in (("l", ph), ("r", ph + math.pi)):
            fx = -math.cos(pp) * 104
            fy = -abs(math.sin(pp)) * 66 if math.sin(pp) > 0 else 0
            kw["foot_" + side] = (fx + (-34 if side == "l" else 34), rig.SOLE + fy)
        kw["hip_dy"] = -abs(math.sin(ph)) * 12
        kw["arm_l"] = -0.12 + math.sin(ph + math.pi) * 0.55
        kw["arm_r"] = 0.12 + math.sin(ph) * 0.55
        kw["body_rot"] = math.sin(ph) * 0.03
    else:
        idle = t - 2.45
        kw.update(foot_l=(-62, rig.SOLE), foot_r=(62, rig.SOLE),
                  hip_dy=math.sin(idle * 2.3) * 4,
                  hand_l=(-146, -10 + math.sin(idle * 2.0) * 8),
                  hand_r=(146, -10 - math.sin(idle * 2.0) * 8))

    pt = S.eo(S.seg(t, 2.65, 3.2))
    if pt > 0:
        kw["hand_r"] = (146 + 120 * pt, -10 + (-390 + 10) * pt)
        kw["head"] = "head_open"
        kw["head_rot"] = -0.16 * pt
        kw["elbow_r"] = 0.12
    if 3.55 < t < 3.72:
        kw["head"] = "head_blink"

    sunny(img, (hip_x, hip_y), unit, **kw)

    # question mark
    qk = S.back(S.seg(t, 2.05, 2.5))
    if qk > 0.02:
        f = art.font("Baloo2", 215)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        bx = hip_x + 300
        by = hip_y - 760 + math.sin(t * 2.6) * 14
        d.text((bx + 8, by + 10), "?", font=f, fill=(12, 16, 40, 90), anchor="mm")
        d.text((bx, by), "?", font=f, fill=(255, 210, 46, 255), anchor="mm",
               stroke_width=18, stroke_fill=(255, 255, 255, 255))
        lay = lay.rotate(0)  # no-op keeps the alpha channel
        k = max(0.02, qk)
        z = lay.resize((int(W * k), int(H * k)), Image.LANCZOS)
        img.alpha_composite(z, (int(bx * (1 - k)), int(by * (1 - k))))

    tk = S.back(S.seg(t, 1.2, 1.75))
    if tk > 0.02:
        ti = A["title"].resize((max(1, int(A["title"].width * tk)),
                                max(1, int(A["title"].height * tk))), Image.LANCZOS)
        img.alpha_composite(ti, (int((W - ti.width) / 2), int(190 - ti.height / 2)))

    # sun smiles wider as he points
    return camera(img, 1.02 + 0.06 * S.eio(S.seg(t, 0, 4.5)), W / 2, H * 0.60)


# ================================================================ SHOT 2 — secret rainbow
def shot2(t, lt):
    A = assets()
    img = A["space"].copy()
    rnd = random.Random(4)
    for i in range(26):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H * 0.75)
        blob(img, (x, y), 4 + (i % 3), (255, 255, 240), 8, int(60 + 60 * abs(math.sin(t * 2 + i))))

    sun = A["sun"].resize((int(A["sun"].width * 0.8), int(A["sun"].height * 0.8)))
    sx, sy = 150, 420
    img.alpha_composite(sun, (int(sx - sun.width / 2), int(sy - sun.height / 2)))

    unit = 1.70
    hip_x = 320
    hip_y = GROUND - rig.SOLE * unit - 40
    up = S.eo(S.seg(t, 0.1, 0.95))
    hand_r = (150 + (238 - 150) * up, -240 + (-330 + 240) * up)
    kw = dict(head="head_open", head_rot=-0.18 * up,
              hand_r=hand_r,
              hand_l=(-205, -300 + math.sin(t * 2.1) * 12),
              foot_l=(-72, rig.SOLE), foot_r=(72, rig.SOLE),
              hip_dy=math.sin(t * 2.2) * 5,
              elbow_r=-0.05)
    sunny(img, (hip_x, hip_y), unit, **kw)
    px, py = hand_world((hip_x, hip_y), unit, hand_r)

    pr = rig.part("prism")[0]
    pr = pr.resize((int(pr.width * unit * 0.62), int(pr.height * unit * 0.62)), Image.LANCZOS)
    pr = pr.rotate(-12 + math.sin(t * 1.1) * 4, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(pr, (int(px - pr.width * 0.42), int(py - pr.height * 0.55)))

    beam = S.eo(S.seg(t, 0.75, 1.3))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    if beam > 0.02:
        p0 = (sx + 118, sy + 96)
        p1 = (px - pr.width * 0.30, py - pr.height * 0.22)
        capsule(d, p0, (p0[0] + (p1[0] - p0[0]) * beam, p0[1] + (p1[1] - p0[1]) * beam),
                16, (255, 252, 230, 240))
        glow(img, lay, 18)

    fan = S.eo(S.seg(t, 1.15, 2.5))
    if fan > 0.02:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        origin = (px + pr.width * 0.26, py - pr.height * 0.04)
        L = 1500 * fan
        for i, col in enumerate(art.RAINBOW):
            a = math.radians(-24 + i * 7.6 + math.sin(t * 1.3 + i) * 0.5)
            capsule(d, origin, (origin[0] + math.cos(a) * L, origin[1] + math.sin(a) * L),
                    30, C(col, 235))
        glow(img, lay, 20)
        blob(img, origin, 46, (255, 255, 240), 26, 210)

    rnd2 = random.Random(12)
    for i in range(22):
        x = rnd2.uniform(0, W)
        y = (rnd2.uniform(0, H) + t * rnd2.uniform(20, 70)) % H
        blob(img, (x, y), rnd2.uniform(2, 5), (200, 235, 255), 10, 70)

    banner(img, "rainbow", t, 0.95)
    return camera(img, 1.02 + 0.05 * S.eio(S.seg(t, 0, 5.0)), W * 0.55, H * 0.50)


# ================================================================ SHOT 3 — the collision
def shot3(t, lt):
    A = assets()
    img = A["day"].copy()
    img = Image.blend(img, Image.new("RGBA", img.size, (24, 58, 128, 255)), 0.40)

    rnd = random.Random(31)
    for i in range(13):
        bx = rnd.uniform(40, W - 40)
        spd = rnd.uniform(26, 70)
        y = (rnd.uniform(0, H) - t * spd) % (H + 200) - 100
        r = rnd.choice(A["mols"])
        sz = rnd.uniform(0.6, 1.3)
        m = r.resize((int(r.width * sz), int(r.height * sz)), Image.LANCZOS)
        img.alpha_composite(m, (int(bx + math.sin(t * 0.9 + i) * 30 - m.width / 2), int(y - m.height / 2)))

    unit = 1.80
    hip_x = W * 0.5 + math.sin(t * 1.1) * 24
    hip_y = 900 + math.sin(t * 1.6) * 26
    sunny(img, (hip_x, hip_y), unit,
          head="head_open", head_rot=math.sin(t * 1.5 + 0.6) * 0.08,
          hand_l=(-215 + math.sin(t * 3.4) * 16, -300),
          hand_r=(215 + math.sin(t * 3.4 + 1.2) * 16, -320),
          foot_l=(-78, rig.SOLE - 40 + math.sin(t * 2.6) * 20),
          foot_r=(78, rig.SOLE - 30 + math.sin(t * 2.6 + 1.4) * 20),
          hip_dy=math.sin(t * 2.1) * 8)

    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(18):
        ap = S.seg(t, 0.5 + i * 0.1, 0.85 + i * 0.1)
        if ap <= 0.02:
            continue
        ph = t * (1.2 + (i % 5) * 0.22) + i * 1.37
        cx = W * 0.5 + math.sin(ph * 1.9) * 440
        cy = 980 + math.cos(ph * 1.4) * 620
        a = math.atan2(math.cos(ph * 2.6), math.sin(ph * 2.1))
        ln = 130 + 190 * abs(math.sin(ph * 1.7))
        capsule(d, (cx - math.cos(a) * ln / 2, cy - math.sin(a) * ln / 2),
                (cx + math.cos(a) * ln / 2, cy + math.sin(a) * ln / 2),
                14, C(art.RAINBOW[4] if i % 3 else art.RAINBOW[5], int(210 * ap)))
    glow(img, lay, 16, 0.9)
    banner(img, "scatter", t, 0.8)
    return camera(img, 1.02 + 0.06 * S.eio(S.seg(t, 0, 6.5)), W * 0.5, H * 0.50)


# ================================================================ SHOT 4 — your eyes
def shot4(t, lt):
    A = assets()
    img = A["day"].copy()
    img = Image.blend(img, Image.new("RGBA", img.size, (150, 214, 252, 255)), 0.32)

    unit = 2.15
    hip_x, hip_y = W * 0.5, GROUND - rig.SOLE * unit
    gl = (hip_x, hip_y - 168 * unit + 6)

    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(11):
        a0 = -2.9 + i * 0.19
        ln = 900 + 130 * math.sin(t * 1.7 + i * 0.7)
        k = S.eo(S.seg(t, 0.15 + i * 0.055, 1.0 + i * 0.055))
        if k <= 0.02:
            continue
        p0 = (gl[0] + math.cos(a0) * ln, gl[1] + math.sin(a0) * ln)
        p1 = (gl[0] + math.cos(a0) * ln * (1 - k), gl[1] + math.sin(a0) * ln * (1 - k))
        capsule(d, p0, p1, 13, (128, 200, 255, 185))
    glow(img, lay, 14, 0.8)

    sunny(img, (hip_x, hip_y), unit,
          head="head_open", head_rot=-0.26 + math.sin(t * 1.2) * 0.04,
          hand_l=(-262, -196 + math.sin(t * 1.9) * 10),
          hand_r=(262, -196 - math.sin(t * 1.9) * 10),
          foot_l=(-64, rig.SOLE), foot_r=(64, rig.SOLE))
    blob(img, (gl[0], gl[1] - 12), 130, (200, 236, 255), 44, 70)

    rnd = random.Random(66)
    for i in range(18):
        y = (rnd.uniform(0, H) + t * rnd.uniform(40, 110)) % H
        blob(img, (rnd.uniform(0, W), y), rnd.uniform(2, 6), (225, 245, 255), 9, 80)

    banner(img, "eyes", t, 1.15)
    return camera(img, 1.04 + 0.05 * S.eio(S.seg(t, 0, 6.0)), W * 0.5, H * 0.58)


# ================================================================ SHOT 5 — sunset twist
def shot5(t, lt):
    A = assets()
    img = A["sunset"].copy()

    sun = A["sun"].resize((int(A["sun"].width * 1.8), int(A["sun"].height * 1.8)))
    tint = Image.new("RGBA", sun.size, (255, 132, 56, 255))
    sun = Image.composite(tint, sun, sun.split()[3])
    sx, sy = 862, 1030 + math.sin(t * 0.7) * 8
    blob(img, (sx, sy), 460, (255, 150, 70), 90, 60)
    img.alpha_composite(sun, (int(sx - sun.width / 2), int(sy - sun.height / 2)))

    rnd = random.Random(88)
    for i in range(30):
        ph = (rnd.uniform(0, 1) + t * rnd.uniform(0.10, 0.22)) % 1.0
        x = rnd.uniform(0, W) + math.sin(t * 1.1 + i) * 24
        y = 1780 - ph * 1640
        blob(img, (x, y), rnd.uniform(2, 6), (255, 176, 96), 10, int(190 * math.sin(ph * math.pi)))

    unit = 1.72
    hip_x = 270
    hip_y = GROUND - rig.SOLE * unit
    sunny(img, (hip_x, hip_y), unit,
          head="head_smile", head_rot=0.10 + math.sin(t * 1.1) * 0.04,
          hand_l=(-140, -180 + math.sin(t * 1.4) * 6),
          hand_r=(198, -286 + math.sin(t * 1.6) * 6),
          foot_l=(-66, rig.SOLE), foot_r=(66, rig.SOLE),
          hip_dy=math.sin(t * 1.7) * 4, pack_rot=-0.09)
    img.alpha_composite(Image.new("RGBA", img.size, (255, 146, 86, 40)))

    banner(img, "sunset", t, 0.85)
    return camera(img, 1.01 + 0.04 * S.eio(S.seg(t, 0, 5.0)), W * 0.5, H * 0.56)


# ================================================================ SHOT 6 — payoff
def shot6(t, lt):
    A = assets()
    img = A["day"].copy()
    sun = A["sun"].resize((int(A["sun"].width * 0.95), int(A["sun"].height * 0.95)))
    img.alpha_composite(sun, (int(880 - sun.width / 2), int(330 - sun.height / 2)))

    # confetti behind the character
    rnd = random.Random(101)
    for i in range(58):
        x = rnd.uniform(0, W)
        y = (rnd.uniform(0, H) + t * rnd.uniform(230, 540)) % (H + 140) - 70
        w2, h2 = rnd.uniform(10, 24), rnd.uniform(16, 32)
        lay = Image.new("RGBA", (int(w2 * 2 + 26), int(h2 * 2 + 26)), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        dd.rounded_rectangle((13, 13, 13 + w2, 13 + h2), 4, fill=C(art.RAINBOW[i % 7], 235))
        lay = lay.rotate((t * rnd.uniform(80, 260) + i * 30) % 360,
                         resample=Image.BICUBIC, expand=True)
        img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))

    unit = 1.76
    hop = abs(math.sin(t * math.pi / 1.0))
    hip_x = W * 0.5
    hip_y = GROUND - rig.SOLE * unit - hop * 170
    sunny(img, (hip_x, hip_y), unit,
          head="head_grin" if t < 2.1 else "head_open",
          head_rot=math.sin(t * 3) * 0.06,
          arm_l=2.05 + math.sin(t * 5) * 0.12,
          arm_r=-2.05 - math.sin(t * 5) * 0.12,
          elbow_l=-0.30, elbow_r=0.30,
          foot_l=(-80, rig.SOLE + hop * 40), foot_r=(80, rig.SOLE + hop * 52))

    banner(img, "outro", t, 0.45)
    return camera(img, 1.05 + 0.05 * S.eio(S.seg(t, 0, 3.0)), W / 2, H * 0.5)


SHOTS = [(0.0, 4.5, shot1), (4.5, 9.5, shot2), (9.5, 16.0, shot3),
         (16.0, 22.0, shot4), (22.0, 27.0, shot5), (27.0, 30.0, shot6)]
XFADE = 0.34


def frame(f):
    t = f / FPS
    cur = 0
    for i, (a, b, fn) in enumerate(SHOTS):
        if t >= a:
            cur = i
    a, b, fn = SHOTS[cur]
    img = fn(t - a, t)
    if cur > 0 and t < a + XFADE:
        pa = SHOTS[cur - 1][0]
        img = Image.blend(SHOTS[cur - 1][2](t - pa, t), img, S.eio((t - a) / XFADE))
    img.alpha_composite(assets()["vig"])
    if f % 2 == 0:
        img.alpha_composite(assets()["grain"])
    return img.convert("RGB")


def main(out_dir, start=0, end=TOTAL):
    os.makedirs(out_dir, exist_ok=True)
    assets()
    for f in range(start, end):
        frame(f).save(os.path.join(out_dir, "f%04d.png" % f))
        if f % 60 == 0:
            print("frame", f, flush=True)
    print("DONE", end - start)


if __name__ == "__main__":
    import sys
    s = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    e = int(sys.argv[2]) if len(sys.argv) > 2 else TOTAL
    o = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "..", "frames")
    main(o, s, e)
