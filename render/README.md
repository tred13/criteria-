# render/

This folder is intentionally empty of video output.

The project ships as **editable source**, not as a pre-rendered file:
open `godot/project.godot` in Godot 3.6 and press Play, or import
`art/svg/*.svg` into Inkscape / Synfig to animate the rig yourself.

To make a video locally (on your own machine, never here):

    python3 tools/render_par.py    # frames/
    python3 tools/mux.py           # render/*.mp4
