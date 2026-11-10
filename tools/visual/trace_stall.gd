extends SceneTree
## Stalls in play (TODO row T2.42): step the match view (MatchDirector) through
## seeded matches at 60 frames a second, as a phone plays them at 1x, and
## report every stretch where the picture stops: the ball still and almost
## nobody moving. Report only; it changes nothing.
##   godot --headless --path . --script tools/visual/trace_stall.gd [-- --matches 20 --min 1.0 --seed 300]
## Prints one STALL line per still stretch of --min wall seconds or more: its
## length, the phase that held it (with the beat's event kind), the ball's
## mode, and how many players moved. Then a summary by phase.

const DT := 1.0 / 60.0
const BALL_STILL := 0.4     # m/s: the ball is not going anywhere
const RUN := 1.2            # m/s: a player is visibly moving
const FEW := 3              # fewer than this many moving reads as a still picture


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var matches := 20
	var min_s := 1.0
	var seed0 := 300
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--matches": matches = int(a[i + 1])
			"--min": min_s = float(a[i + 1])
			"--seed": seed0 = int(a[i + 1])
	await process_frame
	var db = root.get_node("GameDB")
	var squad_script = load("res://scripts/sim/Squad.gd")
	var clubs: Array = db.active_clubs(2027)
	var by_phase := {}
	var worst := []
	var total_wall := 0.0
	var still_wall := 0.0
	for m in range(matches):
		var h_code := str(clubs[(m * 7) % clubs.size()])
		var a_code := str(clubs[(m * 7 + 3) % clubs.size()])
		var sim = load("res://scripts/sim/MatchSim.gd").new(
				squad_script.new(h_code, db.club_list(h_code), true, h_code),
				squad_script.new(a_code, db.club_list(a_code), false, a_code), seed0 + m)
		var res: Dictionary = sim.run()
		var d = load("res://scripts/ui/match/MatchDirector.gd").new()
		d.setup(res, res["events"])
		var tokens: Array = d.get("tokens")
		var prev := []
		for t in tokens:
			prev.append(t["pos"])
		var ball: Dictionary = d.get("ball")
		var prev_ball: Vector2 = ball["pos"]
		var run_s := 0.0
		var run_info := {}
		var wall := 0.0
		var guard := 0
		while not d.idle() and guard < 2000000:
			guard += 1
			d.advance(DT)
			wall += DT
			ball = d.get("ball")
			var bv := (ball["pos"] as Vector2).distance_to(prev_ball) / DT
			prev_ball = ball["pos"]
			var moving := 0
			for i in range(tokens.size()):
				var tp: Vector2 = tokens[i]["pos"]
				if i < prev.size():
					if tp.distance_to(prev[i]) / DT > RUN:
						moving += 1
					prev[i] = tp
				else:
					prev.append(tp)
			var still: bool = bv < BALL_STILL and moving < FEW and str(d.get("mode")) != "break"
			if still:
				if run_s == 0.0:
					var phases: Array = d.get("_phases")
					var pi: int = d.get("_pi")
					var p: Dictionary = phases[pi] if pi < phases.size() else {}
					var beat: Dictionary = d.get("_beat")
					run_info = {"phase": str(p.get("t", "-")), "kind": str(beat.get("kind", "-")),
							"ball": str(ball["mode"]), "k": int(beat.get("k", -1)), "at": wall}
				run_s += DT
			elif run_s > 0.0:
				_close(run_s, run_info, min_s, m, by_phase, worst)
				if run_s >= min_s:
					still_wall += run_s
				run_s = 0.0
		if run_s > 0.0:
			_close(run_s, run_info, min_s, m, by_phase, worst)
		total_wall += wall
	worst.sort_custom(func(x, y): return float(x[0]) > float(y[0]))
	print("SUMMARY %d matches, %.0f s of play at 1x: %.1f s in still stretches of %.1f s or more" % [
			matches, total_wall, still_wall, min_s])
	for k in by_phase:
		var v: Array = by_phase[k]
		print("  %-28s %4d stretches, longest %.2f s" % [k, int(v[0]), float(v[1])])
	print("LONGEST %s" % str(worst.slice(0, 10)))
	quit()


func _close(run_s: float, info: Dictionary, min_s: float, m: int, by_phase: Dictionary, worst: Array) -> void:
	if run_s < min_s:
		return
	var key := "%s/%s" % [info["phase"], info["kind"]]
	var v: Array = by_phase.get(key, [0, 0.0])
	by_phase[key] = [int(v[0]) + 1, maxf(float(v[1]), run_s)]
	worst.append([snappedf(run_s, 0.01), m, key, info["ball"], int(info["k"])])
	print("STALL %.2fs  match %d at %.0fs  phase %-10s beat %-12s ball %s" % [run_s, m, float(info["at"]),
			info["phase"], info["kind"], info["ball"]])
