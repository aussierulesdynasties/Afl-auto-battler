extends SceneTree
## Scratch (never commit): run match_game's functions in suite order and, after
## each, play the kick-in test's forced match (GEE v COL, seed 6101) to find
## which earlier function changes it.

const ORDER := ["_test_auto_sim_untouched", "_test_stoppage_location", "_test_boundary_rules",
	"_test_authenticity_events", "_test_contextual_frees_and_general_spoils",
	"_test_general_contest_player_edge", "_test_free_causes_follow_the_play",
	"_test_free_keeps_possession", "_test_clanger_cause", "_test_no_free_after_goal",
	"_test_free_set_shots_counted", "_test_legs_and_rotations", "_test_moments",
	"_test_playtest_bounce", "_test_set_shot", "_test_live_determinism", "_test_impact_and_ai",
	"_test_decision_credits", "_test_pep_talks", "_test_fatigue_parity",
	"_test_synergies_follow_the_ground", "_test_play_through", "_test_play_through_by_job",
	"_test_play_through_three", "_test_no_main_ruck_call", "_test_auto_rotation",
	"_test_background_matches_rotate", "_test_hothead", "_test_bash5_traits",
	"_test_lockdown_midfielder", "_test_traits", "_test_weather", "_test_wet_weather_play",
	"_test_weather_turns_at_a_break", "_test_wind_and_heat",
	"_test_weather_follows_the_real_games", "_test_metres_and_efficiency"]

var KI
var SQ
var MS
var db


func _initialize() -> void:
	_run.call_deferred()


func _fp(code: String) -> String:
	var l: Array = db.club_list(code)
	var s := 0.0
	var ids := []
	for p in l:
		ids.append(str(p["id"]))
		for k in ["kicking", "marking", "contested_marking", "carry", "intercept", "speed"]:
			s += float(p.get(k, 0.0))
	return "%s n=%d sum=%.1f h=%d" % [code, l.size(), s, hash(",".join(ids))]


func _probe(tag: String) -> void:
	var sim = KI.new(SQ.new("GEE", db.club_list("GEE"), true, "GEE"),
			SQ.new("COL", db.club_list("COL"), false, "COL"), 6101)
	sim.run()
	var kis := 0
	for e in sim.events:
		if bool(e.get("kick_in", false)):
			kis += 1
	print("PKO after %-44s marks=%d credited=%d kick_ins=%d weather=%s tune=%s %s | %s" % [tag,
			sim.marks, sim.credited, kis, sim.weather, str(MS.tune), _fp("GEE"), _fp("COL")])


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
	db = root.get_node("GameDB")
	SQ = load("res://scripts/sim/Squad.gd")
	MS = load("res://scripts/sim/MatchSim.gd")
	var script: GDScript = load("res://tests/test_match_game.gd")
	KI = script.get_script_constant_map()["_SafeKickInMarks"]
	var suite = script.new()
	suite.failures.clear()
	db.skip_ovr_overrides = true
	db.reload()
	_probe("start")
	for fn in ORDER:
		var before: int = suite.failures.size()
		await suite.call(fn)
		_probe("%s (fails %d)" % [fn, suite.failures.size() - before])
	var before2: int = suite.failures.size()
	suite._test_kick_in_mark_not_his_disposal()
	print("PKO real test: new failures %s" % str(suite.failures.slice(before2)))
	quit(0)
