extends RefCounted
## Factions.gd (relationship overhaul, the factions phase): unhappy players
## standing together at every club, pressure, demands and ultimatums, the
## coach's answers, their cards, morale and Togetherness, the leader's trade
## ask, the profile line and the save. Run through tests/run_factions_tests.gd.

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 2047
const Ran := preload("res://tests/functions_ran.gd")


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	GameDB.reload()
	_t("_test_files_check")
	_t("_test_group_forms_and_pushes")
	_t("_test_members_drift_away")
	_t("_test_temperament_sizes_joining")
	_t("_test_meet")
	_t("_test_refuse_then_split")
	_t("_test_unanswered_ultimatum_breaks")
	_t("_test_rival_clubs_answer_by_standing")
	_t("_test_morale_settles_lower")
	_t("_test_cards_come_on_the_leader")
	_t("_test_profile_line")
	_t("_test_season_end_and_save")
	_t("_test_a_season_played")
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	GameState.stories_on = true
	print(Ran.line("Factions", self))


func _fresh() -> void:
	GameState.reset()
	GameState.replay_seed = SUITE_SEED
	GameState.stories_on = false
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	GameState._settle_week_event()
	GameState.week_event = {}


## `n` players of a club, none of them injured, with no temperament lever
## either way (a plain clubless reading: each one is "professional"-free).
func _men(code: String, n: int, skip := 0) -> Array:
	var out := []
	for p in GameState.season.lists[code]:
		if skip > 0:
			skip -= 1
			continue
		p["injury_weeks"] = 0
		p["temperament"] = ["competitor"]
		out.append(p)
		if out.size() == n:
			break
	return out


## A selection grievance worth `v` opinion points, that does not fade.
func _sour(p: Dictionary, v := -12.0, tag := "selection", club := "GEE") -> void:
	Opinion.add_raw(GameState.relations, Opinion.player_key(str(p["id"])), "test_" + tag, v, 0.0, tag,
			"Left out", GameState.season_year, "Round 1", club)


func _tick(code: String, week: int) -> Array:
	var games := {}
	for p in GameState.season.lists[code]:
		games[str(p["id"])] = GameState.games_played(p)
	return Factions.round_tick(GameState, code, GameState.season.lists[code], code == GameState.my_club, games, week)


func _events(evs: Array) -> Array:
	return evs.map(func(e): return str(e["e"]))


func _test_files_check() -> void:
	Factions.reload()
	_check(Factions.check(Factions.cfg()).is_empty(), "The factions file passes its checks (%s)" % str(Factions.check(Factions.cfg())))
	_check(Opinion.check_defs(Opinion.defs()).is_empty(), "The marks file still passes with the faction marks")
	var bad: Array = StoryDeck.validate(StoryDeck.all()).filter(func(e): return str(e).begins_with("faction_"))
	_check(bad.is_empty(), "Every faction card is valid (%s)" % str(bad))
	var broken := Factions.cfg().duplicate(true)
	broken["leave_line"] = broken["join_line"]
	_check(not Factions.check(broken).is_empty(), "A file where a man joins and leaves in one round is refused")
	_check(Temperament.LEVERS.has("faction") and Temperament.scale({"temperament": ["fiery"]}, "faction") > 1.0
			and Temperament.scale({"temperament": ["professional"]}, "faction") < 1.0,
			"A fiery man is quicker to stand with others, a professional slower")


func _test_group_forms_and_pushes() -> void:
	_fresh()
	var men := _men("GEE", 4)
	var evs := _tick("GEE", 100)
	_check(evs.is_empty() and Factions.of_club(GameState, "GEE").is_empty(), "A settled club has no group")
	for p in men.slice(0, 2):
		_sour(p)
	_check(_tick("GEE", 101).is_empty(), "Two unhappy men are not a group")
	_sour(men[2])
	evs = _tick("GEE", 102)
	_check(_events(evs) == ["formed"], "A third makes a group (%s)" % str(_events(evs)))
	var f := Factions.of_player(GameState, "GEE", str(men[0]["id"]))
	_check(str(f.get("k", "")) == "fringe" and (f["members"] as Array).size() == 3 and str(f["state"]) == "forming",
			"Left-out men form the fringe group, three of them, still talking (%s)" % str(f))
	_check((f["members"] as Array).has(str(f["leader"])), "One of them leads it")
	_sour(men[3])
	_tick("GEE", 103)
	_check((f["members"] as Array).size() == 4, "A fourth joins the group that is there")
	var first := int(f["pressure"])
	var demanded := false
	for w in range(104, 120):
		if _events(_tick("GEE", w)).has("demand"):
			demanded = true
			break
	_check(demanded and str(f["state"]) == "demanding" and int(f["pressure"]) >= Factions.num("demand_at") and int(f["pressure"]) > first,
			"Pressure builds until the group asks for something (%d)" % int(f["pressure"]))
	var ult := false
	for w in range(120, 140):
		if _events(_tick("GEE", w)).has("ultimatum"):
			ult = true
			break
	_check(ult and str(f["state"]) == "ultimatum", "Left alone, it gives its final word")


func _test_members_drift_away() -> void:
	_fresh()
	var men := _men("GEE", 4)
	for p in men:
		_sour(p)
	_tick("GEE", 100)
	_check(Factions.of_club(GameState, "GEE").size() == 1, "The group forms")
	for p in men.slice(0, 2):
		GameState.relations.erase(Opinion.player_key(str(p["id"])))
	var evs := _tick("GEE", 101)
	_check(_events(evs) == ["faded"] and Factions.of_club(GameState, "GEE").is_empty(),
			"Two of four come round: too few are left and the group falls apart (%s)" % str(_events(evs)))
	_check(_tick("GEE", 102).is_empty(), "It does not form again straight away")
	for p in men:
		_sour(p)
	_check(_tick("GEE", 103).is_empty(), "Its kind waits before it forms again")
	_check(_events(_tick("GEE", 101 + Factions.num("reform_wait"))) == ["formed"], "After the wait it can")


func _test_temperament_sizes_joining() -> void:
	var line := Factions.num("join_line")
	var need := float(Factions.num("join_need"))
	var calm := {"temperament": ["professional"]}
	var hot := {"temperament": ["fiery"]}
	var op := line - int(ceil(need))   # just enough for a man with no lean
	_check(Factions.readiness(op, {"temperament": ["competitor"]}) >= need, "A man with little lean joins at the line")
	_check(Factions.readiness(op, calm) < need, "A professional the same distance under does not")
	_check(Factions.readiness(line - 3, hot) >= need, "A fiery one joins closer to the line")
	_check(Factions.readiness(line + 5, hot) < 0.0, "Nobody joins above the line")


func _setup_group(state := "demanding") -> Dictionary:
	_fresh()
	var men := _men("GEE", 4)
	for p in men:
		_sour(p)
	_tick("GEE", 100)
	var f := Factions.of_player(GameState, "GEE", str(men[0]["id"]))
	f["state"] = state
	f["pressure"] = Factions.num("demand_at") if state == "demanding" else Factions.num("ultimatum_at")
	if state == "ultimatum":
		f["ult"] = 100
	return f


func _test_meet() -> void:
	var f := _setup_group()
	var ids: Array = (f["members"] as Array).duplicate()
	var r0 := Promises.respect(GameState)
	var a0 := Promises.authority(GameState)
	var t0 := Culture.value(GameState.relations, "GEE", "together")
	var before := Opinion.coach_opinion(GameState.relations, Opinion.player_key(str(ids[0])), true)
	var res: Dictionary = GameState.faction_answer("GEE", f, "meet")
	var st: Array = Factions.cfg()["standing"]["met"]
	_check(Factions.of_club(GameState, "GEE").is_empty() and bool(res["ended"]), "Met, the group is settled")
	_check(Opinion.coach_opinion(GameState.relations, Opinion.player_key(str(ids[0])), true) > before,
			"Each man thinks more of you")
	_check(Promises.respect(GameState) - r0 == int(st[0]) and Promises.authority(GameState) - a0 == int(st[1]),
			"Respect and Authority move by the file's sizes")
	_check(Culture.value(GameState.relations, "GEE", "together") - t0 == int(Factions.cfg()["together"]["met"]),
			"Togetherness rises")
	var parts := Factions.effect_parts("meet", 4, false)
	var words := " ".join(parts.map(func(x): return str(x[1])))
	_check(words.contains("Each of the 4 players") and words.contains("Your Authority down %d" % absi(int(st[1]))),
			"The choice states each man's move and the Authority it costs (%s)" % words)


func _test_refuse_then_split() -> void:
	var f := _setup_group()
	var p0 := int(f["pressure"])
	var a0 := Promises.authority(GameState)
	GameState.faction_answer("GEE", f, "refuse")
	_check(Factions.of_club(GameState, "GEE").size() == 1 and bool(f["refused"])
			and int(f["pressure"]) == p0 + Factions.num("refused_jump"), "Refused, the group hardens")
	_check(Promises.authority(GameState) > a0, "Holding the line builds Authority")
	_check(Factions.ai_answer(GameState, "GEE", f) == "meet" or Factions.ai_answer(GameState, "GEE", f) == "refuse",
			"A rule answers it either way")
	f["state"] = "ultimatum"
	var leader := GameState.list_player(str(f["leader"]))
	leader["contract_years"] = 3
	GameState.faction_answer("GEE", f, "split")
	_check(Factions.of_club(GameState, "GEE").is_empty() and int(leader.get("faction_out", 0)) == GameState.season_year,
			"Broken up, its leader is told he can go")
	GameState._collect_trade_requests()
	var ask: Dictionary = GameState.trade_requests.get(str(leader["id"]), {})
	_check(str(ask.get("why", "")) == "unsettled" and not (ask.get("to", []) as Array).is_empty(),
			"At season's end he asks to be traded (%s)" % str(ask))
	_check(GameState._request_line(leader, ask).contains("falling out with the coach"), "The news says why")


func _test_unanswered_ultimatum_breaks() -> void:
	var f := _setup_group("ultimatum")
	var leader_id := str(f["leader"])
	var t0 := Culture.value(GameState.relations, "GEE", "together")
	var broke := false
	for w in range(101, 101 + Factions.num("ultimatum_rounds") + 2):
		for ev in _tick("GEE", w):
			if str(ev["e"]) == "broken":
				broke = true
				GameState.faction_answer("GEE", ev["f"], "broken")
	_check(broke, "An ultimatum nobody answers breaks the group")
	_check(int(GameState.list_player(leader_id).get("faction_out", 0)) == GameState.season_year,
			"Its leader wants out")
	_check(Culture.value(GameState.relations, "GEE", "together") < t0, "Togetherness takes the hit")


func _test_rival_clubs_answer_by_standing() -> void:
	_fresh()
	var code := "COL"
	var men := _men(code, 4)
	for p in men:
		_sour(p, -12.0, "selection", code)
	var evs := _tick(code, 100)
	_check(_events(evs) == ["formed"], "A rival's unhappy players form a group by the same rule")
	var f: Dictionary = evs[0]["f"]
	var s := Promises.standing(GameState, true, code)
	s["respect"] = 40
	s["authority"] = 60
	_check(Factions.ai_answer(GameState, code, f) == "refuse", "A coach whose Authority leads holds the line")
	f["state"] = "ultimatum"
	_check(Factions.ai_answer(GameState, code, f) == "split", "and on the final word breaks it up")
	s["respect"] = 60
	s["authority"] = 40
	_check(Factions.ai_answer(GameState, code, f) == "meet", "A coach whose Respect leads hears them out")
	s["respect"] = 40
	s["authority"] = 60
	var news0 := GameState.news.size()
	GameState.faction_answer(code, f, "split")
	_check(GameState.news.size() > news0 and str(GameState.news.back().get("text", "")).contains(GameDB.club_name(code)),
			"The league hears when a rival's group is broken up")
	_check(int(Promises.standing(GameState, false, code)["authority"]) > 60, "His own standing moves, not yours")


func _test_morale_settles_lower() -> void:
	var f := _setup_group()
	var id := str(f["members"][0])
	_check(Factions.morale_shift(GameState, "GEE", id) == int(Factions.cfg()["morale_shift"]["demanding"]),
			"A man whose group is pushing settles lower")
	_check(Factions.morale_shift(GameState, "GEE", "nobody") == 0, "Anyone else is untouched")
	var p := {"morale": ClubLife.MORALE_BASE, "injury_weeks": 0}
	ClubLife.drift_morale(p, 50, -6)
	_check(int(p["morale"]) == ClubLife.MORALE_BASE - ClubLife.DRIFT_STEP, "Morale drifts a step towards the lower settling point")


func _faction_deck() -> Array:
	return StoryDeck.all().filter(func(t): return str(t["id"]).begins_with("faction_"))


func _test_cards_come_on_the_leader() -> void:
	var f := _setup_group()
	GameState.stories_on = true
	ClubStories.note_event(GameState, "faction_demand", str(f["leader"]))
	var cards: Array = StoryEngine.pick_week(_faction_deck(), ClubStories.context(GameState), GameState.story)
	_check(cards.size() == 1 and str(cards[0]["tid"]) == "faction_fringe_demand"
			and str(cards[0].get("player_id", "")) == str(f["leader"]),
			"The fringe group's demand comes as a card on its leader (%s)" % str(cards.map(func(c): return c.get("tid", ""))))
	if cards.is_empty():
		return
	_check(not str(cards[0]["text"]).contains("{"), "Every word on the card is filled in (%s)" % str(cards[0]["text"]))
	var detail := str(cards[0]["options"][0]["detail"])
	_check(detail.contains("Each of the 4 players") and detail.contains("Togetherness up"),
			"Its choice states what meeting them does (%s)" % detail)
	var leader := GameState.list_player(str(f["leader"]))
	ClubStories.apply_choice(GameState, cards[0], 0)
	_check(Factions.of_club(GameState, "GEE").is_empty() and leader.has("expects_game"),
			"Picking him meets the demand: the group settles and he is owed the game")
	var u := _setup_group("ultimatum")
	ClubStories.note_event(GameState, "faction_ultimatum", str(u["leader"]))
	var later: Array = StoryEngine.pick_week(_faction_deck(), ClubStories.context(GameState), GameState.story)
	_check(later.size() == 1 and str(later[0]["tid"]) == "faction_fringe_ultimatum", "The final word comes as its own card")
	GameState.stories_on = false


func _test_profile_line() -> void:
	var f := _setup_group()
	var member := str((f["members"] as Array).filter(func(x): return str(x) != str(f["leader"]))[0])
	var line := RelationsView.faction(GameState, member)
	_check(line.begins_with("Stands with the fringe players (4 of them, led by ") and line.contains("They want a fair go at selection"),
			"His profile says who he stands with and what they want (%s)" % line)
	_check(RelationsView.faction(GameState, str(f["leader"])).contains("he leads them"), "The leader's says he leads them")
	_check(RelationsView.faction(GameState, "nobody") == "", "A man with no group has no line")


func _test_season_end_and_save() -> void:
	var f := _setup_group("ultimatum")
	var leader_id := str(f["leader"])
	GameState.save_career()
	var kept := (GameState.factions.duplicate(true) as Dictionary)
	GameState.factions = {}
	_check(GameState.load_career(), "The career loads")
	_check(str(GameState.factions) == str(kept), "The groups come back with the save")
	GameState._factions_season_end()
	_check(GameState.factions.is_empty(), "A season's end clears every group")
	_check(int(GameState.list_player(leader_id).get("faction_out", 0)) == GameState.season_year,
			"A group still on its final word gives up: its leader asks out")


## A season played through at every club: groups form, some reach a demand,
## and the interruption rate stays low (reported: the director's busywork guard).
func _test_a_season_played() -> void:
	_fresh()
	var formed := {}
	var mine := 0
	var pushing := {}
	var s = GameState.season
	var guard := 0
	while s.round_index < s.regular_rounds() and guard < 40:
		guard += 1
		GameState.advance()
		for code in Factions.clubs(GameState):
			for f in Factions.of_club(GameState, str(code)):
				formed["%s|%s|%d" % [code, f["k"], int(f["since"])]] = true
				if str(f["state"]) != "forming":
					pushing["%s|%s|%d" % [code, f["k"], int(f["since"])]] = true
				if code == GameState.my_club:
					mine += 1
	print("Factions season: %d groups formed across the league, %d reached a demand, %d weeks your club had one" % [
			formed.size(), pushing.size(), mine])
	_check(s.round_index >= s.regular_rounds(), "The season plays through with factions on")
	_check(formed.size() <= 18 * 4, "Not every club is at war with its coach (%d groups)" % formed.size())
