extends SceneTree
## Visual review of the Golden Fist (T5.Q11c): the best defender of the season
## in the awards ceremony, the Stats > Awards honours table and the club's trophies.
## Needs a real renderer, e.g.:
##   godot --path . --rendering-method gl_compatibility \
##       --script tools/visual/capture_golden_fist.gd -- --out /tmp/fist --size 390x844
## A fresh career plays its first season out, so the award is the engine's own.
## The trophy room needs a Golden Fist won by your club: the shelf entry is a
## fixture (your best-placed defender, or your first defender with the
## winner's counts), never written to a save.
## Writes <out>_ceremony.png, <out>_awards.png, <out>_trophies.png,
## <out>_trophies_filtered.png and <out>_sheet.png; a _lower.png where the
## Golden Fist sits below the fold (scrolled to it).
##   --size WxH   window size (default 390x844)   --club CODE (default COL)

var _w := 390
var _h := 844
var _club := "COL"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "fist"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
			"--club":
				_club = str(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	var AW = load("res://scripts/sim/Awards.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_fist.save"
	state.settings_path = "user://capture_fist.cfg"
	state.reset()
	state.career_seed = 2031
	state.replay_seed = 2031
	state.start_season(_club, db.club_list(_club))
	state.set_setting("seen_season_stats_intro", true)
	UK.apply_appearance("dark")
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	var guard := 0
	while not state.season_is_over() and guard < 40:
		state.advance()
		guard += 1
	var fist: Array = state.season_awards.get("golden_fist", [])
	print("golden_fist top3 ", fist.slice(0, 3))
	# 1. The ceremony, at the Golden Fist stage, revealed.
	var host := Control.new()
	root.add_child(host)
	host.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var ceremony: Control = load("res://scripts/ui/SeasonAwards.gd").open(host)
	await _frames(5)
	var next: Button = ceremony.find_child("AwardsNext", true, false)
	for i in range(30):
		if _has_label(ceremony, AW.GOLDEN_FIST) and _has_label(ceremony, "Final placings"):
			break
		next.emit_signal("pressed")
		await _frames(4)
		var scene = ceremony.find_child("AwardWinner", true, false)
		if scene != null and not scene._done:
			scene.finish_now()
			await _frames(4)
	await _frames(30)
	_save(out + "_ceremony.png")
	var placed := _label_starting(ceremony, "3. ")
	if placed != null:
		await _show(placed)
		_save(out + "_ceremony_lower.png")
	host.queue_free()
	await _frames(3)
	# 2. Stats > Awards: the season's honours.
	var hub_script = load("res://scripts/ui/StatsHubScene.gd")
	hub_script.current = "awards"
	var hub: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(10)
	_save(out + "_awards.png")
	var fist_row = hub.find_child("Honour_GoldenFist", true, false)
	if fist_row != null:
		await _show(fist_row)
		_save(out + "_awards_lower.png")
	hub.queue_free()
	await _frames(2)
	# 3. The trophy room, with a Golden Fist on your shelf.
	var year: int = state.season_year
	var entry: Dictionary = state.honour_roll.back()
	var shelf := {}
	for r in fist:
		if str(r.get("club", "")) == _club:
			shelf = (r as Dictionary).duplicate(true)
			break
	if shelf.is_empty() and not fist.is_empty():
		shelf = (fist[0] as Dictionary).duplicate(true)
		for p in state.season.lists[_club]:
			if str(p.get("role", "")) == "DEF":
				shelf["id"] = str(p["id"])
				break
		shelf["club"] = _club
	entry["golden_fist"] = [shelf]
	hub_script.current = "ladder"
	hub = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(10)
	load("res://scripts/ui/ClubPage.gd").open_trophies(hub, _club)
	await _frames(10)
	var shelf_b = hub.find_child("Honour_golden_fist_%d" % year, true, false)
	if shelf_b != null:
		await _show(shelf_b)
	_save(out + "_trophies.png")
	var b: Button = hub.find_child("Honour_golden_fist_%d" % year, true, false)
	if b == null:
		push_error("no Honour_golden_fist_%d" % year)
	else:
		b.emit_signal("pressed")
		await _frames(10)
		_save(out + "_sheet.png")
		var last = hub.find_child("SheetLine_1", true, false)
		if last != null:
			await _show(last)
			_save(out + "_sheet_lower.png")
		hub.call("handle_back")
		await _frames(6)
	var opt: OptionButton = hub.find_child("AwardFilter", true, false)
	if opt != null:
		for i in range(opt.item_count):
			if opt.get_item_text(i) == AW.GOLDEN_FIST:
				opt.select(i)
				opt.item_selected.emit(i)
		await _frames(10)
		_save(out + "_trophies_filtered.png")
	load("res://scripts/ui/ClubTrophies.gd").award_filter = ""
	quit()


## Scrolls the nearest scroll container so the node is on screen.
func _show(n: Control) -> void:
	var p := n.get_parent()
	while p != null and not (p is ScrollContainer):
		p = p.get_parent()
	if p != null:
		(p as ScrollContainer).ensure_control_visible(n)
	await _frames(6)


func _label_starting(n: Node, text: String) -> Control:
	for c in n.find_children("*", "Label", true, false):
		if (c as Label).text.begins_with(text) and (c as Label).is_visible_in_tree():
			return c
	return null


func _has_label(n: Node, text: String) -> bool:
	for c in n.find_children("*", "Label", true, false):
		if (c as Label).text == text and (c as Label).is_visible_in_tree():
			return true
	return false


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
