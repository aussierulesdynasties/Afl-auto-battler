extends SceneTree
## Your own plan (CustomPlan), for the director's look, in one launch:
##   godot --path . --script tools/visual/capture_custom_plan.gd -- --out /tmp/cp --club FRE [--size 390x844]
## Writes <out>_tiles.png (How we play: the six plans, your own picked),
## <out>_builder.png (Your own plan: a strength and a cost picked, named),
## <out>_break.png (the plan picker at quarter time, your own plan in it) and
## <out>_line.png (the match screen's plan line on your own plan).
## A fresh career; never touches a real save.

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "/tmp/cp"
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--club":
				club = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				W = int(wh[0])
				H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_custom_plan.save"
	state.settings_path = "user://capture_custom_plan_settings.cfg"
	state.reset()
	state.career_seed = 4127
	state.replay_seed = 4127
	state.set_setting("seen_weekly_loop_intro", true)
	state.set_setting("seen_training_intro", true)
	state.set_setting("seen_coaching_intro", true)
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	DisplayServer.window_set_size(Vector2i(W, H))
	root.size = Vector2i(W, H)
	for i in range(3):
		await process_frame
	state.start_season(club, db.club_list(club))
	state.set_custom_pick("s", "squeeze")
	state.set_custom_pick("c", "slow")
	state.set_custom_name("Dockers squeeze")
	state.set_club_plan("custom")
	root.get_node("Router").go("coaching")
	await _frames(12)
	await _scroll_to("HowWePlay")
	_save(out + "_tiles.png")
	await _scroll_to("OwnPlanSection")
	_save(out + "_builder.png")
	# Match day: the first match at quarter time, then the plan line.
	if not state.prepare_interactive_match():
		push_error("no match to prepare")
		quit(1)
		return
	state.pending_sim.run_quarter()
	var scene = load("res://scenes/MatchScene.tscn").instantiate()
	current_scene.queue_free()
	root.add_child(scene)
	await _frames(12)
	var row: Button = scene.find_child("CallRow_plan", true, false)
	if row != null:
		row.emit_signal("pressed")
		await _frames(8)
	await _scroll_to("PlanPicker", scene)
	_save(out + "_break.png")
	# Close the picker with its own Done: a ui_cancel here reaches the Router as
	# Android Back and puts the title menu over the match.
	var done: Button = scene.find_child("CallDone", true, false)
	if done != null:
		done.emit_signal("pressed")
		await _frames(8)
	var go: Button = scene.find_child("StartQuarter", true, false)
	if go != null:
		go.emit_signal("pressed")
	await _frames(10)
	scene.call("_show_setup", {"gameplan": "custom"})
	await _frames(10)
	_save(out + "_line.png")
	quit(0)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame
	var wipe: Node = root.get_node_or_null("ScreenTransition")
	var waited := 0
	while wipe != null and bool(wipe.get("busy")) and waited < 1800:
		await process_frame
		waited += 1


## Bring a node into view, its top near the top of the scroll.
func _scroll_to(node_name: String, under: Node = null) -> void:
	await _frames(4)
	var base: Node = under if under != null else current_scene
	var n: Node = base.find_child(node_name, true, false)
	var p: Node = n.get_parent() if n != null else null
	while p != null and not (p is ScrollContainer):
		p = p.get_parent()
	if p != null and n is Control:
		var sc := p as ScrollContainer
		sc.scroll_vertical = int((n as Control).global_position.y - sc.global_position.y + sc.scroll_vertical) - 8
	elif n == null:
		print("MISSING ", node_name)
	await _frames(4)


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
