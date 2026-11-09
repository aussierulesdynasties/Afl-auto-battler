extends SceneTree
## Row 117 captures (phone portrait, 390x844): a rival's approach on the hub
## with every answer and how he weighs it, then the Staff screen with a
## promise held and a promise broken. A fresh Fremantle career; never touches
## a real save.
##   godot --path . --script tools/visual/capture_coach_promise.gd -- --out <prefix>
## Writes <prefix>_approach.png and <prefix>_staff.png.

var club := "FRE"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "coach_promise"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	state.autosave_enabled = false
	state.save_path = "user://capture_promise.save"
	state.settings_path = "user://capture_promise.cfg"
	state.reset()
	state.start_season(club, db.club_list(club))
	state.tutorials = false
	var staff: Dictionary = state.club_staff(club)
	var mid: Dictionary = staff.get("MID", {})
	mid["since"] = state.season_year - 6
	state.coach_approaches = [{"cid": str(mid["cid"]), "from_job": "MID", "club": "WBD", "job": "SA",
			"choice": "", "kept": false, "text": ""}]
	root.size = Vector2i(390, 844)
	router.stack = []
	router.go("main")
	await _frames(8)
	router.go("hub")
	var guard := 0
	while root.find_child("CoachApproaches", true, false) == null and guard < 600:
		await process_frame
		guard += 1
	await _frames(20)
	for b in root.find_children("*", "Button", true, false):
		if (b as Button).text == "Got it" and (b as Button).is_visible_in_tree():
			(b as Button).emit_signal("pressed")
	await _frames(20)
	# Any week event is put off, so the approach is what the screen shows.
	for i in range(3):
		for b in root.find_children("*", "Button", true, false):
			if (b as Button).text == "Later" and (b as Button).is_visible_in_tree():
				(b as Button).emit_signal("pressed")
		await _frames(15)
	var card: Control = root.find_child("CoachApproaches", true, false)
	if card != null:
		for sc in root.find_children("*", "ScrollContainer", true, false):
			if (sc as ScrollContainer).is_ancestor_of(card):
				(sc as ScrollContainer).ensure_control_visible(card)
				await _frames(4)
				(sc as ScrollContainer).scroll_vertical = int(card.global_position.y - 120.0 + (sc as ScrollContainer).scroll_vertical)
				break
	await _frames(10)
	_save(out + "_approach.png")
	# Staff: the midfield coach holds a promise; the forwards coach was let down once.
	load("res://scripts/sim/CoachMarket.gd").make_promise(mid, state.season_year)
	var fwd: Dictionary = staff.get("FWD", {})
	fwd["broken"] = {club: 1}
	router.go("staff")
	await _frames(90)
	for b in root.find_children("*", "Button", true, false):
		if (b as Button).text == "Got it" and (b as Button).is_visible_in_tree():
			(b as Button).emit_signal("pressed")
	await _frames(20)
	_save(out + "_staff.png")
	quit()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(path)
