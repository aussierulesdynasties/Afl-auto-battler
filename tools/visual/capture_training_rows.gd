extends SceneTree
## Real renderer: godot --path . --rendering-method gl_compatibility --script tools/visual/capture_training_rows.gd
## Environment: CAP_W, CAP_H (default 390x800), CAP_OUT (file prefix, default
## "training_rows"). Saves <prefix>_list.png, <prefix>_cards.png and <prefix>_group.png:
## the Training list with a long name, an injury stamp, an archetype plan and a short
## name, the list scrolled to the cards, then the same list with a group selected.
## Needs --windowed and an override.cfg; waits on timers, not frame_post_draw, which
## an unfocused window may never send. Illustrative fixture only; it never
## touches a real save.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	state.autosave_enabled = false
	state.save_path = "user://capture_training.save"
	state.settings_path = "user://capture_training.cfg"
	db.reload()
	state.reset()
	state.start_season("COL", db.club_list("COL"))
	var w := int(OS.get_environment("CAP_W")) if OS.get_environment("CAP_W") != "" else 390
	var h := int(OS.get_environment("CAP_H")) if OS.get_environment("CAP_H") != "" else 800
	var prefix := OS.get_environment("CAP_OUT") if OS.get_environment("CAP_OUT") != "" else "training_rows"
	DisplayServer.window_set_size(Vector2i(w, h))
	root.size = Vector2i(w, h)
	# The states a real list shows: a long name, an injury stamp, an archetype plan.
	var list: Array = state.my_list
	list[0]["generic_name"] = "Alexander Papaioannou-Featherstone"
	list[1]["injury_weeks"] = 3
	state.set_player_plan(str(list[2]["id"]), str(state.plans_for(list[2])[1]) if state.plans_for(list[2]).size() > 1 else "position")
	state.set_setting("seen_training_intro", true)
	# Straight onto the screen, not through the router's threaded load (it stalls
	# a --script run's main loop).
	var scene: Node = load(router.SCENES["training"]).instantiate()
	root.add_child(scene)
	current_scene = scene
	for i in range(20):
		await process_frame
	await create_timer(2.0).timeout
	root.get_texture().get_image().save_png(prefix + "_list.png")
	# A wide window shows little of the list at the top: scroll the cards in.
	var scroll := scene.get("_list_scroll") as ScrollContainer
	var first_card := scene.find_child("Card_" + str(list[0]["id"]), true, false) as Control
	if scroll != null and first_card != null:
		scroll.scroll_vertical = int(first_card.get_global_rect().position.y - scroll.get_global_rect().position.y) - 40
		await create_timer(1.0).timeout
		root.get_texture().get_image().save_png(prefix + "_cards.png")
	scene.set("_bulk_selected", {str(list[1]["id"]): true, str(list[3]["id"]): true})
	scene.call("_build")
	for i in range(6):
		await process_frame
	await create_timer(2.0).timeout
	root.get_texture().get_image().save_png(prefix + "_group.png")
	print("CAPTURE saved ", prefix, " at ", w, "x", h)
	quit()
