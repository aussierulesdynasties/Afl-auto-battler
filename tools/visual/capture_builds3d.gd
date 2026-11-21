extends SceneTree
## PROTOTYPE (row 202, 3D view plan step 2d, builds and faces): the MetaHuman footballer at each
## man's real height and weight, with a face of his own (Oval3DBuild), filmed for the director.
##   godot --path . --script tools/visual/capture_builds3d.gd -- OUTDIR MODE [flat]
## MODE "lineup": real Fremantle and St Kilda men standing in a row on the centre square, filmed
##   from the front at chest height and from above-behind (stills, my own self-check and boards).
##   "flat" draws every man as the one average body and the base face, for a before/after board.
## MODE "match": Fremantle v St Kilda (seed 31), 20 s of the first quarter at real speed, from the
##   main camera (rule 2.93: centre line, 15 m up, 25 m back from the boundary, a third of the
##   ground across) and from a close test view that follows the ball (not a game camera).
##   "heads": Melbourne v Fremantle from the first bounce, and the close test view follows Max Gawn
##   (MEL_11, his own Tripo head) instead of the ball, 3 m of ground across at his head height.
## The look is rule 2.80-2.81's fine day, as capture_cameras3d.gd sets it.

const DT := 1.0 / 60.0
const HALF_WID := 67.4
const GLB := "res://assets/oval3d/player_mh.glb"
## The men in the line-up, shortest to tallest; club and surname as in players_enriched_2026.
const LINEUP := [["FRE", "Isaiah", "Dudley"], ["STK", "Liam", "Henry"], ["STK", "Nasiah", "Wanganeen-Milera"],
		["FRE", "Caleb", "Serong"], ["STK", "Rowan", "Marshall"], ["FRE", "Sean", "Darcy"], ["FRE", "Mason", "Cox"]]
## "heads": Gawn, Pickett and Langford in their own Tripo heads (rule 2.99) beside Darcy, still on the MetaHuman head.
const LINEUP_HEADS := [["MEL", "Max", "Gawn"], ["MEL", "Kysaiah", "Pickett"], ["MEL", "Harvey", "Langford"], ["FRE", "Sean", "Darcy"]]
var _lineup_men: Array = LINEUP
var _home := "FRE"
var _away := "STK"
## The man the close view follows in "match heads" (player id); "" follows the ball.
var _follow := ""
var _clouds: NoiseTexture2D
## "gen_avg" / "gen_real": five 190 cm men with no weight on record (a generated player), drawn at
## the average weight for 190 cm (84.8 kg) or at five real 2026 weights of 190 cm men (of the 20
## listed: 74, 80, 85, 89, 99 kg, the lightest, quartiles and heaviest). Looks from the line-up.
var _gen := ""
const GEN_REAL := [74.0, 80.0, 85.0, 89.0, 99.0]


func _initialize() -> void:
	_run.call_deferred()
	create_timer(1500.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var mode := str(args[1])
	var flat := args.size() > 2 and str(args[2]) == "flat"
	_gen = str(args[2]) if args.size() > 2 and str(args[2]).begins_with("gen") else ""
	if args.size() > 2 and str(args[2]) == "heads":
		_lineup_men = LINEUP_HEADS
		# LINEUP="MEL:Changkuoth:Jiath,MEL:Jake:Bowey" films those men instead of the four above.
		if OS.get_environment("LINEUP") != "":
			_lineup_men = []
			for m in OS.get_environment("LINEUP").split(","):
				_lineup_men.append(m.split(":"))
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.use_debanding = true
	var O3 = load("res://scripts/ui/match/Oval3D.gd")
	O3.player_glb = GLB
	O3.loops_glb = GLB
	# As capture_look3d.gd draws the MetaHuman: no shells (they fit the old head), the painted crop.
	O3.hair_glb = "res://__no_hair_shells__.glb"
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var heads := args.size() > 2 and str(args[2]) == "heads"
	_home = "MEL" if heads and mode == "match" else "FRE"
	_away = "FRE" if heads and mode == "match" else "STK"
	_follow = (OS.get_environment("FOLLOW") if OS.get_environment("FOLLOW") != "" else "MEL_11") if heads and mode == "match" else ""  # TEMP FOLLOW: the collar-join film of Cross
	var home_list: Array = gdb.club_list(_home)
	if _follow != "":  # TEMP FOLLOW: the followed man always makes the side (a copy of him rated top for selection only)
		home_list = home_list.duplicate()
		for i in range(home_list.size()):
			if str(home_list[i].get("id", "")) == _follow:
				home_list[i] = home_list[i].duplicate()
				home_list[i]["overall"] = 99.0
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new(_home, home_list, true, _home),
			Squad_.new(_away, gdb.club_list(_away), false, _away), 31).run()
	_make_clouds()
	await _clouds.changed
	if mode == "lineup":
		await _lineup(out, res, gdb, flat)
	else:
		await _match(out, res)
	quit()


func _lineup(out: String, res: Dictionary, gdb, flat: bool) -> void:
	var size := Vector2i(1600, 900)
	root.size = size
	DisplayServer.window_set_size(size)
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, _home, _away)
	_look(oval, 1.0)
	for p in oval.players + oval.umpires:
		(p["node"] as Node3D).visible = false
	var scene: PackedScene = load(GLB)
	var kits := {}
	for m in _lineup_men:
		if not kits.has(str(m[0])):
			kits[str(m[0])] = oval._kit(gdb.club_guernsey(str(m[0])))
	var men := []
	for i in range(_lineup_men.size() if _gen == "" else GEN_REAL.size()):
		var club := str(_lineup_men[i][0])
		var who := {}
		for pl in gdb.club_list(club):
			if str(pl.get("first", "")) == str(_lineup_men[i][1]) and str(pl.get("last", "")) == str(_lineup_men[i][2]):
				who = pl
				break
		var p: Dictionary = oval._player(scene, kits[club], gdb.club_colours(club))
		oval._dress(p, {"pid": str(who.get("id", "")), "num": int(who.get("num", -1))})
		if flat:
			Oval3DBuild.apply(p, GLB, {}, "")
		if _gen != "":
			Oval3DBuild.apply(p, GLB, {"height_cm": 190.0, "weight_kg": Oval3DBuild.avg_kg(190.0) if _gen == "gen_avg" else GEN_REAL[i]}, str(who.get("id", "")))
		var n: Node3D = p["node"]
		n.global_position = Vector3((i - ((_lineup_men.size() if _gen == "" else GEN_REAL.size()) - 1) * 0.5) * 1.3, 0.0, 0.0)
		n.rotation.y = 0.0
		var ap: AnimationPlayer = p["anim"]
		ap.play("idle")
		ap.advance(0.4)
		(p["ring"] as Node3D).visible = false
		men.append(p)
		print("MAN %s %s %s pid %s h %s w %s build %s leg %.3f" % [club, _lineup_men[i][1], _lineup_men[i][2], who.get("id", "?"),
				who.get("height_cm", "?"), who.get("weight_kg", "?"), p.get("build", {}), float(p.get("leg", 1.0))])
	var cam: Camera3D = oval.camera
	cam.keep_aspect = Camera3D.KEEP_WIDTH
	# Which way the men face: their front is +z or -z in the GLB; film both ends, label by file.
	var views := {
		"front": [Vector3(0, 1.25, 14.0), Vector3(0, 1.0, 0), 10.5],
		"back": [Vector3(0, 1.25, -14.0), Vector3(0, 1.0, 0), 10.5],
		"game": [Vector3(0, 15.0, 40.0), Vector3(0, 1.0, 0), 12.0],
	}
	await process_frame
	await process_frame
	# Each man's head from the front and three-quarter, 0.5 m across, at his own head height.
	for i in range(men.size()):
		var skel: Skeleton3D = men[i]["skel"]
		var h: Vector3 = skel.global_transform * skel.get_bone_global_pose(skel.find_bone("head")).origin + Vector3(0, 0.02, 0)
		views["head%d" % i] = [h + Vector3(0, 0.0, 3.0), h, 0.5]
		views["head%d_q" % i] = [h + Vector3(2.1, 0.0, 2.1), h, 0.5]
		views["head%d_b" % i] = [h + Vector3(1.8, 1.2, -2.1), h, 0.5]
		# His head and neck side on, level with his throat, 0.6 m across: the line from his collar to his chin.
		views["head%d_p" % i] = [h + Vector3(0.9, -0.1, 0.0), h + Vector3(0, -0.1, 0), 0.6]
		# Up under his chin from in front, 0.35 m across: the join under a beard, where the ground could show through.
		views["head%d_u" % i] = [h + Vector3(0, -0.75, 1.3), h + Vector3(0, -0.12, 0), 0.35]
		# His whole body alone from the front and the side, a 2.4 m tall frame (4.27 m wide at 16:9), my
		# own check of the kit and shape.
		var at: Vector3 = (men[i]["node"] as Node3D).global_position + Vector3(0, 1.1, 0)
		views["body%d" % i] = [at + Vector3(0, 0.0, 6.0), at, 4.27, i]
		views["body%d_s" % i] = [at + Vector3(6.0, 0.0, 0.0), at, 4.27, i]
		# The same two frames with nobody in them, so his outline can be cut out and measured.
		views["body%d_bg" % i] = [at + Vector3(0, 0.0, 6.0), at, 4.27, -1]
		views["body%d_s_bg" % i] = [at + Vector3(6.0, 0.0, 0.0), at, 4.27, -1]
		# His shorts alone from the front, the side and behind, 1.0 m across at his hips: how they hang.
		var hip: Vector3 = skel.global_transform * skel.get_bone_global_pose(skel.find_bone("pelvis")).origin + Vector3(0, -0.12, 0)
		views["shorts%d" % i] = [hip + Vector3(0, 0.0, 3.0), hip, 1.0, i]
		views["shorts%d_s" % i] = [hip + Vector3(3.0, 0.0, 0.0), hip, 1.0, i]
		views["shorts%d_b" % i] = [hip + Vector3(0, 0.0, -3.0), hip, 1.0, i]
	if OS.get_environment("CLIP") != "":  # TEMP CLIP: the collar-join film, each man jogging, his head and neck close
		for i in range(men.size()):
			var ap2: AnimationPlayer = men[i]["anim"]
			ap2.play("jog")
			ap2.pause()
			var sk: Skeleton3D = men[i]["skel"]
			for ang in [["q", Vector3(2.1, 0.0, 2.1)], ["p", Vector3(3.0, -0.1, 0.0)], ["b", Vector3(-1.8, 0.6, -2.4)]]:
				for k in range(90):
					ap2.seek(k / 30.0, true)
					for j in range(men.size()):
						(men[j]["node"] as Node3D).visible = j == i
					await process_frame
					var hb: Vector3 = sk.global_transform * sk.get_bone_global_pose(sk.find_bone("head")).origin + Vector3(0, -0.03, 0)
					cam.global_position = hb + ang[1]
					cam.look_at(hb, Vector3.UP)
					cam.fov = rad_to_deg(2.0 * atan(0.8 * 0.5 / ang[1].length()))
					await RenderingServer.frame_post_draw
					root.get_viewport().get_texture().get_image().save_png(out.path_join("clip%d_%s_%03d.png" % [i, ang[0], k]))
		print("CLIP done")
		return
	for v in views:
		var eye: Vector3 = views[v][0]
		var aim: Vector3 = views[v][1]
		cam.global_position = eye
		cam.look_at(aim, Vector3.UP)
		cam.fov = rad_to_deg(2.0 * atan(float(views[v][2]) * 0.5 / eye.distance_to(aim)))
		for j in range(men.size()):
			(men[j]["node"] as Node3D).visible = views[v].size() < 4 or int(views[v][3]) == j
		for w in range(4):
			await process_frame
		await RenderingServer.frame_post_draw
		root.get_viewport().get_texture().get_image().save_png(out.path_join("%s%s.png" % ["flat_" if flat else (_gen + "_" if _gen != "" else ""), v]))
	print("LINEUP done")


func _match(out: String, res: Dictionary) -> void:
	var t0 := 30.0 if _follow == "" else 0.0
	var dur := 20.0
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, _home, _away)
	var f0 := int(t0 / DT)
	var f1 := int((t0 + dur) / DT)
	var balls := []
	var n := 0
	var who := -1
	print("FOLLOW ", _follow)
	for i in range(oval.players.size()):
		if str(oval.players[i].get("pid", "")) == _follow and _follow != "":
			who = i
	print("FOLLOW index ", who)
	while n <= f1 and not d.idle():
		d.advance(DT)
		oval.sync(DT)
		balls.append(oval.ball.global_position if who < 0 else (oval.players[who]["node"] as Node3D).global_position)
		n += 1
	f1 = mini(f1, balls.size() - 1)
	oval.queue_free()
	await process_frame
	var aims := []
	for f in range(f0, f1 + 1):
		var a := Vector3.ZERO
		var c := 0
		for g in range(maxi(0, f - 30), mini(balls.size() - 1, f + 30) + 1):
			a += balls[g]
			c += 1
		a /= float(c)
		a.y = 1.0 if _follow == "" else 1.9
		aims.append(a)
	for shot in [["main", Vector2i(1080, 608), 57.0], ["close", Vector2i(1080, 608), 14.0 if _follow == "" else 3.0]]:
		var size: Vector2i = shot[1]
		root.size = size
		DisplayServer.window_set_size(size)
		d = load("res://scripts/ui/match/MatchDirector.gd").new()
		d.setup(res, res["events"])
		oval = load("res://scripts/ui/match/Oval3D.gd").new()
		root.add_child(oval)
		oval.build(d, _home, _away)
		_look(oval, 1.0)
		var cam: Camera3D = oval.camera
		cam.keep_aspect = Camera3D.KEEP_WIDTH
		n = 0
		while n <= f1:
			d.advance(DT)
			oval.sync(DT)
			if n < f0 - 6:
				n += 1
				continue
			var aim: Vector3 = aims[clampi(n - f0, 0, f1 - f0)]
			var eye := Vector3(0.0, 15.0, HALF_WID + 25.0) if shot[0] == "main" else aim + (Vector3(0.0, 3.0, 22.0) if _follow == "" else Vector3(0.0, 0.3, 7.0))
			cam.global_position = eye
			cam.look_at(aim, Vector3.UP)
			cam.fov = rad_to_deg(2.0 * atan(float(shot[2]) * 0.5 / eye.distance_to(aim)))
			var f := n - f0
			if f >= 0 and f % 2 == 0:
				await RenderingServer.frame_post_draw
				root.get_viewport().get_texture().get_image().save_png(out.path_join("%s_%04d.png" % [shot[0], f / 2]))
			else:
				await process_frame
			n += 1
		print("SHOT %s done" % shot[0])
		oval.queue_free()
		await process_frame


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


## Rule 2.80 (sky light, a fine day) and 2.81 (AgX, contrast 1.1, saturation 1.2).
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
	if OS.has_environment("SUN_ANGLE"):  # TEMP test
		oval._sun.light_angular_distance = float(OS.get_environment("SUN_ANGLE"))
	if OS.has_environment("SHADOW_DIST"):  # TEMP test
		oval._sun.directional_shadow_max_distance = float(OS.get_environment("SHADOW_DIST"))
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = expo
	env.adjustment_enabled = true
	env.adjustment_contrast = 1.1
	env.adjustment_saturation = 1.2
