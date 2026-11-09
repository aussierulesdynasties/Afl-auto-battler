extends SceneTree
## The pre-season drill plan by position group (row 101), for the director's look.
## Needs a real renderer and a window (keep it out of the way with an override.cfg):
##   godot --path . --script tools/visual/capture_group_plans.gd -- --out /tmp/gp --club FRE [--size 360x800]
## Weeks 1 to 3 go on Game plan. Writes <out>_whole.png (the drill row on the
## whole side), <out>_forwards.png (the forwards' tab, Win Contest added to
## their drills) and <out>_split.png (the whole side again, the line naming
## the split). Nothing here touches a real save.

var W := 360
var H := 800


func _initialize() -> void:
	_run.call_deferred()


func _shot(path: String) -> void:
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if W >= 760 and img.get_width() != W:
		img.resize(W, H, Image.INTERPOLATE_LANCZOS)
	img.save_png(path)
	print("wrote ", path)


func _run() -> void:
	var out := "/tmp/gp"
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--club":
			club = str(a[i + 1])
		if str(a[i]) == "--size":
			var wh := str(a[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_group_plans.save"
	state.settings_path = "user://capture_group_plans_settings.cfg"
	state.show_real_names = true
	state.reset()
	state.career_seed = 4127
	state.replay_seed = 4127
	state.set_setting("seen_weekly_loop_intro", true)
	state.set_setting("seen_training_intro", true)
	state.set_setting("seen_preseason_intro", true)
	if W >= 760:
		# A PC window: the game lays it out on its own canvas (as capture_plan_know).
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_size(Vector2i(W, H))
		for i in range(10):
			await process_frame
		var factor := float(W) / maxf(1.0, root.get_visible_rect().size.x)
		if factor > 1.05:
			DisplayServer.window_set_size(Vector2i(int(W * factor), int(H * factor)))
			for i in range(10):
				await process_frame
	else:
		DisplayServer.window_set_size(Vector2i(W, H))
		root.size = Vector2i(W, H)
	for i in range(3):
		await process_frame
	state.start_season(club, db.club_list(club))
	state.open_preseason()
	root.get_node("Router").go("hub")
	await _frames(10)
	await _press("Focus0_plan")
	await _scroll_to("Drill0")
	await _shot(out + "_whole.png")
	await _press("DrillFor0_FWD")
	await _press("Drill0_contest")
	await _scroll_to("Drill0")
	await _shot(out + "_forwards.png")
	await _press("DrillFor0_ALL")
	await _scroll_to("Drill0")
	await _shot(out + "_split.png")
	print("forwards ", state.preseason_drills(0, "FWD"), " mids ", state.preseason_drills(0, "MID"))
	quit(0)


## Find a node under the root, waiting up to 900 frames for the scene to build
## (the screen transition and a phone-sized layout take longer than the first press).
func _find(node_name: String) -> Node:
	for i in range(900):
		var n: Node = root.find_child(node_name, true, false)
		if n != null:
			return n
		await process_frame
	return null


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


## Bring a node to the top of whatever scroll holds it.
func _scroll_to(node_name: String) -> void:
	await _frames(4)
	var n: Node = await _find(node_name)
	var p: Node = n.get_parent() if n != null else null
	while p != null and not (p is ScrollContainer):
		p = p.get_parent()
	if p != null:
		var sc := p as ScrollContainer
		sc.scroll_vertical = int((n as Control).get_global_rect().position.y - sc.get_global_rect().position.y) + sc.scroll_vertical - 8
	elif n == null:
		print("MISSING ", node_name)
	await _frames(4)


func _press(node_name: String) -> void:
	await _frames(3)
	var b: Node = await _find(node_name)
	if b is Button:
		(b as Button).emit_signal("pressed")
	else:
		print("MISSING ", node_name)
	await _frames(3)
