extends SceneTree
## PROTOTYPE (row 202, 3D view plan step 2e, the cameras): camera options on the 3D oval, filmed
## for the director to choose between. Nothing here is the game's camera until he picks one.
##   godot --path . --script tools/visual/capture_cameras3d.gd -- OUTDIR CONFIG.json
## CONFIG: {"seed": 31, "expo": 1.0, "turf": 0.32, "cams": {NAME: CAM, ...}, "edits": [EDIT, ...]}
## CAM:    {"eye": [x, y, z], "width": 40.0, "smooth": 0.5, "aim_y": 1.0, "aim": "ball"}
## EDIT:   {"name": "A", "size": [w, h], "cuts": [CUT, ...]}
## CUT:    {"cam": NAME, "from": s, "to": s, "rate": 1.0, "who": token id (aim "player"),
##          "pauses": 2.0 (real footy's pauses play this many times faster, as the match view's
##          MatchDirector.PAUSE_PLAY; default 1), "eye": [x, y, z] (stand the camera here instead)}
## The older form {"t0", "dur", "shots": [CAM + "name", "size"]} is still read: each shot is an
## edit of one cut.
## Each camera works the way a real broadcast camera does: it stands still on its mount (eye, in
## metres: x up the ground, y up, z across; +z is the near wing) and only pans, tilts and zooms.
## It aims at the ball, or at one player (aim "player", the cut's "who"), averaged over `smooth`
## seconds each side as an operator's hand smooths it, and zooms so `width` metres across the
## picture are in shot at what it aims at.
## An edit is the TV picture: its cuts play one after another, each from its own camera. A cut may
## go back in time (a replay) and may run slow ("rate" 0.5 is half speed). Times are seconds of
## the match as the game plays it back. Every frame is 1/30 s of the picture (real speed at rate
## 1). The match always ticks in 1/120 s steps, so a slow cut plays exactly the same football.
## Fremantle v St Kilda (seed). Pass 1 plays the director and the oval without drawing and logs
## where the ball and every player are; pass 2 plays them again for each cut and films it from the
## logged aim. For every cut it prints how often the ball is inside the picture and how often the
## stands stand between the camera and the ball (the line of sight, tested against the stand's
## rake), and writes OUTDIR/NAME_cuts.json (each cut's first and last frame).
## The look is rule 2.80-2.81's fine day (sky light, AgX with the TV grade); not the question.

const DT := 1.0 / 120.0
const HALF_LEN := 86.3
const HALF_WID := 67.4
const FENCE := 6.0
const STAND_DEPTH := 34.0
const STAND_RISE := 24.0
var _clouds: NoiseTexture2D


func _initialize() -> void:
	_run.call_deferred()
	create_timer(3000.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(str(args[1])))
	var seed := int(cfg.get("seed", 31))
	var cams: Dictionary = cfg.get("cams", {})
	var edits: Array = cfg.get("edits", [])
	if cfg.has("shots"):
		var t0 := float(cfg.get("t0", 30.0))
		for shot in cfg["shots"]:
			cams[shot["name"]] = shot
			edits.append({"name": shot["name"], "size": shot["size"],
					"cuts": [{"cam": shot["name"], "from": t0, "to": t0 + float(cfg.get("dur", 20.0))}]})
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.use_debanding = true
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), seed).run()

	# Pass 1: the ball's place and every player's place each step (the oval synced, nothing
	# drawn), kept only around the cuts.
	var last := 0.0
	var keep := {}
	for e in edits:
		for c in e["cuts"]:
			var sm := float((cams[c["cam"]] as Dictionary).get("smooth", 0.5))
			last = maxf(last, float(c["to"]) + sm)
			for f in range(int((float(c["from"]) - sm) / DT) - 2, int((float(c["to"]) + sm) / DT) + 3):
				keep[f] = true
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	var balls := {}
	var men := {}
	var n := 0
	while n <= int(last / DT) + 2 and not d.idle():
		d.advance(DT)
		oval.sync(DT)
		if keep.has(n):
			balls[n] = oval.ball.global_position
			var at := []
			for p in oval.players:
				at.append((p["node"] as Node3D).global_position)
			men[n] = at
		n += 1
	print("PASS1 %d steps (%.1f s)" % [n, n * DT])
	oval.queue_free()
	await process_frame

	_make_clouds()
	await _clouds.changed
	for e in edits:
		var sz: Array = e["size"]
		var size := Vector2i(int(sz[0]), int(sz[1]))
		root.size = size
		DisplayServer.window_set_size(size)
		var frame := 0
		var marks := []
		for c in e["cuts"]:
			var cam_cfg: Dictionary = cams[c["cam"]]
			var a := int(float(c["from"]) / DT)
			var b := int(float(c["to"]) / DT)
			var rate := float(c.get("rate", 1.0))
			var pauses := float(c.get("pauses", 1.0))
			var due := 0.0
			var aims := _aims(cam_cfg, c, a, b, balls, men)
			d = load("res://scripts/ui/match/MatchDirector.gd").new()
			d.setup(res, res["events"])
			oval = load("res://scripts/ui/match/Oval3D.gd").new()
			root.add_child(oval)
			oval.build(d, "FRE", "STK")
			_look(oval, float(cfg.get("expo", 1.0)))
			# A cut may stand its camera somewhere else ("eye" on the cut: another mount of the same
			# kind, e.g. the wing camera at a 50 m line when the centre one's view of a man is blocked).
			var eye_a: Array = c.get("eye", cam_cfg["eye"])
			var eye := Vector3(float(eye_a[0]), float(eye_a[1]), float(eye_a[2]))
			var width := float(cam_cfg.get("width", 40.0))
			var cam: Camera3D = oval.camera
			cam.keep_aspect = Camera3D.KEEP_WIDTH
			# Nobody within 20 m of the lens is drawn: the camera spots sit just above the seats, and
			# supporters in front of the lens never block the gameplay picture (rule 2.101).
			cam.near = float(cam_cfg.get("near", 20.0))
			n = 0
			while n < a - 8:
				d.advance(DT)
				oval.sync(DT)
				n += 1
			await _expose(oval, cam, eye, aims[0], width, float(cfg.get("turf", 0.32)))
			while n < a:
				d.advance(DT)
				oval.sync(DT)
				n += 1
			var first := frame
			var inside := 0
			var blocked := 0
			var total := 0
			var fovs := []
			while n <= b:
				d.advance(DT)
				oval.sync(DT)
				var aim: Vector3 = aims[clampi(n - a, 0, b - a)]
				var hfov := rad_to_deg(2.0 * atan(width * 0.5 / eye.distance_to(aim)))
				cam.global_position = eye
				cam.look_at(aim, Vector3.UP)
				cam.fov = hfov
				# A frame every 1/30 s of the picture: `rate` seconds of play each second, `pauses`
				# times that in one of real footy's pauses (as the match view plays them).
				due -= 1.0
				if due <= 0.0:
					due += 4.0 * rate * (pauses if d.pausing() else 1.0)
					var bp: Vector3 = oval.ball.global_position
					var p := cam.unproject_position(bp)
					if not cam.is_position_behind(bp) and Rect2(Vector2.ZERO, Vector2(size)).has_point(p):
						inside += 1
					if _stand_blocks(eye, bp):
						blocked += 1
					total += 1
					fovs.append(hfov)
					await RenderingServer.frame_post_draw
					root.get_viewport().get_texture().get_image().save_png(
							out.path_join("%s_%04d.png" % [e["name"], frame]))
					frame += 1
				else:
					await process_frame
				n += 1
			fovs.sort()
			marks.append({"cam": c["cam"], "from": c["from"], "to": c["to"], "rate": rate,
					"first": first, "last": frame - 1})
			print("CUT %s %s %.2f-%.2f s x%.2f frames %d-%d | ball in picture %d/%d | stand blocks the ball %d | lens %.1f-%.1f deg" % [
					e["name"], c["cam"], float(c["from"]), float(c["to"]), rate, first, frame - 1,
					inside, total, blocked, fovs[0], fovs[-1]])
			oval.queue_free()
			await process_frame
		var fa := FileAccess.open(out.path_join("%s_cuts.json" % e["name"]), FileAccess.WRITE)
		fa.store_string(JSON.stringify(marks))
		fa.close()
	quit()


## The camera's aim each step of the cut: the ball, or the cut's player ("who"), averaged over the
## camera's `smooth` seconds each side, at aim_y metres up.
func _aims(cam_cfg: Dictionary, c: Dictionary, a: int, b: int, balls: Dictionary, men: Dictionary) -> Array:
	var k := int(float(cam_cfg.get("smooth", 0.5)) / DT)
	var who := int(c.get("who", -1)) if str(cam_cfg.get("aim", "ball")) == "player" else -1
	var aims := []
	for f in range(a, b + 1):
		var s := Vector3.ZERO
		var m := 0
		for g in range(f - k, f + k + 1):
			if not balls.has(g):
				continue
			s += (men[g] as Array)[who] if who >= 0 else balls[g]
			m += 1
		s /= float(maxi(1, m))
		s.y = float(cam_cfg.get("aim_y", 1.0))
		# An operator behind the goals stops tilting down at the goal line: the ball goes on
		# under the picture into the crowd, the camera stays on the ground.
		var cx := float(cam_cfg.get("clamp_x", 999.0))
		s.x = clampf(s.x, -cx, cx)
		aims.append(s)
	return aims


## Exposure set by the open grass, as the look prototype sets it (TURF=0.32): from the cut's first
## aim, the grass read four times and the exposure moved; the seen sky held at the fine day's
## horizon brightness (0.75) at that exposure, as the look prototype's _sky_view does.
func _expose(oval, cam: Camera3D, eye: Vector3, aim0: Vector3, width: float, turf: float) -> void:
	cam.global_position = eye
	cam.look_at(aim0, Vector3.UP)
	cam.fov = rad_to_deg(2.0 * atan(width * 0.5 / eye.distance_to(aim0)))
	var env: Environment = oval._env
	for it in range(5):
		for w in range(3):
			await process_frame
		await RenderingServer.frame_post_draw
		var got := _grass(root.get_viewport().get_texture().get_image())
		if it < 4:
			env.tonemap_exposure *= pow(turf / maxf(got, 0.01), 1.6)
		var skm: ShaderMaterial = env.sky.sky_material
		var hz: Color = RenderingServer.shader_get_parameter_default(skm.shader.get_rid(), "horizon")
		var lum := 0.2126 * hz.r + 0.7152 * hz.g + 0.0722 * hz.b
		skm.set_shader_parameter("view", 0.75 / (env.tonemap_exposure * 1.4 * lum))


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
