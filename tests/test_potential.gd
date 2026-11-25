extends RefCounted
## Potential (POT) regression suite: every player has a sane POT, recent
## history spots the injured stars (rehab year), draft pedigree lifts young
## high picks, the rollover pulls ratings toward POT without passing it,
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
	_t("_test_summer_take_back")
	_t("_test_career_rolls")
	_t("_test_draftee_potential")
	_t("_test_youth_pace")
	_t("_test_draftee_bands")
	_t("_test_pick_values_held")
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
		if not p.has("potential") or int(p["potential"]) < int(p["overall"]) \
				or int(p["potential"]) > Potential.MAX_POT:
			ok = false
		# Real history and draft pedigree may go past the generated caps.
		if p.has("history") or p.has("drafted_pick"):
			continue
		var cap := int(Potential.ROLE_CAP.get(str(p["role"]), 99))
		if int(p["potential"]) > maxi(cap, int(p["overall"])):
			capped = false
	_check(ok, "Every player and prospect has a POT between his rating and the max")
	_check(capped, "Generated POTs respect the position caps")
	var reid := _real("Harley Reid")
	var bont := _real("Marcus Bontempelli")
	_check(int(reid["potential"]) - int(reid["overall"]) > int(bont["potential"]) - int(bont["overall"]),
			"A 21-year-old has more headroom than a 30-year-old")
	var pot_a := int(reid["potential"])
	GameDB.reload()
	_check(int(_real("Harley Reid")["potential"]) == pot_a, "POT is stable across reloads")


func _test_history_and_pedigree() -> void:
	var have_history := 0
	for p in GameDB.players:
		if p.has("history"):
			have_history += 1
	_check(have_history > 500, "Most players carry rated past seasons (%d)" % have_history)
	# The injured stars: short 2026, strong recent seasons. Every start rates
	# a player on his last three seasons (director, row 200, 2026-11-16:
	# Ratings.rate_on_record), so each opens on his record, well above what
	# his short 2026 alone said, and his POT is at least that.
	for name in ["Connor Rozee", "Darcy Moore", "Sam Darcy"]:
		var p := _real(name)
		var short_year := int(p.get("season_overall", p["overall"]))
		_check(int(p["overall"]) >= short_year + 15 and int(p["potential"]) >= int(p["overall"]),
				"%s opens on his record (%d vs %d in 2026 alone, POT %d)" % [
				name, int(p["overall"]), short_year, int(p["potential"])])
	# The rehab year is for the one whose best season still sits well above
	# that record: Sam Darcy (95 in 2025 on 17 games, 76 the year before).
	var darcy := _real("Sam Darcy")
	_check(bool(darcy.get("rehab", false)) and int(darcy["potential"]) > int(darcy["overall"]),
			"Sam Darcy is flagged for a rehab year (%d now, POT %d)" % [
			int(darcy["overall"]), int(darcy["potential"])])
	# A full, healthy 2026 is not a rehab case, however good the history.
	var daicos := _real("Nick Daicos")
	_check(not daicos.has("rehab"), "A player with a full 2026 gets no rehab year")
	# Pedigree: the same young player with a top pick gets a higher ceiling.
	var young := {}
	for p in GameDB.players:
		if float(p["age"]) <= 21.0 and int(p["overall"]) < 70 and not p.has("history"):
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
	for k in base["attr"]:
		base["attr"][k] = 60      # every attribute 60 reads OVR 60
	base["potential"] = 85
	base["xp"] = 0.0
	base["xp_match"] = 0.0
	var games := 0
	while int(Rating.ovr(base)) < 85 and games < 400:
		Growth.play_games(base, 1)
		games += 1
	_check(games >= 140 and games <= 160, "A potential-85 midfielder from 60 reaches 85 after about 150 games (%d)" % games)


## Past his peak (director 2026-11-17): the first summer takes 40% of what he
## trained past his potential, rising to all of it by his last season; from his
## last season on, the season's gains all go and he falls 2, then 3.
func _test_summer_take_back() -> void:
	var p: Dictionary = (_real("Jordan Dawson") as Dictionary).duplicate(true)
	p["id"] = "take_back"
	p["peak_year"] = 2030
	p["career_last"] = 2035.0
	var k := "kicking"
	var at := int(p["attr"][k])
	p["over_gains"] = {k: 10}
	Growth.summer(p, 2030)
	_check(int(p["attr"][k]) == at - 4, "The summer he peaks, 40%% of what he trained past it goes (%d to %d)" % [at, int(p["attr"][k])])
	var q: Dictionary = (_real("Jordan Dawson") as Dictionary).duplicate(true)
	q["id"] = "take_back_late"
	q["peak_year"] = 2030
	q["career_last"] = 2035.0
	q["over_gains"] = {k: 10}
	Growth.summer(q, 2034)
	_check(int(q["attr"][k]) == at - 9, "A year before his last season, 88%% goes (%d to %d)" % [at, int(q["attr"][k])])
	var old: Dictionary = (_real("Jordan Dawson") as Dictionary).duplicate(true)
	old["id"] = "falls"
	old["career_last"] = 2035.0
	old["season_gains"] = {k: 3}
	var ov := int(old["overall"])
	Growth.summer(old, 2035)
	var first := ov - int(old["overall"])
	var ov2 := int(old["overall"])
	Growth.summer(old, 2036)
	var second := ov2 - int(old["overall"])
	_check(first >= 2 and second == 3, "From his last season he falls: the season's gains and 2, then 3 (%d, %d)" % [first, second])
	var hurt: Dictionary = (_real("Jordan Dawson") as Dictionary).duplicate(true)
	hurt["id"] = "hurt"
	hurt["career_last"] = 2035.0
	hurt["games_missed_injured"] = 10
	Growth.summer(hurt, 2030)
	_check(float(hurt["career_last"]) == 2034.75, "A season with 10 games missed injured takes a quarter of a season off (%.2f)" % float(hurt["career_last"]))


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
	for i in range(300):
		plain += float(Growth.roll_seasons(85, false, 1, rng))
		fine += float(Growth.roll_seasons(85, true, 1, rng))
		if Growth.roll_seasons(80, false, 12, rng) < 12:
			short += 1
	plain /= 300.0
	fine /= 300.0
	_check(short == 0, "A roll is never shorter than the seasons played plus one")
	_check(fine >= plain + 2.0, "Fine Wine careers run longer (%.1f seasons against %.1f)" % [fine, plain])


func _top_ten(scale: float) -> Array:
	var old := Prospects.DRAFT_NIGHT_SCALE
	Prospects.DRAFT_NIGHT_SCALE = scale
	var out: Array = []
	for y in range(2027, 2033):
		# As a career drafts them: after the class's pool year (row 65).
		for p in Prospects.age_pool(Prospects.generate_class(y, 700 + y), y, {}):
			if int(p["draft_rank"]) <= 10:
				out.append(p)
	Prospects.DRAFT_NIGHT_SCALE = old
	return out


func _mean_of(ps: Array, key: String) -> float:
	var t := 0.0
	for p in ps:
		t += float(p[key])
	return t / maxf(1.0, float(ps.size()))


func _test_youth_pace() -> void:
	_check(is_equal_approx(Prospects.DRAFT_NIGHT_SCALE, 0.87), "The draft-night scale is 0.87 (row 65 bands)")
	var old_top := _top_ten(1.0)
	var top := _top_ten(Prospects.DRAFT_NIGHT_SCALE)
	var drop := _mean_of(old_top, "overall") - _mean_of(top, "overall")
	_check(BalanceGate.held(drop >= 5.0 and drop <= 12.0, "top-10 draft-night drop vs old curve"), "A top-10 pick arrives about 8 points lower than on the old curve (%.1f)" % drop)
	_check(absf(_mean_of(old_top, "potential") - _mean_of(top, "potential")) <= 1.5, "His ceiling (POT) is the same")
	# Readiness: a few are ready-made, most typical, some long-term projects.
	var ready := 0
	var project := 0
	var ready_ov := 0.0
	var project_ov := 0.0
	for p in top:
		if str(p.get("readiness", "")) == "ready":
			ready += 1
			ready_ov += float(p["overall"])
		elif str(p.get("readiness", "")) == "project":
			project += 1
			project_ov += float(p["overall"])
	var n := float(top.size())
	_check(BalanceGate.held(float(ready) / n >= 0.10 and float(ready) / n <= 0.35, "ready-made share of top 10"), "About 1 in 5 of a top 10 is ready-made (%d of %d)" % [ready, top.size()])
	_check(BalanceGate.held(project > 0 and ready > 0 and ready_ov / float(ready) > project_ov / float(project) + 8.0, "ready-made vs project draft-night gap"),
			"A ready-made pick is well ahead of a project on draft night")
	# Nobody already listed is rescaled: a saved draftee keeps his rating whatever the scale is now,
	# and the real 2026 class (a draft class too, row 65) is rescaled like a generated one.
	var saved: Dictionary = (_top_ten(1.0)[0] as Dictionary).duplicate(true)
	var kept := int(saved["overall"])
	var scale := Prospects.DRAFT_NIGHT_SCALE
	Prospects.DRAFT_NIGHT_SCALE = 0.5
	_check(int(saved["overall"]) == kept, "A draftee already on a list keeps his rating when the scale changes")
	Prospects.DRAFT_NIGHT_SCALE = scale
	var real_pick: Dictionary = {}
	for p in GameDB.draftees:
		real_pick = (p as Dictionary).duplicate(true)
		break
	if not real_pick.is_empty():
		Prospects.project(real_pick)
		var at_scale := int(real_pick["overall"])
		Prospects.DRAFT_NIGHT_SCALE = 1.0
		Prospects.project(real_pick)
		Prospects.DRAFT_NIGHT_SCALE = scale
		_check(at_scale < int(real_pick["overall"]), "The real 2026 class is rescaled like a generated one (%d v %d)" % [at_scale, int(real_pick["overall"])])


## Row 65 (director 4.Q9, 2026-11-04): draftees start lower, picks 1-5 about 60-62 and picks 6-20
## about 55-58, POT kept. Bands by consensus rank (the order the AI drafts in, near enough; the
## draft audit tools/audit/draftee_bands_impl.gd measures by actual pick), for twelve generated
## classes as a career drafts them (after their pool year) and the real 2026 class; POT as on the
## old curve; listed young players untouched.
func _band_means(cls: Array) -> Dictionary:
	var acc := {"top_o": 0.0, "top_p": 0.0, "top_n": 0, "mid_o": 0.0, "mid_p": 0.0, "mid_n": 0,
			"late_o": 0.0, "late_n": 0}
	for p in cls:
		var r := int(p["draft_rank"])
		var key := "top" if r <= 5 else ("mid" if r <= 20 else ("late" if r <= 40 else ""))
		if key == "":
			continue
		acc[key + "_o"] += float(p["overall"])
		if acc.has(key + "_p"):
			acc[key + "_p"] += float(maxi(int(p["overall"]), int(p["potential"])))
		acc[key + "_n"] += 1
	return acc


func _classes(scale: float) -> Array:
	var old := Prospects.DRAFT_NIGHT_SCALE
	Prospects.DRAFT_NIGHT_SCALE = scale
	var out: Array = []
	for y in range(2027, 2039):
		out.append_array(Prospects.age_pool(Prospects.generate_class(y, 900 + y), y, {}))
	Prospects.DRAFT_NIGHT_SCALE = old
	return out


func _real_class(scale: float) -> Array:
	var old := Prospects.DRAFT_NIGHT_SCALE
	Prospects.DRAFT_NIGHT_SCALE = scale
	var out: Array = []
	for p in GameDB.draftees:
		var q: Dictionary = (p as Dictionary).duplicate(true)
		Prospects.project(q)
		out.append(q)
	Prospects.DRAFT_NIGHT_SCALE = old
	return out


func _test_draftee_bands() -> void:
	var scale := Prospects.DRAFT_NIGHT_SCALE
	_check(GameDB.draftees.size() >= 40, "The real 2026 class is loaded (%d)" % GameDB.draftees.size())
	for arm in [["generated", _classes(scale), _classes(1.0)], ["real 2026", _real_class(scale), _real_class(1.0)]]:
		var now := _band_means(arm[1])
		var was := _band_means(arm[2])
		_check(int(now["top_n"]) >= 5 and int(now["mid_n"]) >= 15 and int(now["late_n"]) >= 20,
				"%s: every band has picks (%d, %d, %d)" % [arm[0], now["top_n"], now["mid_n"], now["late_n"]])
		var top: float = now["top_o"] / maxf(1.0, now["top_n"])
		var mid: float = now["mid_o"] / maxf(1.0, now["mid_n"])
		var late: float = now["late_o"] / maxf(1.0, now["late_n"])
		_check(BalanceGate.held(top >= 60.0 and top <= 62.5, "picks 1-5 draftee band"), "%s: picks 1-5 start about 60-62 (%.1f)" % [arm[0], top])
		_check(BalanceGate.held(mid >= 55.0 and mid <= 58.0, "picks 6-20 draftee band"), "%s: picks 6-20 start about 55-58 (%.1f)" % [arm[0], mid])
		_check(BalanceGate.held(late < mid - 2.0 and late >= 46.0, "picks 21-40 draftee band"), "%s: picks 21-40 start lower again, scaled the same way (%.1f)" % [arm[0], late])
		var old_top: float = was["top_o"] / maxf(1.0, was["top_n"])
		_check(BalanceGate.held(old_top - top >= 6.0, "picks 1-5 drop vs old curve"), "%s: picks 1-5 start lower than on the old curve (%.1f v %.1f)" % [arm[0], top, old_top])
		for b in ["top", "mid"]:
			var pot_now: float = now[b + "_p"] / maxf(1.0, now[b + "_n"])
			var pot_was: float = was[b + "_p"] / maxf(1.0, was[b + "_n"])
			_check(absf(pot_now - pot_was) <= 1.0, "%s: POT is kept in band %s (%.1f v %.1f)" % [arm[0], b, pot_now, pot_was])
	# A young player already on a real list is not a draft class: the scale never touches him.
	var young: Array = GameDB.list_additions.filter(func(q): return bool(q.get("projected", false)))
	_check(young.size() >= 5, "The real lists carry projected young players (%d)" % young.size())
	var same := true
	for q in young:
		var at_scale: Dictionary = (q as Dictionary).duplicate(true)
		var at_one: Dictionary = (q as Dictionary).duplicate(true)
		Prospects.project(at_scale)
		Prospects.DRAFT_NIGHT_SCALE = 1.0
		Prospects.project(at_one)
		Prospects.DRAFT_NIGHT_SCALE = scale
		if int(at_scale["overall"]) != int(at_one["overall"]) or int(at_scale["potential"]) != int(at_one["potential"]) 				or at_scale.has("night_drop"):
			same = false
	_check(same, "Listed young players on the real lists keep their rating and POT whatever the scale")
	# The pool year (row 65): a generated class is drafted at the rating it was made with, a year
	# older. Passed over, he plays no AFL games, so he earns no XP and stays
	# where he is (director 2026-11-17: a player grows only from the XP he earns).
	var fresh := Prospects.generate_class(2030, 4)
	var made: Dictionary = (fresh[0] as Dictionary).duplicate(true)
	var pooled: Array = Prospects.age_pool(fresh, 2030, {})
	var kid: Dictionary = pooled[0]
	_check(int(kid["overall"]) == int(made["overall"]) and int(kid["potential"]) == int(made["potential"])
			and is_equal_approx(float(kid["age"]), float(made["age"]) + 1.0),
			"His class's pool year ages him a year and leaves his rating (%d v %d)" % [int(kid["overall"]), int(made["overall"])])
	var grew := 0
	for q in Prospects.age_pool(pooled.duplicate(true), 2031, {}):
		var was: Dictionary = {}
		for r in pooled:
			if str(r["id"]) == str(q["id"]):
				was = r
		if not was.is_empty() and int(q["overall"]) > int(was["overall"]):
			grew += 1
	_check(grew == 0, "Passed over, a prospect does not grow without games (%d of %d grew)" % [grew, pooled.size()])


## Director 2026-10-14, "hold pick values where they are": a pick is read by the player it buys,
## so lowering the draft-night rating does not cheapen picks (today's values, 12 classes, a
## rebuilding club: pick 1 about 1.9, pick 10 about 1.3, pick 30 about 0.7).
func _pick_value_at(pick: int, scale: float) -> float:
	var old := Prospects.DRAFT_NIGHT_SCALE
	Prospects.DRAFT_NIGHT_SCALE = scale
	var t := 0.0
	for c in range(12):
		var ranked: Array = TradeValue.rank_prospects(Prospects.generate_class(2027 + c, 700 + c))
		t += TradeValue.pick_value([[pick, 1.0]], ranked, "rebuilding")
	Prospects.DRAFT_NIGHT_SCALE = old
	return t / 12.0


func _test_pick_values_held() -> void:
	for e in [[1, 1.9], [10, 1.3], [30, 0.7]]:
		var now := _pick_value_at(int(e[0]), Prospects.DRAFT_NIGHT_SCALE)
		var old := _pick_value_at(int(e[0]), 1.0)
		_check(BalanceGate.held(absf(now - float(e[1])) <= 0.15, "rebuilding-club pick value"), "Pick %d is worth about %.1f to a rebuilding club (%.2f)" % [int(e[0]), float(e[1]), now])
		_check(absf(now - old) <= 0.03 * old, "Pick %d is worth the same as on the old curve (%.2f v %.2f)" % [int(e[0]), now, old])


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
		if not p.has("potential") or int(p["potential"]) < int(p["overall"]):
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
	at_start["overall"] = int(orig["overall"])
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
