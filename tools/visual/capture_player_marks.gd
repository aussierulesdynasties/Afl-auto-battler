extends SceneTree
## Visual review tool for T3.R10 (a tired or hurt player told apart without
## colour): one live match on a phone, a still the first time one of your
## players runs out of legs, the first time a player is hurt, and the long-press
## words over each. Needs a real renderer and a window (keep it off screen with
## an override.cfg). Never touches a real save.
##   godot --path . --script tools/visual/capture_player_marks.gd -- --out <prefix> [--size 390x844] [--seed 2027]
## Writes <prefix>_<n>_<state>.png.

var _w := 390
var _h := 844
var _seed := 2027
var _out := "player_marks"
var _n := 0


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				_out = str(a[i + 1])
			"--seed":
				_seed = int(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_player_marks.save"
	state.settings_path = "user://capture_player_marks.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	state.set_vignettes_on(false)
	state.reset()
	state.replay_seed = _seed
	state.start_season("COL", db.club_list("COL"))
	state.set_match_way("watch")
	state.prepare_interactive_match()
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await _frames(20)
	var got_tired := false
	var got_hurt := false
	var got_bench := false
	var guard := 0
	var quarter := 0
	var q4_steps := 0
	var low := 100.0
	while not bool(m.get("_fulltime_shown")) and guard < 80000 and not (got_tired and got_hurt and got_bench):
		guard += 1
		var box: Node = m.find_child("CoachBox", true, false)
		if box != null:
			(box.find_child("StartQuarter", true, false) as Button).emit_signal("pressed")
			quarter += 1
			await _frames(6)
			continue
		var card: Node = m.find_child("MomentCard", true, false)
		if card != null:
			var pick: Button = card.find_child("Moment_0", true, false)
			if pick != null and not pick.disabled and pick.is_visible_in_tree():
				pick.emit_signal("pressed")
				await _frames(6)
				continue
		var replay: Node = m.find_child("BroadcastVignetteOverlay", true, false)
		if replay != null:
			m.call("_finish_broadcast")
			await _frames(6)
			continue
		var pitch = m.get("_pitch")
		if pitch != null and pitch.playing:
			pitch._process(0.25)
			var marks: Dictionary = pitch.marks
			var legs: Array = state.pending_sim.legs(int(m.get("_my_side"))) if state.pending_sim != null else []
			for r in legs:
				if bool(r["on"]):
					low = minf(low, float(r["energy"]))
			if quarter >= 4:
				q4_steps += 1
			if not got_tired and q4_steps >= 60 and q4_steps % 10 == 0 and state.pending_sim != null:
				# No player of yours ran out of legs this match: mark the most
				# tired of them as the view would, for the still only.
				got_tired = await _forced_tired(m, pitch, state)
				continue
			if not got_tired and _has(marks, "tired") and _on_ground(pitch, marks, "tired") != Vector2.INF:
				got_tired = true
				await _still(pitch, marks, "tired", "tired")
			if not got_hurt and _has(marks, "hurt"):
				got_hurt = true
				await _still(pitch, marks, "hurt", "hurt")
			if got_hurt and not got_bench and _on_bench(pitch, "hurt"):
				got_bench = true
				await _still(pitch, marks, "hurt", "hurt_bench")
		await process_frame
	print("lowest own energy on the ground: ", low)
	print("tired=", got_tired, " hurt=", got_hurt, " bench=", got_bench)
	quit()


func _forced_tired(m, pitch, state) -> bool:
	var best := ""
	var e := INF
	var tr: float = pitch.token_radius()
	var at := {}
	for t in pitch.director.tokens:
		at[str(t.get("pid", ""))] = pitch.disc_positions_drawn()[int(t["id"])]
	for r in state.pending_sim.legs(int(m.get("_my_side"))):
		var pid := str(r["id"])
		if not at.has(pid) or not Rect2(Vector2(40, 60), pitch.size - Vector2(80, 160)).has_point(at[pid]):
			continue
		var clear := true
		for q in at.values():
			if q != at[pid] and (q as Vector2).distance_to(at[pid]) < tr * 3.0:
				clear = false
		if clear and bool(r["on"]) and float(r["energy"]) < e:
			e = float(r["energy"])
			best = str(r["id"])
	if best == "":
		return false
	var marks: Dictionary = pitch.marks.duplicate()
	marks[best] = {"mark": "tired", "words": "Tired: running on empty"}
	pitch.set_marks(marks)
	print("forced tired on ", best, " at energy ", e)
	if _on_ground(pitch, marks, "tired") == Vector2.INF:
		return false
	# The scene rebuilds the marks at every event: set them again right before
	# each still.
	pitch.set_process(false)
	var p := _on_ground(pitch, marks, "tired")
	pitch.set_marks(marks)
	await _shot("tired_forced")
	pitch.set_marks(marks)
	p = _on_ground(pitch, marks, "tired")
	if p != Vector2.INF and pitch.show_tip_at(p):
		await _shot("tired_forced_held")
		pitch.tip = {}
	else:
		print("no tip for tired_forced")
	pitch.set_process(true)
	return true


func _has(marks: Dictionary, kind: String) -> bool:
	for pid in marks:
		if str(marks[pid]["mark"]) == kind:
			return true
	return false


## Where a disc with this mark sits on the oval (in the pitch view), or INF.
func _on_ground(pitch, marks: Dictionary, kind: String) -> Vector2:
	for t in pitch.director.tokens:
		var m: Dictionary = marks.get(str(t.get("pid", "")), {})
		if not m.is_empty() and str(m["mark"]) == kind and float(t["down"]) <= 0.0:
			var p: Vector2 = pitch.disc_positions_drawn()[int(t["id"])]
			if Rect2(Vector2(20, 20), pitch.size - Vector2(40, 40)).has_point(p):
				return p
	return Vector2.INF


## Whether a man with this mark is on the bench: he is in the bench's drawer
## now, not on the view (BenchDrawer.rows).
func _on_bench(pitch, kind: String) -> bool:
	for row in pitch.bench_drawer().rows():
		if str(row["mark"]) == kind:
			return true
	return false


## The plain still, then the bench's drawer open when the marked player is in it
## (a hurt man is usually taken off), then the long-press words over him on the
## ground.
func _still(pitch, marks: Dictionary, kind: String, tag: String) -> void:
	await _frames(4)
	await _shot(tag)
	if _on_bench(pitch, kind):
		pitch.open_bench()
		await _frames(2)
		await _shot(tag + "_bench")
		pitch.close_bench()
		await _frames(2)
	var p := _on_ground(pitch, marks, kind)
	if p != Vector2.INF and pitch.show_tip_at(p):
		await _frames(2)
		await _shot(tag + "_held")
		pitch.tip = {}
	else:
		print("no tip for ", tag)


func _shot(name: String) -> void:
	_n += 1
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	if img == null:
		print("no renderer: ", name)
		return
	var path := "%s_%02d_%s.png" % [_out, _n, name]
	img.save_png(path)
	print("wrote ", path)


func _frames(n: int) -> void:
	for i in n:
		await process_frame
