extends SceneTree
## PROTOTYPE (row 202, 3D view plan step 2e, the cameras): camera options on the 3D oval, filmed
## for the director to choose between. Nothing here is the game's camera until he picks one.
##   godot --path . --script tools/visual/capture_cameras3d.gd -- OUTDIR CONFIG.json
## CONFIG: {"seed": 31, "t0": 30.0, "dur": 20.0, "expo": 1.0, "shots": [SHOT, ...]}
## SHOT:   {"name": "A", "size": [w, h], "eye": [x, y, z], "width": 40.0, "lead": 0.0,
##          "smooth": 0.5, "aim_y": 1.0}
## Each camera works the way a real broadcast camera does: it stands still on its mount (eye, in
## metres: x up the ground, y up, z across; +z is the near wing) and only pans, tilts and zooms.
## It aims at the ball (averaged over `smooth` seconds each side, as an operator's hand smooths
## it), and zooms so `width` metres of ground across the picture are in shot at the ball.
## Fremantle v St Kilda (seed), first quarter, filmed from t0 for dur seconds at 30 frames a
## second (real speed). Pass 1 plays the director and the oval without drawing and logs where the
## ball is; pass 2 plays them again and films each shot from the logged aim. For every shot it
## prints how often the ball is inside the picture and how often the stands stand between the
## camera and the ball (the line of sight, tested against the stand's rake).
## The look is rule 2.80-2.81's fine day (sky light, AgX with the TV grade); not the question.

const DT := 1.0 / 60.0
const HALF_LEN := 86.3
const HALF_WID := 67.4
const FENCE := 6.0
const STAND_DEPTH := 34.0
const STAND_RISE := 24.0
var _clouds: NoiseTexture2D


func _initialize() -> void:
	_run.call_deferred()
	create_timer(1500.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(str(args[1])))
	var seed := int(cfg.get("seed", 31))
	var t0 := float(cfg.get("t0", 30.0))
	var dur := float(cfg.get("dur", 20.0))
	var shots: Array = cfg["shots"]
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.use_debanding = true
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), seed).run()

	# Pass 1: the ball's place every frame (the oval synced, nothing drawn).
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	var f0 := int(t0 / DT)
	var f1 := int((t0 + dur) / DT)
	var balls := []
	var n := 0
	while n <= f1 and not d.idle():
		d.advance(DT)
		oval.sync(DT)
		balls.append(oval.ball.global_position)
		n += 1
	f1 = mini(f1, balls.size() - 1)
	print("PASS1 %d frames; window %d-%d; ball from %s to %s" % [balls.size(), f0, f1, balls[f0], balls[f1]])
	oval.queue_free()
	await process_frame

	for shot in shots:
		var sm := float(shot.get("smooth", 0.5))
		var k := int(sm / DT)
		var aims := []
		for f in range(f0, f1 + 1):
			var a := Vector3.ZERO
			var c := 0
			for g in range(maxi(0, f - k), mini(balls.size() - 1, f + k) + 1):
				a += balls[g]
				c += 1
			a /= float(c)
			a.y = float(shot.get("aim_y", 1.0))
			aims.append(a)
		shot["aims"] = aims

	# Pass 2, filmed: one play-through per shot (each its own picture size).
	_make_clouds()
	await _clouds.changed
	for shot in shots:
		var sz: Array = shot["size"]
		var size := Vector2i(int(sz[0]), int(sz[1]))
		root.size = size
		DisplayServer.window_set_size(size)
		d = load("res://scripts/ui/match/MatchDirector.gd").new()
		d.setup(res, res["events"])
		oval = load("res://scripts/ui/match/Oval3D.gd").new()
		root.add_child(oval)
		oval.build(d, "FRE", "STK")
		_look(oval, float(cfg.get("expo", 1.0)))
		var eye_a: Array = shot["eye"]
		var eye := Vector3(float(eye_a[0]), float(eye_a[1]), float(eye_a[2]))
		var cam: Camera3D = oval.camera
		cam.keep_aspect = Camera3D.KEEP_WIDTH
		var width := float(shot.get("width", 40.0))
		# Exposure set by the open grass, as the look prototype sets it (TURF=0.32): from the
		# shot's first aim, bare turf on the ball's row read four times and the exposure moved.
		var aim0: Vector3 = (shot["aims"] as Array)[0]
		cam.global_position = eye
		cam.look_at(aim0, Vector3.UP)
		cam.fov = rad_to_deg(2.0 * atan(width * 0.5 / eye.distance_to(aim0)))
		var env: Environment = oval._env
		for it in range(5):
			for w in range(3):
				await process_frame
			await RenderingServer.frame_post_draw
			var im := root.get_viewport().get_texture().get_image()
			var got := _grass(im)
			if it < 4:
				env.tonemap_exposure *= pow(float(cfg.get("turf", 0.32)) / maxf(got, 0.01), 1.6)
			else:
				print("EXPOSURE %.3f, grass %.3f" % [env.tonemap_exposure, got])
			# The seen sky held at the fine day's horizon brightness (0.75) at this exposure,
			# as the look prototype's _sky_view does, or it blows out white.
			var skm: ShaderMaterial = env.sky.sky_material
			var hz: Color = RenderingServer.shader_get_parameter_default(skm.shader.get_rid(), "horizon")
			var lum := 0.2126 * hz.r + 0.7152 * hz.g + 0.0722 * hz.b
			skm.set_shader_parameter("view", 0.75 / (env.tonemap_exposure * 1.4 * lum))
		var inside := 0
		var blocked := 0
		var total := 0
		var fovs := []
		n = 0
		while n <= f1:
			d.advance(DT)
			oval.sync(DT)
			if n < f0 - 6:
				n += 1
				continue
			var aim: Vector3 = (shot["aims"] as Array)[clampi(n - f0, 0, f1 - f0)]
			var dist := eye.distance_to(aim)
			var hfov := rad_to_deg(2.0 * atan(width * 0.5 / dist))
			cam.global_position = eye
			cam.look_at(aim, Vector3.UP)
			cam.fov = hfov
			var f := n - f0
			if f >= 0 and f % 2 == 0:
				var b: Vector3 = oval.ball.global_position
				var p := cam.unproject_position(b)
				if not cam.is_position_behind(b) and Rect2(Vector2.ZERO, Vector2(size)).has_point(p):
					inside += 1
				if _stand_blocks(eye, b):
					blocked += 1
				total += 1
				fovs.append(hfov)
				await RenderingServer.frame_post_draw
				var img := root.get_viewport().get_texture().get_image()
				img.save_png(out.path_join("%s_%04d.png" % [shot["name"], f / 2]))
			else:
				await process_frame
			n += 1
		fovs.sort()
		print("SHOT %s %dx%d eye %s width %.0f m | ball in picture %d/%d | stand blocks the ball %d | lens %.1f-%.1f deg across" % [
				shot["name"], size.x, size.y, eye, width, inside, total, blocked, fovs[0], fovs[-1]])
		oval.queue_free()
		await process_frame
	quit()


## True when the stand's rake rises above the sight line from the eye to `p` (sampled).
func _stand_blocks(eye: Vector3, p: Vector3) -> bool:
	for i in range(1, 40):
		var u := float(i) / 40.0
		var q := eye.lerp(p, u)
		# How far out the point is, as a fraction from the boundary ellipse.
		var r := Vector2(q.x / HALF_LEN, q.z / HALF_WID).length()
		if r <= 1.0:
			continue
		var ang := atan2(q.z / HALF_WID, q.x / HALF_LEN)
		var bx := cos(ang) * HALF_LEN
		var bz := sin(ang) * HALF_WID
		var out := Vector2(q.x - bx, q.z - bz).length()
		var into := out - FENCE
		if into < 0.0:
			if q.y < 1.2:
				return true
			continue
		if into > STAND_DEPTH:
			continue
		var rake := 1.2 + (STAND_RISE - 1.2) * into / STAND_DEPTH
		if q.y < rake - 0.05:
			return true
	return false


## Mean brightness (0-1) of the grass pixels (green the strongest channel) in the picture's
## lower half: bare turf, stripes and all, without the men, lines or stands.
func _grass(img: Image) -> float:
	var sum := 0.0
	var k := 0
	for y in range(img.get_height() / 2, img.get_height(), 4):
		for x in range(0, img.get_width(), 4):
			var c := img.get_pixel(x, y)
			if c.g > c.r * 1.3 and c.g > c.b * 1.3:
				sum += c.get_luminance()
				k += 1
	return sum / maxf(1.0, k)


func _make_clouds() -> void:
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


## Rule 2.80 (sky light, a fine day) and 2.81 (AgX, contrast 1.1, saturation 1.2), as the look
## prototype (capture_look3d.gd "sky+agxtv") sets them.
func _look(oval, expo: float) -> void:
	var env: Environment = oval._env
	oval.turf.apply("perfect", "day")
	var sm := ShaderMaterial.new()
	sm.shader = load("res://tools/visual/look3d_sky.gdshader")
	sm.set_shader_parameter("energy", 1.4)
	sm.set_shader_parameter("clouds_tex", _clouds)
	sm.set_shader_parameter("cover", 0.32)
	sm.set_shader_parameter("cloud_lit", Color(1, 1, 1))
	sm.set_shader_parameter("cloud_dark", Color(0.62, 0.66, 0.74))
	sm.set_shader_parameter("sun_halo", 0.35)
	var sky := Sky.new()
	sky.sky_material = sm
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	env.sky = sky
	env.background_mode = Environment.BG_SKY
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_sky_contribution = 1.0
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	oval._sun.light_energy = 1.15
	oval._sun.light_color = Color(1.0, 0.95, 0.86)
	oval._sun.directional_shadow_max_distance = 320.0
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = expo
	env.adjustment_enabled = true
	env.adjustment_contrast = 1.1
	env.adjustment_saturation = 1.2
