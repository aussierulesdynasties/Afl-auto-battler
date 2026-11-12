extends SceneTree
## The game-plan trait picker on the Coaching screen, for the director's look:
##   godot --path . --script tools/visual/capture_plan_trait.gd -- --out /tmp/pt --club FRE [--size 390x844]
## Writes <out>_none.png (the picker, no trait), <out>_fortress.png and
## <out>_long_bombers.png (a trait chosen: its gain, cost and how it looks).

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _shot(path: String) -> void:
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(path)
	print("wrote ", path)


func _run() -> void:
	var out := "/tmp/pt"
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
	state.save_path = "user://capture_plan_trait.save"
	state.settings_path = "user://capture_plan_trait_settings.cfg"
	state.reset()
	state.career_seed = 4127
	state.replay_seed = 4127
	state.set_setting("seen_weekly_loop_intro", true)
	state.set_setting("seen_training_intro", true)
	state.set_setting("seen_coaching_intro", true)
	DisplayServer.window_set_size(Vector2i(W, H))
	root.size = Vector2i(W, H)
	for i in range(3):
		await process_frame
	state.start_season(club, db.club_list(club))
	root.get_node("Router").go("coaching")
	await _frames(12)
	await _scroll_to("PlanTraitSection")
	await _shot(out + "_none.png")
	for id in ["fortress", "long_bombers"]:
		await _press("PlanTrait_" + id)
		await _scroll_to("PlanTraitSection")
		await _shot(out + "_" + id + ".png")
	quit(0)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame
	var wipe: Node = root.get_node_or_null("ScreenTransition")
	var waited := 0
	while wipe != null and bool(wipe.get("busy")) and waited < 1800:
		await process_frame
		waited += 1


## Bring a node into view, its top at the top of the scroll.
func _scroll_to(node_name: String) -> void:
	await _frames(4)
	var n: Node = current_scene.find_child(node_name, true, false)
	var p: Node = n.get_parent() if n != null else null
	while p != null and not (p is ScrollContainer):
		p = p.get_parent()
	if p != null and n is Control:
		var sc := p as ScrollContainer
		sc.scroll_vertical = int((n as Control).global_position.y - sc.global_position.y + sc.scroll_vertical) - 8
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
