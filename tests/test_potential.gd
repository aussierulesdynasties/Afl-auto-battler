extends RefCounted
const Ovr := preload("res://tests/ovr.gd")
## Potential (POT) regression suite: every player has a sane POT, recent
## history spots the injured stars (rehab year), draft pedigree lifts young
## high picks, the age curves and breakouts move ratings, a career's end
## takes them down,
## training is cheaper below POT, draft rank drives prospect POT, and POT
## survives a save (old saves get backfilled).
## Run through tests/run_potential_tests.gd.

var failures: Array[String] = []
var checks := 0

## Every season and draft here is seeded (C15): a clock seed makes a different
## league each run.
const SUITE_SEED := 2027
const BalanceGate := preload("res://tests/balance_gate.gd")


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	GameDB.reload()
	_t("_test_every_player_has_potential")
	_t("_test_history_and_pedigree")
	_t("_test_summer_adds_nothing")
	_t("_test_growth_pace")
	_t("_test_summer_fall")
	_t("_test_age_curves")
	_t("_test_breakouts")
	_t("_test_career_rolls")
	_t("_test_draftee_potential")
	_t("_test_draftee_bands")
	_t("_test_pick_values")
	_t("_test_save_and_backfill")
	_t("_test_fine_wine_real_players")
	_t("_test_fine_wine_draftee_rate")
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	print(Ran.line("Potential", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _real(name: String) -> Dictionary:
	for p in GameDB.players:
		if str(p["real_name"]) == name:
			return p
	return {}


func _test_every_player_has_potential() -> void:
	var ok := true
	var capped := true
	for p in GameDB.players + GameDB.draftees:
		if not p.has("potential") or int(p["potential"]) < int(Ovr.of(p)) \
				or int(p["potential"]) > Potential.MAX_POT:
			ok = false
		# Real history and draft pedigree may go past the generated caps.
		if p.has("history") or p.has("drafted_pick"):
			continue
		var cap := int(Potential.ROLE_CAP.get(str(p["role"]), 99))
		if int(p["potential"]) > maxi(cap, int(Ovr.of(p))):
			capped = false
	_check(ok, "Every player and prospect has a POT between his rating and the max")
	_check(capped, "Generated POTs respect the position caps")
	var reid := _real("Harley Reid")
	var bont := _real("Marcus Bontempelli")
	_check(int(reid["potential"]) - int(Ovr.of(reid)) > int(bont["potential"]) - int(Ovr.of(bont)),
			"A 21-year-old has more headroom than a 30-year-old (Reid %d/%d, Bontempelli %d/%d)" % [
			int(Ovr.of(reid)), int(reid["potential"]), int(Ovr.of(bont)), int(bont["potential"])])
	var pot_a := int(reid["potential"])
	GameDB.reload()
	_check(int(_real("Harley Reid")["potential"]) == pot_a, "POT is stable across reloads")


func _test_history_and_pedigree() -> void:
	var have_history := 0
	for p in GameDB.players:
		if p.has("history"):
			have_history += 1
	_check(have_history > 500, "Most players carry rated past seasons (%d)" % have_history)
	# The injured stars: short 2026, strong recent seasons. His rating is his
	# 2026 attributes (the rebuild deletes Ratings.rate_on_record,
	# docs/RATING_REBUILD.md §1); his record shows in his POT, above it.
	for name in ["Connor Rozee", "Darcy Moore", "Sam Darcy"]:
		var p := _real(name)
		_check(int(p["potential"]) > int(Ovr.of(p)),
				"%s's record lifts his POT above his short 2026 (%d now, POT %d)" % [
				name, int(Ovr.of(p)), int(p["potential"])])
	# The rehab year is for the one whose best season still sits well above
	# that record: Sam Darcy (95 in 2025 on 17 games, 76 the year before).
	var darcy := _real("Sam Darcy")
	_check(bool(darcy.get("rehab", false)) and int(darcy["potential"]) > int(Ovr.of(darcy)),
			"Sam Darcy is flagged for a rehab year (%d now, POT %d)" % [
			int(Ovr.of(darcy)), int(darcy["potential"])])
	# A full, healthy 2026 is not a rehab case, however good the history.
	var daicos := _real("Nick Daicos")
	_check(not daicos.has("rehab"), "A player with a full 2026 gets no rehab year")
	# Pedigree: the same young player with a top pick gets a higher ceiling.
	var young := {}
	for p in GameDB.players:
		if float(p["age"]) <= 21.0 and int(Ovr.of(p)) < 70 and not p.has("history"):
			young = p.duplicate(true)
			break
	if not young.is_empty():
		var plain := young.duplicate(true)
		plain.erase("potential")
		plain.erase("drafted_type")
		plain.erase("drafted_pick")
		Potential.assign(plain)
		var top := plain.duplicate(true)
		top.erase("potential")
		top["drafted_type"] = "national"
		top["drafted_pick"] = 1
		Potential.assign(top)
		var rookie := plain.duplicate(true)
		rookie.erase("potential")
		rookie["drafted_type"] = "rookie"
		rookie["drafted_pick"] = 1
		Potential.assign(rookie)
		_check(int(top["potential"]) > int(plain["potential"]),
				"A young pick-1 player has a higher ceiling (%d vs %d)" % [
				int(top["potential"]), int(plain["potential"])])
		_check(int(rookie["potential"]) == int(plain["potential"]),
				"A rookie-draft listing carries no pedigree bonus")


func _age_once(p: Dictionary, year := 2027) -> Dictionary:
	var copy: Dictionary = p.duplicate(true)
	Prospects.age_player(copy, year)
	return copy


## The summer adds nothing on its own (director 2026-11-17, the age jump and
## the free points removed): a player grows only from the XP he earns.
func _test_summer_adds_nothing() -> void:
	var moved := 0
	var young := 0
	for p in GameDB.players:
		if float(p["age"]) > 23.0:
			continue
		young += 1
		var after := _age_once(p)
		if after["attr"] != p["attr"]:
			moved += 1
	_check(young > 0 and moved == 0, "Ageing a year changes no young player's attributes (%d of %d moved)" % [moved, young])


## His pace (director 2026-11-17): a kid at 60 who plays every ordinary game
## reaches potential 65 / 70 / 75 / 80 / 85+ after 65 / 100 / 125 / 140 / 150
## games, the same rate for the same potential, the 65 rate below 65.
func _test_growth_pace() -> void:
	_check(Growth.games_to_potential(65) == 65.0 and Growth.games_to_potential(70) == 100.0
			and Growth.games_to_potential(75) == 125.0 and Growth.games_to_potential(80) == 140.0
			and Growth.games_to_potential(85) == 150.0 and Growth.games_to_potential(95) == 150.0,
			"The pace table is his (%s)" % str([Growth.games_to_potential(65), Growth.games_to_potential(70),
			Growth.games_to_potential(75), Growth.games_to_potential(80), Growth.games_to_potential(85), Growth.games_to_potential(95)]))
	_check(absf(Growth.games_to_potential(72) - 110.0) < 0.01, "Between rows the games fill in evenly (72: %.1f)" % Growth.games_to_potential(72))
	_check(Growth.points_per_game(60) == Growth.points_per_game(65), "Under 65 a game earns what a potential-65 game earns")
	_check(absf(Growth.points_per_game(95) * 150.0 - 35.0) < 0.01, "Potential 95 earns 35 points in 150 games")
	# Played out with the real grant and spending: a potential-85 midfielder
	# at 60 gets there in about 150 games.
	var base: Dictionary = {}
	for p in GameDB.players:
		if str(p.get("role", "")) == "MID" and not (p.get("attr", {}) as Dictionary).is_empty():
			base = (p as Dictionary).duplicate(true)
			break
	base["id"] = "pace_mid"
	base["gm"] = 18.0
	base["sample"] = 18.0
	Ovr.to(base, 60)
	base["potential"] = 85
	base["xp"] = 0.0
	base["xp_match"] = 0.0
	var games := 0
	while int(Rating.ovr(base)) < 85 and games < 400:
		Growth.play_games(base, 1)
		games += 1
	_check(games >= 140 and games <= 160, "A potential-85 midfielder from 60 reaches 85 after about 150 games (%d)" % games)


## His last season (director 2026-11-17): from his last season on, the
## season's gains all go and he falls 2, then 3. Before that the age curves
## move him (RATING_REBUILD §4, in place of the take-back past his peak).
func _test_summer_fall() -> void:
	var k := "kicking"
	var old: Dictionary = (_real("Jordan Dawson") as Dictionary).duplicate(true)
	old["id"] = "falls"
	old["career_last"] = 2035.0
	old["season_gains"] = {k: 3}
	var ov := int(Ovr.of(old))
	Growth.summer(old, 2035)
	var first := ov - int(Ovr.of(old))
	var ov2 := int(Ovr.of(old))
	Growth.summer(old, 2036)
	var second := ov2 - int(Ovr.of(old))
	_check(first >= 2 and second == 3, "From his last season he falls: the season's gains and 2, then 3 (%d, %d)" % [first, second])
	var before: Dictionary = (_real("Jordan Dawson") as Dictionary).duplicate(true)
	before["id"] = "not_yet"
	before["career_last"] = 2035.0
	before["season_gains"] = {k: 3}
	var at: Dictionary = (before["attr"] as Dictionary).duplicate()
	Growth.summer(before, 2034)
	_check(before["attr"] == at, "Before his last season the summer keeps what he gained")
	var hurt: Dictionary = (_real("Jordan Dawson") as Dictionary).duplicate(true)
	hurt["id"] = "hurt"
	hurt["career_last"] = 2035.0
	hurt["games_missed_injured"] = 10
	Growth.summer(hurt, 2030)
	_check(float(hurt["career_last"]) == 2034.75, "A season with 10 games missed injured takes a quarter of a season off (%.2f)" % float(hurt["career_last"]))


## A player at 50 in every attribute, `age` and `pot` (0: no ceiling).
func _fifty(age: float, pot: int) -> Dictionary:
	var p: Dictionary = (_real("Jordan Dawson") as Dictionary).duplicate(true)
	p["id"] = "ages_%d" % int(age)
	for key in p["attr"]:
		p["attr"][key] = 50
	p["age"] = age
	p["potential"] = pot
	p.erase("age_carry")
	return p


## RATING_REBUILD §4, the age curves, a little each regular round: Speed holds
## to 26, -1.5 a season from 27 and -3 from 31; Strength holds to 31 and -1 a
## season from 32 (director 2026-11-25, "Blueprint curves"); the rest move by
## the real players' average at each age (data/age_curves.csv).
func _test_age_curves() -> void:
	_check(Growth.age_change("speed", 26) == 0.0 and Growth.age_change("speed", 27) == -1.5
			and Growth.age_change("speed", 30) == -1.5 and Growth.age_change("speed", 31) == -3.0,
			"Speed holds to 26, then -1.5 a season from 27 and -3 from 31")
	_check(Growth.age_change("strength", 31) == 0.0 and Growth.age_change("strength", 32) == -1.0,
			"Strength holds to 31, then -1 a season from 32")
	_check(Growth.age_change("kicking", 20) > 0.0 and Growth.age_change("endurance", 19) > 0.0
			and Growth.age_change("kicking", 60) == 0.0 and Growth.age_change("discipline", 25) == 0.0,
			"A young player's skills rise with age; an age or attribute with no curve moves nothing")
	# A season of rounds: each attribute moves its season's change, a whole point at a time.
	var young := _fifty(20.4, 0)
	for r in 24:
		Growth.age_step(young, 1.0 / 24.0)
	var season_ok := true
	for key in Attributes.KEYS:
		if absf(float(int(young["attr"][key]) - 50) - Growth.age_change(key, 20)) >= 1.0:
			season_ok = false
	_check(season_ok, "Over 24 rounds a 20-year-old moves each attribute its season's change, short of a part point (Endurance 50 to %d, %.2f a season)"
			% [int(young["attr"]["endurance"]), Growth.age_change("endurance", 20)])
	# At his POT the rises wait; the falls do not.
	var capped := _fifty(20.0, 0)
	capped["potential"] = int(Rating.ovr(capped))
	for r in 24:
		Growth.age_step(capped, 1.0 / 24.0)
	var rose := false
	for key in Attributes.KEYS:
		rose = rose or int(capped["attr"][key]) > 50
	var slows := _fifty(31.0, 0)
	slows["potential"] = int(Rating.ovr(slows))
	for r in 24:
		Growth.age_step(slows, 1.0 / 24.0)
	_check(not rose and int(slows["attr"]["speed"]) == 47 and int(slows["attr"]["strength"]) == 50,
			"At his POT a 20-year-old's rises wait, and a 31-year-old still slows (Speed 50 to %d, Strength 50 to %d)"
			% [int(slows["attr"]["speed"]), int(slows["attr"]["strength"])])
	# Every club's list ages the same way.
	var lists := {"AAA": [_fifty(33.0, 0)], "BBB": [_fifty(33.0, 0)]}
	Growth.age_round(lists, 1)
	_check(int(lists["AAA"][0]["attr"]["speed"]) == 47 and int(lists["BBB"][0]["attr"]["speed"]) == 47
			and int(lists["AAA"][0]["attr"]["strength"]) == 49,
			"A round ages every club's players: at 33 a whole season takes 3 Speed and 1 Strength")
	# A player made older than his first season carries the seasons in between.
	var aged := Growth.age_attrs({"kicking": 40, "speed": 60}, 19, 22)
	var want := int(round(40.0 + Growth.age_change("kicking", 19) + Growth.age_change("kicking", 20) + Growth.age_change("kicking", 21)))
	_check(int(aged["kicking"]) == want and int(aged["speed"]) == 60,
			"Made at 22, a player carries the changes at 19, 20 and 21 (Kicking 40 to %d) and Speed holds that young" % int(aged["kicking"]))


## RATING_REBUILD §4: a breakout adds 4 to 6 to the three attributes his
## position weighs most, and he keeps it.
func _test_breakouts() -> void:
	_check(Growth.top_weighted("Midfielder") == ["contested_ball", "kicking", "handballing"],
			"A midfielder's breakout goes to Contested ball, Kicking and Handballing (%s)" % str(Growth.top_weighted("Midfielder")))
	var found := false
	var shape_ok := false
	for year in range(2030, 2080):
		var p := _fifty(24.0, 0)
		p["id"] = "breaks_%d" % year
		p["apos"] = "Midfielder"
		for key in p["attr"]:
			p["attr"][key] = 57      # reads about OVR 68, inside the breakout band
		var was: Dictionary = (p["attr"] as Dictionary).duplicate()
		if Growth.breakouts("AAA", [p], year).is_empty():
			continue
		found = true
		var jump := int(p["attr"]["contested_ball"]) - 57
		shape_ok = jump >= 4 and jump <= 6 and (p["breakouts"] as Array).size() == 1
		for key in Attributes.KEYS:
			var moved := int(p["attr"][key]) - int(was[key])
			if moved != (jump if key in ["contested_ball", "kicking", "handballing"] else 0):
				shape_ok = false
		break
	_check(found and shape_ok, "A breakout adds the same 4 to 6 to those three and nothing else")


## His career length (director 2026-11-17): a retired real player keeps his
## real last season; anyone else rolls from real careers with a similar peak,
## never shorter than the seasons he has played plus one; a Fine Wine player
## rolls from Fine Wine careers, which run longer.
func _test_career_rolls() -> void:
	var real := {"id": "real_last", "real_last": 2010, "potential": 80}
	_check(Growth.career_last(real, 2005) == 2010.0, "A real player's own last season stands")
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var plain := 0.0
	var fine := 0.0
	var short := 0
	# POT 70: about the 90th percentile of the real peaks in classes.csv on
	# the attributes' scale (RATING_REBUILD), as 85 was on the old one.
	for i in range(300):
		plain += float(Growth.roll_seasons(70, false, 1, rng))
		fine += float(Growth.roll_seasons(70, true, 1, rng))
		if Growth.roll_seasons(80, false, 12, rng) < 12:
			short += 1
	plain /= 300.0
	fine /= 300.0
	_check(short == 0, "A roll is never shorter than the seasons played plus one")
	_check(fine >= plain + 2.0, "Fine Wine careers run longer (%.1f seasons against %.1f)" % [fine, plain])


## Row 65 (director 4.Q9, 2026-11-04): picks 1-5 about 60-62 and picks 6-20 about
## 55-58, balance-gated: since the rating rebuild a draftee is his type's ranges
## at his talent (RATING_REBUILD §4), so the bands are measured here, not set.
## Bands by consensus rank, for twelve generated classes as a career drafts them
## (after their pool year) and the real 2026 class.
func _band_means(cls: Array) -> Dictionary:
	var acc := {"top_o": 0.0, "top_n": 0, "mid_o": 0.0, "mid_n": 0, "late_o": 0.0, "late_n": 0}
	for p in cls:
		var r := int(p["draft_rank"])
		var key := "top" if r <= 5 else ("mid" if r <= 20 else ("late" if r <= 40 else ""))
		if key == "":
			continue
		acc[key + "_o"] += float(Ovr.of(p))
		acc[key + "_n"] += 1
	return acc


func _classes() -> Array:
	var out: Array = []
	for y in range(2027, 2039):
		out.append_array(Prospects.age_pool(Prospects.generate_class(y, 900 + y), y, {}))
	return out


func _test_draftee_bands() -> void:
	_check(GameDB.draftees.size() >= 40, "The real 2026 class is loaded (%d)" % GameDB.draftees.size())
	for arm in [["generated", _classes()], ["real 2026", GameDB.draftees]]:
		var now := _band_means(arm[1])
		_check(int(now["top_n"]) >= 5 and int(now["mid_n"]) >= 15 and int(now["late_n"]) >= 20,
				"%s: every band has picks (%d, %d, %d)" % [arm[0], now["top_n"], now["mid_n"], now["late_n"]])
		var top: float = now["top_o"] / maxf(1.0, now["top_n"])
		var mid: float = now["mid_o"] / maxf(1.0, now["mid_n"])
		var late: float = now["late_o"] / maxf(1.0, now["late_n"])
		_check(top > mid and mid > late, "%s: talent runs in rank order (picks 1-5 %.1f, 6-20 %.1f, 21-40 %.1f)" % [arm[0], top, mid, late])
		_check(BalanceGate.held(top >= 60.0 and top <= 62.5, "picks 1-5 draftee band"), "%s: picks 1-5 start about 60-62 (%.1f)" % [arm[0], top])
		_check(BalanceGate.held(mid >= 55.0 and mid <= 58.0, "picks 6-20 draftee band"), "%s: picks 6-20 start about 55-58 (%.1f)" % [arm[0], mid])
	# The pool year (row 65): a generated class is drafted at the rating it was made with, a year
	# older. Passed over, he plays no AFL games, so he earns no XP and stays
	# where he is (director 2026-11-17: a player grows only from the XP he earns).
	var fresh := Prospects.generate_class(2030, 4)
	var made: Dictionary = (fresh[0] as Dictionary).duplicate(true)
	var pooled: Array = Prospects.age_pool(fresh, 2030, {})
	var kid: Dictionary = pooled[0]
	_check(int(Ovr.of(kid)) == int(Ovr.of(made)) and int(kid["potential"]) == int(made["potential"])
			and is_equal_approx(float(kid["age"]), float(made["age"]) + 1.0),
			"His class's pool year ages him a year and leaves his rating (%d v %d)" % [int(Ovr.of(kid)), int(Ovr.of(made))])
	var grew := 0
	for q in Prospects.age_pool(pooled.duplicate(true), 2031, {}):
		var was: Dictionary = {}
		for r in pooled:
			if str(r["id"]) == str(q["id"]):
				was = r
		if not was.is_empty() and int(Ovr.of(q)) > int(Ovr.of(was)):
			grew += 1
	_check(grew == 0, "Passed over, a prospect does not grow without games (%d of %d grew)" % [grew, pooled.size()])


## Director 2026-10-14, "hold pick values where they are" (today's values, 12 classes, a
## rebuilding club: pick 1 about 1.9, pick 10 about 1.3, pick 30 about 0.7), balance-gated.
func _pick_value_at(pick: int) -> float:
	var t := 0.0
	for c in range(12):
		var ranked: Array = TradeValue.rank_prospects(Prospects.generate_class(2027 + c, 700 + c))
		t += TradeValue.pick_value([[pick, 1.0]], ranked, "rebuilding")
	return t / 12.0


func _test_pick_values() -> void:
	var last := INF
	for e in [[1, 1.9], [10, 1.3], [30, 0.7]]:
		var now := _pick_value_at(int(e[0]))
		_check(now < last, "An earlier pick is worth more (pick %d %.2f)" % [int(e[0]), now])
		last = now
		_check(BalanceGate.held(absf(now - float(e[1])) <= 0.15, "rebuilding-club pick value"), "Pick %d is worth about %.1f to a rebuilding club (%.2f)" % [int(e[0]), float(e[1]), now])


func _test_draftee_potential() -> void:
	var top := []
	var late := []
	for p in GameDB.draftees:
		if int(p["draft_rank"]) <= 10:
			top.append(int(p["potential"]))
		elif int(p["draft_rank"]) > 40:
			late.append(int(p["potential"]))
	var avg := func(a: Array) -> float:
		var t := 0.0
		for x in a:
			t += float(x)
		return t / maxf(1.0, float(a.size()))
	_check(avg.call(top) > avg.call(late) + 5.0, "Top-10 picks carry more POT than late picks")
	var gen := Prospects.generate_class(2027)
	var all_ok := true
	for p in gen:
		if not p.has("potential") or int(p["potential"]) < int(Ovr.of(p)):
			all_ok = false
	_check(all_ok and not gen.is_empty(), "Generated draft classes get a POT")
	var d: Dictionary = GameDB.draftees[0].duplicate(true)
	var before := int(d["potential"])
	Prospects.project(d)
	_check(int(d["potential"]) == before, "Re-projecting a prospect keeps the same POT")


func _test_save_and_backfill() -> void:
	GameState.reset()
	GameState.start_season("WBD", GameDB.club_list("WBD"))
	# No round is played: what is saved is on every player from the first day.
	# Sam Darcy is the rehab case the record still leaves (_test_history_and_pedigree).
	var darcy := {}
	for q in GameState.my_list:
		if str(q["real_name"]) == "Sam Darcy":
			darcy = q
	var pot_before := int(darcy["potential"])
	GameState.save_career()
	GameState.load_career()
	var loaded := GameState.list_player(str(darcy["id"]))
	_check(int(loaded.get("potential", 0)) == pot_before and bool(loaded.get("rehab", false)),
			"POT and the rehab flag survive a save")
	_check(loaded.has("history") and loaded.has("drafted_pick"),
			"History and draft pedigree survive a save")
	# A save written before POT existed: strip it and reload.
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			p.erase("potential")
			p.erase("rehab")
	# An old save from before his first game: rated as the dataset has him.
	var orig: Dictionary = GameDB.player_by_id(str(darcy["id"]))
	var at_start := GameState.list_player(str(darcy["id"]))
	at_start["attr"] = (orig["attr"] as Dictionary).duplicate()
	Ovr.to(at_start, int(Ovr.of(orig)))
	GameState.save_career()
	GameState.load_career()
	var missing := 0
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			if not p.has("potential"):
				missing += 1
	_check(missing == 0, "Loading an old save fills in every POT")
	var back := GameState.list_player(str(darcy["id"]))
	_check(int(back.get("potential", 0)) == pot_before and bool(back.get("rehab", false)),
			"An old save picks up the dataset's POT and rehab year")


## Fine Wine (director, 2026-11-13): the real players named carry it, by their
## real careers; a created player with the same name does not.
func _test_fine_wine_real_players() -> void:
	for name in ["Scott Pendlebury", "Dayne Zorko", "Max Gawn"]:
		var p := _real(name)
		_check(not p.is_empty() and Traits.of(p).has("fine_wine"), "%s carries Fine Wine (%s)" % [name, str(Traits.of(p))])
	var young := _real("Nick Daicos")
	_check(not young.is_empty() and not Traits.fine_wine(young), "A young player does not have it")
	var namesake: Dictionary = _real("Scott Pendlebury").duplicate(true)
	namesake["generated"] = true
	_check(not Traits.fine_wine(namesake), "A created player who shares the name does not inherit it")
	# A Legacy start's veteran, by his real career (still listed at 40).
	_check(Traits.fine_wine({"real_name": "Dustin Fletcher", "dob": "1975-05-07"}), "Dustin Fletcher (143 games at 32+) has it")
	_check(Traits.fine_wine({"real_name": "Michael Tuck", "dob": "1953-06-24"}), "Michael Tuck (161 games at 32+) has it")
	var carriers := 0
	for p in GameDB.players:
		if Traits.fine_wine(p):
			carriers += 1
			_check(int(str(p["dob"]).substr(0, 4)) <= Prospects.FINE_WINE_RECORD_BORN,
					"%s has it only by a career old enough to show it" % str(p["real_name"]))
	print("Fine Wine on the 2026 lists: %d" % carriers)
	_check(carriers == 10, "The ten approved players on the 2026 lists have it (%d)" % carriers)
	var earn := str(Traits.EARNED["fine_wine"]["earn"])
	_check(earn.contains("1 draftee in %d" % int(round(1.0 / Traits.FINE_WINE_DRAFTEE_ODDS))),
			"The look-up states the draftee odds the game rolls (%s)" % earn)
	_check(Traits.ON_TOP.has("fine_wine") and Traits.label("fine_wine") == "Fine Wine", "Fine Wine comes on top of the five")


## The draftee roll lands near the set odds, and generated classes carry it.
func _test_fine_wine_draftee_rate() -> void:
	var total := 0
	var hits := 0
	for b in range(400):
		var cls := []
		for i in range(50):
			cls.append({"generated": true})
		Prospects.roll_fine_wine(cls, "test-%d" % b)
		for p in cls:
			total += 1
			hits += 1 if bool(p.get("fine_wine", false)) else 0
	var rate := float(hits) / float(total)
	print("Fine Wine draftee roll: %d of %d (%.2f%%)" % [hits, total, 100.0 * rate])
	_check(absf(rate - Traits.FINE_WINE_DRAFTEE_ODDS) < 0.003,
			"Draftees roll Fine Wine at about the set odds (%.2f%% of %d, set %.2f%%)" % [
			100.0 * rate, total, 100.0 * Traits.FINE_WINE_DRAFTEE_ODDS])
	# A real draftee rolls; a real player whose career could already show it does not.
	var kids := []
	var veterans := []
	for i in range(4000):
		kids.append({"dob": "2008-05-01"})
		veterans.append({"dob": "1985-05-01"})
	Prospects.roll_fine_wine(kids, "kids")
	Prospects.roll_fine_wine(veterans, "veterans")
	_check(kids.any(func(p): return bool(p.get("fine_wine", false))) and not veterans.any(func(p): return bool(p.get("fine_wine", false))),
			"A real draftee rolls; a real veteran's record decides")
	var in_classes := 0
	var prospects := 0
	for year in range(2027, 2067):
		for p in Prospects.generate_class(year, 7):
			prospects += 1
			in_classes += 1 if Traits.of(p).has("fine_wine") else 0
	print("Fine Wine in generated classes: %d of %d prospects over 40 drafts" % [in_classes, prospects])
	_check(in_classes > 0 and in_classes < prospects / 20,
			"Generated classes carry it, rarely (%d of %d prospects over 40 drafts)" % [in_classes, prospects])
