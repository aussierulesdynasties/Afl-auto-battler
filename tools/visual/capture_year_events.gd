extends SceneTree
## Legacy L10 for the director's look, on a phone: the New career setup with
## the Controversies switch, and year-event cards on the hub of a 1990 career.
## Seeded; never touches a real save.
##   godot --path . --script tools/visual/capture_year_events.gd -- --out PREFIX \
##       [--events bears_owner_collapse,supplements_saga] [--size 390x844]
## Writes <prefix>_setup.png and <prefix>_<event>.png.

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String) -> void:
	await _frames(30)
	root.get_viewport().get_texture().get_image().save_png(path)
	print("wrote ", path)


func _run() -> void:
	var out := "year"
	var ids := "bears_owner_collapse,supplements_saga"
	var cli := OS.get_cmdline_user_args()
	for i in range(cli.size() - 1):
		match str(cli[i]):
			"--out": out = str(cli[i + 1])
			"--events": ids = str(cli[i + 1])
			"--size":
				var wh := str(cli[i + 1]).split("x")
				W = int(wh[0])
				H = int(wh[1])
	await process_frame
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	gs.autosave_enabled = false
	gs.save_path = "user://capture_year.save"
	gs.settings_path = "user://capture_year.cfg"
	for k in ["seen_training_intro", "seen_season_stats_intro", "seen_weekly_loop_intro"]:
		gs.set_setting(k, true)
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	await _frames(10)
	var layout = root.get_node("ScreenLayout")
	layout.ui_scale = 1.0 / maxf(1.0, layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0))
	layout._update_scale()
	await _frames(10)
	print("canvas ", root.get_visible_rect().size)

	# The setup, scrolled to the switch.
	var main: Control = load("res://scenes/Main.tscn").instantiate()
	root.add_child(main)
	await _frames(30)
	main.find_child("NewCareer", true, false).emit_signal("pressed")
	await _frames(30)
	var row = main.find_child("Controversies_on", true, false)
	if row == null:
		push_error("capture_year_events: no Controversies switch")
	else:
		var n: Node = row.get_parent()
		while n != null and not (n is ScrollContainer):
			n = n.get_parent()
		if n != null:
			await _frames(5)
			(n as ScrollContainer).ensure_control_visible(row)
	await _shot("%s_setup.png" % out)
	main.queue_free()
	await _frames(5)

	# Each event's card, in its own club's career, in its own season.
	for id in ids.split(","):
		var e := {}
		for x in YearEvents.all():
			if str(x["id"]) == id:
				e = x
		if e.is_empty() or not e.has("card"):
			push_error("capture_year_events: no card for %s" % id)
			continue
		var club := str((e["clubs"] as Array)[0])
		gs.set_setting("controversies", true)
		gs.reset("1990")
		gs.career_seed = 1990
		gs.replay_seed = 1990
		gs.start_season(club, db.club_list(club))
		gs.season_year = int(e["season"])
		gs.season.round_index = mini(int(e.get("round", 0)), gs.season.fixture.size())
		var cards := YearEvents.week(gs)
		var card := {}
		for c in cards:
			if str(c.get("year_event", "")) == id:
				card = c
		if card.is_empty():
			push_error("capture_year_events: %s gave no card" % id)
			continue
		gs.week_events = [card]
		var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
		root.add_child(hub)
		await _frames(60)
		var w = hub.find_child("WeekEvent", true, false)
		if w != null:
			var n: Node = w.get_parent()
			while n != null and not (n is ScrollContainer):
				n = n.get_parent()
			if n != null:
				(n as ScrollContainer).ensure_control_visible(w)
		await _shot("%s_%s.png" % [out, id])
		hub.queue_free()
		await _frames(5)
	quit()
