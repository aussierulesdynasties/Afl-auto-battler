extends RefCounted
## The league's real year events, 1990 to 2026 (Legacy L10, TODO row 142):
## the data is whole, its cards are valid story cards, a 1990 campaign fires a
## sample across the decades in their real seasons with their real penalties,
## and with Controversies off none of the controversies fires.
## Run through tests/run_year_events_tests.gd.

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 1990
## The sample: one season per decade, with what each must fire.
const SAMPLE := {
	1990: ["vfl_becomes_afl", "port_secret_deal"],
	1996: ["essendon_90s_breach"],
	2002: ["brown_paper_bags"],
	2013: ["supplements_saga", "tanking_inquiry"],
	2014: ["swans_trade_ban"],
	2020: ["hub_season"],
}


func _check(cond: bool, label: String) -> void:
	checks += 1
	if not cond:
		failures.append(label)
		print("  FAIL: ", label)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func run() -> void:
	_t("_test_data_whole")
	_t("_test_cards_valid")
	_t("_test_fine_cut")
	_t("_test_campaign_fires_across_decades")
	_t("_test_week_fires_in_its_season")
	_t("_test_switch_off_fires_no_controversy")
	_t("_test_forfeited_pick_skipped")
	_t("_test_save_keeps_state")
	GameDB.reload()
	print(Ran.line("Year events", self))


# ---------------------------------------------------------------------------
func _test_data_whole() -> void:
	var all := YearEvents.all()
	_check(all.size() >= 60, "The year events load (%d)" % all.size())
	var codes := {"FIT": true}
	for c in GameDB.club_order:
		codes[c] = true
	var ids := {}
	var bad := []
	for e in all:
		var id := str(e.get("id", ""))
		if id == "" or ids.has(id):
			bad.append("id " + id)
		ids[id] = true
		var y := int(e.get("season", 0))
		if y < 1990 or y > 2026 or str(e.get("headline", "")) == "" or (e.get("beats", []) as Array).is_empty():
			bad.append(id)
		if (e.get("rows", []) as Array).is_empty():
			bad.append(id + " rows")
		var clubs = e.get("clubs", [])
		if str(clubs) != "all":
			for c in clubs:
				if not codes.has(str(c)):
					bad.append("%s club %s" % [id, str(c)])
		for p in e.get("penalties", []):
			if not bool(e.get("controversy", false)):
				bad.append(id + " penalty without controversy")
			if not ["fine", "lose_pick", "finals_ban", "trade_ban"].has(str(p.get("op", ""))):
				bad.append(id + " op")
	_check(bad.is_empty(), "Every event has an id, a season 1990-2026, a headline, beats, its research rows and real clubs (%s)" % str(bad))


func _test_cards_valid() -> void:
	var cards := YearEvents.cards()
	_check(cards.size() >= 40, "The events carry their cards (%d)" % cards.size())
	var errs := StoryDeck.validate(cards)
	_check(errs.is_empty(), "Every year card is a valid story card (%s)" % str(errs.slice(0, 5)))
	var bare := []
	for t in cards:
		for o in t.get("options", []):
			if (o.get("effects", []) as Array).is_empty():
				bare.append(str(t["id"]))
	_check(bare.is_empty(), "Every option of every year card does something (%s)" % str(bare))


func _test_fine_cut() -> void:
	# Carlton's $930k in 2002 against a $3.0m-odd cap is about a third of the
	# board's budget; Essendon's $85k in 2003 is the smallest cut.
	var big := YearEvents.fine_cut_m(930000, 2002)
	var small := YearEvents.fine_cut_m(85000, 2003)
	_check(big > 1.0 and big <= YearEvents.CUT_MAX_M, "A large fine bites hard (%.1f)" % big)
	_check(small >= YearEvents.CUT_MIN_M and small < big, "A small fine bites a little (%.1f)" % small)
	_check(YearEvents.fine_cut_m(9000000, 2013) == YearEvents.CUT_MAX_M, "A fine near the whole cap is held at the most a cut can be")


## A 1990 career at Essendon, moved season by season through the sample.
func _start_1990(club: String, controversies: bool) -> void:
	GameState.set_setting("controversies", controversies)
	GameState.reset("1990")
	GameState.career_seed = SUITE_SEED
	GameState.replay_seed = SUITE_SEED
	GameState.start_season(club, GameDB.club_list(club))


## Jump the career to `year`, the regular season done, and run the week's events.
func _jump(year: int) -> Array:
	GameState.season_year = year
	GameState.season.round_index = GameState.season.fixture.size()
	return YearEvents.week(GameState)


func _fired() -> Array:
	return (YearEvents.state(GameState)["done"] as Array)


func _news_has(id: String) -> bool:
	for n in GameState.news:
		if str((n as Dictionary).get("year_event", "")) == id:
			return true
	return false


func _test_campaign_fires_across_decades() -> void:
	_start_1990("ESS", true)
	_check(GameDB.dataset_id == "1990" and GameState.season_year == 1990 and GameState.controversies,
			"A 1990 career with Controversies on")
	var cards_by_year := {}
	for year in SAMPLE:
		cards_by_year[year] = _jump(year)
		for id in SAMPLE[year]:
			_check(_fired().has(id) and _news_has(id), "%d: %s fires and makes the news" % [year, id])
	# Nothing fires out of its season.
	var wrong := []
	for e in YearEvents.all():
		if _fired().has(str(e["id"])) and not SAMPLE.has(int(e["season"])):
			wrong.append(str(e["id"]))
	_check(wrong.is_empty(), "No event fires outside its season (%s)" % str(wrong))
	# Essendon's own controversies come with a card; Carlton's do not.
	var ids_1996 := (cards_by_year[1996] as Array).map(func(c): return str(c.get("year_event", "")))
	var ids_2002 := (cards_by_year[2002] as Array).map(func(c): return str(c.get("year_event", "")))
	_check(ids_1996.has("essendon_90s_breach") and not ids_2002.has("brown_paper_bags"),
			"Your club's event is your call; another club's is news (%s %s)" % [str(ids_1996), str(ids_2002)])
	# The penalties.
	_check(GameState.pick_owner_of(1996, 1, "ESS") == YearEvents.FORFEIT and GameState.pick_owner_of(1996, 2, "ESS") == YearEvents.FORFEIT,
			"Essendon lose their 1996 first and second-round picks")
	_check(GameState.pick_owner_of(2002, 1, "CAR") == YearEvents.FORFEIT and GameState.pick_owner_of(2003, 2, "CAR") == YearEvents.FORFEIT,
			"Carlton lose their first and second-round picks in 2002 and 2003")
	_check(YearEvents.budget_cut_m(GameState, 1997) > 0.0 and YearEvents.budget_cut_m(GameState, 2003) == 0.0,
			"Essendon's 1996 fine cuts its 1997 football budget; Carlton's fine is not yours to pay")
	var cut_2014 := YearEvents.fine_cut_m(2000000, 2013)
	_check(cut_2014 > 2.0 and is_equal_approx(YearEvents.budget_cut_m(GameState, 2014), cut_2014),
			"Essendon's $2m fine in 2013 takes %.1f from 2014's budget" % cut_2014)
	GameState.season_year = 2014
	_check(YearEvents.trade_banned(GameState, "SYD") and not YearEvents.trade_banned(GameState, "ESS"),
			"Sydney are barred from trading players in")
	GameState.season_year = 2016
	_check(not YearEvents.trade_banned(GameState, "SYD"), "Sydney's trade ban ends after 2015")
	# The finals ban: Essendon miss 2013's finals whatever their ladder spot.
	GameState.season_year = 2013
	_check(YearEvents.finals_banned(GameState) == ["ESS"], "Essendon are out of 2013's finals")
	GameState.season.start_finals(YearEvents.finals_banned(GameState))
	var top: Array = GameState.season.finals["top"]
	_check(not top.has("ESS") and top.size() == GameState.season.finalists(),
			"The finals go on without Essendon, the next side in (%s)" % str(top))
	# The budget the coach sees: next season's is cut, and an allocation that
	# no longer fits steps down.
	GameState.season_year = 2014
	GameState._ensure_department_budget()
	_check(is_equal_approx(GameState.department_budget_annual_m(), ClubBudget.ANNUAL_M - cut_2014)
			and ClubBudget.total_m(GameState.department_budget) <= GameState.department_budget_annual_m() + 0.001,
			"2014's football budget is cut and the departments fit it (%.1f of %.1f)" % [
			ClubBudget.total_m(GameState.department_budget), GameState.department_budget_annual_m()])
	# Each event fires once.
	var before := _fired().size()
	_jump(2013)
	_check(_fired().size() == before, "An event fires once")


## The real path: a 1990 week's events come out of the weekly event, at the
## front of the week.
func _test_week_fires_in_its_season() -> void:
	# The season's opening week runs the week's events (_open_board_season).
	_start_1990("BRL", true)
	_check(_fired().has("bears_owner_collapse") and _fired().has("vfl_becomes_afl") and not _fired().has("save_our_skins"),
			"Round 1, 1990: the Bears' owner and the AFL's new name fire; Richmond's round-14 appeal waits (%s)" % str(_fired()))
	var first: Dictionary = GameState.week_events[0] if not GameState.week_events.is_empty() else {}
	_check(str(first.get("year_event", "")) == "bears_owner_collapse", "The Bears' card leads the week (%s)" % str(first.get("id", "")))
	GameState.season.round_index = 14
	GameState._next_week_event()
	_check(_fired().has("save_our_skins") and _news_has("save_our_skins"), "Round 15, 1990: Richmond's appeal is in the news")


func _test_switch_off_fires_no_controversy() -> void:
	_start_1990("ESS", false)
	_check(not GameState.controversies, "A 1990 career with Controversies off")
	var years := {}
	for e in YearEvents.all():
		years[int(e["season"])] = true
	var ys := years.keys()
	ys.sort()
	for y in ys:
		_jump(y)
	var bad := []
	var fired := 0
	for e in YearEvents.all():
		if _fired().has(str(e["id"])):
			fired += 1
			if bool(e.get("controversy", false)):
				bad.append(str(e["id"]))
	_check(bad.is_empty() and fired > 20, "With Controversies off no controversy fires, the rest do (%d fired; %s)" % [fired, str(bad)])
	_check(GameState.pick_owner_of(1996, 1, "ESS") == "ESS" and YearEvents.finals_banned(GameState).is_empty()
			and YearEvents.budget_cut_m(GameState, 2014) == 0.0, "No penalty lands")
	GameState.set_setting("controversies", true)


func _test_forfeited_pick_skipped() -> void:
	var pool := []
	for i in range(6):
		pool.append({"id": "p%d" % i, "overall": 60 - i})
	var d := Draft.build_intake(pool, ["CAR", "ESS", "GEE"], ["CAR", "ESS", "GEE"], SUITE_SEED, {}, {})
	d.set_pick_owners({"1:CAR": YearEvents.FORFEIT, "2:CAR": YearEvents.FORFEIT})
	_check(d.pick_sequence.size() == 4 and not d.pick_sequence.has("CAR") and not d.pick_sequence.has(YearEvents.FORFEIT),
			"The draft skips a forfeited pick (%s)" % str(d.pick_sequence))


func _test_save_keeps_state() -> void:
	_start_1990("ESS", true)
	_jump(1996)
	var was: Dictionary = GameState.year_events.duplicate(true)
	var state: Dictionary = GameState._save_state()
	_check(GameState._restore_career(state.duplicate(true)) and GameState.year_events == was and GameState.controversies,
			"A save keeps the fired events, the penalties and the switch")
	state.erase("controversies")
	state.erase("year_events")
	_check(GameState._restore_career(state.duplicate(true)) and GameState.controversies and GameState.year_events.is_empty(),
			"An older save loads with Controversies on and nothing fired")
