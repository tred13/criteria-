# Why Is The Sky Blue? — 2D animated explainer (9:16, 30 s)

A curiosity-driven explainer about **Rayleigh scattering**, built as a real
cut-out 2D animation: a rigged character with a 2-bone IK skeleton, hand-built
vector art, six composed shots, and a frame-accurate compositor.

| | |
|---|---|
| **Format** | 1080 × 1920 (9:16 vertical) • 30 fps • 30.00 s |
| **Audio** | narrated voice-over, mixed at −3 dBFS peak |
| **Character** | *Sunny* — curious kid, messy hair, round glasses, blue hoodie, yellow backpack |
| **Style** | flat-vector cartoon explainer with soft shadows, rim light, glow and grain |
| **Topic** | Rayleigh scattering → why the sky is blue, and why sunsets go red |

---

## The game — RAYLEIGH RUN

`godot/game/` is a playable 2D pixel platformer (Godot 4.4): collect the light
orbs before the sun sets. Art is real pixel art authored pixel-by-pixel in
`tools/pixel.py`, with editable Pixelorama projects in `art/pixelorama/`.
The `Game check` workflow boots the game headless, then captures gameplay under
Xvfb and publishes it as a release asset.

| | |
|---|---|
| Input | ← → / A D run · Space / ↑ / W jump · R restart |
| Art | 32×32 hero, 16×16 tiles, 18-colour palette, nearest-neighbour |
| Docs | [`docs/GAME.md`](docs/GAME.md) |

## Where the video comes from

**Rendering happens on GitHub, not in any agent sandbox.** The
[`Render film`](.github/workflows/render.yml) workflow renders all 900 frames,
mixes the voice-over and publishes `why-is-the-sky-blue.mp4` as a GitHub
Release asset. Everything — source, assets, docs, the film — lives in this
repository. See `RENDER_POLICY.md`.

```bash
curl -X POST -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/tred13/criteria-/actions/workflows/render.yml/dispatches \
  -d '{"ref":"main","inputs":{"start":"0","end":"900"}}'
```

---

## Shot list

| # | Time | Shot | What moves |
|---|------|------|-----------|
| 1 | 0:00–0:04 | **The hook** — Sunny walks in, stops, points at the sun, title pops | walk cycle (IK feet), arm point, head turn, blinking, drifting clouds |
| 2 | 0:04–0:09 | **A secret rainbow** — he lifts a prism, white light splits into seven beams | arm raise, prism tilt, growing beams, glow |
| 3 | 0:09–0:16 | **The collision** — he floats inside the atmosphere, blue packets bounce everywhere | floating rig, drifting molecules, bouncing light streaks |
| 4 | 0:16–0:22 | **Your eyes** — rays converge into his glasses | converging rays, wide-open arms, sparkles |
| 5 | 0:22–0:27 | **The sunset twist** — low orange sun, embers rising | sway, salute, rising embers, warm rim light |
| 6 | 0:27–0:30 | **Payoff** — celebration jumps, confetti | jump arcs, squash/stretch, confetti, blinking |

## The rig (how the animation works)

```
hip ──┬── leg_thigh ── leg_calf ── sneaker      (2-bone IK, feet on targets)
      ├── body ── arm_upper ── arm_fore ── hand (2-bone IK, hands on targets)
      ├── pack
      └── head (6 expression swaps: smile / open / grin / blink / half / think)
```

* Every part is drawn on its own canvas with an explicit **pivot** (`art/svg/pivots.json`).
* Limbs are solved with **two-bone IK** so a foot can be planted on the ground
  while the hip bobs — the classic cut-out animation workflow.
* Walking, floating, gesturing and jumping are all driven by the same API:
  `hand_l`, `hand_r`, `foot_l`, `foot_r`, `hip_dy`, `head`, `head_rot`.

## Repository layout

```
art/svg/            vector master of every part (Inkscape / Synfig ready) + pivots.json
art/fonts/          Baloo 2 (OFL) — the film's display face
tools/make_svg.py   writes the SVG masters (each group carries data-pivot)
tools/rig.py        2-bone IK cut-out rig (pure python reference implementation)
tools/scenes.py     skies, hills, clouds, title card, caption chips
tools/renderer.py   the six shots + compositor (camera, glow, grain, crossfades)
tools/render_par.py parallel frame renderer
godot/              Godot 3.6 project: SunnyRig.gd + assets/ (same skeleton, live)
godot/assets/       every part as PNG with pivots, backgrounds, captions
docs/               script, storyboard, science notes, production log
render/             final video files
```

## Using the package

Edit the vectors in `art/svg/`, pose the rig with `tools/rig.py`, or open the
Godot project and animate live. Rendering is a GitHub Action — see above.

The Godot project is live: open `godot/project.godot` in Godot 3.6 and press
Play — `SunnyRig.gd` rebuilds the skeleton from `assets/rig_pivots.json` and
runs a wave / point / float demo.

## Science (one paragraph, no hand-waving)

Sunlight is a mix of wavelengths. Air molecules (N₂, O₂) are far smaller than
the light's wavelength, so they scatter *Rayleigh*-style: intensity ∝ 1/λ⁴.
Violet scatters most, but our eyes are much less sensitive to it and ozone
absorbs part of it, so the sky reads **blue**. At sunset the light travels a
much longer path through the atmosphere, the blue is scattered out of the beam,
and the reds and oranges are what reach your eyes.

## Credits

Art, rig, animation and compositing generated procedurally for this project.
Type: **Baloo 2** (SIL Open Font License). Voice-over synthesised for this film.
