extends SceneTree
## The press interview before the draft on a fresh new career (onboarding on),
## as a coach meets it: the League redraft, take the club, the interview opens.
##   godot --path . --script tools/visual/capture_onboarding_interview.gd -- --out DIR [--size 390x844] [--club MEL]
## Writes DIR/<W>x<H>_<screen>.png: walkin (the coach walking in, a moment after
## the screen opens), name, question, reveal. The interview has no Tutorials tip of
## its own (FirstVisitIntro.TEXT has no "interview" key), so none is shot. Prints
## per page whether the press room drew from the figure sheet, its size and the
## coach's on-screen scale per sheet pixel (SCENE lines).
## Needs a real renderer: run windowed, never --headless.

var W := 390
var H := 844
var out := "/tmp/onboarding_interview"
var state


func _initialize() -> void:
	_run.call_deferred()
	create_timer(180.0).timeout.connect(func():
		print("CAPTURE watchdog: timed out")
		quit(2))


func _arg(name: String, fallback: String) -> String:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == name:
			return str(a[i + 1])
	return fallback


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(name: String) -> void:
	await _frames(30)
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


func _report(iv: Node) -> void:
	var SV = load("res://scripts/ui/match/StoppageVignette.gd")
	var VF = load("res://scripts/ui/match/VignetteFigures.gd")
	var stage: Control = iv.find_child("InterviewStage", true, false)
	var v: Node = iv.find_child("MediaConferenceVignette", true, false)
	print("SCENE stage=", stage != null, " size=", stage.size if stage != null else Vector2.ZERO,
			" vignette=", v != null, " sheet=", SV.FIGURE_SHADE.resource_path if v != null else "",
			" sheet_size=", SV.FIGURE_SHADE.get_size() if v != null else Vector2.ZERO,
			" expected=", VF.SHEET_SIZE,
			" figure_scale=", snappedf(v.figure_scale(), 0.001) if v != null and v.has_method("figure_scale") else -1.0)


func _run() -> void:
	out = _arg("--out", out)
	var club := _arg("--club", "MEL")
	var wh := _arg("--size", "390x844").split("x")
	W = int(wh[0])
	H = int(wh[1])
	DirAccess.make_dir_recursive_absolute(out)
	await process_frame
	state = root.get_node("GameState")
	state.autosave_enabled = false
	state.save_path = "user://capture_onboarding_interview.save"
	state.settings_path = "user://capture_onboarding_interview.cfg"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(state.settings_path))
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	await _frames(10)
	var layout = root.get_node("ScreenLayout")
	var base: float = layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0)
	layout.ui_scale = 1.0 / maxf(1.0, base)
	layout._update_scale()

	# A fresh device, New career with Tutorials on (Main._start_new_career).
	state.set_new_career_tutorials(true)
	state.replay_seed = 2031
	state.reset()
	state.begin_draft()
	state.interview_due = true
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _frames(6)
	for b in ui.find_children("*IntroOk", "Button", true, false):
		b.pressed.emit()
	await _frames(4)
	ui.call("_on_club_chosen", club)
	await _frames(10)
	var iv: Node = current_scene
	for i in range(180):
		if iv != null and str(iv.scene_file_path).ends_with("InterviewScene.tscn"):
			break
		await process_frame
		iv = current_scene
	if iv == null:
		for n in root.get_children():
			if str(n.scene_file_path).ends_with("InterviewScene.tscn"):
				iv = n
	print("CAPTURE at ", root.get_node("Router").current(), " scene ", iv.scene_file_path if iv != null else "none")
	if iv == null or not str(iv.scene_file_path).ends_with("InterviewScene.tscn"):
		quit(1)
		return
	print("CAPTURE tips open: ", iv.find_children("*Intro", "", true, false).size())
	await _shot("walkin")
	# The coach seated before the name page's shot.
	await create_timer(1.5).timeout
	_report(iv)
	await _shot("name")
	var f: LineEdit = iv.find_child("CoachName", true, false)
	if f != null:
		f.text = "Pat Reid"
		f.text_changed.emit(f.text)
		await _press(iv, "InterviewStart")
	# The coach is seated and the room settled.
	await create_timer(2.5).timeout
	_report(iv)
	await _shot("question")
	for a in [1, 0, 2, 1, 3, 0, 1]:
		await _press(iv, "InterviewAnswer%d" % a)
	await _frames(4)
	_report(iv)
	await _shot("reveal")
	quit(0)
