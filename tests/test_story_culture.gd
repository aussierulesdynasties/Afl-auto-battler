extends RefCounted
## The culture fixture: Melbourne's home-and-away season played with culture's
## effects on and off, four seeds each, plus the growth arm (Ambition alone).
## Twelve full seasons, so it runs on its own nightly machine instead of inside
## the story suite (director 2026-11-18: "Yes, split both"). Run through
## tests/run_story_culture_tests.gd. Moved from tests/test_story.gd unchanged.

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 2031


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	GameDB.reload()
	StoryDeck.reload()
	_t("_test_culture_effects_fixture")
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	GameState.stories_on = true
	print(Ran.line("Story culture", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


## The player-effect fixture: Melbourne's home-and-away season played twice,
## culture's effects on and off (legs, morale and XP read over the first
## FIXTURE_ROUNDS), with Melbourne's culture set to a
## well-run, very tight, rebuilding group. Everything else is the same seed. The
## sheet predicts fresher legs, players who take being left out better (read
## per game left out), and young players earning more development; each shows,
## and the size is printed.
##
## `growth_only`: only Ambition is set (rebuilding); Standards and Togetherness
## stay neutral, so culture on changes nothing in the matches and the young
## players' ratings at the season's end differ by the extra development alone.
## Since #1718 a player grows only from the games he plays, and the culture's
## +5% XP is about 0.12 OVR a season: with Togetherness on as well the two arms
## play different matches, and that noise hides it.
const FIXTURE_ROUNDS := 8


func _culture_fixture_run(on: bool, run_seed := SUITE_SEED, growth_only := false) -> Dictionary:
	GameState.reset()
	GameState.career_seed = run_seed
	GameState.replay_seed = run_seed
	GameState.culture_effects_on = on
	GameState.start_season("MEL", GameDB.club_list("MEL"))
	if not growth_only:
		GameState.relations[Culture.key("MEL", "standards")] = {"t": 70, "log": []}
		GameState.relations[Culture.key("MEL", "together")] = {"t": 70, "log": []}
	GameState.relations[Culture.key("MEL", "ambition")] = {"t": -70, "log": []}
	var load_sum := 0.0
	var young_xp := 0
	var young_ids := {}
	var young_sg := {}
	for p in GameState.my_list:
		if Culture.young_for_growth(p, GameState.season_year):
			young_ids[str(p["id"])] = int(p.get("overall", 0))
			young_sg[str(p["id"])] = (p.get("season_gains", {}) as Dictionary).duplicate()
	var morale := 0.0
	# Morale each player lost in a game he was left out of while fit: the
	# culture's lever itself, read game by game, so the season's results
	# (wins lift who played) do not drown it. A promised game or run stings
	# by its own rule, so those players are not read.
	var stings := []
	var r := 0
	while not GameState.season.is_regular_done() and r < 30:
		if GameState.week_event_pending():
			GameState.resolve_week_event(0)
		if GameState.media_conference_pending():
			GameState.skip_media_conference()
		var before := {}
		for p in GameState.my_list:
			if not p.has("expects_game") and not Backing.is_active(p):
				before[str(p["id"])] = ClubLife.morale(p)
		GameState.advance()
		r += 1
		if r > FIXTURE_ROUNDS:
			continue
		var res := GameState.last_match
		if not res.is_empty():
			var played := {}
			for row in (res["roster"] as Array)[0 if str(res["home"]) == "MEL" else 1]:
				played[str(row["id"])] = true
			for p in GameState.my_list:
				var id := str(p["id"])
				if before.has(id) and not played.has(id) and not GameState._round_unavailable.has(id) \
						and int(p.get("injury_weeks", 0)) <= 0:
					stings.append(float(int(before[id]) - ClubLife.morale(p)))
		var w := 0.0
		for p in GameState.my_list:
			w += Workload.value(p)
		load_sum += w / float(GameState.my_list.size())
		for row in GameState.last_training_report.get("rows", []):
			if young_ids.has(str(row["id"])):
				young_xp += int(row["xp"])
		if r == FIXTURE_ROUNDS:
			for p in GameState.my_list:
				morale += float(ClubLife.morale(p))
	var young_gain := 0.0
	var young_exact := 0.0
	var young_n := 0
	for p in GameState.my_list:
		var pid := str(p["id"])
		if young_ids.has(pid):
			young_gain += float(int(p.get("overall", 0)) - int(young_ids[pid]))
			young_n += 1
			# The same OVR his new skill points bought, before it is rounded to
			# a whole number (Ratings.overall_per_point).
			var sg: Dictionary = p.get("season_gains", {})
			var sg0: Dictionary = young_sg[pid]
			for k in sg:
				young_exact += float(int(sg[k]) - int(sg0.get(k, 0))) * Ratings.overall_per_point(
						str(p.get("role", "MID")), str(k), Ratings.effective_games(p))
	var bands := "%s/%s/%s" % [Culture.band_key("standards", Culture.value(GameState.relations, "MEL", "standards")),
			Culture.band_key("together", Culture.value(GameState.relations, "MEL", "together")),
			Culture.band_key("ambition", Culture.value(GameState.relations, "MEL", "ambition"))]
	GameState.culture_effects_on = true
	return {"load": load_sum / float(FIXTURE_ROUNDS), "morale": morale / float(GameState.my_list.size()),
			"young_xp": young_xp, "young": young_ids.size(), "bands": bands,
			"young_gain": young_gain / float(maxi(1, young_n)), "young_gain_sum": young_gain, "young_n": young_n,
			"young_exact_sum": young_exact,
			"rounds": r, "stings": stings}


## Seeds the culture fixture is averaged over. The morale it ends the stretch
## on is printed but not checked: one season's results move it more than
## culture does (seed by seed it swings about 5 points either way, against an
## effect of about 2), so its sign follows the seed. The check reads the sting
## of each game left out instead (`stings`), which no result moves.
const CULTURE_SEEDS := [SUITE_SEED, SUITE_SEED + 1, SUITE_SEED + 2, SUITE_SEED + 3]


## Mean and standard error of a list of numbers.
func _mean_se(xs: Array) -> Array:
	var n := float(maxi(1, xs.size()))
	var m := 0.0
	for x in xs:
		m += float(x) / n
	var v := 0.0
	for x in xs:
		v += pow(float(x) - m, 2.0) / maxf(1.0, n - 1.0)
	return [m, sqrt(v / n)]


## The fixture's runs over `seeds`: numbers averaged; bands joined, so
## each must hold on every seed; every left-out game's sting pooled, and every
## young player's OVR gain pooled ("young_pooled": total gain over all of them).
func _culture_fixture_mean(on: bool, seeds: Array = CULTURE_SEEDS, growth_only := false) -> Dictionary:
	var out := {"load": 0.0, "morale": 0.0, "young_xp": 0, "young": 0, "bands": "", "young_gain": 0.0, "rounds": 0,
			"stings": [], "per_seed": [], "young_gain_sum": 0.0, "young_n": 0, "young_exact_sum": 0.0}
	var bands := {}
	var n := float(seeds.size())
	for sd in seeds:
		var r := _culture_fixture_run(on, int(sd), growth_only)
		(out["stings"] as Array).append_array(r["stings"])
		(out["per_seed"] as Array).append(float(r["morale"]))
		out["load"] = float(out["load"]) + float(r["load"]) / n
		out["morale"] = float(out["morale"]) + float(r["morale"]) / n
		out["young_gain"] = float(out["young_gain"]) + float(r["young_gain"]) / n
		out["young_xp"] = int(out["young_xp"]) + int(r["young_xp"])
		out["young"] = int(out["young"]) + int(r["young"])
		out["rounds"] = maxi(int(out["rounds"]), int(r["rounds"]))
		out["young_gain_sum"] = float(out["young_gain_sum"]) + float(r["young_gain_sum"])
		out["young_n"] = int(out["young_n"]) + int(r["young_n"])
		out["young_exact_sum"] = float(out["young_exact_sum"]) + float(r["young_exact_sum"])
		bands[str(r["bands"])] = true
	out["bands"] = ",".join(PackedStringArray(bands.keys()))
	out["young_pooled"] = float(out["young_gain_sum"]) / float(maxi(1, int(out["young_n"])))
	out["young_exact"] = float(out["young_exact_sum"]) / float(maxi(1, int(out["young_n"])))
	return out


func _test_culture_effects_fixture() -> void:
	var t0 := Time.get_ticks_msec()
	var off := _culture_fixture_mean(false)
	var on := _culture_fixture_mean(true)
	# The growth arm: only Ambition set, so on and off play the same matches.
	# Culture off ignores the strands, so the off arm above is its other half.
	var grow := _culture_fixture_mean(true, CULTURE_SEEDS, true)
	print("Culture fixture: %d runs in %.1f s" % [3 * CULTURE_SEEDS.size(), (Time.get_ticks_msec() - t0) / 1000.0])
	var s_on := _mean_se(on["stings"])
	var s_off := _mean_se(off["stings"])
	var gap := float(s_off[0]) - float(s_on[0])
	var gap_se := sqrt(pow(float(s_on[1]), 2.0) + pow(float(s_off[1]), 2.0))
	print("Culture fixture (Melbourne, seeds from %d, mean of %d; first %d rounds): load %.2f v %.2f off | morale lost a game left out %.2f (n %d) v %.2f (n %d) off, gap %.2f se %.3f | morale at the end %.2f v %.2f off (by seed %s v %s) | young XP %d v %d off (%d young players) | bands %s | young OVR gain over the %d-round season %.2f v %.2f off" % [
			int(CULTURE_SEEDS[0]), CULTURE_SEEDS.size(), FIXTURE_ROUNDS, float(on["load"]), float(off["load"]),
			float(s_on[0]), (on["stings"] as Array).size(), float(s_off[0]), (off["stings"] as Array).size(), gap, gap_se,
			float(on["morale"]), float(off["morale"]), str(on["per_seed"]), str(off["per_seed"]),
			int(on["young_xp"]), int(off["young_xp"]), int(on["young"]), str(on["bands"]), int(on["rounds"]),
			float(on["young_gain"]), float(off["young_gain"])])
	_check(str(on["bands"]) == "elite/very/rebuild" and str(off["bands"]) == "elite/very/rebuild",
			"The fixture's culture holds for the stretch (%s, %s)" % [on["bands"], off["bands"]])
	_check(float(on["load"]) < float(off["load"]), "A well-run group carries less load in its legs (%.2f v %.2f)" % [on["load"], off["load"]])
	# A very tight group takes being left out better: every game a fit player
	# misses, pooled over the seeds (a few hundred a side), costs him less,
	# by more than three standard errors.
	_check((on["stings"] as Array).size() >= 100 and (off["stings"] as Array).size() >= 100 and gap > 3.0 * gap_se,
			"A very tight group takes being left out better: %.2f morale lost a game v %.2f off (gap %.2f, se %.3f)" % [
			float(s_on[0]), float(s_off[0]), gap, gap_se])
	_check(float(on["young_xp"]) > float(off["young_xp"]) * 1.02,
			"A rebuilding club's young players earn more development (%d v %d)" % [on["young_xp"], off["young_xp"]])
	# Rated higher: Ambition alone, Standards and Togetherness neutral, so the
	# matches are the same either way; every young player pooled over the seeds.
	# Read before rounding: the culture's +5% XP is about a tenth of a point a
	# player, so whole OVR points tie (66 v 66 over 28 players on CI).
	print("Culture fixture, Ambition alone (rebuilding): bands %s | young OVR gain over the %d-round season %.3f v %.3f off (whole points %.3f v %.3f; %d v %d young players, pooled)" % [
			str(grow["bands"]), int(grow["rounds"]), float(grow["young_exact"]), float(off["young_exact"]),
			float(grow["young_pooled"]), float(off["young_pooled"]), int(grow["young_n"]), int(off["young_n"])])
	_check(str(grow["bands"]) == "mid/mid/rebuild" and float(grow["young_exact"]) > float(off["young_exact"]),
			"...and end the home-and-away season rated higher (%.3f v %.3f OVR gained, rebuilding alone, %s)" % [
			grow["young_exact"], off["young_exact"], grow["bands"]])
