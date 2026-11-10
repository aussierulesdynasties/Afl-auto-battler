extends SceneTree
## Review capture for row T3.R43, dark, phone: the hub's top bar with Search,
## the search sheet (a typed name, then the shortlist), a football word's rule
## sheet, the "When I sim the week" sheet (top and bottom), its Coaching
## section, the Sim the week question with the orders, and a week stopped on a
## card. Needs a real renderer:
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_nav_economy.gd
## On GitHub: gh workflow run capture.yml --ref <branch> -f tool=capture_nav_economy
## (it passes "-- --out <dir>"). Environment: CAP_DIR (folder for the pngs, default "."), CAP_CLUB (default
## "MEL"), CAP_W / CAP_H (default 390 x 844). Never touches a real save.


func _initialize() -> void:
	_run.call_deferred()


func _frames(n := 8) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String) -> void:
	await _frames()
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)


func _env(key: String, fallback: String) -> String:
	return OS.get_environment(key) if OS.get_environment(key) != "" else fallback


func _scroll_to(scene: Node, target: Control, above := 70) -> void:
	for b in scene.find_children("*", "ScrollContainer", true, false):
		var box := b as ScrollContainer
		if box.is_visible_in_tree() and box.is_ancestor_of(target):
			box.scroll_vertical = maxi(0, int(target.global_position.y - box.global_position.y) - above + box.scroll_vertical)
	await _frames()


func _scroll_end(node: Node) -> void:
	for b in node.find_children("*", "ScrollContainer", true, false):
		var box := b as ScrollContainer
		box.scroll_vertical = 100000
	await _frames()


func _hub() -> Node:
	var hub = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(12)
	return hub


func _gone(n: Node) -> void:
	n.queue_free()
	await _frames(2)


func _run() -> void:
	var dir := _env("CAP_DIR", ".")
	var args := OS.get_cmdline_user_args()
	var at := args.find("--out")
	if at >= 0 and at + 1 < args.size():
		dir = args[at + 1]
	var club := _env("CAP_CLUB", "MEL")
	var size := Vector2i(int(_env("CAP_W", "390")), int(_env("CAP_H", "844")))
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	var HS = load("res://scripts/ui/HubSearch.gd")
	var FW = load("res://scripts/ui/FootballWords.gd")
	var SOS = load("res://scripts/ui/SimOrdersSheet.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_nav_economy.save"
	state.settings_path = "user://capture_nav_economy.cfg"
	state.reset()
	state.career_seed = 2026
	state.replay_seed = 2026
	for k in ["seen_training_intro", "seen_weekly_loop_intro", "seen_coaching_intro"]:
		state.set_setting(k, true)
	state.start_season(club, db.club_list(club))
	for i in range(3):
		state.skip_media_conference()
		state.advance()
	state.skip_media_conference()
	state.week_events = []
	UK.apply_appearance("dark")
	root.size = size
	DisplayServer.window_set_size(size)
	var bg := ColorRect.new()
	bg.color = UK.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)

	# The hub's top bar: Search beside Settings.
	var hub = await _hub()
	await _shot("%s/nav_hub_top.png" % dir)
	# Search: a surname typed (a name found at more than one club, if any).
	var p: Dictionary = state.season.lists["GEE"][3]
	var surname := str(p["name"]).get_slice(" ", str(p["name"]).get_slice_count(" ") - 1)
	print("search: ", surname, " -> ", (HS.matches(surname) as Array).size(), " found")
	state.toggle_shortlist(str(state.season.lists["SYD"][2]["id"]))
	state.toggle_shortlist("club:FRE")
	HS.open(hub, surname)
	await _frames(8)
	await _shot("%s/nav_search_typed.png" % dir)
	HS.close_open(hub)
	await _frames(2)
	HS.open(hub, "")
	await _frames(8)
	await _shot("%s/nav_search_shortlist.png" % dir)
	HS.close_open(hub)
	await _frames(2)
	# A football word held: its rule.
	var words: Dictionary = FW.entries()
	var word := ""
	for k in words:
		if str(words[k]["kind"]) != "Rating":
			word = str(k)
			break
	print("word: ", word, " (", str(words[word]["kind"]) if word != "" else "none", ")")
	FW.open(hub, [word])
	await _frames(8)
	await _shot("%s/nav_word_rule.png" % dir)
	FW.close_open(hub)
	await _frames(2)
	# When I sim the week: the sheet, top and bottom.
	state.set_sim_order("questions", "ask")
	var sheet: Control = SOS.open(hub)
	await _frames(8)
	await _shot("%s/nav_orders_top.png" % dir)
	await _scroll_end(sheet)
	await _shot("%s/nav_orders_end.png" % dir)
	SOS.close_open(hub)
	await _frames(2)
	# A card waiting and "Ask me": Sim the week stops on it.
	var card: Dictionary = state.story_card("training_extra_session")
	card["popped"] = true
	state.week_events = [card]
	hub.call("_on_sim_round_pressed")
	await _frames(10)
	await _shot("%s/nav_orders_stop.png" % dir)
	await _gone(hub)
	# No card, and the question before the sim: the orders under it.
	state.week_events = []
	state.set_sim_order("questions", "usual")
	state.set_setting("confirm_sim_round", true)
	hub = await _hub()
	hub.call("_on_sim_round_pressed")
	await _frames(10)
	print("sim confirm: ", hub.find_child("SimConfirm", true, false) != null)
	await _shot("%s/nav_sim_confirm.png" % dir)
	await _gone(hub)
	# Coaching: the section.
	var cs = load("res://scenes/CoachingScene.tscn").instantiate()
	root.add_child(cs)
	await _frames(12)
	var sec: Control = cs.find_child("SimOrdersSection", true, false)
	if sec != null:
		await _scroll_to(cs, sec, 40)
	await _shot("%s/nav_coaching_orders.png" % dir)
	quit()
