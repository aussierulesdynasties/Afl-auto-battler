extends SceneTree
## Match day's scoreboard clock, the controls under a sheet and the Stats tab, through the real flow:
## the opening break, Start, Skip to quarter time, Skip to full time, then the Stats tab.
## Needs a real renderer (a window, never fullscreen). User arguments:
##   --out /tmp/md --size 390x844
##   --out /tmp/md --size 1920x1080 --logical 1280x720   (a PC: ScreenLayout gives that window a 1280x720 canvas)
## Writes <out>_1_pre_match.png, _2_quarter_time.png, _3_break_stats.png, _4_half_time.png,
## _5_three_quarter_time.png, _6_full_time.png and _7_full_time_stats.png, and prints the clock's
## words at each. Seeded; never touches a real save.

var _w := 390
var _h := 844
var _lw := 0
var _lh := 0
var _vp: SubViewport
var _out := "md"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out": _out = str(a[i + 1])
			"--club": club = str(a[i + 1])
			"--logical":
				var lwh := str(a[i + 1]).split("x")
				_lw = int(lwh[0])
				_lh = int(lwh[1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_match_day_states.save"
	state.settings_path = "user://capture_match_day_states.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	_vp = SubViewport.new()
	_vp.size = Vector2i(_w, _h)
	_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	if _lw > 0:
		_vp.size_2d_override = Vector2i(_lw, _lh)
		_vp.size_2d_override_stretch = true
	root.add_child(_vp)
	await _frames(4)
	# An opponent whose colours show against the page (never black and white).
	var tries := 0
	while true:
		state.reset()
		state.career_seed = 2026 + tries
		state.replay_seed = 2026 + tries
		state.set_setting("seen_training_intro", true)
		state.start_season(club, db.club_list(club))
		state.prepare_interactive_match()
		var s0 = state.pending_sim
		var them := str(s0.squads[1].code) if str(s0.squads[0].code) == club else str(s0.squads[0].code)
		if ["MEL", "WBD", "STK"].has(them) or tries > 120:
			print("MATCH ", club, " v ", them, " seed ", 2026 + tries)
			break
		tries += 1
	var scene = load("res://scenes/MatchScene.tscn").instantiate()
	_vp.add_child(scene)
	await _frames(24)
	_shot(scene, "1_pre_match")
	var go: Button = scene.find_child("StartQuarter", true, false)
	go.emit_signal("pressed")
	await _frames(20)
	await scene.call("_on_skip_to_break")
	await _frames(24)
	_shot(scene, "2_quarter_time")
	scene.call("_show_break_stats")
	await _frames(16)
	_shot(scene, "3_break_stats")
	scene.call("handle_back")
	await _frames(8)
	for name in ["4_half_time", "5_three_quarter_time"]:
		(scene.find_child("StartQuarter", true, false) as Button).emit_signal("pressed")
		await _frames(20)
		await scene.call("_on_skip_to_break")
		await _frames(24)
		_shot(scene, name)
	scene.call("_on_skip")
	await _frames(40)
	_shot(scene, "6_full_time")
	scene.set("_ft_tab", "stats")
	scene.call("_render_ft")
	await _frames(16)
	_shot(scene, "7_full_time_stats")
	quit()


func _shot(scene: Node, name: String) -> void:
	var clock: Label = scene.find_child("Clock", true, false)
	print("CLOCK ", name, " '", clock.text if clock != null else "none", "'")
	var img := _vp.get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	var path := "%s_%s.png" % [_out, name]
	img.save_png(path)
	print("wrote ", path)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame
