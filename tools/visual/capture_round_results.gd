extends SceneTree
## Visual review tool for the hub's round Results sheet (director, 2026-11-07: "The
## scores here are really hard to read and know which game they belong to. And the
## bottom row is faded by the UI effect."). Windowed:
##   godot --windowed --path . --script tools/visual/capture_round_results.gd -- --out <prefix> --size 390x844
## A full round of nine games listed (your match among them, as after a simmed week)
## with one game forced to a draw. Writes <out>_top.png (sheet open, at the top) and
## <out>_bottom.png (the list scrolled to its end). Never touches a real save.

var _w := 390
var _h := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	var out := "round_results"
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
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	var feel = load("res://scripts/ui/Feel.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_round_results.save"
	state.settings_path = "user://capture_round_results.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.show_real_names = false
	UK.apply_appearance("dark")
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	feel.force_phone = true
	state.reset()
	state.replay_seed = 2027
	state.start_season("COL", db.club_list("COL"))
	state.advance()
	# One game that is not yours ends level.
	var rest: Array = []
	var drew := false
	for r in state.last_results:
		var res: Dictionary = r
		if not drew and not state.is_my_match(res):
			res["goals"] = [11, 12]
			res["behinds"] = [9, 3]
			res["score"] = [75, 75]
			drew = true
		rest.append(res)
	state.last_results = rest
	# After a simmed week your match sits in the list with the rest (the director's case).
	state.last_match = {}
	state.last_injuries = []
	state.last_mro = []
	var hub = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(10)
	await create_timer(0.5).timeout
	hub.call("_show_results", state.last_results)
	await create_timer(1.5).timeout
	await _save("%s_top.png" % out)
	var sheet: Node = hub.find_child("RoundResults", true, false)
	var sc: ScrollContainer = null
	for n in sheet.find_children("*", "ScrollContainer", true, false):
		sc = n
		break
	if sc != null:
		var bar := sc.get_v_scroll_bar()
		sc.scroll_vertical = int(bar.max_value)
	await create_timer(0.6).timeout
	await _save("%s_bottom.png" % out)
	var fade := sheet.find_child("BarFade", true, false) as CanvasItem
	if fade != null:
		print("fade alpha at the end: ", fade.modulate.a)
	quit(0)


func _save(path: String) -> void:
	await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
