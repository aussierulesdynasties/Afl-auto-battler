extends SceneTree
## Visual review tool for the concussion medical panel (MedicalPanel.gd).
## Fremantle, seeded, dark. Needs a real renderer (windowed, through
## C:/kt/gpu_slot.sh, off screen via override.cfg):
##   godot --path . --script tools/visual/capture_medical_panel.gd -- --out <dir> --size 390x844
## Writes <dir>/medical_sheet.png (a player on four concussions in five years:
## the warning line on his sheet), medical_list.png (his row on the list),
## medical_list_out.png (a concussed team-mate on three),
## medical_cleared.png and medical_retired.png (the hub the week the panel sat
## on your player, each way). Never touches a real save.


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


func _scroll_to(scene: Node, target: Control, above := 70) -> void:
	for b in scene.find_children("*", "ScrollContainer", true, false):
		var box := b as ScrollContainer
		if box.is_visible_in_tree() and box.is_ancestor_of(target):
			box.scroll_vertical = maxi(0, int(target.global_position.y - box.global_position.y) - above + box.scroll_vertical)
	await _frames()


func _career(state, db) -> void:
	state.reset()
	state.career_seed = 7737
	state.replay_seed = 7737
	for key in ["seen_training_intro", "seen_weekly_loop_intro", "seen_coaching_intro"]:
		state.set_setting(key, true)
	state.start_season("FRE", db.club_list("FRE"))
	state.tutorials = false


func _past(state, p: Dictionary, n: int) -> void:
	var CF = load("res://scripts/sim/CareerFacts.gd")
	for i in range(n):
		CF.add(state.career_facts, str(p["id"]), CF.row(state.season_year - 1 - i, "Round 9", "injury", "FRE", "", "concussion"))


## A senior Fremantle player whose sitting on his fifth concussion goes `want`.
func _pick(state, want: bool) -> Dictionary:
	var MP = load("res://scripts/sim/MedicalPanel.gd")
	var best := {}
	for p in state.my_list:
		if int(p.get("injury_weeks", 0)) > 0 or state.career_facts.has(str(p["id"])):
			continue
		if MP.cleared(state.career_seed, str(p["id"]), state.season_year, 5) != want:
			continue
		if best.is_empty() or int(p.get("overall", 0)) > int(best.get("overall", 0)):
			best = p
	return best


## The hub the week the panel sat on one of yours.
func _week(state, db, want: bool, path: String) -> void:
	_career(state, db)
	state.advance()
	var p := _pick(state, want)
	_past(state, p, 4)
	p["injury_weeks"] = 2
	p["injury_kind"] = "concussion"
	var row := {"id": str(p["id"]), "club": "FRE", "weeks": 2, "kind": "concussion"}
	state.last_injuries.append(row)
	state._log_injuries([row], state.last_label)
	state.last_injuries = state._not_medically_out(state.last_injuries).filter(
			func(r): return want or str(r["id"]) != str(p["id"]))
	state.skip_media_conference()
	var hub = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(12)
	hub.call("_show_results", state.last_results)
	await _frames(40)
	var line: Label = hub.find_child("MyMedical", true, false)
	print("WEEK ", "cleared" if want else "retired", " | hub line: ", line.text if line != null else "(no MyMedical)",
			" | news: ", state.news[0].get("text", ""))
	if line != null:
		await _scroll_to(hub, line, 420)
	await _shot(path)
	hub.queue_free()
	await _frames(2)


func _run() -> void:
	var out := "."
	var size := Vector2i(390, 844)
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--size":
			size = Vector2i(int(str(a[i + 1]).get_slice("x", 0)), int(str(a[i + 1]).get_slice("x", 1)))
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_medical.save"
	state.settings_path = "user://capture_medical.cfg"
	_career(state, db)
	UK.apply_appearance("dark")
	root.size = size
	DisplayServer.window_set_size(size)
	var bg := ColorRect.new()
	bg.color = UK.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)

	# The sheet of a fit senior player on four in five years.
	var p := _pick(state, true)
	_past(state, p, 4)
	var host := Control.new()
	host.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(host)
	var sheet: Control = load("res://scripts/ui/PlayerSheet.gd").open(host, p)
	await _frames(10)
	var warn: Label = sheet.find_child("ProfileConcussions", true, false)
	print("SHEET | ", warn.text if warn != null else "(no ProfileConcussions)")
	await _shot(out + "/medical_sheet.png")
	host.queue_free()
	await _frames(2)

	# His row on the list, and a concussed team-mate on three.
	var q := _pick(state, false)
	_past(state, q, 2)
	var CF = load("res://scripts/sim/CareerFacts.gd")
	CF.add(state.career_facts, str(q["id"]), CF.row(state.season_year, "Round 1", "injury", "FRE", "", "concussion"))
	q["injury_weeks"] = 2
	q["injury_kind"] = "concussion"
	var list = load("res://scenes/ListScene.tscn").instantiate()
	root.add_child(list)
	await _frames(12)
	var tab: Button = list.find_child("ListTabFull", true, false)
	if tab != null:
		tab.pressed.emit()
		await _frames(12)
	for st in list.find_children("RowConcussions", "Label", true, false):
		if (st as Label).text.contains("in 5 years"):
			print("LIST | ", (st as Label).text, " | width ", (st as Label).size.x)
	for st in list.find_children("RowConcussions", "Label", true, false):
		if (st as Label).text.contains("in 5 years"):
			await _scroll_to(list, st, 300)
			break
	await _shot(out + "/medical_list.png")
	var qrow: Control = list.find_child("Row_" + str(q["id"]), true, false)
	if qrow != null:
		await _scroll_to(list, qrow, 200)
		await _shot(out + "/medical_list_out.png")
	list.queue_free()
	await _frames(2)

	await _week(state, db, true, out + "/medical_cleared.png")
	await _week(state, db, false, out + "/medical_retired.png")
	quit(0)
