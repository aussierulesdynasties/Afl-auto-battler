extends SceneTree
## Visual review tool for T3.R42 (the score and clock stay on screen): one
## live match on a phone, a still in every match-day state the score test
## walks (tests/run_score_clock_tests.gd). Needs a real renderer and a window
## (keep it off screen with an override.cfg). Never touches a real save.
##   godot --path . --script tools/visual/capture_score_clock.gd -- --out <prefix> [--size 390x844]
## Writes <prefix>_<n>_<state>.png.

var _w := 390
var _h := 844
var _out := "score_clock"
var _n := 0
var _taken := {}


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				_out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_score_clock.save"
	state.settings_path = "user://capture_score_clock.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.show_real_names = false
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	state.set_vignettes_on(true)
	state.set_bounce_scene_every_match(true)
	state.reset()
	state.replay_seed = 2027
	state.start_season("COL", db.club_list("COL"))
	state.set_match_way("watch")
	state.prepare_interactive_match()
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await _frames(20)
	var names := ["pre_bounce", "quarter_time", "half_time", "three_quarter_time"]
	var at := 0
	var guard := 0
	while not bool(m.get("_fulltime_shown")) and guard < 60000:
		guard += 1
		var box: Node = m.find_child("CoachBox", true, false)
		if box != null:
			var nm := str(names[mini(at, 3)])
			await _frames(30)
			await _shot(nm + "_break")
			var best: Button = box.find_child("BestSoFarOpen", true, false)
			if at == 1 and best != null and best.is_visible_in_tree():
				best.emit_signal("pressed")
				await _frames(30)
				await _shot(nm + "_best")
				var sheet: Node = m.find_child("CallSheet_best", true, false)
				var stats: Button = sheet.find_child("BreakStats", true, false) if sheet != null else null
				if stats != null:
					stats.emit_signal("pressed")
					await _frames(30)
					await _shot(nm + "_stats")
					m.call("handle_back")
					await _frames(6)
				m.call("handle_back")
				await _frames(6)
			(box.find_child("StartQuarter", true, false) as Button).emit_signal("pressed")
			await _frames(6)
			at += 1
			if at == 1:
				var pitch0 = m.get("_pitch")
				for i in 40:
					if pitch0.playing:
						pitch0._process(0.25)
					await process_frame
				await _shot("live")
			continue
		var card: Node = m.find_child("MomentCard", true, false)
		if card != null:
			var pick: Button = card.find_child("Moment_0", true, false)
			if pick != null and not pick.disabled and pick.is_visible_in_tree():
				var kind := "call_scene" if card.has_meta("scene") else "call_card"
				if not _taken.has(kind):
					await _frames(40)
					await _shot(kind)
				pick.emit_signal("pressed")
				await _frames(6)
				continue
		var replay: Node = m.find_child("BroadcastVignetteOverlay", true, false)
		if replay != null:
			if not _taken.has("replay"):
				await _frames(60)
				await _shot("replay")
			m.call("_finish_broadcast")
			await _frames(6)
			continue
		var pitch = m.get("_pitch")
		if pitch != null and pitch.playing:
			pitch._process(0.25)
		await process_frame
	await _frames(40)
	await _shot("full_time")
	var fv: Node = root.find_child("FarewellVignette", true, false)
	if fv != null and fv.has_method("finish_now"):
		fv.call("finish_now")
		await _frames(20)
		await _shot("full_time_after_farewell")
	var tab: Button = m.find_child("ReviewTab_stats", true, false)
	if tab != null:
		tab.emit_signal("pressed")
		await _frames(20)
		await _shot("full_time_stats")
	quit()


func _shot(name: String) -> void:
	_taken[name] = true
	_n += 1
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	if img == null:
		print("no renderer: ", name)
		return
	var path := "%s_%02d_%s.png" % [_out, _n, name]
	img.save_png(path)
	print("wrote ", path)


func _frames(n: int) -> void:
	for i in n:
		await process_frame
