extends RefCounted
## Run by tests/run_career_tale_tests.gd (suite "career_tale").
## A player's career story (CareerTale.gd; director 2026-11-10): pinned stories
## for hand-built careers, nothing at all for a thin one, every number traced to
## the record for every player in the premade histories, the same story every
## time and across a save and reload, and the sheet and Brownlow night show it.

var _tree: SceneTree
var checks := 0
var failures: Array[String] = []

## Seeded: every random draw (premade histories, the draft) runs from SUITE_SEED.
const SUITE_SEED := 2027
const NAMES := {"FRE": "Fremantle", "GEE": "Geelong", "MEL": "Melbourne", "STK": "St Kilda"}


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _settle(n := 6) -> void:
	for i in range(n):
		await _tree.process_frame


func run(tree: SceneTree) -> void:
	_tree = tree
	await _tree.process_frame
	GameState.replay_seed = SUITE_SEED
	GameState.career_seed = SUITE_SEED
	GameState.autosave_enabled = false
	GameState.save_path = "user://test_career_tale.save"
	GameState.settings_path = "user://test_career_tale.cfg"
	GameState.delete_saved_career()
	_t("_test_bank_is_sound")
	_t("_test_validator_rejects")
	_t("_test_golden")
	_t("_test_thin_is_silent")
	_t("_test_whose_pick")
	_t("_test_payoff_and_failure_apart")
	_t("_test_writes_nothing")
	await _t("_test_premade_histories")
	_tree.root.size = Vector2i(390, 844)
	await _settle()
	await _t("_test_sheet_shows_it_once")
	GameState.delete_saved_career()
	print(Ran.line("Career tale", self))
	for f in failures:
		print("  FAIL: " + f)


## A hand-built context: you coach `club` from `from` on, `year` is now.
func _ctx(name: String, coached: Dictionary, year: int, club: String, roll := [], log := []) -> Dictionary:
	return {"name": name, "honour_roll": roll, "milestones": {"log": log}, "coached": coached,
			"year": year, "club": club, "club_name": func(code): return str(NAMES.get(code, code)), "skip": {}}


func _seasons(code: String, from: int, to: int) -> Dictionary:
	var out := {}
	for y in range(from, to + 1):
		out[y] = code
	return out


func _career(stints: Array) -> Dictionary:
	var g := 0
	for s in stints:
		g += int(s[3])
	return {"games": g, "goals": 0, "stints": stints, "through": 2032, "unknown": []}


func _bank_is_sound_angles() -> Dictionary:
	return CareerTale.bank()


func _test_bank_is_sound() -> void:
	var angles := _bank_is_sound_angles()
	_check(not angles.is_empty(), "The phrase bank loads")
	var problems := CareerTale.validate(angles)
	_check(problems.is_empty(), "The phrase bank is sound: %s" % [problems])
	for a in CareerTale.WEIGHT:
		_check(angles.has(a), "Every angle has phrases: %s" % a)


func _test_validator_rejects() -> void:
	var bad := {"x": {"slots": ["year"], "coach": ["In {year} he won {votes}."]},
			"y": {"slots": ["year"], "coach": ["In {year {."]}, "z": {"slots": [], "coach": []}}
	var problems := CareerTale.validate(bad)
	_check(problems.size() == 3, "An undeclared slot, a stray brace and an empty angle are all caught: %s" % [problems])


## The cases from the build brief, each with its exact story.
func _cases() -> Array:
	var out := []
	# The defining moment: a late pick of yours wins the Brownlow.
	out.append(["late pick, Brownlow", {"id": "T_A", "drafted_year": 2027, "drafted_type": "national",
			"drafted_pick": 38, "drafted_club": "MEL", "club": "MEL",
			"firsts": {"debut": {"year": 2028, "label": "Round 3"}},
			"career": _career([["MEL", 2028, 2032, 96, 40]])},
			_ctx("Ollie Byrne", _seasons("MEL", 2028, 2032), 2033, "MEL",
				[{"year": 2031, "premier": "MEL", "my_club": "MEL"},
				{"year": 2032, "premier": "GEE", "my_club": "MEL", "brownlow": [{"id": "T_A", "votes": 31, "club": "MEL"}]}],
				[{"who": "player", "id": "T_A", "kind": "games", "value": 50, "year": 2030, "label": "Round 12"}]),
			"Ollie came to us at pick 38 in the 2027 national draft. He debuted for us in Round 3, 2028. He played his 50th game in Round 12, 2030. He was with us for the 2031 premiership. From pick 38, he won the 2032 Brownlow with 31 votes."])
	# The same composer, told plainly: an early pick who left with 14 games.
	out.append(["early pick fell short", {"id": "T_B", "drafted_year": 2028, "drafted_type": "national",
			"drafted_pick": 6, "drafted_club": "FRE", "club": "STK",
			"backed": [{"year": 2029, "round": 4, "games": 3, "played": 1, "state": "broken"}],
			"career": _career([["FRE", 2029, 2031, 14, 3], ["STK", 2032, 2032, 5, 0]])},
			_ctx("Sam Kerr", _seasons("FRE", 2029, 2031), 2032, "FRE"),
			"We took Sam at pick 6 in the 2028 national draft. You promised him 3 games in a row in 2029, then left him out after 1 game. He played 14 games for us and left after 2031."])
	# A real player, drafted before the game by another club; no class rank used.
	out.append(["real player elsewhere", {"id": "T_C", "drafted_year": 2019, "drafted_type": "national",
			"drafted_pick": 12, "drafted_club": "GEE", "club": "GEE", "draft_rank": 30,
			"career": _career([["GEE", 2020, 2027, 150, 200]])},
			_ctx("Jack Doyle", _seasons("FRE", 2027, 2029), 2030, "FRE",
				[{"year": 2026, "premier": "GEE", "my_club": "", "coleman": [{"id": "T_C"}]},
				{"year": 2027, "premier": "STK", "my_club": "FRE", "coleman": [{"id": "T_C"}]}]),
			"Geelong took Jack at pick 12 in the 2019 national draft. He won the Coleman Medal in 2026 and 2027. He was at Geelong for the 2026 premiership."])
	# A pre-listed player (no pick, no draft kind): no draft line, his milestone alone.
	out.append(["no pick", {"id": "T_D", "drafted_year": 2027, "drafted_type": "", "drafted_club": "FRE", "club": "FRE",
			"career": _career([["FRE", 2028, 2033, 100, 20]])},
			_ctx("Leo Hart", _seasons("FRE", 2028, 2033), 2034, "FRE", [],
				[{"who": "player", "id": "T_D", "kind": "games", "value": 100, "year": 2033, "label": "Round 9"}]),
			"His 100th game came in Round 9, 2033."])
	# Two Brownlows from an early pick, and a kept promise.
	out.append(["two Brownlows", {"id": "T_E", "drafted_year": 2027, "drafted_type": "national", "drafted_pick": 2,
			"drafted_club": "FRE", "club": "FRE",
			"backed": [{"year": 2028, "games": 3, "played": 3, "state": "done"}],
			"career": _career([["FRE", 2028, 2033, 120, 30]])},
			_ctx("Max Reid", _seasons("FRE", 2028, 2033), 2034, "FRE",
				[{"year": 2031, "premier": "GEE", "my_club": "FRE", "brownlow": [{"id": "T_E", "votes": 33}]},
				{"year": 2033, "premier": "GEE", "my_club": "FRE", "brownlow": [{"id": "T_E", "votes": 29}]}]),
			"Max came to us at pick 2 in the 2027 national draft. You promised him 3 games in a row in 2028, and he played them all. He won the Brownlow in 2031 and 2033."])
	# The rookie draft is a risk taken: his Brownlow is told from it.
	out.append(["rookie Brownlow", {"id": "T_F", "drafted_year": 2028, "drafted_type": "rookie", "drafted_club": "FRE", "club": "FRE",
			"highs": {"full": true, "disposals": {"n": 41, "year": 2032, "label": "Round 7"}, "goals": {"n": 6, "year": 2031, "label": "Round 2"}},
			"career": _career([["FRE", 2029, 2033, 90, 30]])},
			_ctx("Ned Lowe", _seasons("FRE", 2029, 2033), 2034, "FRE",
				[{"year": 2033, "premier": "GEE", "my_club": "FRE", "brownlow": [{"id": "T_F", "votes": 1}]}]),
			"Ned came to us in the 2028 rookie draft. His best day was 41 disposals in Round 7, 2032. From the rookie draft, he won the 2033 Brownlow with 1 vote."])
	return out


func _test_golden() -> void:
	for c in _cases():
		var said := CareerTale.text(CareerTale.tell(c[1], c[2]))
		_check(said == str(c[3]), "%s:\n    got  %s\n    want %s" % [c[0], said, c[3]])
	# What his "With us" lines already say (Remembered's keys) is not told twice.
	var a: Array = _cases()[0]
	var ctx: Dictionary = a[2].duplicate()
	ctx["skip"] = {"flag:2031": true, "debut": true}
	var said := CareerTale.text(CareerTale.tell(a[1], ctx))
	_check(not said.contains("premiership") and not said.contains("debuted") and said.contains("31 votes"),
			"The sheet's own lines are not repeated: %s" % said)


## A first-year rookie (the draft and a debut) and a player with nothing on
## record tell no story: nothing, never a broken sentence.
func _test_thin_is_silent() -> void:
	var rookie := {"id": "T_G", "drafted_year": 2031, "drafted_type": "rookie", "drafted_club": "FRE", "club": "FRE",
			"firsts": {"debut": {"year": 2032, "label": "Round 1"}}, "career": _career([["FRE", 2032, 2032, 4, 0]])}
	var ctx := _ctx("Al Moss", _seasons("FRE", 2027, 2031), 2032, "FRE")
	_check(CareerTale.tell(rookie, ctx).is_empty(), "A first-year rookie has no story yet")
	_check(CareerTale.tell({}, ctx).is_empty(), "No player, no story")
	_check(CareerTale.tell({"id": "T_H"}, ctx).is_empty(), "A player with nothing on record has no story")
	_check(CareerTale.tell({"id": "T_I", "drafted_pick": 4}, _ctx("", {}, 2030, "")).is_empty(),
			"A pick with no year, club or name says nothing")
	_check(CareerTale.text([]) == "", "No story is an empty passage")


## "We took him" only when you coached the club that took him for the season
## the pick was for: the mid-season draft for its own season, every other for the next.
func _test_whose_pick() -> void:
	var coached := {2030: "FRE", 2031: "GEE"}
	var mid := {"id": "T_J", "drafted_year": 2030, "drafted_type": "midseason", "drafted_pick": 3, "drafted_club": "FRE"}
	var nat := {"id": "T_K", "drafted_year": 2030, "drafted_type": "national", "drafted_pick": 3, "drafted_club": "FRE"}
	var ctx := _ctx("Al Moss", coached, 2032, "GEE")
	_check(CareerTale._facts(mid, ctx)[0]["angle"] == "draft_us", "A mid-season pick in a season you coached them is yours")
	_check(CareerTale._facts(nat, ctx)[0]["angle"] == "draft_club", "A November pick for a season you coached elsewhere is theirs")
	var now := {"id": "T_L", "drafted_year": 2032, "drafted_type": "national", "drafted_pick": 9, "drafted_club": "GEE"}
	_check(CareerTale._facts(now, ctx)[0]["angle"] == "draft_us", "This year's draft, at your club now, is yours")


func _test_payoff_and_failure_apart() -> void:
	# An early pick who left with few games and won a Brownlow elsewhere: the pick paid, so no "fell short".
	var p := {"id": "T_M", "drafted_year": 2027, "drafted_type": "national", "drafted_pick": 5, "drafted_club": "FRE", "club": "GEE",
			"career": _career([["FRE", 2028, 2029, 12, 1], ["GEE", 2030, 2033, 80, 10]])}
	var ctx := _ctx("Al Moss", _seasons("FRE", 2028, 2033), 2034, "FRE",
			[{"year": 2032, "brownlow": [{"id": "T_M", "votes": 30}]}])
	var angles := CareerTale.tell(p, ctx).map(func(s): return s["angle"])
	_check(angles.has("brownlow") and not angles.has("fell_short_us"), "A payoff and a failure never sit together: %s" % [angles])
	# No award row for him: no Brownlow line, however late the pick.
	var q := {"id": "T_N", "drafted_year": 2027, "drafted_type": "national", "drafted_pick": 60, "drafted_club": "FRE", "club": "FRE",
			"backed": [{"year": 2028, "games": 3, "played": 3, "state": "done"}]}
	var qa := CareerTale.tell(q, _ctx("Al Moss", _seasons("FRE", 2028, 2033), 2034, "FRE",
			[{"year": 2032, "brownlow": [{"id": "SOMEONE_ELSE", "votes": 30}]}])).map(func(s): return s["angle"])
	_check(not qa.has("brownlow_late") and not qa.has("brownlow"), "No Brownlow line without his own Brownlow row: %s" % [qa])


func _test_writes_nothing() -> void:
	for c in _cases():
		var before: String = var_to_str(c[1])
		CareerTale.tell(c[1], c[2])
		_check(var_to_str(c[1]) == before, "%s: telling the story leaves the player as he was" % c[0])


## Every number in a sentence is one of its facts; no slot left unfilled, no
## "1 games"; the draft only ever opens.
func _fact_check(where: String, story: Array) -> void:
	var num_re := RegEx.create_from_string("\\d+")
	var i := 0
	for s in story:
		var t := str(s["text"])
		var facts := var_to_str(s["facts"])
		for m in num_re.search_all(t):
			if not facts.contains(m.get_string()):
				_check(false, "%s: %s is not in the facts of \"%s\"" % [where, m.get_string(), t])
				return
		if t.contains("{") or t.contains("}") or t.contains("  ") or not t.ends_with("."):
			_check(false, "%s: broken sentence \"%s\"" % [where, t])
			return
		for bad in [" 1 games", " 1 votes", " 1 goals", " 1 premierships", " 0 votes"]:
			if t.contains(bad):
				_check(false, "%s: \"%s\" in \"%s\"" % [where, bad.strip_edges(), t])
				return
		if i > 0 and str(s["angle"]).begins_with("draft"):
			_check(false, "%s: the draft line is not first" % where)
			return
		i += 1
	_check(story.size() <= CareerTale.MAX_SENTENCES, "%s: at most five sentences" % where)


func _every_player() -> Array:
	var out := []
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			out.append(p)
	return out


func _tell_all() -> Dictionary:
	var out := {}
	var base := CareerTale.context()
	for p in _every_player():
		var ctx := base.duplicate()
		ctx["name"] = GameDB.player_display_name(p)
		out[str(p["id"])] = CareerTale.tell(p, ctx)
	return out


## Every premade history's stories are checked for every player straight from
## the shipped history, during its intake draft (a coach can open a sheet
## there). One start, the 2028 one (its draft is short), also plays out the
## draft and is checked again with this year's draftees on the lists, then
## saved and reloaded. The 2030 start's MEL draft added ~10 s and changed no
## story (measured 2026-11-14: 727 players, 113 told, 0 changed by the draft).
func _test_premade_histories() -> void:
	var told := 0
	_check(PremadeHistory.STARTS.has(2028) and PremadeHistory.STARTS.size() >= 2,
			"The premade histories include the 2028 start (%s)" % str(PremadeHistory.STARTS))
	for first in PremadeHistory.STARTS:
		GameState.reset()
		GameState.tutorials = false
		# A replay seed refuses a premade history (it plays the years live), so
		# the history is picked from the global seed instead, still pinned.
		GameState.replay_seed = 0
		seed(SUITE_SEED + first)
		_check(GameState.begin_from_history(first), "History %d starts" % first)
		var code := "TAS" if first == 2028 else "MEL"
		GameState.choose_sim_ahead_club(code)
		var stories := _tell_all()
		told += _fact_check_all("%d draft" % first, stories)
		# The same save tells the same story.
		_check(var_to_str(_tell_all()) == var_to_str(stories), "%d: the same save, the same stories" % first)
		if first != 2028:
			continue
		var draft: Draft = GameState.draft
		var guard := 0
		while not draft.is_finished() and guard < 500:
			guard += 1
			draft.auto_until_user_turn()
			if draft.is_user_turn():
				draft.pick_for_me()
		_check(GameState.finish_intake_draft(), "%d: the intake draft finishes" % first)
		stories = _tell_all()
		_fact_check_all("%d season" % first, stories)
		# The same story after a save and reload too.
		_check(GameState.save_career(), "%d: the career saves" % first)
		_check(GameState.load_career(), "%d: the career reloads" % first)
		var reloaded := _tell_all()
		var same := true
		for id in stories:
			if CareerTale.text(stories[id]) != CareerTale.text(reloaded.get(id, [])):
				same = false
				_check(false, "%d %s: the story changed across a reload:\n    %s\n    %s" % [first, id,
						CareerTale.text(stories[id]), CareerTale.text(reloaded.get(id, []))])
				break
		_check(same, "%d: a reload tells the same stories" % first)
		GameState.delete_saved_career()
	GameState.replay_seed = SUITE_SEED
	_check(told > 0, "Some players in the premade histories have a story (%d)" % told)


## Fact-checks every story; returns how many players have one.
func _fact_check_all(where: String, stories: Dictionary) -> int:
	var told := 0
	for id in stories:
		_fact_check("%s %s" % [where, id], stories[id])
		if not (stories[id] as Array).is_empty():
			told += 1
	return told


## The sheet shows the story above his facts, and a fact the story says is not
## repeated under it.
func _test_sheet_shows_it_once() -> void:
	GameState.reset()
	GameState.start_season("FRE", GameDB.club_list("FRE"))
	GameState.tutorials = false
	var p: Dictionary = GameState.my_list[0]
	var id := str(p["id"])
	p["drafted_year"] = GameState.season_year - 1
	p["drafted_type"] = "national"
	p["drafted_pick"] = 41
	p["drafted_club"] = "FRE"
	GameState.honour_roll.append({"year": GameState.season_year - 1, "premier": "GEE", "my_club": "",
			"brownlow": [{"id": id, "votes": 27, "club": "FRE"}]})
	var host := Control.new()
	_tree.root.add_child(host)
	host.size = Vector2(390, 844)
	var sheet := PlayerSheet.open(host, p)
	await _settle()
	var story: Label = sheet.find_child("CareerStory", true, false)
	_check(story != null and story.text.contains("27 votes"), "The sheet tells his story")
	if story != null:
		_check(story.text.contains("to us at pick 41") or story.text.begins_with("We took"), "The pick is ours: %s" % story.text)
		_check(story.text.contains("From pick 41, he won the %d Brownlow with 27 votes." % (GameState.season_year - 1)),
				"Told from his pick: %s" % story.text)
	var repeated := false
	for n in sheet.find_children("CareerFact_*", "Label", true, false):
		if (n as Label).text.begins_with("Brownlow Medal") and (n as Label).text.contains(str(GameState.season_year - 1)):
			repeated = true
	_check(not repeated, "The Brownlow the story tells is not listed again under it")
	var box: Control = sheet.find_child("CareerStoryBox", true, false)
	_check(box != null and box.get_global_rect().end.x <= 390.5, "The story fits a portrait phone")
	host.queue_free()
	await _settle()
