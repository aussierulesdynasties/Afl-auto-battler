extends SceneTree
## The first coach's call of a session (TODO row T2.42): trace_stall_live found
## one frame of about 5 s as the first call scene opens, and 0.1-0.2 s for every
## later one. This times the call scene's steps cold, then the same again warm,
## in a fresh process. Report only.
##   godot --path . --script tools/visual/trace_first_call.gd [-- --size 390x844]
## Prints FIRST lines: the step, cold or warm, and its milliseconds.

func _initialize() -> void:
	_run.call_deferred()


func _arg(name: String, fallback: String) -> String:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == name:
			return str(a[i + 1])
	return fallback


func _ms(t0: int) -> float:
	return float(Time.get_ticks_usec() - t0) / 1000.0


func _run() -> void:
	var sz := _arg("--size", "390x844").split("x")
	root.size = Vector2i(int(sz[0]), int(sz[1]))
	await process_frame
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	gs.autosave_enabled = false
	gs.replay_seed = 7
	gs.start_season("MEL", db.club_list("MEL"))
	var t := Time.get_ticks_usec()
	var ok: bool = gs.prepare_interactive_match()
	print("FIRST prepare match: %.0f ms (%s)" % [_ms(t), str(ok)])
	t = Time.get_ticks_usec()
	var stop_scr = load("res://scripts/ui/match/StoppageVignette.gd")
	var scr = load("res://scripts/ui/match/DecisionVignette.gd")
	print("FIRST load the call scene's script and sheets: %.0f ms" % _ms(t))
	var sim = gs.pending_sim
	sim.begin_quarter()
	for pass_i in range(3):
		for kind in ["stoppage", "decision"]:
			var label := "%s %s" % ["cold" if pass_i == 0 else "warm%d" % pass_i, kind]
			var host := Control.new()
			host.size = Vector2(root.size)
			root.add_child(host)
			t = Time.get_ticks_usec()
			var v = stop_scr.new() if kind == "stoppage" else scr.new()
			host.add_child(v)
			v.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
			v.clip_contents = true
			if kind == "stoppage":
				v.setup(sim, 0, "Centre bounce")
			else:
				v.setup_decision(sim, 0, {"kind": "momentum", "title": "Probe", "q": 1, "min": 5})
			print("FIRST %s: setup %.0f ms" % [label, _ms(t)])
			var frames := []
			for f in range(6):
				t = Time.get_ticks_usec()
				await process_frame
				frames.append(int(_ms(t)))
			print("FIRST %s: first frames %s ms" % [label, str(frames)])
			host.queue_free()
			await process_frame
	quit()
