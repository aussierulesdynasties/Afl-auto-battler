extends RefCounted
## Each season's football by era (legacy mode, TODO row 142, phase L5): the era
## rows, a 2026 match unchanged, and a seeded campaign whose 1990 and 2010
## seasons each play their own year's football against the same matches played
## today, through Season (every background match) and your own coached match.
## Run through tests/run_era_football_tests.gd.

var failures: Array[String] = []
var checks := 0

## Every season here is built with its own seed (C15).
const SUITE_SEED := 2027

const Golden := preload("res://tests/season_golden.gd")


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	_t("_test_rows")
	_t("_test_today_unchanged")
	_t("_test_campaign_by_season")
	_t("_test_your_match_plays_its_season")
	_t("_test_interchange_default")
	GameState.replay_seed = 0
	print(Ran.line("Era football", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _codes(n: int) -> Array:
	return (GameDB.active_clubs(2027).duplicate() as Array).slice(0, n)


## Team totals over a round of `s`: each match set up by the season itself
## (Season.match_sim), so it is played as the season plays its matches.
func _round_totals(s: Season, keys: Array) -> Dictionary:
	var out := {}
	for k in keys:
		out[k] = 0.0
	var i := 0
	for m in s.fixture[0]:
		var sim: MatchSim = s.match_sim(str(m["home"]), str(m["away"]), 7000 + i)
		i += 1
		var r: Dictionary = sim.run()
		for side in range(2):
			for k in keys:
				out[k] += float((r["team"][side] as Dictionary).get(k, 0))
	return out


## Every real season from the 1990 start to 2025 has a row; each moves only the
## engine rates EraFootball names, by a believable amount; 2026 on has none.
func _test_rows() -> void:
	var years := EraFootball.years()
	for y in range(1990, 2026):
		_check(y in years, "An era row for %d" % y)
	for y in years:
		var row := EraFootball.rates_for(int(y))
		_check(not row.is_empty(), "%d's row has rates" % y)
		for k in row:
			_check((str(k) in EraFootball.KEYS and Ratings.T.has(str(k))) or str(k) in EraFootball.SIM,
					"%d: %s is an engine rate" % [y, k])
			_check(float(row[k]) > 0.2 and float(row[k]) < 3.0, "%d: %s x%.3f is believable" % [y, k, float(row[k])])
	for y in [0, 2026, 2027, 2040]:
		_check(EraFootball.rates_for(y).is_empty(), "%d plays today's football" % y)


## A match in 2026 (or after, or with no year) is the same match as before era
## football existed: same rates, same score, same team lines, seed for seed.
func _test_today_unchanged() -> void:
	var codes := _codes(2)
	for sd in [11, 12, 13]:
		var runs := []
		for y in [0, 2026, 2031]:
			var h := Squad.new(str(codes[0]), GameDB.club_list(str(codes[0])), true, str(codes[0]))
			var a := Squad.new(str(codes[1]), GameDB.club_list(str(codes[1])), false, str(codes[1]))
			var sim := MatchSim.new(h, a, sd)
			sim.season_year = y
			_check(sim.era_rates.is_empty(), "%d: no era rates" % y)
			var r: Dictionary = sim.run()
			runs.append([r["score"], JSON.stringify(r["team"])])
		_check(runs[0] == runs[1] and runs[0] == runs[2],
				"Seed %d: a 2026 or 2031 match is the match with no year" % sd)


## A seeded campaign: a 1990 season's round, a 2010 season's and the same
## round today, every match on the same seed. Each season's matches take its
## own row (Season sets the match's year), so 1990 tackles far less than today
## (24 a team against 57 in the real seasons), 2010 handballs more than 1990
## (169 against 108), and today's rates are untouched.
func _test_campaign_by_season() -> void:
	var codes := _codes(14)
	var lists := Golden.lists(codes)
	var keys := ["tackles", "handballs", "kicks", "disposals", "hitouts"]
	var tot := {}
	for y in [1990, 2010, 2027]:
		var s := Season.new(codes, lists, 3, y)
		var sim: MatchSim = s.match_sim(str(codes[0]), str(codes[1]), 1)
		_check(sim.season_year == y, "A %d season's match is played in %d" % [y, sim.season_year])
		var want := EraFootball.rates_for(y)
		var base := Ratings.T.duplicate()
		for k in Ratings.FLOW:
			base[k] = Ratings.FLOW[k]
		for k in EraFootball.KEYS:
			var expect := float(base[k]) * float(want.get(k, 1.0))
			_check(is_equal_approx(float(sim._rates()[k]), expect),
					"%d: %s is today's x%.3f" % [y, k, float(want.get(k, 1.0))])
		tot[y] = _round_totals(s, keys)
	_check(tot[1990]["tackles"] < 0.7 * tot[2027]["tackles"],
			"1990 tackles far less than today (%d against %d a round)" % [tot[1990]["tackles"], tot[2027]["tackles"]])
	_check(tot[2010]["handballs"] > 1.25 * tot[1990]["handballs"],
			"2010 handballs far more than 1990 (%d against %d)" % [tot[2010]["handballs"], tot[1990]["handballs"]])
	_check(tot[1990]["hitouts"] < tot[2010]["hitouts"],
			"1990's recorded hit-outs below 2010's (%d against %d)" % [tot[1990]["hitouts"], tot[2010]["hitouts"]])


## Your own match (the one you coach) is played in its season too.
func _test_your_match_plays_its_season() -> void:
	GameState.reset()
	GameState.start_season("MEL", GameDB.club_list("MEL"))
	_check(GameState.prepare_interactive_match() and GameState.pending_sim.season_year == GameState.season.year
			and GameState.pending_sim.era_rates.is_empty(), "A new career's match plays today's football")
	# The same match built again as a 1990 season builds it.
	GameState.season.year = 1990
	GameState._build_pending_sim()
	_check(GameState.pending_sim.season_year == 1990
			and not GameState.pending_sim.era_rates.is_empty(), "A 1990 season's coached match plays 1990's football")
	GameState.reset()


## The bench stays today's until the era rules by year (L4) name each season's.
func _test_interchange_default() -> void:
	_check(EraFootball.interchange(1990) == Ratings.INTERCHANGE and EraFootball.interchange(2026) == Ratings.INTERCHANGE,
			"The interchange count is today's until L4 sets it by year")
