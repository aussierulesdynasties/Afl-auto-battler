extends SceneTree
## The quarter-time calls' Gain and Cost lines (row T1.R26, director 2026-11-10): each call's
## sheet opened from its row, one option picked so its sized lines show. Needs a real renderer:
##   bash C:/kt/gpu_slot.sh godot --path . --script tools/visual/capture_gate_lines.gd -- --out /tmp/gl
##       [--size 390x844] [--club FRE]
## Writes <out>_plan.png (Attacking picked: the gain for this list today), <out>_pep.png (Fire them
## up), <out>_through.png (a midfielder played through), <out>_loose.png (a loose defender) and
## <out>_cover.png (a forward on their loose man, when they run one). Their side runs a loose man
## from the first quarter so the cover call is offered. A fresh career's first match at quarter
## time, seeded; never touches a real save.

var _w := 390
var _h := 844


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "gate_lines"
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
			"--club":
				club = str(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_gates.save"
	state.settings_path = "user://capture_gates.cfg"
	state.reset()
	state.career_seed = 2026
	state.replay_seed = 2026
	state.set_setting("seen_training_intro", true)
	state.start_season(club, db.club_list(club))
	if not state.prepare_interactive_match():
		push_error("no match to prepare")
		quit(1)
		return
	var sim0 = state.pending_sim
	var them := 1 - int(sim0.moment_side)
	var spare: Dictionary = load("res://scripts/sim/Matchups.gd").best_interceptor(sim0.squads[them].ground, 0.0)
	sim0.set_interceptor(them, str(spare.get("id", "")), false)
	sim0.run_quarter()
	sim0.set_interceptor(them, str(spare.get("id", "")), true)
	UK.apply_appearance("dark")
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	var scene = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(scene)
	await _frames(12)
	await _call(scene, "plan", "PlanPicker_attacking", out + "_plan.png")
	await _call(scene, "pep", "PepPicker_fire_up", out + "_pep.png")
	await _call(scene, "pt", "", out + "_through.png")
	await _call(scene, "def", "DefenceSetupPicker_loose", out + "_loose.png")
	await _call(scene, "def", "DefenceSetupPicker_cover", out + "_cover.png")
	quit()


## Open a call's sheet from its row, press `option` (the first played-through
## midfielder when empty), scroll its note into view and save the screen.
func _call(scene: Node, key: String, option: String, path: String) -> void:
	var row: Button = scene.find_child("CallRow_" + key, true, false)
	if row == null:
		push_error("no call row for " + key)
		return
	row.emit_signal("pressed")
	await _frames(8)
	var pick: Button = null
	if option == "":
		for b in scene.find_children("FocusPicker_focus_midGrid_*", "Button", true, false):
			if str(b.name) != "FocusPicker_focus_midGrid_":
				pick = b
				break
	else:
		pick = scene.find_child(option, true, false)
	if pick == null:
		print("no option ", option, " for ", key)
	else:
		pick.emit_signal("pressed")
		await _frames(8)
	var note: Control = scene.find_child({"plan": "PlanNote", "pep": "PepNote", "pt": "FocusGainCost_focus_mid",
			"def": "DefenceNote"}[key], true, false)
	if note != null:
		var p: Node = note.get_parent()
		while p != null:
			if p is ScrollContainer:
				var sc := p as ScrollContainer
				sc.scroll_vertical = maxi(0, int(note.global_position.y + note.size.y - sc.global_position.y - sc.size.y + 24) + sc.scroll_vertical)
				break
			p = p.get_parent()
		var words := PackedStringArray()
		for l in [note] + note.find_children("*", "Label", true, false):
			if l is Label and str(l.text) != "":
				words.append(str(l.text))
		print(key, " NOTE ", " | ".join(words))
	await _frames(4)
	_save(path)
	var back := InputEventAction.new()
	back.action = "ui_cancel"
	back.pressed = true
	Input.parse_input_event(back)
	await _frames(8)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
