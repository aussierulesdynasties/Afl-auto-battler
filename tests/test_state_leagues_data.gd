extends RefCounted
## State leagues data (TODO row 128, step 1): the VFL, SANFL and WAFL 2026 files
## in data/state_leagues/, built by tools/state_leagues/build.py. Checks the one
## schema, the pinned counts, the AFL links (every link is a real AFL id; no AFL
## man is also a state-only man), one side per AFL club, the senior lists after
## the WAFL split, and the real 2026 ladders and finals. Data only: nothing in
## the game reads these files yet. Run through tests/run_state_leagues_data_tests.gd.
## Seeded by design: it reads data files and plays no match.

var failures: Array[String] = []
var checks := 0

const DIR := "res://data/state_leagues/"
const LEAGUES := ["VFL", "SANFL", "WAFL"]
const CLUB_COLS := ["code", "name", "short", "league", "kind", "afl_club", "future_afl_club", "ground",
		"primary", "secondary", "accent", "coach", "coach_note", "source_url", "colour_source", "coach_source"]
const STATS := ["gm", "gl", "bh", "di", "ki", "hb", "mk", "tk", "ho", "cl", "if50", "rb", "cm", "ff", "fa"]
const PLAYER_HEAD := ["sid", "league", "club", "list", "num", "first", "last", "dob", "dob_src", "height_cm",
		"height_src", "weight_kg", "pos"]
const PLAYER_TAIL := ["res_gm", "res_gl", "colts_gm", "colts_gl", "career_gm_pre2026", "junior_club", "note",
		"source_url"]
const LINK_HEAD := ["league", "state_club", "afl_id", "afl_club", "first", "last", "dob"]
const LINK_TAIL := ["match", "source_url"]
const LEAGUE_COLS := ["league", "name", "clubs", "rounds", "games_each", "byes_each", "finals_teams",
		"finals_format", "gf_venue", "points_per_team_game", "points_sd", "goal_accuracy", "premiers",
		"runners_up", "source_url"]
const LADDER_COLS := ["league", "pos", "club", "w", "l", "d", "pts", "pf", "pa", "pct", "source_url"]
const FINAL_COLS := ["league", "seq", "final", "home", "away", "home_score", "away_score", "winner", "source_url"]

## Pinned counts (rows, header excluded). A rebuild that changes them must say why.
const CLUBS := {"VFL": 22, "SANFL": 10, "WAFL": 10}
const PLAYERS := {"VFL": 798, "SANFL": 554, "WAFL": 1155}
const LINKS := 511
const FINALS := {"VFL": 11, "SANFL": 6, "WAFL": 6}
const PREMIERS := {"VFL": "BOX", "SANFL": "NWD", "WAFL": "PEL"}
const MIN_SENIORS := 30

var _files := {}   # name -> {"head": Array, "rows": Array of Dictionary}


func run() -> void:
	failures.clear()
	checks = 0
	GameDB.reload()
	_t("_test_schema")
	_t("_test_pinned_counts")
	_t("_test_clubs")
	_t("_test_one_side_per_afl_club")
	_t("_test_players")
	_t("_test_links_are_afl_men")
	_t("_test_no_afl_man_is_state_only")
	_t("_test_senior_lists")
	_t("_test_ladders")
	_t("_test_finals")
	print(Ran.line("State leagues data", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _read(name: String) -> Dictionary:
	if _files.has(name):
		return _files[name]
	var out := {"head": [], "rows": []}
	var f := FileAccess.open(DIR + name, FileAccess.READ)
	if f == null:
		_files[name] = out
		return out
	out["head"] = Array(f.get_csv_line())
	while not f.eof_reached():
		var cells := f.get_csv_line()
		if cells.size() <= 1 and (cells.size() == 0 or cells[0] == ""):
			continue
		var row := {}
		for i in range(out["head"].size()):
			row[out["head"][i]] = cells[i] if i < cells.size() else ""
		row["_cells"] = cells.size()
		out["rows"].append(row)
	_files[name] = out
	return out


func _rows(name: String) -> Array:
	return _read(name)["rows"]


func _norm(s: String) -> String:
	var out := ""
	for ch in s.to_lower():
		if ch >= "a" and ch <= "z":
			out += ch
	return out


func _clubs(league: String) -> Array:
	return _rows("%s_clubs_2026.csv" % league.to_lower())


func _players(league: String) -> Array:
	return _rows("%s_players_2026.csv" % league.to_lower())


## Every AFL man in GameDB (the lists plus list additions): id -> player.
func _afl() -> Dictionary:
	var out := {}
	for p in GameDB.players:
		out[str(p["id"])] = p
	for p in GameDB.list_additions:
		out[str(p["id"])] = p
	return out


func _test_schema() -> void:
	var want := {"leagues.csv": LEAGUE_COLS, "ladders_2026.csv": LADDER_COLS, "finals_2026.csv": FINAL_COLS,
			"afl_links_2026.csv": LINK_HEAD + STATS + LINK_TAIL}
	for lg in LEAGUES:
		want["%s_clubs_2026.csv" % lg.to_lower()] = CLUB_COLS
		want["%s_players_2026.csv" % lg.to_lower()] = PLAYER_HEAD + STATS + PLAYER_TAIL
	_check(want.size() == 10, "ten state league files expected, got %d" % want.size())
	for name in want:
		var d := _read(name)
		_check(d["head"] == want[name], "%s header is %s, expected %s" % [name, d["head"], want[name]])
		_check(FileAccess.file_exists(DIR + name + ".import"), "%s has no keep .import" % name)
		var short := 0
		for r in d["rows"]:
			if int(r["_cells"]) != want[name].size():
				short += 1
		_check(short == 0, "%s: %d rows with the wrong number of cells" % [name, short])


func _test_pinned_counts() -> void:
	for lg in LEAGUES:
		_check(_clubs(lg).size() == CLUBS[lg], "%s clubs: %d, pinned %d" % [lg, _clubs(lg).size(), CLUBS[lg]])
		_check(_players(lg).size() == PLAYERS[lg],
				"%s players: %d, pinned %d" % [lg, _players(lg).size(), PLAYERS[lg]])
	_check(_rows("afl_links_2026.csv").size() == LINKS,
			"AFL links: %d, pinned %d" % [_rows("afl_links_2026.csv").size(), LINKS])
	_check(_rows("leagues.csv").size() == 3, "leagues.csv: %d rows" % _rows("leagues.csv").size())
	_check(_rows("ladders_2026.csv").size() == 42, "ladders: %d rows" % _rows("ladders_2026.csv").size())
	_check(_rows("finals_2026.csv").size() == 23, "finals: %d rows" % _rows("finals_2026.csv").size())


func _hex(s: String) -> bool:
	if s.length() != 7 or not s.begins_with("#"):
		return false
	return s.substr(1).is_valid_hex_number()


func _test_clubs() -> void:
	var seen := {}
	for lg in LEAGUES:
		var rows := _clubs(lg)
		_check(rows.size() == CLUBS[lg], "%s: club rows before the loop" % lg)
		for c in rows:
			var code := str(c["code"])
			_check(not seen.has(code), "state club code %s used twice" % code)
			_check(not GameDB.clubs.has(code) and not GameDB.CLUB_ORDER.has(code),
					"state club code %s collides with an AFL code" % code)
			seen[code] = true
			_check(c["league"] == lg, "%s listed under %s" % [code, c["league"]])
			_check(["standalone", "reserves", "aligned"].has(c["kind"]), "%s kind %s" % [code, c["kind"]])
			var afl := str(c["afl_club"])
			if c["kind"] == "standalone":
				_check(afl == "", "standalone %s names AFL club %s" % [code, afl])
			else:
				_check(GameDB.CLUB_ORDER.has(afl), "%s side of unknown AFL club '%s'" % [code, afl])
			_check(_hex(c["primary"]) and _hex(c["secondary"]), "%s colours %s %s" % [code, c["primary"], c["secondary"]])
			_check(c["accent"] == "" or _hex(c["accent"]), "%s accent %s" % [code, c["accent"]])
			_check(c["colour_source"] != "", "%s colours have no source" % code)
			_check(str(c["coach"]).strip_edges() != "", "%s has no 2026 senior coach" % code)
			_check(str(c["coach_source"]).begins_with("https://"), "%s coach has no source" % code)


## Each AFL club in 2026 has exactly one state side; Tasmania's is the Devils
## from 2028 (director 2026-11-12). Canberra's and Forge clubs' sides are made
## at runtime, so no file names them.
func _test_one_side_per_afl_club() -> void:
	var sides := {}
	var future := {}
	for lg in LEAGUES:
		for c in _clubs(lg):
			if c["afl_club"] != "":
				sides[c["afl_club"]] = sides.get(c["afl_club"], []) + [c["code"]]
			if c["future_afl_club"] != "":
				future[c["future_afl_club"]] = future.get(c["future_afl_club"], []) + [c["code"]]
	var afl_2026: Array = GameDB.CLUB_ORDER.filter(func(code): return GameDB.data_enter_year(code) <= 2026)
	_check(afl_2026.size() == 18, "18 AFL clubs in 2026, got %d" % afl_2026.size())
	for code in afl_2026:
		_check(sides.get(code, []).size() == 1, "AFL club %s has state sides %s" % [code, sides.get(code, [])])
	_check(sides.size() == 18, "state sides name %d AFL clubs" % sides.size())
	_check(future.get("TAS", []) == ["TASD"], "Tasmania's future side is %s" % [future.get("TAS", [])])
	_check(not sides.has("TAS") and not sides.has("CANB"), "a future AFL club already has a 2026 side")


func _test_players() -> void:
	var sids := {}
	for lg in LEAGUES:
		var codes := {}
		for c in _clubs(lg):
			codes[c["code"]] = true
		var rows := _players(lg)
		_check(rows.size() == PLAYERS[lg], "%s: player rows before the loop" % lg)
		var bad := []
		for p in rows:
			var sid := str(p["sid"])
			if sids.has(sid):
				bad.append("%s twice" % sid)
			sids[sid] = true
			if p["league"] != lg or not codes.has(p["club"]):
				bad.append("%s club %s/%s" % [sid, p["league"], p["club"]])
			if not ["senior", "extra", "junior"].has(p["list"]):
				bad.append("%s list %s" % [sid, p["list"]])
			if str(p["first"]).strip_edges() == "" or str(p["last"]).strip_edges() == "":
				bad.append("%s has no name" % sid)
			var dob := str(p["dob"])
			if dob.length() != 10 or dob.substr(4, 1) != "-" or int(dob.substr(0, 4)) < 1980 or int(dob.substr(0, 4)) > 2012:
				bad.append("%s dob %s" % [sid, dob])
			if not ["source", "age", "league_median"].has(p["dob_src"]):
				bad.append("%s dob_src %s" % [sid, p["dob_src"]])
			var h := int(p["height_cm"])
			if h < 160 or h > 215:
				bad.append("%s height %s" % [sid, p["height_cm"]])
			if p["height_src"] != "source" and not str(p["height_src"]).begins_with("role_median_"):
				bad.append("%s height_src %s" % [sid, p["height_src"]])
			if not str(p["gm"]).is_valid_int():
				bad.append("%s games %s" % [sid, p["gm"]])
			if str(p["source_url"]).find("http") < 0:
				bad.append("%s has no source" % sid)
		_check(bad.is_empty(), "%s players: %s" % [lg, bad.slice(0, 8)])
	# The "Wauer Seb" order fix (SANFL API had the names reversed).
	var wauer := _players("SANFL").filter(func(p): return _norm(p["last"]) == "wauer")
	_check(wauer.size() == 1 and wauer[0]["first"] == "Seb", "Seb Wauer's name order: %s" % [wauer])
	_check(_players("SANFL").filter(func(p): return p["last"] == "Seb").is_empty(), "a SANFL surname is still 'Seb'")


func _test_links_are_afl_men() -> void:
	var afl := _afl()
	_check(afl.size() > 700, "GameDB holds %d AFL men" % afl.size())
	var rows := _rows("afl_links_2026.csv")
	_check(rows.size() == LINKS, "link rows before the loop: %d" % rows.size())
	var codes := {}
	for lg in LEAGUES:
		for c in _clubs(lg):
			codes[c["code"]] = lg
	var seen := {}
	var bad := []
	for l in rows:
		var key := "%s|%s" % [l["afl_id"], l["state_club"]]
		if seen.has(key):
			bad.append("%s twice" % key)
		seen[key] = true
		if codes.get(l["state_club"], "") != l["league"]:
			bad.append("%s: state club %s/%s" % [l["afl_id"], l["league"], l["state_club"]])
		var p = afl.get(str(l["afl_id"]))
		if p == null:
			bad.append("%s is not an AFL id" % l["afl_id"])
			continue
		if str(p["club"]) != str(l["afl_club"]) or _norm(str(p["last"])) != _norm(str(l["last"])) \
				or str(p["dob"]) != str(l["dob"]):
			bad.append("%s is %s %s %s, link says %s %s %s" % [l["afl_id"], p["club"], p["last"], p["dob"],
					l["afl_club"], l["last"], l["dob"]])
	_check(bad.is_empty(), "links: %s" % [bad.slice(0, 8)])


## No AFL-listed man is in a state players file: none shares his name and date
## of birth, and no reserves or aligned side lists a man of its AFL club's name.
## (WAFL same-name men at other clubs stay state men, by the design.)
func _test_no_afl_man_is_state_only() -> void:
	var afl := _afl()
	var by_dob := {}
	var by_club := {}
	for p in afl.values():
		by_dob["%s|%s|%s" % [_norm(str(p["first"])), _norm(str(p["last"])), p["dob"]]] = p["id"]
		by_club["%s|%s|%s" % [p["club"], _norm(str(p["first"])), _norm(str(p["last"]))]] = p["id"]
	var linked := {}
	for l in _rows("afl_links_2026.csv"):
		linked[l["afl_id"]] = true
	var both := []
	var total := 0
	for lg in LEAGUES:
		var aff := {}
		for c in _clubs(lg):
			aff[c["code"]] = c["afl_club"]
		for p in _players(lg):
			total += 1
			var k := "%s|%s|%s" % [_norm(p["first"]), _norm(p["last"]), p["dob"]]
			if p["dob_src"] == "source" and by_dob.has(k):
				both.append("%s = %s" % [p["sid"], by_dob[k]])
			var ck := "%s|%s|%s" % [aff[p["club"]], _norm(p["first"]), _norm(p["last"])]
			if aff[p["club"]] != "" and by_club.has(ck):
				both.append("%s = %s%s" % [p["sid"], by_club[ck], " (also linked)" if linked.has(by_club[ck]) else ""])
	_check(total == PLAYERS["VFL"] + PLAYERS["SANFL"] + PLAYERS["WAFL"], "players checked: %d" % total)
	_check(both.is_empty(), "AFL men in a state players file: %s" % [both])


## Every list has at least 30 senior men after the WAFL split (Colts-only men
## are juniors). A reserves or aligned side also fields its AFL club's men left
## out of the senior side (design: "omitted players first"), so its AFL list counts.
func _test_senior_lists() -> void:
	for lg in LEAGUES:
		var rows := _clubs(lg)
		_check(rows.size() == CLUBS[lg], "%s: clubs before the loop" % lg)
		var seniors := {}
		for p in _players(lg):
			if p["list"] == "senior":
				seniors[p["club"]] = seniors.get(p["club"], 0) + 1
		for c in rows:
			var own: int = seniors.get(c["code"], 0)
			_check(own <= 50, "%s has %d seniors, over the cap of 50" % [c["code"], own])
			var afl_men: int = GameDB.players_by_club.get(c["afl_club"], []).size() if c["afl_club"] != "" else 0
			_check(own + afl_men >= MIN_SENIORS, "%s (%s): %d own seniors + %d AFL men, under %d" % [
					c["code"], c["kind"], own, afl_men, MIN_SENIORS])
			if c["kind"] == "standalone":
				_check(own >= MIN_SENIORS, "standalone %s has %d senior men" % [c["code"], own])


func _test_ladders() -> void:
	var leagues := {}
	for r in _rows("leagues.csv"):
		leagues[r["league"]] = r
	_check(leagues.size() == 3, "leagues.csv names %s" % [leagues.keys()])
	for lg in LEAGUES:
		var L: Dictionary = leagues.get(lg, {})
		_check(int(L.get("clubs", 0)) == CLUBS[lg], "%s clubs in leagues.csv" % lg)
		_check(int(L.get("rounds", 0)) - int(L.get("games_each", 0)) == int(L.get("byes_each", -1)),
				"%s rounds - games != byes" % lg)
		_check(float(L.get("points_per_team_game", 0)) > 50.0 and float(L.get("goal_accuracy", 0)) > 0.4,
				"%s scoring %s / %s" % [lg, L.get("points_per_team_game"), L.get("goal_accuracy")])
		var rows := _rows("ladders_2026.csv").filter(func(r): return r["league"] == lg)
		_check(rows.size() == CLUBS[lg], "%s ladder has %d rows" % [lg, rows.size()])
		var codes := {}
		for c in _clubs(lg):
			codes[c["code"]] = true
		var w := 0
		var l := 0
		for i in range(rows.size()):
			var r: Dictionary = rows[i]
			w += int(r["w"])
			l += int(r["l"])
			_check(int(r["pos"]) == i + 1 and codes.has(r["club"]), "%s ladder row %d: %s" % [lg, i + 1, r["club"]])
			codes.erase(r["club"])
			_check(int(r["w"]) + int(r["l"]) + int(r["d"]) == int(L.get("games_each", 0)),
					"%s %s played %d" % [lg, r["club"], int(r["w"]) + int(r["l"]) + int(r["d"])])
			_check(int(r["pts"]) == 4 * int(r["w"]) + 2 * int(r["d"]), "%s %s points" % [lg, r["club"]])
		_check(w == l, "%s ladder wins %d, losses %d" % [lg, w, l])


func _test_finals() -> void:
	var leagues := {}
	for r in _rows("leagues.csv"):
		leagues[r["league"]] = r
	for lg in LEAGUES:
		var rows := _rows("finals_2026.csv").filter(func(r): return r["league"] == lg)
		_check(rows.size() == FINALS[lg], "%s has %d finals" % [lg, rows.size()])
		if rows.is_empty():
			continue
		for r in rows:
			var hs := int(r["home_score"])
			var as_ := int(r["away_score"])
			_check(hs != as_ and r["winner"] == (r["home"] if hs > as_ else r["away"]), "%s final %s" % [lg, r["seq"]])
		var gf: Dictionary = rows[rows.size() - 1]
		_check(gf["final"] == "GF" and gf["winner"] == PREMIERS[lg], "%s premiers %s" % [lg, gf["winner"]])
		_check(leagues.get(lg, {}).get("premiers", "") == PREMIERS[lg], "%s leagues.csv premiers" % lg)
