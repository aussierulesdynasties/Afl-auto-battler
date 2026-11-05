extends SceneTree
## Real renderer: godot --path . --rendering-method gl_compatibility --script tools/visual/capture_sir_doug.gd
## Environment: CAP_CLUB (default ESS), CAP_W, CAP_H (default 390x844), CAP_OUT (file prefix).
## Row 75, switch sir_doug_round. Saves <prefix>_hub.png (your match card in the
## round's week), <prefix>_fixture.png (Round 11 on the fixture) and, when the
## seeded fixture has byes in Round 11, <prefix>_fixture_after_bye.png (Round 12).
## Picks the first season seed from 1 whose Round 11 has byes. Never touches a real save.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	Features.set_on("sir_doug_round", true)
	state.autosave_enabled = false
	state.save_path = "user://capture_sir_doug.save"
	state.settings_path = "user://capture_sir_doug.cfg"
	state.show_real_names = false
	db.reload()
	var club := OS.get_environment("CAP_CLUB") if OS.get_environment("CAP_CLUB") != "" else "ESS"
	var w := int(OS.get_environment("CAP_W")) if OS.get_environment("CAP_W") != "" else 390
	var h := int(OS.get_environment("CAP_H")) if OS.get_environment("CAP_H") != "" else 844
	var prefix := OS.get_environment("CAP_OUT") if OS.get_environment("CAP_OUT") != "" else "sir_doug"
	DisplayServer.window_set_size(Vector2i(w, h))
	root.size = Vector2i(w, h)
	var seed_used := 0
	for sd in range(1, 41):
		state.reset()
		state.replay_seed = sd
		state.start_season(club, db.club_list(club))
		seed_used = sd
		if not SirDougRound.byes_in(state.season, SirDougRound.ROUND).is_empty():
			break
	state.set_setting("seen_weekly_loop_intro", true)
	state.tutorials = false
	var r := SirDougRound.round_of(state)
	state.season.round_index = SirDougRound.round_for(state, club)
	router.go("hub")
	for i in range(45):
		await process_frame
	var card: Control = current_scene.find_child("SirDougBlurb", true, false)
	if card != null:
		var sc := _scroll_of(card)
		if sc != null:
			sc.ensure_control_visible(card)
	for i in range(6):
		await process_frame
	await _drawn()
	root.get_texture().get_image().save_png(prefix + "_hub.png")
	var fix = load("res://scripts/ui/stats/StatsFixture.gd")
	load("res://scripts/ui/StatsHubScene.gd").current = "fixture"
	for page in [r, r + 1]:
		var late := SirDougRound.after_bye(state, page)
		if page != r and late.is_empty():
			continue
		fix.reset()
		fix._stamp = "%d/%d/%d" % [state.season.round_index, 0, 0]
		fix._page = page
		router.go("stats")
		for i in range(45):
			await process_frame
		await _drawn()
		root.get_texture().get_image().save_png(prefix + ("_fixture.png" if page == r else "_fixture_after_bye.png"))
	print("CAPTURE saved ", prefix, " at ", w, "x", h, " seed ", seed_used, " byes in round 11: ",
			SirDougRound.byes_in(state.season, r))
	quit()


func _scroll_of(n: Node) -> ScrollContainer:
	var p := n.get_parent()
	while p != null:
		if p is ScrollContainer:
			return p
		p = p.get_parent()
	return null


## A frame that has been drawn. frame_post_draw never fires when the window is
## covered, so a short timer backs it up and the capture cannot hang.
func _drawn() -> void:
	var done := [false]
	var mark := func(): done[0] = true
	RenderingServer.frame_post_draw.connect(mark, CONNECT_ONE_SHOT)
	var t := create_timer(1.0)
	while not done[0] and t.time_left > 0.0:
		await process_frame
