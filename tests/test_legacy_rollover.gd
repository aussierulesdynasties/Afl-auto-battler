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
	_t("_test_seventeen_clubs")
	_t("_test_brand_choice", [0])
	_t("_test_brand_choice", [1])
	_t("_test_brand_sim_bears")
	_t("_test_colours_apart")
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


## "bears coaches should be given the choice to rebrand to lions or stay as
## bears" (director, 2026-11-13). Fitzroy play on and you coach the Bears: one
## card, asked once, and either answer holds through a save. Only the look
## changes: the list and every rating stay as they were.
func _test_brand_choice(choice: int) -> void:
	GameState.reset("1990")
	GameState.start_season("BRL", GameDB.club_list("BRL"))
	GameState.legacy = {"fitzroy": "stays"}
	LegacyRollover.keep_fitzroy()
	GameDB.apply_era(1997)
	GameState.week_events = []
	LegacyRollover.week(GameState)
	_check(GameState.week_events.size() == 1 and str(GameState.week_events[0].get("tid", "")) == LegacyRollover.BRAND_TID,
			"The Bears' coach gets the Bears-or-Lions card (%d cards)" % GameState.week_events.size())
	if GameState.week_events.is_empty():
		return
	var card: Dictionary = GameState.week_events[0]
	_check((card["options"] as Array).all(func(o): return (o.get("effects", []) as Array).is_empty())
			and "never how the side plays" in str(card.get("text", "")),
			"The card says it changes the look only, and carries no effect on play")
	var before := _list_sum(GameState.my_list)
	GameState.resolve_card(0, choice)
	GameDB.apply_era(1997)
	var want := "Lions" if choice == 0 else "Bears"
	_check(GameDB.club_short("BRL") == want, "Answer %d: the club is the %s (%s)" % [choice, want, GameDB.club_short("BRL")])
	if choice == 0:
		_check(GameDB.club_colours("BRL")[1].b > 0.4, "The Lions wear blue (%s)" % str(GameDB.club_colours("BRL")))
	_check(_list_sum(GameState.my_list) == before, "The answer changes no player (%s, %s)" % [str(before), str(_list_sum(GameState.my_list))])
	_check(LegacyRollover.kit_gap() >= PitchView.DISC_CLASH,
			"Fitzroy and the %s look apart on the ground (gap %.1f)" % [want, LegacyRollover.kit_gap()])
	GameState.week_events = []
	LegacyRollover.week(GameState)
	_check(GameState.week_events.is_empty(), "The card comes once")
	var saved: Dictionary = GameState.legacy.duplicate(true)
	GameDB.reload("1990")
	GameState.legacy = saved
	LegacyRollover.restore(GameState)
	GameDB.apply_era(1997)
	_check(GameDB.club_short("BRL") == want and GameDB.active_clubs(1997).has("FIT"),
			"A loaded career keeps the %s beside Fitzroy (%s)" % [want, GameDB.club_short("BRL")])
	GameDB.reload("1990")


## A Bears side the sim runs stays the Bears: no card for a coach elsewhere.
func _test_brand_sim_bears() -> void:
	GameState.reset("1990")
	GameState.start_season("HAW", GameDB.club_list("HAW"))
	GameState.legacy = {"fitzroy": "stays"}
	LegacyRollover.keep_fitzroy()
	GameState.week_events = []
	LegacyRollover.week(GameState)
	GameDB.apply_era(1997)
	_check(GameState.week_events.is_empty() and GameDB.club_short("BRL") == "Bears",
			"Hawthorn's coach gets no card and the sim's Bears stay the Bears")
	GameDB.reload("1990")


## "if the lions/bears and fitzroy guernseys clash you can slightly change the
## colours of each" (director, 2026-11-13): checked with the match's own clash
## test, each reshaded a little (hue kept), never past SHADE_MAX.
func _test_colours_apart() -> void:
	for lions in [false, true]:
		GameState.reset("1990")
		GameDB.apply_era(1997)
		if lions:
			GameDB.unpin_era("BRL")
		GameDB.keep_club("FIT")
		if not lions:
			GameDB.pin_era("BRL", 1996)
		var raw_fit := GameDB.club_colours("FIT")
		var raw_bri := GameDB.club_colours("BRL")
		var raw_gap := LegacyRollover.kit_gap()
		LegacyRollover.separate_colours()
		var gap := LegacyRollover.kit_gap()
		var name := "Lions" if lions else "Bears"
		_check(gap >= PitchView.DISC_CLASH, "Fitzroy v the %s: no clash after (gap %.1f, was %.1f)" % [name, gap, raw_gap])
		var fit := GameDB.club_colours("FIT")
		var bri := GameDB.club_colours("BRL")
		var most := 0.0
		for i in range(3):
			most = maxf(most, maxf(absf(fit[i].v - raw_fit[i].v), absf(bri[i].v - raw_bri[i].v)))
			_check(absf(fit[i].h - raw_fit[i].h) < 0.01 or raw_fit[i].s < 0.05, "Fitzroy colour %d keeps its hue" % i)
			_check(absf(bri[i].h - raw_bri[i].h) < 0.01 or raw_bri[i].s < 0.05, "The %s colour %d keeps its hue" % [name, i])
		_check(most <= LegacyRollover.SHADE_MAX + 0.001, "A slight reshade only (%.2f)" % most)
		if raw_gap >= PitchView.DISC_CLASH:
			_check(most == 0.0, "No clash, no reshade (%s)" % name)
		print("Fitzroy v %s: gap %.1f -> %.1f, reshade %.2f" % [name, raw_gap, gap, most])
	GameDB.reload("1990")


func _list_sum(list: Array) -> Array:
	var ovr := 0
	for p in list:
		ovr += int(p.get("overall", 0))
	return [list.size(), ovr]


## A career whose Fitzroy fought off the merger has 17 clubs in 1997 (Port
## enter, the Bears carry on: director 2026-11-13). 1997's 22 rounds cannot
## hold 22 games each for 17 (187 matches, 176 places), so each club plays
## the most they fit, 20; the season runs with byes, every club meets every
## other, and the final eight plays out to a premier.
func _test_seventeen_clubs() -> void:
	GameState.reset("1990")
	LegacyRollover.keep_fitzroy()
	var codes: Array = GameDB.active_clubs(1997)
	_check(codes.size() == 17 and codes.has("FIT") and codes.has("BRL") and codes.has("PAD"),
			"Fitzroy, the Bears and Port make 17 clubs in 1997 (%d)" % codes.size())
	# Lists: the 1990 clubs' own, and the new clubs borrow one each (only the
	# fixture and the finals are under test here).
	var lists := {}
	var donors: Array = GameDB.active_clubs(1990)
	for i in range(codes.size()):
		var c: String = codes[i]
		var src: String = c if donors.has(c) else str(donors[i % donors.size()])
		lists[c] = GameState._career_copies(GameDB.club_list(src))
	var season := Season.new(codes, lists, 1997, 1997)
	_check(season.fixture.size() == season.regular_rounds() and season.regular_rounds() == 22,
			"1997 keeps its 22 rounds with 17 clubs (%d)" % season.fixture.size())
	_check(season.games_per_club() == 20, "Each of the 17 plays 20 games (%d)" % season.games_per_club())
	var games := {}
	var pairs := {}
	var byes := {}
	var twice_in_a_round := 0
	for ri in range(season.fixture.size()):
		var seen := {}
		for m in season.fixture[ri]:
			for c in [str(m["home"]), str(m["away"])]:
				if seen.has(c):
					twice_in_a_round += 1
				seen[c] = true
				games[c] = int(games.get(c, 0)) + 1
			var a := str(m["home"])
			var b := str(m["away"])
			pairs[a + "|" + b if a < b else b + "|" + a] = true
		for c in codes:
			if not seen.has(c):
				byes[c] = int(byes.get(c, 0)) + 1
	_check(twice_in_a_round == 0, "No club plays twice in a round (%d)" % twice_in_a_round)
	_check(codes.all(func(c): return int(games.get(c, 0)) == 20), "Every club plays 20 games (%s)" % str(games))
	_check(pairs.size() == 17 * 16 / 2, "Every club meets every other (%d of 136 pairs)" % pairs.size())
	_check(codes.all(func(c): return int(byes.get(c, 0)) == 2), "Every club has two byes (%s)" % str(byes))
	var guard := 0
	while not season.is_regular_done() and guard < 40:
		season.play_round()
		guard += 1
	season.start_finals()
	while not season.is_season_over() and guard < 60:
		season.play_finals_week()
		guard += 1
	_check(season.is_season_over() and (season.finals["top"] as Array).size() == 8 and str(season.finals["premier"]) != "",
			"The 17-club 1997 season plays its final eight to a premier (%s)" % str(season.finals.get("premier", "")))
	GameDB.reload("1990")


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
			var left: Array = GameState.league_lists.get("FIT", [])
			_check(left.is_empty(), "Fitzroy's list is empty (%d: %s)" % [left.size(),
					str(left.slice(0, 3).map(func(p): return [p.get("id"), p.get("joined"), p.get("club"), p.get("released_by")]))])
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
