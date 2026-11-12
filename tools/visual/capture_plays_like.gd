extends SceneTree
## The "Plays like" line on every draft screen, for the director's look. Needs a
## real renderer:
##   godot --path . --script tools/visual/capture_plays_like.gd -- --out C:/caps/pl [--club FRE] [--size 390x844]
## Writes <out>_national.png, _national_open.png, _league.png, _league_open.png,
## _rookie.png and _midseason.png.

var W := 390
var H := 844
var _state: Node
var _db: Node


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String) -> void:
	await _frames(12)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if W >= 760 and img.get_width() != W:
		img.resize(W, H, Image.INTERPOLATE_LANCZOS)
	img.save_png(path)
	print("wrote ", path, " ", img.get_size())


func _career(club: String) -> void:
	_state.reset()
	_state.career_seed = 2031
	_state.replay_seed = 2031
	_state.start_season(club, _db.club_list(club))
	_state.tutorials = false
	_state.set_setting("seen_weekly_loop_intro", true)


func _lines(host: Node, what: String) -> void:
	var seen := 0
	for l in host.find_children("PlaysLike_*", "Label", true, false) + host.find_children("DetailPlaysLike", "Label", true, false):
		if (l as Label).is_visible_in_tree() and seen < 4:
			print("CAPTURE ", what, ": ", (l as Label).text, " at ", (l as Label).get_global_rect())
			seen += 1


func _run() -> void:
	var out := "C:/kt/plays_like_caps/pl"
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
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.save_path = "user://capture_plays_like.save"
	_state.settings_path = "user://capture_plays_like.cfg"
	_state.show_real_names = true
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	await _frames(10)
	var layout = root.get_node("ScreenLayout")
	var base: float = layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0)
	layout.ui_scale = 1.0 / maxf(1.0, base)
	layout._update_scale()
	await _frames(10)
	print("canvas ", root.get_visible_rect().size)
	var RL = load("res://scripts/state/RookieList.gd")
	var MD = load("res://scripts/state/MidseasonDraft.gd")

	# The National Draft: the board, then a prospect opened.
	_career(club)
	# The scouting list (My list > Scouting): the coming class, read every week.
	var sc: Control = load("res://scenes/ScoutingScene.tscn").instantiate()
	root.add_child(sc)
	await _frames(20)
	_lines(sc, "scouting")
	await _shot(out + "_scouting.png")
	sc.queue_free()
	await _frames(5)
	_state.season.round_index = _state.season.fixture.size()
	_state.open_offseason()
	_state.begin_intake_draft()
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _frames(20)
	if ui.find_child("DraftMeeting", true, false) != null:
		ui.call("handle_back")
	await _frames(20)
	_lines(ui, "national")
	await _shot(out + "_national.png")
	var board: Array = _state.draft.board("", "", "", "overall", true)
	ui.call("_open_player", str(board[0]["id"]))
	await _frames(20)
	_lines(ui.find_child("PlayerDetail", true, false), "national open")
	await _shot(out + "_national_open.png")
	ui.call("_close_player")

	# My list, once our first pick is made.
	var draft = _state.draft
	var turns := 0
	while not draft.is_finished() and str(draft.current_club()) != club and turns < 400:
		turns += 1
		var ai: Dictionary = draft._best_ai_pick(draft.current_club())
		if ai.is_empty() or not draft._draft_pick(draft.current_club(), ai):
			draft._skip_current_pick()
	if str(draft.current_club()) == club and draft.pick(draft.board("", "", "", "overall", true)[0]):
		ui.call("_refresh")
		ui.call("_select_tab", "squad")
		await _frames(20)
		_lines(ui.find_child("PickedName_*", true, false).get_parent(), "my list")
		await _shot(out + "_mylist.png")

	# The Rookie Draft: finish the National Draft, the sheet opens on the next screen.
	while not draft.is_finished():
		var c: Dictionary = draft._best_ai_pick(draft.current_club())
		if c.is_empty() or not draft._draft_pick(draft.current_club(), c):
			draft._skip_current_pick()
	_state.finish_intake_draft()
	ui.queue_free()
	await _frames(5)
	if RL.waiting(_state):
		if _state.needs_season_wrap():
			_state.begin_season_from_wrap()
		var path := "res://scenes/PreSeasonScene.tscn" if _state.preseason_active() else "res://scenes/HubScene.tscn"
		var scene: Control = load(path).instantiate()
		root.add_child(scene)
		await _frames(30)
		_lines(scene, "rookie")
		await _shot(out + "_rookie.png")
		scene.queue_free()
		await _frames(5)
	else:
		print("CAPTURE rookie: no pick waiting")

	# The mid-season draft, on the hub.
	_career(club)
	var year: int = _state.season_year
	var class_now: Array = _state.draftee_pool.filter(func(p): return int(p.get("draft_year", year)) == year)
	for i in mini(25, class_now.size()):
		(class_now[class_now.size() - 1 - i] as Dictionary)["draft_year"] = year - 1
	while (_state.season.lists[club] as Array).size() >= 44:
		(_state.season.lists[club] as Array).pop_back()
	var guard := 0
	while _state.season.round_index < MD.DRAFT_AFTER and guard < 40:
		_state.advance()
		guard += 1
	if MD.waiting(_state):
		MD.close_carnival(_state)
		for card in _state.week_events:
			(card as Dictionary)["popped"] = true
		var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
		root.add_child(hub)
		await _frames(30)
		_lines(hub, "midseason")
		await _shot(out + "_midseason.png")
		hub.queue_free()
		await _frames(5)
	else:
		print("CAPTURE midseason: no pick waiting")

	# The League Draft: the board, then a player opened.
	_state.reset()
	_state.replay_seed = 2031
	_state.tutorials = false
	_state.draft = load("res://scripts/sim/Draft.gd").new(_db.all_players_sorted(),
			_db.active_clubs(2027).duplicate(), 12345)
	ui = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	ui.call("_on_club_chosen", club)
	await _frames(30)
	_lines(ui, "league")
	await _shot(out + "_league.png")
	var first := ui.find_children("Inspect_*", "Button", true, false)
	if not first.is_empty():
		ui.call("_open_player", str(first[0].name).trim_prefix("Inspect_"))
		await _frames(20)
		_lines(ui.find_child("PlayerDetail", true, false), "league open")
		await _shot(out + "_league_open.png")
	quit(0)
