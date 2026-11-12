class_name OvalStadium
extends RefCounted
## The replay's stadium seen from straight above, round the live oval (director,
## 2026-11-12: "Replay stadium everywhere"). The same parts the replays are made of:
## the crowd in its seats (VignetteCrowd.seats, the ground's own seat colour and
## hill), the tiers' fascia in the two clubs' colours, the roof's edge and its
## lights, the light towers and their pools of light, and the replay's own grass
## and mown stripes (VignetteGround.GRASS, a stripe every 12 m, the worn patches,
## VignetteWeather.grass for the day).
##
## Looks only. Everything is built once, in ground metres, into a few meshes and
## drawn each frame with one transform, so the oval's frame costs less than the
## flat fill and the turf polygons it replaces. Nothing here is read by the match
## and no disc, tap or line moves: the oval's own lines, discs and hit tests are
## PitchView's, in the same place as before.

## The ring beyond the boundary line, metres out from it: the fence, the front
## tier, the fascia, the top tier, the roof's edge. The replay's stands are
## deeper (data/grounds.json); from above they are drawn to the depth the live
## view has beside the ground, about 28 m at a phone's corners.
const FENCE := 2.0
const LOWER := [3.0, 9.0]
const FASCIA := [9.0, 10.2]
const UPPER := [10.2, 16.0]
const ROOF := [16.0, 19.5]
const FLAG_OUT := 17.6
const TOWER_OUT := 24.5
## Where round the ground the towers and the flags stand, as an angle from the
## goal-to-goal line (degrees), mirrored into each corner: the corners are the
## part of the stand a phone and a PC both show.
const TOWER_AT := 40.0
const FLAGS_AT := [33.0, 40.0, 47.0]
const SEGMENTS := 192
## The crowd: SEAT_TILES copies of the seats texture round the ground (about a
## metre a seat), ROWS_LOWER and ROWS_UPPER rows of it up each tier.
const SEAT_TILES := 8
const ROWS_LOWER := 6
const ROWS_UPPER := 6
const STRIPE_M := 12.0

const NIGHT := "night"
const TWILIGHT := "twilight"
const DAY := "day"

## Beyond the roof, by time of day: the dark outside a lit ground, dusk, daylight
## on the concourse.
const OUTSIDE := {NIGHT: Color(0.035, 0.035, 0.045), TWILIGHT: Color(0.13, 0.10, 0.14), DAY: Color(0.27, 0.28, 0.30)}
## The crowd and the stands under the lights (kept back, so the play stays in
## front), at dusk, and in daylight.
const STAND_LIGHT := {NIGHT: Color(0.74, 0.74, 0.80), TWILIGHT: Color(0.88, 0.78, 0.78), DAY: Color(1.0, 1.0, 1.0)}
## The turf by time of day, over the weather's colours.
## How strongly the towers show: their glow and their pools of light.
const LAMPS := {NIGHT: 1.0, TWILIGHT: 0.6, DAY: 0.0}

var _key := ""
var _flat: ArrayMesh = null         # roof, fascia, walkway: vertex colours
var _lower: ArrayMesh = null        # the front tier's crowd
var _upper: ArrayMesh = null        # the top tier's crowd
var _lamps: ArrayMesh = null        # roof lights, tower banks and their glow
var _pools: ArrayMesh = null        # the towers' pools of light
var _lit: ArrayMesh = null          # the light over the turf (PitchView's own texture)
var _turf: ArrayMesh = null
var _turf_key := ""
var _seats: Texture2D = null
var _hill: Texture2D = null
var _flags: Array = []              # [{at, home}], ground metres

static var _small := {}
static var _pool_tex: Texture2D = null


## Day, twilight or night for the match being shown, in this weather: the same
## pick the call scenes and the replays draw (VignetteGround.slot_now: the match's
## kick-off, and night under a closed roof), so the oval and the scenes never
## disagree about the hour.
static func time_of_day(weather := "") -> String:
	return time_from(VignetteGround.slot_now(weather))


## The three looks from whatever the kick-off says: a word ("day", "twilight",
## "night"), or a record carrying one.
static func time_from(now) -> String:
	if now is Dictionary:
		for k in ["time", "slot", "name", "id", "kind"]:
			if (now as Dictionary).has(k):
				now = (now as Dictionary)[k]
				break
	var word := str(now).to_lower()
	if word.contains("night"):
		return NIGHT
	if word.contains("twi") or word.contains("dusk"):
		return TWILIGHT
	if word.contains("day") or word.contains("afternoon") or word.contains("arvo"):
		return DAY
	return NIGHT


## The turf's two mown colours today: the replay's grass, as the weather and the
## time of day leave it (VignetteWeather.grass, the one the scenes use).
static func grass(weather: String, tod := NIGHT) -> Array:
	return VignetteWeather.grass(weather, VignetteGround.GRASS, tod)


## Which way the flags stream along the ground, +1 toward the end the home side
## kicks to in the first quarter, -1 toward the other: the end the breeze favours.
## The match says who kicks with it first when the result or the live match
## carries it; without either it blows to the +1 end.
static func breeze_toward(result: Dictionary, sim = null) -> float:
	var side := -1
	if result.has("breeze_side"):
		side = int(result["breeze_side"])
	elif sim != null and sim is Object and "breeze_side" in sim:
		side = int(sim.breeze_side)
	return -1.0 if side == 1 else 1.0


## The view's ground under everything: beyond the roof, then the stands. `base` is
## the transform the ground is drawn in (PitchView's quarter turn and its shake),
## `c` the centre of the ground and `s` pixels a metre, in that frame.
func draw_stands(ci: CanvasItem, view: Rect2, c: Vector2, s: float, colours: Array, weather: String, tod: String) -> void:
	_build(colours)
	ci.draw_rect(view, OUTSIDE.get(tod, OUTSIDE[NIGHT]), true)
	var xf := Transform2D(0.0, Vector2(s, s), 0.0, c)
	var light: Color = STAND_LIGHT.get(tod, STAND_LIGHT[NIGHT])
	if weather == VignetteWeather.WET:
		light = Color(light.r * 0.80, light.g * 0.86, light.b * 0.96)
	ci.draw_mesh(_lower, _hill if _hill != null else _seats, xf, light)
	ci.draw_mesh(_upper, _seats, xf, Color(light.r * 0.86, light.g * 0.86, light.b * 0.88))
	ci.draw_mesh(_flat, null, xf, light)
	var lamps: float = LAMPS.get(tod, 1.0)
	if lamps > 0.0:
		ci.draw_mesh(_lamps, null, xf, Color(1, 1, 1, lamps))


## The turf: the replay's grass and its mown stripes, the worn patches at the
## goal squares and the centre, then the light over it (`light`, PitchView's).
func draw_turf(ci: CanvasItem, c: Vector2, s: float, weather: String, tod: String, light: Texture2D) -> void:
	var key := weather + "|" + tod
	if _turf == null or key != _turf_key:
		_turf_key = key
		_turf = _turf_mesh(grass(weather, tod))
	var xf := Transform2D(0.0, Vector2(s, s), 0.0, c)
	ci.draw_mesh(_turf, null, xf)
	if _lit == null:
		_lit = _lit_mesh()
	# By day the ground is evenly lit: the fall-off into the fence's shadow is half as deep.
	ci.draw_mesh(_lit, light, xf, Color(1, 1, 1, 0.5 if tod == DAY else 1.0))


## The towers' pools of light, over the pockets and the front rows (not by day).
func draw_pools(ci: CanvasItem, c: Vector2, s: float, tod: String) -> void:
	var lamps: float = LAMPS.get(tod, 1.0)
	if lamps <= 0.0 or _pools == null:
		return
	ci.draw_mesh(_pools, _pool_texture(), Transform2D(0.0, Vector2(s, s), 0.0, c), Color(1, 1, 1, lamps))


## In the wind, the flags on the roof stream toward the end the breeze favours
## (`toward`: +1 or -1 along the ground), each in a club's colours. The only part
## drawn fresh every frame: twelve flags.
func draw_flags(ci: CanvasItem, base: Transform2D, c: Vector2, s: float, colours: Array, t: float, toward: float) -> void:
	var w := 9.0 * s
	var h := 3.4 * s
	for i in range(_flags.size()):
		var f: Dictionary = _flags[i]
		var at: Vector2 = c + (f["at"] as Vector2) * s
		var side := 0 if bool(f["home"]) else 1
		# Streaming along the ground, a little across it, as VignetteWeather.WIND_DIR.
		var ang := (0.0 if toward > 0.0 else PI) + 0.22 * toward
		ci.draw_set_transform_matrix(base * Transform2D(ang, at))
		ci.draw_circle(Vector2.ZERO, maxf(1.6, 0.6 * s), Color(0.85, 0.85, 0.88))
		VignetteWeather.draw_flag(ci, Vector2(0.0, -h * 0.5), 0.0, w, h, _first(colours, side), t, float(i) * 1.3, 1.0,
				VignetteGround._second(colours, side))
	ci.draw_set_transform_matrix(base)


## Where the flags stand, ground metres (for tests and captures).
func flag_spots() -> Array:
	return _flags


static func _first(colours: Array, side: int) -> Color:
	if side < colours.size() and not (colours[side] as Array).is_empty():
		return (colours[side] as Array)[0]
	return Color(0.3, 0.3, 0.32)


static func _ring_point(out: float, ang: float) -> Vector2:
	return Vector2(cos(ang) * (MatchMotion.HALF_LEN + out), sin(ang) * (MatchMotion.HALF_WID + out))


func _build(colours: Array) -> void:
	var spec: Dictionary = VignetteGround.spec
	if spec.is_empty():
		VignetteGround._apply(VignetteGround.venue)
		spec = VignetteGround.spec
	var key := "%s|%s" % [str(colours), VignetteGround.venue]
	if key == _key and _flat != null:
		return
	_key = key
	_seats = _small_seats(colours, 11, VignetteGround.seat_colour())
	_hill = _small_seats(colours, 12, VignetteGround.HILL) if spec.get("hill", false) else null
	_lower = _tier_mesh(LOWER, 0, ROWS_LOWER, Color(0.95, 0.95, 0.97))
	_upper = _tier_mesh(UPPER, 14, ROWS_UPPER, Color(0.95, 0.95, 0.97))
	var roof := Color.html(str(spec.get("roof_colour", "#0f0f12")))
	var c0 := _first(colours, 0)
	var c1 := _first(colours, 1) if colours.size() > 1 else c0
	var flat := Build.new()
	var lamps := Build.new()
	for i in range(SEGMENTS):
		var a0 := TAU * float(i) / float(SEGMENTS)
		var a1 := TAU * float(i + 1) / float(SEGMENTS)
		# The walkway behind the fence, in the front tier's shadow.
		flat.band(a0, a1, FENCE, LOWER[0], Color(0.045, 0.045, 0.055))
		# The fascia along the top tier's front, panel by panel in the clubs' colours.
		var panel: Color = (c0 if (i / 6) % 2 == 0 else c1).darkened(0.35)
		flat.band(a0, a1, FASCIA[0], FASCIA[1], panel)
		flat.band(a0, a1, FASCIA[0], FASCIA[0] + 0.3, Color(1, 1, 1, 0.25))
		# The roof over the top rows: a canopy is pale (or the SCG's green), an edge dark.
		var canopy := str(spec.get("roof", "edge")) != "edge"
		flat.band(a0, a1, ROOF[0], ROOF[1], roof.lightened(0.12) if canopy else roof.lightened(0.05))
		flat.band(a0, a1, ROOF[0], ROOF[0] + 0.5, roof.lightened(0.3))
		# The stand's shadow on the ground outside, fading out with no edge.
		flat.fade(a0, a1, ROOF[1], ROOF[1] + 14.0, Color(0.03, 0.03, 0.04, 0.55))
		# Lights under the roof's edge, every few metres.
		if i % 2 == 0:
			var p := _ring_point(ROOF[0] + 0.25, a0)
			lamps.quad(p, 0.55, Color(1.0, 0.97, 0.88, 0.9))
	# The light towers outside the stands: a mast's head, its bank of lights and the glow.
	var towers := []
	_flags = []
	if str(spec.get("towers", "masts")) != "none":
		for q in range(4):
			towers.append(_corner(TOWER_AT, q))
	for q in range(4):
		for k in range(FLAGS_AT.size()):
			_flags.append({"at": _ring_point(FLAG_OUT, _corner(float(FLAGS_AT[k]), q)), "home": (q + k) % 2 == 0})
	var pools := Build.new()
	for ang in towers:
		var p := _ring_point(TOWER_OUT, float(ang))
		for g in range(5, -1, -1):
			lamps.disc(p, 2.2 * (1.0 + float(g) * 1.1), Color(1.0, 0.95, 0.82, 0.07 - float(g) * 0.009))
		flat.quad(p, 2.0, Color(0.09, 0.09, 0.1))
		lamps.quad(p, 1.4, Color(0.98, 0.97, 0.9))
		# Its pool of light: on the pocket and the front rows below it.
		pools.tex_quad(_ring_point(-9.0, float(ang)), 34.0)
	_flat = flat.mesh()
	_lamps = lamps.mesh()
	_pools = pools.mesh() if not towers.is_empty() else null


## The angle `deg` from the goal-to-goal line, in corner q (0 to 3).
static func _corner(deg: float, q: int) -> float:
	var a := deg_to_rad(deg)
	match q:
		1:
			return PI - a
		2:
			return PI + a
		3:
			return TAU - a
	return a


## One tier of seats as a ring of quads, the crowd texture laid round it: `rows`
## rows of the texture from row `from` up the tier.
func _tier_mesh(span: Array, from: int, rows: int, tint: Color) -> ArrayMesh:
	var b := Build.new()
	var per := SEGMENTS / SEAT_TILES
	var v0 := float(from) / float(VignetteCrowd.SEAT_ROWS)
	var v1 := float(from + rows) / float(VignetteCrowd.SEAT_ROWS)
	for i in range(SEGMENTS):
		var a0 := TAU * float(i) / float(SEGMENTS)
		var a1 := TAU * float(i + 1) / float(SEGMENTS)
		var u0 := float(i % per) / float(per)
		var u1 := float(i % per + 1) / float(per)
		b.band(a0, a1, float(span[0]), float(span[1]), tint, Rect2(u0, v0, u1 - u0, v1 - v0))
	return b.mesh()


## The replay's seats texture at a quarter of its size: from above a seat is a
## few pixels, and the full texture would shimmer as the camera moves.
static func _small_seats(colours: Array, seed: int, seat: Color) -> Texture2D:
	var key := "%s|%d|%s" % [str(colours), seed, seat.to_html()]
	if _small.has(key):
		return _small[key]
	if _small.size() > 6:
		_small.clear()
	var img: Image = VignetteCrowd.seats(colours, seed, seat).get_image()
	img.shrink_x2()
	img.shrink_x2()
	var tex := ImageTexture.create_from_image(img)
	_small[key] = tex
	return tex


static func _pool_texture() -> Texture2D:
	if _pool_tex == null:
		var g := Gradient.new()
		g.offsets = PackedFloat32Array([0.0, 0.5, 1.0])
		g.colors = PackedColorArray([Color(1.0, 0.97, 0.86, 0.15), Color(1.0, 0.97, 0.86, 0.05), Color(1.0, 0.97, 0.86, 0.0)])
		var t := GradientTexture2D.new()
		t.gradient = g
		t.fill = GradientTexture2D.FILL_RADIAL
		t.fill_from = Vector2(0.5, 0.5)
		t.fill_to = Vector2(1.0, 0.5)
		t.width = 64
		t.height = 64
		_pool_tex = t
	return _pool_tex


## The oval in ground metres: the grass, a mown stripe every 12 m across it (as
## VignetteGround.draw_ground lays them), the worn turf at the goal squares and
## the centre circle.
static func _turf_mesh(cols: Array) -> ArrayMesh:
	var b := Build.new()
	var hl := MatchMotion.HALF_LEN
	var hw := MatchMotion.HALF_WID
	b.ellipse(Vector2.ZERO, hl, hw, 128, cols[0])
	var x := -hl
	var n := 0
	while x < hl:
		if n % 2 == 1:
			b.stripe(x, minf(x + STRIPE_M, hl), hl, hw, cols[1])
		x += STRIPE_M
		n += 1
	var worn: Array = VignetteGround.WORN
	for end in [-1.0, 1.0]:
		var gx: float = PitchView.GOAL_LINE_M * end
		b.ellipse(Vector2(gx - 3.5 * end, 0.0), 5.0, 4.2, 24, worn[0])
		b.ellipse(Vector2(gx - 2.6 * end, 0.4), 2.8, 2.4, 18, worn[1])
	b.ellipse(Vector2.ZERO, 3.2, 4.0, 24, worn[0])
	b.ellipse(Vector2(-0.2, 0.3), 1.4, 1.8, 16, worn[1])
	return b.mesh()


static func _lit_mesh() -> ArrayMesh:
	var b := Build.new()
	b.ellipse(Vector2.ZERO, MatchMotion.HALF_LEN, MatchMotion.HALF_WID, 96, Color.WHITE, true)
	return b.mesh()


## Triangles gathered into one mesh: positions in ground metres, a colour and
## (for the textured ones) a place on the texture at every corner.
class Build:
	var pts := PackedVector2Array()
	var cols := PackedColorArray()
	var uvs := PackedVector2Array()

	func tri(a: Vector2, b: Vector2, c: Vector2, col: Color, ua := Vector2.ZERO, ub := Vector2.ZERO, uc := Vector2.ZERO) -> void:
		pts.append(a)
		pts.append(b)
		pts.append(c)
		cols.append(col)
		cols.append(col)
		cols.append(col)
		uvs.append(ua)
		uvs.append(ub)
		uvs.append(uc)

	## A piece of the ring between two angles, `o0` to `o1` metres beyond the boundary.
	func band(a0: float, a1: float, o0: float, o1: float, col: Color, uv := Rect2()) -> void:
		var p00 := OvalStadium._ring_point(o0, a0)
		var p01 := OvalStadium._ring_point(o0, a1)
		var p10 := OvalStadium._ring_point(o1, a0)
		var p11 := OvalStadium._ring_point(o1, a1)
		var u00 := uv.position
		var u01 := Vector2(uv.end.x, uv.position.y)
		var u10 := Vector2(uv.position.x, uv.end.y)
		var u11 := uv.end
		tri(p00, p10, p11, col, u00, u10, u11)
		tri(p00, p11, p01, col, u00, u11, u01)

	## The same piece, its colour fading to nothing at the outer edge.
	func fade(a0: float, a1: float, o0: float, o1: float, col: Color) -> void:
		var from := pts.size()
		band(a0, a1, o0, o1, col)
		var clear := Color(col, 0.0)
		for k in [1, 2, 4]:      # band()'s corners on the outer edge
			cols[from + k] = clear

	func quad(c: Vector2, half: float, col: Color) -> void:
		tri(c + Vector2(-half, -half), c + Vector2(half, -half), c + Vector2(half, half), col)
		tri(c + Vector2(-half, -half), c + Vector2(half, half), c + Vector2(-half, half), col)

	func tex_quad(c: Vector2, half: float) -> void:
		tri(c + Vector2(-half, -half), c + Vector2(half, -half), c + Vector2(half, half), Color.WHITE,
				Vector2(0, 0), Vector2(1, 0), Vector2(1, 1))
		tri(c + Vector2(-half, -half), c + Vector2(half, half), c + Vector2(-half, half), Color.WHITE,
				Vector2(0, 0), Vector2(1, 1), Vector2(0, 1))

	func disc(c: Vector2, r: float, col: Color) -> void:
		ellipse(c, r, r, 20, col)

	## A filled ellipse; `lit` lays a texture over it corner to corner.
	func ellipse(c: Vector2, a: float, b: float, n: int, col: Color, lit := false) -> void:
		for i in range(n):
			var t0 := TAU * float(i) / float(n)
			var t1 := TAU * float(i + 1) / float(n)
			var d0 := Vector2(cos(t0), sin(t0))
			var d1 := Vector2(cos(t1), sin(t1))
			if lit:
				tri(c, c + Vector2(d0.x * a, d0.y * b), c + Vector2(d1.x * a, d1.y * b), col,
						Vector2(0.5, 0.5), Vector2(0.5, 0.5) + d0 * 0.5, Vector2(0.5, 0.5) + d1 * 0.5)
			else:
				tri(c, c + Vector2(d0.x * a, d0.y * b), c + Vector2(d1.x * a, d1.y * b), col)

	## A mown stripe from x0 to x1, cut exactly to the oval.
	func stripe(x0: float, x1: float, hl: float, hw: float, col: Color) -> void:
		var steps := 8
		for i in range(steps):
			var xa := lerpf(x0, x1, float(i) / float(steps))
			var xb := lerpf(x0, x1, float(i + 1) / float(steps))
			var ya := hw * sqrt(maxf(0.0, 1.0 - pow(clampf(xa / hl, -1.0, 1.0), 2.0)))
			var yb := hw * sqrt(maxf(0.0, 1.0 - pow(clampf(xb / hl, -1.0, 1.0), 2.0)))
			tri(Vector2(xa, -ya), Vector2(xb, -yb), Vector2(xb, yb), col)
			tri(Vector2(xa, -ya), Vector2(xb, yb), Vector2(xa, ya), col)

	func mesh() -> ArrayMesh:
		var m := ArrayMesh.new()
		if pts.is_empty():
			return m
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = pts
		arr[Mesh.ARRAY_COLOR] = cols
		arr[Mesh.ARRAY_TEX_UV] = uvs
		m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		return m
