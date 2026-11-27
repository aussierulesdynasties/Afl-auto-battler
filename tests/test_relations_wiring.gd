extends RefCounted
## Relationship overhaul, Phase 1 integration: the systems working together.
## Temperaments size opinion marks and how long they last, a drop, a trade, a
## delisting and a backing reach the men tied to the player (bonds), a broken
## promise costs Respect and builds no Authority, the selection preview gives
## the numbers the round applies, and the leader temperament sits at about
## four or five a club. Run through tests/run_relations_wiring_tests.gd.

var failures: Array[String] = []
var checks := 0
const SUITE_SEED := 2027


func run() -> void:
	failures.clear()
	checks = 0
	_t("_test_leaders_per_club")
	_t("_test_drop_mark_scaled")
	_t("_test_drop_reaches_mates")
	_t("_test_preview_matches_round")
	_t("_test_backing_reaches_mates")
	_t("_test_trade_reaches_mates")
	_t("_test_broken_word_no_authority")
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	print(Ran.line("Relations wiring", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _fresh() -> void:
	GameState.reset()
	GameState.replay_seed = SUITE_SEED
	GameState.stories_on = false
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	GameState._settle_week_event()
	GameState.week_event = {}


func _mark(id: String, k: String, src := "") -> Dictionary:
	for m in Opinion.mods(GameState.relations, Opinion.player_key(id)):
		if str(m.get("k", "")) == k and (src == "" or str(m.get("src", "")) == src):
			return m
	return {}


## A player at `code` with a mate at the same club: [player, mate id], or [].
func _with_mate(code: String, kinds := ["mate"]) -> Array:
	var club_of := GameState._bond_clubs()
	for p in GameState.season.lists[code]:
		for t in GameState.bond_ties(str(p["id"])):
			if kinds.has(str(t["kind"])) and str(club_of.get(str(t["id"]), "")) == code:
				return [p, str(t["id"])]
	return []


func _played(res: Dictionary, code: String) -> Dictionary:
	var side := 0 if str(res["home"]) == code else 1
	var out := {}
	for r in (res["roster"] as Array)[side]:
		out[str(r["id"])] = true
	return out


# ---------------------------------------------------------------------------

## The leader temperament is for the voices in the rooms: about four or five a
## club (director 2026-11-26), every named captain among them.
func _test_leaders_per_club() -> void:
	_fresh()
	var clubs: Dictionary = GameState.season.lists
	_check(clubs.size() == 18, "Every club is listed (%d)" % clubs.size())
	var total := 0
	var lo := 99
	var hi := 0
	for code in clubs:
		var n := 0
		for p in clubs[code]:
			if Temperament.has(p, "leader"):
				n += 1
			if Leadership.role_2026(p) == "captain":
				_check(Temperament.has(p, "leader"), "%s's captain is a leader" % code)
		total += n
		lo = mini(lo, n)
		hi = maxi(hi, n)
	print("Leaders: %d league-wide, %d to %d a club" % [total, lo, hi])
	_check(total >= 75 and total <= 95, "About four or five leaders a club, 75 to 95 league-wide (%d)" % total)
	_check(lo >= 1 and hi <= 9, "Every club has at least one and none is crowded with them (%d to %d)" % [lo, hi])


## A fit man left out takes a mark his temperament sizes, and fades at his pace.
func _test_drop_mark_scaled() -> void:
	_fresh()
	GameState.advance()
	var seen := 0
	var right := 0
	var differ := 0
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			var id := str(p["id"])
			for k in ["dropped", "dropped_star"]:
				var m := _mark(id, k, "")
				if m.is_empty() or str(m.get("src", "")) != "":
					continue
				seen += 1
				var d := Opinion.def(k)
				var want := clampf(float(d["v"]) * Temperament.scale(p, "dropped"), -Opinion.MOD_MAX, Opinion.MOD_MAX)
				var fade := float(d.get("fade", 1.0)) * Temperament.scale(p, "decay")
				if absf(float(m["v"]) - want) < 0.01 and absf(float(m["f"]) - fade) < 0.01:
					right += 1
				if absf(Temperament.scale(p, "dropped") - 1.0) > 0.01:
					differ += 1
	_check(seen > 200, "Left-out men across the league carry a mark (%d)" % seen)
	_check(right == seen, "Each is sized and faded by his temperament (%d of %d)" % [right, seen])
	_check(differ > 30, "...and temperaments really change the size for many of them (%d)" % differ)


## A drop reaches his close mate at the club, as a mark named for the moment.
func _test_drop_reaches_mates() -> void:
	_fresh()
	GameState.advance()
	var res: Dictionary = GameState.last_match
	var code := "GEE"
	var played := _played(res, code)
	var hits := 0
	var tried := 0
	for p in GameState.season.lists[code]:
		var id := str(p["id"])
		if played.has(id) or int(p.get("injury_weeks", 0)) > 0 or GameState._round_unavailable.has(id):
			continue
		for t in GameState.bond_ties(id):
			if str(t["kind"]) != "mate" or not GameState.season.lists[code].any(func(q): return str(q["id"]) == str(t["id"])):
				continue
			tried += 1
			var m := _mark(str(t["id"]), "mate_dropped", id)
			if not m.is_empty() and str(m["why"]).contains("You dropped his close mate"):
				hits += 1
	_check(tried > 0, "(setup) a left-out man has a close mate at the club (%d)" % tried)
	_check(hits == tried, "Every such mate carries it, in football words (%d of %d)" % [hits, tried])
	var any_rival := false
	for code2 in GameState.season.lists:
		if code2 == code:
			continue
		for q in GameState.season.lists[code2]:
			for m in Opinion.mods(GameState.relations, Opinion.player_key(str(q["id"]))):
				if str(m.get("k", "")) == "mate_dropped":
					any_rival = true
	_check(any_rival, "Rival clubs' drops reach their players' mates too (every club)")


## The Team selection preview's mate lines are the moves the round makes.
func _test_preview_matches_round() -> void:
	_fresh()
	var pick := []
	for p in GameState.my_list:
		if GameState.in_current_side(p) and int(p.get("injury_weeks", 0)) <= 0:
			var moves := GameState.bond_fallout_moves(str(p["id"]), "drop")
			if not moves.is_empty():
				pick = [p, moves]
				break
	_check(not pick.is_empty(), "(setup) a man in the side has someone tied to him at the club")
	if pick.is_empty():
		return
	var p: Dictionary = pick[0]
	var rel0: Dictionary = GameState.relations.duplicate(true)
	var pv := RelationsView.drop_preview(GameState, p, GameState.relations)
	_check(GameState.relations == rel0, "The preview changes nothing")
	_check((pv["fallout"] as Array).size() == (pick[1] as Array).size(), "The preview lists each man it reaches")
	var club_of := GameState._bond_clubs()
	var before := {}
	for f in pick[1]:
		before[str(f["id"])] = Opinion.coach_opinion(GameState.relations, Opinion.player_key(str(f["id"])), true)
	GameState.apply_bond_fallout(str(p["id"]), "drop", club_of)
	var same := 0
	for f in pv["fallout"]:
		var now := Opinion.coach_opinion(GameState.relations, Opinion.player_key(str(f["id"])), true)
		if now - int(before[str(f["id"])]) == int(f["opinion"]):
			same += 1
	_check(same == (pv["fallout"] as Array).size(), "Each line's number is the move applied (%d of %d)" % [same, (pv["fallout"] as Array).size()])
	var own := Opinion.preview(GameState.relations, Opinion.player_key(str(p["id"])),
			Opinion.drop_mark(int(Rating.ovr(p, 0)), false, RelationsView.STAR_OVR), Temperament.scale(p, "dropped"))
	_check(int(pv["opinion"]) == own, "His own line is sized by his temperament (%d)" % own)


## Backing a player pleases his mates and needles his rival for the spot.
func _test_backing_reaches_mates() -> void:
	_fresh()
	var pair := []
	var club_of := GameState._bond_clubs()
	for q in GameState.my_list:
		if not Ratings.available(q):
			continue
		for t in GameState.bond_ties(str(q["id"])):
			if str(t["kind"]) == "mate" and str(club_of.get(str(t["id"]), "")) == "GEE":
				pair = [q, str(t["id"])]
		if not pair.is_empty():
			break
	_check(not pair.is_empty(), "(setup) a GEE player you can back with a close mate at the club")
	if pair.is_empty():
		return
	var p: Dictionary = pair[0]
	# A young man with a career on record and few games: one you can back.
	p["career"] = {"games": 2, "goals": 0, "stints": [], "through": GameState.season_year - 1, "unknown": []}
	p.erase("backed")
	_check(GameState.back_player(str(p["id"])) != "", "(setup) he is backed")
	var m := _mark(str(pair[1]), "mate_backed", str(p["id"]))
	_check(not m.is_empty() and float(m["v"]) > 0.0, "His mate takes the backing well (%s)" % str(m))
	_check(not m.is_empty() and str(m["why"]).contains("You backed his close mate"), "...in football words")


## A trade reaches the men tied to him at the club that let him go, and only them.
func _test_trade_reaches_mates() -> void:
	_fresh()
	var pair := _with_mate("COL")
	_check(not pair.is_empty(), "(setup) a COL player with a close mate at the club")
	if pair.is_empty():
		return
	var p: Dictionary = pair[0]
	var id := str(p["id"])
	var club_of := GameState._bond_clubs()
	var reached := []
	for f in Bonds.fallout(Bonds.ensure(GameState.bonds), id, "trade", club_of):
		reached.append(str(f["id"]))
	GameState._execute_trade("COL", "CAR", [p], [])
	var m := _mark(str(pair[1]), "mate_traded", id)
	_check(not m.is_empty() and float(m["v"]) < 0.0 and str(m.get("c", "")) == "COL",
			"His close mate at Collingwood takes it hard (%s)" % str(m))
	var elsewhere := 0
	for oid in reached:
		if str(club_of.get(oid, "")) != "COL":
			for mm in Opinion.mods(GameState.relations, Opinion.player_key(str(oid))):
				if str(mm.get("src", "")) == id:
					elsewhere += 1
	_check(elsewhere == 0, "Nobody at another club carries a mark for it (%d)" % elsewhere)


## Breaking your word costs Respect and builds no Authority (director 2026-11-26).
func _test_broken_word_no_authority() -> void:
	_fresh()
	var p := {}
	for q in GameState.my_list:
		if Ratings.available(q):
			p = q
	var a0 := Promises.authority(GameState)
	var r0 := Promises.respect(GameState)
	Promises.settle(GameState, p, "game", "broken")
	_check(Promises.authority(GameState) == a0, "Authority unchanged (%d -> %d)" % [a0, Promises.authority(GameState)])
	_check(Promises.respect(GameState) == r0 + int(Promises.BROKEN["game"][0]), "Respect falls (%d -> %d)" % [r0, Promises.respect(GameState)])
	var w := Promises.witnesses(GameState, p)
	_check(not w.is_empty(), "(setup) he has line-mates")
	if not w.is_empty():
		var m := _mark(str(w[0]["id"]), "saw_promise_broken")
		var want := float(Opinion.def("saw_promise_broken")["v"]) * Temperament.scale(w[0], "promise_broken")
		_check(not m.is_empty() and absf(float(m["v"]) - clampf(want, -40.0, 40.0)) < 0.01,
				"A teammate who saw it takes a mark his temperament sizes (%s)" % str(m))
