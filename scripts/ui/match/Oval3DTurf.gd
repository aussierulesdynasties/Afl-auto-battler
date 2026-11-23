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
var blades_on := true          # the graphics level keeps them (Oval3DQuality)
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


## The standing blades take the turf's colours and weather; so does any other piece of turf
## (Oval3D's apron skirt round a ground model), whole.
func _copy_look() -> void:
	for f in _followers:
		for u in mat.shader.get_shader_uniform_list():
			if str(u["name"]) != "fence_clip":
				f.set_shader_parameter(u["name"], mat.get_shader_parameter(u["name"]))
	if _bmat == null:
		return
	for k in ["grass_a", "grass_b", "wet", "hot", "wind", "wind_dir", "true_colour", "turf_gain"]:
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
	# Under a ground's own towers the grass is lit as brightly as by day (a broadcast's turf is the
	# same green at night), so it takes the day's colours; the old night light kept the darker set.
	var turf_slot := VignetteKickoff.DAY if slot == VignetteKickoff.NIGHT and _towers() != null else slot
	var g: Array = VignetteWeather.grass(weather, VignetteGround.GRASS, turf_slot)
	if wet:
		# The flat views darken wet turf to show the wet; here the sheen shows it, so the
		# colour goes half as dark (fully, the lit ground reads near black).
		# The flat views' wet palette turns blue-grey under lights; soaked turf is the same
		# green, darker. So the dry colour, a shade darker and greyer (measured: without the grey, soaked turf under
		# lights goes neon once the sheen is kept to the puddles).
		var dry: Array = VignetteWeather.grass("", VignetteGround.GRASS, turf_slot)
		var grey := 0.2 if turf_slot == VignetteKickoff.DAY else 0.3
		g = dry.map(func(c: Color) -> Color:
			var l := c.get_luminance()
			return c.lerp(Color(l, l, l), grey) * 0.95)
	mat.set_shader_parameter("grass_a", g[0] * _tint)
	mat.set_shader_parameter("grass_b", g[1] * _tint)
	var apron: Color = VignetteWeather.grass(weather, [VignetteGround.APRON], turf_slot)[0]
	mat.set_shader_parameter("apron_col", apron * _tint)
	var worn: Color = VignetteGround.WORN[1]
	mat.set_shader_parameter("worn_col", VignetteWeather.daylit(Color(worn.r, worn.g, worn.b), turf_slot))
	mat.set_shader_parameter("wet", 1.0 if wet else 0.0)
	mat.set_shader_parameter("hot", 1.0 if hot else 0.0)
	mat.set_shader_parameter("wind", VignetteWeather.wind(weather))
	mat.set_shader_parameter("wind_dir", Vector2(1.0, 0.25).normalized())
	# Under lights the stripes stand out more than in flat daylight.
	mat.set_shader_parameter("stripe_amount", lerpf(0.24, 0.16, d))

	# A hot day's ground is still a watered AFL ground: the fine day's green with some dried
	# patches (the full straw look goes lime under the TV tone, rule 2.81; approved hot sky, 2.84).
	if hot:
		g = VignetteWeather.grass("", VignetteGround.GRASS, turf_slot)
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
	sun.visible = true
	if slot == VignetteKickoff.NIGHT:
		_night(wet)
	else:
		fill.visible = false
		_sky_light(hot)
		if slot == VignetteKickoff.TWILIGHT:
			_late_game()
		if wet:
			_cloud_light()
	_set_towers(TOWERS_ON.get(slot, 0.0))
	# The exposure, set by the brightness of open grass (rule 2.81): each look's grass near a fine
	# day's, as a broadcast camera opens up in poorer light.
	var exposure: float = EXPOSURE[slot]
	if wet:
		exposure *= EXPOSURE_WET[slot]
	# The broadcast colour's turf is lighter under the towers than by day; brought back to a
	# fine day's open grass, as the rule above asks.
	exposure *= lerpf(1.0, float(EXPOSURE_BROADCAST.get(slot, 1.0)), broadcast)
	env.tonemap_exposure = exposure
	_exposure = exposure
	mat.set_shader_parameter("true_colour", broadcast)
	mat.set_shader_parameter("turf_gain", turf_gain)
	_copy_look()
	_sky_view()
	_tone_to_film()
	_light_stands()
	_quality()
	_wet_world(wet)
	_haze()


## Drops in the air at each level (Oval3DQuality "rain"); the node drawing them while it rains.
var rain: Oval3DRain
## What oval_wet was last set to (1 wet kit, 0 dry): the renderer's own copy can't be read back
## at run time outside the editor (a headless run reads nothing).
var wet_kit := 0.0


## A wet day beyond the turf and sky (rule 2.83): rain falls on screen and the far stands grey in
## it, the men's guernseys, hair and skin look wet (oval_wet, read by the player and head shaders),
## and by day the towers are on early, their light a second faint shadow and the glint in the wet
## turf. The graphics level sets how many drops fall (Oval3DQuality "rain").
func _wet_world(wet: bool) -> void:
	wet_kit = 1.0 if wet else 0.0
	RenderingServer.global_shader_parameter_set("oval_wet", wet_kit)
	Oval3DRain.haze(env, wet)
	var level := str(oval.get("quality")) if oval.get("quality") != null else ""
	var drops := int(Oval3DQuality.preset(level)["rain"])
	if rain != null and (not wet or rain.amount != drops):
		rain.queue_free()
		rain = null
	if wet and drops > 0 and rain == null:
		rain = Oval3DRain.new(oval, drops)
		oval.add_child(rain)
	if wet and slot != VignetteKickoff.NIGHT:
		fill.visible = true
		fill.rotation_degrees = Vector3(-58.0, 150.0, 0.0)
		fill.light_color = Color(0.92, 0.95, 1.0)
		fill.light_energy = WET_DAY_TOWERS


## The air's own haze on a dry day (the York Park QA, 2026-11-22: far hills stayed as dark as
## near ones). Real air thins the far land toward the sky at the horizon. Here, on screen, a dark
## hill goes about a fifth of the way to the sky by 3 km, near half by 10 km and two thirds by
## 25 km (a clear winter's day; tools/visual/measure_day_tint3d.gd), and the ground itself (150 m
## across) about one part in a hundred. The haze is the seen sky's own horizon colour at its own
## brightness, so the far land meets the sky behind it, and it follows the sky as the clock moves
## it (warm at a late game, gone at night). A wet day keeps the rain's grey (Oval3DRain.haze).
## Cheap on a phone: one exponential per pixel.
const HAZE_DENSITY := 3.0e-5


func _haze() -> void:
	if weather == VignetteWeather.WET:
		return
	var sm: ShaderMaterial = env.sky.sky_material if env.sky != null else null
	if sm == null or env.background_mode != Environment.BG_SKY:
		env.fog_enabled = false
		return
	var hc = _sky_param(sm, "seen_horizon")
	if hc == null or (hc as Color).a == 0.0:
		hc = _sky_param(sm, "horizon")
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	env.fog_density = HAZE_DENSITY
	env.fog_light_color = Color(hc as Color, 1.0)
	env.fog_light_energy = float(_sky_param(sm, "energy")) * float(_sky_param(sm, "view"))
	env.fog_sun_scatter = 0.0
	env.fog_aerial_perspective = 0.0
	env.fog_sky_affect = 0.0
	env.fog_height_density = 0.0


## The graphics level's cuts to this look (Oval3DQuality): the sun's shadow bands, whether a
## late game's plain stand shades the wing, the standing blades. High keeps the look as built.
func _quality() -> void:
	var level := str(oval.get("quality")) if oval.get("quality") != null else ""
	var p := Oval3DQuality.preset(level)
	Oval3DQuality.apply_sun(level, sun)
	if not bool(p["stand_shade"]):
		_stand_shade(false)
	blades_on = bool(p["blades"])


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
	film.set_shader_parameter("balance", BALANCE.get(slot, Vector3.ONE))
	film.set_shader_parameter("broadcast", broadcast)
	_sky_tint()
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.tonemap_exposure = 1.0
	env.adjustment_enabled = false


## The broadcast camera's white balance for each time of day (oval3d_film.gdshader): red, green
## and blue gains on the drawn light, found by tools/visual/capture_tv_colour.gd calibrate so a grey
## card lying on the open turf comes out grey. The sky light, the grass's bounce and the towers
## otherwise leave the whole picture blue-green (grass near (2, 49, 4), the card (21, 55, 57)).
const BALANCE := {"day": Vector3(0.948, 1.0, 1.052), "twilight": Vector3(0.926, 1.0, 0.978), "night": Vector3(1.229, 1.0, 0.931)}
## How bright the turf is drawn once its colour is read right (oval3d_ground.gdshader's
## true_colour): the grass's colour was turned to linear twice, which made it near black-green;
## read once it is several times lighter, and this brings open grass to a broadcast's brightness.
var turf_gain := 0.65
## 0 is rule 2.81's look as approved; 1 the broadcast colour: the turf's colour read right
## (turf_gain) and the camera's white balance (BALANCE). The director's pick, rule 2.114.
var broadcast := 1.0:
	set(v):
		broadcast = v
		if _applied:
			apply(weather, slot)


## How much of the sky's colour its light keeps in the broadcast colour (oval3d_sky.gdshader).
const SKY_LIGHT_TINT := 0.5


func _sky_tint() -> void:
	if env != null and env.sky != null and env.sky.sky_material is ShaderMaterial:
		(env.sky.sky_material as ShaderMaterial).set_shader_parameter("light_tint", lerpf(1.0, SKY_LIGHT_TINT, broadcast))


## AgX exposure for each time of day, and the factor a wet day adds (measured with
## tools/visual/capture_turf3d.gd: open grass in each look against the fine day's).
const EXPOSURE := {"day": 1.0, "twilight": 2.81, "night": 1.91}
const EXPOSURE_BROADCAST := {"night": 0.72}
## The towers' light on a wet day or twilight, lit early under the cloud (the night's are 1.6 and 0.5).
const WET_DAY_TOWERS := 0.35
const EXPOSURE_WET := {"day": 1.83, "twilight": 1.83, "night": 1.84}


## Night: the towers, high and cool white from behind the far wing, a weaker set from the other
## side, under one dark sky colour (rule 2.80's sky light is the daylight).
## How far a ground's own towers are up in each look (Oval3DTowers): full at night; at a late
## game they are already on, as at every twilight match, their heads lit and a little light on
## the ground under the low sun.
const TOWERS_ON := {"day": 0.0, "twilight": 0.12, "night": 1.0}
var _tower_level := 0.0


## The ground's towers, when it has them (Oval3DTowers.banks); null otherwise.
func _towers() -> Oval3DTowers:
	var t = oval.get("towers")
	return t if t is Oval3DTowers and not (t as Oval3DTowers).banks.is_empty() else null


func _set_towers(k: float) -> void:
	_tower_level = k
	var t := _towers()
	if t != null:
		t.set_level(k)


## The night's light from the ground's own towers (Oval3DTowers): they light the ground and throw
## the men's shadows, so the old night light is off.
func _tower_night(wet: bool) -> void:
	fill.visible = false
	fill.light_energy = 0.0
	sun.light_energy = 0.0
	sun.shadow_enabled = false
	sun.visible = false
	# The stands and the roof catch the spill from the towers and the stands' own lights.
	env.ambient_light_color = Color(0.42, 0.46, 0.5)
	env.ambient_light_energy = 0.3
	if wet:
		env.ambient_light_energy *= 1.1


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
	if _towers() != null:
		_tower_night(wet)


## The sun's turn for this look, `alt` degrees up (the look's own height, where its brightness
## was measured) at the compass bearing the real sun has over this ground at the look's bounce:
## the match's own clock when it follows one, else the ground's place mid-season. The sun is in
## the north at every Australian ground, so the north side of a stadium is the sunlit one
## (Oval3DSunClock.sun_basis; each ground's bearing in data/ground_places.json).
func _real_sun(alt: float) -> Basis:
	var c := clock if clock != null else Oval3DSunClock.for_match(_ground_name(), "", slot)
	var h := float(Oval3DSunClock.KICKOFF.get(slot, c.kickoff)) if clock != null else c.kickoff
	return c.basis_at(h, alt)


## The ground's name as the clock knows it: Oval3D's ground, or the name of the model it shows.
func _ground_name() -> String:
	var g := str(oval.get("ground")) if oval != null and oval.get("ground") != null else ""
	if g != "" or ground == "":
		return g
	for name in GroundModels.GROUNDS:
		if GroundModels.GROUNDS[name] == ground:
			return name
	return ""


## The colour of the sky's light on a fine day, apart from the sky you see (the York Park and SCG
## QA, 2026-11-22: shaded concrete read lavender). The seen sky's deep blue overhead, lighting a
## shaded wall, made its grey a strong blue (saturation 0.66 on screen after the broadcast tone,
## measured with tools/visual/measure_day_tint3d.gd on a real GPU); a TV camera balanced for the
## sun sees shade only a little cool. This light keeps shade cool (about 0.3) and sunlit grey
## near neutral, and leaves the turf's green as it was. Checked against Google Earth's nadir of
## Optus (2026-11-23): the truss shadow on the white roof, blue over red 1.13 here against 1.10
## (it was 1.37), and the shaded bronze cladding, 54 64 85 against 48 63 79 (it was 72 98 156).
## The zenith, which lights a roof, is the greyer; the horizon, which lights a wall, the bluer.
const DAY_LIGHT_ZENITH := Color(0.46, 0.49, 0.53)
const DAY_LIGHT_HORIZON := Color(0.72, 0.78, 0.86)
const HOT_LIGHT_ZENITH := Color(0.515, 0.55, 0.595)


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
		sun.basis = _real_sun(68.0)
		sm.set_shader_parameter("energy", 1.2)
		sm.set_shader_parameter("zenith", HOT_LIGHT_ZENITH)
		sm.set_shader_parameter("horizon", Color(0.82, 0.86, 0.9))
		sun.light_energy = 1.6
		sun.light_color = Color(1.0, 0.96, 0.88)
		_sky_look({"cover": 0.06, "sun_halo": 1.2, "target": 0.7, "seen_horizon": Color(0.66, 0.78, 0.92, 1.0),
				"seen_zenith": Color(0.2, 0.42, 0.82, 1.0), "sky_curve": 0.45})
	else:
		# A fine winter's day: blue, a few fair-weather clouds, the sun's glare round it.
		sun.basis = _real_sun(52.0)
		sm.set_shader_parameter("energy", 1.4)
		sun.light_energy = 1.15
		sun.light_color = Color(1.0, 0.95, 0.86)
		# The seen sky as approved (rule 2.84); its light a paler, greyer blue (DAY_LIGHT_ZENITH).
		sm.set_shader_parameter("zenith", DAY_LIGHT_ZENITH)
		sm.set_shader_parameter("horizon", DAY_LIGHT_HORIZON)
		sm.set_shader_parameter("seen_zenith", Color(0.22, 0.43, 0.78, 1.0))
		sm.set_shader_parameter("seen_horizon", Color(0.68, 0.78, 0.88, 1.0))
		_sky_look({"cover": 0.32, "cloud_lit": Color(1.0, 1.0, 1.0), "cloud_dark": Color(0.62, 0.66, 0.74),
				"sun_halo": 0.35})


## Rule 2.80's late game ("C late games"): the sun 22 degrees up (about 4.30 pm in winter), so a
## stand's top, 24 m up and 34 m back from the fence, shades about 25 m of the wing below it; the
## clouds warm on the sun's side (the approved late-game sky, rule 2.84). The sun stands where it
## really does over the ground at a twilight bounce (_real_sun): low in the north-west in winter.
func _late_game() -> void:
	var sm: ShaderMaterial = env.sky.sky_material
	sun.light_energy = 1.2
	sun.basis = _real_sun(22.0)
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
## turf, the goalposts and the seats keep the sky's own light, and so does the land round a ground
## (GroundModels' surrounds, meta open_ground): it lies in the open under the sky like the turf.
const STAND_GREEN := 0.15    # how much of the grass's colour the stands' grey keeps
const STAND_SHADER := preload("res://scripts/ui/match/oval3d_stand.gdshader")
const AMB_KEYS := ["amb_down", "amb_low", "amb_level", "amb_high", "amb_up"]
var _stand_mats: Array[ShaderMaterial] = []


## Gives a ground model's surfaces the stands' light (called once the model is built). Surfaces the
## stand shader does not cover (see-through or glowing ones) keep their own.
func light_stands(model: Node) -> void:
	var seen := {}
	for mi: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		if mi.mesh == null or mi.has_meta("open_ground"):
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
				if m.ao_enabled and m.ao_texture != null:
					own.set_shader_parameter("use_ao", true)
					own.set_shader_parameter("ao_tex", m.ao_texture)
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
	var grey := (Color(gl, gl, gl) * _bounce_tint(green)).lerp(grass, green)
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


## The colour of the light the ground throws up onto a stand: sunlit ground, so the sun's colour at
## the grass's brightness, not a neutral grey (Marvel QA on the PC GPU, 2026-11-23: a white wall
## facing away from the sun read clearly blue, NAB's fins 96 112 142, where a real shaded white wall
## in daylight is near-neutral grey). Only the stands' grey bounce takes it (green < 1). A stand
## sees more sunlit ground than the centre square's grass (seats, concourses, the far stands lit
## by the sun): STAND_BOUNCE. Measured with tools/visual/measure_day_tint3d.gd at Optus: a shaded
## white wall from blue over red 1.16 to 1.12 and shaded concrete 1.18 to 1.12, shade 5% brighter.
const STAND_BOUNCE := 1.3
func _bounce_tint(green: float) -> Color:
	if green >= 1.0 or sun == null or not sun.visible:
		return Color(1, 1, 1)
	var c := sun.light_color
	var l := c.get_luminance()
	return Color(c.r / l, c.g / l, c.b / l) * STAND_BOUNCE if l > 0.001 else Color(1, 1, 1)


## A sky shader setting, or the shader's own default when the look leaves it unset.
func _sky_param(sm: ShaderMaterial, key: String) -> Variant:
	var v: Variant = sm.get_shader_parameter(key)
	if v == null:
		v = RenderingServer.shader_get_parameter_default(sm.shader.get_rid(), key)
	if v == null:
		v = _code_default(sm.shader.code, key)
	return v


## A uniform's default as the shader's own code writes it. A renderer that does not compile
## shaders (a headless test run) knows no defaults, and the stands would read a sky of nothing.
static func _code_default(code: String, key: String) -> Variant:
	var re := RegEx.create_from_string(
			"uniform\\s+(float|vec4)\\s+" + key + "\\b[^=;]*=\\s*([^;]+);")
	var m := re.search(code)
	if m == null:
		return null
	var val := m.get_string(2).strip_edges()
	if m.get_string(1) == "float":
		return float(val)
	var nums := val.trim_prefix("vec4(").trim_suffix(")").split(",")
	if nums.size() != 4:
		return null
	return Color(float(nums[0]), float(nums[1]), float(nums[2]), float(nums[3]))


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
	sun.basis = Basis.looking_at(Vector3(0.2, -1.0, 0.35).normalized(), Vector3.UP)
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
	blades.visible = blades_on and cam_local.distance_to(Vector3(c.x, 0.0, c.y)) < BLADE_NEAR
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
func follow_clock(p_weather: String, p_clock: Oval3DSunClock) -> void:
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
	var s := {"turf": {}, "env": {}, "shade": _shade, "exposure": _exposure, "towers": _tower_level,
			"sun_on": sun.visible, "sun_shadow": sun.shadow_enabled,
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
	sun.visible = true
	_set_towers(lerpf(float(a.get("towers", 0.0)), float(b.get("towers", 0.0)), t))
	if night:
		# The night look itself (rule 2.82).
		for k in ENV_KEYS:
			env.set(k, a["env"][k])
		env.sky = null
		_set_light(sun, a["sun"], 1.0)
		sun.visible = a.get("sun_on", true)
		sun.shadow_enabled = a.get("sun_shadow", true)
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
			sun.shadow_enabled = sun.light_energy > 0.01
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
	_haze()


## The sun of a day look, at the real sun's height (kept between SUN_LOW and SUN_HIGH) and
## the look's own heading; a wet look keeps its soft sun overhead.
func _sun_up(a: Dictionary, b: Dictionary, t: float, alt: float) -> Dictionary:
	var s := _mix_all(a, b, t)
	var qa: Quaternion = (a["basis"] as Basis).get_rotation_quaternion()
	var qb: Quaternion = (b["basis"] as Basis).get_rotation_quaternion()
	var basis := Basis(qa.slerp(qb, t))
	if weather != VignetteWeather.WET and alt > -900.0 and clock != null:
		# The real sun: its height on the clock (kept between SUN_LOW and SUN_HIGH) and its
		# bearing over the ground.
		basis = clock.basis_at(hour, clampf(alt, SUN_LOW, SUN_HIGH))
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
