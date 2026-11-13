extends SceneTree
## Row 142 first-slice captures (not committed): a 1990 career at a club on its
## real list, through the real flow. Looks: the year event in the feed (round 1),
## a 1990 match (pre-match and live), the 1990 ladder and fixture, the 1990
## draft with the real class, and the 1991 hub after the rollover.
##   godot --windowed --path . --script tools/visual/capture_legacy_season.gd -- --out DIR --club FIT [--only feed,match,ladder,rollover]

const W := 390
const H := 844
var out := "."
var only := ""
var state
var db


func _initialize() -> void:
	_run.call_deferred()


func _arg(name: String, fallback: String) -> String:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == name:
			return str(a[i + 1])
	return fallback


func _want(look: String) -> bool:
	return only == "" or look in only.split(",")


func _frames(n := 14) -> void:
	for i in range(n):
		await process_frame


func _shot(name: String) -> void:
	await _frames()
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png("%s/%s.png" % [out, name])
	print("wrote ", name)


func _reveal(node_name: String, nudge := 0) -> bool:
	var c: Control = root.find_child(node_name, true, false)
	if c == null:
		print("CAPTURE missing ", node_name)
		return false
	for sc in root.find_children("*", "ScrollContainer", true, false):
		if (sc as ScrollContainer).is_ancestor_of(c):
			(sc as ScrollContainer).ensure_control_visible(c)
			await _frames(2)
			(sc as ScrollContainer).scroll_vertical += nudge
	await _frames(6)
	return true


func _sim_weeks(n: int) -> void:
	for i in range(n):
		if state.season == null or state.season.round_index >= state.season.fixture.size():
			return
		state.sim_week()
		state.week_events = []


func _run() -> void:
	out = _arg("--out", out)
	only = _arg("--only", "")
	var club := _arg("--club", "FIT")
	DirAccess.make_dir_recursive_absolute(out)
	await process_frame
	state = root.get_node("GameState")
	db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_legacy_season.save"
	state.settings_path = "user://capture_legacy_season.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))

	state.reset("1990")
	state.career_seed = 1990
	state.replay_seed = 1990
	state.tutorials = false
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.interview_due = true
	state.begin_real_lists()
	state.choose_real_club(club)
	state.interview_due = false
	state.finish_intake_draft()
	print("CAPTURE year=%d club=%s clubs=%d rounds=%d" % [int(state.season_year), str(state.my_club),
			state.season.ladder_sorted().size(), state.season.fixture.size()])
	print("NEWS ", state.news.slice(0, 6))
	print("WEEK ", state.week_events.map(func(e): return str(e.get("year_event", e.get("id", "")))))

	# Look 6: the year event in the round 1 feed.
	if _want("feed"):
		var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
		root.add_child(hub)
		await _frames(240)
		await _shot("6_hub_r1")
		if await _reveal("NewsCard"):
			await _shot("6_hub_news")
		var more: Button = root.find_child("NewsMore", true, false)
		if more != null:
			more.emit_signal("pressed")
			await _frames(25)
			await _shot("6_news_feed")
		if await _reveal("WeekEvent"):
			await _shot("6_week_event")
		hub.queue_free()
		await _frames(4)
	state.week_events = []

	# Look 3: round 1's match, pre-match and live.
	if _want("match"):
		state.prepare_interactive_match()
		var s0 = state.pending_sim
		print("MATCH %s v %s at %s" % [str(s0.squads[0].code), str(s0.squads[1].code), str(s0.get("venue"))])
		var scene = load("res://scenes/MatchScene.tscn").instantiate()
		root.add_child(scene)
		await _frames(30)
		await _shot("3_pre_match")
		(scene.find_child("StartQuarter", true, false) as Button).emit_signal("pressed")
		await _frames(20)
		var pitch = scene.get("_pitch")
		pitch.set_speed(4.0)
		var guard := 0
		var shots := 0
		while guard < 8000 and shots < 2:
			guard += 1
			var mo = scene.get("_moment_overlay")
			if mo != null and is_instance_valid(mo) and not s0.pending_moment.is_empty():
				scene.call("_on_moment_choice", int(s0.pending_moment.get("default", 0)))
				await _frames(2)
				continue
			if scene.find_child("CoachBox", true, false) != null:
				break
			if pitch.playing:
				pitch._process(0.1)
			await process_frame
			var idx := int(scene.get("_playback_event_index"))
			if (shots == 0 and idx >= 40) or (shots == 1 and idx >= 110):
				await _frames(6)
				await _shot("3_live_%d" % shots)
				shots += 1
		scene.call("_on_skip")
		await _frames(40)
		await _shot("3_full_time")
		scene.queue_free()
		await _frames(4)
		state.week_events = []

	# Look 4: the ladder and the fixture, ten rounds in.
	if _want("ladder") or _want("rollover"):
		_sim_weeks(10 - int(state.season.round_index))
	if _want("ladder"):
		var StatsHub = load("res://scripts/ui/StatsHubScene.gd")
		for tab in ["ladder", "fixture"]:
			StatsHub.current = tab
			var sh: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
			root.add_child(sh)
			await _frames(30)
			await _shot("4_%s_r10" % tab)
			sh.queue_free()
			await _frames(4)

	# Look 5: the season out, the 1990 draft with the real class, then 1991.
	if _want("rollover"):
		var guard := 0
		while guard < 80 and state.season != null and not state.season.is_season_over():
			guard += 1
			if state.sim_week() == "none":
				break
			state.week_events = []
		print("SEASON_END round=%d premier=%s" % [int(state.season.round_index), str(state.get("last_premier"))])
		var StatsHub = load("res://scripts/ui/StatsHubScene.gd")
		StatsHub.current = "ladder"
		var sh: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
		root.add_child(sh)
		await _frames(30)
		await _shot("5_ladder_1990_final")
		sh.queue_free()
		await _frames(4)
		if not state.begin_intake_draft():
			print("CAPTURE no intake draft")
		var ds: Control = load("res://scenes/DraftScene.tscn").instantiate()
		root.add_child(ds)
		await _frames(30)
		await _shot("5_draft_1990")
		ds.queue_free()
		await _frames(4)
		var d = state.draft
		var g := 0
		while d != null and not d.is_finished() and g < 400:
			g += 1
			var c: Dictionary = d._best_ai_pick(d.current_club())
			if c.is_empty() or not d._draft_pick(d.current_club(), c):
				d._skip_current_pick()
		state.finish_intake_draft()
		print("ROLLED year=%d clubs=%d" % [int(state.season_year), state.season.ladder_sorted().size()])
		var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
		root.add_child(hub)
		await _frames(240)
		await _shot("5_hub_1991")
		if await _reveal("NewsCard"):
			await _shot("5_hub_1991_news")
		hub.queue_free()
		await _frames(4)
		var ls: Control = load("res://scenes/ListScene.tscn").instantiate()
		root.add_child(ls)
		await _frames(8)
		for t in ls.find_children("*", "Button", true, false):
			if (t as Button).text == "Full list":
				(t as Button).emit_signal("pressed")
				break
		await _frames(30)
		await _shot("5_list_1991")
	quit(0)
