extends SceneTree
## Visual review tool for the off-season Club budget tab (row 99: three lines,
## High performance carrying the game plan's edge), on a phone (390x844):
##   godot --path . --script tools/visual/capture_budget.gd -- --out /tmp/budget
## Writes <out>_sheet.png, four frames: the fresh Standard allocation (top and
## scrolled to High performance), then Recruiting cut to Minimal and High
## performance raised to Strong with Lower and Raise (top, scrolled).

const W := 390
const H := 844


func _initialize() -> void:
	_run.call_deferred()


func _shot() -> Image:
	for i in range(6):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	return img


func _scroll_to_end(scene: Node) -> void:
	for sc in scene.find_children("*", "ScrollContainer", true, false):
		var s := sc as ScrollContainer
		if s.is_visible_in_tree():
			await process_frame
			s.scroll_vertical = int(s.get_v_scroll_bar().max_value)


## A real tap where it lands; the capture window's scaling can put the tap
## off the button (the real-tap proof is in tests/test_workload.gd), so a
## missed tap falls back to pressing the button, and says so.
func _press(Tap, scene: Node, name: String) -> void:
	var b := scene.find_child(name, true, false) as Button
	if b == null:
		print(name, ": missing")
		return
	var why: String = await Tap.tap(b)
	if why != "":
		print(name, ": tap missed (", why, "), pressed instead")
		b.emit_signal("pressed")
	else:
		print(name, ": tapped")
	for i in range(4):
		await process_frame


func _run() -> void:
	var out := "/tmp/budget"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
	await process_frame
	var Tap = load("res://tests/tap.gd")
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	state.reset()
	state.replay_seed = 2027
	state.start_season("GEE", db.club_list("GEE"))
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	state.season.round_index = state.season.fixture.size()
	state.open_offseason()
	var scene = load("res://scenes/OffseasonScene.tscn").instantiate()
	root.add_child(scene)
	for i in range(4):
		await process_frame
	await _press(Tap, scene, "Tab_budget")
	var shots := [await _shot()]
	await _scroll_to_end(scene)
	shots.append(await _shot())
	await _press(Tap, scene, "BudgetLower_recruiting")
	await _press(Tap, scene, "BudgetRaise_high_performance")
	print("levels after taps: ", state.department_budget)
	for sc in scene.find_children("*", "ScrollContainer", true, false):
		(sc as ScrollContainer).scroll_vertical = 0
	shots.append(await _shot())
	await _scroll_to_end(scene)
	shots.append(await _shot())
	var sheet := Image.create(W * shots.size(), H, false, Image.FORMAT_RGBA8)
	for i in range(shots.size()):
		sheet.blit_rect(shots[i], Rect2i(0, 0, W, H), Vector2i(i * W, 0))
		(shots[i] as Image).save_png("%s_%d.png" % [out, i + 1])
	sheet.save_png(out + "_sheet.png")
	print("wrote ", out + "_sheet.png")
	quit(0)
