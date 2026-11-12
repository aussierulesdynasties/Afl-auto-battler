extends SceneTree
## The match scenes in every weather at every time of day (VignetteWeather, VignetteKickoff;
## TODO row 166): the centre bounce, a coach's call, a replay and the pre-match, each in
## perfect, wet, windy and hot weather as a day, a twilight and a night game, on a phone
## (390x844) and a PC (1920x1080). Fremantle v Melbourne at Optus Stadium.
##   godot --path . --script tools/visual/capture_weather.gd -- --out C:/caps/after
##       [--sizes phone,pc] [--slots day,twilight,night] [--weathers perfect,wet,windy,hot]
##       [--scenes bounce,call,replay,prematch] [--old-turf] [--wind -1]
## Writes <out>/<size>_<scene>_<weather>_<slot>.png. Reduced motion is on, so the grain
## and the rain hold still and two runs of the same picture can be compared pixel for pixel.
## --old-turf draws the wide mown bands the ground had before (VignetteGround.fine_turf
## off): with --slots night --weathers perfect it is the picture main draws, for the proof
## that night did not change. On a checkout without the time of day (main) every frame is
## a night one whatever --slots says; pass --slots night there.
## --wind -1: the breeze blows to the near end (the scenes do not say yet which end it is).
## Needs a real renderer and a window (C:/kt/gpu_slot.sh). Nothing here touches a save.

const SIZES := {"phone": Vector2i(390, 844), "pc": Vector2i(1920, 1080)}
const HOME := "FRE"
const AWAY := "MEL"

var _state
var _db
var _sim
var _star: Dictionary
var _opp
var _wind := 1


func _initialize() -> void:
	_run.call_deferred()


func _list(a: PackedStringArray, flag: String, all: Array) -> Array:
	for i in range(a.size() - 1):
		if str(a[i]) == flag:
			return Array(str(a[i + 1]).split(","))
	return all


func _run() -> void:
	var out := "/tmp/weather"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		elif str(a[i]) == "--wind":
			_wind = int(a[i + 1])
	var sizes := _list(a, "--sizes", ["phone", "pc"])
	var slots := _list(a, "--slots", ["day", "twilight", "night"])
	var weathers := _list(a, "--weathers", ["perfect", "wet", "windy", "hot"])
	var scenes := _list(a, "--scenes", ["bounce", "call", "replay", "prematch"])
	DirAccess.make_dir_recursive_absolute(out)
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.save_path = "user://capture.save"
	_state.settings_path = "user://capture_settings.cfg"
	_state.reset()
	_state.career_seed = 2026
	_state.replay_seed = 2026
	_state.set_reduced_motion(true)
	load("res://scripts/ui/Feel.gd").set("reduced", true)
	_state.start_season(HOME, _db.club_list(HOME))
	_state.prepare_interactive_match()
	_sim = _state.pending_sim
	_opp = load("res://scripts/sim/Squad.gd").new(AWAY, _state.season.lists[AWAY], false, AWAY)
	_star = _db.club_list(HOME)[0]
	var ground: Script = load("res://scripts/ui/match/VignetteGround.gd")
	var kickoff: Script = null
	if ResourceLoader.exists("res://scripts/ui/match/VignetteKickoff.gd"):
		kickoff = load("res://scripts/ui/match/VignetteKickoff.gd")
	ground.call("use_match", {"home": HOME, "away": AWAY, "label": "Round 1"})
	if a.has("--old-turf"):
		ground.set("fine_turf", false)
	var grade: Script = load("res://scripts/ui/match/VignetteGrade.gd")
	var n := 0
	for size_name in sizes:
		var px: Vector2i = SIZES[size_name]
		root.size = px
		DisplayServer.window_set_size(px)
		for i in range(6):
			await process_frame
		for slot in slots:
			if kickoff != null:
				kickoff.set("forced_slot", slot)
			for w in weathers:
				grade.set("forced_weather", w)
				for scene in scenes:
					var node: Control = _open(scene, w, Vector2(px))
					var img := await _shot(node, _time(scene))
					img.save_png("%s/%s_%s_%s_%s.png" % [out, size_name, scene, w, slot])
					n += 1
	print("wrote %d frames to %s" % [n, out])
	quit()


func _time(scene: String) -> float:
	match scene:
		"bounce":
			return 3.3
		"call":
			return 2.0
		"replay":
			return 1.3
	return -1.0


## One scene, opened at the window's size, stopped (its time is set by _shot).
func _open(scene: String, w: String, px: Vector2) -> Control:
	match scene:
		"bounce":
			# The centre bounce, just before the ball goes up.
			var bounce: Control = load("res://scripts/ui/match/StoppageVignette.gd").new()
			root.add_child(bounce)
			bounce.size = px
			bounce.call("setup", _sim, 0, "Centre bounce")
			bounce.set("weather", w)
			_blow(bounce)
			bounce.set_process(false)
			return bounce
		"call":
			# A coach's call: his star is running on empty, a fresh man waits on the bench.
			var mine: Array = _state.my_squad().ground
			var sub: Dictionary = _state.my_squad().bench[0]
			_sim.set("weather", w)
			var call_scene: Control = load("res://scripts/ui/match/DecisionVignette.gd").new()
			root.add_child(call_scene)
			call_scene.size = px
			call_scene.call("setup_decision", _sim, 0, {"kind": "tired", "title": "Running on empty",
					"player_id": mine[0]["id"], "sub_id": sub["id"]})
			_blow(call_scene)
			call_scene.set_process(false)
			return call_scene
		"replay":
			# A replay: the speccy, at the moment of the mark.
			var vig: Control = load("res://scripts/ui/match/BroadcastVignette.gd").new()
			root.add_child(vig)
			vig.size = px
			vig.call("setup", "speccy_front", {"kind": "mark", "side": 0, "num": int(_star.get("num", 7)),
					"player_id": str(_star["id"]), "club": HOME, "q": 4}, {}, {"home": HOME, "away": AWAY, "weather": w})
			_blow(vig)
			vig.set_process(false)
			return vig
	# The pre-match: the side in its huddle.
	var pre: Control = load("res://scripts/ui/match/PreMatchVignette.gd").open(root, HOME, AWAY,
			_state.my_squad().ground + _state.my_squad().bench, _opp.ground + _opp.bench,
			"Round 1", false, {"weather": w})
	pre.set_process(false)
	pre.set("_t", 0.76)
	pre.call("set_progress", 0.6)
	return pre


## Says which end the breeze blows to, on the scene's scoreboard (its board).
func _blow(node: Control) -> void:
	for key in ["_board", "_screen_board"]:
		var board = node.get(key)
		if board is Dictionary:
			(board as Dictionary)["wind"] = _wind


## A still of node at its time t (t < 0: as it is), then removed.
func _shot(node: Control, t: float) -> Image:
	if t >= 0.0:
		node.set("_t", t)
	for i in range(5):
		node.queue_redraw()
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if node.get_parent() == root:
		node.queue_free()
	else:
		node.get_parent().queue_free()
	await process_frame
	await process_frame
	return img
