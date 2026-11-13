extends RefCounted
## A Legacy career's rollovers (TODO row 142, phase L8; LegacyRollover): a
## seeded 1990 career, coached at Fitzroy, drafts the real 1990 class, rolls
## into 1991 with 15 clubs and Adelaide on its real list, and on across 1995
## (Fremantle), 1996-97 (the merger talks, the Brisbane Lions, Port Adelaide),
## 2011 (Gold Coast) and 2012 (GWS). A 2026 career never meets any of it.
## Run through tests/run_legacy_rollover_tests.gd.

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 1990


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	_t("_test_2026_unchanged")
	_t("_test_class_rows")
	_t("_test_fitzroy_odds")
	_t("_test_fitzroy_stays")
	_t("_test_campaign")
	GameState.replay_seed = 0
	GameDB.reload()
	print(Ran.line("Legacy rollover", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


## A 2026 career: generated classes, no real lists, nothing recorded.
func _test_2026_unchanged() -> void:
	GameDB.reload()
	GameState.reset()
	GameState.start_season("MEL", GameDB.club_list("MEL"))
	_check(not LegacyRollover.on() and not LegacyRollover.has_class(2026) and not LegacyRollover.has_entry("ADE", 1991),
			"A 2026 career has no real classes or entry lists")
	var real := GameState.draftee_pool.filter(func(p): return str(p.get("id", "")).begins_with("R"))
	_check(real.is_empty() and not GameState.draftee_pool.is_empty(), "A 2026 career's first class is generated")
	_skip_season()
	_check(GameState.start_next_season(), "A 2026 career rolls over")
	_check(GameState.legacy.is_empty() and not GameState._save_state().has("legacy"),
			"A 2026 career records nothing for Legacy and saves no key for it")


## The real classes: each year's class, ranked without gaps, a real name each.
func _test_class_rows() -> void:
	GameDB.reload("1990")
	for year in [1990, 1996, 2010, 2025, 2026]:
		_check(LegacyRollover.has_class(year), "%d has a real class" % year)
	var cls := LegacyRollover.real_class(1990)
	_check(cls.size() >= 50, "The 1990 class is the National and Rookie drafts (%d)" % cls.size())
	var ranks_ok := true
	var named := true
	for i in range(cls.size()):
		var p: Dictionary = cls[i]
		ranks_ok = ranks_ok and int(p["draft_rank"]) == i + 1 and str(p["id"]) == "R1990_%03d" % (i + 1)
		named = named and str(p["real_name"]).strip_edges() != "" and str(p["generic_name"]) != ""
	_check(ranks_ok and named, "Every 1990 prospect has his class rank, a stable id and a real name")
	var hooper := cls.filter(func(p): return str(p["real_name"]) == "Stephen Hooper")
	_check(hooper.size() == 1 and int(hooper[0]["draft_rank"]) == 1, "Stephen Hooper is the first of the 1990 class")
	var aged := Prospects.age_pool(cls.duplicate(true), 1990, {})
	_check(aged.size() == cls.size(), "No real 1990 draftee is too old for his own draft (%d of %d)" % [aged.size(), cls.size()])
	var peaked := cls.filter(func(p): return int(p.get("real_peak", 0)) > 0)
	_check(not peaked.is_empty() and peaked.all(func(p): return int(p["potential"]) >= int(p["overall"])),
			"A draftee with a real best season has his ceiling from it (%d)" % peaked.size())


## The talks give the odds for each of Fitzroy's records.
func _test_fitzroy_odds() -> void:
	GameState.reset("1990")
	GameState.legacy = {"finals": {"1994": ["FIT"], "1995": ["FIT"]}}
	var both := LegacyRollover.talks_line(GameState)
	_check("90% they play on, 10% they merge" in both, "Finals in 1994 and 1995: 90%% they play on (%s)" % both)
	GameState.legacy = {"finals": {"1995": ["FIT"]}}
	var one := LegacyRollover.talks_line(GameState)
	_check("finals in 1995 only" in one and "(100%)" in one, "Finals in 1995 only: finals in 1996 or merge (%s)" % one)
	GameState.legacy = {"finals": {}}
	var none := LegacyRollover.talks_line(GameState)
	_check("no way out" in none and "(100%)" in none, "No finals: the merger goes ahead (%s)" % none)


## A Fitzroy that played finals regularly and won the 90% plays on in 1997
## beside the Bears, and a loaded career keeps it so.
func _test_fitzroy_stays() -> void:
	GameState.reset("1990")
	GameState.start_season("HAW", GameDB.club_list("HAW"))
	var seed := -1
	for s in range(1, 200):
		var rng := RandomNumberGenerator.new()
		rng.seed = hash("fitzroy-merger|%d" % s)
		if rng.randi_range(1, 100) > LegacyRollover.MERGE_ANYWAY_PCT:
			seed = s
			break
	GameState.career_seed = seed
	GameState.legacy = {"finals": {"1994": ["FIT"], "1995": ["FIT"], "1996": []}}
	LegacyRollover.before_moves(GameState, 1997)
	_check(str(GameState.legacy.get("fitzroy", "")) == "stays", "Fitzroy, regular finalists, win the 90% and play on")
	_check(GameDB.active_clubs(1997).has("FIT") and GameDB.active_clubs(1997).has("BRL"),
			"Fitzroy and Brisbane both play in 1997")
	GameDB.apply_era(1997)
	_check(GameDB.club_short("BRL") == "Bears", "Without the merger the Bears stay the Bears (%s)" % GameDB.club_short("BRL"))
	_check(GameState.news.any(func(n): return "fought off the merger" in str(n.get("text", ""))), "The news says Fitzroy play on")
	var saved: Dictionary = GameState.legacy.duplicate(true)
	GameDB.reload("1990")
	_check(not GameDB.active_clubs(1997).has("FIT"), "A reload puts the data's Fitzroy back")
	GameState.legacy = saved
	LegacyRollover.restore(GameState)
	GameDB.apply_era(1997)
	_check(GameDB.active_clubs(1997).has("FIT") and GameDB.club_short("BRL") == "Bears",
			"A loaded career keeps Fitzroy and the Bears")


## The campaign: 1990 to 2012 at Fitzroy, then Brisbane.
func _test_campaign() -> void:
	GameState.reset("1990")
	GameState.start_season("FIT", GameDB.club_list("FIT"))
	var real_1990 := GameState.draftee_pool.filter(func(p): return str(p.get("id", "")).begins_with("R1990_"))
	_check(real_1990.size() == LegacyRollover.real_class(1990).size(),
			"The 1990 career's draft pool is the real 1990 class (%d)" % real_1990.size())
	_check(ExpansionBuild.building(GameState).is_empty(), "Adelaide builds no concession list: it brings its real one")
	# 1990 -> 1991: the clubs draft the real class.
	_skip_season()
	_check(GameState.begin_intake_draft(), "The 1990 intake draft opens")
	var d: Draft = GameState.draft
	while d != null and not d.is_finished():
		var c := d._best_ai_pick(d.current_club())
		if c.is_empty() or not d._draft_pick(d.current_club(), c):
			d._skip_current_pick()
	_check(GameState.finish_intake_draft(), "The 1990 intake draft closes and the season rolls over")
	_check(GameState.season_year == 1991 and GameDB.active_clubs(1991).size() == 15,
			"1991 has 15 clubs (%d in %d)" % [GameDB.active_clubs(GameState.season_year).size(), GameState.season_year])
	var drafted := 0
	for code in GameState.league_lists:
		for p in GameState.league_lists[code]:
			if str(p.get("id", "")).begins_with("R1990_"):
				drafted += 1
	_check(drafted >= 30, "The clubs took the real 1990 class (%d listed)" % drafted)
	_entered("ADE", 1991)
	# On to 2012.
	var lions_checked := false
	while GameState.season_year < 2012:
		var year := GameState.season_year
		_skip_season()
		if not GameState.start_next_season():
			_check(false, "%d rolls over" % year)
			return
		var now := GameState.season_year
		if now == 1996:
			_check(GameState.news.any(func(n): return "merger talks" in str(n.get("text", ""))),
					"The merger talks open before 1996")
		if now == 1995 or now == 1997 or now == 2011 or now == 2012:
			_entered({1995: "FRE", 1997: "PAD", 2011: "GCS", 2012: "GWS"}[now], now)
		if now == 1997:
			lions_checked = true
			_check(str(GameState.legacy.get("fitzroy", "")) == "merged", "Fitzroy, out of the finals, merge (%s)" % str(GameState.legacy))
			_check(not GameDB.active_clubs(1997).has("FIT") and GameDB.active_clubs(1997).size() == 16,
					"1997 has 16 clubs and no Fitzroy (%d)" % GameDB.active_clubs(1997).size())
			_check(GameDB.club_short("BRL") == "Lions", "The Bears are the Brisbane Lions (%s)" % GameDB.club_short("BRL"))
			_check((GameState.league_lists.get("FIT", []) as Array).is_empty(), "Fitzroy's list is empty")
			var lions: Array = GameState.league_lists["BRL"]
			var from_fitzroy := lions.filter(func(p): return int(p.get("joined", 0)) == 1997 and not str(p.get("id", "")).begins_with("E"))
			_check(from_fitzroy.size() >= 1 and from_fitzroy.size() <= LegacyRollover.LIONS_TAKE,
					"The Lions take Fitzroy's best (%d)" % from_fitzroy.size())
			_check(GameState.my_club == "BRL", "Fitzroy's coach goes to the Brisbane Lions (%s)" % GameState.my_club)
			var stray := 0
			for cid in GameState.coaches:
				var c: Dictionary = GameState.coaches[cid]
				if str(c.get("status", "")) == "club" and str(c.get("club", "")) == "FIT":
					stray += 1
			_check(stray == 0, "No coach is left at Fitzroy (%d)" % stray)
			_check(GameState.news.any(func(n): return "have merged" in str(n.get("text", ""))), "The news tells of the merger")
			var real_1996 := 0
			for code in GameState.league_lists:
				for p in GameState.league_lists[code]:
					if str(p.get("id", "")).begins_with("R"):
						real_1996 += 1
			_check(real_1996 > 0, "Real draftees are on the lists")
	_check(lions_checked and GameState.season_year == 2012 and GameDB.active_clubs(2012).size() == 18,
			"2012 has 18 clubs (%d)" % GameDB.active_clubs(GameState.season_year).size())
	var loaded := GameState._save_state()
	_check(loaded.has("legacy") and (loaded["legacy"] as Dictionary).has("finals"), "The save keeps the Legacy record")


## `code` enters `year` on its real list: the real players, a full list.
func _entered(code: String, year: int) -> void:
	var list: Array = GameState.league_lists.get(code, [])
	var rows := 0
	var names := {}
	for p in list:
		names[str(p.get("real_name", ""))] = true
	var absent := []
	for r in GameDB._read_dicts(LegacyRollover.ENTRY_CSV):
		if str(r["club"]) == code and int(r["year"]) == year:
			rows += 1
			var nm := "%s %s" % [str(r["first"]), str(r["last"])]
			if not names.has(nm):
				absent.append("%s%s" % [nm, " (known)" if str(r["known"]) == "1" else ""])
	var real := list.filter(func(p): return str(p.get("real_name", "")).strip_edges() != "" and str(p.get("club", "")) == code)
	_check(GameDB.active_clubs(year).has(code), "%s plays in %d" % [code, year])
	_check(list.size() >= rows - 8 and list.size() <= rows and real.size() == list.size(),
			"%s enter %d on their real list (%d of its %d; not there: %s)" % [code, year, list.size(), rows, ", ".join(absent)])
	var expansion := list.filter(func(p): return str(p.get("id", "")).begins_with("EXP_"))
	_check(expansion.is_empty(), "%s field no generated players" % code)
	var rated := list.filter(func(p): return int(p.get("overall", 0)) > 30)
	_check(rated.size() == list.size(), "Every %s player is rated" % code)
	_check(GameState.news.any(func(n): return "on their real list" in str(n.get("text", "")) and GameDB.club_name(code) in str(n.get("text", ""))),
			"The news tells of %s's entry" % code)


func _skip_season() -> void:
	GameState.season.round_index = GameState.season.fixture.size()
