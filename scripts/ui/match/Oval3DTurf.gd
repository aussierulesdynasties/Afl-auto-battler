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
	var lamps := VignetteKickoff.lights(slot)
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

	_copy_look()
	# The sky behind the stands; at night one dark colour.
	var sky: Array = VignetteWeather.sky(weather, slot)
	env.background_color = sky[1] if sky.size() > 1 else VignetteGround.SKY
	# The backdrop is one flat colour, not a sky: mirrored in the turf at a low angle it
	# lays a grey film over the grass. The wet sheen comes from the lights instead.
	env.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED

	# The key light: the sun by day and at twilight (low and warm then), the towers at night.
	sun.shadow_enabled = true
	if slot == VignetteKickoff.NIGHT:
		# The towers: high, cool white, from behind the far wing; a weaker set from the other side.
		sun.rotation_degrees = Vector3(-58.0, 150.0, 0.0)
		sun.light_color = Color(0.97, 1.0, 0.97)
		sun.light_energy = 1.6
		fill.visible = true
		fill.rotation_degrees = Vector3(-58.0, -30.0, 0.0)
		fill.light_color = Color(0.92, 0.95, 1.0)
		fill.light_energy = 0.5
		env.ambient_light_color = Color(0.4, 0.46, 0.4)
		env.ambient_light_energy = 0.35
	elif slot == VignetteKickoff.TWILIGHT:
		sun.rotation_degrees = Vector3(-22.0, -60.0, 0.0)
		sun.light_color = Color(1.0, 0.75, 0.52)
		sun.light_energy = 1.9
		fill.visible = lamps > 0.0
		fill.rotation_degrees = Vector3(-58.0, 150.0, 0.0)
		fill.light_color = Color(0.92, 0.95, 1.0)
		fill.light_energy = 0.4 * lamps
		env.ambient_light_color = Color(0.6, 0.55, 0.66)
		env.ambient_light_energy = 0.7
	else:
		fill.visible = false
		sun.rotation_degrees = Vector3(-68.0 if hot else -52.0, -35.0, 0.0)
		sun.light_color = Color(1.0, 0.95, 0.85) if hot else Color(1.0, 0.98, 0.94)
		sun.light_energy = 1.55 if hot else 1.25
		env.ambient_light_color = Color(0.62, 0.66, 0.72)
		env.ambient_light_energy = 0.32 if hot else 0.4
	# The broadcast camera opens up in poorer light, as a real one does (measured: the ground's
	# brightness in each look within about 15% of a fine day's).
	var exposure := 1.0
	match slot:
		VignetteKickoff.TWILIGHT:
			exposure = 2.05
		VignetteKickoff.NIGHT:
			exposure = 1.7
	if wet:
		exposure *= 1.85
	env.tonemap_exposure = exposure
	# Under a closed roof no sun reaches the field: the roof's own lights do it (rule 2.91).
	var stadium = oval.get("stadium")
	var roofed: bool = stadium != null and stadium.closed
	sun.visible = not roofed
	if roofed:
		fill.visible = false
	if wet:
		# Overcast: the key goes soft and cool, the sky does most of the lighting.
		sun.light_energy *= 0.55 if slot == VignetteKickoff.DAY else 0.85
		sun.light_color = sun.light_color.lerp(Color(0.85, 0.9, 1.0), 0.5)
		# A grey sky by day; under lights the night sky is black, so no grey cast.
		if slot == VignetteKickoff.DAY:
			env.ambient_light_color = env.ambient_light_color.lerp(Color(0.6, 0.65, 0.72), 0.5)
		env.ambient_light_energy *= 2.4 if slot == VignetteKickoff.DAY else 1.1


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
