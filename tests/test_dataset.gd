extends RefCounted
## The career's dataset (Legacy mode, TODO row 142, step P1): GameDB loads the
## set a career chose, a save keeps it, and the 2026 career behaves exactly as
## it did before the dataset became a choice. The golden fingerprints below
## were taken on main before the change (2026-11-11) and must not move.
## Run through tests/run_dataset_tests.gd.

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 1990

## md5 of the 2026 load, of a seeded real-lists opening, and of a seeded
## three-round redraft season, as main produced them before P1. The load and
## real-lists prints moved with the 2026-11-12 real-list data (list types,
## departures, signings of delisted players and the list each joined); the
## season print did not. The real-lists print moved again that day with the
## 44 rule (RookieList.add_block): West Coast, at 43 of the 44, lists one of
## its three tied prospects and passes its picks, so the opening draft differs.
const GOLDEN_LOAD := "9baf6f36b146d2bfafd65e07b3235c55"
const GOLDEN_REAL := "6b9d20ef93eea2ce95f0a6d936f19727"
## A played match's floating point differs between Windows and Linux builds of
## Godot, so the season has one fingerprint per platform; each was taken on
## main before the change (Linux: run_on_github run 43024085570). The own
## plan (CustomPlan) redrew the season: Linux from Tests run 43083470206; the
## Windows print still predates it and is refreshed on the next local run.
## Result keys added after the golden was taken that record who earned a
## call's credit, not what happened (row 144). "impact" and "plan_traits" were
## already in main's results, so they stay in the hash. "breeze_side" (the
## match-day look, 2026-11-12) records which side had the breeze first, a
## number the match already drew from its seed before the first bounce, so the
## ground's flags can be drawn from a saved result: with it left out the
## season's print is the one taken before it was written down, which is the
## proof that writing it down changed no result and no draw.
const BOOKKEEPING_KEYS := ["impact_by", "breeze_side"]
const GOLDEN_SEASON := {"Windows": "05a96ea659dcfe349e9afec75b01b45a", "Linux": "9c00f9caf199debd6cc6a20325ba8cba"}

## A small league standing in for a legacy set until the 1990 files ship:
## 42 real players re-dated to a 1989 data season, a 1990 first season, and
## no draft class, history, origin, additions, moves or overrides.
const FIXTURE := "test_1989"
const FIXTURE_ROW := {"data_season": 1989, "start_year": 1990, "start_date": "1990-03-01",
		"players": "res://tests/fixtures/dataset_1989_players.csv"}


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	GameDB.reload()
	_t("_test_golden_load")
	_t("_test_golden_real_lists")
	_t("_test_golden_season")
	_t("_test_the_2026_row")
	_t("_test_ladder_of")
	_t("_test_record_weights")
	_t("_test_club_years_today")
	_t("_test_real_1990")
	Datasets.add(FIXTURE, FIXTURE_ROW)
	_t("_test_fixture_load")
	_t("_test_back_to_2026")
	_t("_test_save_keeps_dataset")
	_t("_test_old_and_unknown_saves")
	_t("_test_club_years_1990")
	_t("_test_ground_names_1990")
	_t("_test_guernseys_by_year")
	Datasets.remove(FIXTURE)
	GameState.replay_seed = 0
	GameState.reset()
	print(Ran.line("Dataset", self))


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
# Fingerprints
# ---------------------------------------------------------------------------
static func _player_line(p: Dictionary) -> String:
	var attr: Dictionary = p.get("attr", {})
	var keys := attr.keys()
	keys.sort()
	var a := PackedStringArray()
	for k in keys:
		a.append("%s=%.4f" % [k, float(attr[k])])
	return "%s|%s|%s|%d|%.4f|%d|%d|%s|%s|%d|%s|%s|%s|%s|%s" % [str(p.get("id", "")), str(p.get("real_name", "")),
			str(p.get("club", "")), int(p.get("num", 0)), float(p.get("age", 0.0)), int(p.get("overall", 0)),
			int(p.get("potential", 0)), str(p.get("role", "")), str(p.get("role2", "")), int(p.get("draft_year", 0)),
			str(p.get("rated_on_record", false)), str(p.get("generic_name", "")), str(p.get("home_state", "")),
			str(p.get("career", "")), ",".join(a)]


static func _lists_line(lists: Dictionary) -> String:
	var codes := lists.keys()
	codes.sort()
	var out := PackedStringArray()
	for code in codes:
		for p in lists[code] as Array:
			out.append("%s:%s|%d|%d|%d|%s" % [str(code), _player_line(p), int(p.get("contract_years", 0)),
					int(p.get("drafted_year", 0)), int(p.get("draft_pick", 0)), str(p.get("drafted_type", ""))])
	return "\n".join(out)


func _load_print() -> String:
	var out := PackedStringArray()
	out.append("%d|%d|%s|%.6f|%.6f" % [GameDB.DATA_SEASON, GameDB.START_YEAR, GameDB.START_DATE,
			GameDB.baseline_overall, GameDB.baseline_spread])
	for p in GameDB.players + GameDB.list_additions + GameDB.draftees:
		out.append(_player_line(p))
	var codes: Array = GameDB.clubs.keys()
	codes.sort()
	for code in codes:
		var c: Dictionary = GameDB.clubs[code]
		# pattern3 (L9's anchor colour) came after this golden; today's kits repeat
		# pattern2 in it, which _test_guernseys_by_year checks.
		var g := GameDB.club_guernsey(code)
		g.erase("pattern3")
		out.append("%s|%s|%s|%s|%d|%s" % [code, str(c.get("name", "")), str(c.get("short", "")),
				str(c.get("ground", "")), int(c.get("enter", 0)), str(g)])
	out.append(str(GameDB.club_order))
	out.append(str(GameDB.active_clubs(GameDB.START_YEAR)))
	var dk: Array = GameDB.departures.keys()
	dk.sort()
	for k in dk:
		out.append("dep|%s|%s" % [k, str(GameDB.departures[k])])
	var mk: Array = GameDB.club_moves.keys()
	mk.sort()
	for k in mk:
		out.append("move|%s|%s" % [k, str(GameDB.club_moves[k])])
	out.append(str(_ladder_2026()))
	return "\n".join(out)


func _ladder_2026() -> Array:
	return GameDB.ladder_of(2026)


func _real_print() -> String:
	GameState.reset()
	GameState.replay_seed = 4242
	GameState.career_seed = 4242
	GameState.begin_real_lists()
	GameState.choose_real_club("GEE")
	var guard := 0
	while not GameState.draft.is_finished() and guard < 400:
		guard += 1
		if GameState.draft.is_user_turn():
			var board: Array = GameState.draft.board("", "", "", "overall", true)
			if board.is_empty() or not GameState.draft.pick(board[0]):
				break
	var picks := PackedStringArray()
	for h in GameState.draft.pick_history:
		picks.append("%s|%s|%d" % [str(h.get("club", "")), str(h.get("player_id", "")), int(h.get("pick", 0))])
	GameState.finish_intake_draft()
	var out := PackedStringArray()
	out.append("%d|%s|%d" % [GameState.season_year, GameState.my_club, GameState.free_agents.size()])
	out.append("\n".join(picks))
	out.append(_lists_line(GameState.season.lists))
	return "\n".join(out)


func _season_print() -> String:
	GameState.reset()
	GameState.career_seed = SUITE_SEED
	GameState.replay_seed = SUITE_SEED
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	for i in range(3):
		GameState.advance()
	var out := PackedStringArray()
	out.append("%d|%d" % [GameState.season_year, GameState.season.round_index])
	for row in GameState.season.ladder_sorted():
		out.append(JSON.stringify(row, "", true))
	# Who earned each call's credit is bookkeeping, not play: leave it out so
	# the hash still proves the season plays the same. Results are one array
	# of match results per round.
	var played: Array = []
	for rnd in GameState.season.results:
		var games: Array = []
		for r in rnd:
			var c = r.duplicate(true) if r is Dictionary else r
			if c is Dictionary:
				for k in BOOKKEEPING_KEYS:
					(c as Dictionary).erase(k)
			games.append(c)
		played.append(games)
	out.append(JSON.stringify(played, "", true))
	return "\n".join(out)


func _golden(name: String, text: String, want: String) -> void:
	var got := text.md5_text()
	print("GOLDEN %s=%s (%d chars)" % [name, got, text.length()])
	_check(want != "" and got == want, "The 2026 %s is exactly as before the dataset choice (%s, want %s)" % [name, got, want])


# ---------------------------------------------------------------------------
# Golden: the 2026 career is unchanged
# ---------------------------------------------------------------------------
func _test_golden_load() -> void:
	GameDB.reload()
	var a := _load_print()
	GameDB.reload()
	_check(_load_print() == a, "Two 2026 loads in a row are identical")
	_golden("load", a, GOLDEN_LOAD)


func _test_golden_real_lists() -> void:
	var a := _real_print()
	var b := _real_print()
	_check(a == b, "A seeded real-lists opening plays the same twice")
	_golden("real lists opening", a, GOLDEN_REAL)


func _test_golden_season() -> void:
	var a := _season_print()
	var b := _season_print()
	_check(a == b, "A seeded season's first three rounds play the same twice")
	_golden("seeded season", a, str(GOLDEN_SEASON.get(OS.get_name(), "")))


# ---------------------------------------------------------------------------
# The dataset is the career's choice
# ---------------------------------------------------------------------------
func _test_the_2026_row() -> void:
	GameDB.reload()
	_check(GameDB.dataset_id == "2026" and Datasets.DEFAULT == "2026" and GameDB.DATA_SEASON == 2026
			and GameDB.START_YEAR == 2027 and GameDB.START_DATE == "2027-03-01",
			"Today's start is the 2026 set: 2026 data, a 2027 first season")
	var row := Datasets.get_set("2026")
	var missing := PackedStringArray()
	for key in Datasets.FILE_KEYS:
		if not FileAccess.file_exists(str(row.get(key, ""))):
			missing.append(key)
	_check(missing.is_empty(), "The 2026 set names a shipped file for every key (missing: %s)" % ", ".join(missing))
	_check(Datasets.ready("2026") and Datasets.ready_ids().has("2026") and not Datasets.ready("nope")
			and Datasets.get_set("nope").is_empty(), "Only a known set with its players file can start a career")
	# The 1990 set is declared for the legacy start; it starts nothing until its players ship.
	_check(int(Datasets.get_set("1990").get("data_season", 0)) == 1989
			and int(Datasets.get_set("1990").get("start_year", 0)) == 1990
			and Datasets.ready("1990") == FileAccess.file_exists(Datasets.file("1990", "players")),
			"The 1990 start rates its lists on 1989 and plays 1990, once its players file ships")
	var reloads := GameDB.reloads
	var players := GameDB.players.size()
	GameDB.reload("nope")
	_check(GameDB.reloads == reloads and GameDB.dataset_id == "2026" and GameDB.players.size() == players,
			"An unknown set loads nothing and the last load stays (%d to %d loads, %d to %d players)"
			% [reloads, GameDB.reloads, players, GameDB.players.size()])


func _test_ladder_of() -> void:
	var l26 := GameDB.ladder_of(2026)
	_check(l26.size() == 18, "2026 reads the dataset's own ladder (%d rows)" % l26.size())
	# Any other season reads its decade's file, filtered to the year.
	var l15 := GameDB.ladder_of(2015)
	var premier := ""
	for r in l15:
		if str(r.get("finals", "")) == "premiers":
			premier = str(r["club"])
	_check(l15.size() == 18 and premier == "HAW",
			"2015 reads the 2010s file: 18 clubs, Hawthorn premiers (%d rows, %s)" % [l15.size(), premier])
	_check(GameDB.ladder_of(1789).is_empty(), "A season with no data has no ladder")


## The record weights count back from the data season: the same three
## seasons weigh the same in 1989 as in 2026.
func _test_record_weights() -> void:
	var p26 := {"gm": 6.0, "overall": 60, "history": [[2025, 80, 20], [2024, 78, 18], [2023, 90, 22]]}
	var p89 := {"gm": 6.0, "overall": 60, "history": [[1988, 80, 20], [1987, 78, 18], [1986, 90, 22]]}
	var a := Ratings.record_level(p26, 2026)
	var b := Ratings.record_level(p89, 1989)
	_check(a > 0.0 and is_equal_approx(a, b),
			"The same three seasons weigh the same counted back from 1989 as from 2026 (%.3f, %.3f)" % [a, b])
	_check(is_equal_approx(Ratings.record_level(p26), a), "Without a season named, the record counts back from 2026")
	_check(not is_equal_approx(Ratings.record_level(p89, 2026), a),
			"Seasons from another era weigh nothing in his record")


func _test_fixture_load() -> void:
	GameDB.reload(FIXTURE)
	_check(GameDB.dataset_id == FIXTURE and GameDB.DATA_SEASON == 1989 and GameDB.START_YEAR == 1990
			and GameDB.START_DATE == "1990-03-01", "A legacy set sets the data season, first year and start date")
	_check(GameDB.loaded and GameDB.players.size() == 42,
			"The set's players load and nobody else's (%d)" % GameDB.players.size())
	_check(GameDB.draftees.is_empty() and GameDB.list_additions.is_empty() and GameDB.departures.is_empty()
			and GameDB.club_moves.is_empty(), "Files the era has none of are empty, never 2026's")
	_check(GameDB.players.size() == 42, "The fixture's 42 players are there to rate")
	var rated_ok := true
	var off := 0
	for p in GameDB.players:
		if int(p.get("overall", 0)) <= 0 or not p.has("potential"):
			rated_ok = false
		var want := float(Prospects.days_between(str(p["dob"]), "1990-03-01")) / 365.25
		if not is_equal_approx(float(p["age"]), want) or want < 17.0 or want > 40.0:
			off += 1
	_check(rated_ok, "Every player is rated and has a potential")
	_check(off == 0, "Ages are taken at the set's own start date, 1 March 1990 (%d off)" % off)
	_check(GameDB.club_list("GEE").size() == 3 and GameDB.club_list("ADE").is_empty(),
			"Lists are the set's own")


func _test_back_to_2026() -> void:
	GameDB.reload(FIXTURE)
	GameDB.reload()
	_check(GameDB.dataset_id == "2026" and GameDB.DATA_SEASON == 2026, "Reloading the 2026 set after a legacy one")
	_golden("load after a legacy set", _load_print(), GOLDEN_LOAD)


func _test_save_keeps_dataset() -> void:
	GameState.reset(FIXTURE)
	_check(GameState.dataset == FIXTURE and GameDB.dataset_id == FIXTURE,
			"A career started from a legacy set holds it")
	var state: Dictionary = GameState._save_state()
	_check(str(state.get("dataset", "")) == FIXTURE, "The save names its set")
	GameState.reset()
	_check(GameDB.dataset_id == "2026" and GameState.dataset == "2026", "A new career is the 2026 set again")
	var reloads := GameDB.reloads
	_check(GameState._restore_career(state.duplicate(true)) and GameState.dataset == FIXTURE
			and GameDB.dataset_id == FIXTURE and GameDB.DATA_SEASON == 1989 and GameDB.players.size() == 42,
			"Loading the save loads its set again")
	_check(GameDB.reloads == reloads + 1, "The load reloads the set from its files")


func _test_old_and_unknown_saves() -> void:
	GameState.reset(FIXTURE)
	var state: Dictionary = GameState._save_state()
	state.erase("dataset")
	_check(GameState._restore_career(state.duplicate(true)) and GameState.dataset == "2026"
			and GameDB.dataset_id == "2026", "A save from before the choice is a 2026 career")
	state["dataset"] = "1066"
	_check(not GameState._restore_career(state.duplicate(true)) and GameDB.dataset_id == "2026",
			"A save whose set this build lacks is refused, not loaded onto other players")


# ---------------------------------------------------------------------------
# Clubs by year (P2): one club code across eras
# ---------------------------------------------------------------------------
func _test_club_years_today() -> void:
	GameDB.reload()
	_check(GameDB.active_clubs(2027).size() == 18 and not GameDB.clubs.has("FIT") and not GameDB.club_order.has("FIT"),
			"Today's league is the eighteen clubs; Fitzroy is not loaded (%d)" % GameDB.active_clubs(2027).size())
	_check(GameDB.club_name("BRL") == "Brisbane" and GameDB.club_short("BRL") == "Lions"
			and GameDB.club_name("WBD") == "Western Bulldogs" and GameDB.club_name("NTH") == "North Melbourne",
			"Today's names are clubs.csv's")
	_check(str(GameDB.club_era("BRL", 1995)["short"]) == "Bears" and str(GameDB.club_era("BRL", 1997)["short"]) == "Lions",
			"Brisbane are the Bears until 1996 and the Lions from 1997")
	_check(str(GameDB.club_era("WBD", 1990)["name"]) == "Footscray" and str(GameDB.club_era("WBD", 1997)["name"]) == "Western Bulldogs",
			"The Bulldogs are Footscray until 1996")
	_check(str(GameDB.club_era("NTH", 2003)["name"]) == "Kangaroos" and str(GameDB.club_era("NTH", 2008)["name"]) == "North Melbourne",
			"North are the Kangaroos from 1999 to 2007")
	_check(str(GameDB.club_era("STK", 1990)["ground"]) == "Moorabbin Oval" and str(GameDB.club_era("HAW", 1995)["ground"]) == "Waverley Park"
			and str(GameDB.club_era("COL", 1999)["ground"]) == "Victoria Park" and str(GameDB.club_era("COL", 2000)["ground"]) == "MCG",
			"Each club's home ground is its era's")
	_check(GameDB.ground_name("Marvel Stadium", 2005) == "Telstra Dome" and GameDB.ground_name("Marvel Stadium", 2027) == "Marvel Stadium"
			and GameDB.ground_name("GMHBA Stadium", 1990) == "Kardinia Park", "A ground carries its name of the year")
	_check(GameDB.club_era("BRL", 1995)["primary"] is Color and GameDB.club_era("BRL", 2027)["primary"] == GameDB.club_colours("BRL")[0],
			"Era colours are colours, and today's are clubs.csv's")
	_check(GameDB.club_code("BRB") == "BRL" and GameDB.club_code("FOO") == "WBD" and GameDB.club_code("FIT") == "FIT",
			"The Bears and Footscray carry today's codes")
	var l90 := GameDB.ladder_of(1990)
	var codes := []
	for r in l90:
		codes.append(str(r["club"]))
	_check(l90.size() == 14 and codes.has("BRL") and codes.has("WBD") and codes.has("FIT")
			and not codes.has("BRB") and not codes.has("FOO"), "The 1990 ladder reads in today's codes (%s)" % str(codes))


func _test_club_years_1990() -> void:
	GameDB.reload(FIXTURE)
	var want := {1990: 14, 1991: 15, 1995: 16, 1997: 16, 2026: 18}
	var got := {}
	for y in want:
		got[y] = GameDB.active_clubs(y).size()
	_check(got == want, "Clubs in the league: 14 in 1990, 15 in 1991, 16 in 1995 and 1997, 18 in 2026 (%s)" % str(got))
	var c90 := GameDB.active_clubs(1990)
	var c97 := GameDB.active_clubs(1997)
	_check(c90.has("FIT") and not c90.has("ADE") and not c97.has("FIT") and c97.has("PAD") and c97.has("FRE"),
			"Fitzroy play to 1996; Port Adelaide join in 1997")
	_check(GameDB.enter_year("ADE") == 1991 and GameDB.enter_year("FRE") == 1995 and GameDB.enter_year("PAD") == 1997
			and GameDB.enter_year("GCS") == 2011 and GameDB.enter_year("GWS") == 2012 and GameDB.enter_year("CAR") == 1989
			and GameDB.leave_year("FIT") == 1996 and GameDB.leave_year("CAR") == 0,
			"Entry and last years follow the clubs' history")
	_check(GameDB.club_order.find("FIT") == GameDB.club_order.find("FRE") - 1, "Fitzroy sit in club order before Fremantle")
	_check(GameDB.era_year == 1990 and GameDB.club_name("WBD") == "Footscray" and GameDB.club_short("BRL") == "Bears"
			and GameDB.club_name("FIT") == "Fitzroy" and str(GameDB.club("STK")["ground"]) == "Moorabbin Oval",
			"A 1990 start shows the clubs as they were in 1990")
	GameDB.apply_era(1997)
	_check(GameDB.club_name("WBD") == "Western Bulldogs" and GameDB.club_short("BRL") == "Lions"
			and str(GameDB.club("STK")["ground"]) == "Waverley Park", "A new season shows that year's clubs")
	GameDB.reload()


## Legacy grounds (plan L9): one key per ground whatever it was called, its
## name of the year on every screen, and one story the season it changes.
func _test_ground_names_1990() -> void:
	GameDB.reload(FIXTURE)
	_check(GameDB.ground_key("Princes Park") == "Ikon Park" and GameDB.ground_key("princes_park") == "Ikon Park"
			and GameDB.ground_key("Optus Oval") == "Ikon Park" and GameDB.ground_key("Carrara") == "People First Stadium"
			and GameDB.ground_key("MCG") == "MCG", "Every name a ground has had is the one ground")
	_check(str(GameDB.club_era("CAR", 1990)["ground"]) == "Ikon Park" and str(GameDB.club_era("WBD", 1990)["ground"]) == "Whitten Oval"
			and str(GameDB.club_era("BRL", 1990)["ground"]) == "People First Stadium",
			"The clubs' era grounds are the grounds' keys")
	_check(GameDB.ground_name("Ikon Park", 1990) == "Princes Park" and GameDB.ground_name("Ikon Park", 1994) == "Optus Oval"
			and GameDB.ground_name("Waverley Park", 1991) == "AFL Park" and GameDB.ground_name("People First Stadium", 1990) == "Carrara Stadium"
			and GameDB.ground_name("Whitten Oval", 1994) == "Western Oval" and GameDB.ground_name("MCG", 1990) == "MCG",
			"Each ground carries its name of the year; the MCG keeps its own")
	_check(GameDB.ground_name("GMHBA Stadium", 2017) == "Simonds Stadium" and GameDB.ground_name("GMHBA Stadium", 2018) == "GMHBA Stadium",
			"Kardinia Park was Simonds Stadium to 2017 (ground_names.csv, the sourced table)")
	_check(GameDB.ground_renamed_from("Ikon Park", 1994) == "Princes Park" and GameDB.ground_renamed_from("Ikon Park", 1995) == ""
			and GameDB.ground_renamed_from("Marvel Stadium", 2000) == "" and GameDB.ground_renamed_from("MCG", 1994) == "",
			"A rename is a dated name giving way to another; a ground opening is not one")
	_check(GameDB.ground_shown("Ikon Park") == "Princes Park" and GameDB.ground_shown("Ikon Park", 2000) == "Optus Oval",
			"The screens show the ground's name in the season shown (%s)" % GameDB.ground_shown("Ikon Park"))
	# The club page, the fixture and the next-match line show the year's name.
	var host := Control.new()
	ClubPage.open(host, "CAR")
	var fact: Node = host.find_child("Ground", true, false)
	var said := str((fact as RichTextLabel).text) if fact is RichTextLabel else ""
	_check(said.contains("Princes Park") and not said.contains("Ikon Park"),
			"Carlton's page names its 1990 home ground Princes Park (%s)" % said)
	host.free()
	var lists := {}
	for c in GameDB.active_clubs(1994):
		lists[c] = []
	var s94 := Season.new(GameDB.active_clubs(1994), lists, SUITE_SEED, 1994)
	GameDB.apply_era(1994)
	var venues := {}
	for page in StatsFixture.pages(s94):
		for m in page["matches"]:
			venues[str(m["venue"])] = true
	_check(venues.has("Optus Oval") and venues.has("AFL Park") and not venues.has("Ikon Park") and not venues.has("Waverley Park"),
			"The 1994 fixture names Optus Oval and AFL Park (%s)" % str(venues.keys()))
	# The rename story: once, the season it happens, with the clubs at home there.
	var old_season = GameState.season
	var old_year: int = GameState.season_year
	GameState.news = []
	GameState.milestone_log = {}
	for y in [1994, 1995]:
		GameState.season_year = y
		GameDB.apply_era(y)
		GameState.season = Season.new(GameDB.active_clubs(y), lists, SUITE_SEED, y)
		GameState._ground_rename_news()
	GameState._ground_rename_news()
	var told := GameState.news.filter(func(n): return str(n.get("kind", "")) == "ground")
	var lines := told.map(func(n): return str(n["text"]))
	_check(told.size() == 2 and lines.has("Western Oval takes a new name this season: from Round 1 it is Whitten Oval, home of Fitzroy and Footscray.")
			and lines.has("Princes Park takes a new name this season: from Round 1 it is Optus Oval, home of Carlton."),
			"1994 and 1995 each tell their ground's new name once (%s)" % str(lines))
	var story := NewsFront.story(told[0] if told.size() > 0 else {}, "CAR")
	_check(str(story["headline"]) == "Western Oval becomes Whitten Oval" and str(story["club"]) in ["FIT", "WBD"],
			"The story's headline is the old and new name, in the home club's colours (%s)" % str(story["headline"]))
	GameState.news = []
	GameState.season_year = 2027
	GameDB.reload()
	GameDB.apply_era(2027)
	GameState.season = Season.new(GameDB.active_clubs(2027), {}, SUITE_SEED, 2027)
	GameState._ground_rename_news()
	_check(GameState.news.is_empty(), "Today's grounds keep their names: a 2027 season tells no rename")
	GameState.season = old_season
	GameState.season_year = old_year
	GameState.news = []
	GameState.milestone_log = {}


## Legacy guernseys (TODO row 142, L9): each club wears the guernsey of the
## season being played, 1990 to 2026, and today's kits are clubs.csv's untouched.
func _test_guernseys_by_year() -> void:
	GameDB.reload()
	var raw := {}
	for r in GameDB._read_dicts("res://data/clubs.csv"):
		raw[str(r["code"])] = str(r["guernsey"])
	var today_ok := true
	for y in [2026, 2027]:
		GameDB.apply_era(y)
		for code in raw:
			if GameDB.clubs.has(code) and str(GameDB.clubs[code]["guernsey"]) != raw[code]:
				today_ok = false
			var g := GameDB.club_guernsey(code)
			if g["pattern3"] != g["pattern2"]:
				today_ok = false
	_check(today_ok and GameDB.club_colours("WCE")[0] == Color("#003087"),
			"A 2026 career's clubs wear clubs.csv's guernseys and colours, unchanged")
	GameDB.reload(FIXTURE)
	# Every design the year rows name is drawn by the figures, the crest and the discs.
	var named := {}
	for r in GameDB._read_dicts(GameDB.CLUBS_BY_YEAR_CSV):
		var g := str(r.get("guernsey", ""))
		if g != "":
			named[g.split(":")[0]] = true
	var drawn := true
	for d in named:
		drawn = drawn and GameDB.GUERNSEY_DESIGNS.has(d) and GuernseyCrest.BADGE_DESIGNS.has(d)
	var sheet := GuernseyCrest.BADGE_DESIGN_SHEET.get_size()
	_check(drawn and int(sheet.y / 256.0) * 4 >= GuernseyCrest.BADGE_DESIGNS.size(),
			"Every era design is in the figures' list and on the crest's sheet (%s)" % str(named.keys()))
	# Season by season, as the rollover applies each new year.
	var want := {
		1990: {"WBD": "dogs90", "SYD": "swans90", "WCE": "wings", "BRL": "yoke", "STK": "panels"},
		1995: {"FRE": "anchor", "WCE": "wings", "BRL": "chevron"},
		1997: {"PAD": "power97", "STK": "saints97", "WBD": "dogs97", "BRL": "yoke", "SYD": "yoke"},
		2002: {"STK": "panels", "WCE": "eagles00"},
		2007: {"ADE": "crows06", "PAD": "power97"},
		2010: {"FRE": "anchor", "BRL": "lions10", "ADE": "lowhoops", "PAD": "chevron"},
		2011: {"FRE": "chevrons", "GCS": "sides", "WBD": "dogs97"},
		2012: {"GWS": "giants12", "WBD": "twohoops"},
		2014: {"BRL": "yoke"},
		2016: {"WCE": "wings"},
		2021: {"GWS": "giants"},
		2026: {"GCS": "sides", "WCE": "wings", "FRE": "chevrons"},
	}
	var wrong := []
	for y in want:
		GameDB.apply_era(y)
		for code in want[y]:
			var g := GameDB.club_guernsey(code)
			if str(g["design"]) != str(want[y][code]):
				wrong.append("%s %d: %s" % [code, y, g["design"]])
	_check(wrong.is_empty(), "Each season's clubs wear that season's guernsey (%s)" % str(wrong))
	# Every season 1990-2025, every club playing wears its real guernsey, a picture in the kit
	# atlas (tools/kits/kits.txt); 2026 on, clubs.csv's own.
	var atlas := GameDB.kit_atlas()
	var cells := 0
	if atlas != null:
		cells = GameDB.KIT_PER_ROW * int(atlas.get_height()) / GameDB.KIT_SIDE
	var bare := []
	var outside := false
	for y in range(1990, 2027):
		GameDB.apply_era(y)
		for code in GameDB.active_clubs(y):
			var c := int(GameDB.club_guernsey(code).get("kit_cell", -1))
			if (c < 0) != (y >= 2026):
				bare.append("%s %d" % [code, y])
			outside = outside or c >= cells
	_check(atlas != null and bare.is_empty() and not outside,
			"Every club wears its season's guernsey picture 1990-2025 and clubs.csv's from 2026 (%s)" % str(bare))
	GameDB.apply_era(1997)
	var navy97: Color = GameDB.club_colours("WCE")[0]
	GameDB.apply_era(2005)
	var navy05: Color = GameDB.club_colours("WCE")[0]
	GameDB.apply_era(2018)
	_check(navy97 == Color("#021A31") and navy05 == Color("#05173F") and GameDB.club_colours("WCE")[0] == Color("#003087"),
			"West Coast are navy 1995-2017 and royal blue again from 2018")
	GameDB.apply_era(2024)
	var gold_sides: Color = GameDB.club_guernsey("GCS")["pattern"]
	GameDB.apply_era(2025)
	_check(gold_sides == Color("#FFDD00") and GameDB.club_guernsey("GCS")["pattern"] == Color("#9E140C"),
			"Gold Coast's side panels are gold to 2024 and red from 2025")
	# Fremantle's anchor: four colours, all the way to the figures and the crest.
	GameDB.apply_era(2000)
	var fre := GameDB.club_guernsey("FRE")
	_check(fre["pattern"] == Color.WHITE and fre["pattern2"] == Color("#065D1E") and fre["pattern3"] == Color("#DC0000"),
			"The anchor is white, with green on the wearer's right and red on his left")
	var mat := StoppageVignette.figure_material([fre, GameDB.club_guernsey("WCE")])
	var p3 = mat.get_shader_parameter("kit_pattern3")
	var designs = mat.get_shader_parameter("kit_design")
	_check(p3[0] == Color("#DC0000") and p3[1] == GameDB.club_guernsey("WCE")["pattern2"]
			and int(designs[0]) == 100 + int(fre.get("kit_cell", -100)),
			"The figures wear Fremantle's 2000 picture and get the anchor's red; a kit without a third colour repeats its second")
	var crest := UiKit.club_marker("FRE") as GuernseyCrest
	_check(crest != null and crest.design == "anchor" and crest.third == Color("#DC0000")
			and crest.kit_cell == int(fre.get("kit_cell", -1)),
			"Fremantle's 2000 marker is the anchor picture, its red included")
	if crest:
		crest.free()
	_check(PitchView.disc_design(fre) == "yoke" and PitchView.disc_design(GameDB.club_guernsey("WCE")) == "panels",
			"On the oval the era guernseys draw as the discs' own shapes")
	GameDB.reload()


## The real 1990 start (TODO row 142, L1): the 14 clubs' lists rated on 1989,
## each position scaled on its own season (director 2026-11-13), and a real
## player's ceiling set by his real peak, give or take luck.
func _test_real_1990() -> void:
	_check(Datasets.ready("1990"), "The 1990 start's files ship")
	GameDB.reload("1990")
	_check(GameDB.dataset_id == "1990" and GameDB.DATA_SEASON == 1989 and GameDB.START_YEAR == 1990,
			"The 1990 set loads on 1989's season")
	var per_club := {}
	var ovr := []
	var top := 0
	var stars := 0
	var peaked := 0
	var peak_ok := true
	for p in GameDB.players:
		var c := str(p.get("club", ""))
		per_club[c] = int(per_club.get(c, 0)) + 1
		var o := int(p.get("overall", 0))
		ovr.append(o)
		top = maxi(top, o)
		if o >= 80:
			stars += 1
		if int(p.get("real_peak", 0)) > 0:
			peaked += 1
			var pot := int(p.get("potential", 0))
			if pot < o or abs(pot - clampi(int(p["real_peak"]), o, Potential.MAX_POT)) > int(Potential.REAL_PEAK_LUCK) + 1:
				peak_ok = false
	_check(per_club.size() == 14 and not per_club.has("ADE") and per_club.has("FIT"),
			"Fourteen clubs carry a list, Fitzroy's among them and no Adelaide (%s)" % str(per_club.keys()))
	# A list is its played men plus those yet to play a senior game (list_additions).
	var listed := per_club.duplicate()
	for q in GameDB.list_additions:
		var c := str(q.get("club", ""))
		listed[c] = int(listed.get(c, 0)) + 1
	var thin := 0
	for c in listed:
		if int(listed[c]) < 42:
			thin += 1
	_check(thin == 0 and listed.size() == 14, "Every 1990 club has a full list (%s)" % str(listed))
	ovr.sort()
	var median := int(ovr[ovr.size() / 2])
	_check(median >= 57 and median <= 65, "The 1990 median sits where 2026's does (%d)" % median)
	var share := float(stars) / float(ovr.size())
	_check(share >= 0.04 and share <= 0.12 and top < 99,
			"About 7%% of the 1990 lists rate 80 or more and nobody tops out (%d of %d, best %d)" % [stars, ovr.size(), top])
	_check(peaked > 200 and peak_ok, "A real peak sets each ceiling, give or take luck (%d players)" % peaked)
	_check(Potential.peak_from_year == 1986, "Recent seasons count from the 1990 set's own data season")
	GameDB.reload()
	_check(Ratings.era_anchors.is_empty() and Potential.peak_from_year == 2023,
			"Back on 2026, positions scale on 2026's anchors again")
	_golden("load after the 1990 set", _load_print(), GOLDEN_LOAD)
