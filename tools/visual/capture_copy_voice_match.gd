extends SceneTree
## Copy voice pass 3 (the match view, director 2026-11-10: option B) captures, phone portrait
## 390x844, dark, a fresh Fremantle career against Melbourne that never touches a real save. One
## launch writes every state whose copy the pass changed, so the same script gives the before (on
## main) and the after:
##   godot --path . --script tools/visual/capture_copy_voice_match.gd -- --out <prefix>
## Writes <prefix>_<state>.png for: pre_calls (Our calls, Our side), pre_who (Who tags, the
## assistant's pick), q2_break, q2_did (What our calls did), q2_stats (Back to our calls),
## live (the setup line and the momentum note), momentum (the momentum sheet), live_back (Finish
## the match first), ft_why (Why we won or lost, Our best), ft_glance (Our synergies, the calls by
## quarter, Our week), ft_stats (What our calls did for the match).
##   --club CODE (default FRE)   --vs CODE (default MEL)

var _out := "copy_voice_match"
var _club := "FRE"
var _vs := "MEL"
var _state: Node
var _db: Node


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out":
				_out = str(a[i + 1])
			"--club":
				_club = str(a[i + 1])
			"--vs":
				_vs = str(a[i + 1])
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.save_path = "user://capture_copy_voice_match.save"
	_state.settings_path = "user://capture_copy_voice_match.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(390, 844)
	DisplayServer.window_set_size(Vector2i(390, 844))

	# Before the first bounce: Our calls, Our side; then Who tags.
	_new_match()
	var sim = _state.pending_sim
	var me := int(sim.moment_side)
	var scene = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(scene)
	await _frames(16)
	await _shot("pre_calls")
	_press(scene, "CallRow_tag")
	await _frames(8)
	var tp: Node = scene.find_child("TagPicker", true, false)
	if tp != null:
		for b in tp.find_children("TagPickerGrid_*", "Button", true, false):
			if str(b.name) != "TagPickerGrid_":
				(b as Button).emit_signal("pressed")
				break
	await _frames(8)
	_press(scene, "WhoTagsChange")
	await _frames(8)
	await _shot("pre_who")
	root.remove_child(scene)
	scene.queue_free()
	await _frames(4)

	# Quarter time after a quarter with a tag on: What our calls did, Match stats.
	_new_match()
	sim = _state.pending_sim
	me = int(sim.moment_side)
	var t: Dictionary = (sim.tactics[me] as Dictionary).duplicate()
	t["gameplan"] = "defensive"
	for p in (sim.squads[1 - me]).ground:
		if sim.tag_target_ok(1 - me, str(p["id"])):
			t["tag_id"] = str(p["id"])
			t["tag_set"] = true
			break
	sim.set_tactics(me, t)
	sim.run_quarter()
	scene = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(scene)
	await _frames(16)
	await _shot("q2_break")
	_press(scene, "CallsDidOpen")
	await _frames(8)
	await _shot("q2_did")
	scene.call("handle_back")
	await _frames(6)
	scene.call("_show_break_stats")
	await _frames(8)
	await _shot("q2_stats")
	root.remove_child(scene)
	scene.queue_free()
	await _frames(4)

	# Live: the setup line and the first match's momentum note, the sheet, then Back.
	_new_match()
	sim = _state.pending_sim
	scene = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(scene)
	await _frames(16)
	_press(scene, "StartQuarter")
	await _frames(8)
	var pitch = scene.get("_pitch")
	var guard := 0
	var note: Node = scene.find_child("MomentumNote", true, false)
	while guard < 4000:
		if note != null and (note as CanvasItem).modulate.a >= 1.0:
			break
		if scene.find_child("CoachBox", true, false) != null:
			break
		if pitch.playing:
			pitch._process(0.25)
		await process_frame
		guard += 1
		var card: Node = scene.find_child("MomentCard", true, false)
		if card != null:
			var pick: Node = card.find_child("Moment_0", true, false)
			if pick is Button:
				(pick as Button).emit_signal("pressed")
			await _frames(6)
	if pitch.playing:
		(scene.get("_play_btn") as Button).emit_signal("pressed")
	await _frames(8)
	await _shot("live")
	scene.call("_show_momentum_info")
	await _frames(8)
	await _shot("momentum")
	scene.call("handle_back")
	await _frames(4)
	scene.call("handle_back")
	await _frames(6)
	await _shot("live_back")
	root.remove_child(scene)
	scene.queue_free()
	await _frames(4)

	# Full time, after a match with a call at every break.
	_new_match()
	sim = _state.pending_sim
	me = int(sim.moment_side)
	for q in range(1, 5):
		t = (sim.tactics[me] as Dictionary).duplicate()
		t["gameplan"] = ["attacking", "balanced", "defensive", "contest"][q - 1]
		if q == 1:
			for p in (sim.squads[1 - me]).ground:
				if sim.tag_target_ok(1 - me, str(p["id"])):
					t["tag_id"] = str(p["id"])
					t["tag_set"] = true
					break
		sim.set_tactics(me, t)
		sim.run_quarter()
	var res: Dictionary = sim.result()
	res["home"] = _state.pending_match["home"]
	res["away"] = _state.pending_match["away"]
	res["label"] = _state.pending_match["label"]
	_state.finish_interactive_match(res)
	_state.pending_sim = null
	_state.pending_match = {}
	_state.review_requested = true
	scene = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(scene)
	await _frames(20)
	await _scroll_to(scene, "WhyReasons", 200)
	await _shot("ft_why")
	await _scroll_to(scene, "FullTimeSynergies", 80)
	await _shot("ft_glance")
	# The calls readout shows on the Stats tab of a match you played; this review stands in for one.
	scene.set("_interactive", true)
	scene.set("_ft_tab", "stats")
	scene.call("_render_ft")
	await _frames(12)
	await _scroll_to(scene, "CallsReadout", 80)
	await _shot("ft_stats")
	_state.delete_saved_career()
	quit(0)


func _new_match() -> void:
	var tries := 0
	while true:
		_state.reset()
		_state.career_seed = 2026 + tries
		_state.replay_seed = 2026 + tries
		_state.set_setting("seen_training_intro", true)
		_state.start_season(_club, _db.club_list(_club))
		if not _state.prepare_interactive_match():
			push_error("no match to prepare")
			quit(1)
			return
		var s0 = _state.pending_sim
		var them := str(s0.squads[1].code) if str(s0.squads[0].code) == _club else str(s0.squads[0].code)
		if them == _vs or tries > 80:
			print("match: ", s0.squads[0].code, " v ", s0.squads[1].code, " seed ", _state.career_seed)
			return
		tries += 1


func _press(scene: Node, node_name: String) -> void:
	var b: Node = scene.find_child(node_name, true, false)
	if b is BaseButton and not (b as BaseButton).disabled:
		(b as BaseButton).emit_signal("pressed")
	else:
		print("MISSING ", node_name)


## Scrolls the page that holds `node_name` so the node sits `top` px under the page's top.
func _scroll_to(scene: Node, node_name: String, top: int) -> void:
	var n: Control = scene.find_child(node_name, true, false)
	if n == null:
		print("MISSING ", node_name)
		return
	var sc: Node = n.get_parent()
	while sc != null and not (sc is ScrollContainer):
		sc = sc.get_parent()
	if sc != null:
		var s := sc as ScrollContainer
		s.scroll_vertical = s.scroll_vertical + int(n.get_global_rect().position.y - s.global_position.y) - top
	await _frames(8)


func _shot(shot: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	if img == null:
		print("no renderer: ", shot)
		return
	img.convert(Image.FORMAT_RGBA8)
	var path := "%s_%s.png" % [_out, shot]
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
