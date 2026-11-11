"""
tools/make_svg.py — vector master of every rig part (Inkscape / Synfig ready).

Every layer group carries an explicit rotation pivot so the SVGs can be
imported into Synfig (bones) or Inkscape (cut-out layers) without re-rigging.
The PNGs used by the renderer are exported from these very shapes.
"""
import json
import math
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "art", "svg")
os.makedirs(OUT, exist_ok=True)

INK = "#1a1b26"
SKIN = "#ffd0ad"
SKIN_SH = "#e8a885"
SKIN_LT = "#ffe3cb"
HAIR = "#603822"
HAIR_LT = "#865234"
HOOD = "#3a76d6"
HOOD_D = "#2854a8"
HOOD_L = "#5694ec"
DENIM = "#344e80"
DENIM_D = "#263a62"
PACK = "#ffc52e"
PACK_D = "#e2a016"
SUN = "#ffcd29"
SUN_D = "#f0a810"

PIVOTS = {}


def write(name, w, h, body, pivot):
    PIVOTS[name] = {"width": w, "height": h, "pivot": pivot}
    with open(os.path.join(OUT, name + ".svg"), "w") as f:
        f.write(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}">\n'
            f'  <g id="{name}" data-pivot="{pivot[0]},{pivot[1]}">\n{body}\n  </g>\n</svg>\n'
        )


# ---------------------------------------------------------------- head
def head_svg(mouth="smile", eyes="open", brow="none"):
    ox, oy, R = 150.0, 150.0, 96.0
    s = []
    a = s.append
    # ears
    for sx in (-1, 1):
        a(f'<circle cx="{ox + sx * (R - 12):.1f}" cy="{oy + 22:.1f}" r="21" fill="{SKIN}" stroke="{INK}" stroke-width="6"/>')
    # neck
    a(f'<rect x="{ox - 30:.1f}" y="{oy + R - 40:.1f}" width="60" height="66" rx="12" fill="{SKIN}" stroke="{INK}" stroke-width="5"/>')
    # skull + shading
    a(f'<circle cx="{ox}" cy="{oy}" r="{R}" fill="{SKIN}" stroke="{INK}" stroke-width="6"/>')
    a(f'<path d="M{ox - 82} {oy + 52} A 88 88 0 0 0 {ox + 82} {oy + 52}" fill="none" stroke="{SKIN_SH}" stroke-width="7"/>')
    for sx in (-1, 1):
        a(f'<ellipse cx="{ox + sx * 56:.1f}" cy="{oy + 44:.1f}" rx="24" ry="10" fill="#ff8d85" opacity="0.55"/>')
    # hair
    a(f'<path d="M{ox - 102} {oy + 2} A 102 102 0 0 1 {ox + 102} {oy + 2} '
      f'Q {ox + 44} {oy - 36}, {ox - 6} {oy - 30} Q {ox - 58} {oy - 24}, {ox - 102} {oy + 2} Z" '
      f'fill="{HAIR}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>')
    a(f'<path d="M{ox - 62} {oy - 66} Q {ox - 14} {oy - 92}, {ox + 34} {oy - 74}" fill="none" '
      f'stroke="{HAIR_LT}" stroke-width="8" stroke-linecap="round" opacity="0.9"/>')
    a(f'<circle cx="{ox + 46}" cy="{oy - 62}" r="9" fill="{HAIR_LT}" opacity="0.9"/>')
    # glasses + eyes
    for sx in (-1, 1):
        gx, gy = ox + sx * 47, oy + 6
        a(f'<circle cx="{gx}" cy="{gy}" r="46" fill="#ffffff" opacity="0.92" stroke="{INK}" stroke-width="7"/>')
        if eyes == "open":
            a(f'<circle cx="{gx}" cy="{gy}" r="25" fill="#ffffff"/>')
            a(f'<circle cx="{gx}" cy="{gy}" r="14" fill="{INK}"/>')
            a(f'<circle cx="{gx - 6}" cy="{gy - 7}" r="5" fill="#ffffff"/>')
        elif eyes == "wide":
            a(f'<circle cx="{gx}" cy="{gy}" r="30" fill="#ffffff"/>')
            a(f'<circle cx="{gx}" cy="{gy}" r="16" fill="{INK}"/>')
            a(f'<circle cx="{gx - 8}" cy="{gy - 8}" r="6" fill="#ffffff"/>')
        elif eyes == "half":
            a(f'<path d="M{gx - 26} {gy + 2} a 26 26 0 0 0 52 0 z" fill="{INK}"/>')
            a(f'<path d="M{gx - 26} {gy} a 26 26 0 0 1 52 0" fill="none" stroke="{INK}" stroke-width="7"/>')
        elif eyes == "closed":
            a(f'<path d="M{gx - 26} {gy} a 26 26 0 0 0 52 0" fill="none" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>')
    a(f'<line x1="{ox - 6}" y1="{oy + 4}" x2="{ox + 6}" y2="{oy + 4}" stroke="{INK}" stroke-width="7"/>')
    a(f'<line x1="{ox - 93}" y1="{oy + 2}" x2="{ox - 88}" y2="{oy - 2}" stroke="{INK}" stroke-width="6"/>')
    a(f'<line x1="{ox + 93}" y1="{oy + 2}" x2="{ox + 88}" y2="{oy - 2}" stroke="{INK}" stroke-width="6"/>')
    # brows
    if brow == "up":
        a(f'<path d="M{ox - 66} {oy - 44} L {ox - 22} {oy - 54}" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>')
        a(f'<path d="M{ox + 22} {oy - 54} L {ox + 66} {oy - 44}" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>')
    elif brow == "sad":
        a(f'<path d="M{ox - 66} {oy - 52} L {ox - 22} {oy - 40}" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>')
        a(f'<path d="M{ox + 22} {oy - 40} L {ox + 66} {oy - 52}" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>')
    # mouth
    if mouth == "smile":
        a(f'<path d="M{ox - 30} {oy + 62} q 30 30 60 0" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>')
    elif mouth == "grin":
        a(f'<path d="M{ox - 34} {oy + 44} a 34 34 0 0 0 68 0 z" fill="#96343e" stroke="{INK}" stroke-width="5"/>')
        a(f'<path d="M{ox - 22} {oy + 64} a 22 22 0 0 0 44 0 z" fill="#ff808a"/>')
    elif mouth == "open":
        a(f'<ellipse cx="{ox}" cy="{oy + 74:.1f}" rx="26" ry="23" fill="#7c2834" stroke="{INK}" stroke-width="5"/>')
        a(f'<ellipse cx="{ox}" cy="{oy + 86:.1f}" rx="14" ry="9" fill="#ff7882"/>')
    a(f'<path d="M{ox - 12} {oy + 40} q 12 8 24 0" fill="none" stroke="{SKIN_SH}" stroke-width="5" stroke-linecap="round"/>')
    return 300, 320, "\n".join("    " + x for x in s), (150, 298)


# ---------------------------------------------------------------- body
def body_svg():
    ox, top = 170.0, 26.0
    s = []
    a = s.append
    a(f'<path d="M{ox - 84} {top + 44} L {ox - 102} {top + 118} L {ox - 84} {top + 236} '
      f'L {ox + 84} {top + 236} L {ox + 102} {top + 118} L {ox + 84} {top + 44} Z" fill="{HOOD}"/>')
    a(f'<ellipse cx="{ox}" cy="{top + 54}" rx="100" ry="44" fill="{HOOD}"/>')
    a(f'<rect x="{ox - 96}" y="{top + 86}" width="192" height="150" fill="{HOOD}"/>')
    # shading
    a(f'<g clip-path="url(#hoodclip)">'
      f'<ellipse cx="{ox - 40}" cy="{top + 130}" rx="105" ry="100" fill="{HOOD_D}" opacity="0.55"/>'
      f'<ellipse cx="{ox + 70}" cy="{top + 90}" rx="62" ry="66" fill="{HOOD_L}" opacity="0.7"/>'
      f'</g>')
    # hood collar
    a(f'<ellipse cx="{ox}" cy="{top + 34}" rx="62" ry="31" fill="{HOOD_D}" stroke="{INK}" stroke-width="6"/>')
    a(f'<ellipse cx="{ox}" cy="{top + 34}" rx="44" ry="19" fill="#21468e"/>')
    # outline
    a(f'<path d="M{ox - 84} {top + 44} L {ox - 102} {top + 118} L {ox - 84} {top + 236} '
      f'L {ox + 84} {top + 236} L {ox + 102} {top + 118} L {ox + 84} {top + 44}" fill="none" '
      f'stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>')
    a(f'<path d="M{ox - 100} {top + 54} a 100 44 0 0 1 200 0" fill="none" stroke="{INK}" stroke-width="7"/>')
    # drawstrings + pocket + zip
    for sx in (-1, 1):
        a(f'<line x1="{ox + sx * 34}" y1="{top + 56}" x2="{ox + sx * 38}" y2="{top + 122}" stroke="#eef4ff" stroke-width="7"/>')
        a(f'<circle cx="{ox + sx * 38}" cy="{top + 126}" r="9" fill="#eef4ff" stroke="#3a3e54" stroke-width="3"/>')
    a(f'<path d="M{ox - 64} {top + 136} L {ox - 64} {top + 182} L {ox - 30} {top + 200} '
      f'L {ox + 30} {top + 200} L {ox + 64} {top + 182} L {ox + 64} {top + 136}" fill="none" stroke="{HOOD_D}" stroke-width="6"/>')
    # shorts
    a(f'<rect x="{ox - 84}" y="198" width="168" height="68" rx="24" fill="{DENIM}" stroke="{INK}" stroke-width="7"/>')
    a(f'<rect x="{ox - 84}" y="242" width="168" height="24" fill="{DENIM_D}"/>')
    a(f'<line x1="{ox}" y1="208" x2="{ox}" y2="252" stroke="{DENIM_D}" stroke-width="6"/>')
    a(f'<circle cx="{ox}" cy="220" r="6" fill="#deba6a" stroke="#3a3e54" stroke-width="3"/>')
    a(f'<rect x="{ox - 88}" y="258" width="176" height="16" rx="10" fill="{DENIM_D}" stroke="{INK}" stroke-width="5"/>')
    defs = (f'<defs><clipPath id="hoodclip">'
            f'<path d="M{ox - 84} {top + 44} L {ox - 102} {top + 118} L {ox - 84} {top + 236} '
            f'L {ox + 84} {top + 236} L {ox + 102} {top + 118} L {ox + 84} {top + 44} Z"/>'
            f'<ellipse cx="{ox}" cy="{top + 54}" rx="100" ry="44"/>'
            f'<rect x="{ox - 96}" y="{top + 86}" width="192" height="150"/></clipPath></defs>')
    return 340, 280, defs + "\n" + "\n".join("    " + x for x in s), (170, 250)


# ---------------------------------------------------------------- limbs
def arm_upper_svg():
    ox = 60.0
    s = (f'<rect x="{ox - 26}" y="16" width="52" height="136" rx="24" fill="{HOOD}" stroke="{INK}" stroke-width="6"/>\n'
         f'    <rect x="{ox - 24}" y="22" width="16" height="120" rx="8" fill="{HOOD_D}" opacity="0.8"/>\n'
         f'    <rect x="{ox + 6}" y="22" width="18" height="90" rx="9" fill="{HOOD_L}" opacity="0.8"/>')
    return 120, 180, s, (60, 20)


def arm_fore_svg():
    ox = 60.0
    s = (f'<rect x="{ox - 26}" y="20" width="52" height="76" rx="24" fill="{HOOD_D}" stroke="{INK}" stroke-width="6"/>\n'
         f'    <ellipse cx="{ox}" cy="122" rx="26" ry="30" fill="{SKIN}" stroke="{INK}" stroke-width="6"/>\n'
         f'    <ellipse cx="{ox - 19}" cy="118" rx="13" ry="18" fill="{SKIN}" stroke="{INK}" stroke-width="5"/>\n'
         f'    <ellipse cx="{ox - 6}" cy="112" rx="11" ry="12" fill="{SKIN_LT}"/>')
    return 120, 200, s, (60, 22)


def leg_thigh_svg():
    ox = 55.0
    s = (f'<rect x="{ox - 24}" y="16" width="48" height="132" rx="23" fill="{SKIN}" stroke="{INK}" stroke-width="6"/>\n'
         f'    <rect x="{ox + 5}" y="20" width="21" height="126" rx="10" fill="{SKIN_SH}" opacity="0.8"/>')
    return 110, 180, s, (55, 22)


def leg_calf_svg():
    ox = 60.0
    s = (f'<rect x="{ox - 23}" y="16" width="46" height="96" rx="22" fill="{SKIN}" stroke="{INK}" stroke-width="6"/>\n'
         f'    <rect x="{ox + 5}" y="20" width="20" height="90" rx="10" fill="{SKIN_SH}" opacity="0.8"/>\n'
         f'    <rect x="{ox - 25}" y="100" width="50" height="56" rx="11" fill="#ffffff" stroke="{INK}" stroke-width="5"/>\n'
         f'    <rect x="{ox - 25}" y="130" width="50" height="26" rx="9" fill="#d8e2f6"/>\n'
         f'    <rect x="{ox - 48}" y="148" width="82" height="60" rx="24" fill="#343e5e" stroke="{INK}" stroke-width="6"/>\n'
         f'    <rect x="{ox - 48}" y="194" width="82" height="16" rx="8" fill="#ffffff" stroke="{INK}" stroke-width="5"/>\n'
         f'    <path d="M{ox - 24} 184 a 20 18 0 0 1 30 -14" fill="none" stroke="#76829e" stroke-width="5"/>')
    return 120, 210, s, (60, 22)


def pack_svg():
    ox = 75.0
    s = (f'<rect x="{ox - 58}" y="34" width="116" height="162" rx="34" fill="{PACK}" stroke="{INK}" stroke-width="7"/>\n'
         f'    <path d="M{ox - 58} 68 a 34 34 0 0 1 116 0 v 24 h -116 z" fill="{PACK_D}"/>\n'
         f'    <rect x="{ox - 36}" y="104" width="72" height="54" rx="16" fill="{PACK_D}" stroke="{INK}" stroke-width="5"/>\n'
         f'    <rect x="{ox - 20}" y="118" width="40" height="8" rx="4" fill="{PACK}"/>\n'
         f'    <path d="M{ox - 44} 44 L {ox - 20} 16" stroke="{PACK_D}" stroke-width="12" stroke-linecap="round"/>\n'
         f'    <path d="M{ox + 44} 44 L {ox + 20} 16" stroke="{PACK_D}" stroke-width="12" stroke-linecap="round"/>')
    return 150, 220, s, (75, 46)


def prism_svg():
    s = (f'<path d="M120 20 L 222 196 L 18 196 Z" fill="#baeaff" opacity="0.92" stroke="{INK}" stroke-width="6"/>\n'
         f'    <path d="M120 20 L 120 196 L 18 196 Z" fill="#ffffff" opacity="0.45"/>\n'
         f'    <path d="M60 120 L 150 70" stroke="#ffffff" stroke-width="6" opacity="0.6"/>')
    return 240, 220, s, (120, 190)


def sun_svg():
    ox = oy = 230.0
    s = []
    a = s.append
    for i in range(12):
        ang = math.radians(i * 30)
        x0, y0 = ox + math.cos(ang) * 150, oy + math.sin(ang) * 150
        x1, y1 = ox + math.cos(ang) * 205, oy + math.sin(ang) * 205
        a(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{SUN_D}" stroke-width="34" stroke-linecap="round"/>')
        a(f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="17" fill="{SUN_D}" stroke="{INK}" stroke-width="4"/>')
    a(f'<circle cx="{ox}" cy="{oy}" r="156" fill="{SUN}" stroke="{INK}" stroke-width="7"/>')
    a(f'<circle cx="{ox + 26}" cy="{oy + 40}" r="152" fill="{SUN_D}" opacity="0.55"/>')
    a(f'<circle cx="{ox - 46}" cy="{oy - 54}" r="74" fill="#ffeea0" opacity="0.85"/>')
    a(f'<path d="M{ox - 62} {oy + 26} q 24 24 48 0" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>')
    a(f'<path d="M{ox + 14} {oy + 26} q 24 24 48 0" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>')
    for sx in (-1, 1):
        a(f'<ellipse cx="{ox + sx * 42}" cy="{oy + 43}" rx="20" ry="13" fill="#ff8d85" opacity="0.55"/>')
    return 460, 460, "\n".join("    " + x for x in s), (230, 230)


def cloud_svg():
    s = ('<ellipse cx="140" cy="146" rx="62" ry="60" fill="#fff"/>'
         '<ellipse cx="208" cy="110" rx="78" ry="76" fill="#fff"/>'
         '<ellipse cx="286" cy="122" rx="70" ry="68" fill="#fff"/>'
         '<ellipse cx="354" cy="152" rx="54" ry="52" fill="#fff"/>'
         '<ellipse cx="250" cy="160" rx="74" ry="58" fill="#fff"/>'
         '<rect x="90" y="140" width="322" height="72" rx="36" fill="#fff"/>')
    return 520, 250, s, (260, 160)


if __name__ == "__main__":
    parts = {
        "head_smile": head_svg("smile", "open"),
        "head_open": head_svg("open", "wide", "up"),
        "head_grin": head_svg("grin", "wide"),
        "head_blink": head_svg("smile", "closed"),
        "head_half": head_svg("smile", "half"),
        "head_think": head_svg("smile", "half", "sad"),
        "body": body_svg(),
        "arm_upper": arm_upper_svg(),
        "arm_fore": arm_fore_svg(),
        "leg_thigh": leg_thigh_svg(),
        "leg_calf": leg_calf_svg(),
        "pack": pack_svg(),
        "prism": prism_svg(),
        "sun": sun_svg(),
        "cloud": cloud_svg(),
    }
    for name, (w, h, body, pivot) in parts.items():
        write(name, w, h, body, pivot)
    json.dump(PIVOTS, open(os.path.join(OUT, "pivots.json"), "w"), indent=2)
    print("wrote", len(parts), "svg files to", OUT)
