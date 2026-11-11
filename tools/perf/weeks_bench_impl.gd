extends RefCounted
## The body of tools/perf/weeks_bench.gd (see there).


## The step timer (tools/perf/perf_lap.gd), when the bench tree has one.
var _lap: GDScript = null


func run(root: Node) -> void:
	if ResourceLoader.exists("res://tools/perf/perf_lap.gd"):
		_lap = load("res://tools/perf/perf_lap.gd")
	var club := "GEE"
	var seasons := 3
	var rs := 4242
	var plain := OS.get_cmdline_user_args().has("--plain")
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--club": club = str(a[i + 1])
			"--seasons": seasons = int(a[i + 1])
			"--seed": rs = int(a[i + 1])
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	gs.reset()
	gs.replay_seed = rs
	gs.autosave_enabled = false
	gs.start_season(club, db.club_list(club))
	# The week, as advance() runs it (prep, then _play_steps), one timer a step.
	var prep := {
		"preseason": func(): gs.preseason_sim_to_round1(),
		"week_event": func(): gs._settle_week_event(),
		"midseason_draft": func(): MidseasonDraft.settle(gs),
		"rookie_list": func(): RookieList.settle(gs),
		"club_plan": func(): gs._sync_club_plan(),
		"coach_tactics": func(): gs._refresh_coach_tactics(),
		"usual_plans": func():
			if not gs.season.is_season_over():
				gs._settle_usual_plans(),
		"conditioning": func(): gs._stamp_conditioning(),
	}
	var play := ["play", "log", "xp", "rivals", "after", "save"]
	var ms := {}
	for k in prep:
		ms[k] = 0.0
	for k in play:
		ms[k] = 0.0
	ms["offseason"] = 0.0
	var weeks_ms := 0.0
	var weeks := 0
	var all_hash := ""
	for s in range(seasons):
		var season_results := []
		while not gs.season.is_season_over():
			var w0 := Time.get_ticks_usec()
			if plain and _lap != null:
				var wl = _lap.new("bench.week")
				wl.lap("advance (%s)" % ("regular" if not gs.season.is_regular_done() else "finals"))
				gs.advance()
				_lap.close_top()
				weeks_ms += (Time.get_ticks_usec() - w0) / 1000.0
				weeks += 1
				season_results.append_array(gs.last_results)
				continue
			if plain:
				# GameState.advance() whole: for older trees without these steps.
				gs.advance()
				weeks_ms += (Time.get_ticks_usec() - w0) / 1000.0
				weeks += 1
				season_results.append_array(gs.last_results)
				continue
			gs.recruit_undo.clear()
			for k in prep:
				var t := Time.get_ticks_usec()
				prep[k].call()
				ms[k] += (Time.get_ticks_usec() - t) / 1000.0
			gs._advance_reset()
			var steps: Array = gs._play_steps()
			var stop := ""
			for i in range(steps.size()):
				var t := Time.get_ticks_usec()
				stop = steps[i].call()
				ms[play[i]] += (Time.get_ticks_usec() - t) / 1000.0
				if stop != "":
					break
			weeks_ms += (Time.get_ticks_usec() - w0) / 1000.0
			weeks += 1
			season_results.append_array(gs.last_results)
			if gs.is_sacked():
				print("NOTE sacked in %d" % gs.season_year)
		var h := JSON.stringify(season_results).sha256_text()
		all_hash += h
		print("HASH season %d results %s (%d matches)" % [gs.season_year, h, season_results.size()])
		if s == seasons - 1:
			break
		var o0 := Time.get_ticks_usec()
		var lap = _lap.new("bench.offseason") if _lap != null else null
		if lap: lap.lap("open_offseason")
		gs.open_offseason()
		if lap: lap.lap("begin_intake_draft")
		if gs.begin_intake_draft():
			var d = gs.draft
			var guard := 0
			if lap: lap.lap("draft picks (bench loop)")
			while not d.is_finished() and guard < 5000:
				guard += 1
				var c: Dictionary = d._best_ai_pick(d.current_club())
				if c.is_empty() or not d._draft_pick(d.current_club(), c):
					d._skip_current_pick()
			if lap: lap.lap("finish_intake_draft")
			gs.finish_intake_draft()
		else:
			if lap: lap.lap("start_next_season")
			gs.start_next_season()
		if lap: _lap.close_top()
		ms["offseason"] += (Time.get_ticks_usec() - o0) / 1000.0
	var save_h := JSON.stringify(gs._save_state()).sha256_text() if gs.has_method("_save_state") else "none"
	print("HASH save %s" % save_h)
	print("HASH all %s" % (all_hash + save_h).sha256_text())
	for k in ms:
		print("PERF %-16s %9.0f ms" % [k, ms[k]])
	print("PERF weeks %.1f s over %d weeks (%.0f ms a week); off-season %.1f s" % [
		weeks_ms / 1000.0, weeks, weeks_ms / maxf(1, weeks), ms["offseason"] / 1000.0])
	if _lap != null:
		_lap.dump()
	print("PERF coaches %d, free or away %d" % [gs.coaches.size(), gs.coaches.values().filter(func(c): return str(c.get("status", "")) in ["free", "away"]).size()])
