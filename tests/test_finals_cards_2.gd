extends RefCounted
## The finals cards' second slice (open requirements 35 and 36; director's rulings
## 2026-10-13 and 2026-11-03), behind the switch finals_cards_2: A3, A9, A14, A15,
## A16, B7, B8, B9 and the one card the week your season ends. Each fires on its
## facts and nowhere else, the facts are true, each choice does what it says, the
## season-end card comes once, B8's fitness cost reaches the next pre-season's
## base, and with the switch off the game is exactly as before. Part of the story
## suite (tests/test_story.gd calls run()).

var s   # the story suite: _check()

const IDS := ["finals_drought_over", "finals_prelim_week", "finals_written_off", "finals_knocked_out",
		"finals_one_week_short", "gf_night_before", "gf_premiers", "gf_runners_up"]
const END_IDS := ["finals_knocked_out", "finals_one_week_short", "gf_premiers", "gf_runners_up"]


func run(suite) -> void:
	s = suite
	_t("_test_switch_off")
	Features.set_on(StoryDeck.FINALS_2, true)
	_t("_test_deck")
	_t("_test_season_end_draw")
	_t("_test_end_facts")
	_t("_test_history_lines")
	_t("_test_margin_lines")
	_t("_test_week_facts")
	_t("_test_effects")
	_t("_test_fitness_debt")
	Features.clear(StoryDeck.FINALS_2)
	ClubHistory.reload()


func _check(c: bool, m: String) -> void:
	s._check(c, m)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args, s)


## Geelong ranked `rank` + 1 with the home and away done and the finals drawn (as slice 1's suite).
func _finals_game(seed: int, rank := 0) -> void:
	GameState.reset()
	GameState.career_seed = seed
	GameState.replay_seed = seed
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var sea: Season = GameState.season
	var codes: Array = sea.ladder.keys()
	codes.sort()
	codes.erase("GEE")
	codes.insert(rank, "GEE")
	for i in range(codes.size()):
		var row: Dictionary = sea.ladder[codes[i]]
		row["w"] = 20 - i
		row["l"] = 4 + i
		row["d"] = 0
		row["p"] = 24
		row["pf"] = 2400 - i * 20
		row["pa"] = 2000
	sea.round_index = sea.fixture.size()
	sea.recalc_ladder()
	sea.start_finals()


## Knocked out in the final `tag` (e.g. "EF1", "PF2").
func _knocked_out(seed: int, tag: String) -> void:
	_finals_game(seed, 6)
	GameState.season.finals["slots"]["L_" + tag] = "GEE"
	GameState.season.finals["week"] = 4 if tag.begins_with("PF") else 2


## The Grand Final played: Geelong won it (or lost) by `margin`, `star` its best on the day,
## and `bog` the best on the ground from either side.
func _grand_final(seed: int, won: bool, margin: int, star_bog := true) -> Dictionary:
	_finals_game(seed, 0)
	var sea: Season = GameState.season
	var opp := "COL"
	var mine: Array = GameState.my_list
	var theirs: Array = sea.lists[opp]
	var players := {str(mine[0]["id"]): {"disposals": 30.0, "goals": 2.0}, str(mine[1]["id"]): {"disposals": 10.0},
			str(theirs[0]["id"]): {"disposals": 40.0 if not star_bog else 12.0, "goals": 3.0 if not star_bog else 0.0}}
	var res := {"tag": "GF", "home": "GEE", "away": opp, "score": [80 + (margin if won else 0), 80 + (0 if won else margin)],
			"players": players, "roster": [[{"id": str(mine[0]["id"])}, {"id": str(mine[1]["id"])}], [{"id": str(theirs[0]["id"])}]]}
	sea.finals["weeks"] = [[], [], [], [], [res]]
	sea.finals["week"] = 6
	sea.finals["premier"] = "GEE" if won else opp
	sea.finals["runner_up"] = opp if won else "GEE"
	sea.finals["slots"]["L_GF"] = opp if won else "GEE"
	sea.finals["done"] = true
	return {"star": GameDB.player_display_name(mine[0]), "opp": opp}


func _ids(cards: Array) -> Array:
	return cards.map(func(c): return str((c as Dictionary).get("tid", "")))


func _test_switch_off() -> void:
	Features.set_on(StoryDeck.FINALS_2, false)
	var deck := StoryDeck.all()
	for id in IDS:
		_check(StoryDeck.by_id(deck, id).is_empty(), "Switch off: %s is not in the deck" % id)
	_knocked_out(4101, "EF1")
	GameState._next_week_event()
	_check(GameState.week_events.is_empty(), "Switch off: knocked out, no card comes (as before)")
	_check(not (GameState.story["season"] as Dictionary).has(ClubStories.SEASON_END_MARK), "Switch off: nothing is written to the story")
	var facts: Dictionary = ClubStories.context(GameState)["club"]
	_check(not facts.has("result") and not facts.has("underdog"), "Switch off: the club facts are as before")
	_grand_final(4102, true, 20)
	GameState._next_week_event()
	_check(GameState.week_events.is_empty() and GameState.preseason_run_debt == 0.0, "Switch off: premiers, no card and no fitness debt")
	Features.clear(StoryDeck.FINALS_2)


func _test_deck() -> void:
	var deck := StoryDeck.all()
	for id in IDS:
		_check(not StoryDeck.by_id(deck, id).is_empty(), "Switch on: %s is in the deck" % id)
	var errs := StoryDeck.validate(deck)
	_check(errs.is_empty(), "The deck with the second slice passes its checks: %s" % "; ".join(PackedStringArray(errs.slice(0, 4))))
	var t := StoryDeck.by_id(deck, "gf_premiers").duplicate(true)
	t["id"] = "x"
	t["feature"] = "no_such_switch"
	_check(not StoryDeck.validate([t]).is_empty(), "A card behind an unknown switch is refused")
	# The rulings, as data: no board reward on any of the eight.
	var board := []
	for id in IDS:
		for c in StoryDeck.by_id(deck, id)["choices"]:
			for e in c["effects"]:
				if str(e["op"]) == "board":
					board.append(id)
	_check(board.is_empty(), "No card of the eight rewards the board (%s)" % str(board))
	var a3: Dictionary = StoryDeck.by_id(deck, "finals_drought_over")
	var swap: Dictionary = a3["choices"][1]["effects"][1]
	_check(str(swap["op"]) == "culture" and str(swap["strand"]) == "standards" and int(swap["d"]) == 1,
			"A3 'Keep the noise outside': board +1 swapped for Standards +1")


func _test_season_end_draw() -> void:
	var want := {"EF1": "finals_knocked_out", "SF2": "finals_knocked_out", "WC1": "finals_knocked_out", "PF1": "finals_one_week_short"}
	for tag in want:
		_knocked_out(4200, tag)
		GameState._next_week_event()
		_check(_ids(GameState.week_events) == [want[tag]], "Lost the %s: the season-end card is %s (%s)" % [tag, want[tag], str(_ids(GameState.week_events))])
		GameState._next_week_event()
		_check(GameState.week_events.is_empty(), "Lost the %s: the season-end card comes once" % tag)
	_grand_final(4201, true, 12)
	GameState._next_week_event()
	_check(_ids(GameState.week_events) == ["gf_premiers"], "Premiers: B8 always comes (%s)" % str(_ids(GameState.week_events)))
	_grand_final(4202, false, 12)
	GameState._next_week_event()
	_check(_ids(GameState.week_events) == ["gf_runners_up"], "Runners-up: B9 always comes (%s)" % str(_ids(GameState.week_events)))
	# Twenty seeds: always exactly one card, the right one.
	var bad := 0
	for i in range(20):
		_grand_final(4300 + i, i % 2 == 0, 3 + i * 3)
		GameState._next_week_event()
		if _ids(GameState.week_events) != ["gf_premiers" if i % 2 == 0 else "gf_runners_up"]:
			bad += 1
	_check(bad == 0, "Twenty Grand Finals: the season-end card is always the one card (%d wrong)" % bad)
	# Still in it: no season-end card, and the end cards never come in a finals week.
	_finals_game(4203, 0)
	GameState._next_week_event()
	var leaked := _ids(GameState.week_events).filter(func(x): return END_IDS.has(x))
	_check(leaked.is_empty() and not (GameState.story["season"] as Dictionary).has(ClubStories.SEASON_END_MARK),
			"Still alive: no season-end card")


func _test_end_facts() -> void:
	_knocked_out(4400, "SF1")
	var c := GameState.story_card("finals_knocked_out")
	_check(str(c["facts"]["result"]) == "eliminated" and str(c["facts"]["lost_final"]) == "semi-final",
			"Knocked out in a semi: result and lost_final are true (%s, %s)" % [c["facts"]["result"], c["facts"]["lost_final"]])
	_check(str(c["text"]).begins_with("Out in the semi-final."), "A15 names the final lost (%s)" % c["text"])
	var g := _grand_final(4401, true, 30, true)
	c = GameState.story_card("gf_premiers")
	_check(int(c["facts"]["margin"]) == 30 and str(c["text"]).begins_with("By 30 points, comfortably."), "B8 reads the margin (%s)" % c["text"])
	_check(str(c["text"]).contains("%s was best on ground." % g["star"]), "B8: your best, and best on ground (%s)" % c["text"])
	g = _grand_final(4402, true, 30, false)
	c = GameState.story_card("gf_premiers")
	_check(str(c["text"]).contains("%s was your best." % g["star"]), "B8: your best, beaten for the medal (%s)" % c["text"])
	g = _grand_final(4403, false, 45)
	c = GameState.story_card("gf_runners_up")
	_check(str(c["text"]).begins_with("Beaten by 45 points. A hiding.") and str(c["text"]).contains("%s gave everything." % g["star"])
			and str(c["text"]).ends_with("Nothing in football is quieter than the losing rooms."), "B9 reads true (%s)" % c["text"])
	_check(not str(c["text"]).contains("{"), "No fact left unfilled")


func _test_history_lines() -> void:
	ClubHistory.use({"AAA": {"years": [1990, 2015], "comps": {}, "also": {}, "none": false},
			"NON": {"years": [], "comps": {}, "also": {}, "none": true}})
	var y := 2030
	var roll := func(rows: Array) -> Array:
		var out := []
		for r in rows:
			out.append({"year": r[0], "premier": r[1], "runner_up": r[2]})
		return out
	var cases := [
		["NON", [], true, "The club's first premiership. Ever."],
		["AAA", [[2029, "AAA", "X"]], true, "Back-to-back."],
		["AAA", [[2028, "AAA", "X"], [2029, "AAA", "X"]], true, "Three in a row."],
		["AAA", [[2027, "AAA", "X"], [2028, "AAA", "X"], [2029, "AAA", "X"]], true, "Four in a row."],
		["AAA", [[2029, "X", "AAA"]], true, "A year after losing one, they've won one."],
		["AAA", [[2026, "X", "Y"]], true, "The first flag since 2015."],
		["AAA", [[2025, "AAA", "X"], [2029, "X", "Y"]], true, "Another flag for the club."],
		["AAA", [[2029, "X", "AAA"]], false, "Two Grand Finals, two losses."],
		["AAA", [[2028, "X", "AAA"], [2029, "X", "AAA"]], false, "Three Grand Finals lost in a row."],
		["AAA", [[2029, "AAA", "X"]], false, "Last year's premiers, beaten on the day."],
		["AAA", [[2026, "X", "Y"]], false, "The first Grand Final since 2015, and it got away."],
		["AAA", [[2025, "X", "AAA"]], false, "So close to a flag."],
		# A club the record does not know: never "first ever".
		["ZZZ", [], true, "Another flag for the club."],
	]
	var bad := []
	for c in cases:
		var got := ClubStories.history_line(str(c[0]), y, roll.call(c[1]), bool(c[2]))
		if got != str(c[3]):
			bad.append("%s %s -> %s" % [c[0], str(c[1]), got])
	_check(bad.is_empty(), "Every history line is the right one (%s)" % " | ".join(PackedStringArray(bad)))
	# The csv's flags count only before the save: a save that began in 2026 owns 2026 on.
	_check(ClubStories.history_line("AAA", y, roll.call([[2015, "X", "Y"], [2029, "X", "Y"]]), true) == "The first flag since 1990.",
			"A flag the csv has but the save's own year says otherwise is not counted")
	# Two Grand Finals in a row never read the same.
	var a := ClubStories.history_line("AAA", 2030, roll.call([[2029, "X", "Y"]]), true)
	var b := ClubStories.history_line("AAA", 2031, roll.call([[2029, "X", "Y"], [2030, "AAA", "Y"]]), true)
	_check(a != b, "Back-to-back Grand Finals read differently (%s / %s)" % [a, b])
	ClubHistory.reload()


func _test_margin_lines() -> void:
	var want := {[3, true]: "By 3 points. A kick in it at the siren.", [7, true]: "By 7 points.", [25, true]: "By 25 points, comfortably.",
			[40, true]: "By 40 points. A thumping.", [6, false]: "Beaten by 6 points. Under a goal.", [24, false]: "Beaten by 24 points.",
			[39, false]: "Beaten by 39 points, well held.", [41, false]: "Beaten by 41 points. A hiding.",
			[1, true]: "By 1 point. A kick in it at the siren.", [1, false]: "Beaten by 1 point. Under a goal."}
	var bad := []
	for k in want:
		if ClubStories.margin_line(int(k[0]), bool(k[1])) != str(want[k]):
			bad.append(str(k))
	_check(bad.is_empty(), "The margin bands fall at 6, 24 and 39 (%s)" % str(bad))


func _test_week_facts() -> void:
	# Underdog: a final against a side that finished above you.
	_finals_game(4500, 8)   # ninth: a wildcard final against a side above
	var f: Dictionary = ClubStories.context(GameState)["club"]
	_check(bool(f["underdog"]), "Ninth, playing a wildcard final: the underdog")
	_finals_game(4501, 6)   # seventh: hosts the wildcard against tenth
	f = ClubStories.context(GameState)["club"]
	_check(not bool(f["underdog"]), "Seventh, at home to a side below: not the underdog")
	# Years since a final: the save's own board history.
	GameState.board["history"] = [{"year": GameState.season_year - 4, "position": 3}, {"year": GameState.season_year - 3, "position": 14},
			{"year": GameState.season_year - 2, "position": 12}, {"year": GameState.season_year - 1, "position": 11}]
	f = ClubStories.context(GameState)["club"]
	_check(int(f["years_since_final"]) == 3 and int(f["last_final_year"]) == GameState.season_year - 4,
			"Three seasons without a final since %d (%d)" % [int(f["last_final_year"]), int(f["years_since_final"])])
	var drought := StoryEngine.eligible_subject(StoryDeck.by_id(StoryDeck.all(), "finals_drought_over"),
			ClubStories.context(GameState), GameState.story, 0, RandomNumberGenerator.new())
	_check(not drought.is_empty(), "A3 can come after three years without a final")
	GameState.board["history"] = [{"year": GameState.season_year - 3, "position": 3}]
	drought = StoryEngine.eligible_subject(StoryDeck.by_id(StoryDeck.all(), "finals_drought_over"),
			ClubStories.context(GameState), GameState.story, 0, RandomNumberGenerator.new())
	_check(drought.is_empty(), "...and not after two")
	GameState.board["history"] = []
	drought = StoryEngine.eligible_subject(StoryDeck.by_id(StoryDeck.all(), "finals_drought_over"),
			ClubStories.context(GameState), GameState.story, 0, RandomNumberGenerator.new())
	_check(drought.is_empty(), "...nor when the save has no final on record to name")
	# The forecast is the weather the Grand Final is played in.
	var seen := {}
	for i in range(30):
		_finals_game(4600 + i, 0)
		var sea: Season = GameState.season
		sea.finals["week"] = 5
		sea.finals["slots"]["W_PF1"] = "GEE"
		sea.finals["slots"]["W_PF2"] = "COL"
		var gf := {}
		for m in sea.finals_week_matches():
			gf = m
		if gf.is_empty():
			continue
		var w := sea.weather_for(str(gf["home"]), str(gf["away"]), Season.REGULAR_ROUNDS + 5, gf)
		var line := str(ClubStories.context(GameState)["club"]["forecast_line"])
		if line != str(ClubStories.FORECAST[w]):
			seen["bad"] = int(seen.get("bad", 0)) + 1
		seen[w] = true
	_check(not seen.has("bad") and seen.size() >= 1, "B7's forecast is the Grand Final's own weather (%s)" % str(seen))


func _culture(strand: String) -> int:
	return Culture.value(GameState.relations, "GEE", strand)


func _play(id: String, choice: int) -> Dictionary:
	var c := GameState.story_card(id)
	GameState.week_events = [c]
	var before := {"standards": _culture("standards"), "together": _culture("together"), "ambition": _culture("ambition"),
			"morale": ClubLife.morale(GameState.my_list[0])}
	GameState.resolve_card(0, choice)
	return {"standards": _culture("standards") - int(before["standards"]), "together": _culture("together") - int(before["together"]),
			"ambition": _culture("ambition") - int(before["ambition"]), "morale": ClubLife.morale(GameState.my_list[0]) - int(before["morale"])}


func _test_effects() -> void:
	_knocked_out(4700, "EF1")
	var d := _play("finals_knocked_out", 0)
	_check(d["standards"] == 2 and d["morale"] == -3, "A15 'Tell them': Standards +2, morale -3 (%s)" % str(d))
	_knocked_out(4700, "EF1")
	d = _play("finals_knocked_out", 1)
	_check(d["together"] == 2 and d["morale"] == 0, "A15 'Thank them': Togetherness +2 only (%s)" % str(d))
	_knocked_out(4701, "PF1")
	d = _play("finals_one_week_short", 1)
	_check(d["standards"] == 2 and d["morale"] == -5, "A16 'Nobody's spot': Standards +2, morale -5, no board (%s)" % str(d))
	_grand_final(4702, false, 10)
	d = _play("gf_runners_up", 1)
	_check(d["together"] == 2 and d["morale"] == 0, "B9 'Let it go': Togetherness +2 only (%s)" % str(d))
	_grand_final(4702, false, 10)
	d = _play("gf_runners_up", 0)
	_check(d["ambition"] == 2 and d["morale"] == -4, "B9 'Photo': Ambition +2, morale -4 (%s)" % str(d))
	_grand_final(4703, true, 10)
	d = _play("gf_premiers", 1)
	_check(d["ambition"] == 2 and d["morale"] == 4 and GameState.preseason_run_debt == 0.0, "B8 'One week': Ambition +2, morale +4, no cost (%s)" % str(d))
	_finals_game(4704, 0)
	GameState.season.finals["week"] = 4
	d = _play("finals_prelim_week", 0)
	_check(d["standards"] == 2 and d["morale"] == -2, "A9 'No Grand Final talk': Standards +2, morale -2 (%s)" % str(d))
	_finals_game(4705, 8)
	d = _play("finals_written_off", 1)
	_check(d["together"] == 2, "A14 'Back your players': Togetherness +2 (%s)" % str(d))
	_finals_game(4706, 0)
	d = _play("finals_drought_over", 1)
	_check(d["standards"] == 1, "A3 'Keep the noise outside': Standards +1 (%s)" % str(d))
	# Every gain and cost line carries its size, and none is left with a placeholder.
	var bad := []
	for id in IDS:
		var card := GameState.story_card(id)
		for o in card["options"]:
			for l in StoryEngine.stakes_lines(o["effects"], card["facts"]):
				if str(l).contains("{"):
					bad.append(id)
	_check(bad.is_empty(), "Every line is filled (%s)" % str(bad))


func _test_fitness_debt() -> void:
	_grand_final(4800, true, 10)
	var card := GameState.story_card("gf_premiers")
	var lines := " ".join(StoryEngine.stakes_lines(card["options"][0]["effects"], card["facts"]))
	_check(lines.contains("starts next pre-season one week of running behind"), "B8 'Celebrate' says its cost: %s" % lines)
	_play("gf_premiers", 0)
	_check(GameState.preseason_run_debt == -1.0, "B8 'Celebrate': one week of running owed (%s)" % GameState.preseason_run_debt)
	_check(GameState.save_career() and GameState.load_career() and GameState.preseason_run_debt == -1.0, "The debt survives a reload")
	# The preseason switch on: the next pre-season opens one week behind.
	Features.set_on("preseason", true)
	PreSeason.reload()
	GameState.reset()
	GameState.career_seed = 4801
	GameState.replay_seed = 4801
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	GameState.preseason_run_debt = -1.0
	GameState.preseason = {}
	GameState.open_preseason()
	var entry: Dictionary = (GameState.preseason.get("clubs", {}) as Dictionary).get("GEE", {})
	var other: Dictionary = (GameState.preseason.get("clubs", {}) as Dictionary).get("COL", {})
	_check(float(entry.get("run", 0.0)) == float(other.get("run", 0.0)) - 1.0 and GameState.preseason_run_debt == 0.0,
			"The pre-season opens a week of running behind, and the debt is paid (%s)" % str(entry.get("run", "?")))
	Features.clear("preseason")
	PreSeason.reload()
	GameState.delete_saved_career()
