extends SceneTree
## Skip to the break (director, 2026-11-06): stills of the in-quarter controls
## row at each quarter of a match you coach. Q1-Q3 show "Skip to quarter time /
## half time / three-quarter time" beside "Skip to full time"; Q4 shows Skip to
## full time only. After each skip a still of the break it lands on.
## Real taps (tests/tap.gd) on Start and on the skip button.
## Needs a real renderer (windowed, through C:/kt/gpu_slot.sh, off screen):
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_skip_to_break.gd -- \
##       --club COL --size 390x844 --seed 2027 --out /tmp/skip_to_break
## Never touches a real save.

const Tap := preload("res://tests/tap.gd")

var _out := "/tmp/skip_to_break"
var _fail := 0


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


func _shot(name: String) -> void:
	for i in range(20):
		await process_frame
	var path := "%s_%s.png" % [_out, name]
	root.get_viewport().get_texture().get_image().save_png(path)
	print("CAPTURE %s" % path)


func _answer_moment(m: Node) -> bool:
	var sim = root.get_node("GameState").pending_sim
	var mo = m.get("_moment_overlay")
	if mo != null and is_instance_valid(mo) and sim != null and not sim.pending_moment.is_empty():
		m.call("_on_moment_choice", int(sim.pending_moment.get("default", 0)))
		return true
	return false


## Watch about `frames` frames of play at 2x, answering any call with its default.
func _watch(m: Node, frames: int) -> void:
	var pv = m.get("_pitch")
	pv.set_speed(2.0)
	for i in range(frames):
		if _answer_moment(m):
			pv.set_speed(2.0)
		await process_frame


## A real tap first; an off-screen window can be scaled by the desktop, so a
## tap that misses there falls back to pressing (the suite's headless test
## proves the real tap: _test_skip_to_break).
func _press(b: Control) -> String:
	var why: String = await Tap.tap(b)
	if why != "" and b is Button:
		print("CAPTURE note: tap missed (%s; window %s, root %s), pressing instead" % [why,
				str(DisplayServer.window_get_size()), str(root.size)])
		(b as Button).pressed.emit()
		await process_frame
		return ""
	return why


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
	gs.save_path = "user://capture_skip_to_break.save"
	gs.settings_path = "user://capture_skip_to_break.cfg"
	gs.replay_seed = int(str(a.get("seed", "2027")))
	var db = root.get_node("GameDB")
	var club := str(a.get("club", "COL"))
	gs.reset()
	gs.start_season(club, db.club_list(club))
	gs.set_vignettes_on(false)
	if not gs.prepare_interactive_match():
		print("CAPTURE FAIL: no live match")
		quit(1)
		return
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	for i in range(10):
		await process_frame
	var names := ["quarter_time", "half_time", "three_quarter_time"]
	for q in range(1, 5):
		var start: Control = m.find_child("StartQuarter", true, false)
		var why: String = await _press(start)
		if why != "":
			await _shot("q%d_start_blocked" % q)
			print("CAPTURE FAIL: Start Q%d: %s" % [q, why])
			quit(1)
			return
		await _watch(m, 240)
		var sb: Button = m.find_child("SkipToBreak", true, false)
		var shown := sb != null and sb.is_visible_in_tree()
		print("CAPTURE Q%d skip-to-break button: %s %s" % [q, sb.text if shown else "(hidden)",
				str(sb.get_global_rect()) if shown else ""])
		await _shot("q%d_in_play" % q)
		if q == 4:
			if shown:
				_fail += 1
			break
		if not shown:
			_fail += 1
			break
		# A call can be up when the shot is taken; answer it, then tap.
		_answer_moment(m)
		await process_frame
		var why2: String = await _press(sb)
		print("CAPTURE Q%d tap on %s: %s" % [q, sb.text, "ok" if why2 == "" else why2])
		if why2 != "":
			_fail += 1
			break
		for i in range(30):
			await process_frame
		await _shot("q%d_after_skip_%s" % [q, names[q - 1]])
	quit(0 if _fail == 0 else 1)
