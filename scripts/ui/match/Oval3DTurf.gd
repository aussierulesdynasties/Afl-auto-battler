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

## Each ground's cut and grass (row 202 2b; looks only). Curators cut a fresh pattern before
## every televised match, so no ground has one fixed cut; this is the cut each ground shows in
## the game, a first draft for the director's review. [pattern, band width m, grass]:
## pattern across (bands across the ground, the mower running wing to wing), along, checker
## (cut both ways), diagonal, diamonds (both diagonals); grass couch (the warm-climate grounds:
## a touch warmer and yellower) or rye (the southern grounds: a touch deeper and cooler;
## Adelaide Oval's surface is rye, InDaily 2025). A ground not listed takes DEFAULT_MOW.
const ACROSS := 0
const ALONG := 1
const CHECKER := 2
const DIAGONAL := 3
const DIAMONDS := 4
const DEFAULT_MOW := [ACROSS, 12.0, ""]
const MOWING := {
	"mcg": [ACROSS, 12.0, "rye"], "marvel": [ACROSS, 10.0, "rye"], "optus": [CHECKER, 12.0, "couch"],
	"scg": [DIAGONAL, 10.0, "couch"], "gmhba": [ACROSS, 12.0, "rye"],
	"people_first": [DIAMONDS, 12.0, "couch"], "engie": [CHECKER, 12.0, "couch"],
	"bellerive": [ALONG, 12.0, "rye"], "manuka": [ACROSS, 12.0, "rye"], "norwood": [ACROSS, 10.0, "rye"],
	"waverley_park": [ACROSS, 14.0, "rye"], "windy_hill": [ACROSS, 10.0, "rye"],
	"moorabbin": [ACROSS, 10.0, "rye"], "ikon_park": [ACROSS, 12.0, "rye"], "whitten": [ALONG, 12.0, "rye"],
	"football_park": [ACROSS, 14.0, "rye"], "subiaco": [ACROSS, 12.0, "couch"], "waca": [ACROSS, 12.0, "couch"],
	"york_park": [CHECKER, 10.0, "rye"], "cazalys": [ACROSS, 10.0, "couch"],
	"north_hobart": [ACROSS, 10.0, "rye"], "bruce": [ACROSS, 12.0, "rye"],
	"riverway": [DIAGONAL, 12.0, "couch"], "barossa": [ACROSS, 10.0, "rye"], "sky": [ALONG, 12.0, "rye"],
	"jiangwan": [CHECKER, 12.0, "couch"], "hands": [ACROSS, 10.0, "couch"],
	"blacktown": [ACROSS, 12.0, "couch"], "summit": [ACROSS, 10.0, "rye"], "macpoint": [DIAMONDS, 12.0, "rye"],
	"adelaide": [CHECKER, 12.0, "rye"], "gabba": [ACROSS, 12.0, "couch"],
}
## How each grass shifts the day's turf colours (multiplied in, so weather and light still set them).
const GRASS_TINT := {
	"couch": Color(1.05, 1.0, 0.88),
	"rye": Color(0.96, 1.0, 1.04),
}

var oval: Node3D
var mat: ShaderMaterial
var ground := ""                # the ground's slug (GroundModels); "" the game's own oval
var _tint := Color(1, 1, 1)
var _applied := false
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


## The standing blades take the turf's colours and weather; so does any other piece of turf
## (Oval3D's apron skirt round a ground model), whole.
func _copy_look() -> void:
	for f in _followers:
		for u in mat.shader.get_shader_uniform_list():
			if str(u["name"]) != "fence_clip":
				f.set_shader_parameter(u["name"], mat.get_shader_parameter(u["name"]))
	if _bmat == null:
		return
	for k in ["grass_a", "grass_b", "wet", "hot", "wind", "wind_dir"]:
		_bmat.set_shader_parameter(k, mat.get_shader_parameter(k))


## The ground's own cut and grass (MOWING), from its GroundModels slug; "" the default.
func set_ground(slug: String) -> void:
	ground = slug
	var m: Array = MOWING.get(slug, DEFAULT_MOW)
	mat.set_shader_parameter("mow_pattern", int(m[0]))
	mat.set_shader_parameter("mow_width", float(m[1]))
	_tint = GRASS_TINT.get(m[2], Color(1, 1, 1))
	if _applied:
		apply(weather, slot)
	else:
		_copy_look()


var _followers: Array[ShaderMaterial] = []


## Another piece of turf, painted as the turf is from now on.
func follow(m: ShaderMaterial) -> void:
	_followers.append(m)
	_copy_look()


## The day's look: weather "perfect", "wet", "windy" or "hot" (anything else is perfect);
## slot day, twilight or night (VignetteKickoff).
func apply(p_weather: String, p_slot: String) -> void:
	weather = p_weather
	slot = p_slot if p_slot in VignetteKickoff.SLOTS else VignetteKickoff.NIGHT
	_applied = true
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
	mat.set_shader_parameter("grass_a", g[0] * _tint)
	mat.set_shader_parameter("grass_b", g[1] * _tint)
	var apron: Color = VignetteWeather.grass(weather, [VignetteGround.APRON], slot)[0]
	mat.set_shader_parameter("apron_col", apron * _tint)
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
		mat.set_shader_parameter("grass_a", g[0] * _tint)
		mat.set_shader_parameter("grass_b", g[1] * _tint)
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
	_sky_view()
	_tone_to_film()
	_light_stands()


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


## The light on a ground's model (director, 2026-11-21: roof undersides "grey, a faint green
## tint"). The sky's light map is the view from the centre square: below the horizon it is all
## sunlit grass, right for the men and the turf. A stand is not on the grass: a roof's underside, a
## tier's soffit or a canopy outside the ground faces seats, concrete and paving, yet took the full
## grass green. So the model's surfaces (oval3d_stand.gdshader) take the sky's light as if that
## grass were grey, keeping STAND_GREEN of its colour: faces turned up are lit as before, faces
## turned down go grey. At night the light is one colour already, so nothing changes. The men, the
## turf, the goalposts and the seats keep the sky's own light.
const STAND_GREEN := 0.15    # how much of the grass's colour the stands' grey keeps
const STAND_SHADER := preload("res://scripts/ui/match/oval3d_stand.gdshader")
const AMB_KEYS := ["amb_down", "amb_low", "amb_level", "amb_high", "amb_up"]
var _stand_mats: Array[ShaderMaterial] = []


## Gives a ground model's surfaces the stands' light (called once the model is built). Surfaces the
## stand shader does not cover (see-through or glowing ones) keep their own.
func light_stands(model: Node) -> void:
	var seen := {}
	for mi: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		if mi.mesh == null:
			continue
		for i in mi.mesh.get_surface_count():
			var m := mi.get_active_material(i) as StandardMaterial3D
			if m == null or m.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED or m.emission_enabled:
				continue
			if not seen.has(m):
				var own := ShaderMaterial.new()
				own.shader = STAND_SHADER
				own.resource_name = m.resource_name    # its name still tells what it is (a screen's face)
				own.set_shader_parameter("albedo_tex", m.albedo_texture)
				own.set_shader_parameter("use_vcol", m.vertex_color_use_as_albedo)
				own.set_shader_parameter("albedo_col", m.albedo_color)
				own.set_shader_parameter("roughness_v", m.roughness)
				own.set_shader_parameter("metallic_v", m.metallic)
				own.set_shader_parameter("uv_scale", m.uv1_scale)
				own.set_shader_parameter("uv_offset", m.uv1_offset)
				seen[m] = own
				_stand_mats.append(own)
			mi.set_surface_override_material(i, seen[m])
	_light_stands()


func _light_stands() -> void:
	if _stand_mats.is_empty():
		return
	var amb: Array = [Vector3.ZERO, Vector3.ZERO, Vector3.ZERO, Vector3.ZERO, Vector3.ZERO]
	if env.ambient_light_source == Environment.AMBIENT_SOURCE_SKY and env.sky != null:
		var sm: ShaderMaterial = env.sky.sky_material
		var e := env.ambient_light_energy * env.ambient_light_sky_contribution
		var grey := stand_light(sm, e, STAND_GREEN)
		var sky := stand_light(sm, e, 1.0)
		for k in amb.size():
			amb[k] = grey[k] - sky[k]
	var e_amb := env.ambient_light_energy * env.ambient_light_sky_contribution
	for m in _stand_mats:
		for k in AMB_KEYS.size():
			m.set_shader_parameter(AMB_KEYS[k], amb[k])
		m.set_shader_parameter("ref_scale", 1.0 / e_amb if e_amb > 0.001 else 0.0)


## The sky's light (its cosine-weighted mean, as the engine lights a face from the sky) for a face
## turned straight down, half down, level, half up and straight up, with the grass below the
## horizon keeping `green` of its colour (1 as it is). The sky as oval3d_sky.gdshader draws its light map.
func stand_light(sm: ShaderMaterial, scale := 1.0, green := 1.0) -> Array:
	var zenith: Color = _sky_param(sm, "zenith")
	var horizon: Color = _sky_param(sm, "horizon")
	var bowl: Color = _sky_param(sm, "bowl")
	var grass: Color = _sky_param(sm, "grass")
	var bowl_top: float = _sky_param(sm, "bowl_top")
	var energy: float = _sky_param(sm, "energy")
	var g_energy: float = _sky_param(sm, "grass_energy")
	var gl := grass.get_luminance()
	var grey := Color(gl, gl, gl).lerp(grass, green)
	var out := []
	for ny in [-1.0, -0.5, 0.0, 0.5, 1.0]:
		var n := Vector3(sqrt(1.0 - ny * ny), ny, 0.0)
		var sum := Color(0, 0, 0)
		var wsum := 0.0
		# Directions over the sphere on an even grid of height and bearing (area-even in height).
		for iy in 48:
			var y := -1.0 + (iy + 0.5) * 2.0 / 48.0
			var r := sqrt(1.0 - y * y)
			for ia in 48:
				var az := TAU * (ia + 0.5) / 48.0
				var d := Vector3(r * cos(az), y, r * sin(az))
				var w := d.dot(n)
				if w <= 0.0:
					continue
				var up := horizon.lerp(zenith, smoothstep(bowl_top, 0.75, y))
				var c := bowl.lerp(up, smoothstep(bowl_top - 0.02, bowl_top + 0.02, y))
				c = (grey * g_energy).lerp(c, smoothstep(-0.02, 0.02, y))
				sum += c * w
				wsum += w
		var e := sum / wsum * energy * scale
		out.append(Vector3(e.r, e.g, e.b))
	return out


## A sky shader setting, or the shader's own default when the look leaves it unset.
func _sky_param(sm: ShaderMaterial, key: String) -> Variant:
	var v: Variant = sm.get_shader_parameter(key)
	return v if v != null else RenderingServer.shader_get_parameter_default(sm.shader.get_rid(), key)


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
