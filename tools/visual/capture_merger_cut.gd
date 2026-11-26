extends SceneTree
## The merger screen (director 2026-11-15: "I pick, delist screen"): the Brisbane
## Bears at the 1997 rollover, their list at the era's spots, Fitzroy's best
## across with the merger. Dark theme, a phone in portrait.
## Needs a real renderer (windowed, through C:/kt/gpu_slot.sh, off screen via override.cfg):
##   CAP_DIR=docs/captures/legacy-merger-cut godot --path . --rendering-method gl_compatibility --script tools/visual/capture_merger_cut.gd
## Writes merger_cut_390x844.png (the screen as it opens) and
## merger_cut_marked_390x844.png (all but one picked, scrolled to them).
## Never touches a real save.


func _initialize() -> void:
	_run.call_deferred()


func _shot(path: String) -> void:
	for i in range(8):
		await process_frame
	await create_timer(1.0).timeout
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(path)
	print("CAPTURED ", path)


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	var LegacyRollover = load("res://scripts/state/LegacyRollover.gd")
	gs.autosave_enabled = false
	gs.save_path = "user://capture_merger_cut.save"
	gs.settings_path = "user://capture_merger_cut.cfg"
	var dir := OS.get_environment("CAP_DIR") if OS.get_environment("CAP_DIR") != "" else "docs/captures/legacy-merger-cut"
	var w := int(OS.get_environment("CAP_W")) if OS.get_environment("CAP_W") != "" else 390
	var h := int(OS.get_environment("CAP_H")) if OS.get_environment("CAP_H") != "" else 844
	DirAccess.make_dir_recursive_absolute(dir)
	gs.reset("1990")
	gs.begin_real_lists()
	gs.choose_real_club("BRL")
	gs.finish_intake_draft()
	gs.legacy = {"fitzroy": "merged"}
	gs.season_year = LegacyRollover.TALKS_YEAR + 1
	db.apply_era(LegacyRollover.TALKS_YEAR + 1)
	gs._era_trim("BRL", false)
	LegacyRollover._merge(gs, false)
	gs.merger_cut_due = true
	var UK = load("res://scripts/ui/UiKit.gd")
	UK.apply_palette()
	DisplayServer.window_set_size(Vector2i(w, h))
	root.size = Vector2i(w, h)
	var bg := ColorRect.new()
	bg.color = UK.BG
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)
	# Straight onto the screen, not through the router's threaded load.
	var scene: Control = load(router.SCENES["merger_cut"]).instantiate()
	root.add_child(scene)
	current_scene = scene
	await _shot("%s/merger_cut_%dx%d.png" % [dir, w, h])
	# All but one picked: the lowest rated, as a coach would start.
	var list: Array = gs.season.lists[gs.my_club].duplicate()
	list.sort_custom(func(a, b): return int(a.get("overall", 0)) < int(b.get("overall", 0)))
	var n: int = gs.merger_cut_left()
	scene.set("_going", list.slice(0, n - 1).map(func(q): return str(q["id"])))
	scene.call("_build")
	for i in range(4):
		await process_frame
	var first := scene.find_child("MergerRow_" + str(list[n - 1]["id"]), true, false) as Control
	var p := first.get_parent() if first != null else null
	while p != null and not (p is ScrollContainer):
		p = p.get_parent()
	if p != null:
		var sc := p as ScrollContainer
		sc.scroll_vertical = int(first.global_position.y - sc.global_position.y) + sc.scroll_vertical - 8
	await _shot("%s/merger_cut_marked_%dx%d.png" % [dir, w, h])
	quit()
