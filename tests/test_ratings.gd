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
	_t("_test_weighted_only")
	_t("_test_better_never_lower")
	_t("_test_derived_not_stored")
	_t("_test_out_of_position")
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


## The weights are shares: every attribute at 60 reads 60 at every position.
func _test_flat_reads_flat() -> void:
	for x in [30, 60, 90]:
		for apos in Rating.POSITIONS:
			_check(Rating.of_attrs(_flat(x), apos) == x, "a flat %d reads %d as a %s (%d)" % [
					x, x, apos, Rating.of_attrs(_flat(x), apos)])


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
			var want := int(round(50.0 + 40.0 * float(w.get(k, 0)) / 100.0))
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
		if int(Rating.ovr(p)) != Rating.of_attrs(p["attr"], Rating.apos_of(p)):
			wrong += 1
	_check(stored == 0, "no real player carries a stored OVR (%d do)" % stored)
	_check(wrong == 0, "every real player's OVR is his attributes at his position (%d differ)" % wrong)
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
	_check(Rating.at_line(kd, "DEF") == 80, "in his own line he reads his own OVR (%d)" % Rating.at_line(kd, "DEF"))
	_check(Rating.spot_position("Key Defender", "FWD") == "Key Forward", "a key defender up forward plays key forward (the closest)")
	var phys := {"apos": "Midfielder", "attr": _flat(0)}
	for k in Attributes.PHYSICAL:
		phys["attr"][k] = 80
	var fwd := Rating.spot_position("Midfielder", "FWD")
	_check(Rating.at_line(phys, "FWD") == Rating.of_attrs(phys["attr"], fwd),
			"Physical attributes carry to another line untouched (%d, want %d as a %s)" % [
					Rating.at_line(phys, "FWD"), Rating.of_attrs(phys["attr"], fwd), fwd])


## Selection rates a man at a slot by Rating.at_line, and the salary curve
## prices his derived OVR.
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
