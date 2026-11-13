extends SceneTree
## godot --headless --path . --script tests/run_crowd_tests.gd
## Row 6.51, the crowd knows the score. One seeded match is watched from the
## first bounce to full time on the real match screen, and what the crowd did
## is read back from its own log (CrowdSound.heard) against the match's events:
## - the murmur and the roar rise across a run of goals by one side;
## - a home goal is louder than an away goal;
## - a siren goes at the end of each of the four quarters, and only then;
## - the gap between the pitch showing an event and its sound starting is
##   measured and printed in milliseconds.
## The sound never touches the match: the same seed with the crowd fed nothing
## ends on the same score.

const SUITE_SEED := 2027
const PHONE := Vector2i(390, 844)
## A sound later than this after its event reads as late (about three frames at 60 a second).
const GAP_LIMIT_MS := 50.0
## Seconds of play the test moves the pitch on each frame, besides the frame's own.
## The director steps in sixtieths whatever it is given (MatchDirector.SUBSTEP),
## so a long step plays the same events in fewer drawn frames.
const WATCH_STEP := 2.0

var _state: Node
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_state.autosave_enabled = false
	_state.save_path = "user://test_career.save"
	_state.settings_path = "user://test_settings.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	await _t("_test_levels")
	await _t("_test_sirens_once")
	await _t("_test_watched_match")
	print(Ran.line("Crowd", self))
	quit(0 if _failures.is_empty() else 1)


## The levels on their own: a scripted run of goals, no match.
func _test_levels() -> void:
	var cs := CrowdSound.new()
	root.add_child(cs)
	var bed: AudioStreamPlayer = cs.get_child(0)
	var roars := []
	var beds := []
	for i in range(5):
		cs.event("goal", 0, Time.get_ticks_usec())
		roars.append(float((cs.heard[-1] as Dictionary)["db"]))
		beds.append(bed.volume_db)
	_check(roars[0] < roars[1] and roars[1] < roars[2] and roars[2] < roars[3],
			"Each goal in a home run of four roars louder than the last (%s)" % str(roars))
	_check(beds[0] < beds[1] and beds[1] < beds[2] and beds[2] < beds[3],
			"The murmur rises through a home run of four (%s)" % str(beds))
	_check(is_equal_approx(roars[4], roars[3]) and is_equal_approx(beds[4], beds[3]),
			"A fifth goal in a row is no louder than the fourth (%s)" % str(roars))
	_check(roars[3] < -1.0, "The loudest roar leaves headroom (%.1f dB on a file peaking under -3 dBFS)" % roars[3])
	cs.event("goal", 1, Time.get_ticks_usec())
	var away := float((cs.heard[-1] as Dictionary)["db"])
	_check(away < roars[0], "An away goal that breaks the run is quieter than a home side's first (%.1f, %.1f)" % [away, roars[0]])
	_check(bed.volume_db < beds[1], "The murmur drops back when the run is broken (%.1f)" % bed.volume_db)
	for run in range(1, 6):
		_check(CrowdSound.roar_db(0, run) > CrowdSound.roar_db(1, run),
				"A home goal is louder than an away goal, %d in a row" % run)
	# A goal skipped past counts toward the run and makes no sound.
	var before := cs.heard.size()
	cs.event("goal", 1, -1, false)
	_check(cs.heard.size() == before and cs.run_length() == 2, "A goal skipped past is silent and still counts toward the run")
	cs.queue_free()
	# Behinds: the home side's lift is louder too.
	var home := CrowdSound.new()
	root.add_child(home)
	home.event("behind", 0)
	var visitors := CrowdSound.new()
	root.add_child(visitors)
	visitors.event("behind", 1)
	_check(float((home.heard[0] as Dictionary)["db"]) > float((visitors.heard[0] as Dictionary)["db"]),
			"A home behind lifts the crowd more than an away behind")
	home.queue_free()
	visitors.queue_free()


## One siren a quarter, and extra time gets its own at the end.
func _test_sirens_once() -> void:
	var cs := CrowdSound.new()
	root.add_child(cs)
	for q in [1, 1, 2, 3, 4, 4]:
		cs.event("quarter", -1, Time.get_ticks_usec(), true, q)
	cs.full_time()
	cs.full_time()
	_check(_sirens(cs) == [1, 2, 3, 4], "Four quarters, four sirens, none twice (%s)" % str(_sirens(cs)))
	cs.queue_free()
	var extra := CrowdSound.new()
	root.add_child(extra)
	for q in [1, 2, 3, 4, 5, 5]:
		extra.event("quarter", -1, Time.get_ticks_usec(), true, q)
	extra.full_time()
	_check(_sirens(extra) == [1, 2, 3, 4, 5], "Extra time ends on a siren of its own (%s)" % str(_sirens(extra)))
	extra.queue_free()
	var skipped := CrowdSound.new()
	root.add_child(skipped)
	for q in [1, 2, 3, 4]:
		skipped.event("quarter", -1, -1, false, q)
	skipped.full_time()
	_check(_sirens(skipped) == [4], "A match skipped to its end hears the full-time siren only (%s)" % str(_sirens(skipped)))
	skipped.queue_free()


func _sirens(cs: CrowdSound) -> Array:
	var out := []
	for h in cs.heard:
		if str((h as Dictionary)["kind"]) == "siren":
			out.append(int((h as Dictionary)["q"]))
	return out


## The seeded match, watched on the match screen.
func _test_watched_match() -> void:
	var m: Control = await _watch(false)
	_check(bool(m.get("_fulltime_shown")), "The match reaches full time")
	var crowd: CrowdSound = m.get("_crowd")
	var res: Dictionary = m.get("_res")
	_check(crowd != null and not crowd.heard.is_empty(), "The crowd was heard")
	if crowd == null:
		return

	# What the match says happened: every goal in order with the run it made.
	var goals := []      # [side, run]
	var run_side := -1
	var run_len := 0
	var quarters := []
	for ev in res.get("events", []):
		var kind := str((ev as Dictionary).get("kind", ""))
		if kind == "goal":
			var side := int((ev as Dictionary).get("side", 0))
			run_len = run_len + 1 if side == run_side else 1
			run_side = side
			goals.append([side, run_len])
		elif kind == "quarter" and int((ev as Dictionary).get("q", 0)) <= 4:
			quarters.append(int((ev as Dictionary).get("q", 0)))
	var final_goals: Array = res.get("goals", [0, 0])
	_check(goals.size() == int(final_goals[0]) + int(final_goals[1]) and goals.size() >= 10,
			"The match's events hold every goal (%d of %s)" % [goals.size(), str(final_goals)])

	# What the crowd did.
	var roars := []
	var gaps := []
	for h in crowd.heard:
		var d: Dictionary = h
		if str(d["kind"]) == "goal":
			roars.append(d)
		gaps.append(float(d["gap_ms"]))
	_check(roars.size() == goals.size(), "Every goal watched got one roar (%d roars, %d goals)" % [roars.size(), goals.size()])
	var in_step := roars.size() == goals.size()
	var rises := 0
	var longest := 0
	var home_first := []
	var away_first := []
	for i in range(mini(roars.size(), goals.size())):
		var d: Dictionary = roars[i]
		var side := int(goals[i][0])
		var run := int(goals[i][1])
		in_step = in_step and int(d["side"]) == side and int(d["run"]) == run
		longest = maxi(longest, run)
		if run == 1:
			(home_first if side == 0 else away_first).append(float(d["db"]))
		elif run <= CrowdSound.RUN_CAP:
			var up := float(d["db"]) > float((roars[i - 1] as Dictionary)["db"])
			rises += 1 if up else 0
			_check(up, "Goal %d, the %s side's %d in a row, roars louder than the one before (%.1f after %.1f)" % [
					i + 1, "home" if side == 0 else "away", run, float(d["db"]), float((roars[i - 1] as Dictionary)["db"])])
	_check(in_step, "The crowd's run of goals is the match's, goal for goal")
	_check(longest >= 2 and rises >= 1, "This match has a run of goals for the crowd to rise with (longest %d, %d rises)" % [longest, rises])
	_check(not home_first.is_empty() and not away_first.is_empty(), "Both sides kicked a goal that started a run")
	if not home_first.is_empty() and not away_first.is_empty():
		_check(float(home_first.min()) > float(away_first.max()),
				"A home goal is louder than an away goal (home %.1f dB, away %.1f dB)" % [float(home_first.min()), float(away_first.max())])
	_check(quarters == [1, 2, 3, 4], "The match has four quarter ends (%s)" % str(quarters))
	_check(_sirens(crowd) == [1, 2, 3, 4], "A siren at the end of each of the four quarters, and no other (%s)" % str(_sirens(crowd)))

	# The gap between the pitch showing an event and its sound starting.
	gaps.sort()
	var total := 0.0
	var unmeasured := 0
	for g in gaps:
		total += float(g)
		unmeasured += 1 if float(g) < 0.0 else 0
	_check(unmeasured == 0 and not gaps.is_empty(), "Every sound has a measured gap (%d without)" % unmeasured)
	if not gaps.is_empty():
		var median := float(gaps[gaps.size() / 2])
		var worst := float(gaps[-1])
		print("Crowd event-to-sound gap over %d sounds (%d roars, %d sirens): mean %.3f ms, median %.3f ms, worst %.3f ms. Longest run of goals %d. Audio output latency here %.1f ms (not in the gap)." % [
				gaps.size(), roars.size(), _sirens(crowd).size(), total / gaps.size(), median, worst, longest,
				AudioServer.get_output_latency() * 1000.0])
		_check(median < GAP_LIMIT_MS, "The usual gap is under %.0f ms (median %.3f ms)" % [GAP_LIMIT_MS, median])
	var seen_score: Array = res.get("score", [0, 0]).duplicate()
	m.queue_free()
	await _settle()

	# Sound never affects the match: the same seed watched with no crowd ends on the same score.
	var silent: Control = await _watch(true)
	var silent_score: Array = (silent.get("_res") as Dictionary).get("score", [])
	_check(bool(silent.get("_fulltime_shown")) and silent_score == seen_score,
			"The same seed watched with no crowd ends on the same score (%s, %s)" % [str(silent_score), str(seen_score)])
	silent.queue_free()
	await _settle()


## Watch the seeded match to full time. `no_crowd` takes the crowd out before the first bounce.
func _watch(no_crowd: bool) -> Control:
	var db = root.get_node("GameDB")
	_state.set_vignettes_on(false)
	_state.reset()
	_state.replay_seed = SUITE_SEED
	_state.start_season("FRE", db.club_list("FRE"))
	root.size = PHONE
	_state.set_match_way("watch")
	_check(_state.prepare_interactive_match(), "A live match is prepared")
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	if no_crowd:
		(m.get("_crowd") as Node).free()
		m.set("_crowd", null)
	await _settle()
	var guard := 0
	while not bool(m.get("_fulltime_shown")) and guard < 60000:
		guard += 1
		var box: Node = m.find_child("CoachBox", true, false)
		if box != null:
			var start: Button = box.find_child("StartQuarter", true, false)
			_check(start != null, "The break can be left")
			if start == null:
				break
			start.emit_signal("pressed")
			await _settle()
			continue
		var card: Node = m.find_child("MomentCard", true, false)
		if card != null:
			var pick: Button = card.find_child("Moment_0", true, false)
			if pick != null and not pick.disabled and pick.is_visible_in_tree():
				pick.emit_signal("pressed")
				await _settle()
				continue
		if m.find_child("BroadcastVignetteOverlay", true, false) != null:
			m.call("_finish_broadcast")
			await _settle()
			continue
		var pitch = m.get("_pitch")
		if pitch != null and pitch.playing:
			pitch._process(WATCH_STEP)
		await process_frame
	return m


func _settle() -> void:
	for i in range(6):
		await process_frame


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)
