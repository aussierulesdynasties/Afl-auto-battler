extends SceneTree
## Team familiarity (row 125), for the director's look, one launch: where the side
## is picked with four new-club men in it, a man's list row and profile, the trade
## and free-agency screens, and the draft board. Needs a real renderer:
##   godot --path . --script tools/visual/capture_familiarity.gd -- --out /tmp/fam [--size 390x844] [--club FRE]
## Writes <out>_selection.png, _list.png, _profile.png, _trade.png, _agents.png, _draft.png.

var W := 390
var H := 844
var out := "/tmp/fam"


func _initialize() -> void:
	_run.call_deferred()


func _frames(n := 8) -> void:
	for i in range(n):
		await process_frame


func _shot(what: String) -> void:
	await _frames()
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png("%s_%s.png" % [out, what])
	print("wrote %s_%s.png" % [out, what])


## Scroll the control's page so it sits a third of the way down the screen.
func _show(c: Control) -> void:
	if c == null:
		print("nothing to show")
		return
	var n: Node = c.get_parent()
	while n != null and not n is ScrollContainer:
		n = n.get_parent()
	if n != null:
		var sc := n as ScrollContainer
		sc.scroll_vertical = int(c.global_position.y - sc.global_position.y + sc.scroll_vertical - H / 3)
		await _frames(4)


func _run() -> void:
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--club":
			club = str(a[i + 1])
		if str(a[i]) == "--size":
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
	var sl = root.get_node("ScreenLayout")
	sl.ui_scale = 1.0 / maxf(0.01, sl.desktop_density(Vector2(W, H), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0))
	sl._update_scale()
	await _frames(6)
	for key in ["selection", "list", "offseason", "draft"]:
		state.set_setting("seen_%s_intro" % key, true)
	state.replay_seed = 2027
	state.start_season(club, db.club_list(club))
	# A Squad names copies: the men themselves are on the list.
	# Loaded here: its class needs the autoloads, which a SceneTree script compiles before.
	var fam: GDScript = load("res://scripts/sim/TeamFamiliarity.gd")
	var named: Array = state.my_squad().ground.map(func(q): return state.list_player(str(q["id"])))
	for p in named.slice(0, 4):
		fam.arrive_club(p)
		p["team_fam"] = 70.0
	fam.arrive_draftee(named[4])
	named[4]["team_fam"] = 70.0

	var ui: Control = load("res://scenes/SelectionScene.tscn").instantiate()
	root.add_child(ui)
	await _frames()
	await _show(ui.find_child("TurnoverNote", true, false))
	await _shot("selection")
	ui.queue_free()
	await _frames(3)

	var ls: Control = load("res://scenes/ListScene.tscn").instantiate()
	root.add_child(ls)
	await _frames()
	for t in ls.find_children("*", "Button", true, false):
		if (t as Button).text == "Full list":
			(t as Button).emit_signal("pressed")
			break
	await _frames()
	var row: Control = ls.find_child("Row_" + str(named[0]["id"]), true, false)
	await _show(row)
	await _shot("list")
	if row != null:
		(row as Button).emit_signal("pressed")
		await _frames()
		await _show(ls.find_child("ProfileFamiliarity", true, false))
		await _shot("profile")
	ls.queue_free()
	await _frames(3)

	state.season.round_index = state.season.fixture.size()
	state.open_offseason()
	var off: Control = load("res://scenes/OffseasonScene.tscn").instantiate()
	root.add_child(off)
	await _frames()
	off.set("_tab", "trade")
	off.set("_trade_club", "MEL")
	off.set("_mine", [str(state.my_list[30]["id"])])
	off.set("_theirs", [str(state.season.lists["MEL"][0]["id"])])
	off.call("_build")
	await _frames()
	await _show(off.find_child("TradeFamiliarity", true, false))
	await _shot("trade")
	off.set("_tab", "agents")
	off.call("_build")
	await _frames()
	await _shot("agents")
	off.queue_free()
	await _frames(3)

	if state.begin_intake_draft():
		var dr: Control = load("res://scenes/DraftScene.tscn").instantiate()
		root.add_child(dr)
		await _frames(12)
		# The sheet before the first pick sits over the board.
		for t in root.find_children("*", "Button", true, false):
			if (t as Button).text == "To the draft":
				(t as Button).emit_signal("pressed")
				break
		await _frames(12)
		await _show(dr.find_child("DraftFamiliarity", true, false))
		await _shot("draft")
	quit(0)
