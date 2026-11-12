class_name VignetteGround
extends RefCounted
## The football ground the vignettes play on, built to the AFL's dimensions and seen
## through each scene's camera (Cam), so every painted line, post and stand sits where it
## would on a real ground and holds its shape as the camera zooms and pans:
##   - the oval at its own ground's size (data/grounds.json: the MCG 160 m by 141 m,
##     Bellerive 175 m by 122 m), its boundary line painted round it;
##   - the goal posts on the boundary at each end: goal posts 6.4 m apart, behind posts
##     6.4 m outside them, the goal line between the behind posts, the goal square
##     6.4 m by 9 m in front, the 50 m arc from the middle of the goal line;
##   - the centre square, 50 m by 50 m, and the centre circle, 10 m across with a 3 m
##     circle inside, divided by a line across the ground;
##   - painted lines 10 cm wide (never thinner than a pixel), mown stripes across the
##     oval, the apron outside the boundary, the fence with its boards and the stands
##     rising behind it, full of both clubs' people.
## Oval coordinates: metres from the centre of the ground, x across it (wing to wing),
## y along it towards the end a scene attacks (its goal line at +GOAL_Y).
## Everything is drawn as triangles in a couple of calls, for phones.

## Half the oval's width and half its length: the ground's own (venue), else 136 m by
## 160 m. Literals, not expressions (see GOAL_Y).
static var A := 68.0
static var L := 80.0
const GOAL_GAP := 6.4             # between the goal posts, and from each to its behind post
## The goal posts tower; the behind posts are clearly shorter (director), so even when a
## close shot cuts off the goal posts' tops, the behinds' stand inside it.
const GOAL_H := 12.0
const BEHIND_H := 6.5
const POST_W := 0.35
const PAD_H := 2.8                # the padding round the foot of each post
const PAD_W := 0.75
const SQUARE_DEPTH := 9.0         # the goal square
const ARC := 50.0
const CENTRE_SQUARE := 50.0
const CIRCLE_R := 5.0
const INNER_R := 1.5
const LINE_W := 0.1
## The fence stands this far outside the boundary; the stand rises behind it.
const FENCE := 6.0
const FENCE_H := 1.2
const STAND_DEPTH := 34.0
const STAND_RISE := 24.0
## One copy of the crowd texture covers this much of the stand, along it.
const CROWD_TILE := 30.0
const NEAR := 0.6                 # metres in front of the camera: nearer is clipped
const SKY := Color(0.025, 0.03, 0.035)   # at night; by day and at twilight: VignetteWeather.sky
const GRASS := [Color(0.16, 0.39, 0.17), Color(0.18, 0.43, 0.19)]
const APRON := Color(0.13, 0.32, 0.14)
const PAINT := Color(0.97, 0.97, 0.95, 0.92)
const WORN := [Color(0.26, 0.36, 0.17, 0.55), Color(0.38, 0.36, 0.22, 0.45)]

## The ground being shown, by its fixture name ("MCG"). Each AFL ground has its own size
## and look in data/grounds.json (TODO row 33: looks only, the sim never reads it); any
## other, or "", draws the default ground. Setting it sets the oval's size and look.
static var venue := "":
	set(v):
		venue = v
		_apply(v)

## The ground's look as drawn now (data/grounds.json, its "default" filled in).
static var spec := {}
static var _grounds := {}


## A ground's look: its own entry over the default (an unknown ground is the default).
static func spec_of(ground: String) -> Dictionary:
	if _grounds.is_empty():
		var f := FileAccess.open("res://data/grounds.json", FileAccess.READ)
		if f != null:
			var parsed = JSON.parse_string(f.get_as_text())
			if parsed is Dictionary:
				_grounds = parsed
	var own: Dictionary = _grounds.get("grounds", {})
	var out: Dictionary = (_grounds.get("default", {}) as Dictionary).duplicate(true)
	out.merge(own.get(ground, {}), true)
	out["known"] = own.has(ground)
	return out


## Every ground with its own look.
static func ground_names() -> Array:
	spec_of("")
	return (_grounds.get("grounds", {}) as Dictionary).keys()


static func _apply(ground: String) -> void:
	spec = spec_of(ground)
	A = float(spec.get("width", 136.0)) * 0.5
	L = float(spec.get("length", 160.0)) * 0.5
	GOAL_Y = L * sqrt(1.0 - pow(1.5 * GOAL_GAP / A, 2.0))
	_geometry.clear()


## The ground's empty seats (the crowd texture's base colour) as the ground last drew
## them: under lights the ground's own colour, paler in daylight. Whoever paints the
## crowd ahead of a scene asks here, so it paints the picture the scene will use.
static func seat_colour() -> Color:
	return _seats_in(VignetteKickoff.shown)


static func _seats_in(slot: String) -> Color:
	if spec.is_empty():
		_apply(venue)
	return _lit(Color.html(str(spec.get("seat", "#121216"))), DAY_SEAT, VignetteKickoff.daylight(slot) * 0.85)


## The ground a match is played at: a final's own venue, else the home club's
## (clubs.csv; Collingwood, Hawthorn, Melbourne and Richmond are at the MCG).
static func ground_of(res: Dictionary) -> String:
	var ground := str(res.get("venue", ""))
	if ground == "":
		ground = str(GameDB.club(str(res.get("home", ""))).get("ground", ""))
	return ground


## Draw this match's ground from now on (the static outlives the scene).
static func use_match(res: Dictionary) -> void:
	venue = ground_of(res)
	VignetteKickoff.use_match(res, venue)


## Where the goal line runs: the boundary at the behind posts, L * sqrt(1 - (1.5 * GOAL_GAP / A)^2),
## worked out by _apply for the ground. The default is written out, because a static var set
## from an expression stays 0 when a tool runs with --script (the capture tools), which drew
## the posts on the centre of the ground in every broadcast capture.
static var GOAL_Y := 79.19875571354891


## A camera on the ground: standing at pos (scene metres), height up, looking along fwd
## with its lens level (so posts stay upright); f the focal length in pixels, cx the
## screen x it looks along, hor the horizon's screen y. to_scene maps oval coordinates
## into the scene's own (identity when the scene works in oval coordinates).
class Cam:
	var pos := Vector2.ZERO
	var height := 5.0
	var fwd := Vector2(0, 1)
	var f := 600.0
	var cx := 0.0
	var hor := 0.0
	var to_scene := Transform2D.IDENTITY

	## Across and away from the camera, metres, for a scene point.
	func local(p: Vector2) -> Vector2:
		var d := p - pos
		return Vector2(d.x * fwd.y - d.y * fwd.x, d.dot(fwd))

	## Screen point and pixels per metre there, for a local point h metres up.
	func screen(l: Vector2, h := 0.0) -> Vector3:
		var z := maxf(l.y, 0.001)
		return Vector3(cx + f * l.x / z, hor + f * (height - h) / z, f / z)

	## A scene point h metres up, to the screen (z: pixels per metre; <= 0 behind).
	func project(p: Vector2, h := 0.0) -> Vector3:
		var l := local(p)
		if l.y < NEAR:
			return Vector3(0, 0, -1)
		return screen(l, h)

	func oval(p: Vector2, h := 0.0) -> Vector3:
		return project(to_scene * p, h)


## A camera at pos, height up, looking at target (scene metres).
static func looking(pos: Vector2, height: float, target: Vector2, f: float, cx: float, hor: float) -> Cam:
	var c := Cam.new()
	c.pos = pos
	c.height = height
	c.fwd = (target - pos).normalized()
	c.f = f
	c.cx = cx
	c.hor = hor
	return c


## The whole ground: sky, stands, fence, apron, the oval and its stripes and markings.
## stage: the screen area to cover (the vignette's drawn stage); colours: both clubs'
## colour lists (the crowd, the boards). Goal posts are separate (draw_goals), so a
## scene can put them behind its players.
## board: the match's score for the big screen ({codes: [home, away], goals, behinds,
## q}); empty, the screen shows the clubs' colours only.
## weather: the day's (VignetteWeather; MatchSim.weather) and t the scene's time, for
## what moves with it (flags in the wind). On a windy day board "wind" says which end the
## breeze blows to (+1 the +y end, -1 the other): the flags stream that way and the big
## screen's arrow points there. The time of day comes from VignetteKickoff.
static func draw_ground(ci: CanvasItem, cam: Cam, stage: Rect2, colours: Array, seed := 7, board := {},
		weather := "", t := 0.0) -> void:
	if spec.is_empty():
		_apply(venue)
	# The time of day (VignetteKickoff): night draws exactly as every ground did before
	# there were day games.
	var slot := slot_now(weather)
	VignetteKickoff.shown = slot
	VignetteGrade.sync(ci, weather, slot, far_turf(cam))
	# Under a closed roof the sky is the roof's underside.
	var closed: bool = spec.get("roof") == "closed"
	var sky := VignetteWeather.sky(weather, slot)
	if closed or sky.is_empty():
		ci.draw_rect(stage, Color.html(str(spec["roof_colour"])).darkened(0.35) if closed else SKY, true)
	else:
		_draw_sky(ci, cam, stage, sky, VignetteKickoff.daylight(slot))
	_draw_stands(ci, cam, colours, seed, board, weather, t, slot)
	var tri := Tris.new()
	_fence_and_apron(tri, cam, colours, slot)
	# The oval and its mown stripes across the ground: bands STRIPE m wide (the old turf,
	# for the capture tools' night proof: every 12 m).
	var grass := VignetteWeather.grass(weather, GRASS, slot)
	tri.poly(_clip(cam, _ellipse_ring(A, L, 0.0, 0.0, 180)), grass[0])
	var step := STRIPE if fine_turf else 12.0
	var y := -L
	var n := 0
	while y < L:
		if n % 2 == 1:
			tri.poly(_clip(cam, _band(y, minf(y + step, L))), grass[1])
		y += step
		n += 1
	if fine_turf:
		_turf_detail(tri, cam)
	if weather == VignetteWeather.HOT:
		_bleached(tri, cam, VignetteKickoff.daylight(slot))
	# Worn turf where the game is heaviest: the goal squares and the centre circle.
	for end in [-1.0, 1.0]:
		var gy: float = GOAL_Y * end
		tri.poly(_clip(cam, _ellipse_ring(4.2, 5.0, 0.0, gy - 3.5 * end, 24)), WORN[0])
		tri.poly(_clip(cam, _ellipse_ring(2.4, 2.8, 0.4, gy - 2.6 * end, 18)), WORN[1])
	tri.poly(_clip(cam, _ellipse_ring(4.0, 3.2, 0.0, 0.0, 24)), WORN[0])
	tri.poly(_clip(cam, _ellipse_ring(1.8, 1.4, 0.3, -0.2, 16)), WORN[1])
	_markings(tri, cam)
	tri.flush(ci)
	# Wet turf holds the towers' glare only when the lights are what lights it: at night.
	if weather == VignetteWeather.WET and slot == VignetteKickoff.NIGHT:
		VignetteWeather.draw_sheen(ci, cam, _tower_spots(), A, L)


## The time of day the ground is drawn in, in this weather: the match's (VignetteKickoff),
## except that a ground with its roof closed is lit by its own lights whatever the hour,
## so it always draws as it does at night.
static func slot_now(weather: String) -> String:
	if spec.is_empty():
		_apply(venue)
	if spec.get("roof") == "closed":
		return VignetteKickoff.NIGHT
	return VignetteKickoff.now(weather)


## Capture tools only: false draws the turf as it was before the narrower stripes and
## the mower's lines, to prove the night look is otherwise unchanged.
static var fine_turf := true
## The mown stripes' width across the ground, metres, and the mower's own lines inside
## them (one pass of the mower), drawn only near the camera where they can be seen.
const STRIPE := 6.0
const MOWER := 0.75
const MOWER_REACH := 42.0


## Where the far edge of the turf is on the picture (screen y): the highest point of the
## boundary the camera sees. The heat shimmer sits there, over the far turf and the fence.
static func far_turf(cam: Cam) -> float:
	var y := INF
	for i in range(36):
		var a := TAU * float(i) / 36.0
		var s := cam.oval(Vector2(cos(a) * A, sin(a) * L), 0.0)
		if s.z > 0.0:
			y = minf(y, s.y)
	return cam.hor if y == INF else y


## A day or twilight sky: three colours from the top of the stage down to the horizon,
## the horizon's colour on below it (the stands and the ground cover that).
static func _draw_sky(ci: CanvasItem, cam: Cam, stage: Rect2, sky: Array, day := 1.0) -> void:
	var x0 := stage.position.x
	var x1 := stage.end.x
	var top := stage.position.y
	var hor := clampf(cam.hor, top + 2.0, stage.end.y)
	var mid := lerpf(top, hor, 0.55)
	var c0: Color = sky[0]
	var c1: Color = sky[1]
	var c2: Color = sky[2]
	ci.draw_polygon(PackedVector2Array([Vector2(x0, top), Vector2(x1, top), Vector2(x1, mid), Vector2(x0, mid)]),
			PackedColorArray([c0, c0, c1, c1]))
	ci.draw_polygon(PackedVector2Array([Vector2(x0, mid), Vector2(x1, mid), Vector2(x1, hor), Vector2(x0, hor)]),
			PackedColorArray([c1, c1, c2, c2]))
	if hor < stage.end.y:
		# Below the horizon nothing is sky: what shows between the stand and the fence is
		# the shaded walkway under the front rows.
		ci.draw_rect(Rect2(x0, hor, x1 - x0, stage.end.y - hor), Color(0.045, 0.045, 0.055).lerp(DAY_CONCRETE, day * 0.5), true)


## What makes close turf read as mown grass, not flat blocks of colour:
##   - the ground is cut both ways, so the stripes along it lie faintly over the ones
##     across it (the checker every AFL ground is mown in);
##   - inside each stripe, the mower's own lines, a pass at a time, each a touch lighter
##     or darker than the next. Only near the camera: farther off they are finer than a
##     pixel and would only crawl.
static func _turf_detail(tri: Tris, cam: Cam) -> void:
	var x := -A
	var n := 0
	while x < A:
		if n % 2 == 1:
			tri.poly(_clip(cam, _band_along(x, minf(x + STRIPE, A))), Color(0.0, 0.04, 0.0, 0.085))
		x += STRIPE
		n += 1
	var eye: Vector2 = cam.to_scene.affine_inverse() * cam.pos
	var first := floorf((eye.y - MOWER_REACH) / MOWER)
	var last := ceilf((eye.y + MOWER_REACH) / MOWER)
	for i in range(int(first), int(last)):
		var y0 := float(i) * MOWER
		if y0 < -L or y0 + MOWER > L:
			continue
		var h := hash(i * 9176 + 71)
		var near := 1.0 - absf(y0 - eye.y) / MOWER_REACH
		var strength := (0.025 + 0.05 * float(h % 97) / 97.0) * clampf(near * 1.6, 0.0, 1.0)
		var colour := Color(1.0, 1.0, 0.82, strength) if i % 2 == 0 else Color(0.0, 0.05, 0.0, strength * 1.3)
		tri.poly(_clip(cam, _band(y0, y0 + MOWER * 0.5)), colour)


## A hot day's turf: dry, bleached patches scattered over the oval where the grass has
## burnt off, each a pale straw patch with a paler middle. day: how much daylight (they
## show by day; under lights the turf only yellows, as before).
static func _bleached(tri: Tris, cam: Cam, day: float) -> void:
	if day <= 0.0:
		return
	for i in range(70):
		var h := hash(i * 6121 + 5)
		var ang := TAU * float(h % 1009) / 1009.0
		var out := sqrt(float((h / 1009) % 997) / 997.0) * 0.9
		var at := Vector2(cos(ang) * A * out, sin(ang) * L * out)
		var rx := 1.2 + 3.0 * float((h / 7) % 89) / 89.0
		var ry := rx * (0.55 + 0.4 * float((h / 11) % 83) / 83.0)
		tri.poly(_clip(cam, _ellipse_ring(rx, ry, at.x, at.y, 16)), Color(0.8, 0.74, 0.46, 0.2 * day))
		tri.poly(_clip(cam, _ellipse_ring(rx * 0.55, ry * 0.5, at.x + rx * 0.12, at.y, 12)), Color(0.88, 0.83, 0.58, 0.16 * day))


## The goal posts at one end (end: +1 the far end of oval y, -1 the other), padded
## in pad_colour, nearer posts drawn over farther ones.
static func draw_goals(ci: CanvasItem, cam: Cam, end := 1, pad_colour := Color(0.75, 0.75, 0.78)) -> void:
	_photographers(ci, cam, end)
	var posts := []
	for i in [-1.5, -0.5, 0.5, 1.5]:
		var at := Vector2(i * GOAL_GAP, GOAL_Y * end)
		posts.append([cam.local(cam.to_scene * at).y, at, GOAL_H if absf(i) < 1.0 else BEHIND_H])
	posts.sort_custom(func(a, b): return a[0] > b[0])
	for p in posts:
		var base := cam.oval(p[1])
		if base.z <= 0.0:
			continue
		var top := cam.oval(p[1], p[2])
		var w := maxf(1.5, POST_W * base.z)
		ci.draw_rect(Rect2(base.x - w * 0.5, top.y, w, base.y - top.y), Color(0.96, 0.96, 0.94), true)
		ci.draw_rect(Rect2(base.x - w * 0.5, top.y, w * 0.35, base.y - top.y), Color(1, 1, 1, 0.5), true)
		var pad := cam.oval(p[1], PAD_H)
		var pw := maxf(2.5, PAD_W * base.z)
		ci.draw_rect(Rect2(base.x - pw * 0.5, pad.y, pw, base.y - pad.y), pad_colour, true)
		ci.draw_rect(Rect2(base.x - pw * 0.5, pad.y, pw * 0.3, base.y - pad.y), Color(1, 1, 1, 0.18), true)


## The photographers on the apron behind the goals, either side of the posts: crouched,
## dark against the boards, long lenses pointing up the ground, a glint on the glass.
static func _photographers(ci: CanvasItem, cam: Cam, end: int) -> void:
	for x in [-22.0, -17.5, -14.0, 13.0, 16.5, 21.0, 25.0]:
		var p := Vector2(x, (GOAL_Y + 3.0 + absf(x) * 0.06) * end)
		var s := cam.oval(p)
		if s.z <= 0.0 or s.z < 1.5:
			continue
		var u := s.z
		var at := Vector2(s.x, s.y)
		var body := Color(0.08, 0.08, 0.1)
		ci.draw_rect(Rect2(at + Vector2(-0.3, -0.95) * u, Vector2(0.6, 0.95) * u), body, true)      # crouched
		ci.draw_circle(at + Vector2(0.0, -1.12) * u, 0.17 * u, Color(0.25, 0.2, 0.17))            # head
		ci.draw_rect(Rect2(at + Vector2(-0.45, -1.12) * u, Vector2(0.45, 0.16) * u), Color(0.12, 0.12, 0.13), true)   # lens
		ci.draw_circle(at + Vector2(-0.45, -1.04) * u, maxf(0.6, 0.05 * u), Color(0.75, 0.82, 0.95, 0.8))


## The middle of the goal mouth at one end, h metres up (where a goal goes through).
static func goal_mouth(end := 1, h := 0.0) -> Vector3:
	return Vector3(0.0, GOAL_Y * end, h)


# ---------------------------------------------------------------------------
# Pieces
# ---------------------------------------------------------------------------
static func _markings(tri: Tris, cam: Cam) -> void:
	_line(tri, cam, _ellipse_ring(A, L, 0.0, 0.0, 360), true)                      # the boundary
	for end: float in [-1.0, 1.0]:
		var gy: float = GOAL_Y * end
		_line(tri, cam, [Vector2(-1.5 * GOAL_GAP, gy), Vector2(1.5 * GOAL_GAP, gy)], false)     # goal line
		var sq: float = gy - SQUARE_DEPTH * end
		_line(tri, cam, [Vector2(-0.5 * GOAL_GAP, gy), Vector2(-0.5 * GOAL_GAP, sq),
				Vector2(0.5 * GOAL_GAP, sq), Vector2(0.5 * GOAL_GAP, gy)], false)              # goal square
		# The 50 m arc, from the middle of the goal line, inside the boundary.
		_line(tri, cam, _arc(gy, end), false)
	var h := CENTRE_SQUARE * 0.5
	_line(tri, cam, [Vector2(-h, -h), Vector2(h, -h), Vector2(h, h), Vector2(-h, h)], true)
	_line(tri, cam, _ellipse_ring(CIRCLE_R, CIRCLE_R, 0.0, 0.0, 48), true)
	_line(tri, cam, _ellipse_ring(INNER_R, INNER_R, 0.0, 0.0, 24), true)
	_line(tri, cam, [Vector2(-CIRCLE_R, 0.0), Vector2(CIRCLE_R, 0.0)], false)


## A painted line through oval points, 10 cm wide on the ground: each piece as wide on
## screen as that width really looks from the camera, and never thinner than a pixel
## (fainter instead).
static func _arc(gy: float, end: float) -> Array:
	var key := ["arc", end, A, L]
	if not _geometry.has(key):
		var arc := []
		for i in range(181):
			var a := PI * float(i) / 180.0
			var p := Vector2(cos(a) * ARC, gy - sin(a) * ARC * end)
			if pow(p.x / A, 2.0) + pow(p.y / L, 2.0) < 1.0:
				arc.append(p)
		_geometry[key] = arc
	return _geometry[key]


static func _line(tri: Tris, cam: Cam, pts: Array, closed: bool) -> void:
	var n := pts.size()
	var segs := n if closed else n - 1
	for i in range(segs):
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[(i + 1) % n]
		# Long straights in short pieces, so perspective bends nothing.
		var pieces := maxi(1, int(a.distance_to(b) / 2.0))
		for k in range(pieces):
			_segment(tri, cam, a.lerp(b, float(k) / pieces), a.lerp(b, float(k + 1) / pieces))


static func _segment(tri: Tris, cam: Cam, a: Vector2, b: Vector2) -> void:
	var la := cam.local(cam.to_scene * a)
	var lb := cam.local(cam.to_scene * b)
	if la.y < NEAR and lb.y < NEAR:
		return
	# Clip at the near plane.
	if la.y < NEAR:
		var t := (NEAR - la.y) / (lb.y - la.y)
		a = a.lerp(b, t)
		la = la.lerp(lb, t)
	elif lb.y < NEAR:
		var t := (NEAR - lb.y) / (la.y - lb.y)
		b = b.lerp(a, t)
		lb = lb.lerp(la, t)
	var sa := cam.screen(la)
	var sb := cam.screen(lb)
	var d := Vector2(sb.x - sa.x, sb.y - sa.y)
	if d.length() < 0.01:
		return
	var ns := Vector2(-d.y, d.x).normalized()
	# The line's true width on screen: its two edges, projected.
	var dir := (b - a).normalized()
	var nw := cam.to_scene.basis_xform(Vector2(-dir.y, dir.x)) * (LINE_W * 0.5)
	var mid := cam.to_scene * a.lerp(b, 0.5)
	var e1 := cam.project(mid + nw)
	var e2 := cam.project(mid - nw)
	var width := absf(Vector2(e1.x - e2.x, e1.y - e2.y).dot(ns)) if e1.z > 0.0 and e2.z > 0.0 else 1.0
	var col := PAINT
	col.a *= clampf(width, 0.35, 1.0)
	var hw := maxf(width, 1.0) * 0.5
	var p1 := Vector2(sa.x, sa.y)
	var p2 := Vector2(sb.x, sb.y)
	tri.poly([p1 + ns * hw, p2 + ns * hw, p2 - ns * hw, p1 - ns * hw], col)


## The apron between the boundary and the fence, and the fence's boards in the clubs'
## colours, panel by panel.
static func _fence_and_apron(tri: Tris, cam: Cam, colours: Array, slot := VignetteKickoff.NIGHT) -> void:
	var apron := VignetteWeather.daylit(APRON, slot)
	var n := 180
	for i in range(n):
		var a0 := TAU * float(i) / n
		var a1 := TAU * float(i + 1) / n
		var in0 := Vector2(cos(a0) * A, sin(a0) * L)
		var in1 := Vector2(cos(a1) * A, sin(a1) * L)
		var out0 := Vector2(cos(a0) * (A + FENCE), sin(a0) * (L + FENCE))
		var out1 := Vector2(cos(a1) * (A + FENCE), sin(a1) * (L + FENCE))
		# The apron runs on under the front of the stand, so no gap shows between them.
		var back0 := Vector2(cos(a0) * (A + FENCE + 3.0), sin(a0) * (L + FENCE + 3.0))
		var back1 := Vector2(cos(a1) * (A + FENCE + 3.0), sin(a1) * (L + FENCE + 3.0))
		tri.poly(_clip(cam, [in0, in1, back1, back0]), apron)
		# The boards: an upright quad on the fence line.
		var c: Array = colours[(i / 3) % 2] if colours.size() > 1 else []
		var board: Color = (c[0] as Color).darkened(0.25) if not c.is_empty() else Color(0.2, 0.2, 0.22)
		var la := cam.local(cam.to_scene * out0)
		var lb := cam.local(cam.to_scene * out1)
		if la.y < NEAR or lb.y < NEAR:
			continue
		var b0 := cam.screen(la)
		var b1 := cam.screen(lb)
		var t0 := cam.screen(la, FENCE_H)
		var t1 := cam.screen(lb, FENCE_H)
		tri.poly([Vector2(b0.x, b0.y), Vector2(b1.x, b1.y), Vector2(t1.x, t1.y), Vector2(t0.x, t0.y)], board)
		tri.poly([Vector2(t0.x, t0.y), Vector2(t1.x, t1.y), Vector2(t1.x, t1.y + 1.0), Vector2(t0.x, t0.y + 1.0)],
				Color(1, 1, 1, 0.12))


## The stadium round the oval: two tiers of seats full of both clubs' people, a fascia
## between them in the clubs' colours, the roof's edge with its row of lights, the big
## screen above the far end, the light towers behind, and the haze the lights make.
static func _draw_stands(ci: CanvasItem, cam: Cam, colours: Array, seed: int, board: Dictionary,
		weather := "", t := 0.0, slot := VignetteKickoff.NIGHT) -> void:
	# By day the stands are lit by the sky, not the lights: paler seats, concrete and
	# roofs, and the lights off. day 0 (night) leaves every colour exactly as it was.
	var day := VignetteKickoff.daylight(slot)
	var lamps := VignetteKickoff.lights(slot)
	# The ground's own seats (the MCG's are a pale blue-grey: Commons, "MCG Shane Warne Stand.png").
	var tex := VignetteCrowd.seats(colours, seed, _seats_in(slot))
	# A grass hill: the crowd sitting on the bank (Bellerive, Manuka).
	var hill: Texture2D = VignetteCrowd.seats(colours, seed + 1, VignetteWeather.daylit(HILL, slot)) if spec.get("hill", false) else null
	if ci.texture_filter != CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS:
		ci.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	_towers(ci, cam, day, lamps)
	var ring := _ring_columns(A + FENCE + 2.0, L + FENCE + 2.0, STAND_TILE / 16.0)
	# Tiers, front to back: [inner offset, outer offset, inner height, outer height] beyond
	# the fence line: the ground's own. The MCG rises in three, a band of boxes under each
	# of the upper two.
	var tiers: Array = spec["tiers"]
	var roof_c := _lit(Color.html(str(spec.get("roof_colour", "#0f0f12"))), DAY_ROOF, day * 0.6)
	var under := _lit(Color(0.045, 0.045, 0.055), DAY_CONCRETE, day * 0.75)
	var lower: Array = tiers[0]
	var upper: Array = tiers[tiers.size() - 1]
	var shade := Tris.new()
	var lit := Tris.new()
	var c0: Color = (colours[0] as Array)[0] if colours.size() > 0 and not (colours[0] as Array).is_empty() else Color(0.3, 0.3, 0.32)
	var c1: Color = (colours[1] as Array)[0] if colours.size() > 1 and not (colours[1] as Array).is_empty() else c0
	for i in range(ring.size() - 1):
		var a0: float = ring[i][0]
		var a1: float = ring[i + 1][0]
		var panel: Color = (c0 if (i / 6) % 2 == 0 else c1).darkened(lerpf(0.35, 0.12, day))
		for k in range(1, tiers.size()):
			var below: Array = tiers[k - 1]
			var tier: Array = tiers[k]
			# The underside of the tier above and the concourse: dark, behind the fascia.
			_wall(shade, cam, a0, a1, below[1], below[1], below[3], tier[2] + 0.5, under)
			# The fascia along the tier's front, panel by panel in the clubs' colours.
			_wall(lit, cam, a0, a1, tier[0], tier[0], tier[2] - 2.2, tier[2], panel)
			_wall(lit, cam, a0, a1, tier[0], tier[0], tier[2] - 0.25, tier[2], Color(1, 1, 1, 0.25))
		# The roof over the top row: a thin dark lip, a canopy reaching out over the seats
		# (pale, or the SCG's green), or a closed roof's deep edge.
		match str(spec.get("roof", "edge")):
			"canopy":
				_wall(lit, cam, a0, a1, upper[0] - 2.0, upper[1], upper[3] + 5.0, upper[3] + 2.0, roof_c.darkened(0.3))
				_wall(lit, cam, a0, a1, upper[0] - 2.0, upper[0] - 2.0, upper[3] + 4.2, upper[3] + 5.0, roof_c)
			"closed":
				_wall(shade, cam, a0, a1, upper[0] - 8.0, upper[1], upper[3] + 6.0, upper[3] + 12.0, roof_c)
				_wall(lit, cam, a0, a1, upper[0] - 8.0, upper[0] - 8.0, upper[3] + 5.2, upper[3] + 6.0, roof_c.lightened(0.25))
			_:
				_wall(shade, cam, a0, a1, upper[1] - 4.0, upper[1], upper[3] + 1.0, upper[3] + 4.0, roof_c)
	shade.flush(ci)
	var tints := [Color(0.95, 0.95, 0.97), Color(0.86, 0.86, 0.9), Color(0.78, 0.78, 0.82)]
	for k in range(tiers.size()):
		var seats: Texture2D = hill if k == 0 and hill != null else tex
		_tier(ci, cam, ring, tiers[k], seats, tints[k] if tiers.size() == 3 else tints[k * 2])
	lit.flush(ci)
	if spec.get("trusses", false):
		_mcg_trusses(ci, cam, ring, upper)
	# In the wind, the flags people hold up along the front rows stream out, toward the end
	# the breeze blows to (the board's "wind"), wherever on the ground they are.
	var blowing := VignetteWeather.wind_world(VignetteWeather.wind_end(board))
	if VignetteWeather.wind(weather) > 0.0:
		for i in range(1, ring.size(), 2):
			var a: float = ring[i][0]
			var off: float = lower[0] + 3.0 + float(i % 5) * 2.0
			var p := Vector2(cos(a) * (A + FENCE + 2.0 + off), sin(a) * (L + FENCE + 2.0 + off))
			var h: float = lower[2] + (off - lower[0]) * (lower[3] - lower[2]) / (lower[1] - lower[0]) + 1.6
			var s := cam.oval(p, h)
			if s.z <= 0.0:
				continue
			var home := (i / 2) % 2 == 0
			VignetteWeather.draw_flag(ci, Vector2(s.x, s.y), 2.4 * s.z, 2.4 * s.z, 1.5 * s.z,
					c0 if home else c1, t, float(i) * 1.3, 1.0, _second(colours, 0 if home else 1),
					VignetteWeather.flag_stream(cam, p, h + 2.4, blowing))
	# Lights under the roof's edge, every few metres: on at night, coming on at twilight,
	# off by day.
	var lights := Tris.new()
	for i in range(0, ring.size(), 2):
		if lamps <= 0.0:
			break
		var a: float = ring[i][0]
		var p := Vector2(cos(a) * (A + FENCE + 2.0 + upper[1] - 2.0), sin(a) * (L + FENCE + 2.0 + upper[1] - 2.0))
		var s := cam.oval(p, upper[3] + 1.0)
		if s.z <= 0.0:
			continue
		var r := maxf(0.8, 0.35 * s.z)
		lights.poly([Vector2(s.x - r, s.y - r * 0.5), Vector2(s.x + r, s.y - r * 0.5),
				Vector2(s.x + r, s.y + r * 0.5), Vector2(s.x - r, s.y + r * 0.5)], Color(1.0, 0.97, 0.88, 0.9 * lamps))
	lights.flush(ci)
	# In the wind, the flags along the roofs stream out in the clubs' colours.
	var wind := VignetteWeather.wind(weather)
	if wind > 0.0:
		for i in range(0, ring.size(), 9):
			var a: float = ring[i][0]
			var p := Vector2(cos(a) * (A + FENCE + 2.0 + upper[1] - 1.0), sin(a) * (L + FENCE + 2.0 + upper[1] - 1.0))
			var s := cam.oval(p, upper[3] + 4.0)
			if s.z <= 0.0:
				continue
			var home := (i / 9) % 2 == 0
			VignetteWeather.draw_flag(ci, Vector2(s.x, s.y), 7.0 * s.z, 5.0 * s.z, 2.6 * s.z,
					c0 if home else c1, t, float(i) * 0.7, wind, _second(colours, 0 if home else 1),
					VignetteWeather.flag_stream(cam, p, upper[3] + 11.0, blowing))
	_screen(ci, cam, c0, c1, board, 1, weather, day)
	if int(spec.get("screens", 1)) > 1:
		_screen(ci, cam, c0, c1, board, -1, weather, day)
	elif spec.get("heritage_board", false):
		_heritage_board(ci, cam)
	_haze(ci, cam, weather, slot)


## By day: empty seats, bare concrete, a roof and a light tower's steel in daylight.
const DAY_SEAT := Color(0.42, 0.45, 0.5)
const DAY_CONCRETE := Color(0.3, 0.31, 0.34)
const DAY_ROOF := Color(0.74, 0.76, 0.79)
const DAY_STEEL := Color(0.52, 0.54, 0.57)
const DAY_LAMP := Color(0.72, 0.74, 0.76)


## A colour under the lights turned toward its daylight colour: share 0 gives it back
## untouched (night), so nothing at night moves by a shade.
static func _lit(c: Color, by_day: Color, share: float) -> Color:
	return c if share <= 0.0 else c.lerp(by_day, share)


## Which way the big screen's wind arrow points at an end (+1 the +y end, -1 the other)
## when the breeze blows to wind_end: up (+1) when it blows toward that screen's end,
## since on any shot that shows the screen its end is the far one; down (-1) when it
## blows back toward the camera's end.
static func wind_arrow(wind_end: int, end := 1) -> int:
	return 1 if wind_end * end > 0 else -1


const STAND_TILE := 35.0          # metres of stand per copy of the seats texture
## A grass hill's turf under the crowd sitting on it, darker than the oval at night.
const HILL := Color(0.11, 0.24, 0.12)


## Adelaide Oval's heritage scoreboard at the other end from the big screen: a green
## board with a white clock tower on top and rows of white name panels.
static func _heritage_board(ci: CanvasItem, cam: Cam) -> void:
	var at := Vector2(0.0, -(L + FENCE + 30.0))
	var c := cam.oval(at, 12.0)
	if c.z <= 0.0:
		return
	var size := Vector2(26.0, 14.0) * c.z
	var r := Rect2(Vector2(c.x, c.y) - size * 0.5, size)
	ci.draw_rect(r, Color(0.13, 0.3, 0.2), true)
	ci.draw_rect(r, Color(0.85, 0.85, 0.8, 0.6), false, maxf(1.0, 0.25 * c.z))
	for row in range(4):
		for col in range(6):
			var cell := Rect2(r.position + r.size * Vector2(0.06 + col * 0.15, 0.14 + row * 0.2), r.size * Vector2(0.11, 0.1))
			ci.draw_rect(cell, Color(0.93, 0.93, 0.9, 0.85), true)
	var tower := Rect2(Vector2(c.x, r.position.y) + Vector2(-2.0, -6.0) * c.z, Vector2(4.0, 6.0) * c.z)
	ci.draw_rect(tower, Color(0.9, 0.9, 0.86), true)
	ci.draw_circle(tower.get_center(), 1.3 * c.z, Color(0.2, 0.2, 0.22))


## Columns round the stand ring at even steps along it: [angle, metres along].
static var _ring_cache := {}

static func _ring_columns(ax: float, ay: float, step: float) -> Array:
	# The same ring every frame (constants only): worked out once.
	var key := Vector3(ax, ay, step)
	if not _ring_cache.has(key):
		_ring_cache[key] = _ring_columns_made(ax, ay, step)
	return _ring_cache[key]


static func _ring_columns_made(ax: float, ay: float, step: float) -> Array:
	var fine := 900
	var s := 0.0
	var prev := Vector2(ax, 0.0)
	var columns := [[0.0, 0.0]]
	var next := step
	for i in range(1, fine + 1):
		var a := TAU * float(i) / fine
		var p := Vector2(cos(a) * ax, sin(a) * ay)
		s += p.distance_to(prev)
		prev = p
		if s >= next:
			columns.append([a, next])
			next += step
	if float(columns[columns.size() - 1][0]) < TAU - 0.0001:
		columns.append([TAU, next])               # close the ring: no seam where it began
	return columns


## One tier of seats, raked from its front (inner offset, height) to its back, the seats
## texture laid along it.
static func _tier(ci: CanvasItem, cam: Cam, ring: Array, tier: Array, tex: Texture2D, tint: Color) -> void:
	var pts := PackedVector2Array()
	var uvs := PackedVector2Array()
	var cols := PackedColorArray()
	var idx := PackedInt32Array()
	var base_a := A + FENCE + 2.0
	var base_l := L + FENCE + 2.0
	for i in range(ring.size() - 1):
		var a0: float = ring[i][0]
		var a1: float = ring[i + 1][0]
		var u0 := fposmod(float(ring[i][1]) / STAND_TILE, 1.0)
		var u1 := u0 + (float(ring[i + 1][1]) - float(ring[i][1])) / STAND_TILE
		var quad := [Vector3(cos(a0) * (base_a + tier[0]), sin(a0) * (base_l + tier[0]), tier[2]),
				Vector3(cos(a1) * (base_a + tier[0]), sin(a1) * (base_l + tier[0]), tier[2]),
				Vector3(cos(a1) * (base_a + tier[1]), sin(a1) * (base_l + tier[1]), tier[3]),
				Vector3(cos(a0) * (base_a + tier[1]), sin(a0) * (base_l + tier[1]), tier[3])]
		var uv := [Vector2(u0, 1.0), Vector2(u1, 1.0), Vector2(u1, 0.0), Vector2(u0, 0.0)]
		var ls := []
		for q in quad:
			var l := cam.local(cam.to_scene * Vector2(q.x, q.y))
			if l.y < NEAR:
				break
			ls.append(cam.screen(l, q.z))
		if ls.size() < 4:
			continue
		var b := pts.size()
		for k in range(4):
			pts.append(Vector2(ls[k].x, ls[k].y))
			uvs.append(uv[k])
			cols.append(tint)
		idx.append_array([b, b + 1, b + 2, b, b + 2, b + 3])
	if not idx.is_empty():
		RenderingServer.canvas_item_add_triangle_array(ci.get_canvas_item(), idx, pts, cols, uvs,
				PackedInt32Array(), PackedFloat32Array(), tex.get_rid())


## An upright band round the stand between two angles: from offset o0 to o1 beyond the
## stand's front line, heights h0 to h1.
static func _wall(tri: Tris, cam: Cam, a0: float, a1: float, o0: float, o1: float, h0: float, h1: float, colour: Color) -> void:
	var ax := A + FENCE + 2.0
	var ay := L + FENCE + 2.0
	var p0 := Vector2(cos(a0) * (ax + o0), sin(a0) * (ay + o0))
	var p1 := Vector2(cos(a1) * (ax + o0), sin(a1) * (ay + o0))
	var s: Array
	if o0 == o1:
		# A flat band (the usual one): the same two ground points at both heights.
		var l0 := cam.local(cam.to_scene * p0)
		var l1 := cam.local(cam.to_scene * p1)
		if l0.y < NEAR or l1.y < NEAR:
			return
		s = [cam.screen(l0, h0), cam.screen(l1, h0), cam.screen(l1, h1), cam.screen(l0, h1)]
	else:
		var q0 := Vector2(cos(a0) * (ax + o1), sin(a0) * (ay + o1))
		var q1 := Vector2(cos(a1) * (ax + o1), sin(a1) * (ay + o1))
		s = [cam.oval(p0, h0), cam.oval(p1, h0), cam.oval(q1, h1), cam.oval(q0, h1)]
	for v in s:
		if v.z <= 0.0:
			return
	tri.poly([Vector2(s[0].x, s[0].y), Vector2(s[1].x, s[1].y), Vector2(s[2].x, s[2].y), Vector2(s[3].x, s[3].y)], colour)


## The light towers outside the stands: a mast and a bank of lights at the top of each,
## glowing into the night. day: how much daylight is on the steel; lamps: how strongly
## the lights show (the glow goes with them; by day the bank is a dull grey frame).
static func _towers(ci: CanvasItem, cam: Cam, day := 0.0, lamps := 1.0) -> void:
	var steel := _lit(Color(0.09, 0.09, 0.1), DAY_STEEL, day)
	var lamp := _lit(Color(0.98, 0.97, 0.9), DAY_LAMP, 1.0 - lamps)
	match str(spec.get("towers", "masts")):
		"mcg":
			_mcg_towers(ci, cam, steel, lamp, lamps)
			return
		"none":
			return
	for p in _tower_spots():
		var base := cam.oval(p, 0.0)
		if base.z <= 0.0:
			continue
		var top := cam.oval(p, 78.0)
		var w := maxf(1.0, 1.4 * base.z)
		ci.draw_rect(Rect2(base.x - w * 0.5, top.y, w, base.y - top.y), steel, true)
		var bank := Vector2(6.0, 4.0) * top.z
		for g in range(6):
			if lamps <= 0.0:
				break
			ci.draw_circle(Vector2(top.x, top.y), bank.x * (1.0 + g * 1.1), Color(1.0, 0.95, 0.82, (0.05 - g * 0.007) * lamps))
		ci.draw_rect(Rect2(Vector2(top.x, top.y) - bank * 0.5, bank), lamp, true)


## The MCG's stands as seen from the ground (Commons, "MCG Shane Warne Stand.png",
## EchidnaLives, 2022, CC BY-SA 4.0): three tiers of seats, a band of boxes under the
## middle and upper tiers, a thin dark roof with a row of pale trusses standing up along
## its edge. Heights are read from the photo, not published. Its tiers and its pale
## blue-grey seats (darker than by day, so the crowd stays behind the players) are in
## data/grounds.json with every other ground's.
## A truss every this many stand columns, its base and height in metres.
const MCG_TRUSS_EVERY := 6
const MCG_TRUSS_H := 5.0

static func _mcg_trusses(ci: CanvasItem, cam: Cam, ring: Array, upper: Array) -> void:
	var tri := Tris.new()
	var ax := A + FENCE + 2.0
	var ay := L + FENCE + 2.0
	var off: float = upper[1] - 2.0
	var h0: float = upper[3] + 4.0
	# The roof's top edge, caught by the lights, so the trusses stand on something.
	for i in range(ring.size() - 1):
		_wall(tri, cam, ring[i][0], ring[i + 1][0], upper[1] - 4.0, upper[1], h0 - 0.5, h0, Color(0.5, 0.51, 0.54))
	for i in range(0, ring.size() - 3, MCG_TRUSS_EVERY):
		var a0: float = ring[i][0]
		var a1: float = ring[i + 3][0]
		var am := (a0 + a1) * 0.5
		var p0 := cam.oval(Vector2(cos(a0) * (ax + off), sin(a0) * (ay + off)), h0)
		var p1 := cam.oval(Vector2(cos(a1) * (ax + off), sin(a1) * (ay + off)), h0)
		var pm := cam.oval(Vector2(cos(am) * (ax + off), sin(am) * (ay + off)), h0 + MCG_TRUSS_H)
		if p0.z <= 0.0 or p1.z <= 0.0 or pm.z <= 0.0:
			continue
		var a := Vector2(p0.x, p0.y)
		var b := Vector2(p1.x, p1.y)
		var m := Vector2(pm.x, pm.y)
		# An open triangle of steel: two slim legs up to the apex.
		var w := maxf(0.8, 0.35 * pm.z)
		for leg in [[a, m], [b, m]]:
			var d: Vector2 = (leg[1] - leg[0]).orthogonal().normalized() * w * 0.5
			tri.poly([leg[0] - d, leg[0] + d, leg[1] + d, leg[1] - d], Color(0.62, 0.63, 0.66))
	tri.flush(ci)


## The MCG's six light towers (mcg.org.au, "Light towers"): hollow tubular steel masts
## about 75 m high, tapering from 4.2 m across at the foot to 2 m at the top, each
## carrying a head frame of lamps a further 10 m high, angled 15 degrees in towards the
## ground. The frame's width isn't published: 14 m reads right against photos.
const MCG_MAST := 75.0
const MCG_FRAME_H := 10.0
const MCG_FRAME_W := 14.0
const MCG_TILT := 15.0

static func _mcg_towers(ci: CanvasItem, cam: Cam, steel := Color(0.09, 0.09, 0.1),
		lamp_colour := Color(0.98, 0.97, 0.9), lamps := 1.0) -> void:
	for p in _tower_spots():
		var base := cam.oval(p, 0.0)
		var top := cam.oval(p, MCG_MAST)
		if base.z <= 0.0 or top.z <= 0.0:
			continue
		var wb := maxf(1.0, 4.2 * base.z) * 0.5
		var wt := maxf(1.0, 2.0 * top.z) * 0.5
		ci.draw_colored_polygon(PackedVector2Array([Vector2(base.x - wb, base.y), Vector2(base.x + wb, base.y),
				Vector2(top.x + wt, top.y), Vector2(top.x - wt, top.y)]), steel)
		# The head frame: across the tower's line to the centre, its top leaning in.
		var inward: Vector2 = (-(p as Vector2)).normalized()
		var across := Vector2(-inward.y, inward.x) * MCG_FRAME_W * 0.5
		var lean := inward * MCG_FRAME_H * sin(deg_to_rad(MCG_TILT))
		var rise := MCG_FRAME_H * cos(deg_to_rad(MCG_TILT))
		var corners := [cam.oval(p - across, MCG_MAST), cam.oval(p + across, MCG_MAST),
				cam.oval(p + across + lean, MCG_MAST + rise), cam.oval(p - across + lean, MCG_MAST + rise)]
		var quad := PackedVector2Array()
		for c in corners:
			if c.z <= 0.0:
				quad.clear()
				break
			quad.append(Vector2(c.x, c.y))
		if quad.is_empty():
			continue
		var mid := (quad[0] + quad[1] + quad[2] + quad[3]) * 0.25
		var reach := quad[0].distance_to(quad[1])
		for g in range(6):
			if lamps <= 0.0:
				break
			ci.draw_circle(mid, reach * (0.55 + g * 0.45), Color(1.0, 0.95, 0.82, (0.05 - g * 0.007) * lamps))
		ci.draw_colored_polygon(quad, steel)
		# The lamps, rows across the frame.
		var lamp := maxf(0.8, 0.45 * top.z)
		for row in range(4):
			for col in range(9):
				var u := (float(col) + 0.5) / 9.0
				var v := (float(row) + 0.5) / 4.0
				var at: Vector2 = quad[0].lerp(quad[1], u).lerp(quad[3].lerp(quad[2], u), v)
				ci.draw_rect(Rect2(at - Vector2(lamp, lamp * 0.7), Vector2(lamp * 2.0, lamp * 1.4)), lamp_colour, true)


## Where the big screen at an end (-1: the other one) lands on the screen; empty when it
## is behind the camera.
static func screen_rect(cam: Cam, end := 1) -> Rect2:
	var c := cam.oval(Vector2(0.0, (L + FENCE + 40.0) * end), 30.0)
	if c.z <= 0.0:
		return Rect2()
	var size := Vector2(30.0, 13.0) * c.z
	return Rect2(Vector2(c.x, c.y) - size * 0.5, size)


## The big screen high above the far end, behind the goals, showing the match's score
## as it stands (board): each club's code by a chip of its colour, goals.behinds and
## the total, the quarter beneath. Lit, so it glows a little into the night. The MCG has
## one at each end (end -1: the other one). On a windy day it carries the wind: an arrow
## to the end the breeze blows to (board "wind": +1 the +y end, -1 the other; wind_arrow).
## day: how much daylight; the screen's glow into the air fades with it.
static func _screen(ci: CanvasItem, cam: Cam, home: Color, away: Color, board: Dictionary, end := 1,
		weather := "", day := 0.0) -> void:
	if bool(board.get("off", false)):
		return                                   # a shot too tight for it: half a screen read as a fault
	var r := screen_rect(cam, end)
	if not r.has_area():
		return
	var c := Vector3(r.get_center().x, r.get_center().y, r.size.x / 30.0)
	for g in range(4):
		ci.draw_rect(r.grow((g + 1) * 1.4 * c.z), Color(0.6, 0.7, 0.9, 0.025 * lerpf(1.0, 0.3, day)), true)
	ci.draw_rect(r.grow(0.6 * c.z), Color(0.04, 0.04, 0.05), true)
	ci.draw_rect(r, Color(0.05, 0.07, 0.11), true)
	var codes: Array = board.get("codes", [])
	if codes.size() < 2:
		ci.draw_rect(Rect2(r.position + r.size * Vector2(0.06, 0.18), r.size * Vector2(0.4, 0.5)), home.lightened(0.15), true)
		ci.draw_rect(Rect2(r.position + r.size * Vector2(0.54, 0.18), r.size * Vector2(0.4, 0.5)), away.lightened(0.15), true)
		return
	var font: Font = UiKit.BOLD
	var fs := int(3.2 * c.z)
	if fs < 5:
		return                                   # too far to read: just the glow
	var goals: Array = board.get("goals", [0, 0])
	var behinds: Array = board.get("behinds", [0, 0])
	for side in range(2):
		var y := r.position.y + r.size.y * (0.36 + 0.34 * side)
		var chip := Rect2(r.position.x + r.size.x * 0.05, y - fs * 0.78, fs * 0.5, fs * 0.9)
		ci.draw_rect(chip, home if side == 0 else away, true)
		ci.draw_rect(chip, Color(1, 1, 1, 0.35), false, 1.0)
		var g := int(goals[side])
		var b := int(behinds[side])
		ci.draw_string(font, Vector2(chip.end.x + fs * 0.35, y), str(codes[side]),
				HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(1, 1, 1, 0.95))
		ci.draw_string(font, Vector2(r.position.x + r.size.x * 0.42, y), "%d.%d" % [g, b],
				HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(0.9, 0.92, 0.95, 0.9))
		ci.draw_string(font, Vector2(r.position.x, y), str(g * 6 + b),
				HORIZONTAL_ALIGNMENT_RIGHT, r.size.x * 0.95, fs, Color(1.0, 0.86, 0.35, 0.98))
	var q := int(board.get("q", 0))
	if q > 0:
		ci.draw_string(font, Vector2(r.position.x, r.end.y - fs * 0.25), "Q%d" % q,
				HORIZONTAL_ALIGNMENT_CENTER, r.size.x, int(fs * 0.6), Color(1, 1, 1, 0.6))
	if weather == VignetteWeather.WINDY:
		_wind_arrow(ci, r, fs, wind_arrow(VignetteWeather.wind_end(board), end))


## The wind on the big screen, in its bottom left corner: the word and an arrow, up when
## the breeze blows to this screen's end, down when it blows the other way.
static func _wind_arrow(ci: CanvasItem, r: Rect2, fs: int, up: int) -> void:
	var small := int(fs * 0.6)
	var ink := Color(0.62, 0.86, 1.0, 0.95)
	var base := Vector2(r.position.x + r.size.x * 0.05, r.end.y - fs * 0.25)
	ci.draw_string(UiKit.BOLD, base, "WIND", HORIZONTAL_ALIGNMENT_LEFT, -1, small, ink)
	var word := UiKit.BOLD.get_string_size("WIND", HORIZONTAL_ALIGNMENT_LEFT, -1, small).x
	var mid := base + Vector2(word + small * 0.75, -small * 0.38)
	var half := small * 0.48
	var tip := mid + Vector2(0.0, -half * up)
	var tail := mid + Vector2(0.0, half * up)
	ci.draw_line(tail, tip, ink, maxf(1.0, small * 0.16), true)
	ci.draw_colored_polygon(PackedVector2Array([tip + Vector2(0.0, -half * 0.35 * up),
			tip + Vector2(-half * 0.6, half * 0.55 * up), tip + Vector2(half * 0.6, half * 0.55 * up)]), ink)


## The haze the lights make over the far side: a soft band of light on the horizon, over
## the far stands and the far turf.
static func _haze(ci: CanvasItem, cam: Cam, weather := "", slot := VignetteKickoff.NIGHT) -> void:
	var x0 := cam.cx - 4000.0
	var x1 := cam.cx + 4000.0
	var y := cam.hor
	var band := 0.12 * cam.f
	var haze := VignetteWeather.haze(weather, slot)
	var clear := Color(haze.r, haze.g, haze.b, 0.0)
	ci.draw_polygon(PackedVector2Array([Vector2(x0, y - band * 2.0), Vector2(x1, y - band * 2.0), Vector2(x1, y), Vector2(x0, y)]),
			PackedColorArray([clear, clear, haze, haze]))
	ci.draw_polygon(PackedVector2Array([Vector2(x0, y), Vector2(x1, y), Vector2(x1, y + band * 0.6), Vector2(x0, y + band * 0.6)]),
			PackedColorArray([haze, haze, clear, clear]))


## A club's second colour (for the band on its flags), white if it has none.
static func _second(colours: Array, side: int) -> Color:
	if side < colours.size() and (colours[side] as Array).size() > 1:
		return (colours[side] as Array)[1]
	return Color(1, 1, 1)


## Where the six light towers stand outside the stands (oval metres).
static func _tower_spots() -> Array:
	var out := []
	# Masts drawn where the ground has them; under a roof's lights the rain sheen still
	# catches six.
	var n := 6 if spec.is_empty() or spec.get("towers") == "none" else int(spec.get("tower_count", 6))
	for k in range(n):
		var a := TAU * (float(k) + 0.5) / n
		out.append(Vector2(cos(a) * (A + 75.0), sin(a) * (L + 75.0)))
	return out


## Oval points round an ellipse centred at (ox, oy).
static var _geometry := {}

static func _ellipse_ring(ax: float, ay: float, ox: float, oy: float, n: int) -> Array:
	# Fixed points of the oval, the same every frame: made once, read-only for callers.
	var key := [ax, ay, ox, oy, n]
	if not _geometry.has(key):
		_geometry[key] = _ellipse_ring_made(ax, ay, ox, oy, n)
	return _geometry[key]


static func _ellipse_ring_made(ax: float, ay: float, ox: float, oy: float, n: int) -> Array:
	var out := []
	for i in range(n):
		var a := TAU * float(i) / n
		out.append(Vector2(ox + cos(a) * ax, oy + sin(a) * ay))
	return out


## The slice of the oval between y0 and y1 (a mown stripe).
static func _band(y0: float, y1: float) -> Array:
	var key := ["band", y0, y1, A, L]
	if not _geometry.has(key):
		_geometry[key] = _band_made(y0, y1)
	return _geometry[key]


## The slice of the oval between x0 and x1 (a stripe mown along the ground).
static func _band_along(x0: float, x1: float) -> Array:
	var key := ["along", x0, x1, A, L]
	if not _geometry.has(key):
		var near := []
		var far := []
		for i in range(7):
			var x := lerpf(x0, x1, float(i) / 6.0)
			var y := L * sqrt(maxf(0.0, 1.0 - pow(x / A, 2.0)))
			near.append(Vector2(x, -y))
			far.push_front(Vector2(x, y))
		_geometry[key] = near + far
	return _geometry[key]


static func _band_made(y0: float, y1: float) -> Array:
	var left := []
	var right := []
	var steps := 6
	for i in range(steps + 1):
		var y := lerpf(y0, y1, float(i) / steps)
		var x := A * sqrt(maxf(0.0, 1.0 - pow(y / L, 2.0)))
		left.append(Vector2(-x, y))
		right.push_front(Vector2(x, y))
	return left + right


## A convex oval polygon cut at the camera's near plane, projected to the screen.
static func _clip(cam: Cam, poly: Array) -> Array:
	var ls := []
	for p in poly:
		ls.append(cam.local(cam.to_scene * p))
	var out := []
	for i in range(ls.size()):
		var a: Vector2 = ls[i]
		var b: Vector2 = ls[(i + 1) % ls.size()]
		var a_in := a.y >= NEAR
		var b_in := b.y >= NEAR
		if a_in:
			out.append(a)
		if a_in != b_in:
			out.append(a.lerp(b, (NEAR - a.y) / (b.y - a.y)))
	var screen := []
	for l in out:
		var s := cam.screen(l)
		screen.append(Vector2(s.x, s.y))
	return screen


## Triangles gathered and drawn in one call.
class Tris:
	var points := PackedVector2Array()
	var colors := PackedColorArray()
	var indices := PackedInt32Array()

	## A convex polygon, as a fan.
	func poly(pts: Array, colour: Color) -> void:
		if pts.size() < 3:
			return
		var base := points.size()
		for p in pts:
			points.append(p)
			colors.append(colour)
		for i in range(1, pts.size() - 1):
			indices.append_array([base, base + i, base + i + 1])

	func flush(ci: CanvasItem) -> void:
		if not indices.is_empty():
			RenderingServer.canvas_item_add_triangle_array(ci.get_canvas_item(), indices, points, colors)
