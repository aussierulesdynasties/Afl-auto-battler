extends RefCounted
## The pre-season (PreSeason.gd, rule 69a): the player meetings, the season
## fitness plan and the running it books, one action a week (Running, Game plan
## drilling, Team bonding), the rivals by the same rules, its own dice, saves
## old and new, and the screens by real taps. Every season here is seeded.

const Tap := preload("res://tests/tap.gd")
const BalanceGate := preload("res://tests/balance_gate.gd")
const Press := preload("res://tests/preseason_press.gd")

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 4127
const CLUB := "FRE"


func run() -> void:
	GameState.replay_seed = SUITE_SEED
	_t("_test_rules")
	_t("_test_flow")
	_t("_test_no_extra_running")
	_t("_test_flag_run")
	_t("_test_rivals")
	_t("_test_determinism")
	_t("_test_own_dice")
	_t("_test_sim_to_round_one")
	_t("_test_old_saves")
	await _t("_test_screens")
	await _t("_test_meeting_focus")
	await _t("_test_meeting_group")
	await _t("_test_story_stop")
	await _t("_test_draft_card")
	PreSeason.reload()
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	print(Ran.line("Preseason", self))


func _check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


## A seeded career at `club`; with `open`, its first season starts with a
## pre-season, as a new career does in the game.
func _career(open := true, club := CLUB) -> void:
	GameState.reset()
	GameState.career_seed = SUITE_SEED
	GameState.replay_seed = SUITE_SEED
	GameState.start_season(club, GameDB.club_list(club))
	if open:
		GameState.open_preseason()


## Press on through every stop to Round 1 (Press: the meetings as they stand,
## the plan the club runs, the first action open each week).
func _press_on() -> bool:
	var guard := 0
	while GameState.preseason_active() and guard < 24:
		guard += 1
		Press.advance()
	return not GameState.preseason_active()


## Past the meetings, on `plan`.
func _planned(plan: String) -> void:
	GameState.preseason_meetings_done()
	GameState.set_preseason_plan(plan)


## Take one week as `a` (and, for a drilling week, `drill`), past any stop it
## ends on that is not the next week.
func _week(a: String, drill := "") -> bool:
	if not GameState.set_preseason_action(a):
		return false
	if drill != "":
		GameState.set_preseason_drills([drill])
	var w := GameState.preseason_week()
	GameState.preseason_advance()
	return GameState.preseason_week() == w + 1


## Everything a pre-season leaves behind: results, every listed player's
## rating, XP, injury and morale, each club's weeks, its plan and how well it
## knows each plan, and its culture.
func _sig() -> String:
	var parts := []
	for res in GameState.season_log:
		parts.append("%s-%s:%d-%d" % [str(res["home"]), str(res["away"]),
				int(res["score"][0]), int(res["score"][1])])
	for code in GameState.season.clubs:
		var rows := []
		for p in GameState.season.lists[code]:
			rows.append("%s/%d/%d/%d/%s" % [str(p["id"]), int(p["overall"]), int(p.get("xp", 0)),
					int(p.get("injury_weeks", 0)), str(p.get("morale", ""))])
		rows.sort()
		parts.append("%s[%s|%s|%s]%s" % [str(code), GameState.fitness_plan(str(code)),
				_norm(GameState.preseason_entry(str(code))), _norm(GameState.plan_known.get(code, {})), ",".join(rows)])
	parts.append(_norm(GameState.relations))
	return str(hash("\n".join(parts)))


## A value as text that a save and load leave alone: keys sorted, every number
## to four places (a save can bring a whole number back as 1.0).
func _norm(v: Variant) -> String:
	if v is Dictionary:
		var keys: Array = (v as Dictionary).keys()
		keys.sort_custom(func(a, b): return str(a) < str(b))
		var out := []
		for k in keys:
			out.append("%s:%s" % [str(k), _norm(v[k])])
		return "{" + ",".join(out) + "}"
	if v is Array:
		var items := []
		for x in v:
			items.append(_norm(x))
		return "[" + ",".join(items) + "]"
	if v is int or v is float:
		return "%.4f" % float(v)
	return str(v)


func _play(rounds: int) -> void:
	for i in range(rounds):
		GameState.advance()


func _mean_rating() -> float:
	var total := 0.0
	var n := 0
	for code in GameState.season.clubs:
		for p in GameState.season.lists[code]:
			total += float(p["overall"])
			n += 1
	return total / float(maxi(1, n))


func _acts(code := CLUB) -> Array:
	return GameState.preseason_entry(code).get("acts", [])


# ---------------------------------------------------------------------------
func _test_rules() -> void:
	PreSeason.reload()
	_check(PreSeason.weeks() == 8 and PreSeason.train_weeks() == 7,
			"Eight weeks: seven take an action, and week 8 is the papers' quiet week")
	_check(PreSeason.run_needed("peak") == 5 and PreSeason.run_needed("fast") == 4
			and PreSeason.run_needed("steady") == 3 and PreSeason.run_needed("develop") == 2,
			"Each plan books its own running: Peak 5, Fast 4, Steady 3, Develop 2")
	_check(PreSeason.run_needed("peak", 1) == 6 and PreSeason.run_needed("peak", 9) == 7,
			"One more running week on top for the flag, never more than the seven weeks")
	_check(PreSeason.actions_open(1, 5) == ["run", "drill", "bond"],
			"Week 1 with five weeks of running owed: all three actions are open")
	_check(PreSeason.actions_open(3, 5) == ["run"] and PreSeason.actions_open(7, 1) == ["run"],
			"Once the weeks left are only enough for the running owed, Running is the one action")
	_check(PreSeason.actions_open(5, 0) == ["drill", "bond"],
			"With the booked running done, Running is not offered: no extra running")
	_check(PreSeason.actions_open(8, 0).is_empty() and PreSeason.actions_open(0, 3).is_empty(),
			"Week 8 and before week 1 take no action")
	_check(PreSeason.ai_action(1, 3, "attacking", 0.0) == "run"
			and PreSeason.ai_action(5, 0, "attacking", 0.0) == "drill"
			and PreSeason.ai_action(5, 0, "attacking", float(PreSeason.WELL)) == "bond"
			and PreSeason.ai_action(5, 0, "balanced", 0.0) == "bond",
			"A rival runs while it owes running, then drills its plan until the side knows it well, then bonds")
	_check(PreSeason.clean_week({"a": "yoga"}).is_empty()
			and PreSeason.clean_week({"a": "drill"}, ["attacking"]) == {"a": "drill", "d": ["attacking"]}
			and PreSeason.clean_week({"a": "bond", "card": "bond_beach_day"}) == {"a": "bond", "card": "bond_beach_day"},
			"A week that is not on offer is refused, and a drilling week with no plan drills the side's own")
	# The time trial.
	var list := []
	for i in range(12):
		list.append({"id": "t%02d" % i, "attr": {"durability": 40 + i * 4}})
	list[11]["injury_weeks"] = 3
	var a := PreSeason.trial(list, 7, 2027, CLUB)
	var b := PreSeason.trial(list, 7, 2027, CLUB)
	var both := false
	for id in a["best"]:
		both = both or (a["worst"] as Array).has(id)
	_check(a == b and (a["best"] as Array).size() == 5 and (a["worst"] as Array).size() == 3 and not both,
			"The time trial names the first five and the last three, nobody twice, the same on a replay")
	_check(not (a["best"] as Array).has("t11") and not (a["worst"] as Array).has("t11"),
			"An injured player sits the time trial out")
	_check(PreSeason.trial(list, 8, 2027, CLUB) != a or PreSeason.trial(list, 7, 2028, CLUB) != a,
			"Another career or another year runs a different time trial")


## The coach's pre-season, stop by stop: meetings, plan, seven weeks of one
## action each, the time trial, the practice match, the papers, Round 1.
func _test_flow() -> void:
	PreSeason.reload()
	_career(false)
	_check(not GameState.preseason_active() and GameState.preseason_stop() == "",
			"A career started without a pre-season has none running")
	_career()
	_check(GameState.preseason_active() and GameState.preseason_stop() == "meetings" and GameState.preseason_week() == 0,
			"A new career's pre-season opens on the player meetings")
	var booked := true
	for code in GameState.season.clubs:
		if str(code) != CLUB:
			booked = booked and int(GameState.preseason_entry(str(code))["need"]) == PreSeason.run_needed(GameState.fitness_plan(str(code)))
	_check(booked, "Every rival books the running its own fitness plan needs")
	_check(not GameState.set_preseason_plan("peak") and not GameState.set_preseason_action("run")
			and GameState.preseason_advance() == "meetings" and GameState.preseason_week() == 0,
			"The plan and the week wait until the meetings are done, and pressing on does not skip them")
	# The meetings: a stat focus, locked for the season.
	var p: Dictionary = GameState.my_list[0]
	var opts := GameState.focus_options(p)
	_check(not opts.is_empty() and GameState.set_stat_focus(str(p["id"]), str(opts[0]))
			and GameState.focus_locked(p) and not GameState.set_stat_focus(str(p["id"]), str(opts[opts.size() - 1])),
			"At the meetings a player's stat focus is set for the season, and then it is locked")
	_check(GameState.preseason_meetings_done() and GameState.preseason_stop() == "plan",
			"Meetings done: on to the season fitness plan")
	_check(GameState.preseason_plan_runs("peak") == 5 and GameState.preseason_plan_runs("develop") == 2,
			"The plan screen's numbers are each plan's own running weeks")
	_check(not GameState.set_preseason_plan("yoga") and GameState.set_preseason_plan("peak")
			and GameState.fitness_plan(CLUB) == "peak" and int(GameState.preseason_entry()["need"]) == 5
			and GameState.preseason_stop() == "week" and not GameState.can_revise_fitness(),
			"Peak for September books five weeks of running, is the season's fitness plan, and is not revised before Round 1")
	_check(GameState.preseason_actions() == ["run", "drill", "bond"] and GameState.preseason_next().is_empty()
			and GameState.preseason_advance() == "week" and GameState.preseason_week() == 0,
			"Week 1 offers all three, and does not train until one is picked")
	# Week 1: drill a plan the side does not play.
	var plan := "defensive" if GameState.club_plan != "defensive" else "attacking"
	var level0 := GameState.plan_level(CLUB, plan)
	_check(GameState.set_preseason_action("drill") and GameState.preseason_drills() == [GameState.card_drill_plan()]
			and GameState.set_preseason_drills([plan]) and GameState.preseason_drills() == [plan],
			"A drilling week drills the plan the side plays until another is picked")
	GameState.preseason_advance()
	_check(GameState.preseason_week() == 1 and _acts() == [{"a": "drill", "d": [plan]}],
			"Week 1 is taken as picked")
	_check(_week("drill", plan) and GameState.preseason_week() == 2, "Week 2 drills it again")
	# Weeks 3 to 7: five weeks left, five of running owed.
	_check(GameState.preseason_actions() == ["run"] and not GameState.set_preseason_action("drill")
			and not GameState.set_preseason_action("bond"),
			"With five weeks left and five of running owed, Running is the one action open")
	_check(_week("run") and GameState.preseason_stop() == "trial" and GameState.preseason_week() == 3
			and (GameState.preseason_trial().get("best", []) as Array).size() == 5,
			"After week 3 the time trial waits, five names from the front")
	Press.advance()
	for i in range(4):
		_week("run")
	_check(GameState.preseason_stop() == "practice" and GameState.preseason_week() == 7
			and int(GameState.preseason_entry()["run"]) == 5 and GameState.preseason_run_left() == 0,
			"Week 7 ends at the practice match with the five running weeks done")
	_check(_press_on() and GameState.preseason_week() == 8 and GameState.season.round_index == 0,
			"Pressing on passes the practice match and the papers to Round 1")
	_check(GameState.plan_level(CLUB, plan) == mini(PreSeason.WELL, level0 + 1),
			"Two weeks of drilling lift the plan a step (%d to %d)" % [level0, GameState.plan_level(CLUB, plan)])
	_check(GameState.news.size() > 0 and str(GameState.news[0]["text"]).begins_with("Pre-season is done"),
			"The news says the pre-season is done")


## A plan that books two weeks: once they are run, Running is not offered.
func _test_no_extra_running() -> void:
	PreSeason.reload()
	_career()
	_planned("develop")
	_check(int(GameState.preseason_entry()["need"]) == 2, "Develop books two weeks of running")
	_week("run")
	_week("run")
	Press.answer()
	_check(GameState.preseason_run_left() == 0 and not GameState.preseason_actions().has("run")
			and not GameState.set_preseason_action("run"),
			"With its two weeks run, Running is closed: no extra running")
	var xp0 := 0
	for q in GameState.my_list:
		xp0 += int(q.get("xp", 0))
	GameState.preseason["trial_seen"] = true
	_week("drill")
	var xp1 := 0
	for q in GameState.my_list:
		xp1 += int(q.get("xp", 0))
	_check(xp1 == xp0, "A summer week pays no skill development")


## The flag celebration: one more running week than the plan needs.
func _test_flag_run() -> void:
	PreSeason.reload()
	_career(false)
	GameState.preseason_run_debt = -1.0
	GameState.open_preseason()
	_planned("steady")
	_check(int(GameState.preseason.get("extra_run", 0)) == 1 and int(GameState.preseason_entry()["need"]) == 4
			and GameState.preseason_plan_runs("peak") == 6,
			"After the flag the plan books one more running week (Steady 4, Peak 6)")


## Every rival by the same rules: its running, then drill, then bond; a rival's
## bonding week rolls a card, never the cultural day without an Indigenous player.
func _test_rivals() -> void:
	PreSeason.reload()
	_career(false)
	var off_mean := _mean_rating()
	_career()
	GameState.preseason_sim_to_round1()
	var on_mean := _mean_rating()
	var ordered := true
	var full := true
	var bonded := 0
	var cards_ok := true
	for code in GameState.season.clubs:
		var c := str(code)
		var e := GameState.preseason_entry(c)
		var acts: Array = e["acts"]
		full = full and acts.size() == PreSeason.train_weeks() and int(e["run"]) == int(e["need"])
		var seen_bond := false
		for i in range(acts.size()):
			var a := str(acts[i]["a"])
			if c != CLUB:
				ordered = ordered and (a == "run") == (i < int(e["need"])) and not (seen_bond and a == "drill")
			seen_bond = seen_bond or a == "bond"
			if a == "bond" and c != CLUB:
				var id := str(acts[i].get("card", ""))
				bonded += 1 if id != "" else 0
				var t := StoryDeck.by_id(StoryDeck.all(), id) if id != "" else {}
				cards_ok = cards_ok and (id == "" or ((t.get("phase", []) as Array).has("bonding")
						and (id != "bond_cultural_day" or ClubStories.indigenous_players(GameState.season.lists[code]).size() > 0)))
	_check(full, "Every club takes seven weeks and runs exactly what its plan booked")
	_check(ordered, "Every rival runs first, then drills, then bonds, and never drills after bonding")
	_check(bonded > 0 and cards_ok,
			"Rivals' bonding weeks roll bonding cards (%d), the cultural day only where a club has an Indigenous player" % bonded)
	print("Pre-season parity (seed %d): league mean rating at Round 1 %.2f without, %.2f with" % [SUITE_SEED, off_mean, on_mean])
	_check(BalanceGate.held(absf(on_mean - off_mean) < 1.0, "preseason mean rating lift under a point"),
			"A pre-season moves the league's mean rating by under a point (%.2f to %.2f)" % [off_mean, on_mean])


## A scripted pre-season: the meetings, Fast, two weeks of drilling then the
## running, the rest bonding as open.
func _run_preseason(reload_at := -1) -> String:
	_career()
	_planned("fast")
	var guard := 0
	while GameState.preseason_active() and guard < 30:
		guard += 1
		match GameState.preseason_stop():
			"week":
				var open := GameState.preseason_actions()
				var w := GameState.preseason_week() + 1
				GameState.set_preseason_action("drill" if w <= 2 and open.has("drill") else str(open[0]))
			"trial":
				GameState.preseason["trial_seen"] = true
		var before := GameState.preseason_week()
		Press.advance()
		if GameState.preseason_week() != before and GameState.preseason_week() == reload_at:
			GameState.save_career()
			GameState.load_career()
			GameState.replay_seed = SUITE_SEED
	return _sig()


func _test_determinism() -> void:
	PreSeason.reload()
	var a := _run_preseason()
	var trial_a := GameState.preseason_trial()
	_play(3)
	var a_season := _sig()
	var b := _run_preseason()
	_check(a == b and GameState.preseason_trial() == trial_a,
			"The same seed and the same choices give the same pre-season")
	_play(3)
	_check(_sig() == a_season, "...and the same three rounds after it")
	for at in [2, 5]:
		var c := _run_preseason(at)
		_check(c == a and GameState.preseason_trial() == trial_a,
				"Saved and loaded after week %d, the pre-season finishes the same" % at)
	_career()
	_planned("develop")
	GameState.preseason_sim_to_round1()
	_check(_sig() != a, "Different choices give a different pre-season")
	# A stop is neither skipped nor repeated by a reload.
	_career()
	Press.to("trial")
	GameState.save_career()
	GameState.load_career()
	_check(GameState.preseason_stop() == "trial" and GameState.preseason_week() == 3
			and (GameState.preseason_trial().get("best", []) as Array).size() == 5,
			"Loaded at the time trial, the career is still at the time trial with the same names")
	_press_on()
	GameState.save_career()
	GameState.load_career()
	_check(not GameState.preseason_active() and GameState.preseason_stop() == "" and GameState.preseason_week() == 8,
			"Loaded after week 8, the pre-season is not run again")
	PreSeason.reload()


## The pre-season's draws are its own: with it on or off, the season's seed,
## fixture, first story card and next draft class are the same.
func _test_own_dice() -> void:
	PreSeason.reload()
	_career(false)
	var off := _dice()
	_career()
	GameState.preseason_sim_to_round1()
	var on := _dice()
	_check(on == off, "A pre-season moves no match, draft or story dice (season seed, fixture, card, class)")


func _test_sim_to_round_one() -> void:
	PreSeason.reload()
	_career()
	GameState.set_fitness_plan("fast")
	GameState.preseason_sim_to_round1()
	var acts := _acts()
	var runs_first := acts.size() == 7
	for i in range(acts.size()):
		runs_first = runs_first and (str(acts[i]["a"]) == "run") == (i < 4)
	_check(not GameState.preseason_active() and GameState.preseason_week() == 8
			and GameState.preseason_stop() == "" and GameState.season.round_index == 0
			and (GameState.preseason_trial().get("best", []) as Array).size() == 5,
			"Sim to Round 1 runs all eight weeks and stops for nothing")
	_check(runs_first and int(GameState.preseason_entry()["need"]) == 4,
			"...on the fitness plan the club runs (Fast, four weeks), its running first, as a rival takes it")
	var simmed := _sig()
	_play(1)
	var simmed_r1 := _sig()
	# A round played with the pre-season still waiting runs it hands-off first.
	_career()
	GameState.set_fitness_plan("fast")
	_play(1)
	_check(_sig() == simmed_r1 and not GameState.preseason_active() and simmed != simmed_r1,
			"A round played with the pre-season still waiting runs it hands-off first: nothing is skipped")
	# From week 2, the weeks already taken stand.
	_career()
	_planned("fast")
	_week("drill")
	_week("bond")
	Press.answer()
	if GameState.preseason_stop() == "story":
		Press.advance()
	GameState.preseason_sim_to_round1()
	_check(str(_acts()[0]["a"]) == "drill" and str(_acts()[1]["a"]) == "bond" and int(GameState.preseason_entry()["run"]) == 4,
			"Simmed from week 3, the weeks you took stand and the running is still done")


## Write the current career as a save from before pre-seasons: no `preseason` key.
func _save_as_old() -> void:
	GameState.save_career()
	var state := CareerSave.read(GameState.save_path)
	state.erase("preseason")
	CareerSave.write(state, GameState._save_meta(), GameState.save_path)


func _test_old_saves() -> void:
	PreSeason.reload()
	# Mid-season.
	_career(false)
	_play(2)
	_save_as_old()
	_play(2)
	var straight := _sig()
	_check(GameState.load_career(), "A save from before pre-seasons loads mid-season")
	GameState.replay_seed = SUITE_SEED
	_check(GameState.preseason.is_empty() and not GameState.preseason_active() and GameState.preseason_stop() == "",
			"...with no pre-season running")
	_play(2)
	_check(_sig() == straight, "...and plays on exactly as the career it was saved from")
	# A pre-season saved before the rework (three blocks of load and focus),
	# at the time trial: it carries on under the new rules.
	_career()
	Press.to("trial")
	GameState.save_career()
	var state := CareerSave.read(GameState.save_path)
	var clubs: Dictionary = state["preseason"]["clubs"]
	for code in clubs:
		clubs[code] = {"blocks": [["solid", "running"], ["heavy", "skills"], ["solid", "running"]], "run": 3.0, "xp": 0}
	state["preseason"].erase("met")
	state["preseason"].erase("planned")
	CareerSave.write(state, GameState._save_meta(), GameState.save_path)
	_check(GameState.load_career() and GameState.preseason_stop() == "trial" and GameState.preseason_week() == 3,
			"A pre-season saved before the rework loads at the stop it reached")
	var e := GameState.preseason_entry()
	_check(int(e.get("run", -1)) == 3 and (e.get("acts", []) as Array).size() == 3
			and int(e.get("need", 0)) == PreSeason.run_needed(GameState.fitness_plan(CLUB)),
			"...its running weeks so far counted, and its plan's running booked")
	_check(_press_on() and not GameState.preseason_active() and GameState.season.round_index == 0,
			"...and goes on to Round 1")
	# A new save keeps the pre-season.
	_career()
	_planned("peak")
	_week("drill")
	var snap: Dictionary = GameState.preseason.duplicate(true)
	GameState.save_career()
	GameState.load_career()
	_check(str(GameState.preseason_entry()) == str(snap["clubs"][CLUB]) and GameState.preseason_week() == 1
			and GameState.preseason_stop() == "week",
			"The pre-season survives save and load: the weeks taken, the running booked")


## The stops with a finger's taps: the meetings, the plan, the weeks, Android
## Back, Sim to Round 1, and a PC's width.
func _test_screens() -> void:
	PreSeason.reload()
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.size = Vector2i(390, 844)
	_career()
	GameState.set_setting("seen_weekly_loop_intro", true)
	GameState.set_setting("seen_training_intro", true)
	var scene: Control = await _open(tree)
	_check(scene != null and scene.name == "PreSeasonScene" and Router.current() == "preseason"
			and _label(scene, "PreSeasonHero") == "Player meetings",
			"With a pre-season running, the game opens on the player meetings")
	_check(_fits(scene, 390.0), "Nothing on the meetings runs off a phone's screen")
	_check(scene.find_child("PreSeasonTraining", true, false) == null,
			"The meetings have no Training button: they set the focus themselves")
	# Open a player's meeting and set his focus by taps.
	var p: Dictionary = {}
	for q in GameState.my_list:
		if p.is_empty() and GameState.focus_options(q).size() >= 2:
			p = q
	var pid := str(p["id"])
	var key := str(GameState.focus_options(p)[1])
	var row_tap := scene.find_child("MeetTap_" + pid, true, false) as Control
	await _into_view(tree, row_tap)
	_check(await _tap(row_tap, "a player's meeting"), "A finger's tap opens a player's meeting")
	await _frames(tree, 4)
	var pick := scene.find_child("MeetFocus_" + key, true, false) as Control
	await _into_view(tree, pick)
	_check(await _tap(pick, "a stat focus"), "A finger's tap picks his stat focus")
	await _frames(tree, 4)
	_check(GameState.stat_focus(p) != key or not GameState.focus_locked(p),
			"The pick is a draft until the meetings are done")
	_check(scene.find_child("MeetSheet", true, false) != null,
			"His meeting opens in a panel over the page")
	_check(await _tap(scene.find_child("MeetClose", true, false), "Close"), "A finger's tap closes his meeting")
	await _frames(tree, 4)
	var said := _label(scene, "MeetSaid_" + pid)
	_check(scene.find_child("MeetSheet", true, false) == null and scene.find_child("PreSeasonMeetings", true, false) != null
			and said == GameState.train_stat_label(key).to_lower(),
			"Closing it leaves the four lines, his row showing the focus picked (%s)" % said)
	_check(await _tap(scene.find_child("PreSeasonGo", true, false), "Meetings done"), "A finger's tap finishes the meetings")
	await _frames(tree, 6)
	scene = tree.current_scene as Control
	_check(GameState.stat_focus(p) == key and GameState.focus_locked(p) and GameState.preseason_stop() == "plan",
			"Meetings done locks the focus picked and moves on to the plan")
	# The plan.
	_check(_label(scene, "PreSeasonHero") == "The season fitness plan"
			and _label(scene, "PlanRuns_peak") == "5 weeks of running. 2 weeks free for drilling or bonding."
			and _label(scene, "PlanRuns_develop") == "2 weeks of running. 5 weeks free for drilling or bonding."
			and _fits(scene, 390.0),
			"Each plan says the running it books and the weeks it leaves free (%s)" % _label(scene, "PlanRuns_peak"))
	var dev := scene.find_child("Plan_develop", true, false) as Control
	await _into_view(tree, dev)
	_check(await _tap(dev, "Develop"), "A finger's tap picks Develop")
	await _frames(tree, 4)
	_check(await _tap(scene.find_child("PreSeasonGo", true, false), "Start training"), "A finger's tap starts training")
	await _frames(tree, 6)
	scene = tree.current_scene as Control
	_check(GameState.fitness_plan(CLUB) == "develop" and int(GameState.preseason_entry()["need"]) == 2
			and GameState.preseason_stop() == "week",
			"Develop is the season's plan, booking two weeks of running")
	# Week 1.
	var go := scene.find_child("PreSeasonGo", true, false) as Button
	_check(_label(scene, "PreSeasonHero") == "Week 1 of 8" and go != null and go.disabled
			and _label(scene, "ActionGain_run") != "" and _label(scene, "ActionCost_bond") != ""
			and _fits(scene, 390.0),
			"Week 1 lists the three actions with a Gain and a Cost, and waits for one")
	_check(await _tap(scene.find_child("ActionTap_drill", true, false), "Game plan drilling"),
			"A finger's tap picks Game plan drilling")
	await _frames(tree, 4)
	scene = tree.current_scene as Control
	_check(scene.find_child("DrillPicker", true, false) != null and not (scene.find_child("PreSeasonGo", true, false) as Button).disabled
			and str(GameState.preseason_next().get("a", "")) == "drill",
			"Drilling shows the plans to drill, and the week can train")
	await _tap(scene.find_child("PreSeasonGo", true, false), "Train week 1")
	await _frames(tree, 6)
	scene = tree.current_scene as Control
	_check(GameState.preseason_week() == 1 and str(_acts()[0]["a"]) == "drill" and _label(scene, "PreSeasonHero") == "Week 2 of 8",
			"A finger's tap trains week 1 as picked")
	for i in range(2):
		await _tap(scene.find_child("ActionTap_run", true, false), "Running")
		await _frames(tree, 4)
		await _tap(scene.find_child("PreSeasonGo", true, false), "Train the week")
		await _frames(tree, 6)
		scene = tree.current_scene as Control
	_check(GameState.preseason_stop() == "trial" and scene.find_child("TrialStopwatch", true, false) != null
			and scene.find_child("PreSeasonSummer", true, false) != null,
			"After week 3 the time trial shows, with the summer so far")
	await _tap(scene.find_child("PreSeasonGo", true, false), "Back to training")
	await _frames(tree, 6)
	scene = tree.current_scene as Control
	_check(GameState.preseason_stop() == "week" and _label(scene, "ActionClosed_run") == "Our booked running is done. No extra running."
			and scene.find_child("ActionTap_run", true, false) == null,
			"With the two weeks run, Running says why it is closed and cannot be tapped")
	# Android Back leaves for the main menu with the career saved.
	Router.handle_back()
	await _frames(tree, 6)
	_check(Router.current() != "preseason" and GameState.preseason_active(),
			"Back leaves the pre-season, which is still waiting")
	# A PC's width: nothing runs off.
	tree.root.size = Vector2i(1600, 900)
	scene = await _open(tree)
	_check(scene != null and scene.name == "PreSeasonScene" and _fits(scene, 1600.0),
			"On a PC's width the week fits")
	tree.root.size = Vector2i(390, 844)
	Router.stack = []


## The stat focus picker (director, 2026-11-24): the stats a midfielder is
## rated on are in bold TEXT, the rest regular MUTED; on a 1600x900 window the
## choices sit in the left half and his profile on the right; a phone keeps
## one column.
func _test_meeting_focus() -> void:
	PreSeason.reload()
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.size = Vector2i(1600, 900)
	_career()
	GameState.set_setting("seen_weekly_loop_intro", true)
	GameState.set_setting("seen_training_intro", true)
	var p: Dictionary = {}
	for q in GameState.my_list:
		if p.is_empty() and str(q.get("role", "")) == "MID" and GameState.project_job(q) == "" 				and GameState.focus_options(q).size() >= 6:
			p = q
	_check(not p.is_empty(), "The club has a midfielder with a stat focus to pick")
	if p.is_empty():
		return
	var pid := str(p["id"])
	_check(PlayerProfile.rated_on(p) == ["contested", "creating"],
			"A midfielder is rated most on contested ball and creating (%s)" % str(PlayerProfile.rated_on(p)))
	var scene: Control = await _open(tree)
	var row_tap := scene.find_child("MeetTap_" + pid, true, false) as Control
	await _into_view(tree, row_tap)
	_check(await _tap(row_tap, "a midfielder's meeting"), "A finger's tap opens a midfielder's meeting on a PC")
	await _frames(tree, 6)
	var bold_ok := true
	var seen := 0
	for key in GameState.focus_options(p):
		var b := scene.find_child("MeetFocus_" + str(key), true, false) as Button
		if b == null:
			bold_ok = false
			continue
		seen += 1
		var strong := PlayerProfile.rated_on(p).has(str(key))
		var font := b.get_theme_font("font")
		var ink := b.get_theme_color("font_color")
		var chosen := str(key) == GameState.stat_focus(p)
		if strong and (font != UiKit.BOLD or ink != UiKit.TEXT):
			bold_ok = false
		if not strong and (font != UiKit.FONT or (not chosen and ink != UiKit.MUTED)):
			bold_ok = false
	_check(bold_ok and seen >= 6 and _label(scene, "MeetFocusRated").contains("midfielder"),
			"The stats his position is rated on are bold TEXT, the rest regular MUTED, with the key line (%s)"
			% _label(scene, "MeetFocusRated"))
	var choices := scene.find_child("MeetChoices", true, false) as Control
	var profile := scene.find_child("MeetProfile", true, false) as Control
	var grid := scene.find_child("MeetFocus", true, false) as Control
	var sheet := scene.find_child("MeetSheet", true, false) as Control
	var mid := 800.0
	if sheet != null and sheet.find_child("MeetChoices", true, false) != null:
		var shell := (choices.get_parent() as Control)
		mid = shell.get_global_rect().get_center().x
	_check(choices != null and profile != null and grid != null and sheet != null
			and grid.get_global_rect().end.x <= mid + 0.5
			and profile.get_global_rect().position.x >= mid - 0.5
			and profile.get_global_rect().end.x <= 1600.0 + 0.5
			and profile.find_child("ProfileName", true, false) != null
			and profile.find_child("ProfileAttributes", true, false) != null,
			"On a 1600x900 window his meeting opens over the page, the stat buttons on its left half and his profile on the right (%s / %s)"
			% [str(grid.get_global_rect()) if grid != null else "-", str(profile.get_global_rect()) if profile != null else "-"])
	_check(_fits(scene, 1600.0), "Nothing on the PC meeting runs off the window")
	_check(await _tap(scene.find_child("MeetClose", true, false), "Close"), "A finger's tap closes his meeting on a PC")
	await _frames(tree, 4)
	_check(scene.find_child("MeetSheet", true, false) == null and _one_page(scene)
			and scene.find_child("MeetLine_RUCK", true, false) != null
			and (scene.find_child("MeetLine_MID", true, false) as Control).get_global_rect().position.y
				== (scene.find_child("MeetLine_RUCK", true, false) as Control).get_global_rect().position.y,
			"On a PC the four lines sit side by side on one page")
	await _tap(scene.find_child("MeetTap_" + pid, true, false), "a midfielder's meeting")
	await _frames(tree, 4)
	# A phone: one column, no profile beside, still bold.
	tree.root.size = Vector2i(390, 844)
	await _frames(tree, 6)
	scene = tree.current_scene as Control
	var phone_b := scene.find_child("MeetFocus_contested", true, false) as Button
	_check(scene.find_child("MeetProfile", true, false) == null and phone_b != null
			and phone_b.get_theme_font("font") == UiKit.BOLD and _fits(scene, 390.0),
			"On a phone the meeting stays one column, the rated stats still bold, nothing cut")
	Router.stack = []


## Ticking players and giving them one stat focus together, by a finger's taps
## on a phone (director, 2026-11-25: "multi click players and set stat focus
## for multiple at once"; tick boxes, and a player who can't train the stat is
## named and keeps his own).
func _test_meeting_group() -> void:
	PreSeason.reload()
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.size = Vector2i(390, 844)
	_career()
	GameState.set_setting("seen_weekly_loop_intro", true)
	GameState.set_setting("seen_training_intro", true)
	# A line that all trains one stat, and a player in another line who doesn't.
	var mids := []
	var key := ""
	var g := ""
	var d: Dictionary = {}
	for line in PreSeason.GROUPS:
		if key != "":
			break
		var members := []
		for q in GameState.my_list:
			if PreSeason.group_of(q) == line:
				members.append(q)
		for row in GameState.TRAIN_STATS:
			var k := str(row[0])
			var all_in := not members.is_empty()
			for m in members:
				if GameState.project_job(m) == "" and not GameState.focus_options(m).has(k):
					all_in = false
			if not all_in:
				continue
			for q in GameState.my_list:
				if d.is_empty() and PreSeason.group_of(q) != line and GameState.project_job(q) == "" 						and not GameState.focus_options(q).has(k):
					d = q
			if not d.is_empty():
				key = k
				g = str(line)
				mids = members
				break
	_check(key != "", "A stat one line trains and a player elsewhere doesn't (%s, %s)" % [g, key])
	if key == "":
		return
	var scene: Control = await _open(tree)
	var all_mid := scene.find_child("MeetAll_" + g, true, false) as Control
	await _into_view(tree, all_mid)
	_check(await _tap(all_mid, "All"), "A finger's tap ticks a whole line")
	await _frames(tree, 4)
	var tick := scene.find_child("MeetTick_" + str(d["id"]), true, false) as Control
	await _into_view(tree, tick)
	_check(await _tap(tick, "a defender's tick"), "A finger's tap ticks a player from another line")
	await _frames(tree, 4)
	var go := scene.find_child("PreSeasonGo", true, false) as Button
	_check(go != null and go.text == "Set stat focus for %d" % (mids.size() + 1)
			and scene.find_child("MeetClearTicks", true, false) != null,
			"The way on sets the focus for the ticked players (%s)" % (go.text if go != null else "-"))
	_check(await _tap(go, "Set stat focus"), "A finger's tap opens the stat focus for the ticked players")
	await _frames(tree, 4)
	var pick := scene.find_child("MeetGroupFocus_" + key, true, false) as Control
	_check(pick != null and await _tap(pick, "a stat focus for all"), "A finger's tap picks one stat for them all")
	await _frames(tree, 4)
	var skip := _label(scene, "MeetGroupSkip")
	var set_it := scene.find_child("MeetGroupSet", true, false) as Button
	_check(skip.contains(GameDB.card_surname(d)) and set_it != null and not set_it.disabled,
			"The player who can't train it is named before it is set (%s)" % skip)
	_check(await _tap(set_it, "Set"), "A finger's tap sets it")
	await _frames(tree, 6)
	var ok := scene.find_child("MeetGroupSheet", true, false) == null
	for m in mids:
		if GameState.project_job(m) == "":
			ok = ok and _label(scene, "MeetSaid_" + str(m["id"])) == GameState.train_stat_label(key).to_lower()
	_check(ok and _label(scene, "MeetSaid_" + str(d["id"])) != GameState.train_stat_label(key).to_lower(),
			"Every player in the line shows the focus; the other keeps his own")
	go = scene.find_child("PreSeasonGo", true, false) as Button
	_check(go.text == "Meetings done", "With the ticks spent, the way on is Meetings done again")
	# Every line at once, then cleared.
	var every := scene.find_child("MeetAllLines", true, false) as Control
	await _into_view(tree, every)
	_check(await _tap(every, "Select every line"), "A finger's tap ticks every line")
	await _frames(tree, 4)
	go = scene.find_child("PreSeasonGo", true, false) as Button
	_check(go.text == "Set stat focus for %d" % GameState.my_list.size(),
			"Every player on the list is ticked (%s)" % go.text)
	_check(await _tap(scene.find_child("MeetClearTicks", true, false), "Clear"), "A finger's tap clears the ticks")
	await _frames(tree, 4)
	go = scene.find_child("PreSeasonGo", true, false) as Button
	_check(go.text == "Meetings done", "Clear leaves nobody ticked")
	# His profile from his meeting on a phone.
	var tap := scene.find_child("MeetTap_" + str(d["id"]), true, false) as Control
	await _into_view(tree, tap)
	await _tap(tap, "a defender's meeting")
	await _frames(tree, 4)
	var prof := scene.find_child("MeetProfileOpen", true, false) as Control
	_check(prof != null and await _tap(prof, "Profile"), "A finger's tap on Profile in his meeting")
	await _frames(tree, 4)
	_check(scene.find_child("PlayerProfile", true, false) != null, "His profile opens from his meeting on a phone")
	Router.stack = []


func _dice() -> String:
	var cards := []
	for c in GameState.week_events:
		cards.append(str((c as Dictionary).get("tid", "")))
	var klass := Prospects.generate_class(GameState.season_year + 1, GameState.career_seed)
	var ids := []
	for p in klass:
		ids.append("%s/%d" % [str(p["id"]), int(p.get("overall", 0))])
	return str(hash([GameState.season.seed, str(GameState.season.fixture), cards,
			GameState.season.next_seed(3), ids]))


func _to_practice() -> void:
	_career()
	Press.to("practice")


## A bonding week's card, on the screen, by real taps: the stop says which
## week it is, the card answers, the outcome shows, and the way on works.
func _test_story_stop() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.size = Vector2i(390, 844)
	PreSeason.reload()
	_career()
	GameState.set_setting("seen_weekly_loop_intro", true)
	GameState.set_setting("seen_training_intro", true)
	_planned("develop")
	_week("bond")
	_check(GameState.preseason_stop() == "story" and not GameState.week_events.is_empty()
			and (StoryDeck.by_id(StoryDeck.all(), str(GameState.week_events[0]["tid"])).get("phase", []) as Array).has("bonding")
			and str(_acts()[0].get("card", "")) == str(GameState.week_events[0]["tid"]),
			"A bonding week deals one card from the bonding deck, and the week records it")
	if GameState.preseason_stop() != "story":
		return
	var scene: Control = await _open(tree)
	_check(scene != null and scene.name == "PreSeasonScene" and _label(scene, "PreSeasonHero") == "Team bonding, week 1",
			"A career saved at a card stop opens on that stop, saying which week it is")
	var first_choice := scene.find_child("Event_0", true, false) as Button
	_check(first_choice != null and scene.find_child("PreSeasonCards", true, false) != null,
			"The card is on the pre-season screen with its answers")
	_check(scene.find_child("EventGain_0_0", true, false) != null, "...and its small choice shows its Gain line")
	_check(_fits(scene, 390.0), "Nothing on the card stop runs off a phone's screen")
	var id := str(GameState.week_events[0]["tid"])
	_check(await _tap(first_choice, "the card's first answer"), "A finger's tap answers the card")
	_check(bool(GameState.week_events[0].get("resolved", false)) and int(GameState.week_events[0].get("choice", -1)) == 0
			and str(GameState.week_events[0].get("tid", "")) == id,
			"...and the answer is recorded")
	var scene2 := tree.current_scene as Control
	_check(scene2.find_child("Event_0", true, false) == null, "...and the card then shows what happened, not its buttons")
	var go := scene2.find_child("PreSeasonGo", true, false) as Button
	_check(await _tap(go, "the way on from the card"), "A finger's tap presses on from the card")
	await _frames(tree, 4)
	_check(GameState.preseason_stop() == "week" and not bool(GameState.preseason.get("story_pending", false)),
			"...and the pre-season is back to week 2")
	Router.stack = []
	GameState.delete_saved_career()


func _test_draft_card() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.size = Vector2i(390, 844)
	# The draft card, at the National Draft that follows: the line on a prospect
	# the club saw, and none on one it did not.
	PreSeason.reload()
	_to_practice()
	var offered: Array = GameState.preseason_prospects().map(func(p): return str(p["id"]))
	var held_back := 0
	for q in GameState.draftee_pool:
		held_back += 0 if offered.has(str(q["id"])) or GameState.drafted_draftees.has(str(q["id"])) else 1
	_check(held_back > 0 and not offered.is_empty(), "A new club's academy holds kids back from the trial list in its build year (%d)" % held_back)
	var seen_id := str(offered[3])
	GameState.toggle_practice_invite(seen_id)
	GameState.sim_practice_match()
	_press_on()
	var unseen_id := ""
	for q in GameState.draftee_pool:
		if unseen_id == "" and not ((q.get("seen", {}) as Dictionary).has(CLUB)):
			unseen_id = str(q["id"])
	GameState.season.round_index = GameState.season.fixture.size()
	var drafting: bool = GameState.begin_intake_draft()
	var missing := []
	for id in offered:
		var in_draft: bool = GameState.draft.picked.has(id)
		for q in GameState.draft.pool:
			in_draft = in_draft or str(q["id"]) == id
		if not in_draft:
			missing.append(id)
	_check(drafting and missing.is_empty(), "Every kid he could trial reaches the National Draft (%s)" % str(missing))
	var draft_scene: Control = load("res://scenes/DraftScene.tscn").instantiate()
	tree.root.add_child(draft_scene)
	await _frames(tree, 8)
	draft_scene.call("_open_player", seen_id)
	await _frames(tree, 4)
	var card_line := draft_scene.find_child("SeenPreSeason", true, false) as Label
	var seen_p: Dictionary = {}
	for q in GameState.draftee_pool:
		if str(q["id"]) == seen_id:
			seen_p = q
	_check(drafting and card_line != null and card_line.is_visible_in_tree()
			and card_line.text == PreSeason.seen_line(seen_p, CLUB) and card_line.text.begins_with("Seen in your"),
			"At the National Draft the card of a prospect he saw says so, and what he did that day (%s)" % (card_line.text if card_line != null else "no line"))
	draft_scene.queue_free()
	await _frames(tree, 3)
	draft_scene = load("res://scenes/DraftScene.tscn").instantiate()
	tree.root.add_child(draft_scene)
	await _frames(tree, 8)
	draft_scene.call("_open_player", unseen_id)
	await _frames(tree, 4)
	_check(unseen_id != "" and draft_scene.find_child("SeenPreSeason", true, false) == null,
			"A prospect he did not see has no such line")
	draft_scene.queue_free()
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


## The meetings need no scroll: the page's scroll container holds them whole.
func _one_page(scene: Control) -> bool:
	var page := scene.find_child("PreSeasonPage", true, false) as Control
	var lines := scene.find_child("PreSeasonMeetings", true, false) as Control
	if page == null or lines == null:
		return false
	var sc := page.get_parent() as ScrollContainer
	if sc == null:
		return false
	var ok := lines.get_global_rect().end.y <= sc.get_global_rect().end.y + 0.5 and sc.scroll_vertical == 0
	if not ok:
		push_error("Meetings run past the page: %s vs %s" % [str(lines.get_global_rect()), str(sc.get_global_rect())])
	return ok


func _fits(scene: Control, width: float) -> bool:
	var ok := true
	for n in scene.find_children("*", "Label", true, false):
		var l := n as Label
		if not l.is_visible_in_tree() or l.text == "":
			continue
		var r := l.get_global_rect()
		if r.position.x < -0.5 or r.end.x > width + 0.5:
			ok = false
			push_error("Off the screen: %s (%s)" % [l.text, str(r)])
	return ok


## Scroll `c` into view in the page's scroll container, as a thumb would.
func _into_view(tree: SceneTree, c: Control) -> void:
	var n: Node = c
	while n != null and not (n is ScrollContainer):
		n = n.get_parent()
	if n != null and c != null:
		(n as ScrollContainer).ensure_control_visible(c)
		await _frames(tree, 3)

