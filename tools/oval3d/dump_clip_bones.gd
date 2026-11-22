extends SceneTree
## Every clip baked into a footballer GLB, sampled at 60 Hz: where his hands' palms, feet, toes,
## hips and head are, in the figure's own space (metres, +z his front). Feeds
## tools/oval3d/clip_markers.py, which finds each move's moments (hands let go, foot or hand on
## the ball, mark secured) from the motion itself.
##   godot --headless --path . --script tools/oval3d/dump_clip_bones.gd -- OUT.json [res://...glb]

const HZ := 60.0
const BONES := ["pelvis", "head", "hand_l", "hand_r", "foot_l", "foot_r", "ball_l", "ball_r",
		"calf_l", "calf_r", "lowerarm_l", "lowerarm_r"]


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var path := str(args[1]) if args.size() > 1 else "res://assets/oval3d/player_mh.glb"
	var scene: Node3D = (load(path) as PackedScene).instantiate()
	root.add_child(scene)
	await process_frame
	var ap: AnimationPlayer = scene.find_children("*", "AnimationPlayer", true, false)[0]
	var sk: Skeleton3D = scene.find_children("*", "Skeleton3D", true, false)[0]
	var ids := {}
	for b in BONES:
		ids[b] = sk.find_bone(b)
	# A palm is 60% along the hand bone toward its children (Oval3D._hold_ball's point).
	var hand_len := {}
	for b in ["hand_l", "hand_r"]:
		var kids := sk.get_bone_children(ids[b])
		var sum := 0.0
		for c in kids:
			sum += sk.get_bone_rest(c).origin.length()
		hand_len[b] = sum / maxf(1.0, kids.size()) if kids.size() > 0 else 0.1
	var data := {}
	for anim_name in ap.get_animation_list():
		ap.play(anim_name)
		var length := ap.current_animation_length
		var frames := []
		var n := int(length * HZ) + 1
		for s in range(n):
			ap.seek(minf(length, s / HZ), true)
			var f := {}
			for b in BONES:
				if int(ids[b]) < 0:
					continue
				var pose := sk.get_bone_global_pose(ids[b])
				var o := pose.origin
				if hand_len.has(b):
					o += pose.basis.y.normalized() * float(hand_len[b]) * 0.6
				var w := scene.global_transform.affine_inverse() * (sk.global_transform * o)
				f[b] = [snappedf(w.x, 0.001), snappedf(w.y, 0.001), snappedf(w.z, 0.001)]
			frames.append(f)
		data[str(anim_name)] = {"len": length, "hz": HZ, "frames": frames}
		ap.stop()
	var fa := FileAccess.open(out, FileAccess.WRITE)
	fa.store_string(JSON.stringify(data))
	fa.close()
	print("dumped %d clips to %s" % [data.size(), out])
	quit(0)
