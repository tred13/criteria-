extends Node2D
# ============================================================
#  RAYLEIGH RUN — a one-screen pixel platformer about a kid
#  collecting light orbs before the sun sets.
#
#  Everything is built in code at _ready(): the sky, the parallax
#  hills, the tilemap, the player (AnimatedSprite2D from the pixel
#  sheet), the orbs, the spike hazards, the HUD and the audio.
#  Art comes from art/pixel/ (Pixelorama-friendly 32px sprites).
# ============================================================

const TILE := 16
const GRAVITY := 900.0
const RUN_SPEED := 132.0
const JUMP_V := -380.0
const COYOTE := 0.10
const JUMP_BUFFER := 0.12

var player: CharacterBody2D
var spr: AnimatedSprite2D
var cam: Camera2D
var orbs: Array = []
var spikes: Array = []
var hearts: Array = []
var score := 0
var lives := 3
var time_left := 99.0
var state := "play"          # play | win | over
var t := 0.0
var coyote := 0.0
var buffer := 0.0
var facing := 1
var hud: Label
var banner: Label
var tint: ColorRect
var pickups: AudioStreamPlayer

# --------------------------------------------------------- level data
# '#' ground, '=' platform, 'o' orb, '^' spike, 'P' start
	const LEVEL := [
		"................................................",
		"................................................",
		"................................................",
		"...................................o............",
		".........................o......................",
		".................................=====..........",
		".......................====......=====..........",
		".............o.........====.....................",
		"...............................o................",
		"...........=====................................",
		".....o.....=====....o........=====......o.......",
		".............................=====..............",
		"...=====..........=====...............=====.....",
		"..P=====........o.=====...............=====..o..",
		".................^^.............................",
		"##########################..####################",
		"##########################..####################",
		"##########################..####################",
	]

var width := 48
var height := 18

# --------------------------------------------------------- build
func _ready() -> void:
	randomize()
	autopilot = OS.has_feature("editor") and false
	for a in OS.get_cmdline_user_args():
		if a == "--autopilot":
			autopilot = true
	_build_background()
	_build_tiles()
	_build_player()
	_build_hud()
	_build_audio()
	cam = Camera2D.new()
	cam.position = Vector2(480, 270)
	cam.limit_left = 0
	cam.limit_right = width * TILE
	cam.limit_top = 0
	cam.limit_bottom = height * TILE
	add_child(cam)
	cam.make_current()

func _tex(path: String) -> ImageTexture:
	return ImageTexture.create_from_image(Image.load_from_file(path))

func _sprite_node(path: String, region: Rect2, px: int, pos: Vector2) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = _tex(path)
	s.region_enabled = true
	s.region_rect = region
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	s.centered = true
	s.scale = Vector2(px, px)
	s.position = pos
	add_child(s)
	return s

func _build_background() -> void:
	var layer := Node2D.new()
	layer.z_index = -20
	add_child(layer)

	# tiled sky
	for i in 4:
		var s := Sprite2D.new()
		s.texture = _tex("res://assets/bg_sky.png")
		s.centered = false
		s.region_enabled = false
		s.position = Vector2(i * 320, 0)
		s.scale = Vector2(0.75, 0.75)
		layer.add_child(s)

	# parallax hills + clouds drawn as horizontal repeats
	var far := Node2D.new()
	far.z_index = -18
	add_child(far)
	for i in 4:
		var s := Sprite2D.new()
		s.texture = _tex("res://assets/bg_hills_far.png")
		s.centered = false
		s.position = Vector2(i * 320, 0)
		s.scale = Vector2(0.75, 0.75)
		s.set_meta("parallax", 0.25)
		far.add_child(s)
	set_meta("far", far)

	var near := Node2D.new()
	near.z_index = -16
	add_child(near)
	for i in 4:
		var s := Sprite2D.new()
		s.texture = _tex("res://assets/bg_hills_near.png")
		s.centered = false
		s.position = Vector2(i * 320, 0)
		s.scale = Vector2(0.75, 0.75)
		near.add_child(s)
	set_meta("near", near)

	var clouds := Node2D.new()
	clouds.z_index = -17
	add_child(clouds)
	for i in 4:
		var s := Sprite2D.new()
		s.texture = _tex("res://assets/bg_clouds.png")
		s.centered = false
		s.position = Vector2(i * 320, 0)
		s.scale = Vector2(0.75, 0.75)
		clouds.add_child(s)
	set_meta("clouds", clouds)

func _build_tiles() -> void:
	var body := StaticBody2D.new()
	body.z_index = -1
	add_child(body)

	for y in LEVEL.size():
		var row: String = LEVEL[y]
		for x in row.length():
			var ch := row[x]
			var pos := Vector2(x * TILE + TILE / 2, y * TILE + TILE / 2)
			if ch == "#" or ch == "=":
				var region: Rect2
				if ch == "=":
					region = Rect2(0, 0, TILE, TILE)          # grass slab
				elif y > 0 and LEVEL[y - 1][x] == "#":
					region = Rect2(0, 0, TILE, TILE)
				elif y > 6:
					region = Rect2(16, 0, TILE, TILE)         # dirt
				else:
					region = Rect2(0, 0, TILE, TILE)
				if y >= 10:
					region = Rect2(16, 0, TILE, TILE)
				var s := _sprite_node("res://assets/tiles.png", region, 1, pos)
				s.z_index = -1
				var cs := CollisionShape2D.new()
				var rect := RectangleShape2D.new()
				rect.size = Vector2(TILE, TILE)
				cs.shape = rect
				cs.position = pos
				body.add_child(cs)
			elif ch == "o":
				_add_orb(pos)
			elif ch == "^":
				_add_spike(pos)
			elif ch == "P":
				set_meta("start", pos)

func _add_orb(pos: Vector2) -> void:
	var s := _sprite_node("res://assets/props.png", Rect2(0, 0, 12, 12), 1, pos)
	s.z_index = 1
	s.set_meta("base_y", pos.y)
	s.set_meta("phase", randf() * TAU)
	orbs.append(s)

func _add_spike(pos: Vector2) -> void:
	var s := _sprite_node("res://assets/props.png", Rect2(28, 0, 16, 12), 1, pos + Vector2(0, 2))
	s.z_index = 1
	s.set_meta("pos", pos)
	spikes.append(s)

func _build_player() -> void:
	var start: Vector2 = get_meta("start", Vector2(64, 64))
	player = CharacterBody2D.new()
	player.position = start
	player.z_index = 5
	add_child(player)

	var cs := CollisionShape2D.new()
	var cap := CapsuleShape2D.new()
	cap.radius = 5.0
	cap.height = 20.0
	cs.shape = cap
	cs.position = Vector2(0, 4)
	player.add_child(cs)

	spr = AnimatedSprite2D.new()
	var frames := SpriteFrames.new()
	frames.remove_animation("default")
	for anim in [["idle", [0, 1], 4.0], ["run", [2, 3, 4, 5], 12.0],
				 ["jump", [6], 1.0], ["fall", [7], 1.0]]:
		frames.add_animation(anim[0])
		frames.set_animation_speed(anim[0], anim[2])
		frames.set_animation_loop(anim[0], anim[0] != "jump" and anim[0] != "fall")
		for i in anim[1]:
			var at := AtlasTexture.new()
			at.atlas = _tex("res://assets/kid.png")
			at.region = Rect2(i * 32, 0, 32, 32)
			frames.add_frame(anim[0], at)
	spr.sprite_frames = frames
	spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	spr.position = Vector2(0, -6)
	spr.play("idle")
	player.add_child(spr)

func _build_hud() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)

	hud = Label.new()
	hud.position = Vector2(16, 10)
	hud.add_theme_font_size_override("font_size", 20)
	hud.add_theme_color_override("font_color", Color(1, 1, 1))
	hud.add_theme_color_override("font_shadow_color", Color(0.1, 0.1, 0.2, 0.9))
	hud.add_theme_constant_override("shadow_offset_x", 2)
	hud.add_theme_constant_override("shadow_offset_y", 2)
	layer.add_child(hud)

	for i in 3:
		var h := TextureRect.new()
		h.texture = _tex("res://assets/props.png")
		h.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		h.stretch_mode = TextureRect.STRETCH_KEEP
		var at := AtlasTexture.new()
		at.atlas = h.texture
		at.region = Rect2(46, 2, 9, 9)
		h.texture = at
		h.scale = Vector2(2, 2)
		h.position = Vector2(960 - 90 + i * 26, 14)
		layer.add_child(h)
		hearts.append(h)

	banner = Label.new()
	banner.position = Vector2(0, 210)
	banner.size = Vector2(960, 80)
	banner.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	banner.add_theme_font_size_override("font_size", 40)
	banner.add_theme_color_override("font_color", Color(1, 0.9, 0.35))
	banner.add_theme_color_override("font_outline_color", Color(0.1, 0.1, 0.2, 1))
	banner.add_theme_constant_override("outline_size", 10)
	banner.text = ""
	layer.add_child(banner)

	tint = ColorRect.new()
	tint.color = Color(1, 1, 1, 0)
	tint.size = Vector2(960, 540)
	tint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(tint)

func _build_audio() -> void:
	pickups = AudioStreamPlayer.new()
	var gen := AudioStreamGenerator.new()
	gen.mix_rate = 22050.0
	gen.buffer_length = 0.12
	pickups.stream = gen
	add_child(pickups)
	pickups.play()

# --------------------------------------------------------- input
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_SPACE or event.keycode == KEY_UP or event.keycode == KEY_W:
			buffer = JUMP_BUFFER
		if event.keycode == KEY_R and state != "play":
			get_tree().reload_current_scene()

var autopilot := false
var _auto_t := 0.0


func _hold_left() -> bool:
	if autopilot:
		return _auto_dir() < 0
	return Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A)
func _hold_right() -> bool:
	if autopilot:
		return _auto_dir() > 0
	return Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D)


func _auto_dir() -> int:
	# seek the nearest orb that is above and ahead, otherwise run right
	if player == null or orbs.is_empty():
		return 1
	var best: Sprite2D = null
	var bd := 1e9
	for o in orbs:
		var d: float = abs(o.position.x - player.position.x)
		if d < bd:
			bd = d
			best = o
	if best == null:
		return 1
	return 1 if best.position.x >= player.position.x - 6 else -1


func _auto_jump() -> bool:
	if not autopilot:
		return Input.is_key_pressed(KEY_SPACE) or Input.is_key_pressed(KEY_UP) or Input.is_key_pressed(KEY_W)
	if player == null or not player.is_on_floor():
		return true
	# jump when an orb sits above, or a wall/edge is close
	for o in orbs:
		if abs(o.position.x - player.position.x) < 46 and o.position.y < player.position.y - 14:
			return true
	var ahead := Vector2(player.position.x + 18 * facing, player.position.y + 26)
	var probe := PhysicsPointQueryParameters2D.new()
	probe.position = ahead
	probe.collision_mask = 1
	var hits := get_world_2d().direct_space_state.intersect_point(probe)
	if hits.is_empty():
		return true
	return false

# --------------------------------------------------------- loop
func _physics_process(delta: float) -> void:
	t += delta
	_parallax()
	_follow_camera()

	if state == "play":
		time_left = max(0.0, time_left - delta)
		_move_player(delta)
		_collect()
		_hazards()
		if orbs.is_empty():
			_win()
		elif time_left <= 0.0 or lives <= 0:
			_lose()

	hud.text = "ORBS  %d      TIME  %02d      LIVES  %d" % [score, int(ceil(time_left)), lives]

func _follow_camera() -> void:
	if cam == null or player == null:
		return
	var want := Vector2(clamp(player.position.x + 40 * facing, 480, width * TILE - 480),
						clamp(player.position.y - 40, 270, height * TILE - 270))
	cam.position = cam.position.lerp(want, 0.12)


func _parallax() -> void:
	var cx := cam.position.x
	for key in ["far", "near", "clouds"]:
		var n: Node2D = get_meta(key)
		var k := 0.25 if key == "far" else (0.45 if key == "clouds" else 0.6)
		for c in n.get_children():
			var sp: Sprite2D = c
			sp.position.x = c.get_index() * 320 * 0.75 - cx * k

func _move_player(delta: float) -> void:
	var v := player.velocity
	var dir := 0.0
	if _hold_left():
		dir -= 1.0
	if _hold_right():
		dir += 1.0
	if dir != 0.0:
		facing = int(dir)
	v.x = move_toward(v.x, dir * RUN_SPEED, 900.0 * delta)
	v.y += GRAVITY * delta

	if player.is_on_floor():
		coyote = COYOTE
	else:
		coyote = max(0.0, coyote - delta)
	buffer = max(0.0, buffer - delta)
	if autopilot and _auto_jump() and coyote > 0.0:
		buffer = JUMP_BUFFER
	if buffer > 0.0 and coyote > 0.0:
		v.y = JUMP_V
		buffer = 0.0
		coyote = 0.0
		_sfx(660.0, 0.09)

	# variable jump height
	if v.y < 0 and not _auto_jump():
		v.y += 1100.0 * delta

	player.velocity = v
	player.move_and_slide()
	player.position.x = clamp(player.position.x, 8, width * TILE - 8)
	player.position.y = min(player.position.y, height * TILE + 40)

	spr.flip_h = facing < 0
	if player.is_on_floor():
		spr.play("run" if abs(v.x) > 12 else "idle")
	else:
		spr.play("jump" if v.y < 0 else "fall")
	# squash & stretch on the sprite, not the collider
	var target := Vector2(1, 1)
	if not player.is_on_floor():
		target = Vector2(0.88, 1.14) if v.y < 0 else Vector2(1.1, 0.9)
	spr.scale = spr.scale.lerp(target, 0.25)

	if player.position.y > height * TILE + 30:
		_hurt(true)

func _collect() -> void:
	for o in orbs.duplicate():
		var s: Sprite2D = o
		s.position.y = s.get_meta("base_y") + sin(t * 3.0 + s.get_meta("phase")) * 3.0
		s.rotation = sin(t * 2.0 + s.get_meta("phase")) * 0.25
		if player.position.distance_to(s.position) < 15.0:
			orbs.erase(s)
			score += 1
			s.queue_free()
			_sfx(880.0 + score * 25.0, 0.06)

func _hazards() -> void:
	for sp in spikes:
		var p: Vector2 = sp.get_meta("pos")
		if abs(player.position.x - p.x) < 12 and abs(player.position.y - p.y) < 14:
			_hurt(false)
			return

func _hurt(fell: bool) -> void:
	lives -= 1
	_shake()
	_sfx(180.0, 0.18)
	if hearts.size() > lives and lives >= 0:
		(hearts[lives] as TextureRect).texture.region = Rect2(46, 14, 9, 9)
	if lives <= 0:
		_lose()
		return
	var start: Vector2 = get_meta("start", Vector2(64, 64))
	player.position = start
	player.velocity = Vector2.ZERO

func _shake() -> void:
	var tw := create_tween()
	for i in 4:
		tw.tween_property(cam, "offset", Vector2(randf_range(-5, 5), randf_range(-5, 5)), 0.03)
	tw.tween_property(cam, "offset", Vector2.ZERO, 0.08)

func _sfx(freq: float, dur: float) -> void:
	var pb := pickups.get_stream_playback() as AudioStreamGeneratorPlayback
	if pb == null:
		return
	var rate := 22050.0
	var n := int(rate * dur)
	for i in n:
		var k := 1.0 - float(i) / n
		var v := sin(TAU * freq * float(i) / rate) * 0.25 * k * k
		pb.push_frame(Vector2(v, v))

func _win() -> void:
	state = "win"
	banner.text = "SKY SOLVED!\n\nSPACE — no, press R to play again"
	var tw := create_tween()
	tw.tween_property(tint, "color", Color(0.6, 0.85, 1.0, 0.22), 0.6)

func _lose() -> void:
	state = "over"
	banner.text = "THE SUN WENT DOWN\n\npress R to try again"
	var tw := create_tween()
	tw.tween_property(tint, "color", Color(0.10, 0.06, 0.20, 0.45), 0.6)
