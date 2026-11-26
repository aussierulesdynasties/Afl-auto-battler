extends SceneTree
## How well stoppage_now's throw-in `in` predicts the ball going in (row 202): for each throw-in
## of a seeded match, the director seconds from when the estimate first said "sure" with N
## seconds to go, to the ball actually leaving the line (flight from the pack).
##   godot --headless --path . --script tools/oval3d/probe_throwin_timing.gd [-- SEED]

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var seed := int(args[0]) if args.size() > 0 else 42
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("RIC", gdb.club_list("RIC"), true, "RIC"),
			Squad_.new("SYD", gdb.club_list("SYD"), false, "SYD"), seed).run()
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, (res.get("events", []) as Array).duplicate())
	var dt := 1.0 / 30.0
	var cur := false
	var sure_at := -1.0
	var sure_in := 0.0
	var ended_at := -1.0
	var errs := []
	var gaps := []
	while d.time < 9000.0 and not d.idle():
		d.advance(dt)
		var st: Dictionary = d.stoppage_now()
		var on := str(st.get("kind", "")) == "throwin"
		if on and not cur:
			sure_at = -1.0
		if on and bool(st.get("sure", false)) and sure_at < 0.0:
			sure_at = d.time
			sure_in = float(st["in"])
		if cur and not on:
			ended_at = d.time
		if ended_at >= 0.0 and str(d.ball.get("mode", "")) == "flight":
			if sure_at >= 0.0:
				errs.append([snappedf((d.time - sure_at) - sure_in, 0.01), snappedf(sure_in, 0.01)])
			gaps.append(d.time - ended_at)
			ended_at = -1.0
		cur = on
	print("THROWINS %d  predicted-vs-actual error (s): %s" % [errs.size(), errs])
	print("pack end to flight (s): %s" % [gaps])
	quit()
