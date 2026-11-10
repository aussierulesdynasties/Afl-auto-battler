extends SceneTree
## Row T1.R26 L1: the Redraft board and a scouted prospect's detail as your
## scouts read him (type, traits, Full ratings), with his true salary.
## Needs a real renderer:
##   godot --path . --windowed --script tools/visual/capture_draft_reads.gd -- --out /tmp/reads [--size 390x844]
## Writes <out>_board.png (his row), <out>_detail.png (top of his detail) and
## <out>_ratings.png (Full ratings, the read note at the top).

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String) -> void:
	await _frames(4)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(path)
	print("wrote ", path)


## Scroll every scroll container so `node` sits near the top of its view.
func _scroll_to(ui: Node, node: Control) -> void:
	for sc in ui.find_children("*", "ScrollContainer", true, false):
		var s := sc as ScrollContainer
		if s.is_ancestor_of(node):
			s.scroll_vertical = int(node.global_position.y - s.global_position.y) + s.scroll_vertical - 8


func _run() -> void:
	var out := "/tmp/reads"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		if str(a[i]) == "--out" and i + 1 < a.size():
			out = str(a[i + 1])
		if str(a[i]) == "--size" and i + 1 < a.size():
			var wh := str(a[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
	await process_frame
	root.gui_disable_input = true
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	state.reset()
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	state.draft = load("res://scripts/sim/Draft.gd").new(db.all_players_sorted() + db.all_draftees_sorted(),
			db.active_clubs(2027).duplicate(), 12345)
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _frames(12)
	ui.call("_on_club_chosen", "FRE")
	await _frames(12)
	# The first prospect the scouts only read (not exact), with traits.
	var draft = state.draft
	var who: Dictionary = {}
	for p in db.all_draftees_sorted():
		if bool(draft.user_view(p)["scouted"]) and not Traits.of(draft.scouted_copy(p)).is_empty():
			who = p
			break
	if who.is_empty():
		push_error("no read prospect with traits")
		quit(1)
		return
	var id := str(who["id"])
	print("READS who=", id, " value=", int(who["value"]), " price=", draft.price(who))
	var kind := ui.find_child("Kind_" + id, true, false) as Control
	if kind != null:
		_scroll_to(ui, kind)
		await _frames(2)
		_scroll_to(ui, kind)
	await _shot(out + "_board.png")
	ui.call("_open_player", id)
	await _frames(8)
	await _shot(out + "_detail.png")
	ui.set("_detail_all", true)
	ui.call("_open_player", id)
	await _frames(8)
	var note := ui.find_child("DetailAttributesRead", true, false) as Control
	if note == null:
		push_error("no DetailAttributesRead")
	else:
		_scroll_to(ui, note)
		await _frames(2)
		_scroll_to(ui, note)
	await _shot(out + "_ratings.png")
	quit(0)
