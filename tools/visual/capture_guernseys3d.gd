extends SceneTree
## Every club's home guernsey on the 3D match player (the MetaHuman body), filmed front and back at
## chest height, for the guernsey boards (our render beside the club's real guernsey).
##   godot --path . --script tools/visual/capture_guernseys3d.gd -- OUTDIR [CLUB,CLUB,...|all] [rest|idle] [debug shader]
## Each club gets one man in its home guernsey (number 7), standing alone. pose "rest" (default)
## films him in the body's rest pose, arms out from the sides as a shop photo lays a guernsey
## flat; "idle" films the game's standing pose. Files: <CLUB>_front.png, <CLUB>_back.png (torso,
## 0.62 m across), <CLUB>_side.png, <CLUB>_full.png (the whole man from the front).
## The look is rule 2.80-2.81's fine day, as capture_builds3d.gd sets it.

const GLB := "res://assets/oval3d/player_mh.glb"
const CLUBS := ["ADE", "BRL", "CAR", "COL", "ESS", "FRE", "GEE", "GCS", "GWS", "HAW", "MEL", "NTH",
		"PAD", "RIC", "STK", "SYD", "TAS", "CANB", "WCE", "WBD"]


func _initialize() -> void:
	_run.call_deferred()
	create_timer(900.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var clubs: Array = CLUBS if args.size() < 2 or str(args[1]) == "all" else Array(str(args[1]).split(","))
	var pose := str(args[2]) if args.size() > 2 else "rest"
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.use_debanding = true
	var size := Vector2i(800, 1100)
	root.size = size
	DisplayServer.window_set_size(size)
	var O3 = load("res://scripts/ui/match/Oval3D.gd")
	O3.player_glb = GLB
	O3.loops_glb = GLB
	O3.hair_glb = "res://__no_hair_shells__.glb"
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("MEL", gdb.club_list("MEL"), true, "MEL"),
			Squad_.new("FRE", gdb.club_list("FRE"), false, "FRE"), 31).run()
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, "MEL", "FRE")
	for p in oval.players + oval.umpires:
		(p["node"] as Node3D).visible = false
	var scene: PackedScene = load(GLB)
	var men := []
	for i in range(clubs.size()):
		var club := str(clubs[i])
		var km: ShaderMaterial = oval._kit(gdb.club_guernsey(club))
		if args.size() > 3 and ResourceLoader.exists(str(args[3])):
			km.shader = load(str(args[3]))   # a debug copy of the shader (my own checks)
		var p: Dictionary = oval._player(scene, km, gdb.club_colours(club))
		oval._number(p, 7)
		oval.look(p, {"skin": 1, "hair": 1})
		var n: Node3D = p["node"]
		n.global_position = Vector3((i - (clubs.size() - 1) * 0.5) * 2.0, 0.0, 0.0)
		n.rotation.y = 0.0
		var ap: AnimationPlayer = p["anim"]
		if pose == "idle":
			ap.play("idle")
			ap.advance(0.4)
		else:
			ap.stop()
			(p["skel"] as Skeleton3D).reset_bone_poses()
		(p["ring"] as Node3D).visible = false
		men.append(p)
	var cam: Camera3D = oval.camera
	cam.keep_aspect = Camera3D.KEEP_WIDTH
	await process_frame
	await process_frame
	for i in range(men.size()):
		var skel: Skeleton3D = men[i]["skel"]
		var chest := _bone(skel, ["spine_04", "spine_05", "spine_03", "spine3", "Spine2", "chest"])
		var hips := _bone(skel, ["pelvis", "hips", "Hips"])
		var mid := Vector3(chest.x, 1.30, chest.z)
		var at: Vector3 = (men[i]["node"] as Node3D).global_position
		var views := {
			"front": [mid + Vector3(0, 0, 6.0), mid, 0.62],
			"back": [mid + Vector3(0, 0, -6.0), mid, 0.62],
			"side": [mid + Vector3(6.0, 0, 0), mid, 0.62],
			"full": [at + Vector3(0, 1.0, 8.0), at + Vector3(0, 1.0, 0), 1.75],
		}
		# Close-ups of each armhole's front (the trim edge), a quarter-turn round from the front.
		for sd in [["armR", "upperarm_r"], ["armL", "upperarm_l"]]:
			var sh := _bone(skel, [sd[1]])
			var aim := Vector3(sh.x * 0.8 + chest.x * 0.2, sh.y - 0.08, sh.z + 0.06)
			views[sd[0]] = [aim + Vector3(signf(sh.x - chest.x) * 3.0, 0, 4.0), aim, 0.30]
		for v in views:
			var eye: Vector3 = views[v][0]
			var aim: Vector3 = views[v][1]
			cam.global_position = eye
			cam.look_at(aim, Vector3.UP)
			cam.fov = rad_to_deg(2.0 * atan(float(views[v][2]) * 0.5 / eye.distance_to(aim)))
			for j in range(men.size()):
				(men[j]["node"] as Node3D).visible = j == i
			for w in range(4):
				await process_frame
			await RenderingServer.frame_post_draw
			root.get_viewport().get_texture().get_image().save_png(out.path_join("%s_%s.png" % [clubs[i], v]))
		print("CLUB %s chest %s hips %s" % [clubs[i], chest, hips])
	print("GUERNSEYS done")
	quit()


func _bone(skel: Skeleton3D, names: Array) -> Vector3:
	for nm in names:
		var b := skel.find_bone(str(nm))
		if b >= 0:
			return skel.global_transform * skel.get_bone_global_pose(b).origin
	return skel.global_position + Vector3(0, 1.2, 0)
