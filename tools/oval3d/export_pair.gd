extends SceneTree
## Export a two-man clip's body bones (key_pair.gd's BONES) for the physics pass (sim_pair.py):
##   godot --headless --path . --script tools/oval3d/export_pair.gd -- A.res B.res OUT.json [HZ]
## OUT.json: {"hz", "bones": [{name, parent (index or -1), rest_pos, rest_quat, end}],
## "men": [{"frames": [{"pos": [[x,y,z]...], "quat": [[x,y,z,w]...]}...]} x2]}. Globals in the
## world (the skeleton's transform is identity). Each clip plays inside ClipLimits, as the match
## plays it. "end": where the bone's segment ends at rest (its children's heads, averaged; the
## head and the ball of the foot get a set length).

const GLB := "res://assets/oval3d/player_mh.glb"
const BONES := ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head",
	"clavicle_l", "upperarm_l", "lowerarm_l", "hand_l", "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r",
	"thigh_l", "calf_l", "foot_l", "ball_l", "thigh_r", "calf_r", "foot_r", "ball_r"]


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var a := OS.get_cmdline_user_args()
	var hz := float(a[3]) if a.size() > 3 else 50.0
	var out := {"hz": hz, "bones": [], "men": []}
	var first := true
	for res in [str(a[0]), str(a[1])]:
		var scene: Node3D = (load(GLB) as PackedScene).instantiate()
		root.add_child(scene)
		var ap: AnimationPlayer = scene.find_children("*", "AnimationPlayer", true, false)[0]
		var sk: Skeleton3D = scene.find_children("*", "Skeleton3D", true, false)[0]
		var lib := AnimationLibrary.new()
		lib.add_animation("clip", load(res))
		ap.add_animation_library("pair", lib)
		ClipLimits.apply(ap, sk)
		ap.play("pair/clip")
		ap.pause()
		if first:
			for name in BONES:
				var b := sk.find_bone(name)
				var p := sk.get_bone_parent(b)
				while p >= 0 and not BONES.has(sk.get_bone_name(p)):
					p = sk.get_bone_parent(p)
				var g := sk.get_bone_global_rest(b)
				var end := Vector3.ZERO
				var n := 0
				for c in sk.get_bone_children(b):
					if BONES.has(sk.get_bone_name(c)) or name in ["hand_l", "hand_r"]:
						end += sk.get_bone_global_rest(c).origin
						n += 1
				if n > 0:
					end /= n
				elif name == "head":
					end = g.origin + Vector3(0, 0.2, 0)
				else:
					end = g.origin + (g.basis * Vector3(0, 1, 0)).normalized() * 0.06
				var q := g.basis.get_rotation_quaternion()
				out["bones"].append({"name": name, "parent": BONES.find(sk.get_bone_name(p)) if p >= 0 else -1,
						"rest_pos": [g.origin.x, g.origin.y, g.origin.z], "rest_quat": [q.x, q.y, q.z, q.w],
						"end": [end.x, end.y, end.z]})
			first = false
		var frames := []
		var length := ap.current_animation_length
		var t := 0.0
		while t <= length + 1e-4:
			ap.seek(t, true)
			var fp := []
			var fq := []
			for name in BONES:
				var g := sk.get_bone_global_pose(sk.find_bone(name))
				var q := g.basis.get_rotation_quaternion()
				fp.append([g.origin.x, g.origin.y, g.origin.z])
				fq.append([q.x, q.y, q.z, q.w])
			frames.append({"pos": fp, "quat": fq})
			t += 1.0 / hz
		out["men"].append({"frames": frames})
		scene.queue_free()
	var f := FileAccess.open(str(a[2]), FileAccess.WRITE)
	f.store_string(JSON.stringify(out))
	print("EXPORTED %d frames" % (out["men"][0]["frames"] as Array).size())
	quit()
