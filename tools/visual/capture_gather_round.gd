extends SceneTree
## Visual review tool for Gather Round (row 74, switch `gather_round`). Needs a real
## renderer (a windowed Godot, or capture.yml):
##   godot --path . --script tools/visual/capture_gather_round.gd -- --out tmp/row74-caps/gr
## A seeded Geelong career with the switch on, played to the week of Gather Round.
## Writes <out>_hub.png (the week's match poster), <out>_fixture.png (the fixture list
## open on Gather Round), <out>_match.png (the live match's header) and
## <out>_results.png (the fixture list after the round). --size WxH (default 390x844).

var _w := 390
var _h := 844


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "gather_round"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
	await process_frame
	var F = load("res://scripts/core/Features.gd")
	F.set_on("gather_round", true)
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_gather.save"
	state.settings_path = "user://capture_gather.cfg"
	state.reset()
	state.career_seed = 2027
	state.replay_seed = 2027
	for k in ["seen_training_intro", "seen_season_stats_intro", "seen_weekly_loop_intro"]:
		state.set_setting(k, true)
	state.start_season("GEE", db.club_list("GEE"))
	var g: int = state.season.gather_round()
	var guard := 0
	while state.season.round_index < g and guard < 30:
		state.advance()
		guard += 1
	state.media_conference = {}   # the press sit-down is not what this capture shows
	print("CAPTURE gather round ", g + 1, " at round ", state.season.round_index + 1)
	UK.apply_appearance("dark")
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	var sl = root.get_node("ScreenLayout")
	sl.ui_scale = 96.0 / maxf(96.0, float(DisplayServer.screen_get_dpi()))
	sl.call("_update_scale")

	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(20)
	_save(out + "_hub.png")
	hub.queue_free()
	await _frames(2)

	load("res://scripts/ui/StatsHubScene.gd").current = "fixture"
	var stats: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(stats)
	await _frames(10)
	_save(out + "_fixture.png")
	stats.queue_free()
	await _frames(2)

	if state.prepare_interactive_match():
		var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
		root.add_child(m)
		await _frames(30)
		_save(out + "_match.png")
		m.queue_free()
		await _frames(2)
		var res: Dictionary = state.pending_sim.run()
		res["venue"] = str(state.pending_match.get("venue", ""))
		state.finish_interactive_match(res)
	load("res://scripts/ui/StatsHubScene.gd").current = "fixture"
	stats = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(stats)
	await _frames(10)
	var prev: Button = stats.find_child("PrevRound", true, false)
	if prev != null:
		prev.emit_signal("pressed")
		await _frames(10)
	_save(out + "_results.png")
	quit(0)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
