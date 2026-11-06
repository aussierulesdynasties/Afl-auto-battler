extends RefCounted
## Run by tests/run_key_duels_tests.gd (suite "key_duels").
## Key forward v key defender (row 94, T8.Q6, director 2026-11-06): a key
## forward and his direct opponent meet
## more often (his marking contests up the ground are against his man, and
## sides look for him more inside 50), every contest the full-time line counts
## traces to the play, and the line's "N marks from M contests" is the log.

var _tree: SceneTree
var checks := 0
var failures: Array[String] = []
## The seeds and lists the matches are played on.
const SEEDS := [9401, 9402, 9403, 9404, 9405, 9406, 9407, 9408]
## Matches for the contests-per-duel comparison (seeds 9401 on).
const MORE := 24
const PAIRS := [["COL", "CAR"], ["GEE", "SYD"], ["BRL", "MEL"], ["HAW", "WCE"],
		["FRE", "ADE"], ["STK", "ESS"], ["GWS", "NTH"], ["RIC", "WBD"]]


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func run(tree: SceneTree) -> void:
	_tree = tree
	await _tree.process_frame
	GameDB.skip_ovr_overrides = true
	GameDB.reload()
	_t("_test_key_target")
	_t("_test_more_contests")
	_t("_test_contests_trace_to_play")
	_t("_test_no_lead_at_own_kick")
	_t("_test_line_reads_the_log")
	_t("_test_defenders_by_trade")
	_t("_test_key_defender_takes_key_forward")
	_t("_test_rematch_and_refill_keep_defenders")
	_t("_test_bench_for_back_slot")
	_t("_test_duel_handed_on_at_interchange")
	_t("_test_oval_back_line_by_trade")
	print(Ran.line("Key duels", self))
	for f in failures:
		print("  FAIL: " + f)


## One match per seed: [sim, result].
func _play(i: int) -> Array:
	var p: Array = PAIRS[i % PAIRS.size()]
	var h := str(p[0])
	var a := str(p[1])
	var sim := MatchSim.new(Squad.new(h, GameDB.club_list(h), true, h),
			Squad.new(a, GameDB.club_list(a), false, a), 9401 + i)
	var r: Dictionary = sim.run()
	return [sim, r]


## Contests per key forward who had a direct opponent, over one match.
func _per_duel(sim: MatchSim, r: Dictionary) -> Array:
	var out := []
	for side in range(2):
		for fid in (sim.duels[side] as Dictionary):
			out.append(int(MatchNotes.duel_tally(r, str(fid))[0]))
	return out


func _mean(a: Array) -> float:
	var s := 0.0
	for x in a:
		s += float(x)
	return s / maxf(1.0, float(a.size()))


func _test_key_target() -> void:
	var m := MatchSim.new(Squad.new("COL", GameDB.club_list("COL"), true, "COL"),
			Squad.new("CAR", GameDB.club_list("CAR"), false, "CAR"), 1)
	_check(is_equal_approx(m.key_target(), Matchups.KEY_TARGET_DUELS),
			"A side looks for its key forwards on KEY_TARGET_DUELS of entries")


## Every match has duels, and general-play contests reach the duel log.
func _test_more_contests() -> void:
	var on := []
	var gp_on := 0
	for i in range(MORE):
		var b := _play(i)
		on.append_array(_per_duel(b[0], b[1]))
		for ev in (b[1] as Dictionary)["events"]:
			if (ev as Dictionary).get("general_play", false) and (ev as Dictionary).has("duel_contest"):
				gp_on += 1
	_check(on.size() >= 2 * MORE,
			"Every match has key forwards with direct opponents (%d)" % on.size())
	print("Key duels: contests per duel %.2f (%d matches)" % [_mean(on), MORE])
	_check(gp_on > 0, "General-play contests reach the duel log (%d)" % gp_on)


## Every logged mark is a mark the forward took, against the man the log names;
## every tagged general-play contest is in the log.
func _test_contests_trace_to_play() -> void:
	var fids := 0
	for i in range(SEEDS.size()):
		var g := _play(i)
		var r: Dictionary = g[1]
		var log: Dictionary = r["duels"]
		for fid in log:
			fids += 1
			var contests: Array = log[fid]["contests"]
			var logged_marks := 0
			var men := {}
			for c in contests:
				men[str(c[1])] = true
				if bool(c[2]):
					logged_marks += 1
			var mark_events := 0
			var tagged := 0
			var wrong_man := 0
			for ev in r["events"]:
				var e: Dictionary = ev
				if str(e.get("duel_contest", "")) != str(fid):
					continue
				tagged += 1
				var pid := str(e.get("player_id", ""))
				if str(e.get("kind", "")) == "mark" and pid == str(fid):
					mark_events += 1
					if e.has("against_id") and not men.has(str(e["against_id"])):
						wrong_man += 1
				elif not men.has(pid):
					# A contest he lost is his man's: an intercept mark or a spoil.
					wrong_man += 1
			_check(mark_events == logged_marks,
					"%s: %d marks logged, %d mark events tagged to him" % [fid, logged_marks, mark_events])
			_check(tagged <= contests.size() and wrong_man == 0,
					"%s: %d tagged contests within %d logged, %d against another man" % [fid, tagged, contests.size(), wrong_man])
	_check(fids >= SEEDS.size(), "Key forwards with logged contests: %d" % fids)


## A key forward never leads up at his own kick: no tagged general-play
## contest (his mark, his man's intercept or spoil) is on a ball he kicked
## himself (the last kick before it), over MORE matches.
func _test_no_lead_at_own_kick() -> void:
	var gp := 0
	var own := 0
	for i in range(MORE):
		var g := _play(i)
		var last_kicker := ""
		for ev in (g[1] as Dictionary)["events"]:
			var e: Dictionary = ev
			if str(e.get("kind", "")) == "kick":
				last_kicker = str(e.get("player_id", ""))
			elif e.get("general_play", false) and e.has("duel_contest"):
				gp += 1
				var fid := str(e["duel_contest"])
				if fid == last_kicker or fid == str(e.get("from_id", "-")):
					own += 1
	print("Key duels: %d of %d tagged general-play contests on his own kick" % [own, gp])
	_check(gp > 0 and own == 0,
			"No key forward contests his own kick: %d of %d tagged general-play contests" % [own, gp])


## The full-time line's numbers are the log's, and its verdict is the rule's.
func _test_line_reads_the_log() -> void:
	var lines := 0
	for i in range(SEEDS.size()):
		var g := _play(i)
		var r: Dictionary = g[1]
		var log: Dictionary = r["duels"]
		for fid in log:
			var n := 0
			var won := 0
			var men := {}
			for c in log[fid]["contests"]:
				n += 1
				won += 1 if bool(c[2]) else 0
				men[str(c[1])] = true
			if n < MatchNotes.MIN_DUELS or men.size() != 1:
				continue
			var theirs := int(log[fid]["side"]) != 0
			var line: String = MatchNotes._duel_line(r, str(fid), theirs, 0)
			var want := "%d marks from %d contests" % [won, n]
			_check(line.contains(want), "%s's line says '%s': %s" % [fid, want, line])
			var v := MatchNotes.duel_verdict(won, n)
			var reads := 1 if line.contains(" beat ") else (-1 if line.contains(" held ") else 0)
			_check(reads == v, "%s's line reads the verdict the rule gives (%d): %s" % [fid, v, line])
			lines += 1
	_check(lines >= SEEDS.size(), "Full-time duel lines checked: %d" % lines)


# ---------------------------------------------------------------------------
# Only a defender by trade minds a forward (director, 2026-11-07: "Somehow
# arki butler ended up playing on Taylor Walker. Shouldn't be possible").
# ---------------------------------------------------------------------------
func _player(list: Array, last: String) -> Dictionary:
	for p in list:
		if str(p.get("last", "")) == last:
			return p
	return {}


## Arki Butler, a 2026 draftee: a forward-midfielder, 182 cm.
func _butler() -> Dictionary:
	var b := _player(GameDB.draftees, "Butler")
	if b.is_empty():
		return {}
	b = b.duplicate(true)
	b["id"] = "BUTLER"
	b["num"] = 99
	return b


## A defender by trade, from his own positions: never the back slot he is
## standing in.
func _by_trade(p: Dictionary) -> bool:
	return not p.is_empty() and Ratings.positions(p).has("DEF")


func _pure_defender(club: String) -> Dictionary:
	for p in GameDB.club_list(club):
		if str(p["role"]) == "DEF" and Ratings.second_positions(p).is_empty():
			return p
	return {}


## A forward-midfielder and a ruck in back slots are not defenders; a real
## defender is, and only while he stands in the back line.
func _test_defenders_by_trade() -> void:
	var butler := _butler()
	var ruck := _player(GameDB.club_list("CAR"), "Pittonet")
	var back := _pure_defender("CAR")
	_check(not butler.is_empty() and not ruck.is_empty() and not back.is_empty(),
			"Arki Butler, Marc Pittonet and a Carlton defender are on record")
	if butler.is_empty() or ruck.is_empty() or back.is_empty():
		return
	var up := back.duplicate()
	up["id"] = "UP_THE_GROUND"
	var ground := [Ratings._for_slot(butler, "DEF"), Ratings._for_slot(ruck, "DEF"),
			Ratings._for_slot(back, "DEF"), Ratings._for_slot(up, "MID")]
	var ids := Matchups.defenders(ground).map(func(p): return str(p["id"]))
	_check(ids == [str(back["id"])],
			"Only the defender by trade in the back line can mind a forward: %s" % str(ids))
	_check(not Matchups.is_defender(Ratings._for_slot(ruck, "DEF")), "A ruck in a back slot is not a defender")
	_check(not Matchups.is_defender(Ratings._for_slot(butler, "DEF")),
			"A forward-midfielder in a back slot is not a defender")


## With a key defender on the ground, a tall key forward's default direct
## opponent is a key defender, never the ruck standing in a back slot.
func _test_key_defender_takes_key_forward() -> void:
	var ade := Squad.new("ADE", GameDB.club_list("ADE"), false, "ADE")
	var car := Squad.new("CAR", GameDB.club_list("CAR"), true, "CAR")
	var ruck := _player(GameDB.club_list("CAR"), "Pittonet")
	for i in range(car.ground.size()):
		if str(car.ground[i]["role"]) == "DEF":
			car.ground[i] = Ratings._for_slot(ruck, "DEF")
			break
	var keys := Matchups.defenders(car.ground).filter(
			func(p): return PlayerProfile.player_type(p) == "Key defender")
	_check(not keys.is_empty(), "Carlton have a key defender on the ground")
	var d := Matchups.defaults(ade.ground, car.ground)
	var kf := Matchups.key_forwards(ade.ground)
	_check(not kf.is_empty() and d.has(str(kf[0]["id"])), "Adelaide's first key forward has a direct opponent")
	if keys.is_empty() or kf.is_empty() or not d.has(str(kf[0]["id"])):
		return
	_check(str(d[str(kf[0]["id"])]) == str(keys[0]["id"]),
			"%s (%d cm) is picked up by a key defender, not %s" % [str(kf[0]["id"]),
			int(kf[0].get("height_cm", 0)), str(d[str(kf[0]["id"])])])
	for fid in d:
		_check(str(d[fid]) != str(ruck["id"]), "The ruck in a back slot gets no forward by default")


## The breaks' re-match and an injury's refill pick only defenders by trade:
## with the rest of the back line rucks and midfielders, a forward goes
## without a direct opponent rather than to one of them.
func _test_rematch_and_refill_keep_defenders() -> void:
	var sim := MatchSim.new(Squad.new("CAR", GameDB.club_list("CAR"), true, "CAR"),
			Squad.new("ADE", GameDB.club_list("ADE"), false, "ADE"), 4)
	var sq: Squad = sim.squads[0]
	var d: Dictionary = sim.duels[0]
	_check(not d.is_empty(), "Carlton start with direct opponents on Adelaide's key forwards")
	if d.is_empty():
		return
	var holding := {}
	for fid in d:
		holding[str(d[fid])] = true
	var on := {}
	for g in sq.ground:
		on[str(g["id"])] = true
	var spare := []
	for p in GameDB.club_list("CAR"):
		if not _by_trade(p) and not on.has(str(p["id"])):
			spare.append(p)
	# Rucks first: the tallest men a back line could be filled with.
	spare.sort_custom(func(a, b): return str(a["role"]) == "RUCK" and str(b["role"]) != "RUCK")
	var k := 0
	for i in range(sq.ground.size()):
		var g: Dictionary = sq.ground[i]
		if str(g["role"]) == "DEF" and not holding.has(str(g["id"])) and k < spare.size():
			sq.ground[i] = Ratings._for_slot(spare[k], "DEF")
			k += 1
	sim.interceptor[0] = ""
	for fid in d.keys():
		sim._rematch(0, str(fid), {})
	for fid in d:
		_check(_by_trade(sim._on_ground(0, str(d[fid]))),
				"After a re-match %s is minded by a defender by trade, not %s" % [fid, str(d[fid])])
	# A key defender goes off hurt and another ruck takes his place: no other
	# defender by trade is free, so his forward goes without one.
	var fid0 := str(d.keys()[0])
	var gone := str(d[fid0])
	for i in range(sq.ground.size()):
		if str(sq.ground[i]["id"]) == gone and k < spare.size():
			sq.ground[i] = Ratings._for_slot(spare[k], "DEF")
	sim._refill_duel(0, gone)
	_check(not d.has(fid0), "After an injury %s goes to nobody rather than to %s" % [fid0, str(d.get(fid0, ""))])


## A back slot waits for a defender: a tired one off the bench before a fresh
## midfielder; a defender too tired for that holds the routine change; and
## the man who last stood in a back slot is not a defender for it.
func _test_bench_for_back_slot() -> void:
	var sim := MatchSim.new(Squad.new("CAR", GameDB.club_list("CAR"), true, "CAR"),
			Squad.new("ADE", GameDB.club_list("ADE"), false, "ADE"), 4)
	var sq: Squad = sim.squads[0]
	var back := _pure_defender("CAR")
	var mid := {}
	for p in GameDB.club_list("CAR"):
		if mid.is_empty() and str(p["role"]) == "MID" and not _by_trade(p):
			mid = p
	sim._held = {}
	sq.bench = [mid, back]
	sim.energy[str(mid["id"])] = 100.0
	sim.energy[str(back["id"])] = 70.0
	_check(sim._bench_for(0, "DEF", 85.0, true) == 1,
			"A tired defender goes into the back line before a fresh midfielder")
	sim.energy[str(back["id"])] = 40.0
	_check(sim._bench_for(0, "DEF", 85.0, true) == -1,
			"A spent defender on the bench holds the back line's routine change")
	_check(sim._bench_for(0, "DEF", 0.0) == 1, "For a man off hurt, the defender still comes on first")
	sq.bench = [Ratings._for_slot(_butler(), "DEF"), back]
	sim.energy["BUTLER"] = 100.0
	sim.energy[str(back["id"])] = 90.0
	_check(sim._bench_for(0, "DEF", 85.0, true) == 1,
			"A forward-midfielder who last stood in a back pocket is not a defender for it")
	sq.bench = [mid]
	_check(sim._bench_for(0, "DEF", 85.0, true) == 0,
			"With no defender on the bench another line's player goes on")


## A defender going to the bench hands his forward on, never to a
## forward-midfielder who comes on in his place.
func _test_duel_handed_on_at_interchange() -> void:
	var sim := MatchSim.new(Squad.new("CAR", GameDB.club_list("CAR"), true, "CAR"),
			Squad.new("ADE", GameDB.club_list("ADE"), false, "ADE"), 4)
	var sq: Squad = sim.squads[0]
	var d: Dictionary = sim.duels[0]
	_check(not d.is_empty(), "Carlton start with a direct opponent on a key forward")
	if d.is_empty():
		return
	var fid := str(d.keys()[0])
	var dfn := str(d[fid])
	var gi := -1
	for i in range(sq.ground.size()):
		if str(sq.ground[i]["id"]) == dfn:
			gi = i
	sq.bench = [_butler()]
	sim.energy["BUTLER"] = 100.0
	sim._swap(0, gi, 0)
	var now := str(d.get(fid, ""))
	_check(now != "BUTLER" and now != dfn,
			"Arki Butler on for the key defender does not take his forward: %s" % now)
	_check(now == "" or _by_trade(sim._on_ground(0, now)),
			"The forward goes to a defender by trade or to nobody: %s" % now)


## The oval's direct opponents (MatchDirector) through every interchange of
## whole matches with Arki Butler on the list (the director's report came from
## West Coast v Adelaide, seed 4, with him on Taylor Walker): whoever minds a
## forward from the back line is a defender by trade, and so is every
## direct opponent the match itself recorded.
func _test_oval_back_line_by_trade() -> void:
	var subs := 0
	var minded := 0
	for c in [["WCE", 4], ["MEL", 2], ["CAR", 2]]:
		var club := str(c[0])
		var lst: Array = GameDB.club_list(club).duplicate(true)
		var b := _butler()
		b["club"] = club
		lst.append(b)
		var mine := Squad.new(club, lst, true, club)
		mine.assistant = true
		var theirs := Squad.new("ADE", GameDB.club_list("ADE"), false, "ADE")
		theirs.ai_plans = true
		var sim := MatchSim.new(mine, theirs, int(c[1]))
		var res: Dictionary = sim.run()
		var trade := {}
		for side_roster in res["roster"]:
			for p in side_roster:
				var rec = GameDB.player_by_id(str(p["id"]))
				var def := str(p.get("list_role", "")) == "DEF"
				if rec is Dictionary:
					def = def or Ratings.second_positions(rec).has("DEF")
				trade[str(p["id"])] = def
		for e in res.get("timeline", []):
			var duels: Dictionary = (e as Dictionary).get("duels", {})
			for fid in duels:
				_check(bool(trade.get(str(duels[fid]), false)),
						"%s v ADE seed %d: the match put %s, not a defender, on %s" % [club, int(c[1]), str(duels[fid]), fid])
		var md := MatchDirector.new()
		var evs: Array = res["events"]
		md.setup(res, evs)
		for k in range(evs.size()):
			md._apply_timeline(k)
			var ev: Dictionary = evs[k]
			if str(ev.get("kind", "")) != "sub":
				continue
			subs += 1
			md._sub(ev)
			for t in md.tokens:
				if str(t["role"]) != "FWD" or int(t["match"]) < 0:
					continue
				var o: Dictionary = md.tokens[int(t["match"])]
				if str(o["role"]) != "DEF" or bool(o.get("tagging", false)):
					continue
				minded += 1
				if not bool(trade.get(str(o["pid"]), false)):
					_check(false, "%s v ADE seed %d, event %d: %s (not a defender) minds %s" % [
							club, int(c[1]), k, str(o["name"]), str(t["name"])])
	_check(subs > 0 and minded > 0, "Interchanges replayed: %d; forwards minded checked: %d" % [subs, minded])
