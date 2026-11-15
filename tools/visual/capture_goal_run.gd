extends SceneTree
## Row 14: the run-of-goals call over the centre ball-up
## scene, and without the scene. Needs a real renderer:
##   godot --path . --script tools/visual/capture_goal_run.gd -- --out /tmp/gr [--size 390x844] [--club FRE] [--bounce 1]
## Writes <out>_scene_<n>.png (the scene playing in, then frozen with the call up)
## and <out>_card.png (vignettes off). --bounce 1 stages the late centre ball-up call
## instead (last quarter, 8 minutes left, the scores as the match has them).

var W := 390
var H := 844
var _out := "/tmp/gr"
var _bounce := false


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
	if _bounce:
		sim.current_quarter = 4
		sim.current_minute = 112
		sim._fire_bounce(sim.score(me) - sim.score(them))
	else:
		sim._run = [0, 0]
		sim._run[them] = 3
		(sim.team_stats[them] as Dictionary)["goals"] = float(sim.goals(them) + 3)
		sim._boundary_moment()
	# The scoreboard shows the staged moment's quarter, minute and scores.
	m.call("_update_scoreboard", {"goals": [sim.goals(0), sim.goals(1)], "behinds": [sim.behinds(0), sim.behinds(1)],
			"q": sim.current_quarter, "min": sim.current_minute})
	for o in sim.pending_moment.get("options", []):
		print("CALL ", o.get("label", ""), " | ", o.get("gain", ""), " | ", o.get("cost", ""))
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
			"--bounce":
				_bounce = str(a[i + 1]) == "1"
			"--size":
				var wh := str(a[i + 1]).split("x")
				W = int(wh[0])
				H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	state.autosave_enabled = false
	state.save_path = "user://capture_gr.save"
	state.settings_path = "user://capture_gr_settings.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	await _frames(10)
	var m: Control = await _stage(club, true)
	var vig = m.find_child("StoppageVignette", true, false)
	print("scene art: ", vig != null, " tokens ", vig.tokens.size() if vig != null else 0,
			" sheet ", (vig.FIGURE_SHADE as Texture2D).get_size() if vig != null else Vector2.ZERO)
	for n in range(3):
		await _frames(30)
		await _shot("%s_scene_%d.png" % [_out, n])
	vig.finish_now()
	await _frames(40)
	await _shot("%s_scene_3.png" % _out)
	m.queue_free()
	await _frames(4)
	m = await _stage(club, false)
	await _frames(20)
	await _shot("%s_card.png" % _out)
	m.queue_free()
	quit(0)
