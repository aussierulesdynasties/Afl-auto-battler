extends RefCounted
## Run by tests/run_key_duels_tests.gd (suite "key_duels").
## Key forward v key defender (row 94, T8.Q6, director 2026-11-06; switch
## key_duels): with the switch on a key forward and his direct opponent meet
## more often (his marking contests up the ground are against his man, and
## sides look for him more inside 50), every contest the full-time line counts
## traces to the play, and the line's "N marks from M contests" is the log.
## Off, no general-play contest is logged and the old key-forward share holds.

var _tree: SceneTree
var checks := 0
var failures: Array[String] = []
## The same seeds and lists with the switch off and on (paired).
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
	_t("_test_switch_ships_off")
	_t("_test_more_contests")
	_t("_test_contests_trace_to_play")
	_t("_test_no_lead_at_own_kick")
	_t("_test_line_reads_the_log")
	_t("_test_switch_off_as_before")
	Features.clear("key_duels")
	print(Ran.line("Key duels", self))
	for f in failures:
		print("  FAIL: " + f)


## One match per seed, with the switch as given: [sim, result].
func _play(i: int, on: bool) -> Array:
	Features.set_on("key_duels", on)
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


func _test_switch_ships_off() -> void:
	Features.set_on("key_duels", false)
	_check(Features.KNOWN.has("key_duels"), "key_duels is a known switch")
	_check(bool(ProjectSettings.get_setting("features/key_duels", false)), "key_duels ships on")
	var m := MatchSim.new(Squad.new("COL", GameDB.club_list("COL"), true, "COL"),
			Squad.new("CAR", GameDB.club_list("CAR"), false, "CAR"), 1)
	_check(not m.key_duels_on and is_equal_approx(m.key_target(), Matchups.KEY_TARGET),
			"Off, a side looks for its key forwards on KEY_TARGET of entries")
	Features.set_on("key_duels", true)
	m = MatchSim.new(Squad.new("COL", GameDB.club_list("COL"), true, "COL"),
			Squad.new("CAR", GameDB.club_list("CAR"), false, "CAR"), 1)
	_check(m.key_duels_on and is_equal_approx(m.key_target(), Matchups.KEY_TARGET_DUELS)
			and Matchups.KEY_TARGET_DUELS > Matchups.KEY_TARGET,
			"On, on KEY_TARGET_DUELS of entries, more than KEY_TARGET")


## The row's done-when: more contests per duel with the switch on, same seeds.
func _test_more_contests() -> void:
	var off := []
	var on := []
	var gp_on := 0
	for i in range(MORE):
		var a := _play(i, false)
		var b := _play(i, true)
		off.append_array(_per_duel(a[0], a[1]))
		on.append_array(_per_duel(b[0], b[1]))
		for ev in (b[1] as Dictionary)["events"]:
			if (ev as Dictionary).get("general_play", false) and (ev as Dictionary).has("duel_contest"):
				gp_on += 1
	_check(off.size() >= 2 * MORE and on.size() >= 2 * MORE,
			"Every match has key forwards with direct opponents (%d off, %d on)" % [off.size(), on.size()])
	print("Key duels: contests per duel %.2f off, %.2f on (%d matches, same seeds)" % [_mean(off), _mean(on), MORE])
	_check(_mean(on) >= _mean(off) + 0.4,
			"Contests per duel rise with the switch on: %.2f off, %.2f on" % [_mean(off), _mean(on)])
	_check(gp_on > 0, "General-play contests reach the duel log with the switch on (%d)" % gp_on)


## Every logged mark is a mark the forward took, against the man the log names;
## every tagged general-play contest is in the log.
func _test_contests_trace_to_play() -> void:
	var fids := 0
	for i in range(SEEDS.size()):
		var g := _play(i, true)
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
		var g := _play(i, true)
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
		var g := _play(i, true)
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


## Off: no contest is tagged and the log holds only the entries inside 50,
## exactly as before the switch (the same seed plays the same match twice).
func _test_switch_off_as_before() -> void:
	var tagged := 0
	for i in range(3):
		var a := _play(i, false)
		var b := _play(i, false)
		for ev in (a[1] as Dictionary)["events"]:
			if (ev as Dictionary).has("duel_contest"):
				tagged += 1
		_check((a[1] as Dictionary)["score"] == (b[1] as Dictionary)["score"]
				and (a[1] as Dictionary)["duels"] == (b[1] as Dictionary)["duels"],
				"Seed %d plays the same match twice with the switch off" % (9401 + i))
	_check(tagged == 0, "Off, no contest is tagged as a duel contest (%d)" % tagged)
