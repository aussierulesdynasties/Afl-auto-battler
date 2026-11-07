extends SceneTree
## Visual review tool for the player sheet's club line (director's report,
## 2026-11-08: "Port Adelaide" under his name printed one letter per line).
## Needs a real renderer (windowed, through C:/kt/gpu_slot.sh, off screen via override.cfg):
##   godot --path . --script tools/visual/capture_sheet_club.gd -- --out /tmp/sc --size 390x844
## Writes <out>_match.png (a Port Adelaide player's sheet opened over the match),
## <out>_list.png (an Essendon player's sheet from My list: a red club, his name's
## white ink) and <out>_gws320.png (Greater Western Sydney, the longest club name,
## on a 320 px phone). Seeded; never touches a real save.


func _initialize() -> void:
	_run.call_deferred()


func _shot() -> Image:
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	return img


func _size(sz: Vector2i) -> void:
	root.size = sz
	DisplayServer.window_set_size(sz)


func _report(sheet: Control, out: String) -> void:
	var cl: Label = sheet.find_child("ProfileClub", true, false) if sheet != null else null
	var nm: Label = sheet.find_child("ProfileName", true, false) if sheet != null else null
	print("CAPTURED ", out, " | ", nm.text if nm != null else "no name", " / ",
			"'%s' %d line(s), %.0fx%.0f px at %s, its column %.0f px" % [cl.text, cl.get_line_count(), cl.size.x, cl.size.y,
					cl.get_global_rect().position, (cl.get_parent() as Control).size.x] if cl != null else "no club line")


## The oldest man on the list: a senior footballer, not a draftee.
func _pick(list: Array) -> Dictionary:
	var by_age := list.duplicate()
	by_age.sort_custom(func(x, z): return float(x.get("age", 0.0)) > float(z.get("age", 0.0)))
	return by_age[0]


func _run() -> void:
	var out := "/tmp/sc"
	var size := Vector2i(390, 844)
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--size":
			size = Vector2i(int(str(a[i + 1]).get_slice("x", 0)), int(str(a[i + 1]).get_slice("x", 1)))
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var name_link = load("res://scripts/ui/NameLink.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	state.career_seed = 7737
	state.replay_seed = 7737
	_size(size)

	# Over the match: Port Adelaide, his sheet opened as a tap on his name opens it.
	state.reset()
	state.start_season("PAD", db.club_list("PAD"))
	state.tutorials = false
	state.prepare_interactive_match()
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	current_scene = m
	await _shot()
	var sheet: Control = name_link.open(m, str(_pick(state.my_list)["id"]))
	(await _shot()).save_png(out + "_match.png")
	_report(sheet, out + "_match.png")
	m.queue_free()
	await process_frame

	# My list: Essendon, a red club whose players' names print white.
	state.reset()
	state.start_season("ESS", db.club_list("ESS"))
	state.tutorials = false
	var ls: Control = load("res://scenes/ListScene.tscn").instantiate()
	root.add_child(ls)
	current_scene = ls
	await _shot()
	ls.call("_open_profile", str(_pick(state.my_list)["id"]))
	(await _shot()).save_png(out + "_list.png")
	_report(ls.find_child("PlayerProfile", true, false), out + "_list.png")
	ls.queue_free()
	await process_frame

	# The narrowest phone and the longest club name: Greater Western Sydney.
	_size(Vector2i(320, 693))
	state.reset()
	state.start_season("GWS", db.club_list("GWS"))
	state.tutorials = false
	var gl: Control = load("res://scenes/ListScene.tscn").instantiate()
	root.add_child(gl)
	current_scene = gl
	await _shot()
	gl.call("_open_profile", str(_pick(state.my_list)["id"]))
	(await _shot()).save_png(out + "_gws320.png")
	_report(gl.find_child("PlayerProfile", true, false), out + "_gws320.png")
	quit(0)
