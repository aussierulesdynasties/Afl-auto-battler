extends SceneTree
## PROTOTYPE (row 202, 3D view plan step 2a): the rendering foundation's options on the 3D oval,
## for the director to choose between. The options live here, not in the game: nothing is the
## settled look until he picks it (rule 2.78's freeze).
##   godot --path . --script tools/visual/capture_look3d.gd -- OUTDIR LOOKS [WEATHER] [SLOT]
## LOOKS is a comma list of options (see _apply); an option may join parts with "+", e.g. sky+agx. A seeded Fremantle v St Kilda match is
## played until the phone camera (PitchView's aim_end) holds at least MIN_IN_VIEW men with the
## ball among them, read from the logged positions, then that same moment is saved under each
## option from the phone camera, the wide (wing) camera and the close camera. For each frame it
## prints the mean brightness of the turf round the ball, so options are compared at the same
## exposure, not one simply brighter.

## The oval's share of the match screen on a 1080 x 2400 phone (measured: 506 x 621 at 540 x 1200).
const SIZE := Vector2i(1012, 1242)
const WIDE := Vector2i(1600, 900)
const DT := 1.0 / 24.0
const UP := 18.0
const BACK := 28.0
const MIN_IN_VIEW := 10
## The moment is taken with the ball out on a wing (at least this far from the centre line
## across the ground, and not in a goal square), so a stand's shade can reach the play.
const WING_Z := 38.0
const MID_X := 60.0
var _wing_sign := 1.0
const MAX_T := 300.0


func _initialize() -> void:
	_run.call_deferred()
	create_timer(900.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://look3d"
	var looks := (str(args[1]) if args.size() > 1 else "today").split(",")
	var weather := str(args[2]) if args.size() > 2 else "perfect"
	var slot := str(args[3]) if args.size() > 3 else "day"
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	_size(SIZE)
	# Pass 1, the log: every frame's men in the phone view and where the ball is (the camera is
	# placed and projected without drawing). The moment is the frame with the most men in view
	# while the ball is out on a wing.
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	var played := 0.0
	var want := -1.0
	var best := 0
	while played < MAX_T:
		d.advance(DT)
		oval.sync(DT)
		oval.aim_end(UP, BACK)
		played += DT
		if played < 6.0:
			continue
		var b: Vector3 = oval.ball.global_position
		if absf(b.z) > WING_Z and absf(b.x) < MID_X:
			var n := _in_view(oval)
			if n > best:
				best = n
				want = played
				_wing_sign = signf(b.z)
	oval.queue_free()
	await process_frame
	# Pass 2: the same match again, drawn, to that moment.
	d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	played = 0.0
	while played < want - DT * 0.5:
		d.advance(DT)
		oval.sync(DT)
		oval.aim_end(UP, BACK)
		played += DT
		await process_frame
	var bp: Vector2 = d.ball["pos"]
	print("MOMENT (wing %+.0f): %.2f s, %d men in the phone view, ball at (%.1f, %.1f)" % [_wing_sign, played, _in_view(oval), bp.x, bp.y])
	for look in looks:
		_reset(oval, weather, slot)
		for part in look.split("+"):
			_apply(oval, part)
		await _match_exposure(oval)
		for cam in ["phone", "wide", "close"]:
			_size(WIDE if cam == "wide" else SIZE)
			if cam == "phone":
				oval.aim_end(UP, BACK)
			elif cam == "wide":
				oval.aim_wing(UP, BACK * 1.3)
			else:
				oval.aim_close()
			for i in range(3):
				await process_frame
			await _save(oval, out, "look_%s_%s_%s_%s" % [look, slot, weather, cam])
	quit()


func _size(s: Vector2i) -> void:
	root.size = s
	DisplayServer.window_set_size(s)


## Men (players) whose middle projects inside the phone frame, the ball's man among them.
func _in_view(oval) -> int:
	var cam: Camera3D = oval.camera
	var vp := Rect2(Vector2.ZERO, Vector2(root.size))
	var n := 0
	for p in oval.players:
		var node: Node3D = p["node"]
		var at := node.global_position + Vector3(0, 1.0, 0)
		if cam.is_position_behind(at):
			continue
		if vp.has_point(cam.unproject_position(at)):
			n += 1
	var b: Vector3 = oval.ball.global_position
	if cam.is_position_behind(b) or not vp.has_point(cam.unproject_position(b)):
		return 0
	return n


## Today's look for the weather and slot, from scratch (the options below change it).
func _reset(oval, weather: String, slot: String) -> void:
	var env: Environment = oval._env
	env.background_mode = Environment.BG_COLOR
	env.sky = null
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.fog_enabled = false
	env.glow_enabled = false
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_white = 1.0
	env.adjustment_enabled = false
	_stand_shadow(oval, false)
	oval.get_viewport().msaa_3d = Viewport.MSAA_DISABLED
	oval.get_viewport().screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED
	oval._sun.directional_shadow_max_distance = 160.0
	oval.turf.apply(weather, slot)


func _stand_shadow(oval, on: bool) -> void:
	for c in oval.get_children():
		if c is MeshInstance3D and c.material_override is ShaderMaterial \
				and str(c.material_override.shader.resource_path).ends_with("oval3d_crowd.gdshader"):
			c.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED if on \
					else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


## The sky the light comes from: blue above, the sun's disc, and below the horizon the colour
## the grass and stands throw back up (the bounce light under a player's chin and arms).
## The sky's strength sets the ambient light: with the sky giving all of it, Godot ignores
## ambient_light_energy, so the sky shader's own energy carries it.
func _sky(oval, strength: float) -> void:
	var env: Environment = oval._env
	var sm := ShaderMaterial.new()
	sm.shader = load("res://tools/visual/look3d_sky.gdshader")
	sm.set_shader_parameter("energy", strength)
	var sky := Sky.new()
	sky.sky_material = sm
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	env.sky = sky
	env.background_mode = Environment.BG_SKY
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_sky_contribution = 1.0
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY


## Ambient strength for the sky options, from the command line (AMB=1.2) while tuning.
func _amb(fallback: float) -> float:
	return float(OS.get_environment("AMB")) if OS.get_environment("AMB") != "" else fallback


## With TURF=0.32 on the command line, the exposure is set so bare sunlit turf on the ball's row
## reads that brightness in the phone frame (four passes, the tonemapper is not linear): tone options are
## then compared at the same brightness of grass, not one simply brighter.
func _match_exposure(oval) -> void:
	if OS.get_environment("TURF") == "":
		return
	var want := float(OS.get_environment("TURF"))
	var env: Environment = oval._env
	_size(SIZE)
	oval.aim_end(UP, BACK)
	for i in range(4):
		for f in range(3):
			await process_frame
		await RenderingServer.frame_post_draw
		var img := root.get_viewport().get_texture().get_image()
		var b: Vector3 = oval.ball.global_position
		# Bare turf on the ball's screen row, 500 px towards the middle (the patch at the ball
		# holds men and their rings, which the tonemappers treat differently from grass).
		var c: Vector2 = oval.camera.unproject_position(Vector3(b.x, 0.0, b.z))
		var got := _patch(img, Vector2(clampf(c.x - 500.0, 60.0, img.get_width() - 60.0), c.y))
		env.tonemap_exposure *= pow(want / maxf(got, 0.01), 1.6)
	print("EXPOSURE %.3f for turf %.2f" % [env.tonemap_exposure, want])
	await _true_rings(oval)


## The club rings are unlit paint, a marker, not part of the lit world: exposure and the tonemapper
## would wash them (St Kilda red to peach at AgX's exposure). The game will draw them in their exact
## club colour whatever the tone, so here each club's ring colour is corrected until the screen
## shows the club colour (read at the ring's front edge, between the man and the camera).
func _true_rings(oval) -> void:
	var cam: Camera3D = oval.camera
	var vp := Rect2(Vector2(4, 4), Vector2(root.size) - Vector2(8, 8))
	var by_club := {}
	for p in oval.players:
		var mat: StandardMaterial3D = p["ring"].material_override
		if not mat.has_meta("club"):
			mat.set_meta("club", mat.albedo_color)
		mat.albedo_color = mat.get_meta("club")
		var key: String = (mat.get_meta("club") as Color).to_html()
		if not by_club.has(key):
			by_club[key] = {"ats": [], "near": INF, "mats": []}
		by_club[key]["mats"].append(mat)
		# Points along the ring's front arc, from the club's man nearest the camera.
		var node: Node3D = p["node"]
		var to_cam := cam.global_position - node.global_position
		to_cam.y = 0.0
		var ats := []
		for deg in range(-50, 51, 10):
			var at := node.global_position + to_cam.normalized().rotated(Vector3.UP, deg_to_rad(deg)) * 0.635 					+ Vector3(0, 0.03, 0)
			if not cam.is_position_behind(at) and vp.has_point(cam.unproject_position(at)):
				ats.append(at)
		if ats.size() >= 6 and to_cam.length() < by_club[key]["near"]:
			by_club[key]["near"] = to_cam.length()
			by_club[key]["ats"] = ats
	# The club colour is scaled as a whole (its hue kept) and the scale found by halving: below the
	# tonemapper's shoulder the hue then comes through, only the brightness needs matching.
	for key in by_club:
		by_club[key]["lo"] = 0.02
		by_club[key]["hi"] = 1.0
	for i in range(10):
		for key in by_club:
			var c: Dictionary = by_club[key]
			var sc := sqrt(c["lo"] * c["hi"])
			c["s"] = sc
			var club: Color = c["mats"][0].get_meta("club")
			for m in c["mats"]:
				m.albedo_color = Color(club.r * sc, club.g * sc, club.b * sc)
		for f in range(3):
			await process_frame
		await RenderingServer.frame_post_draw
		var img := root.get_viewport().get_texture().get_image()
		for key in by_club:
			var c: Dictionary = by_club[key]
			var sum := Color(0, 0, 0, 0)
			var k := 0
			for at in c["ats"]:
				var px := img.get_pixelv(Vector2i(cam.unproject_position(at)))
				if px.g >= maxf(px.r, px.b):
					continue
				sum += px
				k += 1
			if k == 0:
				continue
			var got := sum / float(k)
			var want: Color = c["mats"][0].get_meta("club")
			if got.get_luminance() > want.get_luminance():
				c["hi"] = c["s"]
			else:
				c["lo"] = c["s"]
			if i == 9:
				print("RING %s wants %s, shows %s (scale %.3f)" % [key, want.to_html(false), got.to_html(false), c["s"]])


func _apply(oval, look: String) -> void:
	var env: Environment = oval._env
	var sun: DirectionalLight3D = oval._sun
	match look:
		"today":
			pass
		"sky":
			# B: the sky lights the ground and the men (ambient and reflections from it).
			_sky(oval, _amb(1.4))
			sun.light_energy = 1.15
			sun.light_color = Color(1.0, 0.95, 0.86)
		"skyshade":
			# C: as B, with a mid-afternoon sun lower in the west, and the stands cast their
			# shadow across the near wing and pocket.
			_sky(oval, _amb(1.4))
			sun.light_energy = 1.2
			# The sun 22 degrees up behind the stand on the ball's wing (about 4.30 pm in
			# winter): the stand's top, 24 m up and 34 m back from the fence, shades about
			# 25 m of that wing.
			var e := deg_to_rad(22.0)
			var h := Vector3(0.3, 0.0, -_wing_sign).normalized()
			sun.global_basis = Basis.looking_at(h * cos(e) + Vector3(0.0, -sin(e), 0.0), Vector3.UP)
			sun.light_color = Color(1.0, 0.9, 0.76)
			sun.directional_shadow_max_distance = 320.0
			_stand_shadow(oval, true)
		# The picture's tone (post-processing), on top of a light above. Godot's tonemappers turn
		# the scene's light into screen colour: filmic (today), ACES (punchy, saturated), AgX
		# (natural, keeps bright colours from blowing out), and AgX with a broadcast grade.
		"filmic":
			env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
		"aces":
			env.tonemap_mode = Environment.TONE_MAPPER_ACES
		"agx":
			env.tonemap_mode = Environment.TONE_MAPPER_AGX
		"agxtv":
			env.tonemap_mode = Environment.TONE_MAPPER_AGX
			env.adjustment_enabled = true
			env.adjustment_contrast = 1.1
			env.adjustment_saturation = 1.2
		_:
			push_error("unknown look " + look)


func _save(oval, out: String, name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(out.path_join(name + ".png"))
	# The turf round the ball, and on the same screen row 500 px towards the middle of the
	# ground: mean brightness (0-1) of a patch at each (in option C the first is in the stand's
	# shade and the second in the sun).
	var cam: Camera3D = oval.camera
	var b: Vector3 = oval.ball.global_position
	var c := cam.unproject_position(Vector3(b.x, 0.0, b.z))
	var at := _patch(img, c)
	var mid := _patch(img, Vector2(clampf(c.x - 500.0, 60.0, img.get_width() - 60.0), c.y))
	print("SAVED %s  turf at the ball %.3f, 500 px in %.3f" % [name, at, mid])


func _patch(img: Image, c: Vector2) -> float:
	var r := Rect2i(Vector2i(c) - Vector2i(60, 30), Vector2i(120, 60)).intersection(
			Rect2i(Vector2i.ZERO, img.get_size()))
	var sum := 0.0
	var k := 0
	for y in range(r.position.y, r.end.y, 2):
		for x in range(r.position.x, r.end.x, 2):
			sum += img.get_pixel(x, y).get_luminance()
			k += 1
	return sum / maxf(1.0, k)
