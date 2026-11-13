extends SceneTree
## Visual review of Coach of the Year on a phone (CoachOfYear.gd): a rival
## coach's profile with the award on his coaching career, and your own record
## (Season stats > Coach) with the seasons you won it. Real renderer, e.g.:
##   godot --path . --script tools/visual/capture_coach_of_year.gd -- --out /tmp/ard-coty
## Writes <out>_profile.png and <out>_record.png at 390x844.
## Illustrative fixture only; never touches a real save.

const PHONE := Vector2i(390, 844)


func _initialize() -> void:
	_run.call_deferred()


func _settle(n := 8) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	var out := "/tmp/ard-coty"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	state.autosave_enabled = false
	state.save_path = "user://capture_coty.save"
	state.settings_path = "user://capture_coty.cfg"
	state.reset()
	state.start_season("MEL", db.club_list("MEL"))
	root.size = PHONE
	DisplayServer.window_set_size(PHONE)

	# A rival senior coach who won it twice.
	var cid := str(load("res://scripts/sim/Coaches.gd").staff(state.coaches, "WBD").get("SC", ""))
	var c: Dictionary = state.coaches[cid]
	c["coty"] = [2027, 2030]
	state.coach_of_year = [
		{"year": 2027, "club": "WBD", "cid": cid, "you": false, "name": "", "when": "",
			"line": "Took Western Bulldogs from 16th last year to 3rd."},
		{"year": 2030, "club": "WBD", "cid": cid, "you": false, "name": "", "when": "",
			"line": "11 straight wins carried Western Bulldogs into the finals."}]
	var host := _host()
	load("res://scripts/ui/CoachSheet.gd").open(host, c)
	await _settle()
	_save(out + "_profile.png")
	host.free()

	# Your record after four seasons, Coach of the Year in two of them.
	state.honour_roll = []
	for y in [2027, 2028, 2029, 2030]:
		state.honour_roll.append({"year": y, "my_club": "MEL", "my_position": 3,
				"my_record": "16-7-0", "premier": "", "runner_up": "", "my_finals": "QF1"})
	state.coach_of_year = [{"year": 2028, "club": "MEL", "cid": "", "you": true, "name": state.coach_name,
			"line": "Melbourne finished 4th, picked for 12th on paper.", "when": ""}, {"year": 2030, "club": "MEL", "cid": "", "you": true,
			"name": state.coach_name, "line": "Melbourne finished on top of the ladder.", "when": ""}]
	host = _host()
	var page := ScrollContainer.new()
	page.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	host.add_child(page)
	var body: Control = load("res://scripts/ui/stats/StatsCoach.gd").build(host)
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var pad := MarginContainer.new()
	pad.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for side in ["left", "right", "top"]:
		pad.add_theme_constant_override("margin_" + side, 16)
	pad.add_child(body)
	page.add_child(pad)
	await _settle()
	_save(out + "_record.png")
	quit()


func _host() -> Control:
	var bg := ColorRect.new()
	bg.color = load("res://scripts/ui/UiKit.gd").BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)
	return bg


func _save(path: String) -> void:
	var img: Image = root.get_texture().get_image()
	img.save_png(path)
	print("wrote ", path)
