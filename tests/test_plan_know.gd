extends RefCounted
## Plan familiarity (PreSeason.gd, GameState "plan_known"): a side knows each
## game plan well, partly or barely. Two weeks drilling a plan in the
## pre-season (rule 69a: one action a week) move it up a step, the off-season
## slips every plan a step, an unplayed plan fades slowly, and a plan known less
## than well gives less of its upside in the match.

const Tap := preload("res://tests/tap.gd")
const Press := preload("res://tests/preseason_press.gd")

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 5311
const CLUB := "FRE"


func run() -> void:
	GameState.replay_seed = SUITE_SEED
	_t("_test_rules")
	_t("_test_fit_anchors")
	_t("_test_words")
	_t("_test_match_effect")
	_t("_test_drilling")
	_t("_test_ai")
	_t("_test_report_matches_sim")
	_t("_test_off_season_and_fade")
	_t("_test_old_saves")
	await _t("_test_screens")
	_t("_test_group_drills")
	_t("_test_group_credit")
	_t("_test_group_old_saves")
	await _t("_test_group_screen")
	_t("_test_part_rules")
	_t("_test_part_carry")
	_t("_test_part_save")
	await _t("_test_part_screen")
	PreSeason.reload()
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	print(Ran.line("Plan familiarity", self))


func _check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _career(open := true, club := CLUB) -> void:
	GameState.reset()
	GameState.career_seed = SUITE_SEED
	GameState.replay_seed = SUITE_SEED
	GameState.start_season(club, GameDB.club_list(club))
	if open:
		GameState.open_preseason()


## Every level and idle count, in a fixed order, to compare a record with itself.
func _levels() -> String:
	var rows := []
	var codes: Array = GameState.plan_known.keys()
	codes.sort()
	for c in codes:
		for plan in ["balanced"] + PreSeason.DRILL_PLANS:
			rows.append("%s/%s/%.2f" % [c, plan, float(GameState.plan_known[c].get(plan, -1))])
	return ",".join(rows)


func _idles() -> String:
	var rows := []
	var codes: Array = GameState.plan_idle.keys()
	codes.sort()
	for c in codes:
		for plan in PreSeason.DRILL_PLANS:
			rows.append("%s/%s/%d" % [c, plan, int(GameState.plan_idle[c].get(plan, -1))])
	return ",".join(rows)


## Through the rest of the pre-season, each stop answered as it stands and each
## week on the first action open (tests/preseason_press.gd).
func _press_on() -> void:
	var guard := 0
	while GameState.preseason_active() and guard < 30:
		guard += 1
		Press.advance()


## Past the player meetings and the fitness plan (Develop books two weeks of
## running unless said), to the first week waiting on its action.
func _to_week(plan := "develop") -> void:
	GameState.preseason_meetings_done()
	GameState.set_preseason_plan(plan)
	Press.to("week")
	_check(GameState.preseason_stop() == "week", "(setup) a week waits on its action")


## One week trained on action `a` (drilling `plan` when given); the time trial,
## when the week ends on it, seen.
func _week(a: String, plan := "") -> void:
	Press.to("week")
	GameState.set_preseason_action(a)
	if plan != "":
		GameState.set_preseason_drills([plan])
	GameState.preseason_advance()
	if GameState.preseason_stop() == "trial":
		GameState.preseason_advance()


## A year on, straight to the next pre-season. Every plan slips where the
## rollover opens that pre-season
## (GameState.open_preseason, which _start_next_season calls); the rollover
## itself, the season's rounds, the off-season market and the National Draft
## never read or write the plan record, and the rollover alone costs about
## 28 s. So the season is set back to its first round a year on and the
## pre-season opened by hand, through the same call.
func _year_on() -> void:
	var year := GameState.season_year
	GameState.season_year = year + 1
	GameState.season.round_index = 0
	GameState.open_preseason()
	_check(GameState.season_year == year + 1 and GameState.preseason_active() and GameState.preseason_week() == 0,
			"(setup) the next year's pre-season is open")


## One played round as the match engine reports it, for the fade rule
## (GameState._note_plans_played): each entry of `mine` is the plan your side
## played in a quarter, against a Melbourne side on Balanced.
func _round(mine: Array) -> Array:
	var history := []
	for plan in mine:
		history.append({"plans": [{"gameplan": plan}, {"gameplan": "balanced"}]})
	return [{"home": CLUB, "away": "MEL", "tactics_history": history}]


## Two real sides with the squads' familiarity as given ({} = plain).
func _sim(known0: Dictionary, known1: Dictionary, plan0: String, plan1: String, seed_ := 77) -> MatchSim:
	var a := Squad.new("A", GameDB.club_list("FRE"), true, "FRE")
	var b := Squad.new("B", GameDB.club_list("MEL"), false, "MEL")
	a.plan_know = known0
	b.plan_know = known1
	var sim := MatchSim.new(a, b, seed_)
	sim.set_tactics(0, {"gameplan": plan0})
	sim.set_tactics(1, {"gameplan": plan1})
	return sim


# ---------------------------------------------------------------------------
## Bug bash 5 (G15): the league anchors describe today's lists, so the
## average club's fit for each plan is about 1.0 and few sit at a limit.
func _test_fit_anchors() -> void:
	# The anchors describe the game's own lists, with the director's OVR rows
	GameDB.reload()
	var off := []
	var capped := 0
	for plan in PlanFit.NEEDS:
		var sum := 0.0
		var n := 0
		for c in GameDB.club_order:
			# A club yet to enter the league has no list to fit.
			if GameDB.club_list(c).is_empty():
				continue
			var f := PlanFit.fit(Squad.new(c, GameDB.club_list(c), true, c).ground, str(plan))
			sum += f
			n += 1
			if f >= PlanFit.FIT_MAX - 0.001:
				capped += 1
		if n == 0 or absf(sum / n - 1.0) > 0.08:
			off.append("%s %.2f" % [plan, sum / maxi(n, 1)])
	GameDB.reload()
	_check(off.is_empty(), "Each plan's average fit across the league is about 1.0 (%s)" % str(off))
	_check(capped <= GameDB.club_order.size(), "Few club-plan fits sit at the top limit (%d)" % capped)


func _test_rules() -> void:
	PreSeason.reload()
	_check(PreSeason.LEVELS == ["barely", "partly", "well"] and PreSeason.WELL == 2, "Three levels, well on top")
	var start := PreSeason.start_levels("defensive")
	_check(int(start["defensive"]) == 2 and int(start["balanced"]) == 2 and int(start["attacking"]) == 1
			and int(start["contest"]) == 1 and int(start["controlled"]) == 1,
			"A club starts knowing its usual plan and Balanced well, the others partly")
	var slipped := PreSeason.slip_levels(start)
	_check(int(slipped["defensive"]) == 1 and int(slipped["attacking"]) == 0 and int(slipped["balanced"]) == 2,
			"The off-season slips every plan a step but Balanced")
	var twice := PreSeason.slip_levels(slipped)
	_check(int(twice["attacking"]) == 0 and int(twice["defensive"]) == 0 and int(twice["balanced"]) == 2,
			"...and nothing slips below barely")
	_check(PreSeason.clean_drills(["contest", "bogus", "contest", "attacking"]) == ["contest"],
			"A drilling week drills one real plan (rule 69a)")
	_check(PreSeason.clean_drills(["balanced"]).is_empty() and PreSeason.clean_drills("x").is_empty(),
			"Balanced is not drilled, and bad input is nothing")
	var one := PreSeason.drill_credit([{"a": "run"}, {"a": "drill", "d": ["contest"]}, {"a": "bond", "card": "x"}])
	_check(is_equal_approx(float(one["contest"]), 1.0) and one.size() == 1,
			"A drilling week is one week on its plan; running and bonding weeks drill nothing")
	var two := PreSeason.drill_credit([{"a": "drill", "d": ["contest"]}, {"a": "run"}, {"a": "drill", "d": ["contest"]}])
	_check(is_equal_approx(float(two["contest"]), 2.0) and PreSeason.drilled_level(0, 2.0) == 1
			and PreSeason.drilled_level(0, 1.9) == 0,
			"Two weeks drilling one plan is one step, whenever they fall")
	_check(PreSeason.drilled_level(1, 3.0) == 2 and PreSeason.drilled_level(2, 9.0) == 2, "...and well is the top")
	_check(PreSeason.ai_action(6, 0, "defensive", 1.0) == "drill" and PreSeason.ai_action(6, 0, "defensive", 2.0) == "bond"
			and PreSeason.ai_action(6, 0, "balanced", 0.0) == "bond",
			"A rival drills its usual plan until the side knows it well, then bonds; on Balanced it bonds")
	_check(PreSeason.familiar_mult(2) == 1.0 and PreSeason.familiar_mult(1) < 1.0
			and PreSeason.familiar_mult(0) < PreSeason.familiar_mult(1) and PreSeason.familiar_mult(0) > 0.0,
			"Knowing a plan less gives less of it, never nothing")


func _test_words() -> void:
	PreSeason.reload()
	_check(PreSeason.known_line(2) == "Plan fluency: high" and PreSeason.known_line(1) == "Plan fluency: medium"
			and PreSeason.known_line(0) == "Plan fluency: low", "The three lines, in the director's words")
	_check(PreSeason.drill_sentence(["defensive"]) == "Fluency in High Press rises a step for every 2 weeks on it.",
			"A drilling week says what it drills and what that gains")


func _test_match_effect() -> void:
	PreSeason.reload()
	var partly := PreSeason.familiar_mult(1)
	var barely := PreSeason.familiar_mult(0)
	var known := _sim({}, {}, "attacking", "balanced")
	var part := _sim({"attacking": partly}, {}, "attacking", "balanced")
	var bare := _sim({"attacking": barely}, {}, "attacking", "balanced")
	var g0 := known._pv(0, "goal")
	var g1 := part._pv(0, "goal")
	var g2 := bare._pv(0, "goal")
	_check(g0 > g1 and g1 > g2 and g2 > 1.0 - 0.1,
			"A plan known less gives less of its upside, step by step (goal %.4f > %.4f > %.4f)" % [g0, g1, g2])
	_check(is_equal_approx(known._pv(0, "pace"), bare._pv(0, "pace"))
			and is_equal_approx(known._pv(0, "clangers"), bare._pv(0, "clangers")),
			"...but what the plan gives up (legs, clangers) does not move")
	var other := _sim({"defensive": barely}, {}, "attacking", "balanced")
	_check(is_equal_approx(other._pv(0, "goal"), g0), "Knowing another plan badly does not touch the one being run")
	var opp := _sim({}, {"defensive": barely}, "attacking", "defensive")
	var opp0 := _sim({}, {}, "attacking", "defensive")
	_check(opp._pv(1, "press") < opp0._pv(1, "press") and is_equal_approx(opp._pv(0, "goal"), opp0._pv(0, "goal")),
			"The press known barely presses less, and leaves the other side alone")
	_check(is_equal_approx(_sim({"balanced": barely}, {}, "balanced", "balanced")._pv(0, "goal"), 1.0),
			"Balanced has no upside to lose")
	# The checks above prove the rule at the one place the engine reads a plan's
	# upside (MatchSim._pv). A real match on the same dice proves a played match
	# reads it: knowing the plan barely changes how the match goes. Attacking,
	# whose goal upside the checks above show moving on these two sides; up to
	# three seeds, as one match can end on the same score. How much it moves the
	# margin is measured over 200 seeds by tools/audit/plan_know_impl.gd (+1.2
	# points), not replayed on every CI run (director, 2026-11-14).
	var seen := []
	var moved := false
	for s in range(3):
		var ra := _sim({}, {}, "attacking", "balanced", 900 + s).run()
		var rb := _sim({"attacking": barely}, {}, "attacking", "balanced", 900 + s).run()
		seen.append("%s/%s" % [str(ra["score"]), str(rb["score"])])
		if str(ra["score"]) + str(ra.get("goals", "")) != str(rb["score"]) + str(rb.get("goals", "")):
			moved = true
			break
	_check(moved, "A played match reads how well the side knows its plan (known well/barely: %s)" % ", ".join(seen))


func _test_drilling() -> void:
	PreSeason.reload()
	_career(false)
	GameState.set_club_plan("attacking")
	GameState.open_preseason()
	_check(GameState.plan_known.size() == GameState.season.clubs.size(), "Every club has a record from the first pre-season")
	_check(GameState.plan_level(CLUB, "attacking") == 2 and GameState.plan_level(CLUB, "contest") == 1
			and GameState.plan_level(CLUB, "balanced") == 2,
			"A new career: the plan you play and Balanced known well, the others partly")
	_to_week()
	_check(GameState.preseason_drills().is_empty() and not GameState.set_preseason_drills(["contest"]),
			"No plan is drilled until the week is set to Game plan drilling")
	_check(GameState.set_preseason_action("drill") and GameState.preseason_drills() == ["attacking"],
			"A drilling week drills the plan you play until you say otherwise")
	_check(GameState.set_preseason_drills(["contest", "controlled"]) and GameState.preseason_drills() == ["contest"],
			"...one plan a week")
	_check(not GameState.set_preseason_drills(["balanced"]) and GameState.preseason_drills() == ["contest"],
			"...and Balanced cannot be drilled")
	_check(GameState.plan_fluency_after_drills("contest") == 1.5 and GameState.plan_level_after_drills("contest") == 1,
			"One week takes a plan half way to the next level (the page says so before it is trained)")
	_check(GameState.set_preseason_action("run") and GameState.preseason_drills().is_empty(),
			"A running week drills nothing")
	_week("drill", "contest")
	_check(GameState.preseason_week() == 1, "(setup) week 1 is trained")
	_check(GameState.plan_level(CLUB, "contest") == 1, "A plan is not known better until the pre-season is done")
	_week("drill", "contest")
	_check(GameState.plan_level_after_drills("contest") == 2, "Two weeks on a plan lifts it a step")
	_week("drill", "defensive")
	_week("drill", "defensive")
	_check(GameState.preseason_week() == 4, "(setup) four weeks trained, past the time trial")
	_press_on()
	_check(not GameState.preseason_active(), "(setup) the pre-season is done")
	_check(GameState.plan_level(CLUB, "contest") == 2 and GameState.plan_level(CLUB, "defensive") == 2
			and GameState.plan_level(CLUB, "controlled") == 1 and GameState.plan_level(CLUB, "attacking") == 2,
			"Drilled plans are known well by Round 1; the rest are as they were")
	var news := ""
	for n in GameState.news:
		news += str(n).to_lower() + " "
	_check("fluency in win contest is now high" in news, "...and the club's news says which")
	GameState._refresh_coach_tactics()
	var sq := Squad.new("A", GameDB.club_list(CLUB), true, CLUB)
	CoachEffects.apply(sq)
	_check(CoachEffects.table.is_empty() or not sq.plan_know.is_empty(), "A match squad carries what its club knows")


## Rivals follow "Drill, then bond" (rule 69a): the booked running first, then
## the usual plan drilled until the side knows it well, then bonding.
func _test_ai() -> void:
	PreSeason.reload()
	_career(false)
	GameState.open_preseason()
	var before := {}
	for club in GameState.season.clubs:
		before[str(club)] = GameState._usual_plan(str(club))
	_press_on()
	# The first year every usual plan starts known well, so no rival drills it.
	var drilled_well := 0
	for code in before:
		if str(code) != CLUB and _drill_weeks(str(code), str(before[code])) > 0:
			drilled_well += 1
	_check(drilled_well == 0, "A rival that knows its usual plan well bonds instead of drilling it (%d drilled)" % drilled_well)
	# What the season did to each record is the fade test's business: here every
	# club is known well on the plan it opened on, so the off-season is on its own.
	for code in before:
		if PreSeason.DRILL_PLANS.has(str(before[code])):
			GameState.plan_known[code][before[code]] = PreSeason.WELL
	_year_on()
	var usual := {}
	for club in GameState.season.clubs:
		usual[str(club)] = GameState._usual_plan(str(club))
	_press_on()
	var kept := 0
	var back := 0
	var balanced := 0
	var balanced_drills := 0
	for code in usual:
		if str(code) == CLUB:
			continue
		if str(usual[code]) == "balanced":
			balanced += 1
			balanced_drills += _drill_weeks(str(code), "")
			continue
		if str(before.get(code, "")) != str(usual[code]):
			continue
		kept += 1
		back += 1 if GameState.plan_level(str(code), str(usual[code])) == 2 and _drill_weeks(str(code), str(usual[code])) == 2 else 0
	_check(kept > 0 and back == kept,
			"A year on, a rival still on the same usual plan slipped and drilled it two weeks, back to well (%d of %d)" % [back, kept])
	_check(balanced_drills == 0, "...and a rival on Balanced drills nothing (%d clubs)" % balanced)


## A club's drilling weeks this pre-season on `plan` ("" for any plan).
func _drill_weeks(code: String, plan: String) -> int:
	var n := 0
	for wk in GameState.preseason_entry(code).get("acts", []):
		if wk is Dictionary and str(wk.get("a", "")) == "drill" and (plan == "" or (wk.get("d", []) as Array).has(plan)):
			n += 1
	return n


## The Assistant's report names, for every club, the usual game the match
## engine really opens with: the same side, weighed by the same plan knowledge.
func _test_report_matches_sim() -> void:
	PreSeason.reload()
	# One career through the three stages: the report and the sim below only read it.
	_career(true)
	for stage in ["fresh career", "after the pre-season", "each usual plan barely known"]:
		if stage == "after the pre-season":
			_press_on()
		if stage == "each usual plan barely known":
			# Knowledge apart from the list: a club that has let its usual plan
			# slip opens with another, and the report must say so too. The
			# knowledge weights are widened so the slip moves the plan at all.
			PreSeason.data()["familiar_mult"] = {"well": 1.0, "partly": 0.5, "barely": 0.1}
			for club in GameState.season.clubs:
				var bare := GameState._usual_plan(str(club))
				if PreSeason.DRILL_PLANS.has(bare):
					GameState.plan_known[str(club)][bare] = 0
		var wrong := []
		var changed := []
		for club in GameState.season.clubs:
			var code := str(club)
			var home := Squad.new(code, GameState.season.lists[code], true, code, GameState.season.selections.get(code, {}))
			var away := Squad.new("X", GameDB.club_list(CLUB), false, CLUB)
			CoachEffects.apply(home)
			var sim := MatchSim.new(home, away, 77)
			var report := GameState.usual_plan(code)
			if report != sim._usual(0):
				wrong.append("%s: report %s, sim %s" % [code, report, sim._usual(0)])
			var bare := PlanFit.standing_plan(home.ground)
			if bare != report:
				changed.append(code)
		_check(wrong.is_empty(), "%s: the report's usual plan is the one the sim opens with (%s)" % [stage, ", ".join(wrong)])
		if stage == "each usual plan barely known":
			_check(not changed.is_empty(), "...and with a usual plan let slip, some clubs open with another")
		print("  usual plan, %s: %d of %d clubs differ from the plan named without plan knowledge %s" % [stage, changed.size(), GameState.season.clubs.size(), changed])
	PreSeason.reload()


func _test_off_season_and_fade() -> void:
	PreSeason.reload()
	_career(false)
	GameState.set_club_plan("attacking")
	GameState.open_preseason()
	GameState.plan_known[CLUB]["contest"] = 1
	_press_on()
	# One real round proves the round's results reach the record: with a plan
	# fading after one round unplayed, the plan you play stays and one you never
	# touched slips a step.
	PreSeason.data()["fade_rounds"] = 1
	GameState.advance()
	_check(GameState.plan_level(CLUB, "contest") == 0, "A real round: the plan left unplayed knows it a step less")
	_check(GameState.plan_level(CLUB, "attacking") == 2, "...while the plan played stays well")
	# The counting itself, round by round, on the rule the round calls.
	PreSeason.data()["fade_rounds"] = 3
	GameState.plan_known[CLUB]["contest"] = 1
	GameState.plan_idle[CLUB]["contest"] = 0
	GameState.plan_idle[CLUB]["attacking"] = 0
	for i in range(2):
		GameState._note_plans_played(_round(["attacking", "attacking", "attacking", "attacking"]))
	_check(GameState.plan_level(CLUB, "contest") == 1, "Two rounds unplayed: a plan has not faded yet")
	GameState._note_plans_played(_round(["attacking", "attacking", "attacking", "attacking"]))
	_check(GameState.plan_level(CLUB, "contest") == 0, "...but after the third it knows it a step less")
	_check(GameState.plan_level(CLUB, "attacking") == 2, "...while the plan played every week stays well")
	for i in range(4):
		GameState._note_plans_played(_round(["attacking"]))
	_check(GameState.plan_level(CLUB, "contest") == 0, "...and nothing fades below barely")
	# Balanced is the plan put down: your assistant calls the main three in
	# your name (chasing, protecting, countering), never Balanced unless it is
	# the plan you went in with, so once dropped nothing plays it.
	GameState.plan_known[CLUB]["contest"] = 2
	GameState.plan_idle[CLUB]["contest"] = 0
	for i in range(4):
		GameState._note_plans_played(_round(["contest", "attacking", "contest", "contest"]))
	_check(GameState.plan_level(CLUB, "contest") == 2, "A plan played in matches keeps its place")
	GameState.plan_known[CLUB]["defensive"] = 2
	GameState.plan_idle[CLUB]["defensive"] = 0
	for i in range(4):
		GameState._note_plans_played(_round(["defensive", "defensive", "controlled", "defensive"]))
	_check(GameState.plan_level(CLUB, "defensive") == 2, "...as does the one taken up")
	_check(GameState.plan_level(CLUB, "contest") <= 1, "...and the one put down fades")
	var snapshot := _levels()
	var idle := _idles()
	GameState.save_career()
	var saved := CareerSave.read(GameState.save_path)
	_check(saved.has("plan_known") and saved.has("plan_idle"), "The save holds the record")
	GameState.load_career()
	_check(_levels() == snapshot and _idles() == idle, "...and it comes back as saved")
	PreSeason.reload()
	GameState.set_club_plan("controlled")
	GameState.plan_known[CLUB]["controlled"] = 2
	GameState.plan_known[CLUB]["contest"] = 1
	GameState.plan_known[CLUB]["defensive"] = 2
	_year_on()
	_check(GameState.plan_level(CLUB, "contest") == 0 and GameState.plan_level(CLUB, "defensive") == 1
			and GameState.plan_level(CLUB, "balanced") == 2,
			"Over the off-season every plan slips a step, and nothing but Balanced is safe")
	# Peak books five weeks of running: the two weeks after it, left on drilling
	# as they come, drill the plan you play.
	_to_week("peak")
	_press_on()
	_check(_drill_weeks(CLUB, "controlled") == 2, "...a drilling week left as it comes drills the plan you play (%d weeks)" % _drill_weeks(CLUB, "controlled"))
	_check(GameState.plan_level(CLUB, "controlled") == 2, "...which brings it back to well")


func _test_old_saves() -> void:
	PreSeason.reload()
	_career(false)
	GameState.set_club_plan("contest")
	# A save from two rounds in: the rounds themselves are not what is tested.
	GameState.season.round_index = 2
	GameState.save_career()
	var state := CareerSave.read(GameState.save_path)
	state.erase("plan_known")
	state.erase("plan_idle")
	CareerSave.write(state, GameState._save_meta(), GameState.save_path)
	_check(GameState.load_career() and GameState.plan_known.is_empty(), "A save from before familiarity loads, with no record")
	GameState.replay_seed = SUITE_SEED
	GameState.advance()
	_check(GameState.plan_known.size() == GameState.season.clubs.size(), "...and the next round gives every club one")
	_check(GameState.plan_level(CLUB, "contest") == 2 and GameState.plan_level(CLUB, "attacking") == 1
			and GameState.plan_level(CLUB, "balanced") == 2,
			"...with the plan you play known well and the rest partly")
	var sane := true
	for club in GameState.plan_known:
		for plan in GameState.plan_known[club]:
			var l := int(GameState.plan_known[club][plan])
			sane = sane and l >= 0 and l <= 2
	_check(sane, "...every level in range")
	GameState.save_career()
	var bad := CareerSave.read(GameState.save_path)
	bad["plan_known"] = {CLUB: {"contest": 9, "attacking": -4, "junk": "x"}, "BAD": 5}
	bad["plan_idle"] = {CLUB: "x"}
	CareerSave.write(bad, GameState._save_meta(), GameState.save_path)
	GameState.load_career()
	_check(GameState.plan_level(CLUB, "contest") == 2 and GameState.plan_level(CLUB, "attacking") == 0,
			"A damaged record is clamped, not trusted")


func _test_screens() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.size = Vector2i(390, 844)
	PreSeason.reload()
	_career(false)
	GameState.set_club_plan("attacking")
	GameState.open_preseason()
	GameState.set_setting("seen_weekly_loop_intro", true)
	_to_week()
	var scene: Control = await _open(tree)
	_check(scene != null and scene.name == "PreSeasonScene", "The pre-season opens on the week")
	_check(scene.find_child("DrillPicker", true, false) == null, "The drill choice stays out of the way until the week is on drilling")
	var pick := scene.find_child("ActionTap_drill", true, false) as Control
	await _into_view(tree, pick)
	_check(await _tap(pick, "Game plan drilling"), "A finger sets the week to Game plan drilling")
	await _frames(tree, 4)
	_check(str(GameState.preseason_next().get("a", "")) == "drill" and scene.find_child("DrillPicker", true, false) != null,
			"...and the drill choice appears")
	_check(_label(scene, "ActionGain_drill").begins_with("A week on attack corridor, known high now."),
			"...the gain says what it drills: " + _label(scene, "ActionGain_drill"))
	_check(_label(scene, "ActionCost_drill") == "No running or bonding this week.", "...and the cost, the week's other jobs")
	var contest := scene.find_child("Drill_contest", true, false) as Button
	_check(contest != null and contest.text == "Win Contest\nmedium", "Each plan says how well the side knows it")
	_check((scene.find_child("Drill_attacking", true, false) as Button).text == "Attack Corridor\nhigh",
			"The plan you play has high fluency, and a week on it can add nothing")
	await _into_view(tree, contest)
	_check(await _tap(contest, "Win Contest to drill"), "A finger picks Win Contest to drill")
	await _frames(tree, 4)
	_check(GameState.preseason_drills() == ["contest"], "...which is the week's plan")
	contest = scene.find_child("Drill_contest", true, false) as Button
	_check(contest.text == "Win Contest\nmedium\nRd 1: 50% to high", "One week goes half a step, and the button says so: " + contest.text)
	var other := scene.find_child("Drill_controlled", true, false) as Button
	await _into_view(tree, other)
	_check(await _tap(other, "another plan"), "A finger picks another plan")
	await _frames(tree, 4)
	_check(GameState.preseason_drills() == ["controlled"], "...which takes its place: one plan a week")
	_check(_fits(scene, 390.0), "...and nothing runs off a phone's width")
	# Straight to Round 1: the weeks between drill nothing these checks read.
	GameState._finish_preseason()
	_check(not GameState.preseason_active(), "(setup) the pre-season is done")
	GameState.plan_known["FRE"]["controlled"] = 0
	var tiles := PlanTiles.grid(2, [], [])
	tree.root.add_child(tiles)
	await _frames(tree, 2)
	var t_c := tiles.find_child("ClubPlan_controlled", true, false)
	var t_a := tiles.find_child("ClubPlan_attacking", true, false)
	_check(t_c != null and (t_c.find_child("Known", true, false) as Label).text == "Plan fluency: low"
			and (t_a.find_child("Known", true, false) as Label).text == "Plan fluency: high",
			"The pre-match plan tiles carry the same line, in the same words")
	tiles.queue_free()
	# The first break of a coached match: the plan call says it, in full ink.
	GameState.plan_known[CLUB]["contest"] = 0
	GameState.plan_known[CLUB]["defensive"] = 1
	_check(GameState.prepare_interactive_match(), "A match is ready to coach")
	Router.stack = ["main"]
	Router.go("match")
	await _frames(tree, 40)
	var match_scene := tree.current_scene as Control
	var note := match_scene.find_child("PlanKnown", true, false) as Label if match_scene != null else null
	var pick_stars := match_scene.find_child("PlanPicker_contest", true, false) as Button if match_scene != null else null
	_check(note != null and pick_stars != null, "The break has the plan call and a line for how well the side knows it")
	if note != null and pick_stars != null:
		_check(note.text == "Plan fluency: high", "...on the plan the side opens on: " + note.text)
		_check(await _tap(pick_stars, "Win Contest at the break"), "A finger picks another plan")
		_check(note.text == "Plan fluency: low" and note.visible and note.get_theme_color("font_color") == UiKit.TEXT,
				"...and the line follows it, at full strength: " + note.text)
		await _tap(match_scene.find_child("PlanPicker_defensive", true, false) as Button, "High Press at the break")
		_check(note.text == "Plan fluency: medium", "...in the same three words: " + note.text)


# ---------------------------------------------------------------------------
# Row 101 (director, 2026-11-06: "split it between position groups"): a
# drilling week's plan for the mids, the defenders, the forwards and the rucks.
# ---------------------------------------------------------------------------
func _test_group_drills() -> void:
	PreSeason.reload()
	_career()
	_to_week()
	_check(not GameState.set_preseason_drills(["contest"], "MID"), "A week not on drilling has no drills to split")
	_check(GameState.set_preseason_action("drill"), "The week goes on Game plan drilling")
	var side: Array = GameState.preseason_drills()
	var same := not side.is_empty() and not GameState.preseason_drills_split()
	for g in PreSeason.GROUPS:
		same = same and GameState.preseason_drills(g) == side
	_check(same and not GameState.preseason_next().has("s"), "Every group drills the week's plan, and the save holds just that")
	var want := {"MID": ["contest"], "DEF": ["defensive"], "FWD": ["controlled"], "RUCK": ["attacking"]}
	for g in want:
		_check(GameState.set_preseason_drills(want[g], g), "The %s get their own drills" % str(PreSeason.GROUP_LABEL[g]).to_lower())
	var plans := {}
	for g in PreSeason.GROUPS:
		plans[str(GameState.preseason_drills(g))] = g
	_check(plans.size() == 4 and GameState.preseason_drills("FWD") == ["controlled"],
			"Four group drill plans, each its own: %s" % str(plans.keys()))
	_check(GameState.preseason_drills() == side, "...and the whole side's line is as it was")
	_check(GameState.set_preseason_action("drill") and GameState.preseason_drills("DEF") == ["defensive"],
			"Picking drilling again keeps each group's drills")
	_check(not GameState.set_preseason_drills(["contest"], "WING"), "A group the game does not have is refused")
	GameState.set_preseason_drills(side, "MID")
	GameState.set_preseason_drills(side, "DEF")
	_check(GameState.preseason_drills_split() and GameState.preseason_drills("MID") == side,
			"A group put back on the side's drills just follows the side")
	_check(GameState.set_preseason_drills(["controlled"]), "A pick for the whole side")
	var all := not GameState.preseason_drills_split()
	for g in PreSeason.GROUPS:
		all = all and GameState.preseason_drills(g) == ["controlled"]
	_check(all and not GameState.preseason_next().has("s"), "...sets every group, and the week is one plan again")
	GameState.set_preseason_drills(["contest"], "RUCK")
	GameState.set_preseason_action("run")
	_check(GameState.preseason_drills("RUCK").is_empty() and not GameState.preseason_next().has("s"),
			"Off drilling, the week drills nothing for anyone")


func _test_group_credit() -> void:
	PreSeason.reload()
	_career()
	var shares := PreSeason.group_shares(GameState.my_list)
	var total := 0.0
	var empty := 0
	for g in shares:
		total += float(shares[g])
		empty += 1 if float(shares[g]) <= 0.0 else 0
	_check(is_equal_approx(total, 1.0) and empty == 0, "Every group is on the list, and the shares add up to it")
	_to_week()
	GameState.set_preseason_action("drill")
	GameState.set_preseason_drills(["attacking"])
	var whole := GameState.my_drill_credit()
	_check(is_equal_approx(float(whole.get("attacking", 0.0)), 1.0)
			and str(whole) == str(PreSeason.drill_credit([GameState.preseason_next()])),
			"One plan for every group: one week on it")
	GameState.set_preseason_drills(["contest"], "DEF")
	var split := GameState.my_drill_credit()
	_check(is_equal_approx(float(split.get("contest", 0.0)), float(shares["DEF"]))
			and is_equal_approx(float(split.get("attacking", 0.0)), 1.0 - float(shares["DEF"])),
			"The side's drilling counts each group by its share: contest %.2f, attacking %.2f" % [
			float(split.get("contest", 0.0)), float(split.get("attacking", 0.0))])
	GameState.preseason_advance()
	var taken := GameState.my_drill_credit()
	_check(GameState.preseason_week() == 1 and str(taken) == str(split),
			"The week trained counts as the week set: %s" % str(taken))


func _test_group_old_saves() -> void:
	PreSeason.reload()
	_career()
	_to_week()
	GameState.set_preseason_action("drill")
	GameState.set_preseason_drills(["attacking"])
	GameState.set_preseason_drills(["contest"], "FWD")
	GameState.save_career()
	_check(GameState.load_career() and GameState.preseason_drills("FWD") == ["contest"]
			and GameState.preseason_drills("MID") == ["attacking"],
			"A group's own drills are kept through a save and a load")
	# A save from before the rework (2026-11-17), at the end of week 5: its second
	# block (weeks 4 and 5) drilled Attack Corridor with the forwards on Win Contest.
	var state := CareerSave.read(GameState.save_path)
	state["preseason"]["week"] = 5
	state["preseason"].erase("next")
	state["preseason"]["clubs"][CLUB] = {"blocks": [["solid", "running"], ["solid", "plan", ["attacking"], {"FWD": ["contest"]}],
			["solid", "skills"]]}
	CareerSave.write(state, GameState._save_meta(), GameState.save_path)
	_check(GameState.load_career(), "A save from before the weekly actions loads")
	var acts: Array = GameState.preseason_entry().get("acts", [])
	_check(acts.size() == 5 and str(acts[3]) == str({"a": "drill", "d": ["attacking"], "s": {"FWD": ["contest"]}})
			and str(acts[4]) == str(acts[3]),
			"...its drilling weeks keep the forwards' own drills: %s" % str(acts))
	_check(GameState.preseason_stop() == "week" and not GameState.preseason_actions().is_empty(), "...and its next week waits on an action")
	Press.advance()
	_check(GameState.preseason_week() == 6, "...and its pre-season trains on")


func _test_group_screen() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.size = Vector2i(360, 800)
	PreSeason.reload()
	_career(false)
	GameState.open_preseason()
	GameState.set_setting("seen_weekly_loop_intro", true)
	_to_week()
	GameState.set_preseason_action("drill")
	GameState.set_preseason_drills(["attacking"])
	var scene: Control = await _open(tree)
	_check(scene != null and scene.name == "PreSeasonScene", "The pre-season opens")
	var whole := scene.find_child("DrillFor_ALL", true, false) as Button
	var fwd := scene.find_child("DrillFor_FWD", true, false) as Button
	_check(whole != null and fwd != null and bool(whole.get_meta("chosen", false)),
			"A drilling week's drills show the whole side until the coach picks a group")
	_check(_label(scene, "DrillSplit").begins_with("Every group drills the same"), "...and the line under the tabs says so")
	var gaps := _tab_gaps(scene.find_child("DrillFor", true, false) as Control)
	_check(gaps.size() == 4 and gaps.min() >= 8.0 and gaps.max() <= gaps.min() * 2.0,
			"The five group names sit evenly apart on a phone, never run together: gaps %s" % [gaps])
	var narrowest := 999.0
	for t in (scene.find_child("DrillFor", true, false) as Control).get_children():
		narrowest = minf(narrowest, (t as Control).size.x)
	_check(narrowest >= 36.0, "...and each is a thumb wide at least (narrowest %.0f)" % narrowest)
	await _into_view(tree, fwd)
	_check(await _tap(fwd, "Forwards"), "A finger picks the forwards")
	await _frames(tree, 4)
	fwd = scene.find_child("DrillFor_FWD", true, false) as Button
	_check(bool(fwd.get_meta("chosen", false)) and _label(scene, "DrillSplit").begins_with("The forwards: "),
			"...the forwards' tab is on and the line says how many: " + _label(scene, "DrillSplit"))
	var contest := scene.find_child("Drill_contest", true, false) as Button
	await _into_view(tree, contest)
	_check(await _tap(contest, "Contest for the forwards"), "A finger sets the forwards on Win Contest")
	await _frames(tree, 4)
	_check(GameState.preseason_drills("FWD") == ["contest"] and GameState.preseason_drills("MID") == ["attacking"]
			and GameState.preseason_drills() == ["attacking"],
			"...which reaches the forwards alone")
	whole = scene.find_child("DrillFor_ALL", true, false) as Button
	await _into_view(tree, whole)
	_check(await _tap(whole, "All"), "A finger goes back to All, the whole side")
	await _frames(tree, 4)
	contest = scene.find_child("Drill_contest", true, false) as Button
	_check(not bool(contest.get_meta("chosen", false)) and "Forwards: Win Contest" in _label(scene, "DrillSplit"),
			"...which marks no plan and names the split: " + _label(scene, "DrillSplit"))
	_check(_fits(scene, 360.0), "...and nothing runs off a phone's width")


# ---------------------------------------------------------------------------
# Row 126 (director, 2026-11-08: "Partial weeks count"): weeks short of a step go
# into the season as part of one, and the plan button says how far along it is.
func _test_part_rules() -> void:
	PreSeason.reload()
	var one := PreSeason.drill_credit([{"a": "run"}, {"a": "drill", "d": ["contest"]}, {"a": "run"}])
	_check(is_equal_approx(float(one["contest"]), 1.0) and is_equal_approx(PreSeason.drilled_fluency(1.0, float(one["contest"])), 1.5),
			"One drilling week gives its plan half a step")
	_check(PreSeason.drilled_fluency(0.5, 1.0) == 1.0 and PreSeason.drilled_fluency(1.75, 3.0) == 2.0,
			"Parts add up to a step, and high is the top")
	_check(PreSeason.drilled_fluency(0.0, 2.0 / 3.0 + 2.0 / 3.0 + 2.0 / 3.0) == 1.0,
			"Thirds of a week that make a step are a step, not 99% of one")
	_check(PreSeason.fluency_short(1.0) == "medium" and PreSeason.fluency_short(1.5) == "50% to high"
			and PreSeason.fluency_short(0.25) == "25% to medium" and PreSeason.fluency_short(2.0) == "high",
			"The button's words")
	_check(PreSeason.fluency_long(0.5) == "50% of the way to medium" and PreSeason.fluency_long(0.0) == "low", "...and a sentence's")
	_check(PreSeason.known_line(1.5) == "Plan fluency: 50% to high" and PreSeason.known_line(1) == "Plan fluency: medium",
			"The plan tile's line")
	var a := PreSeason.familiar_mult(1)
	var b := PreSeason.familiar_mult(2)
	_check(is_equal_approx(PreSeason.familiar_mult(1.5), (a + b) / 2.0) and PreSeason.familiar_mult(1.25) < PreSeason.familiar_mult(1.5),
			"Part of a step plays that part of the way between the levels")
	var slipped := PreSeason.slip_levels({"contest": 1.5, "attacking": 0.5, "balanced": 2})
	_check(float(slipped["contest"]) == 0.5 and float(slipped["attacking"]) == 0.0 and int(slipped["balanced"]) == 2,
			"The off-season slips a whole step, the part with it, and never below low")
	var low_part := _sim({"attacking": PreSeason.familiar_mult(0.5)}, {}, "attacking", "balanced")
	var low := _sim({"attacking": PreSeason.familiar_mult(0)}, {}, "attacking", "balanced")
	var medium := _sim({"attacking": PreSeason.familiar_mult(1)}, {}, "attacking", "balanced")
	_check(low_part._pv(0, "goal") > low._pv(0, "goal") and low_part._pv(0, "goal") < medium._pv(0, "goal"),
			"In the match itself a half step is more of the plan than low, less than medium")
	var se = load("res://scripts/sim/StoryEngine.gd")
	var w1: String = se._drill_words(1, {"drill_plan": "Win Contest", "drill_level": 1.0, "drill_credit": 0.0})
	_check("from medium to 50% of the way to high" in w1 and "works at 98% of its strength, not 95%" in w1,
			"A card's extra week is worth part of a step, and says so: " + w1)
	var top: String = se._drill_words(1, {"drill_plan": "Win Contest", "drill_level": 2.0, "drill_credit": 0.0})
	_check("Nothing more to gain" in top, "...and at the top it says there is nothing to gain")


func _test_part_carry() -> void:
	PreSeason.reload()
	_career(false)
	GameState.set_club_plan("attacking")
	GameState.open_preseason()
	GameState.news.clear()
	_to_week()
	GameState.set_preseason_action("drill")
	GameState.set_preseason_drills(["contest"])
	_check(GameState.plan_fluency_after_drills("contest") == 1.5, "The page knows where one week leaves a plan")
	GameState.preseason_advance()
	_press_on()
	_check(GameState.plan_fluency(CLUB, "contest") == 1.5, "One week on a plan moves it half a step, carried into the season")
	_check(GameState.plan_level(CLUB, "contest") == 1, "...still medium to whatever asks for the level")
	_check(GameState.plan_fluency(CLUB, "defensive") == 1.0, "...and a plan nobody drilled is as it was")
	var news := ""
	for n in GameState.news:
		news += str(n).to_lower() + " "
	_check("fluency in win contest is now 50% of the way to high" in news, "The club's news says how far: " + news.left(160))
	GameState._refresh_coach_tactics()
	var sq := Squad.new("A", GameDB.club_list(CLUB), true, CLUB)
	CoachEffects.apply(sq)
	_check(is_equal_approx(float(sq.plan_know.get("contest", 0.0)), PreSeason.familiar_mult(1.5))
			and is_equal_approx(float(sq.plan_know.get("defensive", 0.0)), PreSeason.familiar_mult(1)),
			"The match squad carries the part step: %s" % [sq.plan_know])
	_check(GameState.plan_known_line("contest") == "Plan fluency: 50% to high", "The season's plan line says it")
	# Fade: a whole step, the part with it.
	PreSeason.data()["fade_rounds"] = 1
	GameState.advance()
	_check(GameState.plan_fluency(CLUB, "contest") == 0.5, "An unplayed plan fades a whole step and keeps its part")
	PreSeason.reload()
	# Next year: what is left of the part meets the next pre-season's weeks.
	GameState.set_club_plan("attacking")
	GameState.plan_known[CLUB]["contest"] = 1.5
	_year_on()
	_check(GameState.plan_fluency(CLUB, "contest") == 0.5, "Over the off-season the plan slips a step and the part stays")
	GameState.preseason_add_drill(1)
	_check(GameState.plan_fluency_after_drills(GameState.card_drill_plan()) >= 0.5, "A card's one week now counts")
	_to_week()
	GameState.set_preseason_action("drill")
	GameState.set_preseason_drills(["contest"])
	_check(GameState.plan_fluency_after_drills("contest") == 1.0, "One more week finishes the step last year's began")
	GameState.preseason_advance()
	_press_on()
	_check(GameState.plan_level(CLUB, "contest") == 1 and GameState.plan_fluency(CLUB, "contest") == 1.0, "...and the level moves")
	# Rival clubs by the same rule.
	var ai := str(GameState.season.clubs[0]) if str(GameState.season.clubs[0]) != CLUB else str(GameState.season.clubs[1])
	var row: Dictionary = (GameState.preseason["clubs"] as Dictionary)[ai]
	row["acts"] = [{"a": "run"}, {"a": "drill", "d": ["contest"]}, {"a": "bond", "card": "x"}]
	var before: float = float(GameState.plan_known[ai]["contest"])
	GameState._finish_drills()
	_check(GameState.plan_fluency(ai, "contest") == PreSeason.drilled_fluency(before, 1.0) and GameState.plan_fluency(ai, "contest") != before or before >= 2.0,
			"A rival club's drilling week counts by the same rule (%.2f to %.2f)" % [before, GameState.plan_fluency(ai, "contest")])


func _test_part_save() -> void:
	PreSeason.reload()
	_career()
	GameState.plan_known[CLUB]["contest"] = 1.37
	GameState.plan_known[CLUB]["defensive"] = PreSeason.drilled_fluency(0.0, 2.0 * 0.123)
	var f1: float = GameState.plan_fluency(CLUB, "defensive")
	GameState.save_career()
	_check(GameState.load_career(), "A career with a part step saves and loads")
	_check(GameState.plan_fluency(CLUB, "contest") == 1.37 and GameState.plan_fluency(CLUB, "defensive") == f1,
			"...and the part comes back the very same number (%.17f, %.17f)" % [GameState.plan_fluency(CLUB, "contest"), GameState.plan_fluency(CLUB, "defensive")])
	# A save from before part steps holds whole levels.
	var state := CareerSave.read(GameState.save_path)
	state["plan_known"] = {CLUB: {"balanced": 2, "attacking": 2, "defensive": 0, "contest": 1, "controlled": 1}}
	state["plan_idle"] = {CLUB: {"contest": 3}}
	CareerSave.write(state, GameState._save_meta(), GameState.save_path)
	_check(GameState.load_career(), "An old save with whole levels loads")
	_check(GameState.plan_fluency(CLUB, "contest") == 1.0 and GameState.plan_level(CLUB, "defensive") == 0
			and GameState.plan_known_line("contest") == "Plan fluency: medium" and int(GameState.plan_idle[CLUB]["contest"]) == 3,
			"...its levels are what they were, in the same words")
	_to_week()
	GameState.set_preseason_action("drill")
	GameState.set_preseason_drills(["contest"])
	GameState.preseason_advance()
	GameState._finish_preseason()
	_check(GameState.plan_fluency(CLUB, "contest") == 1.5, "...and its next drilling week carries like any other")
	var bad := CareerSave.read(GameState.save_path)
	bad["plan_known"] = {CLUB: {"contest": 7.5, "attacking": -0.5}}
	CareerSave.write(bad, GameState._save_meta(), GameState.save_path)
	GameState.load_career()
	_check(GameState.plan_fluency(CLUB, "contest") == 2.0 and GameState.plan_fluency(CLUB, "attacking") == 0.0,
			"A damaged part step is clamped")


func _test_part_screen() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.size = Vector2i(390, 844)
	PreSeason.reload()
	_career(false)
	GameState.set_club_plan("attacking")
	GameState.open_preseason()
	GameState.set_setting("seen_weekly_loop_intro", true)
	GameState.plan_known[CLUB]["defensive"] = 0.5
	_to_week()
	var scene: Control = await _open(tree)
	var pick := scene.find_child("ActionTap_drill", true, false) as Control
	await _into_view(tree, pick)
	_check(await _tap(pick, "Game plan drilling"), "A finger sets the week to Game plan drilling")
	await _frames(tree, 4)
	var contest := scene.find_child("Drill_contest", true, false) as Button
	_check(contest.text == "Win Contest\nmedium", "Before any drilling a plan says where it stands: " + contest.text.replace("\n", " / "))
	_check((scene.find_child("Drill_defensive", true, false) as Button).text == "High Press\n50% to medium",
			"...and one part way says how far along")
	var h0: float = contest.size.y
	await _into_view(tree, contest)
	_check(await _tap(contest, "Win Contest to drill"), "A finger sets the week on Win Contest")
	await _frames(tree, 4)
	_check(GameState.preseason_drills() == ["contest"], "...one plan on one week")
	contest = scene.find_child("Drill_contest", true, false) as Button
	_check(contest.text == "Win Contest\nmedium\nRd 1: 50% to high", "The button says how far along the week leaves it: " + contest.text.replace("\n", " / "))
	_check(contest.size.y == h0, "...on a button that keeps its height (%.0f, %.0f)" % [h0, contest.size.y])
	# Every line fits a button, at its own font, and three lines fit its height.
	var font: Font = contest.get_theme_font("font")
	var fsize: int = contest.get_theme_font_size("font_size")
	var room: float = contest.size.x - contest.get_theme_stylebox("normal").get_margin(SIDE_LEFT) - contest.get_theme_stylebox("normal").get_margin(SIDE_RIGHT)
	# The longest third line there can be, in the chosen button's bold font, less the
	# room a desktop window's scrollbar takes (a capture cut a line this test passed).
	var widest := 0.0
	for line in ["Rd 1: " + PreSeason.fluency_short(0.5)] + Array(contest.text.split("\n")):
		widest = maxf(widest, UiKit.BOLD.get_string_size(str(line), HORIZONTAL_ALIGNMENT_LEFT, -1, fsize).x)
	_check(widest <= room - 16.0, "No line is cut short (widest %.0f of %.0f)" % [widest, room - 16.0])
	_check(font.get_height(fsize) * 3.0 <= contest.size.y, "...and three lines fit its height (%.0f of %.0f)" % [font.get_height(fsize) * 3.0, contest.size.y])
	_check(_fits(scene, 390.0), "...and nothing runs off a phone's width")
	# The week trained, then straight to the end of week 8, where the drills are credited.
	GameState.preseason_advance()
	GameState._finish_preseason()
	_check(not GameState.preseason_active(), "(setup) the pre-season is done")
	var tiles := PlanTiles.grid(2, [], [])
	# The two-column grid at the narrowest phone's page width (320 less its gutters).
	tiles.custom_minimum_size = Vector2(288, 0)
	tree.root.add_child(tiles)
	await _frames(tree, 2)
	var known := tiles.find_child("ClubPlan_contest", true, false).find_child("Known", true, false) as Label
	_check(known.text == "Plan fluency: 50% to high", "After the pre-season the plan tile carries it: " + known.text)
	_check(known.get_theme_font("font").get_string_size(known.text, HORIZONTAL_ALIGNMENT_LEFT, -1, known.get_theme_font_size("font_size")).x <= known.size.x + 0.5,
			"...in full on the tile (%.0f of %.0f)" % [known.get_theme_font("font").get_string_size(known.text, HORIZONTAL_ALIGNMENT_LEFT, -1, known.get_theme_font_size("font_size")).x, known.size.x])
	tiles.queue_free()



## The space between one tab's name and the next, left to right (each name
## is centred on its tab).
func _tab_gaps(row: Control) -> Array:
	var out := []
	if row == null:
		return out
	var prev_right := NAN
	for t in row.get_children():
		var b := t as Button
		var w := b.get_theme_font("font").get_string_size(b.text, HORIZONTAL_ALIGNMENT_LEFT, -1,
				b.get_theme_font_size("font_size")).x
		var left := b.position.x + (b.size.x - w) / 2.0
		if not is_nan(prev_right):
			out.append(snappedf(left - prev_right, 0.1))
		prev_right = left + w
	return out


## Scroll the page until `c` is on screen, as a thumb would before tapping it.
func _into_view(tree: SceneTree, c: Control) -> void:
	var n: Node = c
	while n != null and not (n is ScrollContainer):
		n = n.get_parent()
	if n != null and c != null:
		(n as ScrollContainer).ensure_control_visible(c)
		await _frames(tree, 3)


func _frames(tree: SceneTree, n: int) -> void:
	for i in range(n):
		await tree.process_frame


func _tap(b: Control, what: String) -> bool:
	var why: String = await Tap.tap(b)
	if why != "":
		_check(false, "A finger's tap reaches %s (%s)" % [what, why])
		if is_instance_valid(b) and b is BaseButton:
			(b as BaseButton).emit_signal("pressed")
	return why == ""


func _open(tree: SceneTree) -> Control:
	Router.stack = ["main"]
	Router.go("hub")
	await _frames(tree, 8)
	return tree.current_scene as Control


func _label(scene: Node, node_name: String) -> String:
	var l := scene.find_child(node_name, true, false) as Label if scene != null else null
	return l.text if l != null else ""


func _fits(scene: Control, width: float) -> bool:
	var ok := true
	# Labels and buttons both: a row of buttons too wide for the phone pushes
	# the whole page past the screen's edge.
	for n in scene.find_children("*", "Control", true, false):
		if not (n is Label or n is Button):
			continue
		var c := n as Control
		var text := str(c.get("text"))
		if not c.is_visible_in_tree() or text == "":
			continue
		var r := c.get_global_rect()
		if r.position.x < -0.5 or r.end.x > width + 0.5:
			ok = false
			push_error("Off the screen: %s (%s)" % [text, str(r)])
	return ok
