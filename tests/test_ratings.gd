extends RefCounted
## The overall rating is read from the attributes and nothing else (Director
## Bible 4.2.30a, docs/RATING_REBUILD.md §2-§3): each position's weights add to
## 100, a flat 60 reads 60 everywhere, an attribute moves only the positions
## that weigh it, out of position takes the director's share off Technical and
## Footy IQ only, selection and pay read the same derived number, and a save
## never carries an OVR of its own. Run through tests/run_ratings_tests.gd.

var failures: Array[String] = []
var checks := 0

## Every season here is seeded (C15): a clock seed makes a different league
## each run.
const SUITE_SEED := 2027


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	_t("_test_weights")
	_t("_test_flat_reads_flat")
	_t("_test_stretch")
	_t("_test_weighted_only")
	_t("_test_better_never_lower")
	_t("_test_derived_not_stored")
	_t("_test_out_of_position")
	_t("_test_match_reads_the_cut")
	_t("_test_dual_roles")
	_t("_test_team_strength_reads_the_cut")
	_t("_test_work_rate_in_match")
	_t("_test_worth_economy")
	_t("_test_ageing_clean_up")
	_t("_test_draftee_hybrids")
	_t("_test_selection_and_pay_read_it")
	_t("_test_save_carries_no_ovr")
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	print(Ran.line("Ratings", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


## Every attribute at `x`.
func _flat(x: int) -> Dictionary:
	var a := {}
	for k in Attributes.KEYS:
		a[k] = x
	return a


## Seven positions, each weighting real attributes, each adding to 100.
func _test_weights() -> void:
	_check(Rating.POSITIONS.size() == 7, "seven AFL positions (%d)" % Rating.POSITIONS.size())
	for apos in Rating.POSITIONS:
		var w: Dictionary = Rating.WEIGHTS.get(apos, {})
		var total := 0
		var known := true
		for k in w:
			total += int(w[k])
			known = known and Attributes.KEYS.has(k)
		_check(total == 100, "%s's weights add to 100 (%d)" % [apos, total])
		_check(known, "%s weighs only the 18 attributes" % apos)
		_check(not w.has("durability"), "%s gives Durability no share of OVR (it is priced in Worth)" % apos)


## The weights are shares: every attribute at 60 is a weighted sum of 60 at
## every position, which the stretch reads as 72.
func _test_flat_reads_flat() -> void:
	for x in [30, 60, 90]:
		for apos in Rating.POSITIONS:
			_check(is_equal_approx(Rating.raw_of(_flat(x), apos), float(x))
					and Rating.of_attrs(_flat(x), apos) == int(round(Rating.stretch(float(x)))),
					"a flat %d is a weighted sum of %d as a %s, OVR %d" % [x, x, apos, Rating.of_attrs(_flat(x), apos)])


## The director's stretch (2026-11-26): replacement level 53 reads 62, a solid
## regular 60 reads 72, a star 67 reads 80-82, a generational superstar 72
## reads 89-92; never down, and the same curve run backwards.
func _test_stretch() -> void:
	_check(Rating.of_attrs(_flat(53), "Midfielder") == 62, "a weighted sum of 53 reads 62 (%d)" % Rating.of_attrs(_flat(53), "Midfielder"))
	_check(Rating.of_attrs(_flat(60), "Midfielder") == 72, "60 reads 72 (%d)" % Rating.of_attrs(_flat(60), "Midfielder"))
	var star := Rating.of_attrs(_flat(67), "Midfielder")
	_check(star >= 80 and star <= 82, "67 reads a star's 80-82 (%d)" % star)
	var great := Rating.of_attrs(_flat(72), "Midfielder")
	_check(great >= 89 and great <= 92, "72 reads a generational 89-92 (%d)" % great)
	_check(int(round(Rating.stretch(63.5))) == 77, "the worked example: 63.5 reads 77 (%.1f)" % Rating.stretch(63.5))
	var past := Rating.of_attrs(_flat(76), "Midfielder")
	_check(past >= 90 and past <= 93, "past a generational sum the climb flattens: 76 reads %d" % past)
	_check(int(round(Rating.stretch(86.8))) == 99, "the best season on record (86.8) reads 99 (%.1f)" % Rating.stretch(86.8))
	var up := true
	var back := true
	var last := -1.0
	for i in range(100, 990):
		var raw := float(i) / 10.0
		var o := Rating.stretch(raw)
		up = up and o >= last
		last = o
		if o > 1.0 and o < 99.0:
			back = back and absf(Rating.unstretch(o) - raw) < 0.001
	_check(up, "the stretch never reads a bigger sum lower")
	_check(back, "unstretch runs it backwards")
	_check(Rating.stretch(1.0) == 1.0 and Rating.stretch(99.0) == 99.0, "it stays within 1-99")


## Raising an attribute lifts a position by its weight, and leaves a position
## that gives it no weight exactly where it was.
func _test_weighted_only() -> void:
	var lifted := 0
	var still := 0
	for apos in Rating.POSITIONS:
		var w: Dictionary = Rating.WEIGHTS[apos]
		for k in Attributes.KEYS:
			var a := _flat(50)
			a[k] = 90
			var got := Rating.of_attrs(a, apos)
			var want := int(round(Rating.stretch(50.0 + 40.0 * float(w.get(k, 0)) / 100.0)))
			if got != want:
				_check(false, "%s at 90 makes a %s %d, want %d" % [k, apos, got, want])
			elif w.has(k):
				lifted += 1
			else:
				still += 1
	_check(lifted > 50 and still > 30, "each attribute moves exactly the positions that weigh it (%d lifted, %d unmoved)" % [lifted, still])


## A better player never rates lower: every attribute up one never takes
## OVR down, at any position.
func _test_better_never_lower() -> void:
	var mono := true
	for apos in Rating.POSITIONS:
		var last := -1
		for x in range(1, 100):
			var y := Rating.of_attrs(_flat(x), apos)
			mono = mono and y >= last
			last = y
	_check(mono, "a better player never rates lower")


## OVR is worked out when it is read: a player dictionary has no "overall",
## and one written there by mistake is ignored.
func _test_derived_not_stored() -> void:
	var players: Array = GameDB.players
	_check(players.size() > 500, "the league has its players (%d)" % players.size())
	var stored := 0
	var wrong := 0
	for p in players:
		if (p as Dictionary).has("overall"):
			stored += 1
		var best := Rating.of_attrs(p["attr"], Rating.apos_of(p))
		for line in Rating.second_lines(p):
			for apos in Rating.LINE_POSITIONS[line]:
				best = maxi(best, Rating.of_attrs(p["attr"], apos))
		if int(Rating.ovr(p)) != best:
			wrong += 1
	_check(stored == 0, "no real player carries a stored OVR (%d do)" % stored)
	_check(wrong == 0, "every real player's OVR is his attributes at his best eligible position (%d differ)" % wrong)
	var p: Dictionary = (players[0] as Dictionary).duplicate(true)
	var right := int(Rating.ovr(p))
	p["overall"] = 99
	_check(int(Rating.ovr(p)) == right, "a stray stored 99 does not change his OVR (%d)" % int(Rating.ovr(p)))
	_check(Rating.ovr({}) == null and Rating.ovr({}, 40) == 40, "no attributes reads the fallback")


## The director's out-of-position shares (2026-11-25): 5% a step, Ruck 25%,
## key defender to key forward 10%, a key player into the midfield 20%; taken
## off Technical and Footy IQ only.
func _test_out_of_position() -> void:
	_check(is_equal_approx(Rating.cut("Gen. Defender", "Midfielder"), 0.05), "one step along the ground costs 5%")
	_check(is_equal_approx(Rating.cut("Gen. Defender", "Gen. Forward"), 0.15), "three steps cost 15%")
	_check(is_equal_approx(Rating.cut("Key Defender", "Key Forward"), 0.10)
			and is_equal_approx(Rating.cut("Key Forward", "Key Defender"), 0.10), "a swingman costs 10% either way")
	_check(is_equal_approx(Rating.cut("Key Defender", "Midfielder"), 0.20)
			and is_equal_approx(Rating.cut("Key Forward", "Midfielder"), 0.20), "a key player in the midfield costs 20%")
	var rucks := true
	for apos in Rating.POSITIONS:
		if apos != "Ruck":
			rucks = rucks and is_equal_approx(Rating.cut(apos, "Ruck"), 0.25) and is_equal_approx(Rating.cut("Ruck", apos), 0.25)
	_check(rucks, "into or out of the ruck costs 25%")
	_check(is_equal_approx(Rating.cut("Midfielder", "Midfielder"), 0.0), "his own position costs nothing")
	# A Key Defender with 80 in everything, in the midfield: Technical and Footy
	# IQ at 64, Physical and Mental untouched, rated as a Midfielder.
	var kd := {"apos": "Key Defender", "attr": _flat(80)}
	var a := _flat(80)
	for k in Attributes.TECHNICAL + Attributes.FOOTY_IQ:
		a[k] = 64
	_check(Rating.at_line(kd, "MID") == Rating.of_attrs(a, "Midfielder"),
			"a key defender in the midfield is rated a Midfielder with his skills 20%% down (%d, want %d)" % [
					Rating.at_line(kd, "MID"), Rating.of_attrs(a, "Midfielder")])
	_check(Rating.at_line(kd, "DEF") == Rating.ovr(kd), "in his own line he reads his own OVR (%d)" % Rating.at_line(kd, "DEF"))
	_check(Rating.spot_position("Key Defender", "FWD") == "Key Forward", "a key defender up forward plays key forward (the closest)")
	var phys := {"apos": "Midfielder", "attr": _flat(0)}
	for k in Attributes.PHYSICAL:
		phys["attr"][k] = 80
	var fwd := Rating.spot_position("Midfielder", "FWD")
	_check(Rating.at_line(phys, "FWD") == Rating.of_attrs(phys["attr"], fwd),
			"Physical attributes carry to another line untouched (%d, want %d as a %s)" % [
					Rating.at_line(phys, "FWD"), Rating.of_attrs(phys["attr"], fwd), fwd])


## The match plays the same cut (mandate 2: the same 80 Kicking kicks the same
## for everyone, changed only by live state and out of position): a key
## defender picked in the midfield kicks 20% down and runs as fast as ever.
func _test_match_reads_the_cut() -> void:
	var cut_keys: Array = Attributes.TECHNICAL + Attributes.FOOTY_IQ + ["disposal"]
	_check(Attributes.CUT_BY_POSITION.size() == cut_keys.size() and cut_keys.all(func(k): return Attributes.CUT_BY_POSITION.has(k)),
			"the match cuts what OVR cuts: Technical, Footy IQ and ball use (%d keys)" % Attributes.CUT_BY_POSITION.size())
	var sim := MatchSim.new(Squad.new("GEE", GameDB.club_list("GEE"), true, "GEE"),
			Squad.new("COL", GameDB.club_list("COL"), false, "COL"), SUITE_SEED)
	var home := {"id": "cut_home", "apos": "Key Defender", "role": "DEF", "attr": _flat(80)}
	var away := home.duplicate(true)
	away["id"] = "cut_away"
	away["role"] = "MID"
	var kick: float = sim._a(away, "kicking") / sim._a(home, "kicking")
	var run: float = sim._a(away, "speed") / sim._a(home, "speed")
	_check(is_equal_approx(kick, 0.80), "his kicking plays 20%% down in the midfield (x%.2f)" % kick)
	_check(is_equal_approx(run, 1.0), "his speed plays the same (x%.2f)" % run)
	var mid := {"id": "cut_mid", "apos": "Midfielder", "role": "MID", "attr": _flat(80)}
	_check(is_equal_approx(sim._a(mid, "kicking"), sim._a(home, "kicking")),
			"the same 80 Kicking kicks the same for a midfielder and a key defender in their own spots")


## Dual roles (director 2026-11-28, decisions 1-3): a Mid-Forward plays
## forward; a ruck who kicks goals and a key forward who rucks get the other
## line; no cut in a second or learned line, where he counts as the line's
## position he rates best at; his headline OVR is the best of them; an
## unlearned line still takes the cut.
func _test_dual_roles() -> void:
	var by := {}
	for p in GameDB.players:
		by[str(p["id"])] = p
	var wright: Dictionary = by.get("ESS_20", {})
	var jackson: Dictionary = by.get("FRE_9", {})
	var thilthorpe: Dictionary = by.get("ADE_7", {})
	_check(str(wright.get("apos", "")) == "Ruck" and str(wright.get("role2", "")) == "FWD",
			"Peter Wright is a ruck with a second line forward")
	_check(Rating.line_cut(wright, "FWD") == 0.0, "no cut for him up forward (%.2f)" % Rating.line_cut(wright, "FWD"))
	_check(Rating.at_line(wright, "FWD") == Rating.of_attrs(wright["attr"], "Key Forward"),
			"up forward he counts as a key forward (%d)" % Rating.at_line(wright, "FWD"))
	_check(int(Rating.ovr(wright)) == Rating.of_attrs(wright["attr"], "Key Forward")
			and int(Rating.ovr(wright)) > Rating.of_attrs(wright["attr"], "Ruck"),
			"his headline OVR is his key forward OVR (%d), not his ruck OVR (%d)" % [
					int(Rating.ovr(wright)), Rating.of_attrs(wright["attr"], "Ruck")])
	var card := PlayerSheet.line_ratings_text(wright)
	_check(card == "Forward %d, Ruck %d." % [Rating.of_attrs(wright["attr"], "Key Forward"), Rating.of_attrs(wright["attr"], "Ruck")],
			"his card shows both lines, best first (%s)" % card)
	_check(str(jackson.get("role2", "")) == "FWD",
			"Luke Jackson's goals (%s in %s games) make him a ruck-forward" % [jackson.get("gl"), jackson.get("gm")])
	_check(str(thilthorpe.get("role2", "")) == "RUCK",
			"Riley Thilthorpe's hitouts (%s in %s games) make him a forward-ruck" % [thilthorpe.get("ho"), thilthorpe.get("gm")])
	var mf := 0
	var mf_fwd := 0
	for p in GameDB.players:
		if str(p.get("apos", "")) == "Mid-Forward":
			mf += 1
			if Ratings.positions(p).has("FWD") and Ratings.plays_role(p, "FWD") and Traits.plays(p, "FWD") \
					and Rating.line_cut(p, "FWD") == 0.0:
				mf_fwd += 1
	_check(mf > 30 and mf_fwd == mf, "every Mid-Forward can be picked forward with no cut (%d of %d)" % [mf_fwd, mf])
	# A Midfielder who learned the back line: no cut there, rated his best back
	# position; the forward line he never learned still takes the cut.
	var mid := {"id": "learn_mid", "apos": "Midfielder", "role": "MID", "learned": ["DEF"], "attr": _flat(70)}
	mid["attr"]["reading_play"] = 90
	_check(Rating.line_cut(mid, "DEF") == 0.0, "a learned line takes no cut")
	_check(Rating.at_line(mid, "DEF") == maxi(Rating.of_attrs(mid["attr"], "Key Defender"), Rating.of_attrs(mid["attr"], "Gen. Defender")),
			"in a learned line he counts as the line's position he rates best at")
	_check(is_equal_approx(Rating.line_cut(mid, "FWD"), Rating.cut("Midfielder", Rating.spot_position("Midfielder", "FWD"))),
			"a line he never learned still takes the cut (%.2f)" % Rating.line_cut(mid, "FWD"))
	_check(GameState.rating_as(mid, "FWD") == Rating.best_in_line(mid["attr"], "FWD"),
			"learning a line is judged without the cut (%d)" % GameState.rating_as(mid, "FWD"))
	# The match reads the same: no cut in his second line.
	var sim := MatchSim.new(Squad.new("GEE", GameDB.club_list("GEE"), true, "GEE"),
			Squad.new("COL", GameDB.club_list("COL"), false, "COL"), SUITE_SEED)
	var w_fwd: Dictionary = wright.duplicate()
	w_fwd["role"] = "FWD"
	w_fwd["own_role"] = "RUCK"
	_check(is_equal_approx(sim._a_fresh(w_fwd, "goalkicking"), float(wright["attr"]["goalkicking"])),
			"Peter Wright kicks for goal at his own %d up forward (%.1f)" % [wright["attr"]["goalkicking"], sim._a_fresh(w_fwd, "goalkicking")])


## Team strength reads the out-of-position cut the match plays (plan step 1):
## a key defender in the midfield adds less contested ball than his raw 80.
func _test_team_strength_reads_the_cut() -> void:
	var kd := {"id": "ts_kd", "apos": "Key Defender", "role": "MID", "attr": _flat(80)}
	var mid := {"id": "ts_mid", "apos": "Midfielder", "role": "MID", "attr": _flat(80)}
	var v_kd := Squad._mean([kd], "contested_ball")
	var v_mid := Squad._mean([mid], "contested_ball")
	_check(is_equal_approx(v_kd, 64.0) and is_equal_approx(v_mid, 80.0),
			"a key defender's 80 contested ball counts 64 in the midfield, a midfielder's 80 (%.1f, %.1f)" % [v_kd, v_mid])
	_check(is_equal_approx(Squad._mean([kd], "speed"), 80.0), "his speed counts in full")


## Work Rate plays (plan step 2): a hard-running side presses a chain's
## second disposal on harder, and its own runners take the pressure off an
## uncontested receive. A side of league-average runners plays as before.
func _test_work_rate_in_match() -> void:
	# Measured first, before the sides below change their players. The neutral
	# point is the picked sides' average, not the list's (issue #2344): the 18
	# clubs' auto-picked 18 average 41.9 before the day's tiredness, 41.35 as the
	# match reads them.
	var total := 0.0
	var count := 0
	for code in GameDB.club_order:
		if GameDB.club_list(code).is_empty():
			continue
		for q in Squad.new(code, GameDB.club_list(code), false, code).ground:
			total += float(q["attr"].get("work_rate", 50))
			count += 1
	var picked := total / float(maxi(1, count))
	_check(absf(picked - MatchSim.WORK_RATE_LEAGUE) < 1.0, "the Work Rate anchor sits at the picked sides' average (%.2f vs %.1f)" % [picked, MatchSim.WORK_RATE_LEAGUE])
	var make := func(home_wr: float, away_wr: float) -> MatchSim:
		var sim := MatchSim.new(Squad.new("GEE", GameDB.club_list("GEE"), true, "GEE"),
				Squad.new("COL", GameDB.club_list("COL"), false, "COL"), SUITE_SEED)
		for side in range(2):
			for q in (sim.squads[side] as Squad).ground:
				var a: Dictionary = (q["attr"] as Dictionary).duplicate()
				a["work_rate"] = home_wr if side == 0 else away_wr
				q["attr"] = a
		return sim
	var avg: MatchSim = make.call(MatchSim.WORK_RATE_LEAGUE, MatchSim.WORK_RATE_LEAGUE)
	var hard: MatchSim = make.call(MatchSim.WORK_RATE_LEAGUE, 80.0)
	var soft: MatchSim = make.call(MatchSim.WORK_RATE_LEAGUE, 10.0)
	_check(absf(avg._work_press(0, 1, 1, 3, "up") - 1.0) < 0.005, "league-average runners (attributes are whole numbers) change next to nothing (%.3f)" % avg._work_press(0, 1, 1, 3, "up"))
	_check(is_equal_approx(hard._work_press(0, 1, 1, 1, ""), 1.0), "a chain's first disposal takes no repeat pressure")
	var h := hard._work_press(0, 1, 1, 3, "")
	var l := soft._work_press(0, 1, 1, 3, "")
	_check(h > 1.0 and l < 1.0, "the hard-running side presses the third kick harder, the soft side less (%.3f, %.3f)" % [h, l])
	var up: MatchSim = make.call(80.0, MatchSim.WORK_RATE_LEAGUE)
	_check(up._work_press(0, 1, 1, 1, "up") < 1.0, "our own runners ease an uncontested receive (%.3f)" % up._work_press(0, 1, 1, 1, "up"))


## Worth (plan step 5, RATING_REBUILD.md Economy): 0.50 OVR + 0.20 Form +
## 0.30 POT, less 1.5 a year past 29, times the durability factor; asking
## salary from Worth; the trade value reads the same durability factor.
func _test_worth_economy() -> void:
	_check(is_equal_approx(Contracts.durability_factor(20.0), 0.85) and is_equal_approx(Contracts.durability_factor(75.0), 1.0)
			and is_equal_approx(Contracts.durability_factor(95.0), 1.05), "durability 20, 75, 95 is 0.85, 1.00, 1.05")
	_check(is_equal_approx(Contracts.durability_factor(0.0), 0.85) and is_equal_approx(Contracts.durability_factor(99.0), 1.05),
			"and holds past the ends")
	var p := {"id": "w_1", "apos": "Midfielder", "role": "MID", "age": 31.0, "potential": 80, "attr": _flat(70)}
	p["attr"]["durability"] = 75
	var ov := float(Rating.ovr(p))
	_check(is_equal_approx(Contracts.form(p), ov), "under five games his Form is his OVR")
	for i in range(12):
		Contracts.note_form(p, 50.0 + i)
	_check((p["worth_form"] as Array).size() == Contracts.FORM_GAMES and is_equal_approx(Contracts.form(p), 56.5),
			"Form is his last ten games (%.1f)" % Contracts.form(p))
	var want := 0.5 * ov + 0.2 * 56.5 + 0.3 * maxf(ov, 80.0) - 1.5 * 2.0
	_check(is_equal_approx(Contracts.worth(p), want), "Worth is the plan's blend (%.2f, %.2f)" % [Contracts.worth(p), want])
	var frail := p.duplicate(true)
	frail["attr"]["durability"] = 20
	_check(is_equal_approx(Contracts.worth(frail), want * 0.85), "an injury-prone man is worth 15% less")
	_check(Contracts.asking_salary(p) == Contracts.asking_at(p, roundi(want)), "he asks the price of his Worth")
	_check(Contracts.asking_salary(frail) < Contracts.asking_salary(p), "and the frail one asks less")
	var tv_frail := float(TradeValue.value(frail, {"phase": "rebuilding", "games": -1})["total"])
	var tv := float(TradeValue.value(p, {"phase": "rebuilding", "games": -1})["total"])
	var tc_frail := float(TradeValue.value(frail, {"phase": "contending", "games": -1})["total"])
	var tc := float(TradeValue.value(p, {"phase": "contending", "games": -1})["total"])
	_check(is_equal_approx(tv_frail / tv, 0.85) and is_equal_approx(tc_frail / tc, 0.85),
			"a trade takes the same 15%% off his whole value, rebuilder or contender (%.3f, %.3f)" % [tv_frail / tv, tc_frail / tc])


## The ageing clean-up (plan step 4): past 34 every attribute takes the pooled
## old-age change, never a rise; Fine Wine never ages faster than a normal
## player; a rehab player comes back toward his potential at the summer.
func _test_ageing_clean_up() -> void:
	var rises := []
	for k in Attributes.KEYS:
		for age in [35, 37, 40]:
			if Growth.season_change(k, age, false) > 0.0:
				rises.append("%s %d" % [k, age])
	_check(rises.is_empty(), "no attribute rises past 34 (%s)" % ", ".join(rises))
	var faster := []
	for k in Attributes.KEYS:
		for age in range(27, 38):
			if Growth.season_change(k, age, true) < Growth.season_change(k, age, false) - 0.0001:
				faster.append("%s %d" % [k, age])
	_check(faster.is_empty(), "Fine Wine never ages faster than normal (%s)" % ", ".join(faster))
	var r := {"id": "rb_1", "apos": "Midfielder", "role": "MID", "age": 24.0, "potential": 80, "rehab": true, "attr": _flat(50)}
	var before := int(Rating.ovr(r))
	Growth.rehab_bounce(r)
	_check(not r.has("rehab") and int(Rating.ovr(r)) > before, "a rehab player comes back higher (%d to %d)" % [before, int(Rating.ovr(r))])
	_check(int(Rating.ovr(r)) <= 80, "never past his potential (%d)" % int(Rating.ovr(r)))
	# A retiring hybrid falls from his own position, not his headline
	# (independent review, 2026-11-28): Peter Wright, ruck 47 and forward 65.
	var wright := {}
	for q in GameDB.players:
		if str(q.get("real_name", "")) == "Peter Wright":
			wright = (q as Dictionary).duplicate(true)
	_check(not wright.is_empty(), "Peter Wright is on a list")
	if not wright.is_empty():
		wright["career_last"] = 2000.0
		var head := int(Rating.ovr(wright))
		var own := int(Rating.ovr_at_own(wright))
		Growth.summer(wright, 2027)
		_check(int(Rating.ovr(wright)) < head and int(Rating.ovr_at_own(wright)) < own,
				"his last summer brings him down, both lines (%d to %d, ruck %d to %d)" % [head, int(Rating.ovr(wright)), own, int(Rating.ovr_at_own(wright))])


## Selection rates a man at a slot by Rating.at_line, and the salary curve
## prices his derived OVR.
## Generated draftees get a second line about as often as real players do, and
## only in pairs real players of their position have (director review
## 2026-11-28, issue #2344: "plausible hybrid archetypes", tighten if over 30%).
func _test_draftee_hybrids() -> void:
	var real_pairs := {
		"Gen. Defender": ["MID", "FWD"], "Key Defender": ["FWD", "RUCK"],
		"Gen. Forward": ["MID", "DEF"], "Key Forward": ["RUCK", "DEF"],
		"Midfielder": ["DEF", "FWD"], "Ruck": ["FWD", "DEF"]}
	var n := 0
	var hybrids := 0
	var odd := []
	for y in range(2027, 2032):
		var pool: Array = Prospects.generate_class(y, 11)
		pool.append_array(Prospects.generate_expansion_list("TAS", y, 36, "t%d" % y))
		for p in pool:
			n += 1
			var r2 := str(p.get("role2", ""))
			if r2 == "":
				continue
			hybrids += 1
			var apos := Rating.apos_of(p)
			if not (real_pairs.get(apos, []) as Array).has(r2):
				odd.append("%s+%s" % [apos, r2])
	var rate := float(hybrids) / float(maxi(1, n))
	_check(n >= 300 and rate >= 0.15 and rate <= 0.30, "draftees with a second line: %.1f%% of %d" % [rate * 100.0, n])
	_check(odd.is_empty(), "draftee second lines are real pairs (%s)" % ", ".join(odd))


func _test_selection_and_pay_read_it() -> void:
	var n := 0
	var same := true
	var paid := true
	for p in GameDB.players:
		n += 1
		for line in ["DEF", "MID", "FWD", "RUCK"]:
			same = same and is_equal_approx(Ratings.line_rating(p, line), float(Rating.at_line(p, line)))
		paid = paid and Ratings.value_of(p) == Ratings.salary_value(int(Rating.ovr(p)))
	_check(n > 500, "rated the league (%d)" % n)
	_check(same, "selection's rating at a slot is Rating.at_line")
	_check(paid, "his value is the salary curve at his derived OVR")


## A save writes attributes, never an OVR, and a loaded player reads the same
## OVR he had.
func _test_save_carries_no_ovr() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var p: Dictionary = GameState.my_list[0]
	var id := str(p["id"])
	var right := int(Rating.ovr(p))
	p["overall"] = right - 7          # as an older build might have written it
	GameState.save_career()
	_check(FileAccess.file_exists(GameState.save_path), "the career saved")
	GameState.load_career()
	var q := GameState.list_player(id)
	_check(not q.is_empty() and not q.has("overall"), "the stray OVR is not written, so a loaded player has none")
	_check(int(Rating.ovr(q)) == right, "his OVR reads the same after a load (%d, was %d)" % [int(Rating.ovr(q)), right])
