extends SceneTree
## Time the years played without you, by step, and print a fingerprint of the
## league at the end, so a speed-up can be proved not to change the results.
##   godot --headless --path . --script tools/perf/sim_ahead_profile.gd -- [--tas] [--seed N]


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	var args := OS.get_cmdline_user_args()
	var tas := args.has("--tas")
	var s := 1
	var i := args.find("--seed")
	if i >= 0:
		s = int(args[i + 1])
	seed(s)
	var t0 := Time.get_ticks_msec()
	if tas:
		gs.challenge = {}
		gs.begin_real_lists()
		gs.begin_wait_for_club("TAS")
	else:
		gs.begin_sim_ahead()
	var t := {"setup": Time.get_ticks_msec() - t0}
	print("SETUP ", t, " sim_ahead ", gs.sim_ahead)
	var worst := 0
	var worst_line := ""
	while true:
		var a := Time.get_ticks_msec()
		var kind := "other"
		if gs.draft != null and gs.draft.intake_mode:
			kind = "draft"
		elif gs.season != null and gs.season.is_season_over():
			kind = "rollover"
		elif gs.season != null:
			kind = "week"
		var line: String = gs.sim_ahead_step()
		var d := Time.get_ticks_msec() - a
		t[kind] = int(t.get(kind, 0)) + d
		if d > worst:
			worst = d
			worst_line = line
		if line == "":
			break
	print("TOTAL_MS ", Time.get_ticks_msec() - t0, " ", t, " worst ", worst, " ", worst_line)
	var parts := []
	for code in gs.season.ladder.keys():
		var l: Dictionary = gs.season.ladder[code]
		parts.append("%s %d %d %d" % [code, l["w"], l["pf"], l["pa"]])
	parts.sort()
	var ps := []
	for code in gs.season.lists:
		for p in gs.season.lists[code]:
			ps.append("%s|%s|%s|%s|%s" % [code, p.get("id"), p.get("overall"), p.get("xp"), p.get("attr")])
	ps.sort()
	print("FINGERPRINT ", gs.career_seed, " ", gs.season_year, " ", "\n".join(parts).md5_text(),
			" ", "\n".join(ps).md5_text(), " players ", ps.size())
	quit(0)
