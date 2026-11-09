extends SceneTree
## My list's Full list pane for a look (STYLE-05, row 6.34): a fresh career for
## each club, the pane at its top and one screen down. Needs a real renderer
## and a window; never touches a real save.
##   godot --path . --windowed --script tools/visual/capture_full_list.gd -- --out DIR --tag after --clubs MEL,FRE
## Writes DIR/<tag>_list_<club>.png and DIR/<tag>_list_<club>_down.png.

var _size := Vector2i(390, 844)


func _initialize() -> void:
	_run.call_deferred()


func _frames(n := 8) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	var out := "."
	var tag := "list"
	var clubs := PackedStringArray(["MEL", "FRE"])
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--tag":
				tag = str(a[i + 1])
			"--clubs":
				clubs = str(a[i + 1]).split(",")
	await process_frame
	var state: Node = root.get_node("GameState")
	var db: Node = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_full_list.save"
	state.settings_path = "user://capture_full_list.cfg"
	root.size = _size
	await _frames(10)
	for club in clubs:
		state.reset()
		state.career_seed = 42
		state.replay_seed = 42
		state.start_season(club, db.club_list(club))
		state.tutorials = false
		var ls: Control = load("res://scenes/ListScene.tscn").instantiate()
		root.add_child(ls)
		await _frames()
		for t in ls.find_children("*", "Button", true, false):
			if (t as Button).text == "Full list":
				(t as Button).emit_signal("pressed")
				break
		await _frames(30)
		var stem := "%s/%s_list_%s" % [out, tag, club]
		_save(stem + ".png")
		var rows: Node = ls.find_child("ListRows", true, false)
		var sc: Node = rows
		while sc != null and not (sc is ScrollContainer):
			sc = sc.get_parent()
		if sc != null:
			(sc as ScrollContainer).scroll_vertical = int((sc as ScrollContainer).size.y) - 40
			await _frames(10)
			_save(stem + "_down.png")
		print("captured ", stem)
		ls.queue_free()
		await _frames(3)
	quit()


func _save(path: String) -> void:
	root.get_viewport().get_texture().get_image().save_png(path)
