class_name PremiershipStreamers
extends Control
## Paper streamers in the premiers' two colours, falling once over the finals
## series when it opens with the flag decided (director, 2026-11-04: particles
## only for the premiership and the Brownlow winner reveal; nowhere else).
## They fall from the top, thin out before the sheet's button and are gone in
## under four seconds: the node frees itself and nothing plays again until the
## series is opened another time. A finger goes straight through them. A look
## only: it reads the premier's code and changes nothing.

## The whole fall, in seconds; the last streamer has faded by then.
const DURATION := 3.6
## The last streamer lets go this long after the first.
const STAGGER := 0.9
## A streamer fades out over this many pixels above the line it must stay clear of.
const FADE := 140.0
## With nothing to stay clear of, they are gone by this share of the height.
const FLOOR := 0.8
const SEED := 20261104

var club := ""
## The premiers' two colours on the dark page: first ink, then second.
var colours: Array[Color] = []
## The control no streamer may cover (the sheet's button), or null.
var clear_of: Control
var _t := 0.0
var _bits: Array = []
var _built_for := -1.0


## Streamers for `premier` over `host`, or null when motion is off (Reduced
## motion, a headless run): then nothing is added at all.
static func play_over(host: Control, premier: String, keep_clear: Control = null) -> PremiershipStreamers:
	if host == null or premier == "" or not UiKit.motion_on():
		return null
	var s := PremiershipStreamers.new()
	s.name = "PremiershipStreamers"
	s.club = premier
	s.colours = [UiKit.club_ink(premier), UiKit.club_ink_second(premier)]
	s.clear_of = keep_clear
	s.mouse_filter = Control.MOUSE_FILTER_IGNORE
	host.add_child(s)
	s.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	Feel.moved.append("streamers")
	return s


func _process(delta: float) -> void:
	seek(_t + delta)


## Put the fall at `t` seconds (tests and captures); at DURATION it is over.
func seek(t: float) -> void:
	_t = t
	if _t >= DURATION:
		set_process(false)
		queue_free()
		return
	queue_redraw()


func elapsed() -> float:
	return _t


## The line the streamers have faded out by, in this control's own pixels.
func floor_y() -> float:
	if clear_of != null and is_instance_valid(clear_of) and clear_of.is_inside_tree():
		return clear_of.get_global_rect().position.y - get_global_rect().position.y - 16.0
	return size.y * FLOOR


func _build() -> void:
	_built_for = size.x
	_bits.clear()
	var rng := RandomNumberGenerator.new()
	rng.seed = SEED
	var n := clampi(int(size.x / 14.0), 24, 60)
	for i in n:
		# Spread across the width in even lanes, so both colours show everywhere.
		var lane := (float(i) + rng.randf_range(0.15, 0.85)) / float(n)
		_bits.append({
			"x": lane * size.x,
			"delay": rng.randf_range(0.0, STAGGER),
			"speed": rng.randf_range(300.0, 460.0),
			"len": rng.randf_range(70.0, 130.0),
			"sway": rng.randf_range(7.0, 16.0),
			"turn": rng.randf_range(1.6, 3.2),
			"phase": rng.randf_range(0.0, TAU),
			"width": rng.randf_range(4.0, 6.0),
			"colour": i % 2,
		})


## Each streamer as [points, colour] at this moment; what _draw paints.
func ribbons() -> Array:
	if colours.size() < 2 or size.x <= 0.0:
		return []
	if _built_for != size.x:
		_build()
	var out := []
	var gone := floor_y()
	for b in _bits:
		var since: float = _t - float(b["delay"])
		if since <= 0.0:
			continue
		var head: float = -10.0 + float(b["speed"]) * since
		var alpha := 1.0 - smoothstep(gone - FADE, gone, head)
		if alpha <= 0.01:
			continue
		var pts := PackedVector2Array()
		for k in 10:
			var y: float = head - float(b["len"]) * float(k) / 9.0
			var x: float = float(b["x"]) + float(b["sway"]) * sin(float(b["phase"]) + y * 0.035 + _t * float(b["turn"]))
			pts.append(Vector2(x, y))
		var c: Color = colours[int(b["colour"])]
		c.a = alpha
		out.append([pts, c, float(b["width"])])
	return out


func _draw() -> void:
	for r in ribbons():
		draw_polyline(r[0], r[1], r[2], true)
