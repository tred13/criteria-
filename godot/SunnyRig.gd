extends Node2D
# ============================================================
#  Sunny — 2-bone IK cut-out rig
#  The same skeleton the film was rendered with (see ../tools/rig.py).
#  Parts come from art/svg -> assets/*.png with explicit pivots.
# ============================================================

const HIP_W := 40.0
const SHOULDER_W := 76.0
const SHOULDER_Y := -190.0
const HEAD_Y := -168.0
const PACK := Vector2(-62, -232)
const THIGH := 128.0
const CALF := 128.0
const UPPER := 124.0
const FORE := 100.0
const SOLE := 256.0

# part -> pivot inside its own texture (px)
const PIVOTS := {
	"head_smile": Vector2(150, 298), "head_open": Vector2(150, 298),
	"head_grin": Vector2(150, 298), "head_blink": Vector2(150, 298),
	"head_half": Vector2(150, 298), "head_think": Vector2(150, 298),
	"body": Vector2(170, 250),
	"arm_upper": Vector2(60, 20), "arm_fore": Vector2(60, 22),
	"leg_thigh": Vector2(55, 22), "leg_calf": Vector2(60, 22),
	"pack": Vector2(75, 46), "prism": Vector2(120, 190),
}

var nodes := {}        # name -> Sprite
var hip := Vector2(540, 1300)
var unit := 1.6        # pixels per design unit

func _ready() -> void:
	_make("pack")
	_make("leg_thigh", "leg_thigh_l")
	_make("leg_calf", "leg_calf_l")
	_make("leg_thigh", "leg_thigh_r")
	_make("leg_calf", "leg_calf_r")
	_make("body")
	_make("arm_upper", "arm_upper_l")
	_make("arm_fore", "arm_fore_l")
	_make("arm_upper", "arm_upper_r")
	_make("arm_fore", "arm_fore_r")
	_make("head_smile")
	set_pose({})
	demo()

func _make(part: String, key: String = "") -> void:
	var k = key if key != "" else part
	var s := Sprite.new()
	s.texture = load("res://assets/%s.png" % part)
	s.centered = false
	add_child(s)
	nodes[k] = s

func _place(key: String, at: Vector2, rot := 0.0) -> void:
	var s: Sprite = nodes[key]
	var part = key
	if key.ends_with("_l") or key.ends_with("_r"):
		part = key.substr(0, key.length() - 2)
	var pv: Vector2 = PIVOTS[part] * unit
	s.scale = Vector2(unit, unit)
	s.rotation = rot
	s.position = at - pv.rotated(rot)

func _ik(root: Vector2, target: Vector2, l1: float, l2: float, bend: float) -> Array:
	var d := clamp((target - root).length(), 1.0, (l1 + l2) * 0.998)
	var a := (target - root).angle()
	var ca := clamp((d * d + l1 * l1 - l2 * l2) / (2.0 * d * l1), -1.0, 1.0)
	var ang := acos(ca)
	var j := root + Vector2(cos(a + bend * ang), sin(a + bend * ang)) * l1
	var e := root + Vector2(cos(a), sin(a)) * d
	return [j, e]

# --- pose API: every value is hip-relative, in design units -------------
func set_pose(p: Dictionary) -> void:
	var head_part = p.get("head", "head_smile")
	if not nodes.has(head_part):
		_make(head_part)
	for k in nodes.keys():
		if k.begins_with("head"):
			nodes[k].visible = (k == head_part)

	var hy := hip + Vector2(0, p.get("hip_dy", 0.0) * unit)
	var legs := [["leg_thigh_l", "leg_calf_l", p.get("foot_l", Vector2(-62, SOLE)), p.get("leg_l", 0.04)],
				 ["leg_thigh_r", "leg_calf_r", p.get("foot_r", Vector2(62, SOLE)), p.get("leg_r", -0.04)]]
	for spec in legs:
		var root := hy + Vector2(-HIP_W if spec[0].ends_with("_l") else HIP_W, 0) * unit
		var tgt: Vector2 = hy + spec[2] * unit
		var j = _ik(root, tgt, THIGH * unit, CALF * unit, 1.0)
		_place(spec[0], root, (j[0] - root).angle() - PI / 2)
		_place(spec[1], j[0], (j[1] - j[0]).angle() - PI / 2)

	_place("pack", hy + PACK * unit, p.get("pack_rot", -0.05))
	_place("body", hy, 0.0)

	var arms := [["arm_upper_l", "arm_fore_l", p.get("hand_l", null), p.get("arm_l", -0.16)],
				 ["arm_upper_r", "arm_fore_r", p.get("hand_r", null), p.get("arm_r", 0.16)]]
	for spec in arms:
		var side := -1.0 if spec[0].ends_with("_l") else 1.0
		var root := hy + Vector2(side * SHOULDER_W, SHOULDER_Y) * unit
		var tgt: Vector2
		if spec[2] == null:
			tgt = root + Vector2(spec[3] * side * UPPER, -UPPER) * unit
		else:
			tgt = hy + spec[2] * unit
		var j = _ik(root, tgt, UPPER * unit, FORE * unit, -1.0 if side < 0 else 1.0)
		_place(spec[0], root, (j[0] - root).angle() - PI / 2)
		_place(spec[1], j[0], (j[1] - j[0]).angle() - PI / 2)

	_place(head_part, hy + Vector2(0, HEAD_Y + p.get("head_dy", 0.0)) * unit, p.get("head_rot", 0.0))

# --- a looping demo: wave, point, float, cheer --------------------------
func demo() -> void:
	var t := 0.0
	var tw := Tween.new()
	add_child(tw)
	tw.interpolate_method(self, "_demo_tick", 0.0, 1.0, 12.0, Tween.TRANS_LINEAR, Tween.EASE_IN_OUT)
	tw.repeat = true
	tw.play()

func _demo_tick(_v: float) -> void:
	var t = OS.get_ticks_msec() / 1000.0
	var wave := sin(t * 3.4) * 18.0
	set_pose({
		"head": "head_open",
		"hand_r": Vector2(150 + wave, -330),
		"hand_l": Vector2(-150, -10 + sin(t * 2.0) * 8),
		"hip_dy": sin(t * 2.4) * 4.0,
		"head_rot": -0.08 + sin(t * 1.6) * 0.04,
	})
