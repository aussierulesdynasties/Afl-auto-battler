extends SceneTree
## Write sim_pair.py's simulated motion back as clips:
##   godot --headless --path . --script tools/oval3d/import_pair.gd -- SIM.json A.res B.res OUT_DIR
## OUT_DIR/A.res and OUT_DIR/B.res (named as the inputs) are the input clips with each simulated
## bone's rotation track and the pelvis position track replaced by the simulation's (sampled at
## SIM.json's rate); the bones the simulation does not carry (fingers, the balls of the feet) keep
## their keyed motion.

const GLB := "res://assets/oval3d/player_mh.glb"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var a := OS.get_cmdline_user_args()
	var sim: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(str(a[0])))
	var hz := float(sim["hz"])
	var names: Array = sim["bones"]
	DirAccess.make_dir_recursive_absolute(str(a[3]))
	for m in 2:
		var res := str(a[1 + m])
		var src: Animation = load(res)
		var scene: Node3D = (load(GLB) as PackedScene).instantiate()
		root.add_child(scene)
		var ap: AnimationPlayer = scene.find_children("*", "AnimationPlayer", true, false)[0]
		var sk: Skeleton3D = scene.find_children("*", "Skeleton3D", true, false)[0]
		var lib := AnimationLibrary.new()
		lib.add_animation("clip", src)
		ap.add_animation_library("pair", lib)
		ap.play("pair/clip")
		ap.pause()
		var frames: Array = sim["men"][m]["frames"]
		var path := str(ap.get_node(ap.root_node).get_path_to(sk))
		var out := Animation.new()
		out.length = (frames.size() - 1) / hz
		# Keep every track of the keyed clip for the bones the simulation leaves alone.
		var simmed := {}
		for n in names:
			simmed[n] = true
		for t in src.get_track_count():
			var bone := str(src.track_get_path(t)).get_slice(":", 1)
			if simmed.has(bone) and (src.track_get_type(t) == Animation.TYPE_ROTATION_3D
					or (bone == "pelvis" and src.track_get_type(t) == Animation.TYPE_POSITION_3D)):
				continue
			src.copy_track(t, out)
		var rot := {}
		for n in names:
			var tr := out.add_track(Animation.TYPE_ROTATION_3D)
			out.track_set_path(tr, "%s:%s" % [path, n])
			rot[n] = tr
		var ptr := out.add_track(Animation.TYPE_POSITION_3D)
		out.track_set_path(ptr, "%s:pelvis" % path)
		# Bones in hierarchy order (parents first): names is already in that order.
		for f in frames.size():
			var t := f / hz
			ap.seek(minf(t, src.length), true)
			var fr: Dictionary = frames[f]
			for i in names.size():
				var b := sk.find_bone(str(names[i]))
				var q: Array = fr["quat"][i]
				var p: Array = fr["pos"][i]
				var g := Transform3D(Basis(Quaternion(q[0], q[1], q[2], q[3])), Vector3(p[0], p[1], p[2]))
				# Keep the bone's own pose scale and its offset from the parent; set its world turn.
				var par := sk.get_bone_parent(b)
				var pg := sk.get_bone_global_pose(par) if par >= 0 else Transform3D.IDENTITY
				var local_basis := (pg.basis.orthonormalized().inverse() * g.basis).orthonormalized()
				sk.set_bone_pose_rotation(b, local_basis.get_rotation_quaternion())
				if str(names[i]) == "pelvis":
					var lp := pg.affine_inverse() * g.origin
					sk.set_bone_pose_position(b, lp)
					out.position_track_insert_key(ptr, t, lp)
				out.rotation_track_insert_key(rot[str(names[i])], t, sk.get_bone_pose_rotation(b))
		ResourceSaver.save(out, str(a[3]).path_join(res.get_file()))
		scene.queue_free()
	print("IMPORTED")
	quit()
