extends SceneTree
## Fixed-seed matches on one thread: time per match and a hash of every result,
## so a speed-up of the match engine can be proved to leave results alone.
##   godot --headless --path . --script tools/perf/match_proof.gd


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	seed(1)
	gs.begin_sim_ahead()
	gs.sim_ahead_step()
	var se = gs.season
	var ms: Array = se.fixture[0]
	# The real lists as loaded: a career's draft and coaches differ run to run.
	var by_club := {}
	for p in root.get_node("GameDB").all_players_sorted():
		var c := str(p.get("club", ""))
		if not by_club.has(c):
			by_club[c] = []
		by_club[c].append(p)
	for c in se.lists:
		se.lists[c] = by_club.get(c, se.lists[c])
	se.selections = {}
	gs.coaches = {}
	ms = [{"home": "COL", "away": "CAR"}, {"home": "GEE", "away": "BRL"}, {"home": "MEL", "away": "SYD"}]
	var out := []
	var spent := 0
	for i in range(24):
		var m: Dictionary = ms[i % ms.size()]
		var sim = se.match_sim(m["home"], m["away"], 7000 + i)
		var a := Time.get_ticks_usec()
		var res: Dictionary = sim.run()
		spent += Time.get_ticks_usec() - a
		out.append(str(res["score"], res["players"]))
	print("PROOF ms_per_match ", spent / 24000, " hash ", "\n".join(out).md5_text())
	quit(0)
