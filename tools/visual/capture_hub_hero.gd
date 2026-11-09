extends SceneTree
## The hub's first screen for the hero's look (row 69): a fresh career at round 1
## and the same career some rounds on, per club, at phone size. A real renderer
## and a window (no --headless). Never touches a real save.
##   godot --path . --windowed --script tools/visual/capture_hub_hero.gd -- --out DIR --tag before --clubs COL,WBD,ADE
## Writes DIR/<tag>_<club>_r<round>.png and <tag>_<club>_r<round>_down.png (scrolled
## one screen down, as a coach reading on would see it).

var _size := Vector2i(390, 844)
var _state: Node
var _router: Node


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "."
	var tag := "hub"
	var clubs := PackedStringArray(["COL", "WBD", "ADE"])
	var rounds := [0, 7]
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--tag":
				tag = str(a[i + 1])
			"--clubs":
				clubs = str(a[i + 1]).split(",")
			"--size":
				var wh := str(a[i + 1]).split("x")
				_size = Vector2i(int(wh[0]), int(wh[1]))
	await process_frame
	_state = root.get_node("GameState")
	var db: Node = root.get_node("GameDB")
	_router = root.get_node("Router")
	_state.autosave_enabled = false
	_state.save_path = "user://capture_hub_hero.save"
	_state.settings_path = "user://capture_hub_hero.cfg"
	root.size = _size
	for club in clubs:
		_state.reset()
		_state.replay_seed = 690
		_state.start_season(club, db.club_list(club))
		_state.tutorials = false
		var played := 0
		for r in rounds:
			while played < r:
				_state.advance()
				played += 1
			_clear_asks()
			_router.stack = []
			_router.go("main")
			await _frames(6)
			_router.go("hub")
			# The first hub of a run can sit behind a loading frame for a while.
			for wait in range(600):
				if root.find_child("ThisWeek", true, false) != null:
					break
				await process_frame
			await _frames(60)
			await _shut_popups()
			await _frames(40)
			var stem := "%s/%s_%s_r%d" % [out, tag, club, r + 1]
			_save(stem + ".png")
			var sc := _page_scroll()
			if sc != null:
				sc.scroll_vertical = int(sc.size.y) - 40
				await _frames(8)
				_save(stem + "_down.png")
			print("captured ", stem)
	quit()


## Anything the week asked is settled so the hub itself shows, as a coach sees
## it once he has dealt with them.
func _clear_asks() -> void:
	for card in _state.week_events:
		card["popped"] = true
	_state.skip_media_conference()


func _shut_popups() -> void:
	for attempt in range(6):
		var shut := false
		for b in root.find_children("*", "Button", true, false):
			var t := (b as Button).text
			if (b as Button).is_visible_in_tree() and (t == "Got it" or t == "Close" or t == "Done" or t == "Later" or t == "Back to hub"):
				(b as Button).emit_signal("pressed")
				shut = true
				break
		if not shut:
			return
		await _frames(12)


func _page_scroll() -> ScrollContainer:
	var week: Node = root.find_child("ThisWeek", true, false)
	while week != null:
		if week is ScrollContainer:
			return week
		week = week.get_parent()
	return null


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(path)
