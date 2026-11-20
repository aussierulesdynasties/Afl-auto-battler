class_name Oval3DTurf
extends Node
## The 3D oval's turf and light for the day (row 197): the weather and the time of day set
## the grass shader (oval3d_ground.gdshader), the sun or the tower lights, the ambient and the
## sky; and a wear map follows where play goes, thin grass on a dry day, mud in the wet.
## Looks only (rule 1.29): it reads the players' positions and never writes to the match.
## The colours come from VignetteWeather, the same ones the vignettes and the flat oval use,
## so a wet night looks like the same wet night in every view.

## The wear map: one texel about 1.5 m, covering the ground plane (Oval3D._ground).
const WEAR_W := 128
const WEAR_H := 102
## Per second a player stands on a texel: how much it thins, and how much it churns.
const THIN_RATE := 0.0035
const CHURN_RATE := 0.006
const UPLOAD_EVERY := 0.25    # s between texture uploads
## The blade tile, its normals and the patch noise (tools/oval3d/make_turf_textures.py).
const BLADES := preload("res://assets/oval3d/turf/blades.png")
const BLADES_N := preload("res://assets/oval3d/turf/blades_n.png")
const PATCHES := preload("res://assets/oval3d/turf/patches.png")

var oval: Node3D
var mat: ShaderMaterial
var env: Environment
var sun: DirectionalLight3D
var fill: DirectionalLight3D
var weather := ""
var slot := VignetteKickoff.DAY
var _wear: Image
# The wear itself, in floats: a frame's scuff (about 0.00004) is far below one step of the
# 8-bit map (1/255) and would round away, so it builds up here and the map shows it.
var _thin := PackedFloat32Array()
var _churn := PackedFloat32Array()
var _tex: ImageTexture
var _half := Vector2.ONE
var _last: Dictionary = {}    # node id -> last ground position
var _since := 0.0
## Standing blades round the ball (oval3d_blades.gdshader), drawn only when the camera is near.
const BLADE_COUNT := 36000
const BLADE_SPAN := 16.0      # m: the square of standing blades round the ball
const BLADE_NEAR := 32.0      # m: farther than this from the ball the camera can't see a blade
var blades: MultiMeshInstance3D
var _bmat: ShaderMaterial
var _clouds: NoiseTexture2D
var _shade := false
var _exposure := 1.0
const SKY_SHADER := preload("res://scripts/ui/match/oval3d_sky.gdshader")


func _init(p_oval: Node3D, p_mat: ShaderMaterial, p_env: Environment, p_sun: DirectionalLight3D, half: Vector2) -> void:
	oval = p_oval
	mat = p_mat
	env = p_env
	sun = p_sun
	_half = half
	fill = DirectionalLight3D.new()
	fill.shadow_enabled = false
	fill.visible = false
	tower = DirectionalLight3D.new()
	tower.shadow_enabled = false
	tower.visible = false
	_wear = Image.create(WEAR_W, WEAR_H, false, Image.FORMAT_RGBA8)
	_thin.resize(WEAR_W * WEAR_H)
	_churn.resize(WEAR_W * WEAR_H)
	_seed_wear()
	_tex = ImageTexture.create_from_image(_wear)
	mat.set_shader_parameter("wear_map", _tex)
	mat.set_shader_parameter("wear_half", _half)
	mat.set_shader_parameter("blades_tex", BLADES)
	mat.set_shader_parameter("blades_n", BLADES_N)
	mat.set_shader_parameter("patches_tex", PATCHES)


func _ready() -> void:
	oval.add_child(fill)
	oval.add_child(tower)
	_make_blades()


## One thin triangle a blade, 7 cm tall and a little over a centimetre wide at the base
## (wider than a real blade so it never thins below a pixel and shimmers), scattered at random.
func _make_blades() -> void:
	var tri := ArrayMesh.new()
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(-0.006, 0, 0), Vector3(0.006, 0, 0), Vector3(0.001, 0.07, 0)])
	arr[Mesh.ARRAY_NORMAL] = PackedVector3Array([Vector3(0, 0, 1), Vector3(0, 0, 1), Vector3(0, 0, 1)])
	tri.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = tri
	mm.instance_count = BLADE_COUNT
	var rng := RandomNumberGenerator.new()
	rng.seed = 1115
	for i in range(BLADE_COUNT):
		mm.set_instance_transform(i, Transform3D.IDENTITY)
		mm.set_instance_custom_data(i, Color(rng.randf_range(-0.5, 0.5) * BLADE_SPAN,
				rng.randf_range(-0.5, 0.5) * BLADE_SPAN, rng.randf(), 0.0))
	# Big enough a box that the square is never culled wherever it has wrapped to.
	mm.custom_aabb = AABB(Vector3(-100, -1, -80), Vector3(200, 2, 160))
	blades = MultiMeshInstance3D.new()
	blades.multimesh = mm
	blades.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_bmat = ShaderMaterial.new()
	_bmat.shader = preload("res://scripts/ui/match/oval3d_blades.gdshader")
	_bmat.set_shader_parameter("span", BLADE_SPAN)
	_bmat.set_shader_parameter("half_size", Vector2(MatchMotion.HALF_LEN, MatchMotion.HALF_WID))
	blades.material_override = _bmat
	oval.add_child(blades)
	_copy_look()


## The standing blades take the turf's colours and weather.
func _copy_look() -> void:
	if _bmat == null:
		return
	for k in ["grass_a", "grass_b", "wet", "hot", "wind", "wind_dir"]:
		_bmat.set_shader_parameter(k, mat.get_shader_parameter(k))


## The day's look: weather "perfect", "wet", "windy" or "hot" (anything else is perfect);
## slot day, twilight or night (VignetteKickoff).
func apply(p_weather: String, p_slot: String) -> void:
	weather = p_weather
	slot = p_slot if p_slot in VignetteKickoff.SLOTS else VignetteKickoff.NIGHT
	var wet := weather == VignetteWeather.WET
	var hot := weather == VignetteWeather.HOT
	var d := VignetteKickoff.daylight(slot)
	var g: Array = VignetteWeather.grass(weather, VignetteGround.GRASS, slot)
	if wet:
		# The flat views darken wet turf to show the wet; here the sheen shows it, so the
		# colour goes half as dark (fully, the lit ground reads near black).
		# The flat views' wet palette turns blue-grey under lights; soaked turf is the same
		# green, darker. So the dry colour, a shade darker and greyer (measured: without the grey, soaked turf under
		# lights goes neon once the sheen is kept to the puddles).
		var dry: Array = VignetteWeather.grass("", VignetteGround.GRASS, slot)
		var grey := 0.2 if slot == VignetteKickoff.DAY else 0.3
		g = dry.map(func(c: Color) -> Color:
			var l := c.get_luminance()
			return c.lerp(Color(l, l, l), grey) * 0.95)
	mat.set_shader_parameter("grass_a", g[0])
	mat.set_shader_parameter("grass_b", g[1])
	var apron: Color = VignetteWeather.grass(weather, [VignetteGround.APRON], slot)[0]
	mat.set_shader_parameter("apron_col", apron)
	var worn: Color = VignetteGround.WORN[1]
	mat.set_shader_parameter("worn_col", VignetteWeather.daylit(Color(worn.r, worn.g, worn.b), slot))
	mat.set_shader_parameter("wet", 1.0 if wet else 0.0)
	mat.set_shader_parameter("hot", 1.0 if hot else 0.0)
	mat.set_shader_parameter("wind", VignetteWeather.wind(weather))
	mat.set_shader_parameter("wind_dir", Vector2(1.0, 0.25).normalized())
	# Under lights the stripes stand out more than in flat daylight.
	mat.set_shader_parameter("stripe_amount", lerpf(0.24, 0.16, d))

	# A hot day's ground is still a watered AFL ground: the fine day's green with some dried
	# patches (the full straw look goes lime under the TV tone, rule 2.81; approved hot sky, 2.84).
	if hot:
		g = VignetteWeather.grass("", VignetteGround.GRASS, slot)
		mat.set_shader_parameter("grass_a", g[0])
		mat.set_shader_parameter("grass_b", g[1])
		mat.set_shader_parameter("hot", 0.4)
	_copy_look()

	# Rule 2.81, the TV broadcast tone: AgX with a footy-TV grade (contrast up a tenth, colour up
	# a fifth), for every match.
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.adjustment_enabled = true
	env.adjustment_contrast = 1.1
	env.adjustment_saturation = 1.2
	env.adjustment_color_correction = null
	sun.shadow_enabled = true
	sun.light_angular_distance = 0.0
	sun.directional_shadow_max_distance = 160.0
	_stand_shade(false)
	if slot == VignetteKickoff.NIGHT:
		_night(wet)
	else:
		fill.visible = false
		_sky_light(hot)
		if slot == VignetteKickoff.TWILIGHT:
			_late_game()
		if wet:
			_cloud_light()
	# The exposure, set by the brightness of open grass (rule 2.81): each look's grass near a fine
	# day's, as a broadcast camera opens up in poorer light.
	var exposure: float = EXPOSURE[slot]
	if wet:
		exposure *= EXPOSURE_WET[slot]
	env.tonemap_exposure = exposure
	_exposure = exposure
	_sky_view()
	_tone_to_film()


## The match film (Oval3D._film) applies the tone itself, after its own look, so the club rings
## drawn after it keep their exact club colour whatever the tone and exposure (rule 2.81). The
## environment hands the film its AgX, exposure and grade, and passes the picture through as it is.
var film: ShaderMaterial:
	set(v):
		film = v
		_tone_to_film()


func _tone_to_film() -> void:
	if film == null or env.tonemap_mode != Environment.TONE_MAPPER_AGX:
		return
	# Godot's own AgX curve settings (environment_storage.cpp, 4.7): white 2.0 on the Mobile renderer.
	var c: float = env.tonemap_agx_contrast
	const X := 0.18
	const WHITE := 2.0
	var toe := (1.0 / X - 1.0) * pow(X, c)
	var den := pow(X, c) + toe
	var slope := c * pow(X, c - 1.0) * toe / (den * den)
	var w := (WHITE - X) * (WHITE - X) / (1.0 - X) * slope
	film.set_shader_parameter("tone", true)
	film.set_shader_parameter("exposure", env.tonemap_exposure)
	film.set_shader_parameter("awp", Vector4(c, toe, slope, w))
	var adj := env.adjustment_enabled
	film.set_shader_parameter("grade", Vector3(env.adjustment_brightness if adj else 1.0,
			env.adjustment_contrast if adj else 1.0, env.adjustment_saturation if adj else 1.0))
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.tonemap_exposure = 1.0
	env.adjustment_enabled = false


## AgX exposure for each time of day, and the factor a wet day adds (measured with
## tools/visual/capture_turf3d.gd: open grass in each look against the fine day's).
const EXPOSURE := {"day": 1.0, "twilight": 2.81, "night": 1.91}
const EXPOSURE_WET := {"day": 1.83, "twilight": 1.83, "night": 1.84}


## Night: the towers, high and cool white from behind the far wing, a weaker set from the other
## side, under one dark sky colour (rule 2.80's sky light is the daylight).
func _night(wet: bool) -> void:
	env.sky = null
	env.background_mode = Environment.BG_COLOR
	var sky: Array = VignetteWeather.sky(weather, slot)
	env.background_color = sky[1] if sky.size() > 1 else VignetteGround.SKY
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	# The backdrop is one flat colour, not a sky: mirrored in the turf at a low angle it
	# lays a grey film over the grass. The wet sheen comes from the lights instead.
	env.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
	sun.rotation_degrees = Vector3(-58.0, 150.0, 0.0)
	sun.light_color = Color(0.97, 1.0, 0.97)
	sun.light_energy = 1.6
	fill.visible = true
	fill.rotation_degrees = Vector3(-58.0, -30.0, 0.0)
	fill.light_color = Color(0.92, 0.95, 1.0)
	fill.light_energy = 0.5
	env.ambient_light_color = Color(0.4, 0.46, 0.4)
	env.ambient_light_energy = 0.35
	if wet:
		sun.light_energy *= 0.85
		sun.light_color = sun.light_color.lerp(Color(0.85, 0.9, 1.0), 0.5)
		env.ambient_light_energy *= 1.1


## Rule 2.80, sky light: the sky lights the ground and the men (ambient and reflections from it),
## the grass bounces light up and the stands round the ground darken the sides. Rule 2.84: the
## sky you see for the weather. Values copied from the approved prototype (capture_look3d.gd).
func _sky_light(hot: bool) -> void:
	var sm := ShaderMaterial.new()
	sm.shader = SKY_SHADER
	sm.set_shader_parameter("clouds_tex", _cloud_noise())
	var sky := Sky.new()
	sky.sky_material = sm
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	env.sky = sky
	env.background_mode = Environment.BG_SKY
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_sky_contribution = 1.0
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	if hot:
		# The sun high and hard, the sky pale with glare, cloudless.
		sun.rotation_degrees = Vector3(-68.0, -35.0, 0.0)
		sm.set_shader_parameter("energy", 1.2)
		sm.set_shader_parameter("zenith", Color(0.35, 0.55, 0.85))
		sm.set_shader_parameter("horizon", Color(0.82, 0.86, 0.9))
		sun.light_energy = 1.6
		sun.light_color = Color(1.0, 0.96, 0.88)
		_sky_look({"cover": 0.06, "sun_halo": 1.2, "target": 0.7, "seen_horizon": Color(0.66, 0.78, 0.92, 1.0),
				"seen_zenith": Color(0.2, 0.42, 0.82, 1.0), "sky_curve": 0.45})
	else:
		# A fine winter's day: blue, a few fair-weather clouds, the sun's glare round it.
		sun.rotation_degrees = Vector3(-52.0, -35.0, 0.0)
		sm.set_shader_parameter("energy", 1.4)
		sun.light_energy = 1.15
		sun.light_color = Color(1.0, 0.95, 0.86)
		_sky_look({"cover": 0.32, "cloud_lit": Color(1.0, 1.0, 1.0), "cloud_dark": Color(0.62, 0.66, 0.74),
				"sun_halo": 0.35})


## Rule 2.80's late game ("C late games"): the sun 22 degrees up behind the near stand (about
## 4.30 pm in winter), so the stand's top, 24 m up and 34 m back from the fence, shades about 25 m
## of the near wing; the clouds warm on the sun's side (the approved late-game sky, rule 2.84).
func _late_game() -> void:
	var sm: ShaderMaterial = env.sky.sky_material
	sun.light_energy = 1.2
	var e := deg_to_rad(22.0)
	var h := Vector3(0.3, 0.0, -1.0).normalized()
	sun.global_basis = Basis.looking_at(h * cos(e) + Vector3(0.0, -sin(e), 0.0), Vector3.UP)
	sun.light_color = Color(1.0, 0.9, 0.76)
	sun.directional_shadow_max_distance = 320.0
	_stand_shade(true)
	_sky_look({"cover": 0.4, "cloud_lit": Color(1.0, 0.93, 0.82), "cloud_dark": Color(0.56, 0.57, 0.64), "sun_halo": 0.55,
			"cloud_sun": 0.8, "target": 0.8})


## A wet day (rule 2.83): the sky is cloud, grey light from all round, the sun only a soft
## brightness from above, so a man's shadow is a faint pool at his feet.
func _cloud_light() -> void:
	var sm: ShaderMaterial = env.sky.sky_material
	sm.set_shader_parameter("energy", 1.4)
	sm.set_shader_parameter("zenith", Color(0.55, 0.57, 0.6))
	sm.set_shader_parameter("horizon", Color(0.66, 0.67, 0.69))
	sm.set_shader_parameter("bowl", Color(0.16, 0.16, 0.17))
	sm.set_shader_parameter("grass", Color(0.14, 0.2, 0.1))
	sm.set_shader_parameter("glow_energy", 0.0)
	sm.set_shader_parameter("stars", 0.0)
	sun.light_energy = 0.45
	sun.light_color = Color(0.95, 0.97, 1.0)
	sun.light_angular_distance = 12.0
	sun.global_basis = Basis.looking_at(Vector3(0.2, -1.0, 0.35).normalized(), Vector3.UP)
	sun.directional_shadow_max_distance = 160.0
	_stand_shade(false)
	env.adjustment_color_correction = null
	_sky_look({"cover": 1.0, "cloud_size": 1.6, "cloud_lit": Color(0.64, 0.66, 0.69), "cloud_dark": Color(0.4, 0.42, 0.45),
			"cloud_sun": 0.15, "target": 0.5})


func _sky_look(p: Dictionary) -> void:
	var sm: ShaderMaterial = env.sky.sky_material
	for k in p:
		if k == "target":
			sm.set_meta("target", p[k])
		else:
			sm.set_shader_parameter(k, p[k])


## The seen sky set for the exposure: its horizon at the look's "target" brightness on screen (a
## sunset sky is far brighter than the grass the exposure is set for, and would blow out white).
## A look without a target keeps the sky's own brightness.
func _sky_view() -> void:
	if env.sky == null:
		return
	var sm: ShaderMaterial = env.sky.sky_material
	if not sm.has_meta("target"):
		return
	var hzv = sm.get_shader_parameter("seen_horizon")
	if hzv == null or hzv.a == 0.0:
		hzv = sm.get_shader_parameter("horizon")
	if hzv == null:
		hzv = RenderingServer.shader_get_parameter_default(SKY_SHADER.get_rid(), "horizon")
	if hzv == null:
		return # headless (tests): no renderer to give the shader's default
	var hz: Color = hzv
	var lum := 0.2126 * hz.r + 0.7152 * hz.g + 0.0722 * hz.b
	sm.set_shader_parameter("view", float(sm.get_meta("target"))
			/ (env.tonemap_exposure * float(sm.get_shader_parameter("energy")) * lum))


## The stands cast their shade across the ground (a late game, rule 2.80).
func _stand_shade(on: bool) -> void:
	_shade = on
	for c in oval.get_children():
		if c is MeshInstance3D and c.material_override is ShaderMaterial \
				and str(c.material_override.shader.resource_path).ends_with("oval3d_crowd.gdshader"):
			c.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED if on \
					else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


## Seamless cloud noise for the sky, made once.
func _cloud_noise() -> NoiseTexture2D:
	if _clouds != null:
		return _clouds
	var fn := FastNoiseLite.new()
	fn.noise_type = FastNoiseLite.TYPE_PERLIN
	fn.fractal_type = FastNoiseLite.FRACTAL_FBM
	fn.fractal_octaves = 5
	fn.frequency = 0.008
	fn.seed = 7
	_clouds = NoiseTexture2D.new()
	_clouds.width = 512
	_clouds.height = 512
	_clouds.seamless = true
	_clouds.generate_mipmaps = true
	_clouds.noise = fn
	return _clouds


func _process(dt: float) -> void:
	_since += dt
	_follow_blades()
	var moved := false
	for group in [oval.get("players"), oval.get("umpires")]:
		if group == null:
			continue
		for p in group:
			var node: Node3D = p["node"]
			if node == null or not node.visible:
				continue
			var at := Vector2(node.position.x, node.position.z)
			var id := node.get_instance_id()
			var was: Vector2 = _last.get(id, at)
			_last[id] = at
			# Standing still wears little; running and turning wear more.
			var speed := minf(at.distance_to(was) / maxf(dt, 1e-3), 9.0)
			if _scuff(at, dt * (0.35 + speed / 6.0)):
				moved = true
	if moved and _since >= UPLOAD_EVERY:
		_since = 0.0
		_tex.update(_wear)


## The standing blades follow the ball, flattened round every boot and the ball itself;
## hidden when the camera is too far off to see one.
func _follow_blades() -> void:
	if blades == null:
		return
	var ball: Node3D = oval.get("ball")
	var cam: Camera3D = oval.get("camera")
	if ball == null or cam == null:
		return
	var c := Vector2(ball.position.x, ball.position.z)
	var cam_local := oval.to_local(cam.global_position)
	blades.visible = cam_local.distance_to(Vector3(c.x, 0.0, c.y)) < BLADE_NEAR
	if not blades.visible:
		return
	_bmat.set_shader_parameter("centre", c)
	var push := []
	for group in [oval.get("players"), oval.get("umpires")]:
		if group == null:
			continue
		for p in group:
			var node: Node3D = p["node"]
			if node != null and node.visible and push.size() < 47:
				var at := Vector2(node.position.x, node.position.z)
				if at.distance_to(c) < BLADE_SPAN:
					push.append(Vector3(at.x, at.y, 0.45))
	if ball.position.y < 0.4:
		push.append(Vector3(ball.position.x, ball.position.z, 0.25))
	var count := push.size()
	while push.size() < 48:
		push.append(Vector3(9999, 9999, 0))
	_bmat.set_shader_parameter("pushers", PackedVector3Array(push))
	_bmat.set_shader_parameter("pusher_count", count)


## Wear one spot by `amount` seconds of a player's boots. False off the map.
func _scuff(at: Vector2, amount: float) -> bool:
	var tx := (at.x / (2.0 * _half.x) + 0.5) * WEAR_W
	var ty := (at.y / (2.0 * _half.y) + 0.5) * WEAR_H
	var cx := int(tx)
	var cy := int(ty)
	if cx < 1 or cy < 1 or cx >= WEAR_W - 1 or cy >= WEAR_H - 1:
		return false
	for oy in [-1, 0, 1]:
		for ox in [-1, 0, 1]:
			var k := 1.0 if ox == 0 and oy == 0 else 0.35
			var i: int = (cy + oy) * WEAR_W + cx + ox
			_thin[i] = minf(_thin[i] + THIN_RATE * amount * k, 0.85)
			_churn[i] = minf(_churn[i] + CHURN_RATE * amount * k, 1.0)
			_wear.set_pixel(cx + ox, cy + oy, Color(_thin[i], _churn[i], 0.0, 1.0))
	return true


## A mid-season ground before the bounce: the centre circle and the goal squares worn
## from weeks of ball-ups and kick-ins, a lighter wear down the corridor.
func _seed_wear() -> void:
	for y in range(WEAR_H):
		for x in range(WEAR_W):
			var p := Vector2((float(x) + 0.5) / WEAR_W - 0.5, (float(y) + 0.5) / WEAR_H - 0.5) * 2.0 * _half
			var thin := 0.0
			var churn := 0.0
			# The centre circle: ruck contests every week.
			var r := p.length()
			thin = maxf(thin, 0.55 * (1.0 - smoothstep(4.0, 11.0, r)))
			churn = maxf(churn, 0.6 * (1.0 - smoothstep(1.5, 5.5, r)))
			# The goal squares and just out from them: kick-ins and packs.
			for s in [-1.0, 1.0]:
				var q := Vector2(p.x - s * (MatchMotion.GOAL_X - 6.0), p.y)
				var gd := Vector2(q.x / 1.6, q.y).length()
				thin = maxf(thin, 0.6 * (1.0 - smoothstep(3.0, 12.0, gd)))
				churn = maxf(churn, 0.6 * (1.0 - smoothstep(1.0, 5.0, gd)))
			# The corridor: a faint thinning straight down the middle.
			thin = maxf(thin, 0.18 * (1.0 - smoothstep(6.0, 18.0, absf(p.y))) * (1.0 - smoothstep(60.0, 80.0, absf(p.x))))
			_thin[y * WEAR_W + x] = thin
			_churn[y * WEAR_W + x] = churn
			_wear.set_pixel(x, y, Color(thin, churn, 0.0, 1.0))


# ---------------------------------------------------------------------------
## The match clock's light (plan 2a.4, one setting for the sky, light and turf): the approved
## looks of rules 2.80 to 2.84 stay as they are, and the real sun over the ground (Oval3DSunClock,
## Sky3D's astronomy) says which of them the ground is in and how high the sun stands. Between two
## looks the picture blends from one to the other: a day game in winter slides into the late
## game's low sun, a twilight game into the towers' light once the sun has set.

## The sun's height, in degrees, where each look holds and where the blends run.
const DAY_FROM := 20.0       # at or above: the day look
const LATE_FROM := 12.0      # day -> late game between the two
const LATE_TO := 2.0         # the late game down to here
const NIGHT_FROM := -6.0     # late game -> night, done at civil dusk
## The sun is never drawn lower than this (a lower sun's shadows run off the ground) nor
## higher than this (the stands' rim and a phone's picture both read worse straight down).
const SUN_LOW := 4.0
const SUN_HIGH := 70.0
## The ambient brightness the 3D view starts with (Oval3D._environment), the day looks' own.
const DAY_AMBIENT := 0.4

var clock: Oval3DSunClock
## The second light while the towers come on as the sun goes (the night look uses `sun` for the
## main towers): it carries whichever of the two is weaker, without a shadow.
var tower: DirectionalLight3D
var hour := -100.0
var _looks := {}
var _live_sky: Sky
var _live_mat: ShaderMaterial

const TURF_KEYS := ["grass_a", "grass_b", "apron_col", "worn_col", "stripe_amount", "hot"]
const ENV_KEYS := ["background_mode", "background_color", "ambient_light_source", "ambient_light_color",
		"ambient_light_energy", "ambient_light_sky_contribution", "reflected_light_source"]
const SKY_COLOURS := ["zenith", "horizon", "seen_zenith", "seen_horizon", "cloud_lit", "cloud_dark",
		"bowl", "grass", "glow", "rim"]


## Follow the match's own sun from its kick-off: the weather's day, late-game and night looks are
## set up once, and set_hour blends between them.
func follow(p_weather: String, p_clock: Oval3DSunClock) -> void:
	clock = p_clock
	_looks.clear()
	for s in VignetteKickoff.SLOTS:
		if s == VignetteKickoff.NIGHT and p_weather == VignetteWeather.HOT:
			continue
		if s != VignetteKickoff.NIGHT:
			env.ambient_light_energy = DAY_AMBIENT
		apply(p_weather, s)
		_looks[s] = _snap()
		_looks[s]["slot"] = s
	hour = -100.0
	set_hour(clock.kickoff)


## The look at a local hour on the ground's clock. A change under a minute is let go: the light
## moves slower than that, and the sky's light map is only redrawn when it moves.
func set_hour(h: float) -> void:
	if clock == null or absf(h - hour) < 1.0 / 60.0:
		return
	hour = h
	var alt := clock.sun_altitude(h)
	var w := look_weights(alt, not _looks.has(VignetteKickoff.NIGHT))
	_write(_looks[w[0]], _looks[w[1]], float(w[2]), alt)


## Which looks the sun's height falls between, and how far from the first to the second:
## [from, to, t]. A hot day is never drawn at night.
static func look_weights(alt: float, no_night := false) -> Array:
	var D := VignetteKickoff.DAY
	var T := VignetteKickoff.TWILIGHT
	var N := VignetteKickoff.NIGHT
	if alt >= DAY_FROM:
		return [D, D, 0.0]
	if alt > LATE_FROM:
		return [D, T, smoothstep(DAY_FROM, LATE_FROM, alt)]
	if alt >= LATE_TO or no_night:
		return [T, T, 0.0]
	if alt > NIGHT_FROM:
		return [T, N, smoothstep(LATE_TO, NIGHT_FROM, alt)]
	return [N, N, 0.0]


## What one look sets, read back after apply().
func _snap() -> Dictionary:
	var s := {"turf": {}, "env": {}, "shade": _shade, "exposure": _exposure,
			"sun": _light(sun), "fill": _light(fill), "fill_on": fill.visible}
	for k in TURF_KEYS:
		s["turf"][k] = mat.get_shader_parameter(k)
	for k in ENV_KEYS:
		s["env"][k] = env.get(k)
	s["sky"] = _sky_params() if env.sky != null else {}
	return s


func _light(l: DirectionalLight3D) -> Dictionary:
	return {"basis": l.basis, "color": l.light_color, "energy": l.light_energy,
			"size": l.light_angular_distance, "reach": l.directional_shadow_max_distance}


## Every uniform of the sky as it stands, the unset ones at the shader's default; the seen sky's
## colours filled in from the light's where the look leaves them to it.
func _sky_params() -> Dictionary:
	var sm: ShaderMaterial = env.sky.sky_material
	var out := {}
	for u in SKY_SHADER.get_shader_uniform_list():
		var k := str(u["name"])
		var v = sm.get_shader_parameter(k)
		if v == null:
			v = RenderingServer.shader_get_parameter_default(SKY_SHADER.get_rid(), k)
		if v != null:
			out[k] = v
	for pair in [["seen_zenith", "zenith"], ["seen_horizon", "horizon"]]:
		var seen = out.get(pair[0])
		if (seen == null or (seen is Color and seen.a == 0.0)) and out.get(pair[1]) is Color:
			out[pair[0]] = Color(out[pair[1]], 1.0)
	return out


## The sky going dark into the night look's flat backdrop: every colour to the backdrop's, the
## sun's halo and glow out, at the brightness the backdrop is drawn at.
static func _nightfall(p: Dictionary, bg: Color) -> Dictionary:
	var out := p.duplicate()
	for k in SKY_COLOURS:
		if out.has(k):
			out[k] = Color(bg, 1.0)
	for k in ["sun_halo", "glow_energy", "disc", "cloud_sun", "stars", "rim_energy"]:
		if out.has(k):
			out[k] = 0.0
	out["energy"] = 1.0
	out["view"] = 1.0
	return out


static func _mix(a, b, t: float):
	if a == null:
		return b
	if b == null:
		return a
	if (a is float or a is int) and (b is float or b is int):
		return lerpf(float(a), float(b), t)
	if a is Color and b is Color:
		return a.lerp(b, t)
	if a is Vector2 and b is Vector2:
		return a.lerp(b, t)
	if a is Vector3 and b is Vector3:
		return a.lerp(b, t)
	return a if t < 0.5 else b


static func _mix_all(a: Dictionary, b: Dictionary, t: float) -> Dictionary:
	var out := {}
	for k in a:
		out[k] = _mix(a[k], b.get(k), t)
	for k in b:
		if not out.has(k):
			out[k] = b[k]
	return out


## Draw the blend of look a into look b, t of the way, with the sun at alt degrees.
func _write(a: Dictionary, b: Dictionary, t: float, alt: float) -> void:
	var night_b := (b["sky"] as Dictionary).is_empty()
	if night_b and t >= 0.999:
		a = b
		t = 0.0
	var night := (a["sky"] as Dictionary).is_empty()
	var turf := _mix_all(a["turf"], b["turf"], t)
	for k in turf:
		mat.set_shader_parameter(k, turf[k])
	_copy_look()
	_stand_shade(a["shade"] if t < 0.5 else b["shade"])
	var exposure: float = lerpf(a["exposure"], b["exposure"], t)
	tower.visible = false
	if night:
		# The night look itself (rule 2.82).
		for k in ENV_KEYS:
			env.set(k, a["env"][k])
		env.sky = null
		_set_light(sun, a["sun"], 1.0)
		fill.visible = a["fill_on"]
		_set_light(fill, a["fill"], 1.0)
	else:
		for k in ENV_KEYS:
			env.set(k, a["env"][k])
		var sky_b: Dictionary = b["sky"] if not night_b else _nightfall(a["sky"], b["env"]["background_color"])
		_set_sky(_mix_all(a["sky"], sky_b, t))
		var day_sun := _sun_up(a["sun"], b["sun"] if not night_b else a["sun"], t if not night_b else 0.0, alt)
		if not night_b:
			_set_light(sun, day_sun, 1.0)
			fill.visible = false
		else:
			# The sun going and the towers coming on: the night's ambient light takes over from the
			# sky's, and the stronger of the sun and the main towers keeps the shadow.
			env.ambient_light_sky_contribution = lerpf(float(a["env"]["ambient_light_sky_contribution"]), 0.0, t)
			env.ambient_light_color = b["env"]["ambient_light_color"]
			env.ambient_light_energy = lerpf(float(a["env"]["ambient_light_energy"]), float(b["env"]["ambient_light_energy"]), t)
			var up := clampf((alt + 0.5) / 2.5, 0.0, 1.0) * (1.0 - t)
			if t < 0.5:
				_set_light(sun, day_sun, up)
				_set_light(tower, b["sun"], t)
			else:
				_set_light(sun, b["sun"], t)
				_set_light(tower, day_sun, up)
			sun.shadow_enabled = true
			tower.shadow_enabled = false
			tower.visible = true
			fill.visible = true
			_set_light(fill, b["fill"], t)
	if not night:
		# Rule 2.81 holds as the sun moves: the camera opens up as a lower sun lights the open
		# grass less than the look's own sun did (and stops down for a higher one).
		if weather != VignetteWeather.WET:
			var real := clampf(alt, SUN_LOW, SUN_HIGH)
			var k := open_up(a["slot"], real)
			# Into the next look's own: the night's exposure as the towers take over.
			k = lerpf(k, 1.0 if night_b else open_up(b["slot"], real), t)
			exposure *= k
			# The seen sky keeps the brightness its look gave it (_sky_view).
			var view = _live_mat.get_shader_parameter("view")
			if view != null:
				_live_mat.set_shader_parameter("view", float(view) / k)
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.adjustment_enabled = true
	env.tonemap_exposure = exposure
	_tone_to_film()


## The sun of a day look, at the real sun's height (kept between SUN_LOW and SUN_HIGH) and
## the look's own heading; a wet look keeps its soft sun overhead.
func _sun_up(a: Dictionary, b: Dictionary, t: float, alt: float) -> Dictionary:
	var s := _mix_all(a, b, t)
	var qa: Quaternion = (a["basis"] as Basis).get_rotation_quaternion()
	var qb: Quaternion = (b["basis"] as Basis).get_rotation_quaternion()
	var basis := Basis(qa.slerp(qb, t))
	if weather != VignetteWeather.WET and alt > -900.0:
		var dir := -basis.z
		var flat := Vector3(dir.x, 0.0, dir.z)
		if flat.length() > 0.01:
			var e := deg_to_rad(clampf(alt, SUN_LOW, SUN_HIGH))
			basis = Basis.looking_at(flat.normalized() * cos(e) + Vector3(0.0, -sin(e), 0.0), Vector3.UP)
	s["basis"] = basis
	return s


## How far the camera opens up (the exposure's factor) as the sun moves from the look's own height,
## so the open grass stays at the look's brightness (rule 2.81). Measured with
## tools/visual/measure_open_up3d.gd (open grass on the far wing, lavapipe, 2026-11-20) at the
## heights in OPEN_ALTS: 1.0 at the look's own sun (day 52 degrees, late game 22).
const OPEN_ALTS := [4.0, 6.0, 9.0, 13.0, 18.0, 25.0, 35.0, 45.0, 55.0, 65.0]
const OPEN_UP := {
	"day": [2.49, 2.29, 2.07, 1.84, 1.63, 1.41, 1.22, 1.06, 0.98, 0.90],
	"twilight": [1.63, 1.50, 1.38, 1.22, 1.08, 0.96, 0.82, 0.72, 0.67, 0.63],
}
## Capture tools may force the factor (forced_open >= 0), to measure the curve.
static var forced_open := -1.0


static func open_up(slot_name: String, alt: float) -> float:
	if forced_open >= 0.0:
		return forced_open
	var ks: Array = OPEN_UP.get(slot_name, [])
	if ks.is_empty():
		return 1.0
	var a := clampf(alt, OPEN_ALTS[0], OPEN_ALTS[-1])
	for i in range(OPEN_ALTS.size() - 1):
		if a <= OPEN_ALTS[i + 1]:
			var f := (a - float(OPEN_ALTS[i])) / (float(OPEN_ALTS[i + 1]) - float(OPEN_ALTS[i]))
			return lerpf(ks[i], ks[i + 1], f)
	return ks[-1]


## The sun's height of a light, in radians.
static func _sun_height(p: Dictionary) -> float:
	return asin(clampf((p["basis"] as Basis).z.y, -1.0, 1.0))


func _set_light(l: DirectionalLight3D, p: Dictionary, k: float) -> void:
	l.basis = p["basis"]
	l.light_color = p["color"]
	l.light_energy = float(p["energy"]) * k
	l.light_angular_distance = p["size"]
	l.directional_shadow_max_distance = p["reach"]


func _set_sky(p: Dictionary) -> void:
	if _live_sky == null:
		_live_mat = ShaderMaterial.new()
		_live_mat.shader = SKY_SHADER
		_live_sky = Sky.new()
		_live_sky.sky_material = _live_mat
		_live_sky.radiance_size = Sky.RADIANCE_SIZE_64
	for k in p:
		_live_mat.set_shader_parameter(k, p[k])
	env.sky = _live_sky
