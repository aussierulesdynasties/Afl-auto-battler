extends SceneTree
## The PC match column in play: the setup line, the feed, the live stats and the
## controls, drawn in a SubViewport of exactly the given size. Needs a real renderer:
##   godot --windowed --path . --script tools/visual/capture_match_column.gd -- --out /tmp/col --size 1600x900 [--frames 600]
## Writes <out>.png and prints each part of the column's height against what it needs. Seeded; never touches a real save.

var _w := 1600
var _h := 900
var _vp: SubViewport


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	var out := "col"
	var frames := 600
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out": out = str(a[i + 1])
			"--frames": frames = int(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_match_column.save"
	state.settings_path = "user://capture_match_column.cfg"
	state.set_setting("seen_training_intro", true)
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	_vp = SubViewport.new()
	_vp.size = Vector2i(_w, _h)
	_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(_vp)
	await _frames(4)
	state.career_seed = 2050
	state.replay_seed = 2050
	state.start_season("HAW", db.club_list("HAW"))
	state.prepare_interactive_match()
	var scene = load("res://scenes/MatchScene.tscn").instantiate()
	_vp.add_child(scene)
	await _frames(24)
	var play: Node = scene.find_child("PlayMatch", true, false)
	if play == null:
		for b in scene.find_children("*", "Button", true, false):
			if (b as Button).text.to_lower().begins_with("play") or (b as Button).text.to_lower().begins_with("start"):
				play = b
				break
	if play != null:
		print("pressing ", play.name, " '", (play as Button).text, "'")
		(play as Button).emit_signal("pressed")
	await _frames(6)
	var start := scene.find_child("StartQuarter", true, false) as Button
	if start != null:
		start.emit_signal("pressed")
	await _frames(6)
	# Play on fast, the real playback path, each call taking its default, until
	# well into the second quarter (or `frames` frames).
	var pitch = scene.get("_pitch")
	var sim = state.pending_sim
	pitch.set_speed(8.0)
	for i in range(frames):
		var box: Node = scene.find_child("CoachBox", true, false)
		if box != null and OS.get_cmdline_user_args().has("--stop-at-break") and i > 10:
			break
		if box != null:
			var go := box.find_child("StartQuarter", true, false) as Button
			if go != null:
				go.emit_signal("pressed")
		if not sim.pending_moment.is_empty():
			scene.call("_on_moment_choice", int(sim.pending_moment.get("default", 0)))
		if pitch.playing:
			pitch._process(0.25)
		await process_frame
	await _frames(6)
	_measure(scene)
	var img := _vp.get_texture().get_image()
	img.save_png(out + ".png")
	print("wrote ", out, ".png")
	quit()


func _measure(scene: Node) -> void:
	var col: Node = scene.find_child("MatchColumn", true, false)
	print("canvas ", _vp.size, " column ", (col as Control).size if col else "none")
	for n in ["SetupLine", "FeedWaiting", "LiveStats", "MatchControls"]:
		var c := scene.find_child(n, true, false) as Control
		if c != null:
			print(n, " visible ", c.is_visible_in_tree(), " pos ", c.position, " size ", c.size, " needs ", c.get_combined_minimum_size())
	var over = scene.get("_over")
	if over != null:
		for c in over.get_children():
			if c is Control:
				print("over child ", c.name, " ", c.get_class(), " vis ", (c as Control).visible, " filter ", (c as Control).mouse_filter, " rect ", (c as Control).get_global_rect(), " kids ", c.get_child_count())
	var cb = scene.get("_controls_box")
	if cb != null:
		print("controls alpha ", (cb as Control).modulate.a)
	var feed := scene.find_child("Feed", true, false) as Control
	if feed != null:
		var sc := feed.get_parent() as Control
		print("FeedScroll size ", sc.size, " feed holds ", feed.get_combined_minimum_size(), " lines ", feed.get_child_count())
		var sv := sc.get_parent() as Control
		print("panel box ", sv.size, " needs ", sv.get_combined_minimum_size())
		for c in sv.get_children():
			print("  child ", c.name, " ", (c as Control).size, " vis ", (c as Control).visible)
