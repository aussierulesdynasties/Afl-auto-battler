extends RefCounted
## The 2020 Legacy career past 2027 (TODO row 142; director 2026-11-13:
## "campaigns can go for eternity"): a seeded Richmond career skips every
## season from 2020 and rolls on, no end year. Nightly (tools/ci_long_suites.txt):
## eight seasons take about seven minutes. Run through
## tests/run_legacy_2020_long_tests.gd.

const Ran := preload("res://tests/functions_ran.gd")
const Career := preload("res://tests/legacy_2020_career.gd")

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := Career.SEED
const CLUB := "RIC"


func run() -> void:
	_t("_test_the_career_rolls_past_2027")
	GameState.reset()
	for f in failures:
		print("FAIL: ", f)
	print(Ran.line("Legacy 2020 long", self))


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures.append(what)


func _test_the_career_rolls_past_2027() -> void:
	Career.start(CLUB)
	var started := Time.get_ticks_msec()
	var years := []
	while GameState.season_year <= 2027:
		var year := GameState.season_year
		GameState.skip_season()
		if not GameState.season.is_season_over():
			_check(false, "The %d season plays out (%s)" % [year, Career.state()])
			break
		years.append(year)
		if not Career.roll_on():
			_check(false, "The career rolls on from %d (%s)" % [year, Career.state()])
			break
		checks += 1
	_check(GameState.season_year == 2028 and years.size() == 8,
			"The career rolls from 2020 to 2028 with no end year (%d, seasons %s)" % [GameState.season_year, str(years)])
	print("Legacy 2020 long: %d seasons in %.0f s" % [years.size(), (Time.get_ticks_msec() - started) / 1000.0])
	GameState.reset()
