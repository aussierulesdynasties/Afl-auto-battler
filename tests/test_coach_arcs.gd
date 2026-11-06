extends RefCounted
## Run by tests/run_coach_arcs_tests.gd (suite "coach_arcs").
## The coach's career arcs (CoachArcs.gd, ClubArcs.gd; director, 2026-11-03,
## phase 1): the arcs file is fit to play, arcs start only from real game
## state, beats come only from active arcs, the state persists through save and
## load (an old save loads empty). A 10-season Sim-the-week career dumps its story log to
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
	_t("_test_file_fit")
	_t("_test_triggers_from_state")
	_t("_test_beats_only_active")
	_t("_test_persist")
	_t("_test_hero_count_trigger")
	_t("_test_poached_moves_club")
	_t("_test_sacked_way_back")
	_t("_test_reunion")
	_t("_test_drought_counts_this_club")
	_t("_test_assistant_leaves")
	_t("_test_ten_seasons")
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	print(Ran.line("Coach arcs", self))
	for f in failures:
		print("  FAIL: " + f)


func _test_file_fit() -> void:
	var defs := CoachArcs.all()
	_check(defs.size() == 14, "all fourteen catalogue arcs are built, got %d" % defs.size())
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
			# A sacking no longer ends the career: the coach changes clubs.
			_check(not GameState.is_sacked(), "a sacked coach goes on at another club")
		if s < n - 1:
			_check(GameState.start_next_season(), "season %d rolls on" % (s + 1))
	var st: Dictionary = GameState.coach_arcs
	var lines := PackedStringArray()
	lines.append("Coach arcs: %d seasons of Sim the week, FRE, seed %d. Clubs: %s" % [n, SUITE_SEED, JSON.stringify(st["coach"]["clubs"])])
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


## Plays the rest of this season, keeping the board where `conf` puts it (-1: leave it).
func _play_out(rng: RandomNumberGenerator, conf := -1) -> void:
	var guard := 0
	while not GameState.season.is_season_over() and guard < 40:
		guard += 1
		if conf >= 0:
			GameState.board["confidence"] = conf
			GameState.board["warned"] = true
		_week(rng)


func _senior_at(code: String) -> Dictionary:
	return ClubMoves._senior_coach(GameState, code)


func _my_assistant() -> String:
	for cid in GameState.coaches:
		var c: Dictionary = GameState.coaches[cid]
		if str(c.get("club", "")) == GameState.my_club and str(c.get("job", "")) == "SA" and str(c.get("status", "")) == "club":
			return str(cid)
	return ""


## Arc 3: a rival's offer taken in season; at its close the arc ends "left",
## and at the rollover he is that club's coach, its coach takes his old job,
## and his record carries on. Persists across save and load.
func _test_poached_moves_club() -> void:
	_fresh()
	var rng := RandomNumberGenerator.new()
	rng.seed = SUITE_SEED + 4
	for i in range(3):
		_week(rng)
	var st: Dictionary = GameState.coach_arcs
	# The trigger reads real finishes: two top-4 seasons at this club.
	var roll: Array = GameState.honour_roll.duplicate(true)
	var finish: Dictionary = GameState._last_finish.duplicate()
	GameState._last_finish = {}
	var k := 0
	for code in GameState.season.ladder:
		k += 1
		GameState._last_finish[str(code)] = k
	GameState.honour_roll.append({"year": GameState.season_year, "my_club": "FRE", "my_position": 2, "premier": "COL"})
	GameState.honour_roll.append({"year": GameState.season_year, "my_club": "FRE", "my_position": 3, "premier": "FRE"})
	var def := CoachArcs.by_id(CoachArcs.all(), "poached")
	_check(ClubMoves.poach_trigger(GameState, st, def["trigger"], false).is_empty(), "poached: only at a season's start")
	var hit := ClubMoves.poach_trigger(GameState, st, def["trigger"], true)
	GameState.honour_roll = roll
	GameState._last_finish = finish
	var suitor := str(hit.get("mem", {}).get("suitor_code", ""))
	_check(suitor != "" and suitor != "FRE", "poached: a struggling rival wants him: %s" % str(hit))
	if suitor == "":
		return
	var their_coach := _senior_at(suitor)
	_check(not their_coach.is_empty(), "poached: the suitor has a senior coach to replace")
	var rec := CoachArcs.start(st, def, GameState.season_year, GameState.story_week(), "", hit["mem"])
	var facts := ClubArcs._facts(GameState, st, rec, {"club": "Fremantle", "opp": ""})
	var b := CoachArcs.due_beat(def, rec, GameState.story_week(), GameState.season_year, "regular", facts)
	_check(str(b.get("id", "")) == "arc_poach_call", "poached: the first beat is the call: %s" % str(b.get("id", "")))
	_check(StoryEngine.fill("{suitor_president} of {suitor}", facts).find("{") < 0, "poached: its names fill the text")
	CoachArcs.answer(def, rec, "arc_poach_call", "listen", GameState.story_week(), GameState.season_year)
	CoachArcs.answer(def, rec, "arc_poach_offer", "take", GameState.story_week() + 3, GameState.season_year)
	CoachArcs.answer(def, rec, "arc_poach_captain", "truth", GameState.story_week() + 5, GameState.season_year)
	_check((rec["flags"] as Dictionary).has("taking") and int(rec["beat"]) == 3, "poached: the offer is taken and every beat played")
	_play_out(rng)
	_check(str(st["move"].get("to", "")) == suitor and str(st["move"].get("why", "")) == "poached", "poached: the move waits for the rollover: %s" % str(st["move"]))
	_check(str(st["done"].get("poached", {}).get("ending", "")) == "left", "poached: it resolves 'left': %s" % str(st["done"].get("poached", {})))
	_check(st["active"].is_empty(), "poached: every arc ends at the club he leaves: %s" % str(st["active"].keys()))
	var coached_before := (st["coach"]["coached"] as Dictionary).size()
	# Save and load with the move pending: it is still made.
	_check(GameState.save_career() and GameState.load_career(), "poached: saves and loads with the move pending")
	st = GameState.coach_arcs
	_check(str(st["move"].get("to", "")) == suitor, "poached: the pending move survives a reload")
	their_coach = _senior_at(suitor)
	_check(GameState.start_next_season(), "poached: the season rolls on")
	st = GameState.coach_arcs
	_check(GameState.my_club == suitor, "poached: he coaches %s now, got %s" % [suitor, GameState.my_club])
	_check(GameState.my_list == GameState.season.lists[suitor], "poached: his list is the new club's")
	_check(str(their_coach.get("club", "")) == "FRE" and str(their_coach.get("job", "")) == "SC", "poached: %s's coach takes the Fremantle job" % suitor)
	_check(_senior_at(suitor).is_empty(), "poached: the club he joins has no AI senior coach (he is it)")
	var clubs: Array = st["coach"]["clubs"]
	_check(clubs.size() == 2 and str(clubs[0]["code"]) == "FRE" and int(clubs[0]["to"]) == GameState.season_year - 1 \
			and str(clubs[1]["code"]) == suitor, "poached: the career history has both clubs: %s" % JSON.stringify(clubs))
	_check(int(st["coach"]["seasons"]) == 1, "poached: the Fremantle season is still on his record: %s" % str(st["coach"]))
	_check((st["coach"]["coached"] as Dictionary).size() > coached_before, "poached: the players he coached at both clubs are remembered")
	_check(str(clubs[0].get("chairman", "")) != "" and str(st["people"].get("chairman", "")) != str(clubs[0]["chairman"]),
			"poached: the old chairman is remembered and the new club has its own")
	var before := JSON.stringify(st)
	_check(GameState.save_career() and GameState.load_career(), "poached: saves and loads at the new club")
	_check(JSON.stringify(GameState.coach_arcs) == before and GameState.my_club == suitor, "poached: the career history comes back as it was")


## Arc 2 (and arc 11's take-over): sacked at a season's close, he takes a job
## at a bottom club, his assistant takes the job he lost, and the way back
## starts at the new club, remembering the old one.
func _test_sacked_way_back() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = SUITE_SEED + 5
	var st: Dictionary = GameState.coach_arcs
	var old := str(GameState.my_club)
	for i in range(3):
		_week(rng)
	# An assistant with a name, after the job: arc 11 runs as the board sinks.
	var sa_id := _my_assistant()
	_check(sa_id != "", "sacked: the club has a senior assistant")
	if sa_id == "":
		return
	var sa: Dictionary = GameState.coaches[sa_id]
	sa["rep"] = 80
	GameState.board["confidence"] = 30
	var adef := CoachArcs.by_id(CoachArcs.all(), "assistant")
	st["active"].erase("assistant")
	var ahit := ClubMoves.assistant_trigger(GameState, st, adef["trigger"], ClubStories.context(GameState), false)
	_check(str(ahit.get("mem", {}).get("assistant_id", "")) == sa_id, "assistant: the trigger names him: %s" % str(ahit))
	st["done"].erase("assistant")
	var arec := CoachArcs.start(st, adef, GameState.season_year, GameState.story_week(), "", ahit.get("mem", {}))
	CoachArcs.answer(adef, arec, "arc_assist_lunch", "confront", GameState.story_week(), GameState.season_year)
	CoachArcs.answer(adef, arec, "arc_assist_offer", "block", GameState.story_week() + 4, GameState.season_year)
	# A goal no side meets: a premiership (+30) cannot save a missed one (0 - 25 + 30 < 30).
	GameState.board["goal"] = {"key": "wins99", "text": "Win 99 games", "wins": 99}
	# A rival's approach for him at the end of the home-and-away season would
	# take him first (he is the man the arc is about): leave it out.
	var guard := 0
	while not GameState.season.is_regular_done() and guard < 40:
		guard += 1
		GameState.board["confidence"] = 0
		GameState.board["warned"] = true
		_week(rng)
	GameState.coach_approaches = GameState.coach_approaches.filter(func(a): return str(a.get("cid", "")) != sa_id)
	_play_out(rng, 0)
	st = GameState.coach_arcs
	_check(not GameState.is_sacked(), "sacked: the career goes on (no sacked card)")
	var to := str(st["move"].get("to", ""))
	_check(str(st["move"].get("why", "")) == "sacked" and to != "" and to != old, "sacked: a job at another club: %s" % str(st["move"]))
	_check(int(st["coach"]["sackings"]) == 1, "sacked: the sacking is on his record")
	_check(str(st["done"].get("assistant", {}).get("ending", "")) == "took_job", "assistant: resolves 'took_job': %s" % str(st["done"].get("assistant", {})))
	_check(GameState.start_next_season(), "sacked: the season rolls on")
	st = GameState.coach_arcs
	sa = GameState.coaches.get(sa_id, {})
	_check(GameState.my_club == to, "sacked: he coaches %s now" % to)
	_check(str(sa.get("club", "")) == old and str(sa.get("job", "")) == "SC", "assistant: he has the job the coach lost: %s" % str([sa.get("club"), sa.get("job")]))
	var wb: Dictionary = st["active"].get("way_back", {})
	_check(not wb.is_empty(), "way back: it starts at the new club: %s" % str(st["active"].keys()))
	_check(str(wb.get("mem", {}).get("old_club", "")) == GameDB.club_name(old) and str(wb.get("mem", {}).get("former", "")) != "",
			"way back: it remembers the club and a player he left: %s" % str(wb.get("mem", {})))
	_check((st["coach"]["clubs"] as Array).size() == 3 and str(st["coach"]["clubs"][1].get("why_left", "")) == "sacked",
			"sacked: three clubs on the record, the second left by the sack: %s" % JSON.stringify(st["coach"]["clubs"]))
	var seen := {}
	for i in range(8):
		for c in GameState.week_events:
			if str(c.get("coach_arc", "")) == "way_back":
				seen[str(c.get("tid", ""))] = true
		_week(rng)
	_check(seen.has("arc_back_why"), "way back: the first press call is dealt: %s" % str(seen.keys()))
	var before := JSON.stringify(GameState.coach_arcs)
	_check(GameState.save_career() and GameState.load_career(), "way back: saves and loads")
	_check(JSON.stringify(GameState.coach_arcs) == before, "way back: comes back as it was")
	_play_out(rng)
	_check(GameState.start_next_season(), "way back: the season rolls on")
	st = GameState.coach_arcs
	var end := str(st["done"].get("way_back", {}).get("ending", ""))
	_check(end in ["rebuilt", "settled", "sacked_again"], "way back: it resolves: %s" % str(st["done"].get("way_back", {})))


## Arc 7: a club he coached before on this week's fixture starts the reunion,
## remembering the club, its chairman and a player; the result is recorded.
func _test_reunion() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = SUITE_SEED + 6
	for i in range(3):
		_week(rng)
	var st: Dictionary = GameState.coach_arcs
	var old := str(st["coach"]["clubs"][0]["code"])
	var ctx := ClubStories.context(GameState)
	var club: Dictionary = (ctx["club"] as Dictionary).duplicate()
	club["opp"] = GameDB.club_name(old)
	st["active"].erase("way_back")
	st["active"].erase("reunion")
	# An earlier test's career may have met this club already; start fresh.
	for h in st["coach"]["clubs"]:
		(h as Dictionary).erase("reunion")
	var hit := ClubMoves.reunion_trigger(GameState, st, club, ctx, false)
	_check(str(hit.get("mem", {}).get("old_code", "")) == old and str(hit.get("mem", {}).get("old_chairman", "")) != "" \
			and str(hit.get("mem", {}).get("former", "")) != "", "reunion: it remembers the old club, its chairman and a player: %s" % str(hit))
	club["opp"] = GameDB.club_name(GameState.my_club)
	_check(ClubMoves.reunion_trigger(GameState, st, club, ctx, false).is_empty(), "reunion: not against any other club")
	if hit.is_empty():
		return
	var def := CoachArcs.by_id(CoachArcs.all(), "reunion")
	var rec := CoachArcs.start(st, def, GameState.season_year, GameState.story_week(), "", hit["mem"])
	var line := StoryEngine.fill(str(def["beats"][0]["text"][-1]), ClubArcs._facts(GameState, st, rec, club))
	_check(line.find("{") < 0 and line.find(GameDB.club_name(old)) >= 0, "reunion: the grudge text names the old club: %s" % line)
	var last: Array = GameState.season.results[-1]
	last.append({"home": GameState.my_club, "away": old, "score": [90, 60]})
	ClubMoves.record_reunion(GameState, st)
	last.pop_back()
	_check((rec["flags"] as Dictionary).has("won"), "reunion: the win over the old club is recorded")
	var drawn := {"flags": {}}
	var st_draw := {"active": {"reunion": {"flags": drawn["flags"], "mem": hit["mem"]}}}
	last.append({"home": GameState.my_club, "away": old, "score": [70, 70]})
	ClubMoves.record_reunion(GameState, st_draw)
	last.pop_back()
	_check((drawn["flags"] as Dictionary).has("drew") and not (drawn["flags"] as Dictionary).has("lost")
			and not (drawn["flags"] as Dictionary).has("won"), "reunion: a draw is neither a win nor a loss: %s" % str(drawn["flags"]))
	CoachArcs.answer(def, rec, "arc_reunion_grudge", "bite", GameState.story_week(), GameState.season_year)
	CoachArcs.answer(def, rec, "arc_reunion_handshake", "gracious", GameState.story_week() + 1, GameState.season_year)
	_check(int(rec["beat"]) == 2, "reunion: both beats played")
	_check(CoachArcs.closing(def, rec, {}, GameState.season_year + 1) == "remembered", "reunion: a win resolves 'remembered'")
	rec["flags"].erase("won")
	_check(CoachArcs.closing(def, rec, {}, GameState.season_year + 1) == "reconciled", "reunion: a gracious loss resolves 'reconciled'")
	rec["flags"]["drew"] = GameState.story_week()
	var draw_end := CoachArcs.closing(def, rec, {}, GameState.season_year + 1)
	var draw_line := str(def["endings"].get(draw_end, {}).get("line", ""))
	_check(draw_end == "level" and draw_line.contains("Honours shared") and not draw_line.contains("better of"),
			"reunion: a drawn reunion resolves 'level' with draw copy: %s / %s" % [draw_end, draw_line])
	rec["flags"].erase("drew")
	# The same old club comes round again only once every 10 seasons.
	ClubArcs._end(GameState, st, def, rec, "reconciled", "Season start")
	_check(not (st["active"] as Dictionary).has("reunion"), "reunion: an ended reunion is no longer active")
	var year := int(GameState.season_year)
	var hist: Dictionary = {}
	for h in st["coach"]["clubs"]:
		if str(h.get("code", "")) == old:
			hist = h
	_check(int(hist.get("reunion", 0)) == year, "reunion: the old club's last reunion is kept: %s" % str(hist))
	club["opp"] = GameDB.club_name(old)
	for back in [1, 5, 9]:
		hist["reunion"] = year - back
		_check(ClubMoves.reunion_trigger(GameState, st, club, ctx, false).is_empty(),
				"reunion: blocked %d season(s) after the last one against %s" % [back, old])
	hist["reunion"] = year - 10
	_check(not ClubMoves.reunion_trigger(GameState, st, club, ctx, false).is_empty(),
			"reunion: allowed again 10 seasons after the last one against %s" % old)
	# A flag won there: the premiership reunion on its 10-year anniversary,
	# even inside the cooldown, naming the flag year and the club.
	hist["reunion"] = year - 1
	var flag_row := {"year": year - 10, "premier": old, "my_club": old, "my_position": 1}
	GameState.honour_roll.append(flag_row)
	var anniv := ClubMoves.reunion_trigger(GameState, st, club, ctx, false)
	_check(bool(anniv.get("mem", {}).get("flag_reunion", false)) and int(anniv.get("mem", {}).get("flag_year", 0)) == year - 10,
			"reunion: a flag club gets the anniversary reunion: %s" % str(anniv))
	if not anniv.is_empty():
		var arec := CoachArcs.start(st, def, year, GameState.story_week(), "", anniv["mem"])
		var sline := ClubArcs._start_line(def, ClubArcs._facts(GameState, st, arec, club))
		_check(sline.find(str(year - 10)) >= 0 and sline.find(GameDB.club_name(old)) >= 0 and sline.find("premiership") >= 0,
				"reunion: the anniversary names the flag year and the team: %s" % sline)
		ClubArcs._end(GameState, st, def, arec, "enjoyed", "Season start")
		_check(int(hist.get("anniv", 0)) == year, "reunion: the anniversary is marked once told")
		_check(ClubMoves.reunion_trigger(GameState, st, club, ctx, false).is_empty(), "reunion: one anniversary reunion a year")
	GameState.honour_roll.erase(flag_row)
	hist.erase("anniv")
	hist["reunion"] = year


## The drought counts seasons at the club he coaches now, not his whole career.
func _test_drought_counts_this_club() -> void:
	var st := CoachArcs.new_state()
	st["coach"].merge({"seasons": 9, "seen": 2035, "start": 2027, "last_flag": 0, "club": "RIC",
			"clubs": [{"code": "FRE", "from": 2027, "to": 2032}, {"code": "RIC", "from": 2033, "to": 0}]}, true)
	_check(ClubArcs._dry(st) == 3, "drought: 3 seasons at Richmond after six at Fremantle, not 9: %d" % ClubArcs._dry(st))
	st["coach"]["last_flag"] = 2034
	_check(ClubArcs._dry(st) == 1, "drought: counted from a flag won at this club: %d" % ClubArcs._dry(st))
	st["coach"]["last_flag"] = 2030
	_check(ClubArcs._dry(st) == 3, "drought: a flag at the old club does not shorten it here: %d" % ClubArcs._dry(st))
	st["coach"].merge({"seen": 2031, "club": "FRE", "clubs": [{"code": "FRE", "from": 2027, "to": 0}], "last_flag": 0}, true)
	_check(ClubArcs._dry(st) == 5, "drought: one club, every season counted: %d" % ClubArcs._dry(st))
	# One drought runs until a flag (or a club change), not one a season.
	var def := CoachArcs.by_id(CoachArcs.all(), "drought")
	var rec := CoachArcs.start(st, def, 2032, 0, "", {})
	rec["beat"] = (def["beats"] as Array).size()
	_check(CoachArcs.closing(def, rec, {"premiers": false}, 2035) == "", "drought: no flag, it runs on into a fourth season")
	_check(CoachArcs.closing(def, rec, {"premiers": true}, 2035) == "broken", "drought: a flag ends it")


## Arc 11, the other way: backed to go, the assistant takes a rival's senior
## job at the season's close and his own job opens.
func _test_assistant_leaves() -> void:
	var st: Dictionary = GameState.coach_arcs
	var sa_id := _my_assistant()
	_check(sa_id != "", "assistant: the new club has a senior assistant")
	if sa_id == "":
		return
	var sa: Dictionary = GameState.coaches[sa_id]
	var to := ""
	for code in GameState.season.ladder:
		if str(code) != GameState.my_club and not _senior_at(str(code)).is_empty():
			to = str(code)
			break
	var def := CoachArcs.by_id(CoachArcs.all(), "assistant")
	st["active"].erase("assistant")
	var rec := CoachArcs.start(st, def, GameState.season_year, 1, "", {"assistant": GameDB.player_display_name(sa), "assistant_id": sa_id,
			"assistant_to": GameDB.club_name(to), "assistant_code": to})
	CoachArcs.answer(def, rec, "arc_assist_lunch", "delegate", 1, GameState.season_year)
	CoachArcs.answer(def, rec, "arc_assist_offer", "back", 5, GameState.season_year)
	ClubMoves._assistant_leaves(GameState, st)
	_check(str(sa.get("club", "")) == to and str(sa.get("job", "")) == "SC", "assistant: backed, he coaches %s" % to)
	_check(GameState._vacancy_open(str(sa.get("job", "SA"))) or GameState._vacancy_open("SA"), "assistant: his job is open")
	_check(CoachArcs.closing(def, rec, {"sacked": false}, GameState.season_year + 1) == "left_friend", "assistant: resolves 'left_friend'")
	st["active"].erase("assistant")


## The match-story facts (plan step 1b): validate() knows them, and an arc
## whose condition is hero_count >= 3 starts only after the third hero match.
func _test_hero_count_trigger() -> void:
	for f in ["hero_streak", "hero_count", "last_hero_mine", "hero_is_arc_player", "close_losses", "turned_against"]:
		_check(CoachArcs.ARC_FACTS.has(f), "the arcs know the fact %s" % f)
	var probe := [{"id": "probe", "kind": "club", "trigger": {"kind": "media"}, "beats": [CoachArcs.by_id(CoachArcs.all(), "media_darling")["beats"][0].duplicate(true)],
			"endings": {"done": {"line": "Done."}}, "close": [{"when": {}, "ending": "done"}]}]
	probe[0]["beats"][0]["id"] = "probe_beat"
	probe[0]["beats"][0]["when"] = {"hero_count_min": 3, "hero_streak_min": 1, "close_losses_max": 9}
	var errs := CoachArcs.validate(probe)
	_check(errs.is_empty(), "validate() accepts the new facts: %s" % str(errs))
	_fresh()
	# A kid of 19 on the list who is not a backed high-potential pick.
	var young: Dictionary = GameState.my_list[GameState.my_list.size() - 1]
	young["age"] = 19.0
	young["potential"] = 60
	var ctx := ClubStories.context(GameState)
	var kid := {}
	for p in ctx["players"]:
		if str(p["id"]) == str(young["id"]):
			kid = p
	_check(not kid.is_empty(), "the list has a player of 20 or under")
	var def := CoachArcs.by_id(CoachArcs.all(), "protege")
	var st: Dictionary = ClubArcs._st(GameState)
	GameState.match_stories = []
	for n in range(1, 4):
		GameState.match_stories.append({"year": GameState.season_year, "club": GameState.my_club, "opp": "WCE", "margin": 8,
				"hero_id": str(kid.get("id", "")), "hero_name": "Kid", "hero_club": GameState.my_club})
		var hit := ClubArcs.trigger(GameState, st, def, ClubStories.context(GameState), false)
		var named := str(hit.get("who", "")) == str(kid.get("id", ""))
		if n < 3:
			_check(not named, "after %d hero match(es) the protege arc does not start for him" % n)
		else:
			_check(named, "after the third hero match the protege arc starts for him: %s" % str(hit))
	var rec := {"who": str(kid.get("id", "")), "start": GameState.season_year}
	var f := ClubArcs._facts(GameState, st, rec, ctx["club"])
	_check(int(f["hero_count"]) == 3 and int(f["hero_streak"]) == 3 and bool(f["hero_is_arc_player"]),
			"the arc's facts read the match stories (%s)" % str([f["hero_count"], f["hero_streak"], f["hero_is_arc_player"]]))
	GameState.match_stories = []
