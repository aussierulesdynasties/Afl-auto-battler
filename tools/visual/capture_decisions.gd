extends SceneTree
## Visual review for the in-match call scenes (DecisionVignette) and the centre bounce
## (StoppageVignette): each scene alone at the window's size, a still per beat. Needs a real
## renderer (windowed, through C:/kt/gpu_slot.sh on this machine):
##   godot --path . --windowed --script tools/visual/capture_decisions.gd -- --out DIR [--size 390x844]
## Writes DIR/call_scene_<kind>_beat<0-4>_<size>.png and DIR/centre_bounce_scene_beat<0-4>_<size>.png:
## beats 0-2 playing in, 3 the freeze, 4 the freeze with the call's room taken off the bottom
## and (where the scene keeps moving) 0.7 s later. Fremantle v Melbourne, seeded.
## --kinds tired,duel,...,bounce: only those. --weather wet (or windy, hot). --clubs FRE,MEL.
## --live SECONDS: the scenes open over a real match screen's oval, SECONDS into the first
## quarter (the club is --clubs' first, the opponent whoever the fixture gives), so every
## man stands where the live oval has him, as in a game. Prints LIVE lines. --live release:
## the oval's play released at once instead, as tests/run_decision_scenes_tests.gd stages it
## (with --clubs COL,<any>: the suite's own spots).
## Prints FRAMING lines (the scene's own projection: horizon, heads, boots, how much of the
## frame is turf) and ART lines: every figure move drawn (strip and frames asked for), proof
## the sheet's moves were used and not a fallback.

var W := 390
var H := 844
const BEATS := [0.3, 1.2, 2.2, 99.0, 100.0]


func _initialize() -> void:
	create_timer(300.0).timeout.connect(func() -> void:
		print("TIMED OUT")
		quit(1))
	_run.call_deferred()


func _run() -> void:
	var out := "/tmp/decisions"
	var a := OS.get_cmdline_user_args()
	var kinds := ["tired", "duel", "hot", "momentum", "set_shot", "bounce"]
	var weather := ""
	var clubs := ["FRE", "MEL"]
	var live_after := -1.0
	var release := false
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out": out = str(a[i + 1])
			"--weather": weather = str(a[i + 1])
			"--kinds": kinds = Array(str(a[i + 1]).split(","))
			"--clubs": clubs = Array(str(a[i + 1]).split(","))
			"--live":
				release = str(a[i + 1]) == "release"
				live_after = 0.0 if release else float(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				W = int(wh[0])
				H = int(wh[1])
	await process_frame
	DirAccess.make_dir_recursive_absolute(out)
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	for i in range(6):
		await process_frame
	var squad_script = load("res://scripts/sim/Squad.gd")
	var sim = load("res://scripts/sim/MatchSim.gd").new(squad_script.new(clubs[0], db.club_list(clubs[0]), true, clubs[0]),
			squad_script.new(clubs[1], db.club_list(clubs[1]), false, clubs[1]), 2027)
	var me := 0
	var live := {}
	if live_after >= 0.0:
		state.reset()
		state.replay_seed = 2027
		state.start_season(clubs[0], db.club_list(clubs[0]))
		state.prepare_interactive_match()
		var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
		root.add_child(m)
		for i in range(8):
			await process_frame
		(m.find_child("StartQuarter", true, false) as Button).emit_signal("pressed")
		for i in range(8):
			await process_frame
		var pitch = m.get("_pitch")
		if release:
			m.set("_skipping", true)
			pitch.release_all()
			m.set("_skipping", false)
		var left := live_after
		while left > 0.0:
			pitch.director.advance(0.1)
			left -= 0.1
		sim = state.pending_sim
		me = int(m.get("_my_side"))
		live = m.call("_live_spots")
		print("LIVE %s v %s, %.0f s in, %d men on the oval" % [sim.squads[me].code, sim.squads[1 - me].code, live_after, live.size()])
		m.visible = false
		m.process_mode = Node.PROCESS_MODE_DISABLED
	if weather != "":
		sim.weather = weather
	var DV = load("res://scripts/ui/match/DecisionVignette.gd")
	var Stoppage = load("res://scripts/ui/match/StoppageVignette.gd")
	Stoppage.log_frames = true
	Stoppage.frame_log.clear()
	sim.moment_side = me
	var moments: Dictionary = _moments(sim, me)
	var canvas: Vector2 = root.get_visible_rect().size
	print("CAPTURE window %dx%d, canvas %s" % [W, H, str(canvas)])
	for k in kinds:
		var vig
		if k == "bounce":
			vig = Stoppage.new()
		else:
			vig = DV.new()
		root.add_child(vig)
		vig.size = canvas
		vig.set_process(false)
		vig.live_spots = live
		await process_frame
		if k == "bounce":
			vig.setup(sim, me, "Centre bounce")
		else:
			vig.setup_decision(sim, me, moments[k])
		for tk in vig.tokens:
			print("TOK ", k, " ", tk.get("role", tk.get("slot", "")), " ", tk["name"], " ", tk["from"], "->", tk["to"])
		for c in range(BEATS.size()):
			var t: float = BEATS[c]
			if t > 50.0:
				vig.finish_now()
				vig.set("_hold", 0.4)
				if t > 99.5:
					vig.call_room = canvas.y * (0.3 if W > H else 0.4)
					vig.call("_process", 0.35)
					vig.call("_process", 0.35)
				print("FRAMING %s beat%d %dx%d %s" % [k, c, W, H, str(vig.shot_numbers())])
			else:
				vig.set("_t", t)
			vig.queue_redraw()
			for i in range(3):
				await process_frame
			var img: Image = root.get_viewport().get_texture().get_image()
			img.convert(Image.FORMAT_RGBA8)
			var stem := "centre_bounce_scene" if k == "bounce" else "call_scene_%s" % k
			img.save_png("%s/%s_beat%d_%dx%d.png" % [out, stem, c, W, H])
		print("TAGS %s %s" % [k, str(vig.tag_log)])
		vig.queue_free()
		await process_frame
	print("wrote ", out)
	var seen := {}
	for e in Stoppage.frame_log:
		var key := "%s/%s" % [e["anim"], e["facing"]]
		if not seen.has(key):
			seen[key] = {"frames": int(e["frames"]), "max_wanted": 0}
		seen[key]["max_wanted"] = maxi(int(seen[key]["max_wanted"]), int(e["wanted"]))
	for key in seen:
		print("ART ", key, " frames ", seen[key]["frames"], " max wanted ", seen[key]["max_wanted"])
	quit(0)


## One hand-built moment per kind from the real squads (ids the way MatchSim fires them).
func _moments(sim, me: int) -> Dictionary:
	var them := 1 - me
	var mine: Array = sim.squads[me].ground
	var theirs: Array = sim.squads[them].ground
	var fwd = theirs.filter(func(p): return str(p["role"]) == "FWD")[0]
	var mid = theirs.filter(func(p): return str(p["role"]) == "MID")[0]
	var dfn = mine.filter(func(p): return str(p["role"]) == "DEF")[0]
	var star = mine[0]
	var sub = sim.squads[me].bench[0]
	sim.duels[me][str(fwd["id"])] = str(dfn["id"])
	return {
		"tired": {"kind": "tired", "title": "Running on empty", "player_id": star["id"], "sub_id": sub["id"]},
		"duel": {"kind": "duel", "title": "Getting on top", "player_id": fwd["id"]},
		"hot": {"kind": "hot", "title": "Kicking a bag", "player_id": mid["id"]},
		"momentum": {"kind": "momentum", "title": "They are on a run"},
		"set_shot": {"kind": "set_shot", "title": "Set shot", "player_id": star["id"], "defender_id": theirs.filter(func(p): return str(p["role"]) == "DEF")[0]["id"]},
	}
