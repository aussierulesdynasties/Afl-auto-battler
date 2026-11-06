extends SceneTree
## Row 121 (T5.r152): the live feed's "Career-best ... for X." line. Starts a seeded
## season, gives every player on your ground a full recorded career of eight games
## with modest bests, starts the real match screen and plays it (answering any
## call, starting each quarter) until the feed says a career best through the real
## event path (PitchView -> MatchScene._career_high_feed), then pauses and saves
## the frame.
## Needs a real renderer (windowed, through C:/kt/gpu_slot.sh, off screen via override.cfg):
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_career_best.gd -- \
##       --club COL --size 390x844 --seed 2027 --out /tmp/career_best
## Never touches a real save.

var _out := "/tmp/career_best"


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
	gs.save_path = "user://capture_career_best.save"
	gs.settings_path = "user://capture_career_best.cfg"
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
	# Every player of yours on the ground: eight games, all on record, bests just
	# under the floors, so the first to pass one is said.
	for row in gs.pending_sim.squads[me].ground:
		var id := str(row["id"])
		var p: Dictionary = gs.list_player(id)
		p["career"] = {"games": 8, "goals": 6, "stints": [], "through": gs.season_year - 1, "unknown": []}
		gs.season_tally.erase(id)
		p["highs"] = {"full": true, "games": gs.games_played(p), "last": "",
				"goals": {"n": 2, "year": gs.season_year - 1, "label": "Round 3"},
				"disposals": {"n": 17, "year": gs.season_year - 1, "label": "Round 5"},
				"marks": {"n": 5, "year": gs.season_year - 1, "label": "Round 6"},
				"tackles": {"n": 4, "year": gs.season_year - 1, "label": "Round 2"}}
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	for i in range(10):
		await process_frame
	var cands: Dictionary = m.get("_duel_mem").get("career_high", {})
	print("CAPTURE candidates %d" % cands.size())
	var pitch = m.get("_pitch")
	var feed: Node = m.find_child("Feed", true, false)
	var said := ""
	var guard := 0
	var max_frames := int(str(a.get("frames", "40000")))
	while said == "" and guard < max_frames:
		guard += 1
		await process_frame
		if not bool(pitch.get("playing")) and guard % 60 == 0:
			var start: Button = m.find_child("StartQuarter", true, false)
			if start != null and start.is_visible_in_tree() and not start.disabled:
				start.pressed.emit()
				pitch.set_speed(8.0)
			else:
				var opt := _gate_option(m)
				if opt != null:
					print("CAPTURE call answered: %s" % opt.text)
					opt.pressed.emit()
		if guard % 1000 == 0:
			print("CAPTURE progress frame %d | feed rows %d | playing %s" % [guard, feed.get_child_count(),
					str(pitch.get("playing"))])
		for c in feed.get_children():
			if str(c.get_meta("feed_kind", "")) == "CareerHighLine":
				said = str(c.get_meta("plain", c.text))
	pitch.playing = false
	# Close any explainer left open, so the frame shows the feed.
	for b in m.find_children("*", "Button", true, false):
		if (b as Button).is_visible_in_tree() and (b as Button).text == "Got it":
			(b as Button).pressed.emit()
	for i in range(30):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(_out + ".png")
	print("CAPTURE %s.png | %dx%d | frames %d | feed: '%s'" % [_out, w, h, guard, said])
	quit(0 if said.contains("Career-best") else 1)


const _NOT_OPTIONS := ["Play", "1x", "2x", "4x", "8x", "Skip to full time", "Pause"]


func _gate_option(m: Node) -> Button:
	var first: Button = null
	for b in m.find_children("*", "Button", true, false):
		var btn := b as Button
		if not btn.is_visible_in_tree() or btn.disabled or btn.text == "" or _NOT_OPTIONS.has(btn.text):
			continue
		if btn.text.begins_with("Take the shot"):
			return btn
		if first == null:
			first = btn
	return first
