extends SceneTree
## The League Draft board, for the director's look at its rows.
## Needs a real renderer:
##   godot --path . --script tools/visual/capture_draft.gd -- --out /tmp/draft [--size 390x844]
## Writes <out>_clubs.png (the club choice, with its line under the grid in view)
## and <out>_sheet.png.

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "/tmp/draft"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		if str(a[i]) == "--out" and i + 1 < a.size():
			out = str(a[i + 1])
		if str(a[i]) == "--size" and i + 1 < a.size():
			var wh := str(a[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	state.reset()
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	state.draft = load("res://scripts/sim/Draft.gd").new(db.all_players_sorted() + db.all_draftees_sorted(),
			db.active_clubs(2027).duplicate(), 12345)
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	for i in range(12):
		await process_frame
	# The club choice, scrolled to its foot so the line under the grid shows.
	for sc in ui.find_children("*", "ScrollContainer", true, false):
		(sc as ScrollContainer).scroll_vertical = 100000
	for i in range(4):
		await process_frame
	var clubs := root.get_viewport().get_texture().get_image()
	clubs.convert(Image.FORMAT_RGBA8)
	clubs.save_png(out + "_clubs.png")
	print("wrote ", out + "_clubs.png")
	ui.call("_on_club_chosen", "COL")
	for i in range(12):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(out + "_sheet.png")
	print("wrote ", out + "_sheet.png")
	quit(0)
