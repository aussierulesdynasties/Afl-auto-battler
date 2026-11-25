extends SceneTree
## Play a clip made from slow-motion footage at real speed: every key's time times SPEED (the
## replay's speed against real time, e.g. 0.4 for Jurrah's 2010 replay, measured from gravity),
## then resampled at HZ so the match gets one key per frame as bake_fit.gd writes.
## RETIME_SMOOTH=sigma (frames) then smooths the legs' turns (thighs to toes), for a leg the fit
## flicks faster than a man can kick where the footage loses it.
##   godot --headless --path . --script tools/oval3d/retime_clip.gd -- IN.res OUT.res SPEED [HZ]

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var speed := float(args[2])
	var hz := float(args[3]) if args.size() > 3 else 25.0
	var src: Animation = load(str(args[0]))
	var out := Animation.new()
	out.length = src.length * speed
	for t in src.get_track_count():
		var typ := src.track_get_type(t)
		var nt := out.add_track(typ)
		out.track_set_path(nt, src.track_get_path(t))
		out.track_set_interpolation_type(nt, src.track_get_interpolation_type(t))
		var n := int(floor(out.length * hz + 1e-4)) + 1
		for k in n:
			var at := (k / hz) / speed
			if typ == Animation.TYPE_ROTATION_3D:
				out.rotation_track_insert_key(nt, k / hz, src.rotation_track_interpolate(t, at))
			elif typ == Animation.TYPE_POSITION_3D:
				out.position_track_insert_key(nt, k / hz, src.position_track_interpolate(t, at))
			elif typ == Animation.TYPE_SCALE_3D:
				out.scale_track_insert_key(nt, k / hz, src.scale_track_interpolate(t, at))
	var sig := float(OS.get_environment("RETIME_SMOOTH")) if OS.get_environment("RETIME_SMOOTH") != "" else 0.0
	if sig > 0.0:
		for t in out.get_track_count():
			if out.track_get_type(t) != Animation.TYPE_ROTATION_3D:
				continue
			var bone := str(out.track_get_path(t)).get_slice(":", 1)
			if not (bone.begins_with("thigh") or bone.begins_with("calf") or bone.begins_with("foot") or bone.begins_with("ball")):
				continue
			var qs := []
			for k in out.track_get_key_count(t):
				qs.append(out.track_get_key_value(t, k))
			var r := int(ceil(3.0 * sig))
			for k in qs.size():
				var acc := Vector4.ZERO
				var ref: Quaternion = qs[k]
				for i in range(maxi(0, k - r), mini(qs.size(), k + r + 1)):
					var q: Quaternion = qs[i]
					if q.dot(ref) < 0.0:
						q = -q
					var g := exp(-0.5 * pow((i - k) / sig, 2))
					acc += Vector4(q.x, q.y, q.z, q.w) * g
				out.track_set_key_value(t, k, Quaternion(acc.x, acc.y, acc.z, acc.w).normalized())
	print("RETIMED %.2f s -> %.2f s" % [src.length, out.length])
	print("SAVED %s %s" % [args[1], error_string(ResourceSaver.save(out, str(args[1])))])
	quit()
