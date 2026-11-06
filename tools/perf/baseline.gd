extends SceneTree
## Performance baseline on this machine (no phone). Needs a real renderer, so it
## is not headless; run it offscreen with the Mobile renderer via
## tools/perf/run_baseline.sh, which sets that up and isolates the save folder.
## godot --path . --rendering-method mobile --script tools/perf/baseline.gd -- [--out FILE]
## Prints PERF lines; the same lines go to FILE when given. Measures: GameDB
## boot, each main scene's load and first draw (the Hub twice: first load,
## then again with the resources cached), autosave, the first broadcast
## vignette's frame hitch, and a match's frame times and draw calls.
## Nothing here touches a real save or the sim's results.

var _lines: Array = []


func _initialize() -> void:
	_run.call_deferred()


func _say(s: String) -> void:
	print(s)
	_lines.append(s)


func _median(a: Array) -> float:
	if a.is_empty():
		return 0.0
	var b := a.duplicate()
	b.sort()
	return float(b[b.size() / 2])


func _pct(a: Array, p: float) -> float:
	if a.is_empty():
		return 0.0
	var b := a.duplicate()
	b.sort()
	return float(b[mini(b.size() - 1, int(p * b.size()))])


func _frames(n: int, host: Node = null) -> Dictionary:
	# Real frame times and draw calls over n frames.
	var dts: Array = []
	var calls: Array = []
	var last := Time.get_ticks_usec()
	for i in range(n):
		await process_frame
		var now := Time.get_ticks_usec()
		dts.append((now - last) / 1000.0)
		last = now
		calls.append(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
	return {"dts": dts, "calls": calls}


func _run() -> void:
	var out := ""
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
	await process_frame
	var db = root.get_node("GameDB")
	var gs = root.get_node("GameState")
	var router = root.get_node("Router")
	if "--screens" in a:
		await _screens(db, gs)
		_write(out)
		quit()
		return
	_say("PERF renderer %s | adapter %s | window %s" % [
			str(ProjectSettings.get_setting("rendering/renderer/rendering_method")),
			RenderingServer.get_video_adapter_name(), str(root.size)])
	_say("PERF engine start to first script frame %d ms (includes the GameDB and autoload boot)" % Time.get_ticks_msec())

	var t := Time.get_ticks_usec()
	db.reload()
	_say("PERF GameDB reload %.0f ms (%d clubs)" % [(Time.get_ticks_usec() - t) / 1000.0, db.clubs.size() if "clubs" in db else 0])

	gs.autosave_enabled = false
	seed(43000)
	gs.reset()
	gs.start_season("GEE", db.club_list("GEE"))

	# Scene loads: load, then add and wait for the first drawn frame.
	for key in ["hub", "hub", "list", "selection", "training", "staff", "coaching", "offseason", "season_review"]:
		var path: String = str(router.SCENES[key])
		var t0 := Time.get_ticks_usec()
		var ps: PackedScene = load(path)
		var t1 := Time.get_ticks_usec()
		var inst: Node = ps.instantiate()
		root.add_child(inst)
		var t2 := Time.get_ticks_usec()
		await process_frame
		await process_frame
		var t3 := Time.get_ticks_usec()
		_say("PERF scene %-14s load %5.0f ms | instance and ready %5.0f ms | first draw %5.0f ms" % [
				key + (" (again)" if key == "hub" and _lines.back().find("scene hub ") >= 0 else ""),
				(t1 - t0) / 1000.0, (t2 - t1) / 1000.0, (t3 - t2) / 1000.0])
		inst.queue_free()
		await process_frame

	# Autosave.
	gs.autosave_enabled = true
	var times: Array = []
	for i in range(7):
		gs.mark_dirty()
		var s0 := Time.get_ticks_usec()
		gs.save_career()
		times.append((Time.get_ticks_usec() - s0) / 1000.0)
	var size := 0
	var f := FileAccess.open(gs.save_path, FileAccess.READ)
	if f != null:
		size = f.get_length()
	_say("PERF autosave median %.0f ms, slowest %.0f ms, file %.1f MB" % [_median(times), float(_pct(times, 1.0)), size / 1048576.0])
	gs.autosave_enabled = false

	# First broadcast vignette: the frame times around its first draw.
	var squad: Array = db.club_list("COL")
	var star: Dictionary = squad[0]
	var ev := {"kind": "goal", "side": 0, "num": int(star.get("num", 7)), "player_id": str(star["id"]),
			"club": "COL", "q": 4, "set_shot": false, "crumb": false}
	var vig = load("res://scripts/ui/match/BroadcastVignette.gd").new()
	root.add_child(vig)
	vig.size = Vector2(root.size)
	var v0 := Time.get_ticks_usec()
	vig.setup("goal_line", ev, {}, {"home": "COL", "away": "CAR"})
	var setup_ms := (Time.get_ticks_usec() - v0) / 1000.0
	var fr: Dictionary = await _frames(30)
	_say("PERF first vignette (goal_line) setup %.0f ms; first frame %.0f ms, then median %.1f ms, slowest %.1f ms" % [
			setup_ms, float((fr["dts"] as Array)[0]), _median((fr["dts"] as Array).slice(1)), float(_pct((fr["dts"] as Array).slice(1), 1.0))])
	vig.queue_free()
	await process_frame

	# A match in the live view: frame times and draw calls.
	var squad_script = load("res://scripts/sim/Squad.gd")
	var sim = load("res://scripts/sim/MatchSim.gd").new(
			squad_script.new("GEE", db.club_list("GEE"), true, "GEE"),
			squad_script.new("COL", db.club_list("COL"), false, "COL"), 42)
	var m0 := Time.get_ticks_usec()
	var res: Dictionary = sim.run()
	_say("PERF MatchSim.run %.0f ms (%d events)" % [(Time.get_ticks_usec() - m0) / 1000.0, (res["events"] as Array).size()])
	res["home"] = "GEE"
	res["away"] = "COL"
	var pitch = load("res://scripts/ui/PitchView.gd").new()
	pitch.size = Vector2(root.size)
	root.add_child(pitch)
	await process_frame
	pitch.setup(res)
	pitch.set_speed(1.0)
	pitch.play()
	var mf: Dictionary = await _frames(600)
	var d: Array = mf["dts"]
	var c: Array = mf["calls"]
	var slow := d.filter(func(x): return x > 33.4).size()
	_say("PERF match view, 600 frames: median %.1f ms, 95th %.1f ms, slowest %.1f ms, %d frames over 33 ms; draw calls median %d, most %d" % [
			_median(d), _pct(d, 0.95), float(_pct(d, 1.0)), slow, int(_median(c)), int(_pct(c, 1.0))])
	_write(out)
	quit()


func _write(out: String) -> void:
	if out != "":
		var wf := FileAccess.open(out, FileAccess.WRITE)
		for l in _lines:
			wf.store_line(str(l))


## --screens: the screens that carry the team oval (TeamBuilder), opened as a
## tap opens them, early (after round 3) and late (after round 20) in a seeded
## season: Season stats > Awards (tab tap to the first drawn frame), the
## ladder's team view (a club's side sheet) and My list. Median of RUNS. Then
## the oval's own share of the Awards open: building it, laying out its cards
## (_place_spots) and how often it redraws, idle and while the page scrolls.
const RUNS := 5


func _first_drawn(found: Callable) -> float:
	# From now to the end of the first frame drawn once `found` is true.
	var t0 := Time.get_ticks_usec()
	while true:
		await RenderingServer.frame_post_draw
		if found.call():
			return (Time.get_ticks_usec() - t0) / 1000.0
	return 0.0


func _screens(db, gs) -> void:
	_say("PERF screens: window %s, logical %s" % [str(root.size), str(root.content_scale_size)])
	gs.autosave_enabled = false
	gs.replay_seed = 4242
	gs.reset()
	gs.start_season("GEE", db.club_list("GEE"))
	for intro in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		gs.set_setting("seen_%s_intro" % intro, true)
	gs.set_setting("seen_season_stats_intro", true)
	var hub_script = load("res://scripts/ui/StatsHubScene.gd")
	var ladder_script = load("res://scripts/ui/stats/StatsLadder.gd")
	var builder_script = load("res://scripts/ui/TeamBuilder.gd")
	for upto in [3, 20]:
		while gs.season.round_index < upto:
			gs.advance()
		var tag := "after round %d" % gs.season.round_index
		var awards: Array = []
		var team: Array = []
		var lists: Array = []
		var aa_layouts: Array = []
		for run in range(RUNS):
			# Awards: on the ladder, tap the Awards tab.
			hub_script.current = "ladder"
			var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
			root.add_child(s)
			for i in range(4):
				await process_frame
			var tab: Button = s.find_child("Section_awards", true, false)
			builder_script.layouts = 0
			var t0 := Time.get_ticks_usec()
			tab.emit_signal("pressed")
			await _first_drawn(func(): return s.find_child("AATeam", true, false) != null)
			awards.append((Time.get_ticks_usec() - t0) / 1000.0)
			aa_layouts.append(int(builder_script.layouts))
			# The team view: a club's side sheet from the ladder.
			hub_script.current = "ladder"
			s.call("_build")
			for i in range(3):
				await process_frame
			t0 = Time.get_ticks_usec()
			ladder_script._side_sheet(s, "COL")
			await _first_drawn(func(): return s.find_child("TeamBuilder", true, false) != null)
			team.append((Time.get_ticks_usec() - t0) / 1000.0)
			s.queue_free()
			await process_frame
			# My list.
			t0 = Time.get_ticks_usec()
			var l: Control = load("res://scenes/ListScene.tscn").instantiate()
			root.add_child(l)
			await _first_drawn(func(): return true)
			lists.append((Time.get_ticks_usec() - t0) / 1000.0)
			l.queue_free()
			await process_frame
		_say("PERF screen open (%s), median of %d: Awards tab %.0f ms | team view %.0f ms | My list %.0f ms   (runs: %s | %s | %s; oval layouts per Awards open: %s)" % [
				tag, RUNS, _median(awards), _median(team), _median(lists),
				_runs(awards), _runs(team), _runs(lists), _runs(aa_layouts)])
		# The oval's share of the Awards open.
		hub_script.current = "awards"
		var h: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
		root.add_child(h)
		for i in range(4):
			await process_frame
		var aa: Control = h.find_child("AATeam", true, false)
		var build_all: Array = []
		var build_oval: Array = []
		var place: Array = []
		for run in range(RUNS):
			var b0 := Time.get_ticks_usec()
			var sec: Control = load("res://scripts/ui/stats/StatsAwards.gd").build(h)
			build_all.append((Time.get_ticks_usec() - b0) / 1000.0)
			sec.free()
			var tb: Control = builder_script.new()
			tb.field_only = true
			b0 = Time.get_ticks_usec()
			tb.setup(aa.call("side"), false, gs.my_list, true)
			build_oval.append((Time.get_ticks_usec() - b0) / 1000.0)
			tb.free()
			aa.set("_placed_for", Vector2(-1, -1))
			b0 = Time.get_ticks_usec()
			aa.call("_place_spots")
			place.append((Time.get_ticks_usec() - b0) / 1000.0)
		var pitch: Control = aa.find_child("Pitch", true, false)
		var draws := [0]
		var places := [0]
		pitch.draw.connect(func(): draws[0] += 1)
		pitch.resized.connect(func(): places[0] += 1)
		await _frames(5)
		draws[0] = 0
		var idle: Dictionary = await _frames(60)
		var idle_draws: int = draws[0]
		var sc: ScrollContainer = h.find_child("StatsScroll", true, false)
		draws[0] = 0
		places[0] = 0
		var scroll_dts: Array = []
		var last := Time.get_ticks_usec()
		for i in range(60):
			sc.scroll_vertical = (i * 20) % 1200
			await process_frame
			var now := Time.get_ticks_usec()
			scroll_dts.append((now - last) / 1000.0)
			last = now
		_say("PERF Awards parts (%s): whole section built %.0f ms (oval's cards built %.0f ms of it); oval card layout (_place_spots) %.0f ms (once per new pitch size); idle 60 frames median %.1f ms, %d oval redraws; scrolling 60 frames median %.1f ms, slowest %.1f ms, %d oval redraws, %d oval resizes" % [
				tag, _median(build_all), _median(build_oval), _median(place),
				_median(idle["dts"]), idle_draws, _median(scroll_dts), float(_pct(scroll_dts, 1.0)), draws[0], places[0]])
		h.queue_free()
		await process_frame


func _runs(a: Array) -> String:
	return "/".join(a.map(func(x): return "%.0f" % float(x)))
