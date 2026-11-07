extends SceneTree
## Visual review tool for a club's trophies, opened from its club page (rulings
## 118, 118a; moved from Season stats 2026-11-06). Needs a real renderer;
## capture.yml runs it:
##   gh workflow run capture.yml --ref <branch> -f tool=capture_trophies \
##       -f args="--size 390x844"
## A fresh Collingwood career plays its first season out, then the honour roll
## is seeded so every shelf has something on it: that season made a
## premiership (with a Brownlow and an All-Australian), plus an older season
## from before the room recorded records and All-Australians. Writes
## <out>_empty.png (before the first game), <out>_page.png (your club's page at
## its Trophies link), <out>.png, <out>_lower.png (scrolled to your seasons),
## <out>_flag.png and <out>_medal.png (the sheets), <out>_filtered.png (the
## All-Australians alone), <out>_rival_page.png and <out>_rival.png (--rival's
## page and trophies) and <out>_stats.png (Season stats, its tabs).
##   --size WxH   window size (default 390x844)    --light   light appearance
##   --club CODE  the club to coach (default COL; use a coloured club for a look)
##   --history    show a stand-in "Before you" row for that club (fixture, not data)
##   --rival CODE another club to show (default GWS, which has won nothing)
## Never touches a real save.

var _w := 390
var _h := 844
var _club := "COL"
var _rival := "GWS"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "trophies"
	var mode := "dark"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
			"--light":
				mode = "light"
			"--club":
				_club = str(a[i + 1])
			"--rival":
				_rival = str(a[i + 1])
			"--history":
				# A stand-in table, to see the "Before you" row (not real data).
				var fake := {}
				fake[_club] = {"years": [1896, 1902, 1910, 1917, 1919, 1927, 1928, 1930, 1935, 1936, 1953, 1958, 1990, 2010, 2023],
						"comps": {}, "none": false}
				ClubHistory.use(fake)
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_trophies.save"
	state.settings_path = "user://capture_trophies.cfg"
	state.reset()
	state.career_seed = 2031
	state.replay_seed = 2031
	state.start_season(_club, db.club_list(_club))
	# The hub's first-visit note would sit over the room.
	state.set_setting("seen_season_stats_intro", true)
	UK.apply_appearance(mode)
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	var hub_script = load("res://scripts/ui/StatsHubScene.gd")
	hub_script.current = "ladder"
	var scene: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(scene)
	await _frames(10)
	load("res://scripts/ui/ClubPage.gd").open_trophies(scene, _club)
	await _frames(10)
	_save(out + "_empty.png")
	scene.queue_free()
	await _frames(2)
	var guard := 0
	while not state.season_is_over() and guard < 40:
		state.advance()
		guard += 1
	var year: int = state.season_year
	var entry: Dictionary = state.honour_roll.back()
	var ids := []
	for p in state.season.lists[_club]:
		ids.append(str(p["id"]))
	entry["premier"] = _club
	entry["runner_up"] = "CAR"
	entry["my_position"] = 1
	# A record that fits a minor premier (the season played may not).
	entry["my_record"] = "18-5-0"
	entry["brownlow"] = [{"id": ids[0], "club": _club, "votes": 31}]
	entry["my_aa"] = [ids[0], ids[2]]
	var old := {"year": year - 1, "my_club": _club, "premier": "GEE", "runner_up": _club, "my_position": 3,
		"brownlow": [], "coleman": [{"id": ids[4], "club": _club, "goals": 71}], "rising_star": [],
		"coaches_award": [], "my_bf": [{"id": ids[0], "club": _club, "bf": 120}]}
	state.honour_roll = [old, entry]
	scene = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(scene)
	await _frames(10)
	_save(out + "_stats.png")
	load("res://scripts/ui/ClubLink.gd").open(scene, _club)
	await _frames(10)
	await _show(scene.find_child("TrophiesLink", true, false))
	_save(out + "_page.png")
	await _tap(scene, "TrophiesLink")
	_save(out + ".png")
	var t: Control = scene.find_child("Tenure", true, false)
	var sc: ScrollContainer = _scroller(t)
	if sc != null and t != null:
		sc.scroll_vertical = int(t.global_position.y - sc.global_position.y) + sc.scroll_vertical
		await _frames(6)
		_save(out + "_lower.png")
		sc.scroll_vertical = 0
		await _frames(4)
	await _tap(scene, "Club_premiership_%d" % year)
	_save(out + "_flag.png")
	scene.call("handle_back")
	await _frames(6)
	await _tap(scene, "Honour_brownlow_%d" % year)
	_save(out + "_medal.png")
	scene.call("handle_back")
	await _frames(6)
	# One kind of honour: the All-Australians alone, under each player.
	var opt: OptionButton = scene.find_child("AwardFilter", true, false)
	if opt != null:
		for i in range(opt.item_count):
			if opt.get_item_text(i) == "All-Australian":
				opt.select(i)
				opt.item_selected.emit(i)
		await _frames(10)
		_save(out + "_filtered.png")
		load("res://scripts/ui/ClubTrophies.gd").award_filter = ""
	# A rival's page and its trophies: only what the season records for it.
	scene.queue_free()
	await _frames(2)
	scene = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(scene)
	await _frames(10)
	load("res://scripts/ui/ClubLink.gd").open(scene, _rival)
	await _frames(10)
	await _show(scene.find_child("TrophiesLink", true, false))
	_save(out + "_rival_page.png")
	await _tap(scene, "TrophiesLink")
	_save(out + "_rival.png")
	quit()


## The scroll a node sits in, if any.
func _scroller(n: Node) -> ScrollContainer:
	var at: Node = n.get_parent() if n != null else null
	while at != null and not (at is ScrollContainer):
		at = at.get_parent()
	return at as ScrollContainer


## Scroll n into view in its scroll.
func _show(n: Control) -> void:
	var sc := _scroller(n)
	if sc != null:
		sc.ensure_control_visible(n)
		await _frames(6)


func _tap(scene: Node, node_name: String) -> void:
	var b: Button = scene.find_child(node_name, true, false)
	if b == null:
		push_error("no " + node_name)
		return
	b.emit_signal("pressed")
	await _frames(10)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
