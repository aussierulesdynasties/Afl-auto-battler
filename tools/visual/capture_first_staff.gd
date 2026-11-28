extends SceneTree
## A created club's first staff (director 2026-11-15), phone portrait 390x844:
## the Staff screen as the League Draft leaves it (the senior assistant's
## shortlist open), the shortlist scrolled into view, and the next job's
## shortlist after one appointment. A fresh career with a Club Forge club;
## never touches a real save.
##   godot --path . --script tools/visual/capture_first_staff.gd -- --out <prefix>
## Writes <prefix>_step.png, <prefix>_shortlist.png and <prefix>_next.png.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "first_staff"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	state.autosave_enabled = false
	state.save_path = "user://capture_first_staff.save"
	state.settings_path = "user://capture_first_staff.cfg"
	state.reset()
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.create_club({"name": "Port Melbourne", "short": "Borough", "code": "PMB",
			"location": "port-melbourne", "primary": "#1B3A8C", "secondary": "#C8102E",
			"accent": "#FFFFFF", "design": "hoops", "kit": "p/s/a"})
	state.start_season("PMB", db.club_list("CAR").duplicate(true))
	state.tutorials = false
	root.size = Vector2i(390, 844)
	router.stack = []
	router.go_over("hub", "staff")
	await _frames(90)
	_save(out + "_step.png")
	var card: Control = root.find_child("Vacancy_SA", true, false)
	_scroll_to(card, 8.0)
	await _frames(10)
	_save(out + "_shortlist.png")
	var pick: Button = root.find_child("Appoint_SA_1", true, false)
	if pick != null:
		pick.emit_signal("pressed")
	await _frames(20)
	_scroll_to(root.find_child("Vacancy_MID", true, false), 8.0)
	await _frames(10)
	_save(out + "_next.png")
	quit()


func _scroll_to(c: Control, gap: float) -> void:
	if c == null:
		return
	for sc in root.find_children("*", "ScrollContainer", true, false):
		if (sc as ScrollContainer).is_ancestor_of(c):
			var s := sc as ScrollContainer
			s.scroll_vertical = int(c.global_position.y - s.global_position.y - gap + s.scroll_vertical)
			return


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(path)
