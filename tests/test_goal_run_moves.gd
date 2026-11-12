extends RefCounted
## Row 14: the run of goals against you offers two concrete football moves
## over a centre ball-up, each with its gain and cost as percentages, neither
## called the better. Run through tests/run_goal_run_moves_tests.gd. Seeded by
## design.

const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")

var _state: Node
var tree: SceneTree
var root: Window
var checks := 0
var failures: Array[String] = []


func run() -> void:
	failures.clear()
	checks = 0
	tree = Engine.get_main_loop() as SceneTree
	root = tree.root
	_state = root.get_node("GameState")
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	_state.replay_seed = 2027
	root.get_node("GameDB").reload()
	await _t("_test_on_offers_two_moves")
	await _t("_test_each_move_takes_effect")
	await _t("_test_no_call_in_a_simulated_match")
	for vignettes in [true, false]:
		await _t("_test_the_card_on_a_phone", [vignettes])
	print(Ran.line("Goal run moves", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _sim(seed: int) -> MatchSim:
	var db = root.get_node("GameDB")
	return MatchSim.new(Squad.new("MEL", db.club_list("MEL"), true, "MEL"),
			Squad.new("CAR", db.club_list("CAR"), false, "CAR"), seed)


## A sim that has just conceded its third goal in a row, with a call due.
func _run_against(seed: int) -> MatchSim:
	var sim := _sim(seed)
	sim.moment_side = 0
	sim.current_quarter = 2
	sim.current_minute = 40
	sim._moments_this_q = 0
	sim._last_moment_chain = sim._chain_no - 100
	(sim.team_stats[1] as Dictionary)["goals"] = 3.0
	sim._run = [0, 3]
	return sim


func _test_on_offers_two_moves() -> void:
	var sim := _run_against(4500)
	_check(sim._boundary_moment() and str(sim.pending_moment["kind"]) == "momentum", "The run still asks a call")
	var opts: Array = sim.pending_moment["options"]
	_check(opts.size() == 2 and str(opts[0]["key"]) == "stack" and str(opts[1]["key"]) == "flood",
			"Two moves: stack the centre bounce, flood behind the ball")
	var all := ""
	for o in opts:
		var gain := str(o["gain"])
		var cost := str(o["cost"])
		all += " " + gain + " " + cost + " " + str(o["label"]) + " " + str(o["detail"])
		_check(gain.contains("%") and cost.contains("%"),
				"%s says what it gains and what it costs, as percentages (%s / %s)" % [o["label"], gain, cost])
	var low := all.to_lower()
	_check(not low.contains("best") and not low.contains("recommend") and not low.contains("better option")
			and not low.contains("ride it out"),
			"No option is called the better, and there is no Ride it out")
	# The percentages are the engine's own constants, not typed copy.
	var mins: int = 2 * 30 - 40
	var stack := GateOdds.burst_lines("stack", mins, false)
	_check(str(opts[0]["gain"]) == GateOdds.gain(str(stack[0])) and str(opts[0]["cost"]) == GateOdds.cost(str(stack[1])),
			"The stack lines come from the engine's constants")
	var flood := GateOdds.burst_lines("flood", mins, false)
	_check(str(opts[1]["gain"]) == GateOdds.gain(str(flood[0])) and str(opts[1]["cost"]) == GateOdds.cost(str(flood[1])),
			"The flood lines come from the engine's constants")


func _test_each_move_takes_effect() -> void:
	for pick in [0, 1]:
		var sim := _run_against(4501)
		sim._boundary_moment()
		var m := sim.resolve_moment(pick)
		var key := "stack" if pick == 0 else "flood"
		_check((sim.bursts[0] as Dictionary).has(key) and (sim.bursts[0] as Dictionary).size() == 1,
				"Taking %s starts exactly that call" % key)
		_check(str(m["outcome"]).contains(str(MatchSim.BURSTS[key]["label"])),
				"The outcome names the move (%s)" % str(m["outcome"]))


## A match nobody is coaching (Sim the week, AI v AI) makes no call.
func _test_no_call_in_a_simulated_match() -> void:
	var sim := _run_against(4502)
	sim._boundary_moment()
	var m := sim.resolve_moment(int(sim.pending_moment["default"]))
	_check(int(m["choice"]) == -1 and (sim.bursts[0] as Dictionary).is_empty() and str(m["outcome"]) == "No change.",
			"The default is no call: no burst starts")
	var played := 0
	for seed in range(7000, 7006):
		var res := _sim(seed).run()
		for mm in res.get("moments", []):
			if str((mm as Dictionary).get("kind", "")) == "momentum":
				_check(int((mm as Dictionary)["choice"]) == -1, "A simulated match makes no run call")
		played += 1 if res.has("score") else 0
	_check(played == 6, "Six simulated matches play through (%d)" % played)


func _test_the_card_on_a_phone(vignettes: bool) -> void:
	var tag := "scene" if vignettes else "no scene"
	_state.set_vignettes_on(vignettes)
	var db = root.get_node("GameDB")
	var sz := Vector2i(360, 740)
	_state.reset()
	_state.start_season("COL", db.club_list("COL"))
	root.size = sz
	_check(_state.prepare_interactive_match(), "A live match is prepared (%s)" % tag)
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await _settle()
	(m.find_child("StartQuarter", true, false) as Button).emit_signal("pressed")
	await _settle()
	m.get("_pitch").pause()
	var sim: MatchSim = _state.pending_sim
	var me := int(m.get("_my_side"))
	var them := 1 - me
	sim.pending_moment = {}
	sim.moment_side = me
	sim.current_quarter = 2
	sim.current_minute = 40
	sim._moments_this_q = 0
	sim._last_moment_chain = sim._chain_no - 100
	sim._run = [0, 0]
	sim._run[them] = 3
	(sim.team_stats[them] as Dictionary)["goals"] = float(sim.goals(them) + 3)
	_check(sim._boundary_moment() and bool(sim.pending_moment.get("moves", false)),
			"MatchSim asks the two-move call (%s)" % tag)
	m.call("_show_moment")
	await _settle()
	var card = m.find_child("MomentCard", true, false)
	_check(card != null, "The call card opens (%s)" % tag)
	if card == null:
		m.queue_free()
		return
	var vig = m.find_child("StoppageVignette", true, false)
	if vignettes:
		# The intended art loaded, not a fallback: the figure sheets at their contract size,
		# the players dressed in both clubs' guernseys, both sides at the ball-up.
		_check(vig != null and vig.tokens.size() >= 6, "The call opens over the centre ball-up scene")
		var mat := (vig.material as ShaderMaterial) if vig != null else null
		_check(mat != null and Vector2i((vig.FIGURE_SHADE as Texture2D).get_size()) == VignetteFigures.SHEET_SIZE
				and Array(mat.get_shader_parameter("kit_base")).size() == 4,
				"The figure sheet and club guernseys are loaded (not a fallback)")
		vig.finish_now()
		for i in range(40):
			await tree.process_frame
	else:
		_check(vig == null, "Vignettes off: no scene")
	var buttons := card.find_children("Moment_*", "Button", true, false)
	_check(buttons.size() == 2, "Exactly two moves to tap (%d)" % buttons.size())
	# The heading is drawn by the scene when there is one, else it is on the card.
	var text := _text(card) + (str(vig.title) if vig != null else "")
	_check(text.contains("They have kicked 3 in a row") and text.contains("%"),
			"The card names the run and gives the odds in percentages (%s)" % tag)
	_check(not text.contains("Ride it out") and not text.to_lower().contains("recommend"), "No Ride it out, no advice")
	var viewport := Rect2(Vector2.ZERO, Vector2(sz))
	var fits := true
	for b in buttons:
		fits = fits and viewport.encloses((b as Button).get_global_rect()) and (b as Button).size.y >= 44.0
	_check(fits, "Both moves are on screen and thumb-sized (%s)" % tag)
	# A real tap on the second move, the way a finger delivers it.
	var asked := sim.moments.size()
	var why: String = await Tap.tap(buttons[1])
	_check(why == "", "A real tap reaches the second move (%s: %s)" % [tag, why])
	var taken: Dictionary = sim.moments[asked] if sim.moments.size() > asked else {}
	_check(str(taken.get("choice_label", "")) == "Flood behind the ball" and str(taken.get("kind", "")) == "momentum"
			and str(taken.get("outcome", "")).begins_with("Flood behind the ball"),
			"The tap makes the call: flood behind the ball (%s)" % tag)
	for i in range(40):
		await tree.process_frame
	_check(not is_instance_valid(card) or card.get_parent() == null, "The card is gone once it is answered (%s)" % tag)
	m.queue_free()
	await _settle()
	_state.set_vignettes_on(true)


func _settle() -> void:
	for i in range(6):
		await tree.process_frame


func _text(node: Node) -> String:
	var out := ""
	for n in node.find_children("*", "Control", true, false):
		if n is Label:
			out += (str(n.get_meta("plain")) if n.has_meta("plain") else (n as Label).text) + "\n"
		elif n is RichTextLabel:
			out += (n as RichTextLabel).get_parsed_text() + "\n"
	return out
