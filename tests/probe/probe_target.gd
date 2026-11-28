extends SceneTree
## Scratch probe (never commit): test_match_game's _test_play_through_three paired-match part,
## the forward target's shots with the three calls on and off, with change 1 (the centre-clearance
## presser from the four at the bounce) off (as before) and on. Seeds PT_S0 .. PT_S0+PT_N-1.
## One line per seed: PT <seed> <C> fs_on fs_base.

func _initialize() -> void:
	_run.call_deferred()


func _mk(MS, SQ, seed: int):
	var db = root.get_node("GameDB")
	return MS.new(SQ.new("GEE", db.club_list("GEE"), true, "GEE"),
			SQ.new("COL", db.club_list("COL"), false, "COL"), seed)


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
	root.get_node("GameDB").reload()
	var MS = load("res://tests/probe/pressfwd_ms.gd")
	var SQ = load("res://scripts/sim/Squad.gd")
	var RO = load("res://scripts/sim/Roles.gd")
	var s0 := int(OS.get_environment("PT_S0")) if OS.get_environment("PT_S0") != "" else 900
	var n := int(OS.get_environment("PT_N")) if OS.get_environment("PT_N") != "" else 80
	var probe = _mk(MS, SQ, 60)
	var who := {}
	for p in probe.squads[0].ground:
		var role := str(p["role"])
		if not who.has(role):
			who[role] = p
	var mid: Dictionary = who["MID"]
	for p in probe.squads[0].ground:
		if str(p["role"]) == "MID" and RO.usual_touches(p) < RO.usual_touches(mid):
			mid = p
	var fwd: Dictionary = who["FWD"]
	var def: Dictionary = who["DEF"]
	var three := {"focus_mid": str(mid["id"]), "focus_fwd": str(fwd["id"]), "focus_def": str(def["id"])}
	print("PT target %s mid %s def %s" % [fwd["id"], mid["id"], def["id"]])
	for off in [false, true]:
		for i in range(n):
			var seed := s0 + i
			var a = _mk(MS, SQ, seed)
			var b = _mk(MS, SQ, seed)
			a.off = off
			b.off = off
			var plan := {"gameplan": str(b.standing[0])}
			a.set_tactics(0, plan.merged(three))
			b.set_tactics(0, plan)
			var ra: Dictionary = a.run()
			var rb: Dictionary = b.run()
			var fa: Dictionary = (ra["players"] as Dictionary).get(str(fwd["id"]), {})
			var fb: Dictionary = (rb["players"] as Dictionary).get(str(fwd["id"]), {})
			print("PT %d %s %d %d" % [seed, "off" if off else "on",
					int(fa.get("goals", 0)) + int(fa.get("behinds", 0)),
					int(fb.get("goals", 0)) + int(fb.get("behinds", 0))])
	quit(0)
