class_name VignetteWeather
extends RefCounted
## The day's weather as the match views draw it (ARD-M4-016; MatchSim.weather: "perfect",
## "wet", "windy" or "hot"). Presentation only: the look follows the weather and changes
## nothing. Restrained: nothing here covers the ball or a name.
##   wet    darker, sheened turf (the lights in it), a cooler overcast, light rain;
##   windy  flags on the stand roofs and in the crowd streaming toward the end the
##          breeze blows to, an arrow on the big screen (director, 2026-11-12: no lines
##          drawn over the grass);
##   hot    by day: harsh light, dry yellowed turf with bleached patches, a tight dark
##          shadow under every player, a pale washed-out sky and a shimmer on the horizon.
## Anything else (perfect, unknown or none) draws as before.
## The time of day (VignetteKickoff: day, twilight or night) sets the light all of this is
## seen in; with no slot given, every function here answers for a night game, exactly as
## before there were day games.

const WET := "wet"
const WINDY := "windy"
const HOT := "hot"


## Turf under daylight: brighter and a touch warmer than under the lights.
const DAY_TURF := Color(1.42, 1.3, 1.22)
## Dry straw: what a hot day's turf leans to under lights, and by day.
const STRAW_NIGHT := Color(0.46, 0.46, 0.22)
const STRAW_DAY := Color(0.62, 0.6, 0.34)


## A turf colour as the slot's light shows it.
static func daylit(c: Color, slot: String) -> Color:
	var d := VignetteKickoff.daylight(slot)
	if d <= 0.0:
		return c
	return c.lerp(Color(minf(c.r * DAY_TURF.r, 1.0), minf(c.g * DAY_TURF.g, 1.0), minf(c.b * DAY_TURF.b, 1.0), c.a), d)


## The turf's mown colours, by weather and time of day.
static func grass(weather: String, base: Array, slot := VignetteKickoff.NIGHT) -> Array:
	var d := VignetteKickoff.daylight(slot)
	var lit := base.map(func(c: Color) -> Color: return daylit(c, slot))
	match weather:
		WET:
			# Darker and bluer; by day a little less so, the sky still lighting it.
			return lit.map(func(c: Color) -> Color:
				return Color(c.r * lerpf(0.62, 0.74, d), c.g * lerpf(0.7, 0.8, d), c.b * lerpf(0.82, 0.86, d)))
		HOT:
			return lit.map(func(c: Color) -> Color:
				return c.lerp(STRAW_NIGHT.lerp(STRAW_DAY, d), lerpf(0.42, 0.5, d)))
	return lit


## How strongly a figure's shadow falls (alpha), by weather and the time of day being
## drawn: overcast softens it, the sun firms it, a hot day's sun makes it a dark pool.
static func shadow_alpha(weather: String) -> float:
	var d := VignetteKickoff.daylight(VignetteGround.slot_now(weather))
	match weather:
		WET:
			return 0.18
		HOT:
			return lerpf(0.58, 0.72, d)
	return lerpf(0.32, 0.44, d)


## How wide a figure's shadow is against its usual size: on a hot day the sun is high and
## the shadow pulls in tight under the boots.
static func shadow_tight(weather: String) -> float:
	if weather != HOT:
		return 1.0
	return lerpf(1.0, 0.8, VignetteKickoff.daylight(VignetteGround.slot_now(weather)))


## How hard the wind pulls flags and banners: 0 calm, 1 a strong breeze.
static func wind(weather: String) -> float:
	return 1.0 if weather == WINDY else 0.0


## The haze over the far side: its colour and strength.
static func haze(weather: String, slot := VignetteKickoff.NIGHT) -> Color:
	var d := VignetteKickoff.daylight(slot)
	match weather:
		HOT:
			return Color(1.0, 0.86, 0.6, 0.32).lerp(Color(1.0, 0.95, 0.8, 0.5), d)
		WET:
			return Color(0.74, 0.8, 0.9, 0.26).lerp(Color(0.8, 0.83, 0.87, 0.34), d)
	return Color(0.85, 0.88, 1.0, 0.13).lerp(Color(0.9, 0.95, 1.0, 0.2), d)


## The sky behind the stands by weather and time of day: three colours (the top of the
## picture, part way down, the horizon). Empty at night: the night sky is one flat dark
## colour (VignetteGround.SKY).
static func sky(weather: String, slot: String) -> Array:
	match slot:
		VignetteKickoff.DAY:
			match weather:
				WET:
					return [Color(0.42, 0.46, 0.51), Color(0.55, 0.59, 0.63), Color(0.69, 0.71, 0.73)]
				HOT:
					return [Color(0.5, 0.68, 0.9), Color(0.78, 0.86, 0.93), Color(0.99, 0.96, 0.86)]
			return [Color(0.24, 0.47, 0.82), Color(0.47, 0.67, 0.9), Color(0.78, 0.88, 0.96)]
		VignetteKickoff.TWILIGHT:
			match weather:
				WET:
					return [Color(0.13, 0.15, 0.21), Color(0.25, 0.25, 0.32), Color(0.45, 0.4, 0.41)]
				HOT:
					return [Color(0.16, 0.16, 0.36), Color(0.62, 0.34, 0.4), Color(1.0, 0.62, 0.26)]
			return [Color(0.08, 0.11, 0.28), Color(0.36, 0.27, 0.45), Color(0.96, 0.56, 0.32)]
	return []


## Over the scene, under the names and the bars, at time t: wet, an overcast and rain
## falling across it (streaks thin enough that the ball and the players read through
## them). rect: the screen to cover. Under Settings > Reduced motion the rain holds still.
static func draw_air(ci: CanvasItem, rect: Rect2, t: float, weather: String) -> void:
	if weather != WET:
		return
	if Feel.reduced:
		t = 0.0
	ci.draw_rect(rect, Color(0.05, 0.08, 0.12, 0.13), true)       # overcast
	var n := int(clampf(rect.size.x * rect.size.y / 1900.0, 40.0, 420.0))
	var lean := Vector2(-0.18, 1.0).normalized()                  # it falls slanting a touch
	for i in range(n):
		var h := hash(i * 7919 + 13)
		var fx := float(h % 10007) / 10007.0
		var fy := float((h / 10007) % 10009) / 10009.0
		var speed := 0.9 + 0.5 * float((h / 7) % 97) / 97.0      # screens a second
		var streak := (18.0 + float(h % 15)) * rect.size.y / 844.0
		var y := fposmod(fy + t * speed, 1.0) * (rect.size.y + streak) - streak
		var x := fposmod(fx + 0.09 * y / rect.size.y, 1.0) * rect.size.x
		var p := rect.position + Vector2(x, y)
		var a := 0.24 + 0.16 * float((h / 3) % 7) / 7.0
		ci.draw_line(p, p + lean * streak, Color(0.86, 0.9, 0.96, a), 1.4, true)


## Which way the wind blows, oval metres: down the ground toward the +y end (the end the
## scenes attack), a little across it. wind_world turns it for the end the breeze really
## blows to.
const WIND_DIR := Vector2(0.25, 1.0)


## The wind's direction on the ground (oval metres) when the breeze blows to an end:
## +1 the +y end, -1 the other. A scene passes the end as its board's "wind".
static func wind_world(end: int) -> Vector2:
	return Vector2(WIND_DIR.x, WIND_DIR.y * (-1.0 if end < 0 else 1.0)).normalized()


## The end the breeze blows to, from a scene's board ({"wind": +1 or -1}); +1 when the
## scene does not say.
static func wind_end(board: Dictionary) -> int:
	return -1 if int(board.get("wind", 1)) < 0 else 1


## How a flag at oval point p, h metres up, streams on screen in a wind blowing along
## world (oval metres): x and y the direction on screen (a unit vector) and z how much of
## its length shows (1 side on, less as the wind blows along the line of sight).
static func flag_stream(cam: VignetteGround.Cam, p: Vector2, h: float, world: Vector2) -> Vector3:
	var a := cam.oval(p, h)
	var b := cam.oval(p + world * 3.0, h)
	if a.z <= 0.0 or b.z <= 0.0:
		return Vector3(1.0, 0.0, 1.0)
	var d := Vector2(b.x - a.x, b.y - a.y)
	var seen := d.length()
	if seen < 0.001:
		return Vector3(1.0, 0.0, 0.3)
	return Vector3(d.x / seen, d.y / seen, clampf(seen / (3.0 * a.z), 0.3, 1.0))


## Wind lines on the flat pitch view. No longer part of the look (director, 2026-11-12:
## the wind shows in flags, the scoreboard arrow and the ball's drift, never as lines on
## the grass); kept only until the pitch view stops calling it.
static func draw_wind_flat(ci: CanvasItem, rect: Rect2, t: float) -> void:
	for i in range(14):
		var h := hash(i * 3313 + 7)
		var fy := 0.1 + 0.8 * float(h % 997) / 997.0
		var speed := 0.16 + 0.08 * float((h / 997) % 89) / 89.0        # views a second
		var length := (0.12 + 0.08 * float(h % 7) / 7.0) * rect.size.x
		var x0 := fposmod(float((h / 5) % 991) / 991.0 + t * speed, 1.3) - 0.15
		var pts := PackedVector2Array()
		var cols := PackedColorArray()
		for k in range(13):
			var u := float(k) / 12.0
			pts.append(rect.position + Vector2(x0 * rect.size.x + u * length,
					fy * rect.size.y + sin(u * 3.0 + t * 2.0 + float(i)) * 3.0))
			cols.append(Color(0.92, 0.95, 1.0, 0.3 * sin(u * PI)))
		ci.draw_polyline_colors(pts, cols, 1.2, true)


## Wet turf holds the lights: for each light tower in view, a soft pool of glare on the
## grass between the camera and the tower, where light off a wet surface comes back to the
## eye. A low-contrast patch lying flat on the ground (an ellipse in oval metres, seen in
## perspective), brightest in the middle and fading to nothing at its edge: no streaks and
## no edge, so it never reads as a beam, an object or a hole. Drawn with the ground, under
## the players.
const GLARE := Color(0.84, 0.9, 1.0)
const GLARE_ALPHA := 0.14
## How far from the camera toward the tower the pool lies (0 at the camera, 1 at the
## boundary), and its size: across the line of sight a share of that distance, and
## longer along it.
const GLARE_AT := 0.35
const GLARE_ACROSS := 0.2
const GLARE_ALONG := 1.5

static func draw_sheen(ci: CanvasItem, cam: VignetteGround.Cam, towers: Array, a_axis: float, l_axis: float) -> void:
	var to_oval := cam.to_scene.affine_inverse()
	var eye: Vector2 = to_oval * cam.pos
	var points := PackedVector2Array()
	var colors := PackedColorArray()
	var indices := PackedInt32Array()
	var rings := [[0.0, 1.0], [0.4, 0.62], [0.75, 0.22], [1.0, 0.0]]     # radius share, brightness
	var seg := 32
	for p in towers:
		var tower: Vector2 = p
		# Only towers in front of the camera, roughly within its view.
		var seen := cam.local(cam.to_scene * tower)
		if seen.y <= 0.0 or absf(seen.x) > seen.y * 1.2:
			continue
		# The boundary on the way to the tower, and the pool part way out to it.
		var dir := tower.normalized()
		var edge := Vector2(dir.x * a_axis, dir.y * l_axis)
		var reach := edge - eye
		var dist := reach.length()
		if dist < 8.0:
			continue
		var along := reach / dist
		var across := Vector2(-along.y, along.x)
		var centre := eye + reach * GLARE_AT
		var r_across := clampf(dist * GLARE_ACROSS, 5.0, 16.0)
		var r_along := r_across * GLARE_ALONG
		var ok := true
		var base := points.size()
		for ring in rings:
			var share: float = ring[0]
			var c := Color(GLARE, GLARE_ALPHA * float(ring[1]))
			var n := 1 if share == 0.0 else seg
			for k in range(n):
				var ang := TAU * float(k) / float(seg)
				var at := centre + (along * cos(ang) * r_along + across * sin(ang) * r_across) * share
				var sp := cam.oval(at, 0.0)
				if sp.z <= 0.0:
					ok = false
					break
				points.append(Vector2(sp.x, sp.y))
				colors.append(c)
			if not ok:
				break
		if not ok:
			points.resize(base)
			colors.resize(base)
			continue
		# The middle fans out to the first ring; each ring joins the next.
		for k in range(seg):
			indices.append_array([base, base + 1 + k, base + 1 + (k + 1) % seg])
		for r in range(1, rings.size() - 1):
			var inner := base + 1 + (r - 1) * seg
			var outer := inner + seg
			for k in range(seg):
				var k2 := (k + 1) % seg
				indices.append_array([inner + k, outer + k, outer + k2, inner + k, outer + k2, inner + k2])
	if not indices.is_empty():
		RenderingServer.canvas_item_add_triangle_array(ci.get_canvas_item(), indices, points, colors)


## A flag on a pole in a club's colours (the top half colour, the bottom half second),
## streaming with the wind at time t: pole foot at foot, pole height pole_h px, flag w x h
## px, phase so a crowd's flags don't wave as one. wind_strength 0 hangs it, 1 streams it.
## stream: which way it streams on screen and how much of its length shows (flag_stream);
## left out, straight to the right at full length.
static func draw_flag(ci: CanvasItem, foot: Vector2, pole_h: float, w: float, h: float, colour: Color,
		t: float, phase: float, wind_strength: float, second := Color(1, 1, 1),
		stream := Vector3(1.0, 0.0, 1.0)) -> void:
	var dir := Vector2(stream.x, stream.y)
	var top := foot - Vector2(0, pole_h)
	ci.draw_line(foot, top, Color(0.8, 0.8, 0.82), maxf(1.0, w * 0.045), true)
	var steps := 12
	var upper := []
	var middle := []
	var lower := []
	for i in range(steps + 1):
		var u := float(i) / steps
		# A wave runs out from the pole; the free end flicks most.
		var ripple := sin(u * 7.0 - t * 12.0 + phase) * h * 0.18 * u * wind_strength
		var droop := (1.0 - wind_strength) * u * h * 0.9
		var out := dir * (u * w * stream.z * lerpf(0.35, 1.0, wind_strength) * (1.0 - 0.06 * sin(t * 7.0 + phase) * u))
		var x := top.x + out.x
		var y := top.y + out.y + ripple + droop
		upper.append(Vector2(x, y + u * h * 0.06))
		middle.append(Vector2(x, y + h * 0.5))
		lower.append(Vector2(x, y + h - u * h * 0.06 - droop * 0.6))
	_strip(ci, upper, middle, colour)
	_strip(ci, middle, lower, second)
	var outline := PackedVector2Array()
	for p in upper:
		outline.append(p)
	for i in range(steps, -1, -1):
		outline.append(lower[i])
	outline.append(upper[0])
	ci.draw_polyline(outline, Color(0, 0, 0, 0.35), 1.0, true)      # a soft edge, not stair-steps


static func _strip(ci: CanvasItem, a: Array, b: Array, colour: Color) -> void:
	var poly := PackedVector2Array()
	for p in a:
		poly.append(p)
	for i in range(b.size() - 1, -1, -1):
		poly.append(b[i])
	ci.draw_colored_polygon(poly, colour)
