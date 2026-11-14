extends SceneTree
## Team selection (the team builder), for the director's look. Needs a real
## renderer:
##   godot --path . --script tools/visual/capture_selection.gd -- --out /tmp/sel [--size 1280x720] [--picked]
## --picked: one player tapped, waiting for the second tap. --opp: the oval
## flipped to this week's opponent. --guide: the synergy guide with Complete.
## --report: the assistant's report. --rounds N: play N rounds first.
## --oval: (old) scrolled down to the oval. --drag: mid-drag, the centre's token
## pressed and moved by real mouse events (the name preview under the pointer).
## --strategy KEY: that auto-pick applied, scrolled to its note (BuilderHint).
## --list: the first-visit card already seen, so the players not picked show.
## --profile: the centre's profile open. --loads: three players given set
## loads and moods (row 183's states). --club CODE. --window WxH: the W x H canvas drawn into a window this big
## (960x540 at 1920x1080, as a PC at 200%). (The phone's week is the match preview now:
## tools/visual/capture_match_preview.gd.)
## Writes <out>_sheet.png.

var W := 1280
var H := 720
var WIN := Vector2i.ZERO


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "/tmp/sel"
	var picked := false
	var drag := false
	var oval := false
	var mode := ""
	var club := "COL"
	var page := ""
	var rounds := 0
	var vs := ""
	var strategy := ""
	var list_view := false
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		if str(a[i]) == "--out" and i + 1 < a.size():
			out = str(a[i + 1])
		if str(a[i]) == "--size" and i + 1 < a.size():
			var wh := str(a[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
		if str(a[i]) == "--window" and i + 1 < a.size():
			var ww := str(a[i + 1]).split("x")
			WIN = Vector2i(int(ww[0]), int(ww[1]))
		if str(a[i]) == "--club" and i + 1 < a.size():
			club = str(a[i + 1])
		if str(a[i]) == "--page" and i + 1 < a.size():
			page = str(a[i + 1])
		if str(a[i]) == "--rounds" and i + 1 < a.size():
			rounds = int(a[i + 1])
		if str(a[i]) == "--vs" and i + 1 < a.size():
			vs = str(a[i + 1])
		if str(a[i]) == "--strategy" and i + 1 < a.size():
			strategy = str(a[i + 1])
		if str(a[i]) == "--picked":
			picked = true
		if str(a[i]) == "--list":
			list_view = true
		if str(a[i]) == "--oval":
			oval = true
		if str(a[i]) == "--drag":
			drag = true
		if str(a[i]) in ["--opp", "--guide", "--report"]:
			mode = str(a[i]).trim_prefix("--")
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	state.reset()
	# The window is sized so the UI has exactly W x H units, whatever this
	# screen's DPI scale is (ScreenLayout divides the window by it).
	var px := WIN if WIN != Vector2i.ZERO else Vector2i(W, H)
	root.size = px
	DisplayServer.window_set_size(px)
	# One unit is one pixel, as on a phone's reference size (not this PC's DPI);
	# with --window, one unit is window/canvas pixels.
	var sl = root.get_node("ScreenLayout")
	sl.ui_scale = (float(px.x) / float(W)) / maxf(0.01, sl.desktop_density(Vector2(px), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0))
	sl._update_scale()
	for i in range(6):
		await process_frame
	print("view ", root.get_visible_rect().size)
	state.replay_seed = 2027
	state.start_season(club, db.club_list(club))
	for r in range(rounds):
		state.advance()
	# --vs CODE: play on until that club is the next opponent (longest-name proof).
	var guard := 0
	while vs != "" and str(state.my_next_opponent().get("code", "")) != vs and guard < 30:
		state.advance()
		guard += 1
	if drag or list_view:
		state.set_setting("seen_selection_intro", true)  # the first-visit card would sit over the oval
	if "--loads" in a:
		# Row 183's look: a week's recovery leaves most legs at 0, so a few
		# players carry set loads and moods to show every state of the numbers.
		var side: Dictionary = state.current_side()
		var set_to := [["C", 0, 58.0, 36], ["FWD", 1, 27.0, 55], ["DEF", 2, 12.0, 74]]
		for s in set_to:
			var ids: Array = side.get("MID" if s[0] == "C" else s[0], [])
			if ids.size() > int(s[1]):
				var man = state.list_player(str(ids[int(s[1])]))
				man["workload"] = s[2]
				man["morale"] = s[3]
	var ui: Control = load("res://scenes/SelectionScene.tscn").instantiate()
	if page != "":
		ui.set("_page", page)
	root.add_child(ui)
	for i in range(8):
		await process_frame
	if "--raised" in a:
		# The phone's list pulled up over the oval.
		ui.find_child("TeamBuilder", true, false).set_raised(true, false)
	if "--dent" in a:
		# A few men from other clubs, so the chemistry bar is short of full.
		for q in state.my_squad().ground.slice(0, 6):
			var man = state.list_player(str(q["id"]))
			load("res://scripts/sim/TeamFamiliarity.gd").arrive_club(man)
			man["team_fam"] = 70.0
		ui.call("_build")
	if picked:
		var c: Button = ui.find_child("Spot_C", true, false)
		if c != null:
			c.emit_signal("pressed")
	if "--profile" in a:
		# The centre's profile, with his fatigue, morale and form (row 183).
		var cp: Control = ui.find_child("Spot_C", true, false)
		if cp != null:
			ui.call("_open_profile", str(cp.get_meta("id")))
	match mode:
		"opp":
			ui.set("_view", "opp")
			ui.call("_build")
		"guide":
			ui.get("_week").show_synergies()
		"report":
			ui.get("_week").show_report(str(state.my_next_opponent().get("code", "")))
	for i in range(8):
		await process_frame
	if strategy != "":
		ui.call("_apply_strategy", strategy)
		for i in range(8):
			await process_frame
		var hint: Control = ui.find_child("BuilderHint", true, false)
		var sc2: ScrollContainer = ui.find_child("SelectionScroll", true, false)
		if hint != null and sc2 != null:
			sc2.scroll_vertical = int(hint.global_position.y - sc2.global_position.y + sc2.scroll_vertical - H / 2)
			for j in range(4):
				await process_frame
		print("note: ", hint.get("text") if hint != null else "(none)")
	if oval:
		var pitch: Control = ui.find_child("Pitch", true, false)
		var sc: ScrollContainer = ui.find_child("SelectionScroll", true, false)
		if sc != null and pitch != null:
			for i in range(3):
				sc.scroll_vertical = int(pitch.global_position.y - sc.global_position.y + sc.scroll_vertical - 8)
				for j in range(3):
					await process_frame
		print("oval at y ", pitch.global_position.y if pitch != null else -1.0, " pitch ", pitch.size if pitch != null else Vector2.ZERO)
	if drag:
		var c: Control = ui.find_child("Spot_C", true, false)
		if c != null:
			var from := c.get_global_rect().get_center()
			var press := InputEventMouseButton.new()
			press.button_index = MOUSE_BUTTON_LEFT
			press.pressed = true
			press.position = from
			press.global_position = from
			Input.parse_input_event(press)
			await process_frame
			for k in range(1, 9):
				var mv := InputEventMouseMotion.new()
				mv.button_mask = MOUSE_BUTTON_MASK_LEFT
				mv.position = from + Vector2(-6.0 * k, 9.0 * k)
				mv.global_position = mv.position
				mv.relative = Vector2(-6.0, 9.0)
				Input.parse_input_event(mv)
				await process_frame
			print("dragging: ", root.gui_is_dragging())
		for i in range(4):
			await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(out + "_sheet.png")
	print("wrote ", out + "_sheet.png")
	quit(0)
