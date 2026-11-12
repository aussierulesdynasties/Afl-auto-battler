extends SceneTree
## The 1990 league's guernseys on one sheet (the 1990 start), plus the Bears'
## 1992 change, for checking against the real kits. Needs a real renderer:
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_era_guernseys.gd -- --out PATH.png

## The 14 clubs of the 1990 VFL/AFL.
const CLUBS_1990 := ["BRL", "CAR", "COL", "ESS", "FIT", "WBD", "GEE", "HAW", "MEL", "NTH",
		"RIC", "STK", "SYD", "WCE"]


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "era_guernseys.png"
	var cli := OS.get_cmdline_user_args()
	for i in range(cli.size() - 1):
		if str(cli[i]) == "--out":
			out = str(cli[i + 1])
	await process_frame
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	db.reload("1990")  # the 1990 start keeps Fitzroy; today's start drops it
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = Vector2i(1240, 370)
	var bg := ColorRect.new()
	bg.color = UK.BG
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)
	var grid := GridContainer.new()
	grid.columns = 8
	grid.position = Vector2(30, 20)
	grid.add_theme_constant_override("h_separation", 18)
	grid.add_theme_constant_override("v_separation", 14)
	root.add_child(grid)
	var shown := 0
	for code in CLUBS_1990:
		if not db.clubs.has(code):
			push_error("no club %s in 1990" % code)
			continue
		grid.add_child(_cell(UK, code, "%s 1990" % db.clubs[code].get("name", code)))
		shown += 1
	db.apply_era(1992)
	grid.add_child(_cell(UK, "BRL", "%s 1992" % db.clubs["BRL"].get("name", "BRL")))
	print("era guernseys: %d clubs of 1990" % shown)
	for i in range(8):
		await process_frame
	root.get_viewport().get_texture().get_image().save_png(out)
	quit()


func _cell(UK, code: String, text: String) -> Control:
	var v := VBoxContainer.new()
	var c := CenterContainer.new()
	c.add_child(UK.club_marker(code, 110.0))
	v.add_child(c)
	var l := Label.new()
	l.text = text
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.custom_minimum_size.x = 128
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(l)
	return v
