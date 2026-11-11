extends SceneTree
## Visual review tool for the full-time "Your calls" (director bug, 2026-11-12:
## it showed Q1, rarely Q2, never Q3 or Q4). Run through C:/kt/gpu_slot.sh:
##   godot --path . --script tools/visual/capture_your_calls.gd -- --out <prefix>
## Plays the first match of a --club career (seed --seed) with a call made
## before every quarter, as the coach would at each break: Q1 an Attack Corridor
## plan and a tag, Q2 a midfielder to go through, Q3 Defend First, Q4 Win the
## Contest and a forward to go through. Then writes <out>_calls.png: the Summary
## scrolled to Your calls. Never touches a real save.
##   --size WxH (default 390x844)   --club CODE (default FRE)   --seed N (default 3)

var _w := 390
var _h := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _first(sim, side: int, pos: String, skip := "") -> String:
	for p in (sim.squads[side]).ground:
		if str(p["id"]) != skip and str(p.get("role", "")) == pos:
			return str(p["id"])
	return str((sim.squads[side]).ground[0]["id"])


func _run() -> void:
	var out := "your_calls"
	var club := "FRE"
	var seed := 3
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
			"--seed":
				seed = int(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	var MN = load("res://scripts/ui/match/MatchNotes.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_your_calls.save"
	state.settings_path = "user://capture_your_calls.cfg"
	state.reset()
	state.career_seed = seed
	state.replay_seed = seed
	state.set_setting("seen_training_intro", true)
	state.start_season(club, db.club_list(club))
	if not state.prepare_interactive_match():
		push_error("no interactive match")
		quit(1)
		return
	var sim = state.pending_sim
	var me := int(sim.moment_side)
	for q in range(1, 5):
		var t: Dictionary = (sim.tactics[me] as Dictionary).duplicate()
		match q:
			1:
				t["gameplan"] = "attacking"
				for p in (sim.squads[1 - me]).ground:
					if sim.tag_target_ok(1 - me, str(p["id"])):
						t["tag_id"] = str(p["id"])
						t["tag_set"] = true
						break
			2:
				t["focus_mid"] = _first(sim, me, "MID")
			3:
				t["gameplan"] = "defensive"
			4:
				t["gameplan"] = "contest"
				t["focus_fwd"] = _first(sim, me, "FWD")
		sim.set_tactics(me, t)
		sim.run_quarter()
	var res: Dictionary = sim.result()
	res["home"] = state.pending_match["home"]
	res["away"] = state.pending_match["away"]
	res["label"] = state.pending_match["label"]
	for q in range(1, 5):
		print("Q%d lines: %s" % [q, str(MN.calls_lines(res, me, q))])
	print("summary: ", MN.full_time_calls(res, me, {}))
	state.finish_interactive_match(res)
	state.pending_sim = null
	state.pending_match = {}
	state.review_requested = true
	UK.apply_appearance("dark")
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	var full = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(full)
	await _frames(20)
	var box: Control = full.find_child("FullTimeCalls", true, false)
	if box == null:
		push_error("Your calls is not on the screen")
		quit(1)
		return
	var sc := box.get_parent()
	while sc != null and not (sc is ScrollContainer):
		sc = sc.get_parent()
	if sc != null:
		# The heading near the top, the whole list below it.
		var s := sc as ScrollContainer
		s.scroll_vertical = s.scroll_vertical + int(box.get_global_rect().position.y - s.global_position.y) - 80
	await _frames(10)
	for c in box.get_children():
		print("  shown: ", c.get_meta("plain", c.get("text")))
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(out + "_calls.png")
	print("wrote ", out, "_calls.png")
	state.delete_saved_career()
	quit(0)
