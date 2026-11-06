extends SceneTree
## godot --headless --path . --script tests/run_career_highs_tests.gd
## Career highs (row 121, ruling T5.r152, CareerHighs.gd): a new best for one of
## yours is said once in the week's news and once in the match feed, from his
## own recorded games; a quiet game, an equal best, a debut, a career on
## imported totals and another club's player say nothing; a round run twice
## says nothing twice; the record survives a save.

const Ran := preload("res://tests/functions_ran.gd")
const SUITE_SEED := 2121
var _state: Node
var _CH: GDScript
var _MN: GDScript
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _run() -> void:
	await process_frame
	seed(SUITE_SEED)
	_state = root.get_node("GameState")
	_CH = load("res://scripts/sim/CareerHighs.gd")
	_MN = load("res://scripts/ui/match/MatchNotes.gd")
	_state.autosave_enabled = false
	_state.save_path = "user://test_career_highs.save"
	_state.settings_path = "user://test_career_highs.cfg"
	_state.delete_saved_career()
	await _t("_test_rules")
	await _t("_test_wording")
	await _t("_test_round_news")
	await _t("_test_save_keeps_record")
	await _t("_test_feed_lines")
	await _t("_test_match_screen")
	await _t("_test_played_week")
	print(Ran.line("Career highs", self))
	for f in _failures:
		print("  FAIL: " + f)
	_state.delete_saved_career()
	quit(1 if not _failures.is_empty() else 0)


func _fresh() -> void:
	_state.reset()
	_state.start_season("COL", root.get_node("GameDB").club_list("COL"))


func _settle() -> void:
	for i in range(6):
		await process_frame


## A record that has seen every one of his `games` games, with these bests.
func _record(p: Dictionary, games: int, bests: Dictionary) -> void:
	var rec := {"full": true, "games": games, "last": ""}
	for stat in bests:
		rec[stat] = {"n": int(bests[stat]), "year": 2026, "label": "Round 1"}
	p["highs"] = rec


## The pure rules: baseline, floor, equal, minimum games, imported careers,
## once per match key, and a gap in the record.
func _test_rules() -> void:
	var line := {"goals": 4, "disposals": 26, "marks": 8, "tackles": 7}
	# A debut sets the baseline and says nothing, however big.
	var kid := {}
	_check(_CH.update(kid, line, 0, true, 2026, "Round 1", "k1").is_empty(), "A debut says nothing")
	_check(_CH.complete(kid) and _CH.best(kid, "disposals") == 26, "...but sets his baseline")
	# Before MIN_GAMES nothing is said either.
	var n := 1
	while n < _CH.MIN_GAMES:
		var big := {"disposals": 26 + n}
		_check(_CH.update(kid, big, n, true, 2026, "Round %d" % (n + 1), "k%d" % (n + 1)).is_empty(),
				"Game %d is too early to say a high" % (n + 1))
		n += 1
	_check(_CH.best(kid, "disposals") == 26 + n - 1, "...his best still moves")
	# A career high once he has his games.
	var p := {}
	_record(p, 6, {"goals": 2, "disposals": 18, "marks": 5, "tackles": 4})
	var got: Array = _CH.update(p, {"disposals": 25, "goals": 1}, 6, true, 2026, "Round 7", "m7")
	_check(got == [["disposals", 25]], "25 disposals past a best of 18 is a career high (%s)" % str(got))
	_check(_CH.best(p, "disposals") == 25 and int(p["highs"]["games"]) == 7, "The best and games move on")
	_check(_CH.update(p, {"disposals": 25}, 6, true, 2026, "Round 7", "m7").is_empty(),
			"The same match recorded again says nothing")
	_check(int(p["highs"]["games"]) == 7, "...and counts nothing")
	_check(_CH.update(p, {"disposals": 25}, 7, true, 2026, "Round 8", "m8").is_empty(),
			"Equalling his best is not a career high")
	_check(_CH.update(p, {"marks": 6, "tackles": 5}, 8, true, 2026, "Round 9", "m9").is_empty(),
			"A new best under the floor stays quiet")
	_check(_CH.best(p, "marks") == 6, "...though it is kept")
	var two: Array = _CH.update(p, {"goals": 3, "tackles": 12}, 9, true, 2026, "Round 10", "m10")
	_check(two.size() == 2 and str(two[0][0]) == "tackles", "Two at once, the bigger step first (%s)" % str(two))
	# A veteran on imported totals: tracked, never said.
	var vet := {}
	_check(_CH.update(vet, line, 120, true, 2026, "Round 1", "v1").is_empty(), "A veteran's first recorded game says nothing")
	_check(not _CH.complete(vet), "...his record is not his career")
	_check(_CH.update(vet, {"disposals": 40}, 121, true, 2026, "Round 2", "v2").is_empty(),
			"...and a big game later says nothing either")
	# A career partly unknown never counts in full.
	var unknown := {}
	_CH.update(unknown, line, 0, false, 2026, "Round 1", "u1")
	_check(not _CH.complete(unknown), "A career not on record in full is never full")
	# Games the record missed clear it.
	var gap := {}
	_record(gap, 8, {"disposals": 18})
	_check(_CH.update(gap, {"disposals": 30}, 10, true, 2026, "Round 11", "g11").is_empty(),
			"Games the record missed: no career high said")
	_check(not _CH.complete(gap), "...and the record is no longer full")


func _test_wording() -> void:
	_check(_CH.feed_line("Calder", "goals", 4) == "Career-high four goals for Calder.", "Feed, goals")
	_check(_CH.feed_line("Calder", "disposals", 34, true) == "Career-high 34 disposals for Calder, and counting.",
			"Feed, at a break")
	var db = root.get_node("GameDB")
	var carlton: String = db.club_name("CAR")
	_check(_CH.news_line("Calder", "disposals", 34, "CAR", "Round 7")
			== "Calder had a career-high 34 disposals against %s in Round 7." % carlton, "News, disposals")
	_check(_CH.news_line("Calder", "goals", 5, "CAR", "Grand Final")
			== "Calder kicked a career-high five goals against %s in the Grand Final." % carlton, "News, goals in a final")
	_check(_CH.news_line("Calder", "marks", 9, "CAR", "Semi Final 1")
			== "Calder took a career-high nine marks against %s in a Semi Final." % carlton, "News, marks")
	_check(_CH.news_line("Calder", "tackles", 8, "CAR", "Round 2")
			== "Calder laid a career-high eight tackles against %s in Round 2." % carlton, "News, tackles")


## Sets his tally so that, with this match counted, he has played `games`.
func _set_games(p: Dictionary, games: int) -> void:
	var id := str(p["id"])
	var t: Dictionary = _state.season_tally.get(id, {"club": _state.my_club, "games": 0, "goals": 0,
			"goals_ha": 0, "disposals": 0, "distance_run": 0.0, "influence": 0.0, "votes": 0, "bf": 0,
			"polled": 0, "coaches": 0})
	_state.season_tally[id] = t
	t["games"] = 0
	t["games"] = games - _state.games_played(p)


func _highs_news() -> Array:
	var out := []
	for item in _state.news:
		if str(item.get("kind", "")) == "milestone" and str(item.get("text", "")).contains("career-high"):
			out.append(str(item["text"]))
	return out


## The week's news: yours only, once, nothing for a quiet game.
func _test_round_news() -> void:
	_fresh()
	var mine: Dictionary = {}
	for p in _state.my_list:
		if Career.complete(p):
			mine = p
			break
	_check(not mine.is_empty(), "(setup) a player of yours on a full career")
	var opp_code := "GEE"
	var theirs: Dictionary = _state.season.lists[opp_code][0]
	for p in [mine, theirs]:
		p["career"] = {"games": 6, "goals": 0, "stints": [], "through": _state.season_year - 1, "unknown": []}
		_state.season_tally.erase(str(p["id"]))
		_record(p, 6, {"goals": 2, "disposals": 18, "marks": 5, "tackles": 4})
		_set_games(p, 7)
	var res := {"home": _state.my_club, "away": opp_code, "label": "Round 7", "score": [90, 60],
			"roster": [[{"id": str(mine["id"])}], [{"id": str(theirs["id"])}]],
			"players": {str(mine["id"]): {"disposals": 25, "goals": 1}, str(theirs["id"]): {"disposals": 30}}}
	var before := _highs_news().size()
	_state._note_career_highs([res])
	var said := _highs_news()
	var who: String = root.get_node("GameDB").player_display_name(mine)
	var want := "%s had a career-high 25 disposals against %s in Round 7." % [who, root.get_node("GameDB").club_name(opp_code)]
	_check(said.size() == before + 1 and said[0] == want, "One news item, his (%s)" % str(said.slice(0, 2)))
	_check(_CH.best(theirs, "disposals") == 30, "Their player's best is kept")
	_state._note_career_highs([res])
	_check(_highs_news().size() == before + 1, "The same round run again says nothing more")
	# A quiet game.
	_set_games(mine, 8)
	var quiet := res.duplicate(true)
	quiet["label"] = "Round 8"
	quiet["players"] = {str(mine["id"]): {"disposals": 14, "marks": 3}}
	quiet["roster"] = [[{"id": str(mine["id"])}], []]
	_state._note_career_highs([quiet])
	_check(_highs_news().size() == before + 1, "A quiet game says nothing")


## The record is kept on the player, so a save keeps it.
func _test_save_keeps_record() -> void:
	_fresh()
	var p: Dictionary = _state.my_list[0]
	_record(p, 9, {"disposals": 27})
	var id := str(p["id"])
	_check(_state.save_career(), "(setup) saved")
	_check(_state.load_career(), "Loads")
	var back: Dictionary = _state.list_player(id)
	_check(_CH.complete(back) and _CH.best(back, "disposals") == 27,
			"His career high survives a save (%s)" % str(back.get("highs", {})))
	# An old save: no record on anyone. A player who has played starts silent.
	var other: Dictionary = _state.my_list[1]
	other.erase("highs")
	var g: int = maxi(1, _state.games_played(other))
	_CH.update(other, {"disposals": 40}, g, Career.complete(other), _state.season_year, "Round 1", "x")
	_check(not _CH.complete(other), "A player from an old save who has played is tracked, never said")


## _MN.career_high_lines: goals at the goal, the rest at the break, once
## each, only for the candidates given, capped a quarter.
func _test_feed_lines() -> void:
	var mem := {"career_high": {"a": {"goals": 3, "disposals": 18, "marks": 5, "tackles": 4}}}
	var goal := {"kind": "goal", "q": 2, "min": 10, "side": 0, "player_id": "a", "name": "Ari Bramble"}
	var said := []
	for i in range(5):
		said.append_array(_MN.career_high_lines(mem, goal, {}))
	_check(said == ["Career-high four goals for Ari Bramble."], "His fourth goal passes his best of three, said once (%s)" % str(said))
	var them := goal.duplicate()
	them["player_id"] = "b"
	_check(_MN.career_high_lines(mem, them, {}).is_empty(), "Nothing for a player not given")
	# A real player of the save, so the feed can name him.
	_fresh()
	var aid := str(_state.my_list[0]["id"])
	var who: String = _MN._pname(aid)
	_check(who != "", "(setup) a named player")
	mem["career_high"][aid] = {"disposals": 18, "marks": 5, "tackles": 4}
	var res := {"quarter_teams": [
		{"quarter": 1, "players": {aid: {"disposals": 9.0, "marks": 2.0}}},
		{"quarter": 2, "players": {aid: {"disposals": 21.0, "marks": 4.0, "tackles": 7.0}}},
		{"quarter": 3, "players": {aid: {"disposals": 26.0, "marks": 6.0, "tackles": 7.0}}}]}
	var qev := func(q: int) -> Dictionary:
		return {"kind": "quarter", "q": q, "min": 30, "side": -1}
	_check(_MN.career_high_lines(mem, qev.call(1), res).is_empty(), "Under his best at quarter time: nothing")
	var q2: Array = _MN.career_high_lines(mem, qev.call(2), res)
	_check(q2 == ["Career-high 21 disposals for %s, and counting." % who], "One line a player at a break (%s)" % str(q2))
	var q3: Array = _MN.career_high_lines(mem, qev.call(3), res)
	_check(q3 == ["Career-high seven tackles for %s, and counting." % who], "The other high waits for the next break (%s)" % str(q3))
	_check(_MN.career_high_lines(mem, qev.call(3), res).is_empty(), "Each stat once a match")
	_check(_MN.career_high_lines({"career_high": {}}, qev.call(3), res).is_empty(), "No candidates, no lines")
	# The cap: three players over at one break, two lines.
	var many := {"career_high": {}}
	var snap := {}
	for i in range(3):
		var id := str(_state.my_list[i + 1]["id"])
		many["career_high"][id] = {"disposals": 18}
		snap[id] = {"disposals": 22.0}
	var capped: Array = _MN.career_high_lines(many, qev.call(4), {"quarter_teams": [{"quarter": 4, "players": snap}]})
	_check(capped.size() == _MN.MAX_HIGH_LINES, "At most %d a quarter (%d)" % [_MN.MAX_HIGH_LINES, capped.size()])
	_check(not str(capped[0]).contains("and counting"), "At the final siren the count is final")


## The match screen is told whose career high it could say, only yours, and the
## feed says it once.
func _test_match_screen() -> void:
	_fresh()
	root.size = Vector2i(420, 860)
	_check(_state.prepare_interactive_match(), "A live match is prepared")
	var sim = _state.pending_sim
	var me := 0 if str(_state.pending_match["home"]) == _state.my_club else 1
	var row: Dictionary = sim.squads[me].ground[0]
	var pid := str(row["id"])
	var p: Dictionary = _state.list_player(pid)
	p["career"] = {"games": 8, "goals": 20, "stints": [], "through": _state.season_year - 1, "unknown": []}
	_state.season_tally.erase(pid)
	_record(p, 8, {"goals": 2, "disposals": 18, "marks": 5, "tackles": 4})
	var cands: Dictionary = _state.career_high_candidates()
	_check(cands.has(pid), "He is a candidate")
	for r in sim.squads[1 - me].ground:
		_check(not cands.has(str(r["id"])), "No player of theirs is a candidate")
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await _settle()
	_check((m.get("_duel_mem").get("career_high", {}) as Dictionary).has(pid), "The screen is told")
	var feed: Node = m.find_child("Feed", true, false)
	var lines := func() -> Array:
		var out := []
		for c in feed.get_children():
			if str(c.get_meta("feed_kind", "")) == "CareerHighLine":
				out.append(str(c.text))
		return out
	var goal := {"kind": "goal", "q": 1, "min": 3, "side": me, "player_id": pid, "name": "Test Kicker", "score": [6, 0]}
	for i in range(4):
		m.call("_career_high_feed", goal)
	var rows: Array = lines.call()
	_check(rows.size() == 1 and str(rows[0]).ends_with("Career-high three goals for Test Kicker."),
			"His third goal reaches the feed, once (%s)" % str(rows))
	m.queue_free()
	await _settle()


## A played week records every player who took the field, at every club, and
## a first-season week says no career high (nobody has his games yet).
func _test_played_week() -> void:
	_fresh()
	var before := _highs_news().size()
	_state.advance()
	var res: Dictionary = _state.my_last_result()
	_check(not res.is_empty(), "(setup) the week was played")
	var seen := 0
	var missing := 0
	for side in (res.get("roster", []) as Array):
		for r in side:
			var p: Dictionary = _state._find_player(str(r["id"]))
			if p.is_empty():
				continue
			if _CH.get_record(p).is_empty():
				missing += 1
			else:
				seen += 1
	_check(seen > 0 and missing == 0, "Everyone who played has a record (%d, %d missing)" % [seen, missing])
	_check(_highs_news().size() == before, "Nothing said in the first week")
