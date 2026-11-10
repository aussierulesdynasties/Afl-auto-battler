extends Control
## LoadFlair - what a long wait looks at (row 121, director 2026-11-08: "give
## the load screens some flair, perhaps a logo, a bespoke loading anim"): the
## game's logo over a set shot from behind the kicker. A Sherrin leaves the boot
## end over end, sails away and goes through the big sticks, kick after kick. The
## padding on the posts is your club's. One kick in six sprays through for a behind.
##
## Presentation only. It lives on the ScreenTransition cover and is up only when
## the cover has a line on it, so a quick screen change stays a plain wipe.
##
## The ball is drawn straight on the rendering server, not in _draw, so tick()
## can move it while the main thread is in the middle of blocking work
## (ScreenTransition.keep_moving draws that frame by hand). A real 3D ball is
## projected: an ellipsoid of revolution always has an ellipse for an outline,
## and the panel seams and the lace are points on it, so it turns rather than
## squashes. Reduced motion: the ball sits on the ground, still, in front of
## the posts (a ball in the air and not moving would be a hovering ball).

const LOGO := preload("res://assets/ui/aussie_rules_dynasties_logo_placeholder.png")
## The lettering inside the file (the same crop the title screen uses).
const LOGO_REGION := Rect2(90, 228, 1374, 614)
const LOGO_MAX_W := 420.0

## One kick: time in the air, then a beat before the next one.
const FLIGHT_S := 1.5
const REST_S := 0.22
## Turns of the ball per kick. A drop punt tumbles backwards.
const TURNS := 2.25
## Where each kick starts (x at the boot) and where it crosses the goal line, in
## half-widths of the goal: inside 1 is a goal, between 1 and 3 is a behind.
const KICK_FROM := [-1.6, 1.2, -0.7, 2.0, -1.9, 0.6]
const KICK_TO := [0.25, -0.4, 1.95, 0.1, -0.2, 0.45]

## How far the ball carries past the goal line, and how quickly things shrink
## with distance (at the goal line they are 1 / (1 + PERSPECTIVE) of near size).
const Z_END := 1.3
const PERSPECTIVE := 2.57
## The ball's half length to half width (a real Sherrin is about 1.35 to 1).
const BALL_RATIO := 1.35
## The way the ball's tumble axis leans off side-on: enough to see it turn.
const AXIS_LEAN := deg_to_rad(45.0)
## Ball half length when near, as a share of the stage width.
const BALL_NEAR := 0.125

const LEATHER := Color("b3271e")
const SEAM := Color("4d0f0b")
const LACE := Color("f1eee6")
const POST := Color("efeadd")
const CHALK := Color(0.94, 0.92, 0.86, 0.62)
const TURF := Color(0.13, 0.30, 0.17)
const SHADOW := Color(0.0, 0.0, 0.0, 0.34)

const SEGMENTS := 22
const RINGS := [0.34, 0.6, 0.8, 0.93, 1.0]
const SEAM_SAMPLES := 14
## Below this half length in pixels the seams and lace are mush: leather only.
const DETAIL_MIN_PX := 6.5

## Tests: set the ball's clock by hand (ms since it opened), -1 to run free.
var hand_clock_ms := -1
## Tests: open as a browser does (the ball at rest).
var web_still := false
## Filled by tick(); tests read them.
var ball_at := Vector2.ZERO
var ball_turn := 0.0
var ticks := 0

var _logo: TextureRect
var _stage: Control
var _ball_item: RID
var _pad := POST
var _t0_ms := 0
var _still := false
## Fan geometry for the ball, built once.
var _indices := PackedInt32Array()


func _ready() -> void:
	name = "LoadFlair"
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visible = false
	_logo = TextureRect.new()
	_logo.name = "LoadLogo"
	var art := AtlasTexture.new()
	art.atlas = LOGO
	art.region = LOGO_REGION
	_logo.texture = art
	_logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# Its black ground adds nothing under an additive blend, as on the title.
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	_logo.material = mat
	add_child(_logo)
	_stage = Control.new()
	_stage.name = "LoadStage"
	_stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stage.draw.connect(_draw_ground)
	add_child(_stage)
	_ball_item = RenderingServer.canvas_item_create()
	RenderingServer.canvas_item_set_parent(_ball_item, _stage.get_canvas_item())
	_build_indices()


func _exit_tree() -> void:
	if _ball_item.is_valid():
		RenderingServer.free_rid(_ball_item)
		_ball_item = RID()


## Up, for `club` (its colour on the post padding; "" before a career has one).
func open(club: String, still: bool) -> void:
	_pad = UiKit.club_ink(club, UiKit.PANEL_ALT) if club != "" else POST
	# A browser cannot draw while blocking work runs, so what it shows for a
	# wait are stills (a skip draws one a week): the ball rests on the turf
	# there, as with Reduced motion, so no still catches it hanging in the air.
	_still = still or web_still or OS.has_feature("web")
	_t0_ms = Time.get_ticks_msec()
	visible = true
	fit()
	tick()


func close() -> void:
	visible = false


## Lay out for the window: logo, then the set shot, then `line_top` is where the
## cover's line goes. The whole stack sits a little above the centre.
func fit() -> float:
	var view := get_viewport_rect().size
	var logo_w := minf(LOGO_MAX_W, view.x - 64.0)
	var logo_h := roundf(logo_w * LOGO_REGION.size.y / LOGO_REGION.size.x)
	var stage_w := minf(view.x - 64.0, 300.0)
	var stage_h := roundf(minf(stage_w * 0.68, view.y * 0.3))
	stage_w = roundf(stage_h / 0.68)
	var total := logo_h + 20.0 + stage_h + 24.0 + 64.0
	var top := roundf(maxf(16.0, (view.y - total) * 0.46))
	_logo.position = Vector2(roundf((view.x - logo_w) * 0.5), top)
	_logo.size = Vector2(logo_w, logo_h)
	_stage.position = Vector2(roundf((view.x - stage_w) * 0.5), top + logo_h + 20.0)
	_stage.size = Vector2(stage_w, stage_h)
	_stage.queue_redraw()
	return _stage.position.y + stage_h + 24.0


# ---------------------------------------------------------------------------
# The shot: where things land on the stage
# ---------------------------------------------------------------------------
func _scale_at(z: float) -> float:
	return 1.0 / (1.0 + PERSPECTIVE * z)


## The ground under depth z (0 at the boot, 1 at the goal line), as a stage y.
func _ground_y(z: float) -> float:
	var h := _stage.size.y
	var horizon := 0.591 * h
	return horizon + (0.98 * h - horizon) * _scale_at(z)


## x on the stage for a world x in half-goal-widths, at depth z.
func _x_at(world_x: float, z: float) -> float:
	var w := _stage.size.x
	return w * 0.5 + world_x * 0.14 * w * (1.0 + PERSPECTIVE) * _scale_at(z)


## Where the ball is `t` (0 to 1) through kick number `kick`: {at, half_len,
## shadow_at, z}. Straight in the world, so straight on the screen but for the
## height; the height is one parabola that lands past the goal line.
func flight(t: float, kick: int) -> Dictionary:
	var h := _stage.size.y
	var z := Z_END * t
	var from: float = float(KICK_FROM[kick % KICK_FROM.size()]) * 0.24
	var to: float = float(KICK_TO[kick % KICK_TO.size()])
	var world_x := lerpf(from, to, z)
	var zz := z / 1.35
	var height := 1.25 * h * 4.0 * zz * (1.0 - zz)
	var s := _scale_at(z)
	var gx := _x_at(world_x, z)
	var gy := _ground_y(z)
	return {
		"at": Vector2(gx, gy - height * s),
		"half_len": BALL_NEAR * _stage.size.x * s,
		"shadow_at": Vector2(gx, gy),
		"height": height,
		"z": z,
	}


# ---------------------------------------------------------------------------
# Per frame
# ---------------------------------------------------------------------------
func _process(_delta: float) -> void:
	if visible and not _still:
		tick()
		_stage.queue_redraw()     # a frame is wanted (low processor mode)


## Put the ball where the clock says. Safe in the middle of blocking work: it
## touches only this one rendering-server item.
func tick() -> void:
	ticks += 1
	var rs := RenderingServer
	rs.canvas_item_clear(_ball_item)
	if _still:
		var rest := Vector2(_stage.size.x * 0.5, _stage.size.y * 0.915)
		var half := BALL_NEAR * _stage.size.x * 0.82
		ball_at = rest
		ball_turn = 0.32
		rs.canvas_item_set_modulate(_ball_item, Color.WHITE)
		_add_shadow(rest + Vector2(0.0, half / BALL_RATIO * 0.86), half * 0.92, 1.0)
		_add_ball(rest, half, 0.32)
		return
	var ms := hand_clock_ms if hand_clock_ms >= 0 else Time.get_ticks_msec() - _t0_ms
	var elapsed := float(ms) / 1000.0
	var period := FLIGHT_S + REST_S
	var kick := int(elapsed / period)
	var t := fposmod(elapsed, period) / FLIGHT_S
	if t >= 1.0:
		rs.canvas_item_set_modulate(_ball_item, Color(1, 1, 1, 0))
		return
	var f := flight(t, kick)
	var fade := minf(clampf(t / 0.03, 0.0, 1.0), clampf((1.0 - t) / 0.08, 0.0, 1.0))
	rs.canvas_item_set_modulate(_ball_item, Color(1, 1, 1, fade))
	var half: float = float(f["half_len"])
	var z: float = float(f["z"])
	ball_at = f["at"]
	ball_turn = t * TURNS
	if z <= 1.0:
		var lift := clampf(float(f["height"]) / _stage.size.y, 0.0, 1.0)
		_add_shadow(f["shadow_at"], half * 0.9, 1.0 - 0.6 * lift)
	_add_ball(ball_at, half, ball_turn * TAU)


func _add_shadow(at: Vector2, half: float, strength: float) -> void:
	var pts := PackedVector2Array()
	for i in range(14):
		var a := TAU * float(i) / 14.0
		pts.append(at + Vector2(cos(a) * half, sin(a) * half * 0.24))
	var c := SHADOW
	c.a *= strength
	RenderingServer.canvas_item_add_polygon(_ball_item, pts, PackedColorArray([c]))


func _build_indices() -> void:
	# A fan to the first ring, then quads ring to ring. Vertex 0 is the centre.
	var n: int = SEGMENTS
	for i in range(n):
		_indices.append_array([0, 1 + i, 1 + (i + 1) % n])
	for r in range(RINGS.size() - 1):
		var a: int = 1 + r * n
		var b: int = a + n
		for i in range(n):
			var j: int = (i + 1) % n
			_indices.append_array([a + i, b + i, b + j, a + i, b + j, a + j])


## The ball at `at`, half length `half`, tumbled by `turn` radians. x right,
## y up, z into the screen; the top of the ball comes back toward the kicker.
func _add_ball(at: Vector2, half: float, turn: float) -> void:
	var a := half
	var b := half / BALL_RATIO
	var lean_x := sin(AXIS_LEAN)
	var lean_z := cos(AXIS_LEAN)
	var c := cos(turn)
	var s := sin(turn)
	var u := Vector3(lean_x * s, c, -lean_z * s)         # the long axis
	var w := Vector3(lean_z, 0.0, lean_x)                # the tumble axis
	var v := w.cross(u)
	# The outline: an ellipse along u's shadow on the screen.
	var flat := Vector2(u.x, -u.y)                        # screen y is down
	var f := flat.length()
	var along := flat / f if f > 0.001 else Vector2.DOWN
	var across := Vector2(-along.y, along.x)
	var long_r := sqrt(a * a * f * f + b * b * (1.0 - f * f))
	_add_leather(at, along, across, long_r, b)
	var pts := PackedVector2Array()
	for i in range(SEGMENTS + 1):
		var e := TAU * float(i) / float(SEGMENTS)
		pts.append(at + along * cos(e) * long_r + across * sin(e) * b)
	var width := maxf(1.0, half * 0.05)
	RenderingServer.canvas_item_add_polyline(_ball_item, pts, PackedColorArray([SEAM]), width, true)
	if half < DETAIL_MIN_PX:
		return
	for k in range(4):
		_add_seam(at, a, b, u, v, w, TAU * float(k) / 4.0 + 0.5, width)
	_add_lace(at, a, b, u, v, w, 0.5, half)


## The leather, lit from the top left from a light that stays put as it turns.
func _add_leather(at: Vector2, along: Vector2, across: Vector2, long_r: float, short_r: float) -> void:
	var n: int = SEGMENTS
	var light := Vector3(-0.5, -0.62, -0.6).normalized()
	var pts := PackedVector2Array()
	var cols := PackedColorArray()
	pts.resize(1 + RINGS.size() * n)
	cols.resize(pts.size())
	pts[0] = at
	cols[0] = _lit(Vector3(0.0, 0.0, -1.0), light)
	var k := 1
	for r: float in RINGS:
		for i in range(n):
			var e := TAU * float(i) / float(n)
			var ce := cos(e)
			var se := sin(e)
			pts[k] = at + along * ce * long_r * r + across * se * short_r * r
			var flat := (along * ce + across * se) * r
			cols[k] = _lit(Vector3(flat.x, flat.y, -sqrt(maxf(0.0, 1.0 - r * r))), light)
			k += 1
	RenderingServer.canvas_item_add_triangle_array(_ball_item, _indices, pts, cols)


func _lit(normal: Vector3, light: Vector3) -> Color:
	var d := maxf(0.0, normal.dot(light))
	var col := LEATHER * (0.34 + 0.86 * d)
	col = col.lerp(Color.WHITE, pow(d, 14.0) * 0.28)
	col.a = 1.0
	return col


## A point on the ball's skin: `s` along it (0 to PI, tip to tip), `p` round it.
## Returns the screen offset in xy and in z how much it faces away (+) or at you.
func _skin(a: float, b: float, u: Vector3, v: Vector3, w: Vector3, s: float, p: float) -> Vector3:
	var round_dir := v * cos(p) + w * sin(p)
	var point := u * (a * cos(s)) + round_dir * (b * sin(s))
	var normal := u * (cos(s) / a) + round_dir * (sin(s) / b)
	return Vector3(point.x, -point.y, normal.z)


## One panel seam, tip to tip, drawn only where it faces the viewer.
func _add_seam(at: Vector2, a: float, b: float, u: Vector3, v: Vector3, w: Vector3, p: float, width: float) -> void:
	var run := PackedVector2Array()
	for i in range(SEAM_SAMPLES + 1):
		var s := PI * float(i) / float(SEAM_SAMPLES)
		var q := _skin(a, b, u, v, w, s, p)
		if q.z < 0.0:
			run.append(at + Vector2(q.x, q.y))
		else:
			_flush_run(run, SEAM, width)
			run = PackedVector2Array()
	_flush_run(run, SEAM, width)


func _flush_run(run: PackedVector2Array, col: Color, width: float) -> void:
	if run.size() >= 2:
		RenderingServer.canvas_item_add_polyline(_ball_item, run, PackedColorArray([col]), width, true)


## The lace: a short white run across the middle of one seam.
func _add_lace(at: Vector2, a: float, b: float, u: Vector3, v: Vector3, w: Vector3, p: float, half: float) -> void:
	var width := maxf(1.0, half * 0.06)
	var bars := 6
	for i in range(bars):
		var s := PI * (0.34 + 0.32 * float(i) / float(bars - 1))
		var one := _skin(a, b, u, v, w, s, p - 0.2)
		var two := _skin(a, b, u, v, w, s, p + 0.2)
		if one.z < 0.0 and two.z < 0.0:
			var line := PackedVector2Array([at + Vector2(one.x, one.y), at + Vector2(two.x, two.y)])
			RenderingServer.canvas_item_add_polyline(_ball_item, line, PackedColorArray([LACE]), width, true)


# ---------------------------------------------------------------------------
# The ground: drawn once per layout
# ---------------------------------------------------------------------------
## Four posts and the goal square from out on the kicking line, to AFL
## proportions: three equal gaps, the behind posts half the goal posts' height.
func _draw_ground() -> void:
	var w := _stage.size.x
	var h := _stage.size.y
	if w <= 0.0 or h <= 0.0:
		return
	var goal_y := _ground_y(1.0)
	var near_y := _ground_y(0.0)
	# The turf fades into the cover, so the shot has no edge.
	var turf_clear := TURF
	turf_clear.a = 0.0
	var turf := TURF
	turf.a = 0.8
	var horizon := _ground_y(1.35)
	var far_l := _x_at(-16.0, 1.35)
	var far_r := _x_at(16.0, 1.35)
	var mid_l := _x_at(-9.0, 0.5)
	var mid_r := _x_at(9.0, 0.5)
	var mid_y := _ground_y(0.5)
	_stage.draw_polygon(PackedVector2Array([Vector2(far_l, horizon), Vector2(far_r, horizon),
			Vector2(mid_r, mid_y), Vector2(mid_l, mid_y)]),
			PackedColorArray([turf_clear, turf_clear, turf, turf]))
	_stage.draw_polygon(PackedVector2Array([Vector2(mid_l, mid_y), Vector2(mid_r, mid_y),
			Vector2(w * 0.5 + w * 0.3, near_y), Vector2(w * 0.5 - w * 0.3, near_y)]),
			PackedColorArray([turf, turf, turf_clear, turf_clear]))
	# The goal line and behind line, then the goal square coming toward you.
	var line_w := maxf(1.0, w * 0.006)
	_stage.draw_line(Vector2(_x_at(-3.0, 1.0), goal_y), Vector2(_x_at(3.0, 1.0), goal_y), CHALK, line_w, true)
	var sq_z := 0.8
	var sq_y := _ground_y(sq_z)
	_stage.draw_line(Vector2(_x_at(-1.0, 1.0), goal_y), Vector2(_x_at(-1.0, sq_z), sq_y), CHALK, line_w, true)
	_stage.draw_line(Vector2(_x_at(1.0, 1.0), goal_y), Vector2(_x_at(1.0, sq_z), sq_y), CHALK, line_w, true)
	_stage.draw_line(Vector2(_x_at(-1.0, sq_z), sq_y), Vector2(_x_at(1.0, sq_z), sq_y), CHALK, line_w, true)
	# Behind posts first, then the goal posts in front of nothing: same plane.
	for side in [-3.0, 3.0]:
		_post(_x_at(side, 1.0), goal_y, h * 0.31, maxf(2.0, w * 0.011))
	for side in [-1.0, 1.0]:
		_post(_x_at(side, 1.0), goal_y, h * 0.6, maxf(2.5, w * 0.015))


func _post(x: float, foot: float, tall: float, width: float) -> void:
	_stage.draw_line(Vector2(x, foot), Vector2(x, foot - tall), POST, width, true)
	# Round the top, and pad the bottom in the club's colour.
	_stage.draw_circle(Vector2(x, foot - tall), width * 0.5, POST, true)
	var pad := minf(tall * 0.32, _stage.size.y * 0.13)
	_stage.draw_line(Vector2(x, foot), Vector2(x, foot - pad), _pad, width * 1.7, true)
