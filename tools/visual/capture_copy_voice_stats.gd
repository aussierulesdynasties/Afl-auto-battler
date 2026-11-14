extends SceneTree
## Copy voice pass 10 (stats and menus, row 139; director 2026-11-10: option B) captures, phone
## portrait 390x844, a fresh Fremantle career that never touches a real save. One launch writes every
## state whose copy the pass changed, so the same script gives the before (on main) and the after:
##   godot --path . --script tools/visual/capture_copy_voice_stats.gd -- --out <prefix> [--only a,b]
## Writes <prefix>_<state>.png for: guide, guide_ball, guide_use, guide_scoring, guide_defence, guide_body, guide_ovr, guide_pot,
## guide_strengths, guide_traits, guide_injuries, guide_dev, options, options_sim, options_view,
## options_saves, list_shape, list_full, list_rookie, stats_intro, stats_ladder, stats_coach.

const CLUB := "FRE"
var _out := "copy_voice_stats"
var _only: PackedStringArray = []
var _state: Node
var _db: Node
var _router: Node


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			_out = str(a[i + 1])
		elif str(a[i]) == "--only":
			_only = str(a[i + 1]).split(",")
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_router = root.get_node("Router")
	_state.autosave_enabled = false
	_state.save_path = "user://capture_copy_voice_stats.save"
	_state.settings_path = "user://capture_copy_voice_stats.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(390, 844)
	DisplayServer.window_set_size(Vector2i(390, 844))
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	_fresh()

	# The stat guide: the tiles, then every page whose words changed.
	var guide_pages := {"guide_ball": "group0", "guide_use": "group1", "guide_scoring": "group2",
			"guide_defence": "group3", "guide_body": "group4",
			"guide_ovr": "topic0", "guide_pot": "topic1", "guide_strengths": "topic2", "guide_traits": "topic3",
			"guide_injuries": "topic4", "guide_dev": "topic5"}
	if _want("guide") or guide_pages.keys().any(func(k): return _want(k)):
		var host: Node = await _go("hub", "Hub")
		var guide_gd = load("res://scripts/ui/StatGuide.gd")
		var overlay: Control = guide_gd.show(host)
		await _frames(10)
		if _want("guide"):
			await _shot("guide")
		for k in guide_pages:
			if _want(k):
				guide_gd.open_page(overlay, guide_pages[k])
				await _frames(8)
				await _shot(k)
		overlay.queue_free()

	# Settings from the hub: the top, then scrolled to each changed row.
	var option_rows := {"options_sim": "SettingsSimConfirm", "options_view": "SettingsMatchFigures",
			"options_saves": "SettingsSaves"}
	if _want("options") or option_rows.keys().any(func(k): return _want(k)):
		var host: Node = await _go("hub", "Hub")
		var sheet: Control = load("res://scripts/ui/OptionsSheet.gd").open(host, true)
		await _frames(10)
		if _want("options"):
			await _shot("options")
		for k in option_rows:
			if not _want(k):
				continue
			var row: Control = sheet.find_child(option_rows[k], true, false)
			if row == null and k == "options_saves":
				row = _label_holding(sheet, "career saves")
			await _scroll_to(row)
			await _shot(k)
		sheet.queue_free()

	# My list: the shape (its note), the full list (the rookie spots), a rookie's upgrade.
	if _want("list_shape") or _want("list_full") or _want("list_rookie"):
		var scene: Node = await _go("list", "ListScene")
		if _want("list_shape"):
			await _shot("list_shape")
		scene.set("_pane", "list")
		scene.call("_show_pane")
		await _frames(10)
		if _want("list_full"):
			await _scroll_to(scene.find_child("CatBListWhy", true, false) if scene.find_child("CatBListWhy", true, false) != null
					else _label_holding(scene, "Rookie list"))
			await _shot("list_full")
		if _want("list_rookie"):
			# A fresh Fremantle list has no rookies: put its youngest on the rookie list for the frame.
			var rook := ""
			var young := 99.0
			for p in _state.my_list:
				if float(p.get("age", 99.0)) < young:
					young = float(p.get("age", 99.0))
					rook = str(p["id"])
			for p in _state.my_list:
				if str(p["id"]) == rook:
					p["rookie_list"] = "A"
			if rook != "":
				scene.call("_open_profile", rook)
				await _frames(12)
				var b := _label_holding(scene, "senior minimum")
				if b != null:
					await _scroll_to(b)
				await _shot("list_rookie")

	# Season stats: the first-visit intro, the ladder's filters, the coach's record.
	if _want("stats_intro") or _want("stats_ladder") or _want("stats_coach"):
		var hub_gd = load("res://scripts/ui/StatsHubScene.gd")
		hub_gd.current = "ladder"
		var scene: Node = await _go("stats", "StatsHub")
		if _want("stats_intro"):
			scene.call("_show_intro")
			await _frames(10)
			await _shot("stats_intro")
			var intro: Node = root.find_child("SeasonStatsIntro", true, false)
			if intro != null:
				intro.queue_free()
			await _frames(4)
		if _want("stats_ladder"):
			await _shot("stats_ladder")
		if _want("stats_coach"):
			hub_gd.current = "coach"
			scene = await _go("stats", "StatsHub")
			await _shot("stats_coach")

	quit()


func _want(state: String) -> bool:
	return _only.is_empty() or _only.has(state)


func _fresh() -> void:
	_state.reset()
	_state.career_seed = 4402
	_state.replay_seed = 4402
	_state.start_season(CLUB, _db.club_list(CLUB))
	_state.tutorials = false
	_state.week_events = []


## Opens `route` from the main menu and waits for the scene whose path holds `scene`.
func _go(route: String, scene: String) -> Node:
	_router.stack = []
	_router.go("main")
	var guard := 0
	while not _on("Main") and guard < 600:
		await process_frame
		guard += 1
	_router.go("hub")
	guard = 0
	while not _on("Hub") and guard < 600:
		await process_frame
		guard += 1
	await _frames(20)
	for i in range(3):
		for b in root.find_children("*", "Button", true, false):
			if (b as Button).is_visible_in_tree() and (b as Button).text in ["Got it", "Later"]:
				(b as Button).emit_signal("pressed")
		await _frames(8)
	if route != "hub":
		_router.go(route)
		guard = 0
		while not _on(scene) and guard < 600:
			await process_frame
			guard += 1
		await _frames(30)
	return current_scene


## The first visible Label whose text holds `part`.
func _label_holding(under: Node, part: String) -> Control:
	for l in under.find_children("*", "Label", true, false):
		if (l as Label).is_visible_in_tree() and (l as Label).text.contains(part):
			return l
	return null


func _scroll_to(c: Control) -> void:
	if c == null:
		return
	var sc := c.get_parent()
	while sc != null and not (sc is ScrollContainer):
		sc = sc.get_parent()
	if sc != null:
		await _frames(4)
		(sc as ScrollContainer).scroll_vertical = int(c.global_position.y - (sc as ScrollContainer).global_position.y
				+ (sc as ScrollContainer).scroll_vertical - 120.0)
	await _frames(6)


func _on(scene: String) -> bool:
	return current_scene != null and current_scene.scene_file_path.contains(scene)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


## Frames, not frame_post_draw: a still screen (the ladder) draws no new frame, so that signal never comes.
func _shot(name: String) -> void:
	await _frames(4)
	var img := root.get_viewport().get_texture().get_image()
	img.save_png("%s_%s.png" % [_out, name])
	print("wrote %s_%s.png" % [_out, name])
