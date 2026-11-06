extends SceneTree
## Row 106 (T5.Q8): the live feed's "First AFL goal for X." for a player you never
## backed. Starts a seeded season, gives every player on your ground a career on
## record with no goals and no run, starts the real match screen and plays it until
## your first goal puts the line in the feed, then pauses and saves the frame.
## Needs a real renderer (windowed, through C:/kt/gpu_slot.sh, off screen):
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_first_goal.gd -- \
##       --club COL --size 390x844 --seed 2027 --out /tmp/first_goal
## Never touches a real save.

var _out := "/tmp/first_goal"


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
	gs.save_path = "user://capture_first_goal.save"
	gs.settings_path = "user://capture_first_goal.cfg"
	gs.replay_seed = int(str(a.get("seed", "2027")))
	var db = root.get_node("GameDB")
	var club := str(a.get("club", "COL"))
	gs.reset()
	gs.start_season(club, db.club_list(club))
	if not gs.prepare_interactive_match():
		print("CAPTURE FAIL: no live match")
		quit(1)
		return
	var me := 0 if str(gs.pending_match["home"]) == gs.my_club else 1
	# Every player of yours on the ground: never backed, a career on record, no goal
	# yet. Whoever kicks your first goal of the match gets the line, through the real
	# event path (PitchView -> MatchScene._story_feed).
	for row in gs.pending_sim.squads[me].ground:
		var p: Dictionary = gs.list_player(str(row["id"]))
		p["career"] = {"games": 4, "goals": 0, "stints": [], "through": gs.season_year - 1, "unknown": []}
		p.erase("backed")
		gs.season_tally.erase(str(row["id"]))
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
	pitch.set_speed(4.0)
	var feed: Node = m.find_child("Feed", true, false)
	var said := ""
	var guard := 0
	var max_frames := int(str(a.get("frames", "6000")))
	while said == "" and guard < max_frames:
		guard += 1
		await process_frame
		# A coach's call stops play: take the first option (the shot, when offered).
		if not bool(pitch.get("playing")) and guard % 60 == 0:
			var opt := _gate_option(m)
			if opt != null:
				print("CAPTURE call answered: %s" % opt.text)
				opt.pressed.emit()
		if guard % 500 == 0:
			print("CAPTURE progress frame %d | feed rows %d | playing %s" % [guard, feed.get_child_count(),
					str(pitch.get("playing"))])
		for c in feed.get_children():
			if str(c.get_meta("feed_kind", "")) == "StoryLine" and str(c.text).contains("First AFL goal for"):
				said = str(c.text)
	pitch.playing = false
	for i in range(20):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(_out + ".png")
	print("CAPTURE %s.png | %dx%d | frames %d | feed: '%s'" % [_out, w, h, guard, said])
	quit(0 if said.contains("First AFL goal for") else 1)


const _NOT_OPTIONS := ["Play", "1x", "2x", "4x", "8x", "Skip to full time", "Pause"]


func _gate_option(m: Node) -> Button:
	var first: Button = null
	for b in m.find_children("*", "Button", true, false):
		var btn := b as Button
		if not btn.is_visible_in_tree() or btn.disabled or _NOT_OPTIONS.has(btn.text):
			continue
		if btn.text.begins_with("Take the shot"):
			return btn
		if first == null:
			first = btn
	return first
