extends SceneTree
## Row 103 for the director's look. Real renderer, windowed off screen
## (override.cfg), through C:/kt/gpu_slot.sh:
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_synergy_fit.gd
## or on GitHub: gh workflow run capture.yml --ref <branch> -f tool=capture_synergy_fit -f resolution=390x844
## Environment: CAP_W, CAP_H (default 390x844), CAP_OUT (file prefix, default
## "synergy_fit"). Saves <prefix>_sheet.png (a rival's profile: which of your
## synergies he would complete) and <prefix>_focus.png (a stat focus naming the
## trait it grows him toward). Illustrative fixture; never touches a real save.

const SEED := 2027
const CLUB := "FRE"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	OS.low_processor_usage_mode = false
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	state.autosave_enabled = false
	state.save_path = "user://capture_synergy_fit.save"
	state.settings_path = "user://capture_synergy_fit.cfg"
	state.replay_seed = SEED
	db.reload()
	state.reset()
	state.start_season(CLUB, db.club_list(CLUB))
	var w := int(OS.get_environment("CAP_W")) if OS.get_environment("CAP_W") != "" else 390
	var h := int(OS.get_environment("CAP_H")) if OS.get_environment("CAP_H") != "" else 844
	var prefix := OS.get_environment("CAP_OUT") if OS.get_environment("CAP_OUT") != "" else "synergy_fit"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			prefix = str(a[i + 1])
	DisplayServer.window_set_size(Vector2i(w, h))
	root.size = Vector2i(w, h)
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)

	# Your nearest synergy brought to one short (illustrative), then a rival
	# made to carry the trait it is short of.
	var ground: Array = state.my_squad().ground
	var near_row: Dictionary = Traits.progress(ground).filter(func(r): return not bool(r["active"]))[0]
	var want_syn := str(near_row["key"])
	var want_t := ""
	for t in near_row["needs"]:
		if int(near_row["have"][t]) < int(near_row["needs"][t]):
			want_t = str(t)
	var sline := str(Traits.SYNERGIES[want_syn]["line"])
	var td: Dictionary = Traits.DEFS[want_t]
	var short := int(near_row["missing"]) - 1
	for q in ground:
		if short <= 0:
			break
		if Traits.of(q).has(want_t) or (sline != "" and str(q["role"]) != sline):
			continue
		var troles: Array = td["roles"]
		if not troles.is_empty() and not troles.has(str(q["role"])):
			continue
		var lp: Dictionary = state.list_player(str(q["id"]))
		lp["attr"][str(td["stat"])] = int(td["min"]) + 8
		if Traits.of(lp).has(want_t):
			short -= 1
	var d: Dictionary = Traits.DEFS[want_t]
	var line := str(Traits.SYNERGIES[want_syn]["line"])
	var roles: Array = d["roles"]
	var role := line if line != "" else (str(roles[0]) if not roles.is_empty() else "MID")
	var rec: Dictionary = {}
	for code in state.season.lists:
		if str(code) == CLUB:
			continue
		for q in state.season.lists[code]:
			if str(q["role"]) == role:
				rec = (q as Dictionary).duplicate(true)
				break
		if not rec.is_empty():
			break
	# Only the one trait, so it is his first two.
	for k in Traits.DEFS:
		var kd: Dictionary = Traits.DEFS[k]
		if not kd.has("max"):
			rec["attr"][str(kd["stat"])] = mini(int(rec["attr"].get(str(kd["stat"]), 0)), int(kd["min"]) - 3)
	rec["attr"][str(d["stat"])] = int(d["min"]) + 6
	if bool(d.get("small", false)):
		rec["attr"]["marking"] = 45
	print("CAPTURE recruit for ", want_syn, " / ", want_t, ": ", state.synergy_fit(rec))
	router.go("list")
	await _frames(8)
	load("res://scripts/ui/PlayerSheet.gd").open(current_scene, rec)
	await _frames(8)
	var fit: Control = current_scene.find_child("SynergyFit", true, false)
	var sc := _scroll_of(fit)
	if fit != null and sc != null:
		sc.ensure_control_visible(fit)
	await _save(prefix + "_sheet.png")

	# Training: a midfielder's contested focus, picked, names Contested bull.
	var p: Dictionary = {}
	for q in state.my_list:
		if str(q["role"]) == "MID" and not Traits.of(q).has("bull") and int(q["attr"]["contested"]) < 84:
			p = q
			break
	for b in current_scene.find_children("*", "Button", true, false):
		if (b as Button).text == "Close":
			(b as Button).emit_signal("pressed")
	await _frames(4)
	state.set_setting("seen_training_intro", true)
	router.go("training")
	for i in range(120):
		if current_scene != null and current_scene.has_method("_open_player"):
			break
		await process_frame
	var scene = current_scene
	if not scene.has_method("_open_player"):
		push_error("training scene did not open")
		quit(1)
		return
	scene.call("_open_player", str(p["id"]))
	await _frames(6)
	scene.set("_focus_choice", "contested")
	scene.call("_build")
	await _frames(6)
	var panel: Control = scene.find_child("StatFocus", true, false)
	var dsc: ScrollContainer = scene.get("_detail_scroll")
	if panel != null and dsc != null:
		dsc.scroll_vertical = maxi(0, int(panel.global_position.y - dsc.global_position.y) + dsc.scroll_vertical - 8)
		await _frames(2)
		var tl: Control = scene.find_child("StatFocusTrait", true, false)
		if tl != null:
			dsc.ensure_control_visible(tl)
	await _save(prefix + "_focus.png")
	print("CAPTURE saved ", prefix, " at ", w, "x", h)
	quit()


func _scroll_of(c: Node) -> ScrollContainer:
	var n := c
	while n != null:
		if n is ScrollContainer:
			return n
		n = n.get_parent()
	return null


func _save(path: String) -> void:
	await _frames(3)
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(path)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame
