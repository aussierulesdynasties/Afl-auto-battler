extends SceneTree
## A goal umpire held at chosen moments of his clips (row 202), filmed close from the front and
## from three-quarters: for checking his clothes and hands at each key pose in the game itself.
##   godot --path . --rendering-method mobile --script tools/visual/capture_crew_pose.gd -- OUTDIR CLIP T1,T2,...
## With CREW_FLAGS=furl,air he holds both flags, the cloth furled (0) to open (1), in still air
## (0) to streaming (1).
## Saves OUTDIR/<clip>_<t>_<front|quarter|back>.png.

const DT := 1.0 / 30.0


func _initialize() -> void:
	_run.call_deferred()
	create_timer(1200.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _shot(pv, out: String, name: String) -> void:
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	pv._vp3d.get_texture().get_image().save_png(out.path_join(name + ".png"))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var clip := str(args[1]) if args.size() > 1 else "goal_signal"
	var times := (str(args[2]) if args.size() > 2 else "0.36,0.62").split(",")
	DirAccess.make_dir_recursive_absolute(out)
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = Vector2i(700, 700)
	var pv = load("res://scripts/ui/PitchView.gd").new()
	pv.size = Vector2(700, 700)
	pv.three_d = true
	root.add_child(pv)
	res["home"] = "FRE"
	res["away"] = "STK"
	res["label"] = "Round 1"
	res["venue"] = "Alan Ray Oval"
	pv.setup(res)
	pv.set_speed(1.0)
	pv.play()
	pv.set_process(false)
	var oval = pv._oval3d
	var cam := Camera3D.new()
	cam.fov = 30.0
	oval.add_child(cam)
	for i in range(10):
		pv._process(DT)
	pv.pause() if pv.has_method("pause") else null
	var u: Dictionary = {}
	for x in oval.umpires:
		if str(x["role"]) == "goal":
			u = x
			break
	var ap: AnimationPlayer = u["anim"]
	var n: Node3D = u["node"]
	n.rotation.y = atan2(-n.position.x, -n.position.z)
	print("POSE clips: ", ap.get_animation_list().has(clip))
	# CREW_FLAGS=furl,air: both flags in his hands, the cloth set so.
	var fl := OS.get_environment("CREW_FLAGS")
	if fl != "":
		var fa := fl.split(",")
		var crew = load("res://scripts/ui/match/Oval3DCrew.gd")
		var flags: Dictionary = crew.flags(u["skel"], crew.glb_for(oval.player_glb))
		for s in flags.values():
			(s["node"] as Node3D).visible = true
			s["grip"].active = true
			(s["cloth"] as ShaderMaterial).set_shader_parameter("furl", float(fa[0]))
			(s["cloth"] as ShaderMaterial).set_shader_parameter("air", float(fa[1]))
	for t in times:
		ap.play(clip, 0.0)
		ap.seek(float(t), true)
		ap.advance(0.0)
		await process_frame
		var sk: Skeleton3D = u["skel"]
		print("POSE %s t %s hand_r %s cur %s pos %.2f" % [clip, t, sk.get_bone_global_pose(sk.find_bone("hand_r")).origin,
				ap.current_animation, ap.current_animation_position])
		var fw := n.global_transform.basis.z
		var side := fw.cross(Vector3.UP).normalized()
		var mid := n.global_position + Vector3(0, 1.45, 0)
		for v in [["front", fw], ["quarter", (fw + side).normalized()], ["back", -fw]]:
			cam.global_position = mid + (v[1] as Vector3) * 2.6 + Vector3(0, 0.1, 0)
			cam.look_at(mid, Vector3.UP)
			cam.current = true
			await _shot(pv, out, "%s_%s_%s" % [clip, t, v[0]])
	quit()
