extends SceneTree
## How a career starts (row 141), for the director's look:
##   godot --path . --script tools/visual/capture_interview_starts.gd -- --out DIR [--size 390x844]
## Writes DIR/<W>x<H>_<screen>.png: warning (Yes to Canberra on the real
## lists), canberra_name and canberra_question (the interview after the 2030
## start), rebuild_name and rebuild_reveal (the interview on a Rebuild).
## Needs a real renderer: run windowed (override.cfg), never --headless.

var W := 390
var H := 844
var out := "/tmp/interview_starts"
var state
var db


func _initialize() -> void:
	_run.call_deferred()
	# A script error inside the run stops it without quit(): never sit idle on a slot.
	create_timer(180.0).timeout.connect(func():
		print("CAPTURE watchdog: timed out")
		quit(2))


func _arg(name: String, fallback: String) -> String:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == name:
			return str(a[i + 1])
	return fallback


func _shot(name: String) -> void:
	for i in range(30):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	var path := "%s/%dx%d_%s.png" % [out, W, H, name]
	img.save_png(path)
	print("wrote ", path)


func _press(scene: Node, node_name: String) -> void:
	var b: Button = scene.find_child(node_name, true, false)
	if b == null:
		print("CAPTURE missing button ", node_name)
		return
	b.pressed.emit()
	await process_frame


func _fresh(seed: int) -> void:
	state.reset()
	state.career_seed = 2027
	state.replay_seed = seed
	state.tutorials = false
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)


## The interview as the hub opens it, on the name page.
func _interview() -> Control:
	var iv: Control = load("res://scenes/InterviewScene.tscn").instantiate()
	root.add_child(iv)
	for i in range(6):
		await process_frame
	return iv


func _name_and_start(iv: Control) -> void:
	var f: LineEdit = iv.find_child("CoachName", true, false)
	f.text = "Pat Reid"
	f.text_changed.emit(f.text)
	await _press(iv, "InterviewStart")


func _run() -> void:
	out = _arg("--out", out)
	var wh := _arg("--size", "390x844").split("x")
	W = int(wh[0])
	H = int(wh[1])
	DirAccess.make_dir_recursive_absolute(out)
	await process_frame
	state = root.get_node("GameState")
	db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_interview.save"
	state.settings_path = "user://capture_interview.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	for i in range(10):
		await process_frame
	var layout = root.get_node("ScreenLayout")
	var base: float = layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0)
	layout.ui_scale = 1.0 / maxf(1.0, base)
	layout._update_scale()

	print("CAPTURE stage 1")
	# 1. New career: Real 2026 lists, then Yes to Canberra.
	_fresh(2027)
	var menu: Control = load("res://scenes/Main.tscn").instantiate()
	root.add_child(menu)
	for i in range(10):
		await process_frame
	menu.call("_on_new_career")
	menu.call("_on_pick_year", "2026")  # past the year step (row 142 L2)
	await process_frame
	await _press(menu, "StartMode_real")
	await _press(menu, "Canberra_yes")
	print("CAPTURE warning shown: ", menu.find_child("SimAheadWarning", true, false) != null)
	await _shot("warning")
	menu.queue_free()
	await process_frame

	print("CAPTURE stage 2")
	# 2. The 2030 start from its shipped history, Canberra taken: the interview.
	_fresh(0)
	state.set_canberra(true)
	state.interview_due = true
	if not state.begin_from_history(state.SIM_AHEAD_TO):
		print("CAPTURE no 2030 history")
		quit(1)
		return
	print("CAPTURE took CANB: ", state.choose_sim_ahead_club("CANB"), " due ", state.interview_due,
			" coach '", state.coach_name, "'")
	var iv := await _interview()
	await _shot("canberra_name")
	await _name_and_start(iv)
	await _shot("canberra_question")
	iv.queue_free()
	await process_frame

	print("CAPTURE stage 3")
	# 3. Rebuild: the bottom club's interview, name page and the reveal.
	_fresh(2027)
	state.interview_due = true
	state.challenge = {"kind": "rebuild"}
	state.begin_real_lists()
	if state.my_club == "":
		state.choose_real_club(str(state.challenge.get("club", "")))
	print("CAPTURE rebuild club ", state.my_club, " due ", state.interview_due)
	iv = await _interview()
	await _shot("rebuild_name")
	await _name_and_start(iv)
	for a in [1, 0, 2, 1, 3, 0, 1]:
		await _press(iv, "InterviewAnswer%d" % a)
	await _shot("rebuild_reveal")
	quit(0)
