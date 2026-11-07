extends SceneTree
## Proof tool for the loading cover (ScreenTransition.run). Windowed, through
## the GPU slot:
##   bash C:/kt/gpu_slot.sh godot --windowed --path . --script tools/visual/capture_loading_cover.gd -- --out <dir> [--size 390x844] [--reduced]
## Opens a Fremantle career on the hub, taps Sim the week the way a finger
## does (a touch event at its place on screen), and saves every drawn frame from the tap until the
## screen is back: <dir>/f_000.png on. Prints one line per frame (ms since the
## tap, the gap since the frame before, whether the cover line was up, the
## round) and a summary: the longest gap between drawn frames (the stall) and
## whether the frame on screen during it showed the line. Works on a build
## without the cover too (it reports no line), for a before and after.
## Never touches a real save.


var _w := 390
var _h := 844


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "loading_cover"
	var reduced := false
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
			"--reduced":
				reduced = true
	DirAccess.make_dir_recursive_absolute(out)
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	var wipe = root.get_node("ScreenTransition")
	state.autosave_enabled = false
	state.save_path = "user://capture_loading_cover.save"
	state.settings_path = "user://capture_loading_cover.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.show_real_names = false
	state.set_confirm_sim_round(false)
	load("res://scripts/ui/Feel.gd").reduced = reduced
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	state.reset()
	state.replay_seed = 2027
	state.start_season("FRE", db.club_list("FRE"))
	state.tutorials = false
	router.stack = []
	router.go("hub")
	while bool(wipe.get("busy")):
		await process_frame
	await create_timer(1.5).timeout
	var sim: Control = current_scene.find_child("SimRound", true, false)
	if sim == null:
		print("no Sim the week button")
		quit(1)
		return
	var line: Label = wipe.get_node_or_null("CoverLine")
	var start_round: int = state.season.round_index
	var t0 := Time.get_ticks_msec()
	var frames: Array = []
	var on_draw := func():
		frames.append({"ms": Time.get_ticks_msec() - t0,
				"line": line != null and line.visible and bool(wipe.get("busy")),
				"text": line.text if line != null else "",
				"round": int(state.season.round_index)})
		root.get_texture().get_image().save_png("%s/f_%03d.png" % [out, frames.size() - 1])
	RenderingServer.frame_post_draw.connect(on_draw)
	_tap_and_report(sim)
	# Until the week is simmed and the screen is back (or 20 s).
	while Time.get_ticks_msec() - t0 < 20000:
		await process_frame
		if int(state.season.round_index) != start_round and not bool(wipe.get("busy")) and frames.size() > 4:
			break
	for i in range(10):
		await process_frame
	RenderingServer.frame_post_draw.disconnect(on_draw)
	var worst := 0
	var worst_at := 0
	for i in range(frames.size()):
		var gap: int = int(frames[i]["ms"]) - (int(frames[i - 1]["ms"]) if i > 0 else 0)
		print("FRAME %03d ms=%d gap=%d line=%s round=%d %s" % [i, int(frames[i]["ms"]), gap,
				str(frames[i]["line"]), int(frames[i]["round"]), str(frames[i]["text"]) if frames[i]["line"] else ""])
		if gap > worst:
			worst = gap
			worst_at = i
	# The frame on screen during the stall is the one drawn just before it.
	var shown: Dictionary = frames[maxi(worst_at - 1, 0)] if not frames.is_empty() else {}
	var first_line := -1
	for i in range(frames.size()):
		if frames[i]["line"]:
			first_line = i
			break
	print("SUMMARY stall_ms=%d frame_on_screen_during_stall=%d line_on_it=%s first_line_frame=%d ms_to_line=%d round %d->%d" % [
			worst, maxi(worst_at - 1, 0), str(shown.get("line", false)), first_line,
			int(frames[first_line]["ms"]) if first_line >= 0 else -1, start_round, int(state.season.round_index)])
	quit(0)


## A finger's tap on c, as tests/tap.gd delivers it, but placed in window
## pixels: on a PC with display scaling the UI is stretched, and Tap's spot is
## in UI units. Prints whether c got it.
func _tap_and_report(c: Control) -> void:
	var at: Vector2 = root.get_final_transform() * (c.get_screen_transform() * (c.size * 0.5))
	var hit := [false]
	var on_press := func(): hit[0] = true
	(c as BaseButton).pressed.connect(on_press)
	for down in [true, false]:
		var touch := InputEventScreenTouch.new()
		touch.index = 0
		touch.position = at
		touch.pressed = down
		Input.parse_input_event(touch)
		Input.flush_buffered_events()
		await process_frame
		await process_frame
	if is_instance_valid(c):
		(c as BaseButton).pressed.disconnect(on_press)
	print("TAP at %s pixels: %s" % [str(at), "pressed SimRound" if hit[0] else "missed, went to %s" % str(c.get_viewport().gui_get_hovered_control())])
