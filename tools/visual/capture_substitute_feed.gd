extends SceneTree
## The substitute in the match feed (Legacy, EraRules): plays a live match under
## an era year's rules (2013: the substitute comes on at three-quarter time at the
## latest; 2021: the medical sub, only for an injury) and saves the frame once
## the feed calls him. The season is today's; only the rules year changes.
## Needs a real renderer (windowed, through C:/kt/gpu_slot.sh, off screen):
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_substitute_feed.gd -- \
##       --club FRE --year 2013 --size 390x844 --seed 2027 --out /tmp/substitute_feed
## Never touches a real save.

var _out := "/tmp/substitute_feed"


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
	gs.save_path = "user://capture_substitute_feed.save"
	gs.settings_path = "user://capture_substitute_feed.cfg"
	gs.tutorials = false
	gs.replay_seed = int(str(a.get("seed", "2027")))
	var db = root.get_node("GameDB")
	var club := str(a.get("club", "FRE"))
	gs.reset()
	gs.start_season(club, db.club_list(club))
	gs.tutorials = false
	var year := int(str(a.get("year", "2013")))
	EraRules.year = year
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
	pitch.set_speed(8.0)
	# One frame per look: the injury line naming the substitute, and (2011-15)
	# the three-quarter-time change, which has its own line.
	var looks := {"_injury": "the medical sub, " if EraRules.medical_sub() else "the substitute, "}
	if not EraRules.medical_sub():
		looks["_tactical"] = "Substitute:"
	var guard := 0
	var max_frames := int(str(a.get("frames", "150000")))
	var found := 0
	while not looks.is_empty() and guard < max_frames:
		guard += 1
		await process_frame
		if guard % 30 != 0:
			continue
		for key in looks.keys():
			var line := _feed_line(m, str(looks[key]))
			if line == "":
				continue
			# Found at a break (the three-quarter-time change): the break card
			# covers the feed, so start the quarter and look once play is on.
			var start_q: Button = m.find_child("StartQuarter", true, false)
			if start_q != null and start_q.is_visible_in_tree() and not start_q.disabled:
				start_q.pressed.emit()
				for i in range(int(str(a.get("after", "20")))):
					await process_frame
			var was: bool = pitch.get("playing")
			pitch.playing = false
			for i in range(20):
				await process_frame
			root.get_viewport().get_texture().get_image().save_png(_out + str(key) + ".png")
			print("CAPTURE %s%s.png | %dx%d | year %d | frames %d | line '%s'" % [_out, key, w, h, year, guard, line])
			looks.erase(key)
			found += 1
			pitch.playing = was
		# A break or a coach's call stops play: carry on.
		if not bool(pitch.get("playing")):
			var b := _go_on(m)
			if b != null:
				b.pressed.emit()
	print("CAPTURE done: %d found, missing %s" % [found, str(looks.keys())])
	quit(0 if looks.is_empty() else 1)


func _feed_line(m: Node, want: String) -> String:
	for n in m.find_children("*", "Label", true, false):
		var l := n as Label
		if l.is_visible_in_tree() and l.text.contains(want):
			return l.text
	for n in m.find_children("*", "RichTextLabel", true, false):
		var r := n as RichTextLabel
		if r.is_visible_in_tree() and r.get_parsed_text().contains(want):
			return r.get_parsed_text()
	return ""


const _NOT_OPTIONS := ["1x", "2x", "4x", "8x", "Skip to full time", "Pause"]


## The control that carries play on: the next quarter's start, or a call's first option.
func _go_on(m: Node) -> Button:
	var first: Button = m.find_child("Moment_0", true, false)
	if first != null and first.is_visible_in_tree() and not first.disabled:
		return first
	var start: Button = m.find_child("StartQuarter", true, false)
	if start != null and start.is_visible_in_tree() and not start.disabled:
		return start
	for b in m.find_children("*", "Button", true, false):
		var btn := b as Button
		if not btn.is_visible_in_tree() or btn.disabled or _NOT_OPTIONS.has(btn.text) \
				or str(btn.name) == "MomentumBar":
			continue
		return btn
	return null
