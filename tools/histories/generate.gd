extends SceneTree
## Play one pre-made history and write it (see scripts/state/PremadeHistory.gd).
##   godot --headless --path . --script tools/histories/generate.gd -- <2030|2028> <n>
##   godot --headless --path . --script tools/histories/generate.gd -- --check
## --check exits 1 if any history is missing or behind the code or data.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	var args := OS.get_cmdline_user_args()
	if args.has("--check"):
		quit(_check(gs))
		return
	var first := int(args[0])
	var t0 := Time.get_ticks_msec()
	gs.reset()
	var stamps := PremadeHistory.stamps()
	if first == gs.SIM_AHEAD_TO:
		gs.set_canberra(true)
		gs.begin_sim_ahead()
	else:
		gs.set_canberra(false)
		gs.begin_real_lists()
		if not gs.begin_wait_for_club("TAS"):
			push_error("No wait for Tasmania")
			quit(1)
			return
	while gs.sim_ahead_step() != "":
		pass
	stamps["first_season"] = first
	var path := PremadeHistory.path_for(first, int(args[1]))
	var ok: bool = gs.write_history(path, stamps)
	print("WROTE ", path, " ", ok, " ms ", Time.get_ticks_msec() - t0)
	quit(0 if ok else 1)


func _check(gs) -> int:
	gs.reset()
	var now := PremadeHistory.stamps()
	var bad := 0
	for first in PremadeHistory.STARTS:
		for n in PremadeHistory.COUNT:
			var p := PremadeHistory.path_for(first, n)
			var meta := CareerSave.read_packed_meta(p)
			for key in now:
				if str(meta.get(key, "")) != str(now[key]):
					print("STALE ", p, " ", key)
					bad += 1
	print("HISTORIES ", "fresh" if bad == 0 else "STALE: run tools/histories/regen.sh")
	return 0 if bad == 0 else 1
