extends SceneTree
## Coaches' votes at the half-time break and at full time, 390x844.
##   godot --path . --script tools/visual/capture_votes.gd -- --out <dir>/votes --club FRE --vs MEL [--seed 2050]
## Writes <out>_<club>_ht.png (the break, scrolled to Best so far) and <out>_<club>_ft.png (full time).
var _vp: SubViewport


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "votes"
	var club := "FRE"
	var vs := "MEL"
	var seed_from := 2050
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out": out = str(a[i + 1])
			"--club": club = str(a[i + 1])
			"--vs": vs = str(a[i + 1])
			"--seed": seed_from = int(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_votes.save"
	state.settings_path = "user://capture_votes.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	_vp = SubViewport.new()
	_vp.size = Vector2i(390, 844)
	_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(_vp)
	await _frames(4)
	var tries := 0
	while true:
		state.reset()
		state.career_seed = seed_from + tries
		state.replay_seed = seed_from + tries
		state.set_setting("seen_training_intro", true)
		state.start_season(club, db.club_list(club))
		state.prepare_interactive_match()
		var s0 = state.pending_sim
		var them := str(s0.squads[1].code) if str(s0.squads[0].code) == club else str(s0.squads[0].code)
		if them == vs or tries > 80:
			break
		tries += 1
	var sim = state.pending_sim
	sim.run_quarter()
	sim.run_quarter()
	var scene = load("res://scenes/MatchScene.tscn").instantiate()
	_vp.add_child(scene)
	await _frames(24)
	var open_best: Button = scene.find_child("BestSoFarOpen", true, false)
	print("BestSoFarOpen found ", open_best != null)
	if open_best != null:
		open_best.emit_signal("pressed")
	await _frames(14)
	await _shot("%s_%s_ht.png" % [out, club])
	scene.queue_free()
	await _frames(4)
	sim.run_quarter()
	sim.run_quarter()
	scene = load("res://scenes/MatchScene.tscn").instantiate()
	_vp.add_child(scene)
	await _frames(4)
	scene.set("_res", sim.result())
	scene.set("_finished", true)
	scene.call("_show_fulltime")
	await _frames(14)
	var bp: Node = scene.find_child("BestPlayers", true, false)
	print("BestPlayers found ", bp != null)
	for s in scene.find_children("*", "ScrollContainer", true, false):
		if bp != null and (s as Control).is_ancestor_of(bp):
			(s as ScrollContainer).scroll_vertical = int((bp as Control).global_position.y - (s as Control).global_position.y + (s as ScrollContainer).scroll_vertical) - 60
	await _frames(6)
	await _shot("%s_%s_ft.png" % [out, club])
	quit()


func _shot(path: String) -> void:
	await _frames(2)
	var img := _vp.get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(path)
	print("wrote ", path)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame
