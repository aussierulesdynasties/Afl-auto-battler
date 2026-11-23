extends RefCounted
## The break talks suite's body, loaded by tests/run_break_talks_tests.gd by path
## (a runner names no class at its top: its load would reach the autoloads).
## Quarter-break talks (BreakTalks, director 2026-11-21): the dice rules, the
## sim's once-a-break sit-down and half-time speech, rival clubs making the
## same calls, and the break screen on a phone with real taps.

const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")

var _state: Node
var _db: Node
var _checks := 0
var _failures: Array[String] = []


var tree: SceneTree


func go(t: SceneTree) -> void:
	tree = t
	await tree.process_frame
	_state = tree.root.get_node("GameState")
	_db = tree.root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.event_sheets = false
	_state.save_path = "user://test_break_talks.save"
	_state.settings_path = "user://test_break_talks_settings.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	_t("_test_rules")
	_t("_test_copy")
	_t("_test_sim")
	await _t("_test_break_on_a_phone", [Vector2i(390, 844)])
	await _t("_test_break_on_a_phone", [Vector2i(360, 740)])
	print(Ran.line("Break talks", self))


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


func _settle(n := 6) -> void:
	for i in range(n):
		await tree.process_frame


func _test_rules() -> void:
	for e in range(BreakTalks.EDGE_MIN, BreakTalks.EDGE_MAX + 1):
		var o := BreakTalks.odds(e)
		var total := 0.0
		for k in o:
			total += float(o[k])
		_check(absf(total - 1.0) < 0.0001, "The odds add to 100%% at edge %d (%.4f)" % [e, total])
		# Snake eyes always backfires: no edge makes a talk safe.
		_check(float(o["backfire"]) >= 1.0 / 36.0 - 0.0001, "A talk can always backfire (edge %d)" % e)
	var plain := BreakTalks.odds(0)
	_check(absf(float(plain["backfire"]) - 3.0 / 36.0) < 0.0001, "With no edge it backfires on 2 or 3: 8%")
	_check(float(BreakTalks.odds(3)["backfire"]) < float(plain["backfire"])
			and float(BreakTalks.odds(-3)["backfire"]) > float(plain["backfire"]),
			"A better edge backfires less, a worse one more")
	_check(float(BreakTalks.odds(2)["big"]) > float(plain["big"]), "A better edge lands the big lift more often")
	_check(BreakTalks.band([1, 1], 3) == "backfire" and BreakTalks.band([6, 6], -3) == "small",
			"Snake eyes backfires at any edge; double six with the worst edge still lifts")
	_check(BreakTalks.manage_edge(60.0) == -1 and BreakTalks.manage_edge(70.0) == 0 and BreakTalks.manage_edge(80.0) == 1,
			"Man-management: Fair -1, Good 0, Strong +1")
	_check(BreakTalks.trust_edge(-100) == -2 and BreakTalks.trust_edge(0) == 0 and BreakTalks.trust_edge(100) == 2,
			"Trust: lost -2, neutral 0, close +2")
	_check(BreakTalks.edge("sit", 90.0, "FATH", 100) == BreakTalks.EDGE_MAX
			and BreakTalks.edge("sit", 50.0, "", -100) == BreakTalks.EDGE_MIN, "The edge is capped both ways")
	_check(BreakTalks.edge("sit", 70.0, "FATH", 0) == 1 and BreakTalks.edge("speech", 70.0, "FATH", 0) == 0
			and BreakTalks.edge("speech", 70.0, "HARD", 0) == 1, "A Father Figure sits down better; a Hardline speaks better")
	# The speech reaches everyone, so each man's share is smaller than a sit-down's.
	for k in BreakTalks.KEYS:
		_check(absf(BreakTalks.lift("speech", k)) <= absf(BreakTalks.lift("sit", k)),
				"The speech's lift per man is no bigger than a sit-down's (%s)" % k)


func _test_copy() -> void:
	var lines: Array = []
	for e in [-3, 0, 3]:
		lines.append_array(BreakTalks.gate_texts("sit", e, "Petracca"))
		lines.append_array(BreakTalks.gate_texts("speech", e))
	for k in BreakTalks.KEYS:
		lines.append(BreakTalks.result_line("sit", k, "Petracca"))
		lines.append(BreakTalks.result_line("speech", k))
	lines.append_array(BreakTalks.edge_lines("sit", 80.0, "FATH", 40))
	lines.append_array(BreakTalks.edge_lines("speech", 60.0, "HARD", -40))
	for l in lines:
		_check(str(l) != "" and CopyRules.check(str(l)).is_empty(), "Talk copy keeps the voice rules: %s" % str(l))
	var g: Array = BreakTalks.gate_texts("sit", 0, "Petracca")
	_check(str(g[0]).contains("%") and str(g[1]).contains("%"), "The gate gives the odds and the size as percentages")


func _match() -> MatchSim:
	var home := Squad.new("Collingwood", _db.club_list("COL"), true, "COL")
	var away := Squad.new("Carlton", _db.club_list("CAR"), false, "CAR")
	return MatchSim.new(home, away, 4242)


func _test_sim() -> void:
	var sim := _match()
	sim.moment_side = 0   # we coach side 0; side 1 is a rival with nobody waiting on it
	_check(not sim.can_sit_down(0) and not sim.can_speak(0), "No talk before the first bounce")
	sim.run_quarter()
	_check(sim.can_sit_down(0) and not sim.can_speak(0), "Quarter time: a sit-down, no speech")
	var rival_sit := sim.talk_now(1, "sit")
	_check(not rival_sit.is_empty() and rival_sit["q"] == 2, "The rival coach sat down with someone at quarter time")
	var id := str((sim.squads[0] as Squad).ground[0]["id"])
	var p: Dictionary = (sim.squads[0] as Squad).ground[0]
	var before := sim.fit(p)
	var t := sim.sit_down(0, id)
	_check(not t.is_empty() and (t["dice"] as Array).size() == 2, "Sitting down rolls two dice")
	_check(absf(sim.fit(p) - before - float(t["lift"])) < 0.0001, "His fitness moves by the roll's lift (%s)" % str(t["band"]))
	_check(sim.sit_down(0, str((sim.squads[0] as Squad).ground[1]["id"])).is_empty() and not sim.can_sit_down(0),
			"Once a break")
	var again := _match()
	again.moment_side = 0
	again.run_quarter()
	_check(again.sit_down(0, id)["dice"] == t["dice"], "The same match rolls the same dice")
	sim.run_quarter()
	_check(not sim._talk_lift.has(id), "A talk lifts one quarter only")
	_check(sim.can_sit_down(0) and sim.can_speak(0), "Half time: a sit-down and the speech")
	var sp := sim.give_speech(0)
	_check(not sp.is_empty() and sim.give_speech(0).is_empty(), "One speech at half time")
	_check(not sim.talk_now(1, "speech").is_empty(), "The rival coach spoke at half time")
	var everyone := true
	for q in (sim.squads[0] as Squad).ground + (sim.squads[0] as Squad).bench:
		everyone = everyone and absf(float(sim._talk_lift.get(str(q["id"]), 0.0)) - float(sp["lift"])) < 0.0001
	_check(everyone, "The speech lifts (or drops) everyone of ours alike")
	sim.run_quarter()
	sim.run_quarter()
	_check(not sim.can_sit_down(0) and not sim.can_speak(0), "No talk at full time")
	var res := sim.result()
	_check((res["talks"] as Array).size() == 6, "Six talks in all: our two, their three sit-downs and speech (%d)" % (res["talks"] as Array).size())
	var lines := MatchNotes.talk_lines(res, 0, 3)
	_check(lines.size() == 1 and str(lines[0]).begins_with("Half-time speech"), "The next break says what the speech was followed by: %s" % str(lines))
	# A match nobody coaches: both sides talk at every break by themselves.
	var simmed := _match()
	simmed.run()
	_check((simmed.result()["talks"] as Array).size() == 8, "A simmed match: each side three sit-downs and a speech")
	var off := _match()
	off.talks_off = [true, true]
	off.run()
	_check((off.result()["talks"] as Array).is_empty(), "A balance arm can switch the talks off")


## From the hub to quarter time on a phone: the sit-down with real taps, the
## dice landing on the sim's roll; at half time the speech the same way.
func _test_break_on_a_phone(sz: Vector2i) -> void:
	var db = tree.root.get_node("GameDB")
	var router = tree.root.get_node("Router")
	_state.reset()
	_state.replay_seed = 2027
	_state.start_season("COL", db.club_list("COL"))
	_state.set_setting("seen_weekly_loop_intro", true)
	tree.root.size = sz
	router.stack = ["hub"]
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	tree.root.add_child(hub)
	await _settle()
	_state.set_vignettes_on(false)
	hub.call("_on_play_match")
	await _settle()
	var m: Node = tree.current_scene
	if m == null or m.name != "MatchScene":
		_check(false, "The match opens (%s)" % str(sz))
		hub.queue_free()
		return
	var spoke := false
	var sat := 0
	var guard := 0
	while not bool(m.get("_finished")) and guard < 20000:
		guard += 1
		var box = m.get("_coach_overlay")
		var mo = m.get("_moment_overlay")
		if box != null and is_instance_valid(box):
			var sim: MatchSim = _state.pending_sim
			var q := sim.current_quarter
			if q > 1:
				var my_side := int(m.get("_my_side"))
				var row: Control = m.find_child("CallRow_sit", true, false)
				_check(row != null and row.is_visible_in_tree(), "%s: the sit-down has its row at break %d" % [sz, q])
				# A real tap on the first player offered (after Nobody).
				var grid: Node = m.find_child("SitPickerGrid", true, false)
				var first: Button = null
				if grid != null:
					for b in grid.get_children():
						if b is Button and not str(b.name).ends_with("Grid_") and str(b.name) != "SitPickerGrid_" and not str(b.name).ends_with("Other"):
							first = b
							break
				var why: String = await Tap.tap(first) if first != null else "no player offered"
				await _settle()
				_check(why == "", "%s: a real tap picks a player at break %d (%s)" % [sz, q, why])
				var go: Button = m.find_child("SitDown", true, false)
				_check(go != null and go.text.begins_with("Sit down with") and not go.disabled,
						"%s: the button names him (%s)" % [sz, go.text if go != null else "none"])
				var gain: Node = m.find_child("SitGainCost", true, false)
				_check(gain != null and (gain as Control).is_visible_in_tree(), "%s: the gate shows the odds once he is picked" % sz)
				why = await Tap.tap(go) if go != null else "no button"
				_check(why == "", "%s: a real tap sits down (%s)" % [sz, why])
				await _settle(80)
				var t := sim.talk_now(my_side, "sit")
				var dice = m.find_child("SitDice", true, false)
				var said: Label = m.find_child("SitResult", true, false)
				_check(not t.is_empty() and dice != null and dice.is_landed() and dice.faces == t["dice"],
						"%s: the dice land on the sim's roll at break %d" % [sz, q])
				_check(said != null and said.visible and said.text == BreakTalks.result_line("sit", str(t["band"]),
						m.call("_surname", _db.player_display_name_by_id(str(t["id"]), "He"))),
						"%s: the result is said (%s)" % [sz, said.text if said != null else ""])
				if dice != null:
					var r: Rect2 = dice.get_global_rect()
					_check(r.position.x >= 0.0 and r.end.x <= float(sz.x), "%s: the dice fit the phone (%s)" % [sz, r])
				_check(go == null or not go.visible, "%s: once a break: the button goes" % sz)
				sat += 1
				# Done shuts the sit-down's sheet (a real tap), as a coach does.
				var done_b: Control = m.find_child("CallDone", true, false)
				var why_d: String = await Tap.tap(done_b) if done_b != null else "no Done"
				await _settle()
				_check(why_d == "" or m.get("_pc_break"), "%s: Done shuts the sheet (%s)" % [sz, why_d])
				if q == 3:
					var sp: Button = m.find_child("GiveSpeech", true, false)
					why = await Tap.tap(sp) if sp != null else "no speech button"
					_check(why == "", "%s: a real tap gives the speech (%s)" % [sz, why])
					await _settle(80)
					var st := sim.talk_now(my_side, "speech")
					var sd = m.find_child("SpeechDice", true, false)
					_check(not st.is_empty() and sd != null and sd.faces == st["dice"], "%s: the speech's dice land on its roll" % sz)
					spoke = true
				else:
					_check(m.find_child("GiveSpeech", true, false) == null, "%s: no speech but at half time (break %d)" % [sz, q])
				# Close the sheet the taps opened, then start the quarter.
				m.call("_close_break_sheets")
				await _settle()
			var start: Control = m.find_child("StartQuarter", true, false)
			var w: String = await Tap.tap(start)
			await _settle()
			if w != "":
				_check(false, "%s: a real tap on Start (%s)" % [sz, w])
				break
		elif mo != null and is_instance_valid(mo) and not _state.pending_sim.pending_moment.is_empty():
			m.call("_on_moment_choice", int(_state.pending_sim.pending_moment.get("default", 0)))
			await tree.process_frame
		elif int(m.get("_breaks_played")) < 3 and not bool(m.get("_skipping")):
			# The quarter itself is not under test: play it out at once.
			m.call("_on_skip_to_break")
			await _settle()
		else:
			var pv = m.get("_pitch")
			pv.set_speed(8.0)
			if pv.playing:
				pv._process(0.25)
			await tree.process_frame
	_check(sat == 3 and spoke, "%s: three sit-downs and a speech in the match (%d, %s)" % [sz, sat, str(spoke)])
	for n in [hub, m]:
		if n != null and is_instance_valid(n) and n != tree.root:
			n.queue_free()
	_state.pending_sim = null
	await _settle()
