extends RefCounted
## The pre-season practice match (PreSeason.gd, GameState "practice"): who
## plays whom, the side and the prospects trialled, what it leaves behind (and
## what it must not), the AI clubs' matches, saves old and new, and the
## screens by real taps on a phone and a PC. Every season is seeded.

const Tap := preload("res://tests/tap.gd")

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 4127
const CLUB := "FRE"


func run() -> void:
	GameState.replay_seed = SUITE_SEED
	_t("_test_pairs")
	_t("_test_flow")
	_t("_test_trial")
	_t("_test_leaves_nothing")
	_t("_test_ai_clubs")
	_t("_test_determinism")
	_t("_test_saves")
	_t("_test_sim_to_round_one")
	await _t("_test_screens_phone")
	await _t("_test_sim_to_round_one_taps")
	await _t("_test_match_way")
	await _t("_test_screens_pc")
	await _t("_test_created_club")
	PreSeason.reload()
	GameState.delete_saved_career()
	for path in _snaps.values():
		CareerSave.delete(path)
	GameState.replay_seed = 0
	print(Ran.line("Practice", self))


func _check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _career(club := CLUB, seed := SUITE_SEED) -> void:
	GameState.reset()
	GameState.career_seed = seed
	GameState.replay_seed = seed
	GameState.start_season(club, GameDB.club_list(club))
	GameState.stories_on = false  # the pre-season cards have their own suites (preseason, story)
	GameState.open_preseason()


## Careers saved once and loaded again (load_career, the game's own path):
## a career and its pre-season to the practice stop cost several seconds to
## build, a load about half that. _test_saves proves a save at the stop loads
## at the stop with the trial as it was.
var _snaps := {}


func _snap(key: String) -> void:
	var path := "user://test_practice_%s.save" % key
	var was := GameState.save_path
	GameState.save_path = path
	GameState.save_career()
	GameState.save_path = was
	_snaps[key] = path


func _from_snap(key: String) -> bool:
	var was := GameState.save_path
	GameState.save_path = str(_snaps[key])
	var ok := GameState.load_career()
	GameState.save_path = was
	GameState.replay_seed = SUITE_SEED
	return ok


## Fremantle's first pre-season, waiting at the practice match: built and
## saved the first time, loaded every time after.
func _stop() -> void:
	if _snaps.has("stop"):
		_check(_from_snap("stop") and GameState.preseason_stop() == "practice" and not GameState.practice_played(),
				"(setup) the saved career loads at the practice stop")
		return
	_career()
	_check(_to_practice(), "(setup) the pre-season reaches the practice stop")
	_snap("stop")


## Press on until the practice match is waiting for the coach.
func _to_practice() -> bool:
	var guard := 0
	while GameState.preseason_active() and GameState.preseason_stop() != "practice" and guard < 12:
		guard += 1
		GameState.preseason_advance()
	return GameState.preseason_stop() == "practice"


## The papers wait in week 8 (their own suite, papers): pressing on passes them.
func _past_papers(at: String) -> String:
	return GameState.preseason_advance() if at == "papers" else at


## The same on screen: a tap on the way on passes the papers.
func _past_papers_scene(tree: SceneTree, scene: Control) -> Control:
	if scene != null and scene.name == "PreSeasonScene" and GameState.preseason_stop() == "papers":
		await _tap(scene.find_child("PreSeasonGo", true, false), "On to Round 1 from the papers")
		await _frames(tree, 10)
		return tree.current_scene as Control
	return scene


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
	for n in scene.find_children("*", "Label", true, false):
		var l := n as Label
		if not l.is_visible_in_tree() or l.text == "":
			continue
		var r := l.get_global_rect()
		if r.position.x < -0.5 or r.end.x > width + 0.5:
			ok = false
			push_error("Off the screen: %s (%s)" % [l.text, str(r)])
	return ok


func _ladder_sig() -> String:
	return str(GameState.season.ladder) + str(GameState.season.round_index) + str(GameState.season_log.size())


# ---------------------------------------------------------------------------
func _test_pairs() -> void:
	var all := []
	for c in GameDB.club_order.slice(0, 18):
		all.append(str(c))
	var pairs := PreSeason.practice_pairs(all, "FRE", SUITE_SEED, 2027)
	var seen := {}
	var twice := false
	for pr in pairs:
		twice = twice or seen.has(pr[0]) or seen.has(pr[1])
		seen[pr[0]] = true
		seen[pr[1]] = true
	_check(all.size() == 18 and pairs.size() == 9 and seen.size() == 18 and not twice,
			"The draw gives every one of the 18 clubs exactly one practice match")
	_check(PreSeason.practice_opponent(pairs, "FRE") == "WCE" and PreSeason.practice_opponent(pairs, "WCE") == "FRE",
			"Fremantle play West Coast")
	var near := true
	for pr in pairs:
		near = near and PreSeason.PRACTICE_REGION.get(pr[0], "x") == PreSeason.PRACTICE_REGION.get(pr[1], "y")
	_check(near and PreSeason.practice_opponent(pairs, "ADE") == "PAD" and PreSeason.practice_opponent(pairs, "BRL") == "GCS"
			and PreSeason.practice_opponent(pairs, "SYD") == "GWS",
			"Every pairing is within a region: the Western, Queensland, South Australian and Sydney derbies, and Victorian clubs against Victorian clubs")
	_check(str(PreSeason.practice_pairs(all, "FRE", SUITE_SEED, 2027)) == str(pairs),
			"The same career and year always give the same draw")
	var vic_opponents := {}
	for y in range(2027, 2047):
		vic_opponents[PreSeason.practice_opponent(PreSeason.practice_pairs(all, "MEL", SUITE_SEED, y), "MEL")] = true
	_check(vic_opponents.size() >= 4 and not vic_opponents.has("FRE"),
			"A Victorian club meets a different Victorian club from year to year")
	var odd := all.duplicate()
	odd.append("TAS")
	var p19 := PreSeason.practice_pairs(odd, "TAS", SUITE_SEED, 2027)
	_check(PreSeason.practice_opponent(p19, "TAS") != "" and p19.size() == 9,
			"With an odd number of clubs, yours still has a match (one other club has none)")
	var forged := all.duplicate()
	forged.append("ZZZ")
	forged.append("YYY")
	_check(PreSeason.practice_opponent(PreSeason.practice_pairs(forged, "ZZZ", SUITE_SEED, 2027), "ZZZ") == "YYY",
			"Two clubs outside any region are drawn against each other")
	_check(PreSeason.practice_opponent(PreSeason.practice_pairs(["FRE"], "FRE", 1, 2027), "FRE") == "",
			"A league of one has nobody to play")


func _test_flow() -> void:
	_stop()
	_check(GameState.preseason_week() == 7 and GameState.practice_opponent() == "WCE",
			"The pre-season stops after week 7 for the practice match, against West Coast")
	var pr := GameState.preseason_practice()
	_check(not GameState.practice_played() and (pr["invites"] as Array).is_empty() and not bool(pr["seen"]),
			"...with nobody trialled and nothing played")
	_check(GameState.preseason_step_week() == "practice" and GameState.preseason_week() == 7,
			"Training does not go on past the stop")
	GameState.sim_practice_match()
	_check(GameState.practice_played() and GameState.preseason_stop() == "practice",
			"Simming it plays it, and the stop stays for the report")
	var rep: Dictionary = GameState.preseason_practice()["report"]
	var names: Array = rep["names"]
	var score: Array = rep["score"]
	_check(names == ["Fremantle", "West Coast"] and int(score[0]) >= 0 and int(score[1]) >= 0 and str(rep["opponent"]) == "WCE",
			"The report names the two clubs and carries the score")
	_check(not GameState.sim_practice_match(), "It cannot be played twice")
	_check(_past_papers(GameState.preseason_advance()) == "done" and not GameState.preseason_active() and GameState.preseason_week() == 8,
			"Pressing on from the report finishes the last week and opens Round 1")
	# Set up and put down again, then pressed on: one career for both.
	_stop()
	var before: Array = GameState.my_list.map(func(p): return str(p["id"]) + str(p.get("xp", 0)))
	_check(GameState.prepare_practice_match() and GameState.pending_phase == "practice"
			and str(GameState.pending_match["home"]) == "FRE" and str(GameState.pending_match["away"]) == "WCE"
			and GameState.pending_sim != null,
			"Coached from the box, it is Fremantle at home to West Coast")
	GameState._clear_pending()
	_check(before.size() == GameState.my_list.size() and not GameState.practice_played(), "...and setting it up changes nobody")
	_check(GameState.preseason_advance() == "practice" and GameState.practice_played() and GameState.preseason_stop() == "practice",
			"Pressing on without playing it sims it and shows the report")


func _test_trial() -> void:
	_stop()
	var prospects: Array = GameState.preseason_prospects()
	var ids := prospects.slice(0, 8).map(func(p): return str(p["id"]))
	var all_in := true
	for i in range(6):
		all_in = all_in and GameState.toggle_practice_invite(ids[i])
	_check(all_in, "Up to six prospects can be trialled")
	_check(not GameState.toggle_practice_invite(ids[6]) and GameState.practice_invites().size() == 6,
			"...and not a seventh")
	_check(GameState.toggle_practice_invite(ids[5]) and GameState.practice_invites().size() == 5 and GameState.toggle_practice_invite(ids[6]),
			"An invitation can be taken back, and the place given to someone else")
	_check(not GameState.toggle_practice_invite("nobody"), "Someone not in the class cannot be trialled")
	var trialled: Array = GameState.practice_invites().duplicate()
	var built: Dictionary = GameState._practice_mine()
	var squad: Squad = (built["sim"] as MatchSim).squads[0]
	var on := squad.ground.filter(func(p): return trialled.has(str(p["id"])))
	var nums := {}
	var dup := false
	for p in squad.ground + squad.bench:
		dup = dup or nums.has(int(p["num"]))
		nums[int(p["num"])] = true
	_check(squad.ground.size() == 18 and squad.bench.size() == 5 and on.size() == 6 and not dup,
			"A trialled prospect starts: 18 on the ground and 5 on the bench, each with his own number")
	var every_guest := true
	for p in on:
		every_guest = every_guest and bool(p.get("guest", false)) and float(p.get("cond_injury", 1.0)) == 0.0
	_check(every_guest, "...each a guest who cannot be hurt")
	GameState.sim_practice_match()
	var rep: Dictionary = GameState.preseason_practice()["report"]
	var lines: Array = rep["prospects"]
	var noted := true
	for row in lines:
		var p := _pool(str(row["id"]))
		var note := PreSeason.seen_line(p, CLUB)
		noted = noted and trialled.has(str(row["id"])) and note.begins_with("Seen in your 2027 practice match.")
	_check(lines.size() == 6 and noted, "Each prospect trialled has a line on his draft card, in his own words: seen in the practice match")
	var p0 := _pool(trialled[0])
	_check(PreSeason.seen_mult(p0, CLUB) < 1.0 and PreSeason.seen_mult(p0, "ZZZ") == 1.0,
			"...and your club's read of him is surer, nobody else's")
	var hurt_guest := false
	for inj in GameState.preseason_injuries():
		hurt_guest = hurt_guest or trialled.has(str(inj["id"]))
	_check(not hurt_guest, "No prospect is ever hurt")
	var untouched := true
	for q in prospects:
		var note: Dictionary = (q.get("seen", {}) as Dictionary).get(CLUB, {})
		if not trialled.has(str(q["id"])) and str(note.get("kind", "")) == "practice":
			untouched = false
	_check(untouched, "Only the prospects trialled are noted")
	# An opponent never trials the same prospect.
	_stop()
	var mine: Array = GameState._guest_picks(CLUB, 6, [], 1.0)
	for id in mine:
		GameState.toggle_practice_invite(id)
	var b2: Dictionary = GameState._practice_mine()
	var g: Dictionary = b2["guests"]
	var clash := false
	for id in g["WCE"]:
		clash = clash or (g["FRE"] as Array).has(id)
	_check((g["FRE"] as Array).size() == 6 and (g["WCE"] as Array).size() == 6 and not clash,
			"Both clubs trial six prospects and never the same one")
	GameState._clear_pending()
	# Spots left empty are filled by your recruiters, as every club's are: the
	# match always gives its full look at the class (director, 2026-11-03).
	_stop()
	var own := str(GameState.preseason_prospects()[GameState.preseason_prospects().size() - 1]["id"])
	GameState.toggle_practice_invite(own)
	var picks: Array = GameState._guest_picks(CLUB, 6, [own], GameState.recruiting_uncertainty_mult())
	GameState.sim_practice_match()
	var filled: Array = GameState.practice_invites()
	_check(filled.size() == 6 and filled[0] == own and filled.slice(1) == picks
			and (GameState.preseason_practice()["report"]["prospects"] as Array).size() == 6,
			"A trial left short is filled by your recruiters' top-rated prospects, and all six are seen")


func _pool(id: String) -> Dictionary:
	for p in GameState.draftee_pool:
		if str(p.get("id", "")) == id:
			return p
	return {}


func _test_leaves_nothing() -> void:
	_stop()
	var ladder := _ladder_sig()
	var board := GameState.board_confidence()
	var tally := str(GameState.season_tally)
	var votes := str(GameState.season_log)
	GameState.sim_practice_match()
	_check(_ladder_sig() == ladder and GameState.board_confidence() == board and str(GameState.season_tally) == tally
			and str(GameState.season_log) == votes and GameState.season.round_index == 0,
			"It leaves nothing on the ladder, the season's record, the votes or the board")
	# Development: the same match with and without it.
	var with_dev := _lists_after(1.0)
	var without := _lists_after(0.0)
	var grew := 0
	var wce_grew := 0
	for k in with_dev["FRE"]:
		grew += 1 if with_dev["FRE"][k] != without["FRE"][k] else 0
	for k in with_dev["WCE"]:
		wce_grew += 1 if with_dev["WCE"][k] != without["WCE"][k] else 0
	_check(grew >= 23 - PreSeason.practice_guests() and wce_grew >= 23 - PreSeason.practice_guests(), "The players who play get a reserves game's development, at both clubs (%d, %d)" % [grew, wce_grew])
	PreSeason.reload()
	var leftover := false
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			leftover = leftover or p.has("cond_injury") or bool(p.get("guest", false))
	_check(not leftover, "Nobody keeps the day's half injury risk, and no guest is left on a list")
	# Injuries happen, at half the rate.
	var rate_ok := float(PreSeason.tune("practice_injury_rate")) == 0.5
	_check(rate_ok, "A listed player carries half a match's injury risk (the director's ruling)")
	var sq: Dictionary = GameState._practice_squad(CLUB, true, [])
	var half := true
	for p in (sq["squad"] as Squad).ground:
		half = half and float(p.get("cond_injury", 0.0)) == 0.5
	_check(half, "...in the side that takes the field")
	for p in GameState.my_list:
		p.erase("cond_injury")


func _lists_after(games: float) -> Dictionary:
	PreSeason.reload()
	PreSeason.data()["practice_xp_games"] = games
	PreSeason.data()["practice_injury_rate"] = 0.0
	_stop()
	GameState.sim_practice_match()
	var out := {}
	for code in ["FRE", "WCE"]:
		var rows := {}
		for p in GameState.season.lists[code]:
			rows[str(p["id"])] = "%d/%d" % [int(p["overall"]), int(p.get("xp", 0))]
		out[code] = rows
	PreSeason.reload()
	return out


func _test_ai_clubs() -> void:
	_career()
	var before := {}
	for code in GameState.season.clubs:
		before[str(code)] = GameState.season.lists[code].map(func(p): return int(p.get("xp", 0)))
	_to_practice()
	var seen_by := {}
	for q in GameState.draftee_pool:
		for club in (q.get("seen", {}) as Dictionary):
			if (q["seen"][club] as Dictionary).get("kind", "") == "practice":
				seen_by[str(club)] = true
	_check(not seen_by.has(CLUB) and not seen_by.has("WCE") and seen_by.size() >= 12,
			"Every other pair of clubs has played too, each noting the prospects it trialled")
	var pr: Dictionary = GameState.preseason_practice()
	_check(GameState.season.round_index == 0 and GameState.season_log.is_empty(),
			"...and none of it is on the ladder")
	var hurt := 0
	for inj in GameState.preseason_injuries():
		if str(inj.get("how", "")) == "practice":
			hurt += 1
	_check(hurt >= 0, "AI clubs' practice injuries are recorded the way match injuries are")
	_check(str(pr.get("opponent", "")) == "WCE", "Your pairing is waiting for you, not played")


func _test_determinism() -> void:
	var sigs := []
	for i in range(2):
		_career()
		_to_practice()
		GameState.toggle_practice_invite(str(GameState.preseason_prospects()[0]["id"]))
		GameState.sim_practice_match()
		var rep: Dictionary = GameState.preseason_practice()["report"]
		sigs.append(str(rep["score"]) + str(rep["stood"]) + str(rep["prospects"]))
	_check(sigs[0] == sigs[1], "The same career, side and trial give the same practice match")


func _test_saves() -> void:
	_stop()
	GameState.toggle_practice_invite(str(GameState.preseason_prospects()[1]["id"]))
	GameState.save_career()
	var kept: Dictionary = GameState.preseason_practice().duplicate(true)
	# No reset() first: load_career resets the career itself (_restore_career).
	_check(GameState.load_career() and GameState.preseason_stop() == "practice"
			and str(GameState.preseason_practice()) == str(kept),
			"A save made at the practice stop loads at the practice stop, the trial as it was")
	GameState.sim_practice_match()
	GameState.save_career()
	_check(GameState.load_career() and GameState.practice_played() and GameState.preseason_stop() == "practice"
			and not (GameState.preseason_practice()["report"] as Dictionary).is_empty(),
			"A save made after the match keeps its report")
	# Old saves: made before there was a practice match.
	_stop()
	GameState.preseason.erase("practice")
	_check(GameState.preseason_stop() == "" and _past_papers(GameState.preseason_advance()) == "done" and not GameState.preseason_active(),
			"A save from week 7 with no practice match runs on to Round 1")
	_career()
	GameState.preseason_advance()  # to the time trial, week 3
	GameState.save_career()
	var raw := CareerSave.read(GameState.save_path)
	_check(not (raw.get("preseason", {}) as Dictionary).has("practice"), "(a save from before week 7 holds no practice match yet)")
	_check(GameState.load_career() and GameState.preseason_week() < 5, "(setup) the save loads at the time trial")
	# Pressed on from the time trial until past week 5 (where the old
	# intra-club stop stood): it runs on to week 7 and the practice match.
	var guard := 0
	while GameState.preseason_week() < 5 and guard < 8:
		guard += 1
		GameState.preseason_advance()
	_check(GameState.preseason_week() == 7 and GameState.preseason_stop() == "practice",
			"With no intra-club match, pressing on from the time trial runs to the practice match at the end of week 7")
	_check(GameState.practice_opponent() == "WCE",
			"A save from before week 7 loads and meets the practice match when it gets there")
	# A save standing at the old intra-club stop (end of week 5, before the one
	# pre-season match, director 2026-11-03): it loads, the old match is gone,
	# and pressing on meets the practice match. Made from the same career.
	GameState.preseason["week"] = 5
	GameState.preseason.erase("practice")
	GameState.preseason["intra"] = {"mode": "best", "invites": [], "played": false, "seen": false}
	GameState.save_career()
	_check(GameState.load_career() and not GameState.preseason.has("intra") and GameState.preseason_stop() == "",
			"A save from the old intra-club stop loads with the old match gone and the pre-season not waiting")
	_check(GameState.preseason_advance() == "practice" and GameState.preseason_week() == 7 and GameState.practice_opponent() == "WCE",
			"...and pressing on meets the practice match at the end of week 7")


## The news lines naming the practice match's result (not its injuries, whose
## line also says "practice match").
func _practice_news() -> Array:
	var out := []
	for n in GameState.news:
		if str(n.get("kind", "")) == "preseason" and str(n.get("text", "")).begins_with("Practice match: "):
			out.append(n)
	return out


func _test_sim_to_round_one() -> void:
	_career()
	GameState.preseason_sim_to_round1()
	_check(not GameState.preseason_active() and GameState.practice_played() and bool(GameState.preseason_practice()["seen"]),
			"Sim to Round 1 plays the practice match on the settings in force and does not stop for it")
	var lines := _practice_news()
	var line := str(lines[0]["text"]) if lines.size() == 1 else ""
	var rep: Dictionary = GameState.preseason_practice().get("report", {})
	var g: Array = rep.get("goals", [0, 0])
	var b: Array = rep.get("behinds", [0, 0])
	var stood: Array = rep.get("stood", [])
	var first := GameDB.player_display_name(GameState.list_player(str(stood[0]))) if not stood.is_empty() else ""
	_check(lines.size() == 1 and not stood.is_empty() and line.contains("Fremantle %d.%d (%d)" % [int(g[0]), int(b[0]), int(g[0]) * 6 + int(b[0])])
			and line.contains("West Coast %d.%d (%d)" % [int(g[1]), int(b[1]), int(g[1]) * 6 + int(b[1])])
			and line.contains("Stood out: " + first) and str(lines[0]["when"]) == "Pre-season",
			"Simmed past, the practice match's result and who stood out go in the news, once (%s)" % line)
	# Round 1 set up with the pre-season still running (the hub's safety net) does the same.
	_career()
	GameState.preseason_advance()
	_check(GameState.prepare_interactive_match() and GameState.practice_played() and not GameState.preseason_active()
			and _practice_news().size() == 1,
			"Round 1 set up mid pre-season sims the practice match and puts its result in the news")
	GameState._clear_pending()
	# Already played and its report shown at the stop: no news line on top.
	_stop()
	GameState.sim_practice_match()
	GameState.preseason_sim_to_round1()
	_check(not GameState.preseason_active() and _practice_news().is_empty(),
			"A practice match already played and shown adds no news line on the way to Round 1")
	# Melbourne's opponent: checked in _test_screens_pc, on the Melbourne career
	# it takes to the same stop.


func _tap_to_practice(tree: SceneTree) -> Control:
	var scene: Control = await _open(tree)
	var guard := 0
	while GameState.preseason_stop() != "practice" and guard < 10:
		guard += 1
		var go := scene.find_child("PreSeasonGo", true, false) as Control
		await _tap(go, "the way on")
		await _frames(tree, 10)
		scene = tree.current_scene as Control
	return scene


func _test_screens_phone() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.size = Vector2i(390, 844)
	# The stop itself is under test here: the taps through the weeks to it are
	# proved by _test_created_club (coached) and _test_screens_pc.
	_stop()
	GameState.set_setting("seen_weekly_loop_intro", true)
	GameState.set_setting("seen_training_intro", true)
	var scene: Control = await _open(tree)
	_check(scene != null and scene.name == "PreSeasonScene" and GameState.preseason_stop() == "practice"
			and _label(scene, "PreSeasonHero") == "The practice match"
			and _label(scene, "PracticeHome") == "Fremantle" and _label(scene, "PracticeAway") == "West Coast",
			"Phone: the practice stop names the match, Fremantle at home to West Coast")
	_check(_label(scene, "PracticeCount") == "0 of 6 trialled" and _label(scene, "PracticePlan").begins_with("Game plan: ")
			and scene.find_child("PracticeSelection", true, false) != null and _fits(scene, 390.0),
			"Phone: it says how many are trialled, the plan, and fits the screen")
	_check(scene.find_child("IntraSetup", true, false) == null and scene.find_child("PracticeFill", true, false) != null,
			"Phone: one pre-season match (no intra-club stop on the way), and the recruiters can fill the trial")
	var ids: Array = GameState.preseason_prospects().slice(0, 2).map(func(p): return str(p["id"]))
	for id in ids:
		_check(await _tap(scene.find_child("Trial_" + str(id), true, false), "a prospect"),
				"Phone: a finger's tap trials a prospect")
	_check(GameState.practice_invites().size() == 2 and _label(scene, "PracticeCount") == "2 of 6 trialled"
			and bool((scene.find_child("Trial_" + str(ids[0]), true, false) as Button).get_meta("chosen", false)),
			"Phone: the two are marked and counted")
	# The gate states both sides, sized from the rules (director, 2026-10-18).
	var cost2 := _label(scene, "PracticeCost")
	var gap2 := GameState.practice_trial_gap_pct(GameState.practice_invites())
	_check(_label(scene, "PracticeGain").contains("%d%% tighter" % roundi((1.0 - float(PreSeason.tune("seen_uncertainty"))) * 100.0))
			and (cost2.contains("about %d%% below" % gap2) if gap2 > 0 else cost2.contains("no lower")),
			"Phone: the trial's gain and cost carry their sizes, the cost for the two chosen (%s)" % cost2)
	var risk := _label(scene, "PracticeRisk")
	_check(risk.contains("%d%% of a normal match's injury risk" % roundi(float(PreSeason.tune("practice_injury_rate")) * 100.0))
			and risk.contains("prospect cannot be hurt") and _label(scene, "PracticeGain").contains("He cannot be hurt"),
			"Phone: the injury rule reads the same in both places: listed players at half risk, a prospect never hurt (%s)" % risk)
	_check(await _tap(scene.find_child("Trial_" + str(ids[1]), true, false), "the same prospect"),
			"Phone: a second tap takes it back")
	_check(GameState.practice_invites().size() == 1, "Phone: ...and he is out")
	# Side and plan are one tap away, and Back comes home.
	_check(await _tap(scene.find_child("PracticeSelection", true, false), "Selection"), "Phone: a finger's tap opens Selection")
	await _frames(tree, 8)
	_check(Router.current() == "selection", "Phone: Selection opens")
	Router.back()
	await _frames(tree, 8)
	scene = tree.current_scene as Control
	_check(scene != null and scene.name == "PreSeasonScene" and GameState.practice_invites().size() == 1
			and GameState.preseason_stop() == "practice",
			"Phone: Back from Selection returns to the practice stop with the trial kept")
	Router.handle_back()
	await _frames(tree, 8)
	_check(Router.current() == "main" and GameState.preseason_stop() == "practice",
			"Phone: Back at the stop goes to the main menu and keeps it")
	scene = await _open(tree)
	# Coach it.
	_check(await _tap(scene.find_child("PreSeasonGo", true, false), "Coach the match"), "Phone: a finger's tap goes to coach the match")
	await _frames(tree, 30)
	var m := tree.current_scene as Control
	_check(m != null and m.name == "MatchScene" and GameState.pending_phase == "practice"
			and str(GameState.pending_match["home"]) == "FRE" and str(GameState.pending_match["away"]) == "WCE"
			and int(m.get("_my_side")) == 0,
			"Phone: the match opens in the match view, Fremantle v West Coast, the coach in charge of Fremantle")
	var ladder := _ladder_sig()
	m.call("_on_skip")
	await _frames(tree, 40)
	var cont := m.find_child("FullTimeContinue", true, false) as Button
	_check(cont != null and GameState.practice_played() and m.find_child("LadderMove", true, false) == null
			and m.find_child("NextFixture", true, false) == null,
			"Phone: at full time it is over and nothing is said of the ladder or a next round (cont %s, played %s, ladder %s, next %s)" % [
			str(cont != null), str(GameState.practice_played()), str(m.find_child("LadderMove", true, false)), str(m.find_child("NextFixture", true, false))])
	_check(await _tap(cont, "Continue at full time"), "Phone: a finger's tap leaves full time")
	await _frames(tree, 12)
	scene = tree.current_scene as Control
	_check(scene != null and scene.name == "PreSeasonScene" and GameState.preseason_stop() == "practice"
			and _label(scene, "PracticeSide_0") == "Fremantle" and _label(scene, "PracticeSide_1") == "West Coast"
			and _label(scene, "PracticeStood_0") != "" and _label(scene, "PracticeSeen_0") != ""
			and _label(scene, "PracticeSeenLine_0") != "" and _ladder_sig() == ladder and _fits(scene, 390.0),
			"Phone: the report shows the score, who stood out and the line on the prospect, and the ladder is untouched")
	_check(await _tap(scene.find_child("PreSeasonGo", true, false), "Back to training after the match"),
			"Phone: a finger's tap goes on")
	await _frames(tree, 10)
	scene = tree.current_scene as Control
	scene = await _past_papers_scene(tree, scene)
	_check(scene != null and scene.name == "HubScene" and not GameState.preseason_active() and GameState.preseason_week() == 8,
			"Phone: the quiet week passes and the hub opens at Round 1")
	# Simmed from the screen.
	_stop()
	scene = await _open(tree)
	_check(await _tap(scene.find_child("PracticeSim", true, false), "Sim the match"), "Phone: a finger's tap sims the match")
	await _frames(tree, 6)
	scene = tree.current_scene as Control
	_check(GameState.practice_played() and _label(scene, "PracticeSide_0") == "Fremantle",
			"Phone: simming shows the report")
	Router.stack = []


## Sim to Round 1 by real taps on a phone: it says first what it plays without
## you; Cancel and Back keep the pre-season; going on reaches the hub with the
## practice match's result in the news.
func _test_sim_to_round_one_taps() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.size = Vector2i(390, 844)
	_career()
	GameState.set_setting("seen_weekly_loop_intro", true)
	GameState.set_setting("seen_training_intro", true)
	GameState.set_confirm_sim_round(true)
	var scene: Control = await _open(tree)
	_check(scene != null and scene.name == "PreSeasonScene" and GameState.preseason_stop() == "plan",
			"Phone: a new career opens on the pre-season plan")
	_check(await _tap(scene.find_child("PreSeasonSim", true, false), "Sim to Round 1"), "Phone: a finger's tap on Sim to Round 1")
	await _frames(tree, 6)
	var sheet := scene.get_node_or_null("PreSeasonSimConfirm") as Control
	var why := _label(scene, "PreSeasonSimWhy")
	_check(sheet != null and sheet.is_visible_in_tree() and GameState.preseason_active() and why.contains("practice match")
			and why.contains("time trial") and _fits(scene, 390.0),
			"Phone: it asks first, naming the time trial and the practice match (%s)" % why)
	var go := scene.find_child("PreSeasonSimGo", true, false) as Control
	var cancel := scene.find_child("PreSeasonSimCancel", true, false) as Control
	_check(go != null and cancel != null and go.size.y >= 44.0 and cancel.size.y >= 44.0,
			"Phone: both answers are thumb-sized")
	_check(await _tap(cancel, "Cancel"), "Phone: a finger's tap on Cancel")
	await _frames(tree, 4)
	_check(scene.get_node_or_null("PreSeasonSimConfirm") == null and GameState.preseason_active()
			and GameState.preseason_stop() == "plan" and not GameState.practice_played(),
			"Phone: Cancel closes it and nothing is played")
	await _tap(scene.find_child("PreSeasonSim", true, false), "Sim to Round 1 again")
	await _frames(tree, 6)
	Router.handle_back()
	await _frames(tree, 4)
	_check(Router.current() == "preseason" and scene.get_node_or_null("PreSeasonSimConfirm") == null
			and GameState.preseason_active(),
			"Phone: Back closes the question and stays on the pre-season")
	await _tap(scene.find_child("PreSeasonSim", true, false), "Sim to Round 1 a third time")
	await _frames(tree, 6)
	_check(await _tap(scene.find_child("PreSeasonSimGo", true, false), "Sim to Round 1 in the question"),
			"Phone: a finger's tap goes on")
	await _frames(tree, 12)
	scene = tree.current_scene as Control
	_check(scene != null and scene.name == "HubScene" and not GameState.preseason_active() and GameState.practice_played()
			and _practice_news().size() == 1,
			"Phone: the hub opens at Round 1 with the practice match played and its result in the news")
	Router.stack = []


## The practice match is always watched: Skip does not carry over, because the
## coach pressed Coach the match (Sim the match is beside it), and an old Key
## moments setting (cut, director 2026-11-08) reads as Watch.
func _test_match_way() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.size = Vector2i(390, 844)
	var was := GameState.match_way()
	for way in ["skip", "watch", "key"]:
		_stop()
		# Written raw: "key" is what an install from before the cut still holds.
		GameState.set_setting("match_way", way)
		GameState.match_way_live = "skip"   # a leftover from another match
		_check(GameState.prepare_practice_match() and GameState.match_way_live == "watch",
				"With %s set, the practice match is watched (%s)" % [way, GameState.match_way_live])
		GameState._clear_pending()
	_stop()
	GameState.set_match_way("skip")
	GameState.set_setting("seen_weekly_loop_intro", true)
	GameState.set_setting("seen_training_intro", true)
	var scene: Control = await _open(tree)
	_check(await _tap(scene.find_child("PreSeasonGo", true, false), "Coach the match"), "Phone: a finger's tap goes to coach the match")
	var m: Control = null
	for i in range(120):
		await tree.process_frame
		m = tree.current_scene as Control
		if m != null and m.name == "MatchScene" and m.find_child("CoachBox", true, false) != null:
			break
	var speeds_shown := 0
	var km_node := false
	if m != null and m.name == "MatchScene":
		for b in m.get("_speed_btns"):
			if (b as Control).is_visible_in_tree():
				speeds_shown += 1
		for c in m.find_children("*", "Control", true, false):
			if str(c.name).begins_with("KeyMoments"):
				km_node = true
	_check(m != null and m.name == "MatchScene" and m.find_child("CoachBox", true, false) != null
			and not bool(m.get("_fulltime_shown")) and speeds_shown == 4 and not km_node,
			"Phone: with Skip set, Coach the match opens the practice match watched (scene %s, live %s, speeds %d)" % [
			str(m.name) if m != null else "none", GameState.match_way_live, speeds_shown])
	GameState._clear_pending()
	GameState.set_match_way(was)
	Router.stack = []
	Router.replace("hub")
	await _frames(tree, 4)


func _test_screens_pc() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.size = Vector2i(960, 540)
	_career("MEL")
	GameState.set_setting("seen_weekly_loop_intro", true)
	GameState.set_setting("seen_training_intro", true)
	var scene: Control = await _tap_to_practice(tree)
	var opp := GameState.practice_opponent()
	_check(PreSeason.PRACTICE_REGION.get(opp, "") == "VIC" and opp != "MEL",
			"Melbourne's practice match is against another Victorian club (%s)" % opp)
	_check(scene != null and scene.name == "PreSeasonScene" and _label(scene, "PracticeHome") == "Melbourne" and _label(scene, "PracticeAway") == GameDB.club_name(opp)
			and _fits(scene, 960.0),
			"PC: the practice stop fits the screen and names the match")
	var go := scene.find_child("PreSeasonGo", true, false) as Control
	var foot := scene.find_child("PreSeasonActions", true, false) as Control
	_check(go != null and go.size.x < 500.0 and foot != null and foot.get_global_rect().end.y <= 540.0,
			"PC: the way on is sized to its words and the buttons are on the screen")
	var id := str(GameState.preseason_prospects()[0]["id"])
	_check(await _tap(scene.find_child("Trial_" + id, true, false), "a prospect"), "PC: a click trials a prospect")
	_check(GameState.practice_invites() == [id], "PC: he is trialled")
	_check(await _tap(scene.find_child("PracticePlanGo", true, false), "Game plan"), "PC: a click opens the game plan")
	await _frames(tree, 8)
	_check(Router.current() == "coaching", "PC: the game plan opens")
	Router.back()
	await _frames(tree, 8)
	scene = tree.current_scene as Control
	_check(await _tap(scene.find_child("PracticeSim", true, false), "Sim the match"), "PC: a click sims the match")
	await _frames(tree, 6)
	scene = tree.current_scene as Control
	_check(GameState.practice_played() and _label(scene, "PracticeSide_0") == "Melbourne"
			and _label(scene, "PracticeSide_1") == GameDB.club_name(opp) and _fits(scene, 960.0),
			"PC: the report shows the two clubs and fits")
	_check(await _tap(scene.find_child("PreSeasonGo", true, false), "Back to training"), "PC: a click goes on")
	await _frames(tree, 8)
	scene = tree.current_scene as Control
	scene = await _past_papers_scene(tree, scene)
	_check(scene != null and scene.name == "HubScene" and not GameState.preseason_active(),
			"PC: the hub opens at Round 1")
	tree.root.size = Vector2i(390, 844)
	Router.stack = []
	if tree.current_scene != null:
		tree.current_scene.queue_free()
	await _frames(tree, 3)


## A career with a created club (Club Forge): its own League Draft, then the
## pre-season opened on the seed. Before 2026-11-07 a created club had no
## region, was the odd club out of 19 and never got its practice match.
func _created_career() -> void:
	GameState.reset()
	GameState.career_seed = SUITE_SEED
	GameState.replay_seed = SUITE_SEED
	GameState.create_club({"name": "Port Melbourne", "short": "Borough", "code": "PMB",
			"location": "port-melbourne", "primary": "#1B3A8C", "secondary": "#C8102E",
			"accent": "#FFFFFF", "design": "hoops", "kit": "p/s/a"})
	GameState.begin_draft()
	var draft: Draft = GameState.draft
	draft.start_for_user("PMB")
	var guard := 0
	while not draft.is_finished() and guard < 5000:
		guard += 1
		var cand := draft._best_ai_pick(draft.current_club())
		if cand.is_empty() or not draft._draft_pick(draft.current_club(), cand):
			draft._skip_current_pick()
	GameState.start_season("PMB", draft.list())
	GameState.stories_on = false
	GameState.set_setting("seen_weekly_loop_intro", true)
	GameState.set_setting("seen_training_intro", true)
	GameState.open_preseason()


## Every way through the pre-season plays the created club's practice match
## and shows its report: coached from the box, simmed from the stop, pressed
## on without playing, and Sim to Round 1. Real taps on a phone.
func _test_created_club() -> void:
	var all := []
	for c in GameDB.club_order.slice(0, 18):
		all.append(str(c))
	var alone := all.duplicate()
	alone.append("ZZZ")
	var p19 := PreSeason.practice_pairs(alone, "ZZZ", SUITE_SEED, 2027)
	_check(PreSeason.practice_opponent(p19, "ZZZ") != "" and p19.size() == 9,
			"A club outside every region, left alone once the regions pair off, still has a match")
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.size = Vector2i(390, 844)
	# Coached. The created career is built once and saved twice, at the plan
	# and at the practice stop; the other three ways load it.
	_created_career()
	_snap("created_plan")
	var scene: Control = await _tap_to_practice(tree)
	_snap("created_stop")
	var opp := GameState.practice_opponent()
	_check(GameState.preseason_stop() == "practice" and PreSeason.PRACTICE_REGION.get(opp, "") == "VIC"
			and _label(scene, "PracticeHome") == "Port Melbourne",
			"A created club from Port Melbourne stops for its practice match, against a Victorian club (%s)" % opp)
	_check(await _tap(scene.find_child("PreSeasonGo", true, false), "Coach the match"),
			"Created club: a finger's tap goes to coach the match")
	await _frames(tree, 30)
	var m := tree.current_scene as Control
	_check(m != null and m.name == "MatchScene" and GameState.pending_phase == "practice",
			"Created club: the practice match opens in the match view")
	if m != null and m.name == "MatchScene":
		m.call("_on_skip")
		await _frames(tree, 40)
		await _tap(m.find_child("FullTimeContinue", true, false), "Continue at full time")
		await _frames(tree, 12)
	scene = tree.current_scene as Control
	_check(GameState.practice_played() and scene != null and scene.name == "PreSeasonScene"
			and _label(scene, "PracticeSide_0") == "Port Melbourne",
			"Created club, coached: the match is played and its report shown")
	# Simmed from the stop.
	_check(_from_snap("created_stop") and str(GameState.custom_club.get("code", "")) == "PMB" and GameState.preseason_stop() == "practice",
			"(setup) the created club's career loads at the practice stop")
	scene = await _open(tree)
	_check(await _tap(scene.find_child("PracticeSim", true, false), "Sim the match"),
			"Created club: a finger's tap sims the match")
	await _frames(tree, 6)
	scene = tree.current_scene as Control
	_check(GameState.practice_played() and _label(scene, "PracticeSide_0") == "Port Melbourne",
			"Created club, simmed: the match is played and its report shown")
	# Pressed on without playing.
	_from_snap("created_stop")
	_check(GameState.preseason_advance() == "practice" and GameState.practice_played()
			and GameState.preseason_stop() == "practice",
			"Created club, pressed on: the match is simmed and the report waits")
	# Sim to Round 1 from the plan.
	_check(_from_snap("created_plan") and GameState.preseason_stop() == "plan" and GameState.my_club == "PMB",
			"(setup) the created club's career loads at the pre-season plan")
	scene = await _open(tree)
	_check(await _tap(scene.find_child("PreSeasonSim", true, false), "Sim to Round 1"),
			"Created club: a finger's tap sims to Round 1")
	await _frames(tree, 4)
	# Ask before simming (#1101): the question's Sim to Round 1, when it asks.
	if scene.get_node_or_null("PreSeasonSimConfirm") != null:
		await _tap(scene.find_child("PreSeasonSimGo", true, false), "Sim to Round 1 in the question")
	await _frames(tree, 10)
	_check(not GameState.preseason_active() and GameState.practice_played()
			and not (GameState.preseason_practice().get("report", {}) as Dictionary).is_empty(),
			"Created club, Sim to Round 1: the match is played on the way and its report kept")
	Router.stack = []
	GameDB.unregister_custom_clubs()
