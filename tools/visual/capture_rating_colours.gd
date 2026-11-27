extends SceneTree
## Visual review tool for the rating rebuild's Phase 8 (RATING_REBUILD §5): the
## player card's Ratings section, in its four groups and its colours
## (PlayerSheet.COLOUR_CUTS). Collingwood, seeded.
## Needs a real renderer (windowed, through C:/kt/gpu_slot.sh, off screen via override.cfg):
##   godot --path . --script tools/visual/capture_rating_colours.gd -- --out /tmp/rc --size 390x844
## Writes <out>_<player>.png per player, scrolled to the Ratings heading.
## Never touches a real save.


func _initialize() -> void:
	_run.call_deferred()


func _shot() -> Image:
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	return img


func _run() -> void:
	var out := "/tmp/rc"
	var size := Vector2i(390, 844)
	var who := ["Nick Daicos", "Darcy Moore", "Darcy Cameron"]
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--size":
			size = Vector2i(int(str(a[i + 1]).get_slice("x", 0)), int(str(a[i + 1]).get_slice("x", 1)))
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var sheet_script = load("res://scripts/ui/PlayerSheet.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	state.career_seed = 7737
	state.replay_seed = 7737
	state.reset()
	state.start_season("COL", db.club_list("COL"))
	root.size = size
	DisplayServer.window_set_size(size)
	var host := Control.new()
	host.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(host)
	for p in state.my_list:
		for key in ["injury_weeks", "injury_kind", "suspension_weeks"]:
			p.erase(key)
	for name in who:
		var found: Array = state.my_list.filter(
				func(q): return "%s %s" % [q.get("first", ""), q.get("last", "")] == name)
		if found.is_empty():
			push_error("not on the list: " + name)
			continue
		var p: Dictionary = found[0]
		var sheet: Control = sheet_script.open(host, p)
		await _shot()
		var heads := sheet.find_children("*", "Label", true, false).filter(
				func(l): return (l as Label).text == "Ratings")
		var top: Control = heads[0] if not heads.is_empty() else sheet.find_child("ProfileAttributes", true, false)
		var sc: Node = top.get_parent()
		while sc != null and not (sc is ScrollContainer):
			sc = sc.get_parent()
		if sc != null:
			(sc as ScrollContainer).scroll_vertical += int(top.global_position.y - (sc as Control).global_position.y) - 12
		var img: Image = await _shot()
		var file := "%s_%s.png" % [out, name.get_slice(" ", 1).to_lower()]
		img.save_png(file)
		print("SHOT %s | %s OVR %d" % [file, name, int(load("res://scripts/sim/Rating.gd").ovr(p))])
		sheet.queue_free()
		await process_frame
	quit(0)
