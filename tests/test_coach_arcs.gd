extends RefCounted
## Run by tests/run_coach_arcs_tests.gd (suite "coach_arcs").
## The coach's career arcs (CoachArcs.gd, ClubArcs.gd; director, 2026-11-03,
## phase 1): the arcs file is fit to play, arcs start only from real game
## state, beats come only from active arcs, the state persists through save and
## load (an old save loads empty), and with the switch "coach_arcs" off nothing
## is written or shown. A 10-season Sim-the-week career dumps its story log to
## tests/output/coach_arcs_story.txt (not committed) for a person to read.

var _tree: SceneTree
var checks := 0
var failures: Array[String] = []
const SUITE_SEED := 2027
const DUMP := "res://tests/output/coach_arcs_story.txt"


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _fresh() -> void:
	GameState.reset()
	GameState.start_season("FRE", GameDB.club_list("FRE"))
	GameState.replay_seed = SUITE_SEED
	GameState.tutorials = false
	Router.stack = []


## Answers this week's cards the way a player might: a seeded choice, and now
## and then no answer at all (the round settles it).
func _answer(rng: RandomNumberGenerator) -> void:
	for i in range(GameState.week_events.size()):
		var c: Dictionary = GameState.week_events[i]
		if bool(c.get("resolved", false)) or rng.randi_range(0, 5) == 0:
			continue
		GameState.resolve_card(i, rng.randi_range(0, (c.get("options", []) as Array).size() - 1))


func _week(rng: RandomNumberGenerator) -> void:
	_answer(rng)
	GameState.advance()


func run(tree: SceneTree) -> void:
	_tree = tree
	await _tree.process_frame
	GameState.autosave_enabled = false
	GameState.save_path = "user://test_coach_arcs.save"
	GameState.settings_path = "user://test_coach_arcs.cfg"
	GameState.delete_saved_career()
	_t("_test_switch_off")
	Features.set_on("coach_arcs", true)
	_t("_test_file_fit")
	_t("_test_triggers_from_state")
	_t("_test_beats_only_active")
	_t("_test_persist")
	_t("_test_ten_seasons")
	Features.clear("coach_arcs")
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	print(Ran.line("Coach arcs", self))
	for f in failures:
		print("  FAIL: " + f)


func _test_switch_off() -> void:
	_check(not Features.on("coach_arcs"), "the switch ships off")
	_fresh()
	GameState.board["confidence"] = 20
	var rng := RandomNumberGenerator.new()
	rng.seed = SUITE_SEED
	var arc_card := false
	for i in range(12):
		_week(rng)
		for c in GameState.week_events:
			arc_card = arc_card or str(c.get("coach_arc", "")) != ""
	_check(GameState.coach_arcs.is_empty(), "off: nothing is written")
	_check(not arc_card, "off: no arc card shows")
	_check(ClubArcs.big_call(GameState).is_empty(), "off: no big call")
	_check(GameState.news.filter(func(n): return str(n["kind"]) == ClubArcs.NEWS_KIND).is_empty(), "off: no arc news")
	_check(GameState.save_career() and GameState.load_career() and GameState.coach_arcs.is_empty(), "off: the save has no arcs")


func _test_file_fit() -> void:
	var defs := CoachArcs.all()
	_check(defs.size() == 10, "ten arcs are built (catalogue 1, 4, 5, 6, 8, 9, 10, 12, 13, 14), got %d" % defs.size())
	var errs := CoachArcs.validate(defs)
	_check(errs.is_empty(), "the arcs file is fit to play: %s" % str(errs))


func _test_triggers_from_state() -> void:
	_fresh()
	var rng := RandomNumberGenerator.new()
	rng.seed = SUITE_SEED + 1
	for i in range(3):
		_week(rng)
	var st: Dictionary = GameState.coach_arcs
	_check(not st.is_empty(), "on: the arc state is kept")
	_check(not (st["active"] as Dictionary).has("hot_seat") and not (st["active"] as Dictionary).has("drought") \
			and not (st["active"] as Dictionary).has("legacy"), "a new coach is not on the hot seat, in a drought or a legend")
	# The board really loses faith: the hot seat follows by round 8.
	GameState.board["confidence"] = 25
	for i in range(8):
		_week(rng)
	_check((st["active"] as Dictionary).has("hot_seat") or (st["done"] as Dictionary).has("hot_seat"),
			"a board below 40 by round 8 puts the coach on the hot seat")
	# A real trade request: the star-wants-out trigger names that player.
	var star: Dictionary = GameState.my_list[0]
	GameState.trade_requests[str(star["id"])] = {"year": GameState.season_year}
	var hit := ClubArcs.trigger(GameState, st, CoachArcs.by_id(CoachArcs.all(), "star_wants_out"), ClubStories.context(GameState), false)
	_check(str(hit.get("who", "")) == str(star["id"]), "a trade request triggers the star-wants-out arc about him: %s" % str(hit))
	GameState.trade_requests.erase(str(star["id"]))
	_check(ClubArcs.trigger(GameState, st, CoachArcs.by_id(CoachArcs.all(), "drought"), ClubStories.context(GameState), true).is_empty(),
			"no drought for a coach with no seasons behind him")

func _test_beats_only_active() -> void:
	_fresh()
	GameState.board["confidence"] = 25
	var rng := RandomNumberGenerator.new()
	rng.seed = SUITE_SEED + 2
	var seen := 0
	var stray := []
	for i in range(20):
		_answer(rng)
		GameState.advance()
		for c in GameState.week_events:
			var id := str(c.get("coach_arc", ""))
			if id == "":
				continue
			seen += 1
			if not (GameState.coach_arcs["active"] as Dictionary).has(id):
				stray.append(id)
			_check(ClubArcs.big_call(GameState).get("card", {}) == c or bool(c.get("resolved", false)), "the big call is the due beat")
	_check(seen > 0, "arc beats were dealt")
	_check(stray.is_empty(), "every beat comes from an active arc: %s" % str(stray))


func _test_persist() -> void:
	var before := JSON.stringify(GameState.coach_arcs)
	_check(before.length() > 20, "there is arc state to save")
	_check(GameState.save_career(), "saves")
	GameState.reset()
	_check(GameState.load_career(), "loads")
	_check(JSON.stringify(GameState.coach_arcs) == before, "the arcs come back as they were")
	# An old save (no arcs in it) loads empty.
	GameState.coach_arcs = {}
	_check(GameState.save_career() and GameState.load_career(), "an old save loads")
	_check(GameState.coach_arcs.is_empty(), "an old save's arcs start empty")


func _test_ten_seasons() -> void:
	_fresh()
	var rng := RandomNumberGenerator.new()
	rng.seed = SUITE_SEED + 3
	var sackings := []
	# Ten seasons locally (about 10 minutes); CI plays three to stay inside
	# the suite time limit. COACH_ARCS_SEASONS overrides either.
	var n := 3 if OS.get_environment("CI") != "" else 10
	if OS.get_environment("COACH_ARCS_SEASONS").is_valid_int():
		n = maxi(2, OS.get_environment("COACH_ARCS_SEASONS").to_int())
	for s in range(n):
		var guard := 0
		while not GameState.season.is_season_over() and guard < 40:
			guard += 1
			_week(rng)
			if GameState.is_sacked():
				# Test only: keep the career going to read ten seasons of story.
				sackings.append(GameState.season_year)
				GameState.board["sacked"] = false
				GameState.board["warned"] = false
				GameState.board["confidence"] = 45
		if s < n - 1:
			_check(GameState.start_next_season(), "season %d rolls on" % (s + 1))
	var st: Dictionary = GameState.coach_arcs
	var lines := PackedStringArray()
	lines.append("Coach arcs: %d seasons of Sim the week, FRE, seed %d. Sacked (and kept on, test only): %s" % [n, SUITE_SEED, str(sackings)])
	lines.append("Coach: %s" % JSON.stringify(st["coach"]))
	var started := {}
	for row in st["log"]:
		lines.append("%d %s [%s] %s" % [int(row[0]), str(row[1]), str(row[2]), str(row[3])])
		if str(row[3]).begins_with("BEGINS"):
			started[str(row[2])] = true
	lines.append("Arcs started: %s" % str(started.keys()))
	lines.append("Done: %s" % JSON.stringify(st["done"]))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://tests/output"))
	var f := FileAccess.open(DUMP, FileAccess.WRITE)
	if f != null:
		f.store_string("\n".join(lines) + "\n")
		f.close()
	_check(f != null, "the story log is written to %s" % DUMP)
	_check(started.size() >= (4 if n >= 10 else 1), "several arcs start over ten seasons: %s" % str(started.keys()))
	_check(int(st["coach"]["seasons"]) == n - 1, "every closed season is counted: %s" % str(st["coach"]))
