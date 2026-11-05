class_name VignetteAtmos
extends RefCounted
## Depth and air over the match vignettes (prototype "atmos", director 2026-11-06: the
## lighting is "so sterile"). Presentation only, drawn as extra draw calls: no figure
## sheet, no figure shader logic and no full-screen pass is touched.
##   draw_back (after the ground and goals, before the players):
##     the far field darkens (the lights fall off toward the far end), then far stands and
##     far turf fade and cool into the air's haze; the mown stripes catch a sheen that
##     flips with which way the camera looks along them; each light tower glows in the
##     air round it and throws a faint shaft of light down onto the oval.
##   draw_front (after the weather, before the names and bars):
##     a glare streak across each light bank, a dusting of motes drifting in the light
##     (still under Settings > Reduced motion), and the corners falling into shadow.
## The weather sets the air: wet (mist, bigger halos), hot (warm dust), windy and perfect
## (a clear night: least haze). Players stay crisp: nothing hazes them but the glare.

## The switch: false draws exactly what the game drew before.
const ON := false

static var _soft: GradientTexture2D
static var _edge: GradientTexture2D


## How the air reads for this weather: haze colour and strength, tower glow and its
## size, shaft strength, motes (count) and mote colour.
static func air(weather: String) -> Dictionary:
	match weather:
		VignetteWeather.WET:
			return {"haze": Color(0.56, 0.63, 0.72), "haze_a": 0.42, "glow": 0.5, "glow_r": 1.7,
					"shaft": 0.075, "motes": 0, "mote": Color(0.85, 0.9, 1.0), "fall": 0.26}
		VignetteWeather.HOT:
			return {"haze": Color(0.86, 0.74, 0.55), "haze_a": 0.36, "glow": 0.34, "glow_r": 1.15,
					"shaft": 0.06, "motes": 46, "mote": Color(1.0, 0.9, 0.7), "fall": 0.2}
	return {"haze": Color(0.5, 0.58, 0.72), "haze_a": 0.34, "glow": 0.36, "glow_r": 1.0,
			"shaft": 0.035, "motes": 26, "mote": Color(0.95, 0.95, 1.0), "fall": 0.22}


static func _soft_tex() -> GradientTexture2D:
	if _soft == null:
		var g := Gradient.new()
		g.offsets = PackedFloat32Array([0.0, 0.18, 0.5, 1.0])
		g.colors = PackedColorArray([Color(1, 1, 1, 1), Color(1, 1, 1, 0.45), Color(1, 1, 1, 0.1), Color(1, 1, 1, 0)])
		_soft = GradientTexture2D.new()
		_soft.gradient = g
		_soft.fill = GradientTexture2D.FILL_RADIAL
		_soft.fill_from = Vector2(0.5, 0.5)
		_soft.fill_to = Vector2(1.0, 0.5)
		_soft.width = 128
		_soft.height = 128
	return _soft


static func _edge_tex() -> GradientTexture2D:
	if _edge == null:
		var g := Gradient.new()
		g.offsets = PackedFloat32Array([0.0, 0.55, 1.0])
		g.colors = PackedColorArray([Color(0, 0, 0, 0), Color(0, 0, 0, 0.0), Color(0, 0, 0, 1)])
		_edge = GradientTexture2D.new()
		_edge.gradient = g
		_edge.fill = GradientTexture2D.FILL_RADIAL
		_edge.fill_from = Vector2(0.5, 0.5)
		_edge.fill_to = Vector2(1.2, 0.5)
		_edge.width = 128
		_edge.height = 128
	return _edge


## Screen y of the turf at distance z metres ahead of the camera.
static func _ground_y(cam: VignetteGround.Cam, z: float) -> float:
	return cam.hor + cam.f * cam.height / maxf(z, 0.01)


## A full-width band from y0 to y1, colour c0 at the top fading to c1 at the bottom.
static func _band(ci: CanvasItem, stage: Rect2, y0: float, y1: float, c0: Color, c1: Color) -> void:
	if y1 - y0 < 0.5:
		return
	var x0 := stage.position.x
	var x1 := stage.end.x
	ci.draw_polygon(PackedVector2Array([Vector2(x0, y0), Vector2(x1, y0), Vector2(x1, y1), Vector2(x0, y1)]),
			PackedColorArray([c0, c0, c1, c1]))


## Behind the players. Returns the light banks' screen points and radii ([Vector3]) in
## ci's current drawing space, for draw_front.
static func draw_back(ci: CanvasItem, cam: VignetteGround.Cam, stage: Rect2, weather: String) -> Array:
	if not ON:
		return []
	var a := air(weather)
	var hz: Color = a["haze"]
	var ha: float = a["haze_a"]
	var hor := cam.hor
	var clear := Color(hz, 0.0)
	var dark := Color(0.0, 0.01, 0.03, 0.0)
	# The lights fall off toward the far end: the turf from 45 m out darkens to 150 m.
	var y45 := _ground_y(cam, 45.0)
	var y150 := _ground_y(cam, 150.0)
	_band(ci, stage, y150, y45, Color(dark, a["fall"]), dark)
	# Aerial perspective: the far turf and the stands above it fade and cool into the haze,
	# strongest where they meet (farthest), gone by 70 m out and up the stands' height.
	var up := maxf(cam.f * 40.0 / 230.0, (hor - stage.position.y) * 0.5)
	var y70 := _ground_y(cam, 70.0)
	var y220 := _ground_y(cam, 220.0)
	_band(ci, stage, hor - up * 1.5, hor - up * 0.3, clear, Color(hz, ha * 0.6))
	_band(ci, stage, hor - up * 0.3, y220, Color(hz, ha * 0.6), Color(hz, ha))
	_band(ci, stage, y220, y150, Color(hz, ha), Color(hz, ha * 0.45))
	_band(ci, stage, y150, y70, Color(hz, ha * 0.45), clear)
	_sheen(ci, cam, ha)
	return _lights(ci, cam, a)


## The mown stripes' sheen: the grass laid away from the camera shines, laid toward it
## darkens, so it flips as the camera looks up or down the ground; strongest where the
## view grazes the turf (farther out).
static func _sheen(ci: CanvasItem, cam: VignetteGround.Cam, _ha: float) -> void:
	var along := cam.to_scene.basis_xform(Vector2(0, 1)).normalized().dot(cam.fwd)
	var k := absf(along)
	if k < 0.05:
		return
	var L := VignetteGround.L
	var y := -L
	var n := 0
	while y < L:
		var y1 := minf(y + 12.0, L)
		var lit := (n % 2 == 1) == (along > 0.0)
		var mid := cam.local(cam.to_scene * Vector2(0.0, (y + y1) * 0.5))
		var graze := clampf((mid.y - 8.0) / 70.0, 0.25, 1.0)
		var c := Color(0.85, 1.0, 0.8, 0.07 * k * graze) if lit else Color(0.0, 0.03, 0.0, 0.06 * k * graze)
		var pts := VignetteGround._clip(cam, VignetteGround._band(y, y1))
		if pts.size() >= 3:
			ci.draw_colored_polygon(PackedVector2Array(pts), c)
		y += 12.0
		n += 1


static func _lights(ci: CanvasItem, cam: VignetteGround.Cam, a: Dictionary) -> Array:
	var out := []
	var tex := _soft_tex()
	var warm := Color(1.0, 0.94, 0.8)
	var centre := cam.oval(Vector2.ZERO, 0.0)
	for p in VignetteGround._tower_spots():
		var top := cam.oval(p, 78.0)
		if top.z <= 0.0:
			continue
		var at := Vector2(top.x, top.y)
		# A shaft of light from the bank down onto the oval, fading as it falls.
		if centre.z > 0.0:
			var foot := cam.oval((p as Vector2) * 0.35, 0.0)
			if foot.z > 0.0:
				var fp := Vector2(foot.x, foot.y)
				var side := (fp - at).orthogonal().normalized() * maxf(20.0, 26.0 * foot.z)
				ci.draw_polygon(PackedVector2Array([at, fp + side, fp - side]),
						PackedColorArray([Color(warm, a["shaft"]), Color(warm, 0.0), Color(warm, 0.0)]))
		# The glow in the air round the bank.
		var r := maxf(14.0, 34.0 * top.z) * float(a["glow_r"])
		ci.draw_texture_rect(tex, Rect2(at - Vector2(r, r), Vector2(r, r) * 2.0), false, Color(warm, a["glow"]))
		ci.draw_texture_rect(tex, Rect2(at - Vector2(r, r) * 0.3, Vector2(r, r) * 0.6), false, Color(1, 1, 0.96, 0.55))
		out.append(Vector3(at.x, at.y, r))
	return out


## Over the players, under the names and bars. lights: draw_back's, moved into screen
## space; t the scene's time.
static func draw_front(ci: CanvasItem, rect: Rect2, lights: Array, weather: String, t: float) -> void:
	if not ON:
		return
	var a := air(weather)
	var tex := _soft_tex()
	var wet := weather == VignetteWeather.WET
	for l in lights:
		var at := Vector2(l.x, l.y)
		var r: float = l.z
		if not rect.grow(r).has_point(at):
			continue
		# A horizontal glare streak across the bank, longer in the wet.
		var w := r * (4.0 if wet else 2.6)
		ci.draw_texture_rect(tex, Rect2(at - Vector2(w, r * 0.07), Vector2(w * 2.0, r * 0.14)), false,
				Color(1.0, 0.95, 0.85, 0.32 if wet else 0.24))
	# Motes drifting in the light (held still under reduced motion).
	var n: int = a["motes"]
	var drift := 0.0 if Feel.reduced else t
	var mc: Color = a["mote"]
	for i in range(n):
		var hx := fposmod(sin(float(i) * 12.9898) * 43758.5453, 1.0)
		var hy := fposmod(sin(float(i) * 78.233) * 12345.678, 1.0)
		var hs := fposmod(sin(float(i) * 3.71) * 9876.5, 1.0)
		var p := Vector2(fposmod(hx * rect.size.x + drift * (6.0 + hs * 10.0), rect.size.x),
				fposmod(hy * rect.size.y * 0.75 + rect.size.y * 0.1 - drift * (2.0 + hs * 3.0), rect.size.y * 0.85))
		ci.draw_circle(rect.position + p, 0.6 + hs * 1.0, Color(mc, 0.1 + hs * 0.16))
	# The corners fall into shadow, so the eye goes to the lit middle.
	ci.draw_texture_rect(_edge_tex(), rect, false, Color(1, 1, 1, 0.5 if wet else 0.4))
