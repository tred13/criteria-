# RAYLEIGH RUN — 2D pixel platformer

A one-screen platformer starring the kid from *Why Is The Sky Blue?*.
Collect every light orb before the sun goes down.

| | |
|---|---|
| Engine | **Godot 4.4** (GL Compatibility) |
| Art | **Pixel Art**, 32×32 character, 16×16 tiles — Pixelorama project files included |
| Resolution | 960×540 (nearest-neighbour filtering, no smoothing) |
| Input | ← → / A D to run, Space / ↑ / W to jump, R to restart |
| Files | `godot/game/` (project), `art/pixel/` (PNG sheets), `art/pixelorama/` (editable `.pxo`) |

## How it plays

* Momentum-based running with coyote time (0.10 s) and a jump buffer (0.12 s) —
  jumps feel forgiving, not floaty.
* Variable jump height: release the jump key early and the kid cuts the arc.
* Squash & stretch is applied to the *sprite*, never the collider, so the hitbox
  stays predictable.
* Orbs bob and rotate; spikes cost a heart and respawn you at the start.
* 99-second timer. Clear every orb to win. Lose all 3 hearts or run out of time
  and the sun goes down.

## Level format

The whole level is a string map in `scripts/Game.gd` — edit and re-run:

```
'#' ground   '=' platform   'o' orb   '^' spike   'P' start
```

## Building the art

```bash
python3 tools/pixel.py      # sprites, tiles, parallax layers, .pxo projects
```

`art/pixelorama/kid.pxo` opens in Pixelorama with four layers
(legs / body / hair / glasses) across eight frames.
`art/pixelorama/tiles.pxo` holds the four tiles.

## Playing / exporting

Open `godot/game/project.godot` in Godot 4.4 and press Play.
Export templates are not included; use *Project → Export* after installing them.
