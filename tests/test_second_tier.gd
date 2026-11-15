extends RefCounted
## The real second tier by season (Legacy mode, TODO row 142, L7): a Legacy
## start lays each season's leagues and sides below the AFL over the state
## leagues (SecondTier, data/legacy/second_tier/), and a 2026 career is exactly
## as before. A seeded 1990 campaign rolls on and every season start to 2026
## is checked against the data, through every change of shape.
## Run through tests/run_second_tier_tests.gd.
## Seeded by design: the campaign rolls a season on (GameState._start_next_season)
## without playing a match.

var failures: Array[String] = []
var checks := 0

const SEED := 1990


func run() -> void:
	failures.clear()
	checks = 0
	_t("_test_today_unchanged")
	_t("_test_data_reads")
	_t("_test_campaign_rolls_through_the_shapes")
	GameState.reset()
	GameState.delete_saved_career()
	GameDB.reload()
	print(Ran.line("Second tier", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


## A league's sides in a season as sorted [code, kind, afl clubs] triples.
func _sides(year: int, league: String) -> Array:
	var t: SecondTier = GameDB.second_tier
	var rows := t.sides_in(year)
	var out := []
	for code in t.shape(year).get(league, {}).get("clubs", []):
		var s: Dictionary = rows[code]
		out.append("%s %s %s" % [code, s["kind"], "|".join(s["afl_clubs"])])
	out.sort()
	return out


## The state leagues as GameDB holds them now, against the data for `year`.
func _matches_data(year: int) -> String:
	var shape: Dictionary = GameDB.second_tier.shape(year)
	if shape.keys().size() != GameDB.state_leagues.size():
		return "leagues %s, data %s" % [str(GameDB.state_leagues.keys()), str(shape.keys())]
	var n := 0
	for id in shape:
		if not GameDB.state_leagues.has(id) or GameDB.league_clubs(id) != shape[id]["clubs"]:
			return "%s differs" % id
		n += (shape[id]["clubs"] as Array).size()
	if n != GameDB.state_clubs.size() or not GameDB.state_players.is_empty():
		return "%d clubs, data %d; %d players" % [GameDB.state_clubs.size(), n, GameDB.state_players.size()]
	for code in GameDB.active_clubs(year):
		var at := GameDB.second_tier_of(code, year)
		if at.is_empty():
			return "%s has no second tier" % code
		if str(at["code"]) != "" and GameDB.state_side_of(code) == "":
			return "%s's side %s is not a state club" % [code, at["code"]]
	return ""


# ---------------------------------------------------------------------------
func _test_today_unchanged() -> void:
	GameDB.reload()
	var leagues := GameDB.state_leagues.duplicate(true)
	var n_clubs := GameDB.state_clubs.size()
	var n_players := GameDB.state_players.size()
	_check(GameDB.second_tier.is_empty() and not Datasets.get_set("2026").has(Datasets.SECOND_TIER_KEY),
			"The 2026 set has no second tier by season")
	for y in [2027, 2031, 2040]:
		GameDB.apply_era(y)
	_check(GameDB.state_leagues == leagues and GameDB.state_clubs.size() == n_clubs
			and GameDB.state_players.size() == n_players and GameDB.second_tier_year == 0,
			"Season starts leave today's VFL, SANFL and WAFL as loaded (%d clubs, %d players)"
			% [GameDB.state_clubs.size(), GameDB.state_players.size()])
	_check(GameDB.state_side_of("HAW") == "BOX" and GameDB.state_side_of("ADE") == "ADR",
			"Today's sides still answer for their AFL clubs")


func _test_data_reads() -> void:
	GameDB.reload("1990")
	var t: SecondTier = GameDB.second_tier
	_check(not t.is_empty(), "The 1990 set reads its second tier")
	_check(_matches_data(1990) == "" and GameDB.second_tier_year == 1990,
			"A 1990 load holds 1990's shape: %s" % _matches_data(1990))
	# 2026 in the data is today's VFL, SANFL and WAFL, side for side.
	GameDB.reload()
	var today := {}
	for id in ["VFL", "SANFL", "WAFL"]:
		var rows := []
		for code in GameDB.league_clubs(id):
			var c: Dictionary = GameDB.state_clubs[code]
			rows.append("%s %s %s" % [code, c["kind"], c["afl_club"]])
		rows.sort()
		today[id] = rows
	GameDB.reload("1990")
	for id in today:
		_check(_sides(2026, id) == today[id], "The data's 2026 %s is today's (%d, %d sides)"
				% [id, _sides(2026, id).size(), (today[id] as Array).size()])
	_check(t.shape(2026).keys().size() == 3, "2026 has three leagues below the AFL (%s)" % str(t.shape(2026).keys()))
	_check(t.shape(2040) == t.shape(2026), "A season past the data keeps 2026's shape")


## A seeded 1990 career's seasons from 1990 to 2026: each season start holds
## that season's shape, through the AFL Reserves' end, the VFL's alignments,
## the cancelled 2020 VFL, the NEAFL years and today's leagues. A save and
## load restores the season's shape. The career rolls on once for real (1990
## to 1991): a rollover lays the new season's shape with
## GameDB.apply_era(next year) (GameState._start_next_season), so every later
## season start is that same call, without 35 more off-seasons.
func _test_campaign_rolls_through_the_shapes() -> void:
	if not Datasets.ready("1990"):
		_check(false, "The 1990 start's files ship")
		return
	seed(SEED)
	GameState.reset("1990")
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var t: SecondTier = GameDB.second_tier
	var bad: Array = []
	var held := {}
	for y in range(1990, 2027):
		if y == 1991:
			GameState._ensure_league_lists()
			GameState._start_next_season(1991, 0)
			_check(GameState.season_year == 1991, "The 1990 career rolls on into 1991 (%d)" % GameState.season_year)
		elif y > 1991:
			GameDB.apply_era(y)
		var why := _matches_data(y)
		if why != "" or GameDB.second_tier_year != y:
			bad.append("%d: %s (shape of %d)" % [y, why, GameDB.second_tier_year])
		held[y] = GameDB.state_leagues.keys()
		if y == 1991:
			GameState.save_career()
			GameDB.apply_era(1990)
			GameState.load_career()
			_check(GameState.season_year == 1991 and GameDB.second_tier_year == 1991 and _matches_data(1991) == "",
					"A 1991 save loads back into 1991's shape (%d, %s)" % [GameDB.second_tier_year, _matches_data(1991)])
	_check(bad.is_empty(), "Every season from 1990 to 2026 starts in its own shape (%d: %s)" % [bad.size(), str(bad.slice(0, 3))])
	_check(held.size() == 37, "The campaign reached 2026 (%d seasons)" % held.size())
	if held.size() < 37:
		return
	# The changes of shape, season by season.
	_check(held[1990].has("AFLR") and held[1990].has("VFA") and not held[1990].has("VFL"),
			"1990: the AFL Reserves and the VFA (%s)" % str(held[1990]))
	_check(held[1999].has("AFLR") and not held[2000].has("AFLR") and held[2000].has("VFL"),
			"The AFL Reserves' last season is 1999; in 2000 the Victorian clubs' players go to the VFL")
	_check(not held[2020].has("VFL") and held[2019].has("VFL") and held[2021].has("VFL"),
			"No VFL in 2020")
	_check(str(t.of_club("HAW", 2020)["kind"]) == "none" and str(t.of_club("HAW", 2021)["code"]) == "BOX",
			"Hawthorn's players have no second tier in 2020 and Box Hill again in 2021")
	_check(held[2011].has("NEAFL") and held[2019].has("NEAFL") and not held[2020].has("NEAFL") and not held[2010].has("NEAFL"),
			"The NEAFL runs 2011 to 2019")
	_check(str(t.of_club("ADE", 1991)["kind"]) == "host" and str(t.of_club("ADE", 2014)["kind"]) == "reserves",
			"Adelaide's players go back to the SANFL clubs in 1991 and to the Crows' own side by 2014")
	_check(not held[1995].has("QAFL") and str(t.of_club("BRL", 1995)["league"]) == "QAFL"
			and str(t.of_club("BRL", 1995)["code"]) == "",
			"1995: the Bears' players go back to the QAFL clubs, a league the data does not lay out (%s)" % str(held[1995]))
	_check(_sides(2026, "VFL") == _sides(2040, "VFL"), "Past 2026 the shape holds")
	var mine := GameDB.league_clubs("VFL").duplicate()
	mine.sort()
	GameDB.reload()
	var today := GameDB.league_clubs("VFL").duplicate()
	today.sort()
	_check(mine == today, "The campaign's 2026 VFL is today's clubs (%d, %d)" % [mine.size(), today.size()])
