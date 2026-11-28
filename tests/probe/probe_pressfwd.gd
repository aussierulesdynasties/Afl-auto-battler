extends SceneTree
## Scratch probe (never commit): test_pressure's _test_high_pressure_forward, measured with change
## C off (as before) and on, over PF_N matches (seeds 900+), with the forward's share of the
## centre-clearance picks.

func _initialize() -> void:
	_run.call_deferred()


func _mk(MS, SQ, seed: int, target: String, pressure: float):
	var lists := []
	for code in ["GEE", "COL"]:
		var l: Array = []
		for p in root.get_node("GameDB").club_list(code):
			l.append(p.duplicate(true))
		lists.append(l)
	var home = SQ.new("GEE", lists[0], true, "GEE")
	var away = SQ.new("COL", lists[1], false, "COL")
	if target != "":
		for p in away.ground:
			if str(p["id"]) == target:
				p["attr"]["pressure"] = pressure
		away._aggregate()
	return MS.new(home, away, seed)


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
	root.get_node("GameDB").reload()
	var MS = load("res://tests/probe/pressfwd_ms.gd")
	var SQ = load("res://scripts/sim/Squad.gd")
	var n := int(OS.get_environment("PF_N")) if OS.get_environment("PF_N") != "" else 16
	var probe = _mk(MS, SQ, 1, "", 0.0)
	var target := ""
	for p in probe.squads[1].ground:
		if str(p["role"]) == "FWD":
			target = str(p["id"])
			break
	print("PF target %s" % target)
	for off in [true, false]:
		var line := []
		for pr in [40.0, 95.0]:
			var acts := 0.0
			var bp := 0
			var bt := 0
			for i in range(n):
				var sim = _mk(MS, SQ, 900 + i, target, pr)
				sim.off = off
				sim.target = target
				var res: Dictionary = sim.run()
				acts += float((res["players"].get(target, {}) as Dictionary).get("pressure_acts", 0.0))
				bp += sim.bounce_picks
				bt += sim.bounce_target
			line.append("P%d acts %.2f/game, clearance picks %.2f/game, to him %.2f/game" % [pr, acts / n, float(bp) / n, float(bt) / n])
		print("PF n=%d C=%s | %s" % [n, "off" if off else "on", " || ".join(line)])
	quit(0)
