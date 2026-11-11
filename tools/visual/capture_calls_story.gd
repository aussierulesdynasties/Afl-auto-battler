extends SceneTree
## Visual review tool for row 144 (our calls in the full-time story). Run through
## C:/kt/gpu_slot.sh, or capture.yml:
##   gh workflow run capture.yml --ref <branch> -f tool=capture_calls_story \
##       -f args="--club FRE --size 390x844"
## Plays first-match career seeds of --club with three of our calls made at the
## first bounce (an Attack Corridor game plan, a Fire them up pep talk and a tag
## on their first taggable midfielder) until full time tells at least --calls of
## them, then writes <out>_top.png (the result) and <out>_calls.png (the Summary
## scrolled to Our calls). Never touches a real save.
##   --size WxH (default 390x844)   --club CODE (default FRE)   --calls N (default 2)
##   --max N   seeds to look through (default 60)

var _w := 390
var _h := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _start(state, db, club: String, seed: int) -> bool:
	state.autosave_enabled = false
	state.save_path = "user://capture_calls_story.save"
	state.settings_path = "user://capture_calls_story.cfg"
	state.reset()
	state.career_seed = seed
	state.replay_seed = seed
	state.set_setting("seen_training_intro", true)
	state.start_season(club, db.club_list(club))
	return state.prepare_interactive_match()


## Our calls at the first bounce, as the coach would make them on the match screen.
func _make_calls(sim) -> void:
	var me := int(sim.moment_side)
	var t: Dictionary = (sim.tactics[me] as Dictionary).duplicate()
	t["gameplan"] = "attacking"
	t["pep"] = "fire_up"
	for p in (sim.squads[1 - me]).ground:
		if sim.tag_target_ok(1 - me, str(p["id"])):
			t["tag_id"] = str(p["id"])
			t["tag_set"] = true
			break
	sim.set_tactics(me, t)


func _play(state, db, club: String, seed: int) -> Dictionary:
	if not _start(state, db, club, seed):
		return {}
	var sim = state.pending_sim
	_make_calls(sim)
	for q in range(4):
		sim.run_quarter()
	var res: Dictionary = sim.result()
	res["home"] = state.pending_match["home"]
	res["away"] = state.pending_match["away"]
	res["label"] = state.pending_match["label"]
	return res


func _run() -> void:
	var out := "calls_story"
	var club := "FRE"
	var want := 2
	var max_seeds := 60
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
			"--calls":
				want = int(a[i + 1])
			"--max":
				max_seeds = int(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	var MS = load("res://scripts/sim/MatchStory.gd")
	var found := -1
	for seed in range(1, max_seeds + 1):
		var res := _play(state, db, club, seed)
		if res.is_empty():
			continue
		var me := 0 if str(res["home"]) == club else 1
		var c: Dictionary = MS.calls(res, me)
		var n := 0
		for r in c.get("rows", []):
			n += 1 if str(r["kind"]) == "call" else 0
		if n >= want:
			found = seed
			print("seed ", seed, " score ", res["score"], " margin ", c["margin"])
			for r in c["rows"]:
				print("  ", r["text"], "  [", r["kind"], " ", r["pts"], "]")
			print("  impact mine ", res["impact"][me])
			print("  impact theirs ", res["impact"][1 - me])
			break
	if found < 0:
		push_error("no seed with %d calls told" % want)
		quit(1)
		return
	var res2 := _play(state, db, club, found)
	state.finish_interactive_match(res2)
	state.pending_sim = null
	state.pending_match = {}
	state.review_requested = true
	UK.apply_appearance("dark")
	_size_window()
	var full = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(full)
	await _frames(20)
	_save(out + "_top.png")
	var grid: Control = full.find_child("CallsStory", true, false)
	if grid == null:
		push_error("Our calls is not on the screen")
		quit(1)
		return
	var sc := grid.get_parent()
	while sc != null and not (sc is ScrollContainer):
		sc = sc.get_parent()
	if sc != null:
		# The whole of Our calls in view: its last row (the final margin) near the bottom.
		var s := sc as ScrollContainer
		var bottom := grid.get_global_rect().end.y
		s.scroll_vertical = s.scroll_vertical + int(bottom - (s.global_position.y + s.size.y)) + 16
	await _frames(10)
	print("calls grid on screen: ", grid.get_global_rect())
	_save(out + "_calls.png")
	state.delete_saved_career()
	quit(0)


func _size_window() -> void:
	if _w >= 760:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
