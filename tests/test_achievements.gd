extends RefCounted
## Achievements (director, 2026-11-14): 100 in all - two for each of the 22
## clubs a career can field (Fitzroy and the Club Forge club included) and 56
## for the coach. Each check type unlocks (or stays locked) exactly on the
## context it is written for. The context is the shape GameState builds at
## season's end, so these tests exercise the real check without simulating a
## season - plus one full season for the end-to-end path and the save round
## trip.
## Run through tests/run_achievements_tests.gd.

var failures: Array[String] = []
var checks := 0

## Every season and draft here is seeded (C15): a clock seed makes a different
## league each run.
const SUITE_SEED := 2027


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	GameDB.reload()
	_t("_test_catalog")
	_t("_test_rivals")
	_t("_test_dynasty_flags")
	_t("_test_hard_singles")
	_t("_test_second_chance")
	_t("_test_matches")
	_t("_test_streaks_and_rises")
	_t("_test_forge")
	_t("_test_coach_career")
	_t("_test_coach_awards")
	_t("_test_no_double_unlock")
	_t("_test_full_season")
	GameState.reset()
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	print(Ran.line("Achievements", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


# ---------------------------------------------------------------------------
# Context builders (the shape GameState passes to Achievements.check_season)
# ---------------------------------------------------------------------------
## A ladder for `ordered` (top to bottom) with distinct points/percentage.
func _ladder(ordered: Array) -> Dictionary:
	var out := {}
	for i in range(ordered.size()):
		var w := maxi(0, 18 - i)
		var pf := 2000 - i * 10
		var pa := 1500 + i * 10
		out[ordered[i]] = {"code": ordered[i], "p": 20, "w": w, "l": maxi(0, 20 - w),
				"d": 0, "pf": pf, "pa": pa, "pts": 4 * w,
				"pct": 100.0 * pf / pa}
	return out


func _codes(n := 18) -> Array:
	return (GameDB.CLUB_ORDER as Array).slice(0, n)


## `codes` with `code` moved to `pos` (0-based).
func _at(codes: Array, code: String, pos: int) -> Array:
	var out := codes.duplicate()
	out.erase(code)
	out.insert(pos, code)
	return out


func _order(ladder: Dictionary) -> Array:
	var rows: Array = ladder.values()
	rows.sort_custom(func(a, b): return int(a["pts"]) > int(b["pts"]))
	return rows.map(func(r): return str(r["code"]))


## A season's context. `opt`: past ([{year, premier, my_club, finalists,
## ladder_order}...] older entries), entry (merged into this season's roll
## entry), and any top-level key (my_club, slots, matches, gf, yours, forge).
func _ctx(premier: String, runner: String, ladder: Dictionary,
		year := 2026, opt := {}) -> Dictionary:
	var enter := {}
	for code in GameDB.club_order:
		enter[code] = GameDB.enter_year(code)
	var order := _order(ladder)
	var finalists: Array = order.slice(0, 8)
	var my_club := str(opt.get("my_club", ""))
	var entry := {"year": year, "premier": premier, "runner_up": runner, "my_club": my_club,
			"ladder_order": order, "finalists": finalists}
	entry.merge(opt.get("entry", {}), true)
	var roll: Array = (opt.get("past", []) as Array).duplicate()
	roll.append(entry)
	return {"year": year, "premier": premier, "runner_up": runner,
			"ladder": ladder, "finalists": finalists,
			"finals_slots": opt.get("slots", {}), "enter": enter, "my_club": my_club,
			"forge": opt.get("forge", []), "matches": opt.get("matches", []),
			"gf": opt.get("gf", {}), "roll": roll, "yours": opt.get("yours", {})}


## A past roll entry.
func _past(year: int, premier: String, my_club := "", finalists := [], order := []) -> Dictionary:
	return {"year": year, "premier": premier, "my_club": my_club,
			"finalists": finalists, "ladder_order": order}


func _ids(unlocked: Dictionary, ctx: Dictionary) -> Dictionary:
	return Achievements.check_season(unlocked, ctx)


func _m(home: String, away: String, hs: int, away_score: int, tag := "") -> Dictionary:
	return {"home": home, "away": away, "score": [hs, away_score], "tag": tag}


# ---------------------------------------------------------------------------
func _test_catalog() -> void:
	_check(Achievements.DEFINITIONS.size() == 100, "There are 100 achievements")
	var seen_ids := {}
	var seen_names := {}
	var per_club := {}
	for d in Achievements.DEFINITIONS:
		var id := str(d["id"])
		_check(not seen_ids.has(id), "Achievement ids are unique (%s)" % id)
		seen_ids[id] = true
		_check(not seen_names.has(str(d["name"])), "Achievement names are unique (%s)" % str(d["name"]))
		seen_names[str(d["name"])] = true
		per_club[str(d["club"])] = int(per_club.get(str(d["club"]), 0)) + 1
		_check(str(d.get("name", "")) != "" and str(d.get("desc", "")) != "",
				"%s has a name and a description" % id)
		_check(str(d.get("type", "")) != "", "%s has a checkable type" % id)
	_check(int(per_club.get("", 0)) == 56, "56 coach achievements (%d)" % int(per_club.get("", 0)))
	var clubs: Array = GameDB.active_clubs(2030)
	clubs.append("FIT")
	clubs.append(Achievements.FORGE)
	_check(clubs.size() == 22, "22 clubs a career can field")
	for code in clubs:
		_check(int(per_club.get(code, 0)) == 2, "%s has two achievements" % code)
	_check(per_club.size() == 23, "No achievement for a club outside the 22 (%s)" % str(per_club.keys()))
	_check(Achievements.definition("ade_showdown_double") != {}
			and Achievements.definition("ade_first_flag").is_empty()
			and Achievements.definition("gcs_top_four").is_empty(),
			"Scrapped ids are gone; definition() finds the new ones")
	for d in Achievements.DEFINITIONS:
		if not Achievements.is_coach(d):
			_check(str(d["type"]) == "beat_twice" or Achievements.for_club(str(d["club"]))[0]["type"] == "beat_twice",
					"%s: each club pairs a rivalry with a hard one" % str(d["id"]))


func _test_rivals() -> void:
	var ladder := _ladder(_codes())
	for d in Achievements.DEFINITIONS:
		if str(d["type"]) != "beat_twice" or str(d["opp"]) == "PREMIER":
			continue
		var c := str(d["club"])
		var o := str(d["opp"])
		var two := [_m(c, o, 90, 80), _m(o, c, 70, 75)]
		_check(_ids({}, _ctx("GEE", "HAW", ladder, 2030, {"matches": two})).has(str(d["id"])),
				"%s beat %s twice: %s" % [c, o, str(d["id"])])
	var split := [_m("ADE", "PAD", 90, 80), _m("PAD", "ADE", 90, 75)]
	_check(not _ids({}, _ctx("GEE", "HAW", ladder, 2026, {"matches": split})).has("ade_showdown_double"),
			"A split is no double")
	_check(_ids({}, _ctx("GEE", "HAW", ladder, 2026,
			{"matches": split + [_m("ADE", "PAD", 80, 70, "PF1")]})).has("ade_showdown_double"),
			"A finals win is the second win")
	_check(not _ids({}, _ctx("GEE", "HAW", ladder, 2026, {"matches": [split[0]]})).has("ade_showdown_double"),
			"One win is not two")
	var codes := _codes() + ["MYC"]
	var beat_gee := [_m("MYC", "GEE", 90, 80), _m("GEE", "MYC", 70, 75)]
	var fctx := {"matches": beat_gee, "forge": ["MYC"], "past": [_past(2025, "GEE")]}
	_check(_ids({}, _ctx("HAW", "SYD", _ladder(codes), 2026, fctx)).has("forge_giant_killers"),
			"The Forge club beat last season's premiers twice")
	fctx["past"] = [_past(2025, "HAW")]
	_check(not _ids({}, _ctx("HAW", "SYD", _ladder(codes), 2026, fctx)).has("forge_giant_killers"),
			"Beating a club that was not premier is not giant-killing")


func _test_dynasty_flags() -> void:
	var codes := _codes()
	var ladder := _ladder(codes)
	var ade5 := _ladder(_at(codes, "ADE", 4))
	_check(_ids({}, _ctx("ADE", "GEE", ade5, 2026, {"past": [_past(2025, "ADE")]})).has("ade_crows_98"),
			"Back-to-back, the second from fifth")
	_check(not _ids({}, _ctx("ADE", "GEE", _ladder(_at(codes, "ADE", 3)), 2026,
			{"past": [_past(2025, "ADE")]})).has("ade_crows_98"), "From fourth is not the '98 Crows")
	_check(not _ids({}, _ctx("ADE", "GEE", ade5)).has("ade_crows_98"), "One flag is not two")
	_check(not _ids({}, _ctx("GEE", "HAW", ade5, 2026, {"past": [_past(2025, "ADE")]})).has("ade_crows_98"),
			"It unlocks only in a season the club wins the flag")
	_check(_ids({}, _ctx("BRL", "GEE", ladder, 2026, {"past": [_past(2024, "BRL"),
			_past(2025, "BRL")]})).has("brl_three_peat"), "Three in a row")
	_check(not _ids({}, _ctx("BRL", "GEE", ladder, 2026, {"past": [_past(2023, "BRL"),
			_past(2025, "BRL")]})).has("brl_three_peat"), "A gap is no three-peat")
	_check(_ids({}, _ctx("COL", "GEE", ladder, 2026, {"past": [_past(2023, "COL"),
			_past(2024, "COL"), _past(2025, "COL")]})).has("col_four_in_a_row"), "Four in a row")
	_check(_ids({}, _ctx("GEE", "HAW", ladder, 2026, {"past": [_past(2022, "GEE"),
			_past(2024, "GEE")]})).has("gee_three_in_five"), "Three in five")
	_check(not _ids({}, _ctx("GEE", "HAW", ladder, 2026, {"past": [_past(2021, "GEE"),
			_past(2024, "GEE")]})).has("gee_three_in_five"), "2021 is outside the five-season window")
	var mel := [_past(2021, "MEL"), _past(2022, "MEL"), _past(2023, "MEL"), _past(2025, "MEL")]
	_check(_ids({}, _ctx("MEL", "GEE", ladder, 2026, {"past": mel})).has("mel_the_fifties"),
			"Five in six")
	mel[0]["year"] = 2020
	_check(not _ids({}, _ctx("MEL", "GEE", ladder, 2026, {"past": mel})).has("mel_the_fifties"),
			"Five in seven is not")


func _test_hard_singles() -> void:
	var codes := _codes()
	var ladder := _ladder(codes)
	var two_l := [_m("CAR", "GEE", 60, 90), _m("HAW", "CAR", 90, 60), _m("CAR", "SYD", 90, 60)]
	_check(_ids({}, _ctx("CAR", "GEE", ladder, 2026, {"matches": two_l})).has("car_blues_95"),
			"The flag with two losses")
	two_l.append(_m("CAR", "COL", 50, 80, "QF1"))
	_check(not _ids({}, _ctx("CAR", "GEE", ladder, 2026, {"matches": two_l})).has("car_blues_95"),
			"A third loss, in a final, rules it out")
	var ess := _ladder(codes)
	ess["ESS"]["w"] = 21
	_check(_ids({}, _ctx("ESS", "HAW", ess)).has("ess_bombers_2000"), "21 wins and the flag")
	_check(not _ids({}, _ctx("GEE", "HAW", ess)).has("ess_bombers_2000"), "21 wins without the flag")
	var fre_top := _ladder(_at(codes, "FRE", 0))
	_check(_ids({}, _ctx("FRE", "GEE", fre_top)).has("fre_top_and_flag"), "Top and the flag")
	_check(not _ids({}, _ctx("GEE", "FRE", fre_top)).has("fre_top_and_flag"),
			"Top and a lost Grand Final is not enough")
	var gold := {"entry": {"brownlow": [{"id": "p1", "club": "GCS"}]}}
	_check(_ids({}, _ctx("GCS", "GEE", ladder, 2026, gold)).has("gcs_flag_and_brownlow"),
			"The flag and a Suns Brownlow")
	_check(not _ids({}, _ctx("GEE", "GCS", ladder, 2026, gold)).has("gcs_flag_and_brownlow"),
			"A Brownlow without the flag")
	var lost := _past(2025, "GEE")
	lost["runner_up"] = "GWS"
	_check(_ids({}, _ctx("GWS", "HAW", ladder, 2026, {"past": [lost]})).has("gws_redemption"),
			"Lost the Grand Final, won it the next year")
	lost["runner_up"] = "HAW"
	_check(not _ids({}, _ctx("GWS", "HAW", ladder, 2026, {"past": [lost]})).has("gws_redemption"),
			"No Grand Final loss to redeem")
	_check(_ids({}, _ctx("FIT", "GEE", ladder, 1993)).has("fit_flag"), "A Fitzroy flag")
	var tas := GameDB.enter_year("TAS")
	_check(_ids({}, _ctx("TAS", "GEE", ladder, tas + 4)).has("tas_early_flag"),
			"Tasmania's flag in their fifth season")
	_check(not _ids({}, _ctx("TAS", "GEE", ladder, tas + 5)).has("tas_early_flag"),
			"The sixth season is too late")
	_check(_ids({}, _ctx("CANB", "GEE", ladder, GameDB.enter_year("CANB"))).has("canb_early_flag"),
			"Canberra's flag in their first season")
	var nth := []
	for y in range(2022, 2026):
		var e := _past(y, "NTH" if y % 2 == 0 else "GEE")
		e["runner_up"] = "GEE" if y % 2 == 0 else "NTH"
		nth.append(e)
	_check(_ids({}, _ctx("GEE", "NTH", ladder, 2026, {"past": nth})).has("nth_five_grand_finals"),
			"Five Grand Finals running, won or lost")
	nth[1]["runner_up"] = "HAW"
	_check(not _ids({}, _ctx("GEE", "NTH", ladder, 2026, {"past": nth})).has("nth_five_grand_finals"),
			"A missed Grand Final breaks the run")
	var pad_top := _at(codes, "PAD", 0)
	var pad_past := [_past(2024, "GEE", "", [], pad_top), _past(2025, "GEE", "", [], pad_top)]
	_check(_ids({}, _ctx("GEE", "HAW", _ladder(pad_top), 2026, {"past": pad_past})).has("pad_three_minors"),
			"Three minor premierships in a row")
	var syd_in := _at(codes, "SYD", 2)
	var syd := []
	for y in range(2017, 2026):
		syd.append(_past(y, "SYD" if y == 2020 else "GEE", "", syd_in.slice(0, 8)))
	_check(_ids({}, _ctx("GEE", "HAW", _ladder(syd_in), 2026, {"past": syd})).has("syd_bloods"),
			"Ten Septembers with a flag in them")
	syd[3]["premier"] = "GEE"
	_check(not _ids({}, _ctx("GEE", "HAW", _ladder(syd_in), 2026, {"past": syd})).has("syd_bloods"),
			"Ten Septembers without a flag")
	syd[3]["premier"] = "SYD"
	syd[1]["finalists"] = []
	_check(not _ids({}, _ctx("GEE", "HAW", _ladder(syd_in), 2026, {"past": syd})).has("syd_bloods"),
			"A missed September breaks the ten")


func _test_second_chance() -> void:
	var ladder := _ladder(_codes())
	var good := {"L_QF1": "WCE", "W_SF1": "WCE", "W_PF2": "WCE", "W_GF": "WCE"}
	_check(_ids({}, _ctx("WCE", "GEE", ladder, 2026, {"slots": good, "my_club": "WCE"})).has("coach_long_way"),
			"Lose a qualifying final, win the rest: the long way")
	var other := {"L_QF2": "WCE", "W_SF2": "WCE", "W_PF1": "WCE", "W_GF": "WCE"}
	_check(_ids({}, _ctx("WCE", "GEE", ladder, 2026, {"slots": other, "my_club": "WCE"})).has("coach_long_way"),
			"The QF2 loser's path runs through SF2 and PF1")
	var won_qf := {"W_QF1": "WCE", "W_PF1": "WCE", "W_GF": "WCE"}
	_check(not _ids({}, _ctx("WCE", "GEE", ladder, 2026, {"slots": won_qf, "my_club": "WCE"})).has("coach_long_way"),
			"Winning the qualifying final is not the long way")


func _test_matches() -> void:
	var ladder := _ladder(_codes())
	var home := [_m("GEE", "HAW", 100, 50), _m("CAR", "GEE", 100, 50), _m("GEE", "SYD", 80, 60)]
	_check(_ids({}, _ctx("HAW", "SYD", ladder, 2026, {"matches": home, "my_club": "GEE"})).has("coach_home_unbeaten"),
			"Every home game won (an away loss does not count)")
	home.append(_m("GEE", "ADE", 60, 60))
	_check(not _ids({}, _ctx("HAW", "SYD", ladder, 2026, {"matches": home, "my_club": "GEE"})).has("coach_home_unbeaten"),
			"A home draw is not a win")
	var big := [_m("GEE", "HAW", 160, 55)]
	var out := _ids({}, _ctx("HAW", "SYD", ladder, 2026, {"matches": big, "my_club": "GEE"}))
	_check(out.has("coach_ton_up") and out.has("coach_150"), "A 105-point win with 160 on the board")
	_check(not _ids({}, _ctx("HAW", "SYD", ladder, 2026, {"matches": big, "my_club": "HAW"})).has("coach_ton_up"),
			"The losing coach gets nothing for it")
	var beat := []
	for c in _codes():
		if c != "GEE":
			beat.append(_m("GEE", c, 90, 60))
	_check(_ids({}, _ctx("HAW", "SYD", ladder, 2026, {"matches": beat, "my_club": "GEE"})).has("coach_beat_them_all"),
			"Beat every other club")
	beat.pop_back()
	_check(not _ids({}, _ctx("HAW", "SYD", ladder, 2026, {"matches": beat, "my_club": "GEE"})).has("coach_beat_them_all"),
			"One club unbeaten is not all of them")
	var streak := []
	for i in range(10):
		streak.append(_m("GEE", "HAW", 90, 60))
	_check(_ids({}, _ctx("HAW", "SYD", ladder, 2026, {"matches": streak, "my_club": "GEE"})).has("coach_streak_10"),
			"Ten wins in a row")
	streak[5] = _m("GEE", "HAW", 60, 90)
	_check(not _ids({}, _ctx("HAW", "SYD", ladder, 2026, {"matches": streak, "my_club": "GEE"})).has("coach_streak_10"),
			"A loss breaks the run")
	var gf := {"home": "GEE", "away": "HAW", "score": [80, 77]}
	var gctx := {"gf": gf, "my_club": "GEE"}
	_check(_ids({}, _ctx("GEE", "HAW", ladder, 2026, gctx)).has("coach_gf_thriller"), "A three-point Grand Final win")
	gctx["my_club"] = "HAW"
	_check(_ids({}, _ctx("GEE", "HAW", ladder, 2026, gctx)).has("coach_heartbreak"), "A three-point Grand Final loss")
	gctx = {"gf": {"home": "GEE", "away": "HAW", "score": [130, 60]}, "my_club": "GEE"}
	_check(_ids({}, _ctx("GEE", "HAW", ladder, 2026, gctx)).has("coach_gf_romp"), "A 70-point Grand Final win")
	var prelim := [_m("GEE", "HAW", 90, 70, "PF1")]
	var dctx := {"matches": prelim, "my_club": "GEE", "past": [_past(2025, "HAW")]}
	_check(_ids({}, _ctx("SYD", "GEE", ladder, 2026, dctx)).has("coach_beat_premiers"),
			"Beat last season's premiers in a final")
	dctx["matches"] = [_m("GEE", "HAW", 90, 70)]
	_check(not _ids({}, _ctx("SYD", "GEE", ladder, 2026, dctx)).has("coach_beat_premiers"),
			"A home-and-away win over them is not a final")


func _test_streaks_and_rises() -> void:
	var codes := _codes()
	# The coach: last at STK, then the finals at STK.
	var last := _at(codes, "STK", 17)
	var spoon := [_past(2025, "GEE", "STK", [], last)]
	var finals_now := _at(codes, "STK", 5)
	_check(_ids({}, _ctx("GEE", "HAW", _ladder(finals_now), 2026, {"past": spoon, "my_club": "STK"})).has("coach_bottom_to_finals"),
			"Last, then the finals")
	_check(_ids({}, _ctx("STK", "HAW", _ladder(finals_now), 2026, {"past": spoon, "my_club": "STK"})).has("coach_worst_to_first"),
			"Last, then the flag")
	var moved := [_past(2025, "GEE", "CAR", [], last)]
	_check(not _ids({}, _ctx("STK", "HAW", _ladder(finals_now), 2026, {"past": moved, "my_club": "STK"})).has("coach_worst_to_first"),
			"Last at another club does not count")


func _test_forge() -> void:
	var codes := _at(_codes() + ["MYC"], "MYC", 2)
	var past := [_past(2022, "MYC"), _past(2024, "MYC")]
	var out := _ids({}, _ctx("MYC", "GEE", _ladder(codes), 2026, {"forge": ["MYC"], "past": past}))
	_check(out.has("forge_dynasty"), "The Forge club's three flags in five seasons")
	_check(str(out.get("forge_dynasty", "")) == "MYC", "Stored against the created club's code")
	_check(not _ids({}, _ctx("MYC", "GEE", _ladder(codes), 2026, {"past": past})).has("forge_dynasty"),
			"No created club, no Forge achievement")
	_check(Achievements.for_code("MYC", ["MYC"]).size() == 2
			and str(Achievements.for_code("MYC", ["MYC"])[0]["club"]) == Achievements.FORGE,
			"The created club shows the Forge pair")


func _test_coach_career() -> void:
	var ladder := _ladder(_codes())
	var past := []
	for y in range(2016, 2026):
		past.append(_past(y, "GEE", "CAR"))
	var out := _ids({}, _ctx("GEE", "HAW", ladder, 2026, {"past": past, "my_club": "CAR"}))
	_check(out.has("coach_seasons_5") and out.has("coach_seasons_10") and out.has("coach_one_club"),
			"Eleven seasons at Carlton")
	_check(not out.has("coach_seasons_20") and not out.has("coach_three_clubs"), "Not twenty, one club")
	_check(_ids({}, _ctx("GEE", "HAW", ladder, 2026, {"past": [_past(2024, "GEE", "ADE"),
			_past(2025, "GEE", "ESS")], "my_club": "CAR"})).has("coach_three_clubs"), "Three clubs")
	_check(_ids({}, _ctx("GEE", "HAW", ladder, 2026, {"past": [_past(2024, "ADE", "ADE")], "my_club": "GEE"})).has("coach_two_club_flags"),
			"Flags at Adelaide and Geelong")
	var flags := [_past(2022, "GEE", "GEE"), _past(2023, "GEE", "GEE"), _past(2024, "ADE", "ADE"), _past(2025, "ADE", "ADE")]
	out = _ids({}, _ctx("GEE", "HAW", ladder, 2026, {"past": flags, "my_club": "GEE"}))
	_check(out.has("coach_five_flags") and out.has("coach_three_peat") and out.has("coach_back_to_back"),
			"Five flags, the last three in a row (across clubs)")
	_check(not _ids({}, _ctx("GEE", "HAW", ladder, 2026, {"past": [_past(2025, "GEE", "")], "my_club": "GEE"})).has("coach_back_to_back"),
			"A flag the club won before you came is not yours")
	var coachless := _ids({}, _ctx("GEE", "HAW", ladder, 2026)).keys().filter(func(id): return str(id).begins_with("coach_"))
	_check(coachless.is_empty(), "No coach, no coach achievement (%s)" % str(coachless))


func _test_coach_awards() -> void:
	var ladder := _ladder(_codes())
	var entry := {"brownlow": [{"id": "p1", "club": "GEE"}], "coleman": [{"id": "p2", "club": "GEE", "goals": 101}],
			"rising_star": [{"id": "p3", "club": "GEE"}], "my_aa": ["p1", "p2", "p3", "p4", "p5"],
			"my_bf": [{"id": "p1"}], "premier_side": ["p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "p9", "p10"]}
	var yours := {"p1": [2020, 34, "national"], "p2": [2021, 3, "national"], "p3": [2022, 0, "rookie"],
			"p4": [2020, 1, "national"], "p5": [2020, 2, "national"], "p6": [2020, 2, "national"],
			"p7": [2020, 2, "national"], "p8": [2020, 2, "national"], "p9": [2020, 2, "national"], "p10": [2020, 2, "national"]}
	var out := _ids({}, _ctx("GEE", "HAW", ladder, 2026, {"my_club": "GEE", "entry": entry, "yours": yours}))
	for id in ["coach_brownlow", "coach_faith_repaid", "coach_late_pick_brownlow", "coach_coleman",
			"coach_coleman_drafted", "coach_century", "coach_rising_star", "coach_rising_star_drafted",
			"coach_all_australian", "coach_five_all_australians", "coach_medal_sweep",
			"coach_coleman_flag", "coach_home_grown", "coach_rookie_aa", "coach_bf_late_pick"]:
		_check(out.has(id), "%s unlocks" % id)
	var none := _ids({}, _ctx("GEE", "HAW", ladder, 2026, {"my_club": "GEE", "entry": entry}))
	_check(none.has("coach_brownlow") and not none.has("coach_faith_repaid") and not none.has("coach_home_grown"),
			"A medallist you did not draft is not faith repaid")
	yours["p1"] = [2020, 12, "national"]
	_check(not _ids({}, _ctx("GEE", "HAW", ladder, 2026, {"my_club": "GEE", "entry": entry, "yours": yours})).has("coach_late_pick_brownlow"),
			"Pick 12 is not the steal")
	var dual := {"past": [{"year": 2024, "my_club": "GEE", "brownlow": [{"id": "p1", "club": "GEE"}]}],
			"my_club": "GEE", "entry": entry}
	_check(_ids({}, _ctx("HAW", "GEE", ladder, 2026, dual)).has("coach_dual_brownlow"), "A second Brownlow")
	var norm := {"my_club": "GEE", "entry": {"norm_smith": [{"id": "p1", "club": "GEE"}]}}
	_check(_ids({}, _ctx("GEE", "HAW", ladder, 2026, norm)).has("coach_norm_smith"), "Norm Smith in a flag")
	_check(not _ids({}, _ctx("HAW", "GEE", ladder, 2026, norm)).has("coach_norm_smith"), "Norm Smith in a loss")


func _test_no_double_unlock() -> void:
	var ctx := _ctx("FIT", "GEE", _ladder(_codes()), 1993)
	_check(_ids({}, ctx).has("fit_flag") and _ids({"fit_flag": {"year": 1990}}, ctx).get("fit_flag", "") == "",
			"An unlocked achievement is never re-reported")


func _test_full_season() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var guard := 0
	while not GameState.season.is_season_over() and guard < 40:
		GameState.advance()
		guard += 1
	_check(GameState.season.is_season_over(), "The season completes")
	_check(GameState.achievements is Dictionary, "Achievements are a dictionary of unlocks")
	var unknown := []
	var unstamped := []
	for id in GameState.achievements:
		if Achievements.definition(str(id)).is_empty():
			unknown.append(str(id))
		var got: Dictionary = GameState.achievements[id]
		if int(got.get("year", 0)) != GameDB.START_YEAR or str(got.get("club", "")) == "":
			unstamped.append(str(id))
	_check(unknown.is_empty(), "Only catalogued achievements unlock (%d unlocked; unknown: %s)" % [GameState.achievements.size(), str(unknown)])
	_check(unstamped.is_empty(), "Each unlock is stamped with its season and club (%s)" % str(unstamped))
	var entry: Dictionary = GameState.honour_roll[-1]
	_check((entry.get("ladder_order", []) as Array).size() == GameState.season.ladder.size()
			and not (entry.get("finalists", []) as Array).is_empty(),
			"The honour roll keeps the final ladder and the finalists")
	# The save drops ids from outside the catalogue (the first twenty).
	GameState.achievements["ade_first_flag"] = {"year": 2025}
	_check(GameState.save_career(), "The career saves")
	GameState.achievements.erase("ade_first_flag")
	var before := GameState.achievements.duplicate(true)
	_check(GameState.load_career(), "The career loads")
	_check(GameState.achievements == before, "Achievements survive a save and load; scrapped ids are dropped")
