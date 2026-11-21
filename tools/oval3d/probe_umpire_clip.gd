extends SceneTree
## Measures the field umpire's bounce clip (umpire_bounce_01) on the 3D oval's umpire: its
## length, and his palms and pelvis every 1/15 s, for Oval3D's UMP_T_REL, UMP_T_HIT and
## UMP_BOUNCE_REACH (the ball leaves his hands, is on the turf, and how far in front):
##   godot --path . --script tools/oval3d/probe_umpire_clip.gd
func _initialize() -> void:
	_run.call_deferred()
func _run() -> void:
	await process_frame
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	var u: Dictionary = oval.umpires[0]
	var ap: AnimationPlayer = u["anim"]
	var node: Node3D = u["node"]
	node.position = Vector3.ZERO
	node.rotation = Vector3.ZERO
	ap.play("umpire_bounce_01")
	var L := ap.current_animation_length
	print("len ", L)
	var skel: Skeleton3D = u["skel"]
	print("bones ", skel.get_bone_name(0), " ", skel.get_bone_name(1), " ", skel.get_bone_name(2))
	var t := 0.0
	while t <= L + 0.001:
		ap.seek(t, true)
		var gt := skel.global_transform
		var s := ""
		for k in range(2):
			var pose := skel.get_bone_global_pose(u["hands"][k])
			var p: Vector3 = gt * (pose.origin + pose.basis.y.normalized() * float(u["hand_len"][k]) * 0.6)
			s += " h%d(%.2f,%.2f,%.2f)" % [k, p.x, p.y, p.z]
		var hb := skel.find_bone("pelvis")
		if hb < 0: hb = skel.find_bone("Hips")
		if hb < 0: hb = skel.find_bone("hips")
		var hips := gt * skel.get_bone_global_pose(hb).origin
		print("t=%.2f%s hips(%.2f,%.2f,%.2f)" % [t, s, hips.x, hips.y, hips.z])
		t += 1.0 / 15.0
	quit()
