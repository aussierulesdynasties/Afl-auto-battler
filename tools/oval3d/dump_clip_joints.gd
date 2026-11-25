extends SceneTree
## Every clip baked into a footballer GLB, sampled at 30 Hz: each body joint's rotation away
## from its rest pose (a quaternion, in its parent's space), and the joint's bone direction at
## rest. Feeds tools/oval3d/joint_audit.py, which measures each joint's bend and twist against a
## real body's limits and against the Epic GASP clips (reel feedback 2026-11-22: "some of the
## animations create some strange model contortion").
##   godot --headless --path . --script tools/oval3d/dump_clip_joints.gd -- OUT.json [res://...glb]

const HZ := 30.0
const JOINTS := ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head",
		"clavicle_l", "upperarm_l", "lowerarm_l", "hand_l", "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r",
		"thigh_l", "calf_l", "foot_l", "ball_l", "thigh_r", "calf_r", "foot_r", "ball_r"]


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
	var rest := {}
	for b in JOINTS:
		var id := sk.find_bone(b)
		if id < 0:
			continue
		# The bone's direction: toward its first child at rest (its own space).
		var kids := sk.get_bone_children(id)
		var dir := Vector3.UP
		if kids.size() > 0:
			dir = sk.get_bone_rest(kids[0]).origin.normalized()
		var r := sk.get_bone_rest(id).basis.get_rotation_quaternion()
		rest[b] = {"id": id, "dir": [dir.x, dir.y, dir.z], "rest": [r.x, r.y, r.z, r.w]}
	if OS.get_environment("CLIP_LIMITS") != "":
		# As a match plays them (Oval3D._player): held inside ClipLimits.
		ClipLimits.apply(ap, sk)
	var data := {"joints": rest, "clips": {}}
	for anim_name in ap.get_animation_list():
		ap.play(anim_name)
		var length := ap.current_animation_length
		var frames := []
		for s in range(int(length * HZ) + 1):
			ap.seek(minf(length, s / HZ), true)
			var f := {}
			for b in rest:
				var q := sk.get_bone_pose_rotation(int(rest[b]["id"]))
				f[b] = [snappedf(q.x, 0.0001), snappedf(q.y, 0.0001), snappedf(q.z, 0.0001), snappedf(q.w, 0.0001)]
			frames.append(f)
		data["clips"][str(anim_name)] = {"len": length, "hz": HZ, "frames": frames}
		ap.stop()
	var fa := FileAccess.open(out, FileAccess.WRITE)
	fa.store_string(JSON.stringify(data))
	fa.close()
	quit()
