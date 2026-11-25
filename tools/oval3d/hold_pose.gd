extends SceneTree
## Hold a man still where the footage loses him under a pack (Jurrah's teammate, under him for
## three seconds of replay): every bone keeps the pose of the last frame he is seen, his hips
## sinking SINK metres as the other man's weight comes on, then he eases back into the film over
## EASE frames. Better than a guess made from nothing (the fit stood him up straight).
## With HOLD_BRIDGE=1 he is instead carried from his pose at FROM to his pose at TO (each bone turned
## evenly between them, eased): for a man the footage loses in mid-movement, where the fit's guess
## invents a pose (Jurrah stood on his head while hidden in the tangle).
##   godot --headless --path . --script tools/oval3d/hold_pose.gd -- IN.res OUT.res FROM:TO [SINK] [EASE] [HZ]

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var ft := str(args[2]).split(":")
	var a := int(ft[0])
	var b := int(ft[1])
	var sink := float(args[3]) if args.size() > 3 else 0.0
	var ease := int(args[4]) if args.size() > 4 else 6
	var hz := float(args[5]) if args.size() > 5 else 25.0
	var anim: Animation = (load(str(args[0])) as Animation).duplicate(true)
	for t in anim.get_track_count():
		var typ := anim.track_get_type(t)
		if typ != Animation.TYPE_ROTATION_3D and typ != Animation.TYPE_POSITION_3D:
			continue
		var bone := str(anim.track_get_path(t)).get_slice(":", 1)
		var held = anim.track_get_key_value(t, anim.track_find_key(t, a / hz, Animation.FIND_MODE_APPROX))
		if OS.get_environment("HOLD_BRIDGE") != "":
			var end = anim.track_get_key_value(t, anim.track_find_key(t, b / hz, Animation.FIND_MODE_APPROX))
			for k in range(a + 1, b):
				var key := anim.track_find_key(t, k / hz, Animation.FIND_MODE_APPROX)
				var w := smoothstep(float(a), float(b), float(k))
				anim.track_set_key_value(t, key, (held as Quaternion).slerp(end, w) if typ == Animation.TYPE_ROTATION_3D else (held as Vector3).lerp(end, w))
			continue
		# After the hold his hips keep the place the hold left them (his own movement from there
		# on, carried across), so he does not slide back to where the fit had him.
		var is_hips := typ == Animation.TYPE_POSITION_3D and bone == "pelvis"
		var last_k := int(round(anim.length * hz))
		var carry := Vector3.ZERO
		if is_hips:
			carry = (held as Vector3) - Vector3(0, 0, sink) - (anim.track_get_key_value(t, anim.track_find_key(t, b / hz, Animation.FIND_MODE_APPROX)) as Vector3)
		for k in range(a + 1, (last_k + 1) if is_hips else (b + ease + 1)):
			var key := anim.track_find_key(t, k / hz, Animation.FIND_MODE_APPROX)
			if key < 0:
				continue
			var v = held
			if typ == Animation.TYPE_POSITION_3D and bone == "pelvis":
				# The sink: the pelvis's parent is the MetaHuman root, which is Z-up.
				var s := sink * smoothstep(float(a), float(b), float(mini(k, b)))
				v = (held as Vector3) - Vector3(0, 0, s)
			if k > b and is_hips:
				# Across the ground carried; his height eased back to his own as he gets up.
				var own_p := anim.track_get_key_value(t, key) as Vector3
				var w := smoothstep(float(b), float(b + ease), float(k))
				v = Vector3(own_p.x + carry.x, own_p.y + carry.y, lerpf((held as Vector3).z - sink, own_p.z, w))
			elif k > b:
				var w := smoothstep(float(b), float(b + ease), float(k))
				var own = anim.track_get_key_value(t, key)
				v = (v as Quaternion).slerp(own, w) if typ == Animation.TYPE_ROTATION_3D else (v as Vector3).lerp(own, w)
			anim.track_set_key_value(t, key, v)
	print("SAVED %s %s" % [args[1], error_string(ResourceSaver.save(anim, str(args[1])))])
	quit()
