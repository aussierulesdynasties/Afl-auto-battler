extends SceneTree
## Visual review for the in-match decision scenes (DecisionVignette, TODO row 13): each
## call kind on a phone, four beats down the page. Needs a real renderer.
##   godot --path . --script tools/visual/capture_decisions.gd -- --out /tmp/decisions
## --scale N: render the 390x844 phone at N times the pixels. --window WxH: a desktop window.
## --kinds tired,duel,...: only those. Prints ART lines: every figure move the scenes drew
## (strip and frames asked for), proof the sheet's moves were used and not a fallback.

var W := 390
var H := 844
const BEATS := [0.3, 1.2, 2.2, 99.0]


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "/tmp/decisions"
	var a := OS.get_cmdline_user_args()
	var scale := 1
	var kinds := ["tired", "duel", "hot", "momentum", "set_shot"]
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--scale":
			scale = maxi(1, int(a[i + 1]))
		if str(a[i]) == "--kinds":
			kinds = str(a[i + 1]).split(",")
		if str(a[i]) == "--window":
			var wh := str(a[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
			scale = 1
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	state.replay_seed = 2027
	state.reset()
	state.start_season("COL", db.club_list("COL"))
	root.get_node("ScreenLayout").ui_scale = float(scale)
	root.size = Vector2i(W * scale, H * scale)
	DisplayServer.window_set_size(Vector2i(W * scale, H * scale))
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_EXPAND
	root.content_scale_size = Vector2i(W, H)
	state.prepare_interactive_match()
	var sim = state.pending_sim
	var DV = load("res://scripts/ui/match/DecisionVignette.gd")
	var Stoppage = load("res://scripts/ui/match/StoppageVignette.gd")
	Stoppage.log_frames = true
	Stoppage.frame_log.clear()
	var me := 0
	sim.moment_side = me
	var moments: Dictionary = _moments(sim, me)
	var sheet := Image.create(W * scale * BEATS.size(), H * scale * kinds.size(), false, Image.FORMAT_RGBA8)
	for r in range(kinds.size()):
		var k: String = kinds[r]
		var vig = DV.new()
		root.add_child(vig)
		vig.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		vig.set_process(false)
		await process_frame
		vig.setup_decision(sim, me, moments[k])
		for tk in vig.tokens:
			print("TOK ", k, " ", tk["role"], " ", tk["name"], " ", tk["from"], "->", tk["to"])
		for c in range(BEATS.size()):
			var t: float = BEATS[c]
			if t > 50.0:
				vig.finish_now()
				vig.set("_hold", 0.4)
			else:
				vig.set("_t", t)
			vig.queue_redraw()
			for i in range(3):
				await process_frame
			var img: Image = root.get_viewport().get_texture().get_image()
			img.convert(Image.FORMAT_RGBA8)
			sheet.blit_rect(img, Rect2i(0, 0, W * scale, H * scale), Vector2i(c * W * scale, r * H * scale))
		vig.queue_free()
	sheet.save_png(out + "_sheet.png")
	print("wrote ", out + "_sheet.png")
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
