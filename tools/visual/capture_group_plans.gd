extends SceneTree
## The pre-season plan by position group (row 101), for the director's look.
## Needs a real renderer and a window (keep it out of the way with an override.cfg):
##   godot --path . --script tools/visual/capture_group_plans.gd -- --out /tmp/gp --club FRE [--size 360x800]
## Writes <out>_every.png (the "Plan for" choice on every group, the first
## block under it), <out>_forwards.png (the forwards picked, their first block
## set to Heavy; _forwards_block.png scrolled to that block) and <out>_back.png (every group again, the line naming the
## group with a plan of its own). Nothing here touches a real save.

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
	load("res://scripts/core/Features.gd").set_on("preseason", true)
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
	await _scroll_to("PreSeasonGroups")
	await _shot(out + "_every.png")
	await _press("Group_FWD")
	await _press("Load0_heavy")
	await _scroll_to("PreSeasonGroups")
	await _shot(out + "_forwards.png")
	await _scroll_to("Block_0")
	await _shot(out + "_forwards_block.png")
	await _press("Group_ALL")
	await _scroll_to("PreSeasonGroups")
	await _shot(out + "_back.png")
	print("forwards ", state.preseason_blocks("", "FWD")[0], " mids ", state.preseason_blocks("", "MID")[0])
	quit(0)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


## Bring a node to the top of whatever scroll holds it.
func _scroll_to(node_name: String) -> void:
	await _frames(4)
	var n: Node = current_scene.find_child(node_name, true, false)
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
	var b: Node = current_scene.find_child(node_name, true, false)
	if b is Button:
		(b as Button).emit_signal("pressed")
	else:
		print("MISSING ", node_name)
	await _frames(3)
