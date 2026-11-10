extends SceneTree
## Review capture for row T5.r158 (a club across generations), dark.
##   godot --path . --script tools/visual/capture_premiership_side.gd -- --size 390x844 --out <prefix>
## You coach Fremantle in the career's fifth season; Melbourne's premiership
## two seasons back is staged on
## the honour roll with three of today's Melbourne players in its side, and
## Geelong's the season before with eight. Opens each page from the ladder by
## its handler (the real taps are in tests/run_clublink_tests.gd). Writes
## <out>_named.png (Melbourne: survivors named) and <out>_counted.png (Geelong:
## survivors counted). Never touches a real save.

var _w := 390
var _h := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(out: String, shot: String) -> void:
	await _frames(4)
	var img := root.get_viewport().get_texture().get_image()
	if img == null:
		print("no renderer: ", shot)
		return
	img.convert(Image.FORMAT_RGBA8)
	img.save_png("%s_%s.png" % [out, shot])
	print("wrote ", out, "_", shot, ".png")


func _side(gs, code: String, keep: int) -> Array:
	var list: Array = gs.season.lists[code]
	var side := []
	for i in 23:
		side.append(str(list[i * 2]["id"]) if i < keep else "gone_%s_%d" % [code, i])
	return side


func _run() -> void:
	var out := "premiership_side"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
	await process_frame
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	gs.autosave_enabled = false
	gs.save_path = "user://capture_premiership_side.save"
	gs.settings_path = "user://capture_premiership_side.cfg"
	UK.apply_appearance("dark")
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	gs.reset()
	gs.set_setting("seen_season_stats_intro", true)
	gs.career_seed = 2026
	gs.replay_seed = 2026
	gs.start_season("FRE", db.club_list("FRE"))
	for i in range(3):
		gs.advance()
	# A fifth season, so both flags fall inside the career (it starts in 2027).
	gs.season_year = int(gs.season_year) + 4
	var y := int(gs.season_year)
	gs.honour_roll = [
		{"year": y - 3, "premier": "GEE", "runner_up": "SYD", "premier_side": _side(gs, "GEE", 8)},
		{"year": y - 2, "premier": "MEL", "runner_up": "GEE", "premier_side": _side(gs, "MEL", 3)},
	]
	load("res://scripts/ui/StatsHubScene.gd").current = "ladder"
	var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(s)
	current_scene = s
	await _frames(12)
	var CL = load("res://scripts/ui/ClubLink.gd")
	for pair in [["MEL", "named"], ["GEE", "counted"]]:
		CL.open(s.find_child("Club_" + pair[0], true, false), pair[0])
		await _frames(12)
		var page: Node = s.find_child("ClubPage", true, false)
		var line: Node = page.find_child("PremiershipSide", true, false) if page != null else null
		print(pair[0], " line: ", (line as RichTextLabel).get_parsed_text() if line != null else "none")
		await _shot(out, pair[1])
		var close: Node = page.find_child("CloseClub", true, false) if page != null else null
		if close != null:
			(close as Button).emit_signal("pressed")
			await _frames(10)
	quit(0)
