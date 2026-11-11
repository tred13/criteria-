"""rig.py — 2-bone IK cut-out rig for Sunny.

All skeleton numbers are in DESIGN UNITS (character ~616 units tall).
`unit` = pixels per design unit, so the same rig works at any resolution.
"""
import math
from PIL import Image, ImageDraw
import art

# ------------------------------------------------------------------ skeleton (design units)
HIP_W = 40            # leg roots at ±HIP_W
SHOULDER_W = 76       # arm roots at ±SHOULDER_W
SHOULDER_Y = -190
HEAD_Y = -168
PACK = (-62, -232)

THIGH, CALF = 128, 128
UPPER, FORE = 124, 100
SOLE = 256            # hip height above the sole when standing

PARTS = ["head_smile", "head_open", "head_grin", "head_blink", "head_half", "head_think",
         "body", "arm_upper", "arm_fore", "leg_thigh", "leg_calf", "pack", "prism"]


def _build(name):
    table = {
        "head_smile": (art.draw_head("smile", "open"), (150, 298)),
        "head_open": (art.draw_head("open", "wide", brow="up"), (150, 298)),
        "head_grin": (art.draw_head("grin", "wide"), (150, 298)),
        "head_blink": (art.draw_head("smile", "closed"), (150, 298)),
        "head_half": (art.draw_head("smile", "half"), (150, 298)),
        "head_think": (art.draw_head("smile", "half", brow="sad"), (150, 298)),
        "body": (art.draw_body(), (170, 250)),
        "arm_upper": (art.draw_arm_upper(), (60, 20)),
        "arm_fore": (art.draw_arm_fore(), (60, 22)),
        "leg_thigh": (art.draw_leg_thigh(), (55, 22)),
        "leg_calf": (art.draw_leg_calf(), (60, 22)),
        "pack": (art.draw_pack(), (75, 46)),
        "prism": (art.draw_prism(), (120, 190)),
    }
    c, pv = table[name]
    return c.result(), pv


CACHE = {}


def part(name):
    if name not in CACHE:
        CACHE[name] = _build(name)
    return CACHE[name]


_SCALED = {}


def _scaled(img, unit):
    key = (id(img), round(unit, 3))
    hit = _SCALED.get(key)
    if hit is None:
        w = max(1, int(round(img.width * unit)))
        h = max(1, int(round(img.height * unit)))
        hit = img if (w, h) == img.size else img.resize((w, h), Image.LANCZOS)
        _SCALED[key] = hit
    return hit


def _place(canvas, img, pivot, at, rot=0.0, unit=1.0):
    """Draw `img` so that its pivot lands on `at`, scaled by `unit`."""
    p = _scaled(img, unit)
    w, h = p.size
    pw, ph = pivot[0] * unit, pivot[1] * unit
    if rot:
        # pad around the pivot first, otherwise rotation crops the limb
        span = int(math.hypot(w, h)) * 2 + 8
        pad = Image.new("RGBA", (span, span), (0, 0, 0, 0))
        pad.alpha_composite(p, (int(span / 2 - pw), int(span / 2 - ph)))
        pad = pad.rotate(math.degrees(rot), resample=Image.BICUBIC,
                         center=(span / 2, span / 2))
        canvas.alpha_composite(pad, (int(round(at[0] - span / 2)), int(round(at[1] - span / 2))))
    else:
        canvas.alpha_composite(p, (int(round(at[0] - pw)), int(round(at[1] - ph))))


def ik2(root, target, l1, l2, bend=1.0):
    dx, dy = target[0] - root[0], target[1] - root[1]
    d = max(1e-3, min(math.hypot(dx, dy), (l1 + l2) * 0.998))
    a = math.atan2(dy, dx)
    cos_a = max(-1.0, min(1.0, (d * d + l1 * l1 - l2 * l2) / (2 * d * l1)))
    ang = math.acos(cos_a)
    jx = root[0] + math.cos(a + bend * ang) * l1
    jy = root[1] + math.sin(a + bend * ang) * l1
    return (jx, jy), (root[0] + math.cos(a) * d, root[1] + math.sin(a) * d)


def _disc(canvas, at, r, color):
    lay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse((at[0] - r, at[1] - r, at[0] + r, at[1] + r), fill=color)
    canvas.alpha_composite(lay)


def _dir(a, b):
    return -math.atan2(b[0] - a[0], b[1] - a[1])


def compose(canvas, hip, unit, head="head_smile", head_rot=0.0, head_dy=0.0,
            body_rot=0.0, hip_dy=0.0,
            hand_l=None, hand_r=None, foot_l=None, foot_r=None,
            arm_l=0.16, arm_r=-0.16, leg_l=0.03, leg_r=-0.03,
            elbow_l=-0.34, elbow_r=0.34, knee_l=0.0, knee_r=0.0,
            pack_rot=-0.05, pack_dx=0.0, shadow=True, flip=False):
    """Composite Sunny onto `canvas` (RGBA). Limb targets are hip-relative design units."""
    W, H = canvas.size
    img = canvas if isinstance(canvas, Image.Image) else Image.new("RGBA", canvas, (0, 0, 0, 0))
    hx, hy = hip[0], hip[1] + hip_dy * unit
    sx = -1 if flip else 1

    if shadow:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.ellipse((hx - 116 * unit, hy + SOLE * unit - 14 * unit,
                   hx + 116 * unit, hy + SOLE * unit + 30 * unit), fill=(24, 30, 62, 48))
        img.alpha_composite(lay)

    shoulder_y = hy + SHOULDER_Y * unit

    # ---------------- legs
    for side, foot, knee, ang in ((-1 * sx, foot_l, knee_l, leg_l), (1 * sx, foot_r, knee_r, leg_r)):
        root = (hx + side * HIP_W * unit, hy)
        if foot is not None:
            tgt = (hx + foot[0] * unit * sx, hy + foot[1] * unit)
            j, e = ik2(root, tgt, THIGH * unit, CALF * unit, bend=1.0)
        else:
            a = ang
            j = (root[0] + math.sin(a) * THIGH * unit, root[1] + math.cos(a) * THIGH * unit)
            a2 = a + knee
            e = (j[0] + math.sin(a2) * CALF * unit, j[1] + math.cos(a2) * CALF * unit)
        _place(img, part("leg_thigh")[0], part("leg_thigh")[1], root, _dir(root, j), unit)
        _place(img, part("leg_calf")[0], part("leg_calf")[1], j, _dir(j, e), unit)

    # ---------------- backpack
    _place(img, part("pack")[0], part("pack")[1],
           (hx + (PACK[0] + pack_dx) * unit * sx, hy + PACK[1] * unit), pack_rot * sx, unit)

    # ---------------- torso
    _place(img, part("body")[0], part("body")[1], (hx, hy), -body_rot * sx, unit)

    # ---------------- arms
    for side, hand, elb, ang in ((-1 * sx, hand_l, elbow_l, arm_l), (1 * sx, hand_r, elbow_r, arm_r)):
        root = (hx + side * SHOULDER_W * unit, shoulder_y)
        if hand is not None:
            tgt = (hx + hand[0] * unit * sx, hy + hand[1] * unit)
            j, e = ik2(root, tgt, UPPER * unit, FORE * unit, bend=1.0 if side < 0 else -1.0)
        else:
            a = ang * (1.0 if side > 0 else -1.0)
            j = (root[0] + math.sin(a) * UPPER * unit, root[1] + math.cos(a) * UPPER * unit)
            a2 = a + elb * (1.0 if side > 0 else -1.0)
            e = (j[0] + math.sin(a2) * FORE * unit, j[1] + math.cos(a2) * FORE * unit)
        _place(img, part("arm_upper")[0], part("arm_upper")[1], root, _dir(root, j), unit)
        _place(img, part("arm_fore")[0], part("arm_fore")[1], j, _dir(j, e), unit)


    # ---------------- head
    _place(img, part(head)[0], part(head)[1],
           (hx, hy + (HEAD_Y + head_dy) * unit), -head_rot * sx, unit)
    return img


def hand_at(hip, unit, hand, flip=False):
    sx = -1 if flip else 1
    return (hip[0] + hand[0] * unit * sx, hip[1] + hand[1] * unit)
