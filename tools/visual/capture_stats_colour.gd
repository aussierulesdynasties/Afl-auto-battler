extends SceneTree
## The club line's colour on Season stats (director, 2026-11-06), for his look.
## Needs a real renderer:
##   godot --path . --script tools/visual/capture_stats_colour.gd -- --out /tmp/sc [--size 390x844] [--club COL]
## A fresh career at --club (default Collingwood) plays three rounds. Writes
## <out>_players.png (the Players list by disposals), <out>_players_goals.png
## (by goals), <out>_players_mine.png (your own club's rows, on their tint),
## <out>_swatches.png (every club's code line as a rival's row on PANEL_ALT and
## as your own tinted row, with its worst contrast) and
## <out>_trophies.png (your seasons, this one at "Round 3 of 24").
## Never touches a real save.

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "/tmp/sc"
	var club := "COL"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		var v := str(a[i + 1]) if i + 1 < a.size() else ""
		match str(a[i]):
			"--out": out = v
			"--club": club = v
			"--size":
				W = int(v.split("x")[0])
				H = int(v.split("x")[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_stats_colour.save"
	state.settings_path = "user://capture_stats_colour.cfg"
	state.replay_seed = 2031
	state.reset()
	state.set_setting("seen_season_stats_intro", true)
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	state.start_season(club, db.club_list(club))
	for r in range(3):
		state.advance()
	var sp = load("res://scripts/ui/stats/StatsPlayers.gd")
	var hub = load("res://scripts/ui/StatsHubScene.gd")
	for pass_ in [["disposals", "_players.png", ""], ["goals", "_players_goals.png", ""],
			["disposals", "_players_mine.png", club]]:
		sp.reset_view()
		sp.reset_filters()
		sp.pick_group(str(pass_[0]))
		if str(pass_[2]) != "":
			sp.set_filter("club", str(pass_[2]))
		hub.current = "players"
		var ui: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
		root.add_child(ui)
		await _frames(12)
		_save(out + str(pass_[1]))
		ui.queue_free()
		await _frames(2)
	# Every club's code line, as the Players row sets it, rival and own.
	var strip := _swatches(UK, db)
	root.add_child(strip)
	await _frames(6)
	_save(out + "_swatches.png")
	strip.queue_free()
	await _frames(2)
	hub.current = "trophies"
	var t_ui: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(t_ui)
	await _frames(10)
	var sc: ScrollContainer = t_ui.find_child("StatsScroll", true, false)
	var t: Control = t_ui.find_child("Tenure", true, false)
	if sc != null and t != null:
		sc.scroll_vertical = int(t.global_position.y - sc.global_position.y) + sc.scroll_vertical - 40
		await _frames(6)
	_save(out + "_trophies.png")
	quit()


func _swatches(UK, db) -> Control:
	var SS = load("res://scripts/ui/stats/StatsSide.gd")
	var state = root.get_node("GameState")
	var was: String = state.my_club
	var bg := ColorRect.new()
	bg.color = UK.BG
	bg.size = Vector2(W, H)
	var v := GridContainer.new()
	v.columns = 2
	v.position = Vector2(16, 8)
	v.add_theme_constant_override("h_separation", 0)
	v.add_theme_constant_override("v_separation", 0)
	bg.add_child(v)
	var codes := ["ADE", "BRL", "CAR", "COL", "ESS", "FRE", "GEE", "GCS", "GWS", "HAW", "MEL", "NTH",
			"PAD", "RIC", "STK", "SYD", "WCE", "WBD", "TAS", "CANB"]
	# Left: a rival's row on the lightest page surface (PANEL_ALT). Right: the
	# same club as your own row, on its tint. Each with its worst contrast.
	for code in codes:
		for own in [false, true]:
			state.my_club = code if own else ("CAR" if code == "COL" else "COL")
			var c: Color = SS.code_ink(code)
			var row := PanelContainer.new()
			var flat := StyleBoxFlat.new()
			flat.bg_color = UK.BG.lerp(UK.club_vivid(code), 0.22) if own else UK.PANEL_ALT
			flat.content_margin_left = 8
			flat.content_margin_right = 8
			row.add_theme_stylebox_override("panel", flat)
			row.custom_minimum_size = Vector2((W - 32) / 2.0, 0)
			row.clip_contents = true
			var h := HBoxContainer.new()
			h.add_theme_constant_override("separation", 6)
			row.add_child(h)
			h.add_child(UK.club_marker(code, 18.0))
			var who := VBoxContainer.new()
			who.add_theme_constant_override("separation", 0)
			who.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			h.add_child(who)
			who.add_child(UK.line("%s · %s" % [code, "your row" if own else "3 games"], UK.SECONDARY, c))
			who.add_child(UK.line("#%s  %.1f:1" % [c.to_html(false).to_upper(), UK.min_contrast(c, SS.row_surfaces(code))], UK.FINE, UK.MUTED))
			v.add_child(row)
	state.my_club = was
	return bg


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
