extends RefCounted
## Your own plan (CustomPlan.gd, director 2026-11-12): one strength and one cost,
## a sixth plan that never stacks on another. The lists and their sizes; it
## counters nothing and nothing counters it; the strength grows and shrinks with
## the side, the cost never does; its gates; it changes the match; its work is
## booked to the game plan; save and reload; an older save with a game-plan trait
## drops it; rival clubs build their own.
## Run through tests/run_custom_plan_tests.gd.

var failures: Array[String] = []
var checks := 0
const SUITE_SEED := 2027
const SEEDS := [77, 78, 79, 80]


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	_t("_test_lists")
	_t("_test_clean_and_clash")
	_t("_test_off_plan_neutral")
	_t("_test_counters_nothing")
	_t("_test_strength_scales_cost_does_not")
	_t("_test_gates")
	_t("_test_changes_the_match")
	_t("_test_booked_to_game_plan")
	_t("_test_save_reload")
	_t("_test_old_trait_save")
	_t("_test_rivals_build_one")
	GameState.delete_saved_career()
	CoachEffects.table = {}
	CoachEffects.usual = {}
	CoachEffects.customs = {}
	CoachEffects.my_custom = {}
	GameState.replay_seed = 0
	print(Ran.line("CustomPlan", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


## Every strength and cost has a name, a lever the match has, a size, and a
## line that states the size as a percentage; the sizes sit in one band; a
## strength helps the side running it and a cost hurts it.
func _test_lists() -> void:
	var pct := RegEx.create_from_string("[0-9]+%")
	for strength in [true, false]:
		var ids: Array = CustomPlan.STRENGTH_IDS if strength else CustomPlan.COST_IDS
		_check(ids.size() == (CustomPlan.STRENGTHS if strength else CustomPlan.COSTS).size(),
				"Every entry is in the list's order")
		for id in ids:
			var e := CustomPlan.entry(str(id), strength)
			var v := float(e["size"])
			var good := {"goal": v > 1.0, "opp_goal": v < 1.0, "clangers": v < 1.0, "stoppage": v > 0.0,
					"mid_press": v > 1.0, "legs": v < 1.0, "reach": v > 1.0, "fwd_turnover": v > 1.0,
					"momentum": v > 1.0, "pep": v > 1.0, "gain": v > 1.0, "broken": v < 1.0,
					"inj": v < 1.0, "icept": v < 1.0}
			_check(str(e.get("name", "")) != "" and good.has(str(e.get("lever", ""))),
					"%s has a name and a lever the match has" % id)
			var l := CustomPlan.line(str(id), strength)
			_check(pct.search(l) != null, "%s states its size as a percentage (%s)" % [id, l])
			var sh := CustomPlan.share(e)
			# Fire them up's lift is a share of one call's lift, not of the match.
			var cap := 0.5 if str(e["lever"]) == "pep" else 0.25
			_check(sh >= 0.03 and sh <= cap, "%s moves its lever by a comparable share (%.2f)" % [id, sh])
			_check(bool(good.get(str(e["lever"]), not strength)) == strength,
					"%s is a %s" % [id, "strength" if strength else "cost"])


func _test_clean_and_clash() -> void:
	_check(CustomPlan.clean({"s": "nonsense", "c": "slow"}) == {"name": "", "s": "", "c": "slow"},
			"A strength not on the list is dropped")
	_check(CustomPlan.clash("clean", "loose") and not CustomPlan.clash("clean", "slow"),
			"A strength and a cost on the same lever clash")
	_check(str(CustomPlan.clean({"s": "clean", "c": "loose"})["c"]) == "", "A clashing cost is dropped")
	_check(not CustomPlan.ready({"s": "sharp", "c": ""}) and CustomPlan.ready({"s": "sharp", "c": "slow"}),
			"Built only with a strength and a cost")
	_check(CustomPlan.name_of({"s": "sharp", "c": "slow"}) == CustomPlan.DEFAULT_NAME
			and CustomPlan.name_of({"name": "  The Squeeze  "}) == "The Squeeze",
			"Unnamed it is Our plan; a name is kept trimmed")
	_check(CustomPlan.name_clean("x".repeat(60)).length() == CustomPlan.NAME_MAX, "A name is kept short")
	for s in CustomPlan.STRENGTH_IDS:
		var n := 0
		for c in CustomPlan.COST_IDS:
			if not CustomPlan.clash(str(s), str(c)):
				n += 1
		_check(n >= CustomPlan.COST_IDS.size() - 2, "%s goes with nearly every cost (%d)" % [s, n])


## Built but off it (another plan on), every lever is neutral; the same seed
## plays the same match with or without a built plan on the shelf.
func _test_off_plan_neutral() -> void:
	var sim := _sim({"s": "sharp", "c": "slow"}, 77, 0, "balanced")
	var neutral := true
	for key in ["goal", "gain", "clangers", "legs", "reach", "momentum", "pep", "inj", "icept"]:
		neutral = neutral and sim._gt(0, key) == 1.0
	_check(neutral and sim._gt(0, "stoppage", 0.0) == 0.0, "Off your own plan every lever is neutral")
	_check(_play({}, 77, 0, "balanced") == _play({"s": "sharp", "c": "slow"}, 77, 0, "balanced"),
			"A built plan not in play changes nothing")


## It counters nothing and nothing counters it: no counter names it, a press
## meets it as it meets Balanced, its own press is Balanced's, and a coach who
## counters what he sees stays on his plan against it.
func _test_counters_nothing() -> void:
	_check(not MatchSim.COUNTER.has(CustomPlan.KEY) and not MatchSim.COUNTER.values().has(CustomPlan.KEY),
			"No counter names your own plan")
	_check(not MatchSim.PLANS.has(CustomPlan.KEY), "Your own plan has no plan levers of its own")
	var own := _sim({"s": "squeeze", "c": "slow"}, 77, 0, "custom")
	var bal := _sim({}, 77, 0, "balanced")
	for opp_plan in ["defensive", "contest", "attacking", "controlled", "balanced"]:
		own.tactics[1]["gameplan"] = opp_plan
		bal.tactics[1]["gameplan"] = opp_plan
		_check(own._press_on(0) == bal._press_on(0) and own._press_on(1) == bal._press_on(1),
				"Against %s, the press is the same as Balanced's both ways" % opp_plan)
		for key in ["press", "gain", "contest", "clangers", "goal"]:
			_check(own._pv(0, key) == bal._pv(0, key), "%s: your own plan's %s is Balanced's" % [opp_plan, key])
	# A rival coach who counters what he saw last quarter stays put against it.
	own.current_quarter = MatchSim.COUNTER_Q
	own.tactics_history = [{"quarter": 1, "plans": [{"gameplan": "custom"}, {"gameplan": "defensive"}]}]
	_check(own._counter_plan(1, "defensive") == "", "A rival coach has no counter to your own plan")


## Its strength grows and shrinks with the coaches' execution and how well the
## side knows it; its cost stays as written.
func _test_strength_scales_cost_does_not() -> void:
	var sim := _sim({"s": "clean", "c": "leaky"}, 77, 0, "custom")
	_check(sim._gt(0, "clangers") == CustomPlan.CLEAN_CLANGERS and sim._gt(0, "opp_goal") == CustomPlan.LEAKY_OPP_GOAL,
			"As written on a plain day (%.3f, %.3f)" % [sim._gt(0, "clangers"), sim._gt(0, "opp_goal")])
	(sim.squads[0] as Squad).tactics_exec = 0.5
	_check(is_equal_approx(sim._gt(0, "clangers"), 1.0 + (CustomPlan.CLEAN_CLANGERS - 1.0) * 0.5)
			and sim._gt(0, "opp_goal") == CustomPlan.LEAKY_OPP_GOAL,
			"Half the execution: half the strength, the whole cost")
	(sim.squads[0] as Squad).tactics_exec = 1.0
	(sim.squads[0] as Squad).plan_know = {"custom": 0.8}
	_check(is_equal_approx(sim._gt(0, "clangers"), 1.0 + (CustomPlan.CLEAN_CLANGERS - 1.0) * 0.8)
			and sim._gt(0, "opp_goal") == CustomPlan.LEAKY_OPP_GOAL,
			"Known less well: less of the strength, the whole cost")
	var st := _sim({"s": "stoppage", "c": "slow"}, 77, 0, "custom")
	(st.squads[0] as Squad).tactics_exec = 1.2
	_check(is_equal_approx(st._gt(0, "stoppage", 0.0), CustomPlan.STOPPAGE_WIN * 1.2)
			and st._gt(0, "gain") == CustomPlan.SLOW_GAIN,
			"Sharper coaches: more of an added strength, the cost as written")
	_check(is_equal_approx(MatchSim.upside_scale(st.squads[0], CustomPlan.KEY), 1.2),
			"The gate's size for the list today uses the same factors")


func _test_gates() -> void:
	var sim := _sim({"s": "fast_start", "c": "fade"}, 77, 0, "custom")
	sim.current_quarter = 1
	_check(sim._gt(0, "goal") == CustomPlan.FAST_START_GOAL and sim._gt(0, "legs") == 1.0,
			"Fast out of the blocks: first quarter, sharper shots, legs as usual")
	sim.current_quarter = 4
	_check(sim._gt(0, "goal") == 1.0 and sim._gt(0, "legs") == CustomPlan.LATE_LEGS,
			"Fade late: last quarter, legs go quicker, shots as usual")
	var fr := _sim({"s": "front", "c": "sit"}, 77, 0, "custom")
	fr.team_stats[0]["goals"] = 4.0
	_check(fr._gt(0, "momentum") == 1.0 and fr._gt(0, "opp_goal") == CustomPlan.LEAD_OPP_GOAL,
			"24 points up: in front, but not well in front")
	fr.team_stats[0]["goals"] = 5.0
	fr.momentum = 0.5
	_check(fr._front_run() == CustomPlan.FRONT_MOMENTUM, "30 points up, their run of play counts more")
	fr.team_stats[0]["goals"] = 0.0
	_check(fr._gt(0, "opp_goal") == 1.0, "Level: sitting on a lead costs nothing")


## Strengths and costs change the match; a lever moves its own line.
func _test_changes_the_match() -> void:
	var base := []
	for s in SEEDS:
		base.append(_play({}, s, 0, "balanced"))
	var pairs := [["sharp", "slow"], ["lockdown", "loose"], ["squeeze", "break"], ["fitness", "injuries"],
			["long", "read"], ["fwd_press", "stoppage"], ["stoppage", "leaky"]]
	for pr in pairs:
		var moved := false
		for i in range(SEEDS.size()):
			moved = moved or _play({"s": pr[0], "c": pr[1]}, SEEDS[i], 0, "custom") != base[i]
		_check(moved, "%s with %s changes the match" % pr)
	var cl := {"clean": 0.0, "loose": 0.0}
	for s in SEEDS:
		cl["clean"] += _stat({"s": "clean", "c": "slow"}, s, "clangers")
		cl["loose"] += _stat({"s": "sharp", "c": "loose"}, s, "clangers")
	_check(cl["clean"] < cl["loose"], "Clean hands give away fewer clangers than Loose hands (%s)" % [cl])


## Its work goes to the game plan at full time.
func _test_booked_to_game_plan() -> void:
	var sim := _sim({"s": "sharp", "c": "slow"}, 77, 0, "custom")
	sim.run()
	_check(float((sim.impact[0] as Dictionary).get("gameplan", 0.0)) != 0.0,
			"Your own plan's work is booked to the game plan")
	_check(not MatchSim.DECISION_CAUSES.has("plan_trait") and MatchSim.DECISION_CAUSES.has("gameplan"),
			"No cause of its own at full time")


func _test_save_reload() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	_check(GameState.CLUB_PLANS.has("custom"), "Your own plan is in How we play")
	GameState.set_club_plan("custom")
	_check(GameState.club_plan != "custom", "Your own plan cannot be picked before it is built")
	_check(GameState.set_custom_pick("s", "clean") and not GameState.set_custom_pick("c", "loose")
			and GameState.set_custom_pick("c", "slow"), "Picks are kept, a clash refused")
	GameState.set_custom_name("The Squeeze")
	GameState.set_club_plan("custom")
	_check(GameState.club_plan == "custom" and CoachEffects.my_custom == {"name": "The Squeeze", "s": "clean", "c": "slow"},
			"Built and picked")
	_check(CoachReport.plan_label("custom") == "The Squeeze" and CoachReport.plan_label("custom", false) == CoachReport.THEIR_OWN,
			"Your plan goes by its name, a rival's by what it is")
	_check(GameState.save_career() and GameState.load_career(), "The career saves and loads")
	_check(GameState.club_plan == "custom" and GameState.custom_plan == {"name": "The Squeeze", "s": "clean", "c": "slow"}
			and CoachEffects.my_custom == GameState.custom_plan, "Your own plan survives a reload (%s)" % [GameState.custom_plan])
	var sq := GameState.my_coached_squad()
	_check(sq.custom_plan == GameState.custom_plan, "Your match squad carries it")
	var g := GateOdds.plan_texts_for(sq, "custom")
	_check(str(g[0]).contains("clangers") and str(g[1]).contains("6%"), "The gate says its gain and cost (%s)" % [g])


## An older save with a game-plan trait loads clean and drops it; a save whose
## plan is an unbuilt own plan plays Balanced.
func _test_old_trait_save() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var state: Dictionary = GameState._save_state()
	_check(not state.has("custom_plan"), "A career with no plan of its own saves none")
	state["plan_trait"] = "fortress"
	_check(GameState._restore_career(state) and GameState.custom_plan.is_empty()
			and not GameState._save_state().has("plan_trait"), "An older save with a trait loads and drops it")
	state["club_plan"] = "custom"
	state["custom_plan"] = {"s": "sharp", "c": ""}
	_check(GameState._restore_career(state) and GameState.club_plan == "balanced",
			"An own plan that is not built plays Balanced")


## Every club gets it: some rival coaches build one for the season, on seeded
## dice; their match squad runs it; the scouting report says it in words.
func _test_rivals_build_one() -> void:
	var built := 0
	for code in GameDB.clubs:
		if CustomPlan.ai_builds(str(code), 2026):
			built += 1
			var p := CustomPlan.ai_pick(str(code), 2026)
			_check(CustomPlan.ready(p) and p == CustomPlan.ai_pick(str(code), 2026),
					"%s's plan is built, and the same each time" % code)
	_check(built >= 1 and built <= 10, "Some rival coaches build their own plan (%d)" % built)
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	GameState.rival_plans = {"year": GameState.season_year, "clubs": {}, "usual": {"SYD": "custom"},
			"custom": {"SYD": {"name": "", "s": "lockdown", "c": "slow"}}}
	CoachEffects.usual = {"SYD": "custom"}
	CoachEffects.customs = GameState._season_customs()
	var theirs := Squad.new("Sydney", GameDB.club_list("SYD"), false, "SYD")
	CoachEffects.apply_row(theirs, {"ai": true, "exec": 1.0, "read": 0.0})
	_check(theirs.usual_plan == "custom" and CustomPlan.ready(theirs.custom_plan), "A rival's match squad runs its plan")
	var report := " ".join(GameState.opponent_report("SYD"))
	_check(report.contains("a plan of their own: lock the door, at the cost of slow ball")
			and RegEx.create_from_string("[0-9]+%").search(report) == null,
			"The report on a rival names its plan, in words (%s)" % report.left(300))
	var sim := MatchSim.new(Squad.new("Geelong", GameDB.club_list("GEE"), true, "GEE"), theirs, 77)
	_check(sim._plan(1) == "custom" and is_equal_approx(sim._gt(1, "opp_goal"),
			CustomPlan.lever(CustomPlan.entry("lockdown", true), "opp_goal", 1.0, sim._custom_up(1)))
			and sim._gt(1, "opp_goal") < 1.0,
			"It plays its own plan from the first bounce")
	CoachEffects.usual = {}
	CoachEffects.customs = {}


func _sim(plan: Dictionary, s: int, side := 0, on := "custom") -> MatchSim:
	var h := Squad.new("Geelong", GameDB.club_list("GEE"), true, "GEE")
	var w := Squad.new("Sydney", GameDB.club_list("SYD"), false, "SYD")
	(h if side == 0 else w).custom_plan = plan
	var sim := MatchSim.new(h, w, s)
	(sim.tactics[side] as Dictionary)["gameplan"] = on
	(sim.tactics[1 - side] as Dictionary)["gameplan"] = "balanced"
	return sim


func _play(plan: Dictionary, s: int, side := 0, on := "custom") -> Array:
	var sim := _sim(plan, s, side, on)
	var res: Dictionary = sim.run()
	return [res.get("score", []), sim.injuries.size(), sim.team_stats[0].get("clangers", 0.0),
			sim.team_stats[1].get("intercept_marks", 0.0), sim.team_stats[0].get("metres_gained", 0.0),
			sim.team_stats[1].get("clangers", 0.0), sim.team_stats[1].get("metres_gained", 0.0)]


func _stat(plan: Dictionary, s: int, key: String) -> float:
	var sim := _sim(plan, s)
	sim.run()
	return float(sim.team_stats[0].get(key, 0.0))
