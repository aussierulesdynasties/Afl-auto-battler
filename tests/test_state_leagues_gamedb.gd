extends RefCounted
## GameDB loads the state leagues (TODO row 128, step 2): the 2026 dataset's
## state_leagues folder gives GameDB.state_leagues, state_clubs, state_players
## and state_links beside the AFL. Checks the counts, that the AFL load is
## exactly as without the state leagues (players, ratings, aliases, baseline,
## one reload each), that a dataset without the key loads none, the club
## lookups for state codes, the Player names switch on state men, and the
## mature-age recruits' VFL clubs read from the data (Aspley gone).
## Run through tests/run_state_leagues_gamedb_tests.gd. Seeded by design: it
## loads data and plays no match.

var failures: Array[String] = []
var checks := 0

const CLUBS := {"VFL": 22, "SANFL": 10, "WAFL": 10}
const PLAYERS := 798 + 554 + 1155
const LINKS := 511
const NO_STATE := "2026_no_state_test"


func run() -> void:
	failures.clear()
	checks = 0
	_t("_test_loads_three_leagues")
	_t("_test_afl_unchanged")
	_t("_test_no_key_no_leagues")
	_t("_test_club_lookups")
	_t("_test_name_switch")
	_t("_test_mature_recruit_clubs")
	Datasets.remove(NO_STATE)
	GameDB.reload()
	print(Ran.line("State leagues in GameDB", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _test_loads_three_leagues() -> void:
	GameDB.reload()
	_check(GameDB.state_leagues.size() == 3 and GameDB.state_clubs.size() == 42,
			"The 2026 load has 3 state leagues and 42 clubs (%d, %d)"
			% [GameDB.state_leagues.size(), GameDB.state_clubs.size()])
	for id in CLUBS:
		var codes := GameDB.league_clubs(id)
		_check(codes.size() == int(CLUBS[id]) and int(GameDB.state_leagues[id]["clubs"]) == codes.size(),
				"%s lists its %d clubs (%d)" % [id, CLUBS[id], codes.size()])
		for code in codes:
			_check(str(GameDB.state_clubs[code]["league"]) == id, "%s is a %s club" % [code, id])
	_check(GameDB.state_players.size() == PLAYERS and GameDB.state_links.size() == LINKS,
			"%d state-only men and %d AFL links (%d, %d)"
			% [PLAYERS, LINKS, GameDB.state_players.size(), GameDB.state_links.size()])
	var by_club := 0
	var bad: Array = []
	var ids := {}
	for p in GameDB.state_players:
		ids[p["id"]] = true
		if float(p["age"]) < 14.0 or float(p["age"]) > 45.0 or float(p["height_cm"]) < 150.0 \
				or not GameDB.is_state_club(str(p["club"])) or GameDB.player_by_id(str(p["id"])) != null:
			bad.append(str(p["id"]))
	for code in GameDB.state_clubs:
		by_club += GameDB.state_list(code).size()
	_check(bad.is_empty(), "Every state man has an age, a height and a state club, and no AFL id (%d: %s)"
			% [bad.size(), str(bad.slice(0, 3))])
	_check(ids.size() == PLAYERS and by_club == PLAYERS, "Every state man has his own id and one list (%d, %d)"
			% [ids.size(), by_club])
	var vfl: Dictionary = GameDB.state_list("BOX")[0]
	_check(vfl["stat_cols"] == ["gm", "gl", "bh", "di", "ki", "hb", "mk", "tk", "ho"] and not vfl.has("cl"),
			"A VFL man carries only the nine stats the VFL records (%s)" % str(vfl["stat_cols"]))
	var afl_ids := {}
	for q in GameDB.players + GameDB.list_additions:
		afl_ids[str(q["id"])] = true
	var bad_links: Array = []
	for row in GameDB.state_links:
		if not afl_ids.has(str(row["afl_id"])) or not GameDB.is_state_club(str(row["state_club"])):
			bad_links.append(str(row["afl_id"]))
	_check(bad_links.is_empty(), "Every link joins an AFL-listed man (a list or a list addition) to a state club (%s)" % str(bad_links.slice(0, 3)))


## The AFL side of a load, everything a career is built from.
func _afl_digest() -> String:
	return "%s|%s|%s|%s|%s|%s|%s|%s" % [str(GameDB.players), str(GameDB.draftees), str(GameDB.list_additions),
			str(GameDB.baseline_overall), str(GameDB.baseline_spread), str(GameDB.club_order),
			str(GameDB.clubs.keys()), str(GameDB._alias_next)]


func _test_afl_unchanged() -> void:
	var row := Datasets.get_set("2026").duplicate()
	row.erase(Datasets.STATE_LEAGUES_KEY)
	Datasets.add(NO_STATE, row)
	var r0 := GameDB.reloads
	GameDB.reload(NO_STATE)
	var without := _afl_digest()
	var pristine_without := GameDB.pristine
	GameDB.reload()
	var with := _afl_digest()
	_check(GameDB.reloads == r0 + 2, "Each load is one reload (%d to %d)" % [r0, GameDB.reloads])
	_check(without == with, "The AFL lists, ratings, aliases, draft class and baseline are exactly as without the state leagues (%s vs %s)"
			% [without.md5_text(), with.md5_text()])
	_check(GameDB.pristine == pristine_without and GameDB.pristine, "The load is still pristine")
	_check(GameDB.players.size() == 669 and GameDB.club_order == GameDB.CLUB_ORDER,
			"The AFL keeps its 669 players and its club order (%d)" % GameDB.players.size())


func _test_no_key_no_leagues() -> void:
	_check(not Datasets.get_set("1990").has(Datasets.STATE_LEAGUES_KEY), "The 1990 set names no state leagues")
	GameDB.reload(NO_STATE)
	_check(GameDB.state_leagues.is_empty() and GameDB.state_clubs.is_empty() and GameDB.state_players.is_empty()
			and GameDB.state_links.is_empty() and GameDB.club("BOX").is_empty() and GameDB.club_name("BOX") == "BOX",
			"A set without state leagues loads none, and a state code is unknown")
	_check(Prospects.state_league_clubs("VICM").is_empty() and Prospects.state_league_clubs("TAS").size() == 5,
			"Without them no VFL club is named for a recruit; the TSL still is")
	if Datasets.ready("1990"):
		GameDB.reload("1990")
		_check(GameDB.state_clubs.is_empty(), "The 1990 load has no state clubs")
	GameDB.reload()


func _test_club_lookups() -> void:
	GameDB.reload()
	_check(GameDB.club_name("BOX") == "Box Hill Hawks" and GameDB.club_short("BOX") == "Box Hill"
			and GameDB.club_name("WWT") == "Woodville-West Torrens" and GameDB.club_name("PEL") == "Peel Thunder",
			"State codes name their clubs")
	var cols := GameDB.club_colours("CLA")
	_check(cols.size() == 3 and cols[0] is Color and cols[0] == Color.html("#0C2340") and cols[2] == cols[1],
			"A state club's colours are Colors; with no third colour it tints with its second")
	_check(GameDB.club("ADE") == GameDB.clubs["ADE"] and GameDB.club_name("ADE") == str(GameDB.clubs["ADE"]["name"]),
			"AFL codes still answer as the AFL club")
	var overlap: Array = []
	for code in GameDB.state_clubs:
		if GameDB.clubs.has(code):
			overlap.append(code)
	_check(overlap.is_empty(), "No state code is an AFL or past club's code (%s)" % str(overlap))
	var sides := {}
	for afl in GameDB.CLUB_ORDER.slice(0, 18):
		var side := GameDB.state_side_of(str(afl))
		_check(side != "" and str(GameDB.state_clubs[side]["afl_club"]) == afl,
				"%s fields a state side (%s)" % [afl, side])
		sides[side] = true
	_check(sides.size() == 18, "The 18 AFL clubs field 18 different sides (%d)" % sides.size())
	_check(GameDB.state_side_of("TAS") == "" and GameDB.state_side_of("CANB") == "",
			"Tasmania and Canberra field none in 2026")


func _test_name_switch() -> void:
	GameDB.reload()
	var was: bool = GameState.show_real_names
	var p: Dictionary = GameDB.state_list("WIL")[0]
	GameState.show_real_names = true
	var real_shown := GameDB.player_display_name(p)
	var real_last := GameDB.card_surname(p)
	GameState.show_real_names = false
	var alias_shown := GameDB.player_display_name(p)
	GameState.show_real_names = was
	_check(real_shown == "%s %s" % [p["first"], p["last"]] and real_last == str(p["last"]),
			"Real names on: a state man shows his own name (%s)" % real_shown)
	_check(alias_shown != real_shown and alias_shown != "" and alias_shown == str(p["generic_name"]),
			"Real names off: he shows a made-up name (%s)" % alias_shown)
	var afl_real := {}
	var labels := {}
	var clash: Array = []
	for q in GameDB.players + GameDB.draftees:
		afl_real[str(q.get("real_name", ""))] = true
		labels[str(q.get("generic_name", ""))] = true
	for q in GameDB.state_players:
		var label := str(q["generic_name"])
		if label == "" or labels.has(label) or afl_real.has(label):
			clash.append(label)
		labels[label] = true
	_check(clash.is_empty(), "Every state man's made-up name is his own and no real AFL name (%d: %s)"
			% [clash.size(), str(clash.slice(0, 3))])


func _test_mature_recruit_clubs() -> void:
	GameDB.reload()
	_check(Prospects.state_league_clubs("QLD") == [["Southport", "VFL"]],
			"Queensland's VFL club is Southport alone: Aspley left the VFL (%s)" % str(Prospects.state_league_clubs("QLD")))
	var vicm := Prospects.state_league_clubs("VICM")
	var all_vfl := vicm.size() == 6
	for c in vicm + Prospects.state_league_clubs("VICC"):
		all_vfl = all_vfl and str(c[1]) == "VFL" and GameDB.state_clubs.values().any(func(r): return r["name"] == c[0])
	_check(all_vfl, "Victoria's VFL clubs are named from the data (%s)" % str(vicm))
	_check(Prospects.state_league_clubs("NSW").size() == 2 and str(Prospects.state_league_clubs("TAS")[0][1]) == "TSL",
			"AFL Sydney and the TSL stay as origins")
