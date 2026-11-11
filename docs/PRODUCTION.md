# Production log — "Why Is The Sky Blue?"

## Pipeline actually used

| Stage | Tool | Output |
|---|---|---|
| Vector art authoring | SVG (hand-authored primitives, Inkscape-compatible, `data-pivot` per group) | `art/svg/*.svg` (15 parts + backgrounds) |
| Rig + animation | Python 2-bone IK cut-out rig (`tools/rig.py`) — the same skeleton the Godot project rebuilds | posed frames |
| Shot composition | `tools/scenes.py` + `tools/renderer.py` — camera, glow, grain, vignette, crossfades | 900 frames @ 1080×1920 |
| Engine parity build | Godot 3.6 project (`godot/`) with the identical skeleton, live in-engine | `SunnyRig.gd` |
| Encoding | ffmpeg (imageio) H.264 + AAC | `render/*.mp4` |

This environment has no GUI, so Krita / OpenToonz / Pencil2D / Synfig / Pixelorama
cannot be launched here. Everything those tools would produce was therefore
authored in their **native file formats**: layered vector parts (`.svg`, importable
into Inkscape and Synfig as bone-ready groups), per-part PNG sprites with explicit
pivots (Krita / OpenToonz layer stack), and a live Godot project that rebuilds the
rig in-engine.

## Fixes made while animating

1. **Rotation cropped limbs** — `_place()` rotated the raw sprite and cut it at the
   canvas edge; now every limb is padded around its pivot before rotating.
2. **FK direction on the second arm** — a positive elbow angle used to fold one arm
   into the torso; FK angles are now mirrored per side.
3. **Scale units** — the rig originally mixed design units with pixels, producing
   duplicate feet/shoes at large zooms. All skeleton numbers are now design units
   multiplied by a single `unit` factor.
4. **Head/torso proportion** — after adding knees and elbows the character was
   ~6.5 heads tall; segment lengths were retuned to 128/128 (legs) and 124/100
   (arms) for a 5-head cartoon build.
5. **Blocking** — the sun, captions and question mark were moved out of the
   character's silhouette; captions now pop over the letterbox strip.
6. **Confetti depth** — confetti used to fall in front of the face; it is now
   composited behind the character.

## Deliverables

* `render/why-is-the-sky-blue.mp4` — master, 1080×1920, 30 fps, 30.00 s
* `render/why-is-the-sky-blue-share.mp4` — 720×1280 share copy
* `art/svg/` — editable vector master of every part
* `godot/` — live rig project (open in Godot 3.6, press Play)
