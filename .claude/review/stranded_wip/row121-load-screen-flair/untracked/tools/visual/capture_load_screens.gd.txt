extends SceneTree
## Proof tool for the load screens (row 121). Windowed, through the GPU slot:
##   bash C:/kt/gpu_slot.sh godot --windowed --path . --script tools/visual/capture_load_screens.gd -- --out <dir> [--size 390x844] [--no-pump] [--shots] [--reduced] [--strip] [--only a,b] [--club FRE] [--icon]
## Plays every wait in the game on seeded careers, the way the game starts each
## one, and prints one line per wait: how long the cover's line was up, how many
## frames reached the screen, the longest gap between them (a freeze) and the
## frames drawn by hand. --no-pump is the same with the hand-drawn frames off, for
## a before and after. --shots saves one frame of each wait with the ball in the
## air (<dir>/<wait>.png; saving costs time, so a timing run leaves it off).
## --strip saves the ball every 100 ms of its own clock across three kicks
## (<dir>/strip_NNN.png), so the frames are exact whatever the machine is doing.
## --icon shows the Signwriter icon in the logo's place, for comparing the two.
## Never touches a real save.

const MID_AIR_MS := 650

var _w := 390
var _h := 844
var _out := "load_screens"
var _club := "FRE"
var _shots := false
var _icon := false
var _only := []
var _state
var _db
var _router
var _wipe
var _flow := ""
var _times: Array = []
var _shot_done := false
var _last_text := ""


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	var no_pump := false
	var reduced := false
	var strip := false
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				_out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
			"--no-pump":
				no_pump = true
			"--shots":
				_shots = true
			"--reduced":
				reduced = true
			"--strip":
				strip = true
			"--icon":
				_icon = true
			"--club":
				_club = str(a[i + 1])
			"--only":
				_only = Array(str(a[i + 1]).split(","))
	DirAccess.make_dir_recursive_absolute(_out)
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_router = root.get_node("Router")
	_wipe = root.get_node("ScreenTransition")
	_wipe.set("pump_on", not no_pump)
	var flair: Control = _wipe.call("flair")
	if _shots:
		flair.set("start_offset_ms", MID_AIR_MS)
	if _icon:
		flair.call("show_icon_for_compare")
	_state.autosave_enabled = false
	_state.save_path = "user://capture_load_screens.save"
	_state.settings_path = "user://capture_load_screens.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	_state.show_real_names = false
	_state.set_confirm_sim_round(false)
	load("res://scripts/ui/Feel.gd").reduced = reduced
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	if strip:
		await _strip()
		_quit()
		return
	RenderingServer.frame_post_draw.connect(_on_draw)
	await _career()
	print("DONE")
	_quit()


func _quit() -> void:
	_router.stack = []
	quit(0)


func _fresh() -> void:
	_state.reset()
	_state.replay_seed = 2027
	_state.start_season(_club, _db.club_list(_club))
	_state.tutorials = false


func _career() -> void:
	# Continue: a real save, read back the way the menu does it.
	_fresh()
	_state.save_career() if _state.has_method("save_career") else _state.autosave()
	_router.stack = []
	_router.go("main")
	await _settled()
	await _wait("continue", func(): current_scene.call("_on_continue"))
	await _go_hub()
	await _wait("sim_week", func(): current_scene.call("_on_sim_round"))
	await _go_hub()
	await _wait("list", func(): _router.go("list"))
	await _wait("selection", func(): _router.go("selection"))
	await _wait("preseason", func(): _router.go("preseason"))
	# The match load, as MatchKickoff has it with Skip chosen.
	await _go_hub()
	await _wait("match", func():
		_wipe.call("run", "Heading to the ground...", func():
			if _state.prepare_interactive_match():
				_state.match_way_live = "skip"
				_router.go("match")))
	# Skipping the season, then its ends.
	_fresh()
	await _go_hub()
	await _wait("skip_season", func(): current_scene.call("_on_skip_season"))
	await _go_hub()
	while not _state.season.is_season_over():
		_state.advance()
	await _wait("season_review", func(): _router.go("season_review"))
	await _wait("offseason", func(): _router.go("offseason"))
	await _go_hub()
	await _wait("new_season", func():
		_router.go("season_review")
		await _settled()
		current_scene.call("_start_intake_draft"))
	# A new career, as the title screen starts one: draft night...
	_state.reset()
	_state.replay_seed = 2027
	_router.stack = []
	_router.go("main")
	await _settled()
	await _wait("draft", func(): current_scene.call("_on_new_career"))
	# ... the pre-made years without you (a seed of 0 is what a player has) ...
	_state.reset()
	_state.replay_seed = 0
	_state.begin_real_lists()
	_router.stack = []
	_router.go("main")
	await _settled()
	await _wait("years_without_you", func(): current_scene.call("_play_years_without_you"))
	# ... and the same years played for real, for a career with no pre-made
	# history to load (a seed set here stands in for that).
	_state.reset()
	_state.replay_seed = 2027
	_state.begin_real_lists()
	_router.stack = []
	_router.go("main")
	await _settled()
	await _wait("years_played_out", func(): current_scene.call("_play_years_without_you"))


func _go_hub() -> void:
	_router.stack = []
	_router.go("hub")
	await _settled()


func _settled() -> void:
	await process_frame
	await process_frame
	var t0 := Time.get_ticks_msec()
	while bool(_wipe.get("busy")) and Time.get_ticks_msec() - t0 < 180000:
		await process_frame
	await create_timer(0.4).timeout


## Start one wait, measure it from the first frame with the line on the cover to
## the cover leaving, and print its line.
func _wait(flow: String, start: Callable) -> void:
	if not _only.is_empty() and not _only.has(flow):
		# The state still has to move on for the waits after it.
		await start.call()
		await _settled()
		return
	_flow = flow
	_times = []
	_shot_done = not _shots
	_last_text = ""
	var pumped0: int = int(_wipe.get("pumped_frames"))
	var pumped_us0: int = int(_wipe.get("pumped_us"))
	var t0 := Time.get_ticks_msec()
	await start.call()
	await process_frame
	while bool(_wipe.get("busy")) and Time.get_ticks_msec() - t0 < 400000:
		await process_frame
	_flow = ""
	var gap := 0
	for i in range(1, _times.size()):
		gap = maxi(gap, int(_times[i]) - int(_times[i - 1]))
	var up: int = int(_times[-1]) - int(_times[0]) if _times.size() > 1 else 0
	var hand: int = int(_wipe.get("pumped_frames")) - pumped0
	print("WAIT %-18s total_ms=%d line_up_ms=%d frames=%d longest_freeze_ms=%d hand_frames=%d hand_ms=%d text=%s" % [
			flow, Time.get_ticks_msec() - t0, up, _times.size(), gap, hand,
			(int(_wipe.get("pumped_us")) - pumped_us0) / 1000, _last_text])
	await create_timer(0.4).timeout


func _on_draw() -> void:
	if _flow == "" or not bool(_wipe.call("line_visible")):
		return
	_times.append(Time.get_ticks_msec())
	var line: Label = _wipe.get_node("CoverLine")
	_last_text = line.text
	if not _shot_done:
		_shot_done = true
		root.get_texture().get_image().save_png("%s/%s.png" % [_out, _flow])


## A frame every 100 ms across three kicks, on a named line, for the eye.
func _strip() -> void:
	_fresh()
	_router.stack = []
	_router.go("hub")
	await _settled()
	var held := [true]
	_wipe.call("cover", func():
		while held[0]:
			await process_frame, "Playing Round 7...")
	await create_timer(0.4).timeout
	var flair: Control = _wipe.call("flair")
	var n := 0
	while n < 54:
		flair.set("hand_clock_ms", n * 100)
		flair.call("tick")
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("%s/strip_%03d.png" % [_out, n])
		n += 1
	flair.set("hand_clock_ms", -1)
	held[0] = false
	await _settled()
	print("STRIP frames=%d" % n)
