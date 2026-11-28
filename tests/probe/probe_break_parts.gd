extends SceneTree
## Scratch probe (never commit): what each part of the phone break holds, as the
## matchday_breaks test sets it up (390x844, picks named), after the facts fit.

var _state: Node


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _dump(n: Node, depth: int, max_depth: int) -> void:
	if not (n is Control):
		return
	var c := n as Control
	if not c.visible:
		print("PROBE ", "  ".repeat(depth), n.name, " (hidden)")
		return
	var txt := ""
	if c is Label:
		txt = (c as Label).text.substr(0, 60)
	elif c is RichTextLabel:
		txt = (c as RichTextLabel).get_parsed_text().substr(0, 60)
	elif c is Button:
		txt = (c as Button).text.substr(0, 40)
	print("PROBE ", "  ".repeat(depth), n.name, " h=", int(c.get_combined_minimum_size().y), " '", txt, "'")
	if depth < max_depth:
		for ch in n.get_children():
			_dump(ch, depth + 1, max_depth)


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.event_sheets = false
	_state.save_path = "user://test_career.save"
	_state.settings_path = "user://test_settings.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	_state.replay_seed = 2027
	var sz := Vector2i(390, 844)
	for pair in [["COL", "CAR"], ["FRE", "MEL"]]:
		var club: String = pair[0]
		var vs: String = pair[1]
		root.size = sz
		var hit := 0
		for tries in range(80):
			_state.reset()
			_state.career_seed = 2050 + tries
			_state.replay_seed = 2050 + tries
			_state.set_setting("seen_training_intro", true)
			_state.start_season(club, db.club_list(club))
			_state.prepare_interactive_match()
			var sq = _state.pending_sim.squads
			if str(sq[0].code) == vs or str(sq[1].code) == vs:
				hit = 2050 + tries
				break
		for q in [2, 3]:
			_state.reset()
			_state.career_seed = hit
			_state.replay_seed = hit
			_state.set_setting("seen_training_intro", true)
			_state.start_season(club, db.club_list(club))
			_state.prepare_interactive_match()
			var sim = _state.pending_sim
			var me := int(sim.moment_side)
			var t: Dictionary = (sim.tactics[me] as Dictionary).duplicate()
			var used := {}
			for slot in load("res://scripts/ui/match/MatchNotes.gd").FOCUS_ORDER:
				for p in sim.squads[me].ground:
					if not used.has(str(p["id"])):
						t[slot] = str(p["id"])
						used[str(p["id"])] = true
						break
			sim.set_tactics(me, t)
			for i in range(q - 1):
				sim.run_quarter()
			var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
			root.add_child(m)
			await _frames(40)
			var box: Node = m.find_child("CoachBox", true, false)
			print("PROBE ==== %s v %s q%d seed %d" % [club, vs, q, hit])
			for sc in box.find_children("*", "ScrollContainer", true, false):
				var scc := sc as ScrollContainer
				if scc.vertical_scroll_mode == ScrollContainer.SCROLL_MODE_DISABLED:
					continue
				var inner: Control = null
				for ch in scc.get_children():
					if ch is Control and not (ch is ScrollBar):
						inner = ch
						break
				print("PROBE room ", int(scc.size.y), " holds ", int(inner.get_combined_minimum_size().y), " sep ",
						inner.get_theme_constant("separation") if inner is BoxContainer else -1)
				_dump(inner, 0, 3)
				break
			var footer: Node = box.find_child("*Footer*", true, false)
			m.queue_free()
			await _frames(6)
	quit(0)
