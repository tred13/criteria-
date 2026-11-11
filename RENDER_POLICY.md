# RENDER POLICY — HARD RULE

**No rendering. No frame generation. No video export. Ever.**

This project is delivered as editable source only:

* vector masters (`art/svg/`)
* rig + animation code (`tools/`, `godot/`)
* documentation (`docs/`)

Any agent or contributor working on this repository must **not** run
`renderer.py`, `render_par.py`, `mux.py`, `godot --export`, ffmpeg, or any
other frame/video generation step. Exporting is the user's decision on the
user's own machine.
