extends SceneTree
## The first match a device watches: the momentum line under the meter keeps its
## room from the first frame, so the ground never moves when it appears. Starts a
## seeded season with the intro unseen, saves the frame just after the first
## ball-up (line unseen) and the frame once momentum first moves (line shown),
## and prints the ground's rect in both.
## Needs a real renderer (windowed, through C:/kt/gpu_slot.sh, off screen):
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_momentum_line.gd -- \
##       --club FRE --size 390x844 --seed 2027 --out /tmp/momentum_line
## Never touches a real save.

var _out := "/tmp/momentum_line"


func _initialize() -> void:
	_run.call_deferred()


func _args() -> Dictionary:
	var out := {}
	var a := OS.get_cmdline_user_args()
	var i := 0
	while i < a.size():
		var k := str(a[i])
		if k.begins_with("--"):
			var v := ""
			if i + 1 < a.size() and not str(a[i + 1]).begins_with("--"):
				v = str(a[i + 1])
				i += 1
			out[k.substr(2)] = v
		i += 1
	return out


func _run() -> void:
	await process_frame
	var a := _args()
	_out = str(a.get("out", _out))
	var size_s := str(a.get("size", "390x844")).split("x")
	var w := int(size_s[0])
	var h := int(size_s[1])
	root.size = Vector2i(w, h)
	DisplayServer.window_set_size(Vector2i(w, h))
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://capture_momentum_line.save"
	gs.settings_path = "user://capture_momentum_line.cfg"
	gs.tutorials = true
	gs.set_setting("seen_momentum_intro", false)
	gs.replay_seed = int(str(a.get("seed", "2027")))
	var db = root.get_node("GameDB")
	var club := str(a.get("club", "FRE"))
	gs.reset()
	gs.start_season(club, db.club_list(club))
	gs.tutorials = true
	gs.set_setting("seen_momentum_intro", false)
	if not gs.prepare_interactive_match():
		print("CAPTURE FAIL: no live match")
		quit(1)
		return
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	for i in range(10):
		await process_frame
	var start: Button = m.find_child("StartQuarter", true, false)
	if start == null:
		print("CAPTURE FAIL: no Start")
		quit(1)
		return
	start.pressed.emit()
	var pitch = m.get("_pitch")
	var note: Label = m.find_child("MomentumNote", true, false)
	for i in range(30):
		await process_frame
	var before: Rect2 = pitch.get_global_rect()
	var note_a_before := note.modulate.a
	root.get_viewport().get_texture().get_image().save_png(_out + "_before.png")
	pitch.set_speed(4.0)
	var guard := 0
	var max_frames := int(str(a.get("frames", "6000")))
	while note.modulate.a < 1.0 and guard < max_frames:
		guard += 1
		await process_frame
		# A coach's call stops play: take the first option.
		if not bool(pitch.get("playing")) and guard % 60 == 0:
			var opt := _gate_option(m)
			if opt != null:
				opt.pressed.emit()
	pitch.playing = false
	for i in range(20):
		await process_frame
	var after: Rect2 = pitch.get_global_rect()
	root.get_viewport().get_texture().get_image().save_png(_out + "_after.png")
	print("CAPTURE %s_before.png / _after.png | %dx%d | frames %d | note alpha %.1f -> %.1f | ground %s -> %s | same %s"
			% [_out, w, h, guard, note_a_before, note.modulate.a, before, after, str(before == after)])
	quit(0 if before == after and note.modulate.a == 1.0 else 1)


const _NOT_OPTIONS := ["Play", "1x", "2x", "4x", "8x", "Skip to full time", "Pause"]


func _gate_option(m: Node) -> Button:
	for b in m.find_children("*", "Button", true, false):
		var btn := b as Button
		if not btn.is_visible_in_tree() or btn.disabled or _NOT_OPTIONS.has(btn.text) \
				or str(btn.name) == "MomentumBar":
			continue
		return btn
	return null
