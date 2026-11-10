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
	root.size = Vector2i(W, H)
	root.gui_disable_input = true
	DisplayServer.window_set_size(Vector2i(W, H))

	print("CAPTURE stage 1")
	# 1. New career: Real 2026 lists, then Yes to Canberra.
	_fresh(2027)
	root.get_node("Router").to_main_menu(false)
	for i in range(60):
		await process_frame
		if current_scene != null and current_scene.has_method("_on_new_career"):
			break
	current_scene._on_new_career()
	await process_frame
	await _press(current_scene, "StartMode_real")
	await _press(current_scene, "Canberra_yes")
	print("CAPTURE warning shown: ", current_scene.find_child("SimAheadWarning", true, false) != null)
	await _shot("warning")
	current_scene.queue_free()
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
