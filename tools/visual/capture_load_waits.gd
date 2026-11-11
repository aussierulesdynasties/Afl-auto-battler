extends SceneTree
## Proof tool for the load screens (the set shot on the cover). Windowed, through
## the GPU slot:
##   bash C:/kt/gpu_slot.sh godot --windowed --path . --script tools/visual/capture_load_waits.gd -- --out <dir> [--size 390x844] [--flows load,sim,list,skip] [--web] [--no-png]
## Three real waits, each started by a finger's tap at the control's place:
## Continue on the title (loading a career), Sim the week on the hub, and My list
## on the hub (a slow screen). For each it saves every drawn frame from the tap
## until the screen is back (<dir>/<flow>/f_000.png on) and prints one line per
## frame: ms since the tap, the gap since the frame before, how far the dots
## cover, whether the line and the set shot are up, the ball's tick count and
## the screen. Then a summary per flow: frames with full cover but no set shot
## (the grey screen), the longest gap between frames while the set shot was up,
## and the share of the wait the set shot was on screen. Never touches a real save.

var _w := 390
var _h := 844
var _png := true
var _wipe: Node
var _state: Node


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "load_waits"
	var flows := ["load", "sim", "list", "skip"]
	var web := false
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
			"--flows":
				flows = Array(str(a[i + 1]).split(","))
			"--no-png":
				_png = false
			"--web":
				web = true
	await process_frame
	_state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	_wipe = root.get_node("ScreenTransition")
	# --web: the flair and the screen loads behave as in a browser build (the
	# ball at rest, scenes loaded under the line); read with SUMMARY-BROWSER.
	if web:
		(_wipe.call("flair") as Node).set("web_still", true)
		router.set("test_main_thread_load", true)
	_state.autosave_enabled = true
	_state.event_sheets = false
	_state.save_path = "user://capture_load_waits.save"
	_state.settings_path = "user://capture_load_waits.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	_state.show_real_names = false
	_state.set_confirm_sim_round(false)
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	_state.reset()
	_state.replay_seed = 2027
	_state.start_season("FRE", db.club_list("FRE"))
	_state.tutorials = false
	_state.save_career()
	if "load" in flows:
		# The title with a career on disk and none in memory: Continue loads it.
		_state.reset()
		router.stack = []
		router.go("main")
		await _settle()
		var cont := current_scene.find_child("ContinueCareer", true, false) as Control
		if cont == null:
			print("no Continue button")
		else:
			await _trace("load", cont, out, func(): return current_scene != null and current_scene.name != "Main")
	else:
		router.stack = []
		router.go("hub")
	await _settle()
	if "sim" in flows:
		var sim := current_scene.find_child("SimRound", true, false) as Control
		var r0: int = int(_state.season.round_index)
		await _trace("sim", sim, out, func(): return int(_state.season.round_index) != r0)
		# The results popup: close it so the hub is clear for the next tap.
		await _settle()
		var done := _find_text(current_scene, ["Continue", "Done", "Close"])
		if done != null:
			(done as BaseButton).pressed.emit()
		await _settle()
	if "list" in flows:
		var lst := _find_text(current_scene, ["My list"])
		await _trace("list", lst, out, func(): return current_scene != null and current_scene.scene_file_path.ends_with("ListScene.tscn"))
	if "skip" in flows:
		# Skip the rest of the home and away: the survey opens on the club's
		# answers; Next through it, then the traced tap is the sheet's own Skip.
		if not current_scene.scene_file_path.ends_with("HubScene.tscn"):
			router.stack = []
			router.go("hub")
			await _settle()
		# The skip is a long press of the week's button (HoldPress): open what it opens.
		var open: BaseButton = null
		for n in current_scene.find_children("*", "Button", true, false):
			if n.get_meta("bulk_skip", "") == "home_away":
				open = n as BaseButton
		if open == null:
			print("skip: no long press for the home and away")
		else:
			current_scene.call("_open_skip_confirm", "home_away")
			await _settle()
			for i in range(8):
				var nxt := current_scene.find_child("SkipNext", true, false) as BaseButton
				if nxt == null:
					break
				nxt.pressed.emit()
				await process_frame
				await process_frame
			var go := current_scene.find_child("SkipSeasonGo", true, false) as Control
			await _trace("skip", go, out, func(): return _state.season.is_regular_done())
	quit(0)


func _settle() -> void:
	while bool(_wipe.get("busy")):
		await process_frame
	await create_timer(1.0).timeout


func _find_text(n: Node, texts: Array) -> Control:
	if n is BaseButton and (n as Control).is_visible_in_tree() and n.get("text") in texts:
		return n
	for c in n.get_children():
		var f := _find_text(c, texts)
		if f != null:
			return f
	return null


func _trace(flow: String, c: Control, out: String, arrived: Callable) -> void:
	if c == null:
		print("%s: no control to tap" % flow)
		return
	var dir := "%s/%s" % [out, flow]
	DirAccess.make_dir_recursive_absolute(dir)
	var flair: Control = _wipe.call("flair")
	var rect: Control = _wipe.get_node("TransitionRect")
	var mat: ShaderMaterial = rect.material
	var line: Label = _wipe.get_node("CoverLine")
	var t0 := Time.get_ticks_msec()
	var frames: Array = []
	# A browser shows a frame only once the script of the frame that drew it has
	# returned: the next process frame marks this frame as handed over.
	var on_process := func():
		if not frames.is_empty():
			frames[frames.size() - 1]["shown"] = true
	process_frame.connect(on_process)
	var on_draw := func():
		var f := {"ms": Time.get_ticks_msec() - t0,
				"cover": float(mat.get_shader_parameter("factor")) if rect.visible else 0.0,
				"line": line.visible,
				"flair": flair.visible,
				"ticks": int(flair.get("ticks")),
				"ball": flair.get("ball_at"),
				"scene": str(current_scene.name) if current_scene != null else "-",
				"shown": false}
		frames.append(f)
		if _png:
			root.get_texture().get_image().save_png("%s/f_%03d.png" % [dir, frames.size() - 1])
	RenderingServer.frame_post_draw.connect(on_draw)
	await _tap(c)
	while Time.get_ticks_msec() - t0 < 300000:
		await process_frame
		if bool(arrived.call()) and not bool(_wipe.get("busy")) and frames.size() > 4:
			break
	for i in range(6):
		await process_frame
	RenderingServer.frame_post_draw.disconnect(on_draw)
	process_frame.disconnect(on_process)
	var grey := 0
	var grey_ms := 0
	var flair_ms := 0
	var worst_flair_gap := 0
	var covered_ms := 0
	for i in range(frames.size()):
		var f: Dictionary = frames[i]
		var next_ms: int = int(frames[i + 1]["ms"]) if i + 1 < frames.size() else int(f["ms"])
		var on_screen: int = next_ms - int(f["ms"])
		var gap: int = int(f["ms"]) - (int(frames[i - 1]["ms"]) if i > 0 else 0)
		print("%s FRAME %03d ms=%d gap=%d shown=%s cover=%.2f line=%s flair=%s ticks=%d ball=%s %s" % [flow, i,
				int(f["ms"]), gap, "Y" if f["shown"] else "n", float(f["cover"]), str(f["line"]), str(f["flair"]), int(f["ticks"]),
				str(f["ball"]), str(f["scene"])])
		if float(f["cover"]) >= 0.999:
			covered_ms += on_screen
			if not f["flair"]:
				grey += 1
				grey_ms += on_screen
			else:
				flair_ms += on_screen
				worst_flair_gap = maxi(worst_flair_gap, on_screen)
	# The browser's view: each handed-over frame stays up until the next one.
	var web_grey_ms := 0
	var web_shot_ms := 0
	var web_worst := 0
	var shown := []
	for f in frames:
		if f["shown"]:
			shown.append(f)
	for i in range(shown.size()):
		var f: Dictionary = shown[i]
		var up: int = (int(shown[i + 1]["ms"]) if i + 1 < shown.size() else int(f["ms"])) - int(f["ms"])
		if float(f["cover"]) >= 0.999:
			if f["flair"]:
				web_shot_ms += up
				web_worst = maxi(web_worst, up)
			else:
				web_grey_ms += up
	print("SUMMARY-BROWSER %s handed_over=%d grey_ms=%d set_shot_ms=%d longest_still_ms=%d" % [
			flow, shown.size(), web_grey_ms, web_shot_ms, web_worst])
	print("SUMMARY %s frames=%d full_cover_ms=%d grey_frames=%d grey_ms=%d set_shot_ms=%d longest_set_shot_frame_ms=%d" % [
			flow, frames.size(), covered_ms, grey, grey_ms, flair_ms, worst_flair_gap])


## A finger's tap on c, placed in window pixels (as capture_loading_cover.gd).
func _tap(c: Control) -> void:
	var at: Vector2 = root.get_final_transform() * (c.get_screen_transform() * (c.size * 0.5))
	for down in [true, false]:
		var touch := InputEventScreenTouch.new()
		touch.index = 0
		touch.position = at
		touch.pressed = down
		Input.parse_input_event(touch)
		Input.flush_buffered_events()
		await process_frame
