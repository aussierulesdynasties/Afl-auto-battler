extends SceneTree
## Review capture for row 122 (a page for every club, the honour board), dark.
## Needs a real renderer and a window (keep it off screen with an override.cfg):
##   godot --path . --script tools/visual/capture_club_page.gd -- --size 390x844 --out <prefix>
## Fremantle (--club), six rounds played, two players gone with a place on the board (a
## 160-gamer traded to Melbourne, a best and fairest winner who has retired).
## Opens each sheet by its handler (the real taps are proven in
## tests/run_clublink_tests.gd and run_stats_tests.gd). Writes <out>_rival.png and
## <out>_rival_lower.png (a rival's page), <out>_mine.png (your club's page),
## <out>_board.png (the honour board) and <out>_facts.png (a retired player's
## career facts) and <out>_news.png (the news front page). Never touches a real save.

var _w := 390
var _h := 844
## Your club (--club, default Fremantle).
var _club := "FRE"
## The rival whose page is shot (--rival; default the top of the ladder).
var _rival := ""


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


func _run() -> void:
	var out := "club_page"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--club":
				_club = str(a[i + 1])
			"--rival":
				_rival = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
	await process_frame
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	var HB = load("res://scripts/sim/HonourBoard.gd")
	var CP = load("res://scripts/ui/ClubPage.gd")
	var Car = load("res://scripts/sim/Career.gd")
	gs.autosave_enabled = false
	gs.save_path = "user://capture_club_page.save"
	gs.settings_path = "user://capture_club_page.cfg"
	UK.apply_appearance("dark")
	if _w >= 760:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_size(Vector2i(_w, _h))
		await _frames(10)
		var factor := float(_w) / maxf(1.0, root.get_visible_rect().size.x)
		if factor > 1.05:
			DisplayServer.window_set_size(Vector2i(int(_w * factor), int(_h * factor)))
			await _frames(10)
	else:
		root.size = Vector2i(_w, _h)
		DisplayServer.window_set_size(Vector2i(_w, _h))
	gs.reset()
	gs.set_setting("seen_season_stats_intro", true)
	gs.career_seed = 2026
	gs.replay_seed = 2026
	gs.start_season(_club, db.club_list(_club))
	for i in range(6):
		gs.advance()
	# Two players gone with a place on the board.
	var y := int(gs.season_year)
	var big: Dictionary = gs.my_list[3]
	var c: Dictionary = Car.fresh()
	c["stints"] = [[_club, y - 9, y, 168, 211]]
	c["through"] = y
	big["career"] = c
	HB.upsert(gs, big)
	gs.my_list.erase(big)
	if gs.season.lists[gs.my_club] != gs.my_list:
		(gs.season.lists[gs.my_club] as Array).erase(big)
	big["club"] = "MEL"
	(gs.season.lists["MEL"] as Array).append(big)
	HB.sweep(gs)
	gs.honour_roll.append({"year": y - 1, "my_club": _club, "premier": "",
			"my_bf": [{"id": "ghost1", "name": "Jack Hartley"}],
			"brownlow": [{"id": "ghost1", "name": "Jack Hartley", "club": _club}]})
	gs.departed_names["ghost1"] = {"generic_name": "Jack Hartley", "year": y - 1}
	HB.backfill(gs, func(id: String) -> Dictionary: return gs._any_player(id))

	load("res://scripts/ui/StatsHubScene.gd").current = "ladder"
	var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(s)
	current_scene = s
	await _frames(12)
	var rival := _rival
	for r in ([] if rival != "" else gs.season.ladder_sorted()):
		if str(r["code"]) != _club:
			rival = str(r["code"])
			break
	var CL = load("res://scripts/ui/ClubLink.gd")
	CL.open(s.find_child("Club_" + rival, true, false), rival)
	await _frames(12)
	print("rival page ", rival)
	var page: Node = s.find_child("ClubPage", true, false)
	await _shot(out, "rival")
	var sc: ScrollContainer = page.find_child("*Scroll*", true, false) as ScrollContainer if page != null else null
	if sc == null and page != null:
		for n in page.find_children("*", "ScrollContainer", true, false):
			sc = n
			break
	if sc != null:
		sc.scroll_vertical = 100000
		await _frames(8)
		await _shot(out, "rival_lower")
	var close: Node = page.find_child("CloseClub", true, false) if page != null else null
	if close != null:
		(close as Button).emit_signal("pressed")
		await _frames(10)
	CL.open(s.find_child("Club_" + _club, true, false), _club)
	await _frames(12)
	page = s.find_child("ClubPage", true, false)
	await _shot(out, "mine")
	var hb_btn: Node = page.find_child("HonourBoardButton", true, false) if page != null else null
	if hb_btn != null:
		(hb_btn as Button).emit_signal("pressed")
		await _frames(12)
	await _shot(out, "board")
	var board: Node = s.find_child(CP.BOARD_NAME, true, false)
	var ghost: Node = board.find_child("Board_ghost1", true, false) if board != null else null
	var bh: Node = board.find_child("BoardHead", true, false) if board != null else null
	if bh != null:
		var parts := []
		for l in bh.find_children("*", "Label", true, false):
			parts.append("%s=%.0f" % [(l as Label).text, (l as Control).size.x])
		print("tap board head right %.0f view %.0f %s" % [(bh as Control).get_global_rect().end.x, s.size.x, " ".join(parts)])
	if ghost != null:
		CP.open_row(s, gs.honour_board["ghost1"])
		await _frames(12)
		print("facts open ", s.find_child(CP.FACTS_NAME, true, false) != null)
	await _shot(out, "facts")
	# Club names in the news are tappable now: the front page, opened by its handler.
	s.queue_free()
	await _frames(4)
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	current_scene = hub
	await _frames(12)
	if not gs.news.is_empty():
		hub._show_news()
		await _frames(12)
	await _shot(out, "news")
	quit(0)
