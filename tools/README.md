# tools/

Reference implementation of the production pipeline. Reading / editing these
is encouraged; **executing the frame or video generators is not** (see
`../RENDER_POLICY.md`).

| file | role |
|---|---|
| `art.py` | drawing primitives: canvas with 4× supersampling, palette, sprite parts, typography |
| `rig.py` | 2-bone IK cut-out rig — the skeleton every shot poses |
| `scenes.py` | skies, hills, clouds, molecules, title card, caption chips |
| `renderer.py` | the six-shot timeline / compositor (offsets, camera, glow, grain, transitions) |
| `make_svg.py` | writes the vector masters in `art/svg/` with per-part `data-pivot` |
| `mux.py` | reference ffmpeg assembly (kept for documentation, not for use here) |
