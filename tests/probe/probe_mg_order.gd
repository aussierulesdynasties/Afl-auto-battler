extends SceneTree
## Scratch probe (never commit): which earlier match_game function changes the
## skip check (seed 301 moments) and the windy lead shots.

var MS
var SQ
var db


func _initialize() -> void:
	_run.call_deferred()


func _sim(seed: int):
	return MS.new(SQ.new("GEE", db.club_list("GEE"), true, "GEE"), SQ.new("COL", db.club_list("COL"), false, "COL"), seed)


func _state(tag: String) -> void:
	var sim = _sim(301)
	sim.moment_side = 0
	var res: Dictionary = sim.run()
	var keep = MS.tune
	MS.tune = {"WX_miss_behind": 0.0}
	var lead := 0
	var opts := {}
	var turn := 0
	for seed in range(830, 838):
		var live = _sim(seed)
		live.weather = "windy"
		live.moment_side = 0
		while live.current_quarter <= 4:
			live.begin_quarter()
			while not live.continue_quarter():
				var m: Dictionary = live.pending_moment
				var pick := int(m.get("default", 0))
				if str(m["kind"]) == "set_shot":
					var keys := []
					for o in m["options"]:
						keys.append(str(o["key"]))
					opts[",".join(keys)] = int(opts.get(",".join(keys), 0)) + 1
					var key: String = ["bomb", "pass"][turn % 2]
					turn += 1
					for i in range(keys.size()):
						if keys[i] == key:
							pick = i
				live.resolve_moment(pick)
			live.end_quarter()
		for shot in live.shot_log:
			if str(shot[4]) == "lead":
				lead += 1
	MS.tune = keep
	print("PROBEO after %s: skip301 moments=%d tune=%s lead=%d opts=%s" % [tag, (res["moments"] as Array).size(), str(keep), lead, str(opts)])


func _run() -> void:
	await process_frame
	MS = load("res://scripts/sim/MatchSim.gd")
	SQ = load("res://scripts/sim/Squad.gd")
	db = root.get_node("GameDB")
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
	_state("start")
	var suite = load("res://tests/test_match_game.gd").new()
	db.skip_ovr_overrides = true
	db.reload()
	_state("reload")
	for seed in range(301, 331):
		var s2 = _sim(seed)
		s2.moment_side = 0
		var r2: Dictionary = s2.run()
		print("PROBEO seed %d moments=%d" % [seed, (r2["moments"] as Array).size()])
	for fn in ["_test_auto_sim_untouched", "_test_stoppage_location", "_test_boundary_rules",
			"_test_authenticity_events", "_test_contextual_frees_and_general_spoils",
			"_test_general_contest_player_edge", "_test_free_causes_follow_the_play",
			"_test_free_keeps_possession", "_test_clanger_cause", "_test_no_free_after_goal",
			"_test_free_set_shots_counted", "_test_legs_and_rotations", "_test_moments"]:
		await suite._t(fn)
		_state(fn)
	for f in suite.failures:
		print("PROBEO FAIL ", f)
	quit(0)
