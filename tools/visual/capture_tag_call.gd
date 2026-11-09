extends SceneTree
## Row 120: the call when their midfielder is kicking a bag, with what each answer does and
## costs. Needs a real renderer:
##   godot --path . --script tools/visual/capture_tag_call.gd -- --out /tmp/tc [--club FRE]
## Writes <out>_scene.png (the scene with the call up) and <out>_card.png (vignettes off),
## and prints the call's lines.

var W := 390
var H := 844
var _out := "/tmp/tc"


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String) -> void:
	await _frames(2)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(path)
	print("wrote ", path, " ", img.get_size())


func _stage(club: String, vignettes: bool) -> Control:
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.set_vignettes_on(vignettes)
	state.reset()
	state.replay_seed = 2027
	state.start_season(club, db.club_list(club))
	state.prepare_interactive_match()
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await _frames(8)
	(m.find_child("StartQuarter", true, false) as Button).emit_signal("pressed")
	await _frames(8)
	m.get("_pitch").pause()
	var sim = state.pending_sim
	var me := int(m.get("_my_side"))
	var them := 1 - me
	sim.pending_moment = {}
	sim.moment_side = me
	sim.current_quarter = 2
	sim.current_minute = 40
	sim._moments_this_q = 0
	sim._last_moment_chain = sim._chain_no - 100
	for p in sim.squads[them].ground:
		if str(p["role"]) == "MID":
			sim.player_stats[str(p["id"])] = {"goals": 3.0}
			break
	sim._boundary_moment()
	print("MOMENT ", sim.pending_moment.get("kind", ""), " ", sim.pending_moment.get("title", ""))
	for o in sim.pending_moment.get("options", []):
		print("OPTION ", o.get("label", ""), " | ", o.get("gain", ""), " | ", o.get("cost", ""))
	m.call("_show_moment")
	return m


func _run() -> void:
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out":
				_out = str(a[i + 1])
			"--club":
				club = str(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	state.autosave_enabled = false
	state.save_path = "user://capture_tc.save"
	state.settings_path = "user://capture_tc_settings.cfg"
	state.show_real_names = true
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	await _frames(10)
	var m: Control = await _stage(club, true)
	await _frames(200)
	await _shot(_out + "_scene.png")
	m.queue_free()
	await _frames(4)
	var m2: Control = await _stage(club, false)
	await _frames(30)
	await _shot(_out + "_card.png")
	m2.queue_free()
	quit(0)
