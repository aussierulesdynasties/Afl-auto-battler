extends SceneTree
## How the 3D oval's players move (row 198, the gaits): for every player each frame, his drawn
## pace on the turf (Oval3DAnim._pace) as a share of his own top speed (his token's "top", on the
## movement clock: drawn / MatchDirector.TEMPO), the clip he plays and its rate, and which way he
## moves against the way he would face (the ball): ahead, side-on or backwards. Prints the share
## of player-time in each band and direction, so a gait set is sized to what a match asks of it.
##   godot --headless --path . --script tools/visual/measure_oval3d_gaits.gd -- [SECONDS] [SEED]

const DT := 1.0 / 60.0
const BANDS := [0.03, 0.1, 0.2, 0.3, 0.45, 0.6, 0.75, 0.9, 99.0]   # share of his top speed


## A moving loop (Oval3DAnim.is_loop; not called, so this script builds before the autoloads).
static func _loop(name: String) -> bool:
	return name in ["jog", "carry", "walk", "backstep", "backpedal", "shuffle_l", "shuffle_r", "side_run_l", "side_run_r"]


func _initialize() -> void:
	_run.call_deferred()
	create_timer(3000.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var secs := float(args[0]) if args.size() > 0 else 300.0
	var seed := int(args[1]) if args.size() > 1 else 31
	var O = load("res://scripts/ui/match/Oval3D.gd")
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), seed).run()
	res["home"] = "FRE"
	res["away"] = "STK"
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = O.new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	var anim = oval.anim
	var tempo := float(d.TEMPO)
	var count := {}     # "band|dir" -> frames
	var clips := {}     # clip -> frames
	var rates := {}     # "band" -> [rates]
	var total := 0
	var was := {}       # player -> his clip last frame
	var switches := 0   # one moving loop to another (a gait change)
	var stops := 0      # a moving loop to idle or back
	var pairs := {}     # "from>to" -> gait changes
	var t := 0.0
	while t < secs:
		d.advance(DT)
		oval.sync(DT)
		t += DT
		var bp: Vector2 = d.ball["pos"]
		for i in range(anim.players.size()):
			var p: Dictionary = anim.players[i]
			var node: Node3D = p["node"]
			if not node.visible:
				continue
			var v: Vector2 = anim._pace[i]
			var real := v.length() / tempo / float(d.tokens[i]["top"])
			var band := 0
			while real > float(BANDS[band]):
				band += 1
			var here := Vector2(node.position.x, node.position.z)
			var to := bp - here
			var dir := "-"
			if real > 0.03 and to.length() > 2.0:
				var c := v.normalized().dot(to.normalized())
				dir = "ahead" if c > 0.5 else ("back" if c < -0.5 else "side")
			var key := "%d|%s" % [band, dir]
			count[key] = int(count.get(key, 0)) + 1
			var ap: AnimationPlayer = p["anim"]
			var cn := str(ap.current_animation)
			if cn.begins_with("tackle_"):
				cn = "tackle_*"
			clips[cn] = int(clips.get(cn, 0)) + 1
			var before := str(was.get(i, cn))
			if before != cn:
				if _loop(before) and _loop(cn):
					switches += 1
					var pk := before + ">" + cn
					pairs[pk] = int(pairs.get(pk, 0)) + 1
				elif before == "idle" or cn == "idle":
					stops += 1
			was[i] = cn
			if cn in ["jog", "carry"]:
				if not rates.has(band):
					rates[band] = []
				rates[band].append(float(anim._rate[i]))
			total += 1
	print("GAITS %d player-frames over %.0f s, seed %d (bands: share of his top speed)" % [total, secs, seed])
	var lo := 0.0
	for b in range(BANDS.size()):
		var hi := float(BANDS[b])
		var row := []
		var s := 0
		for dir in ["-", "ahead", "side", "back"]:
			var n := int(count.get("%d|%s" % [b, dir], 0))
			s += n
			row.append("%s %5.1f%%" % [dir, 100.0 * n / maxf(1, total)])
		var rs: Array = rates.get(b, [])
		rs.sort()
		var med := "-" if rs.is_empty() else "%.2f" % float(rs[rs.size() / 2])
		print("BAND %4.2f-%4.2f top  %5.1f%%   %s   run-loop rate median %s" % [lo, hi, 100.0 * s / maxf(1, total), "  ".join(row), med])
		lo = hi
	var mins := total * DT / 60.0
	print("CHANGES per player-minute: gait to gait %.1f, to or from standing %.1f" % [switches / maxf(mins, 1e-6), stops / maxf(mins, 1e-6)])
	var pk := pairs.keys()
	pk.sort_custom(func(a, b): return int(pairs[a]) > int(pairs[b]))
	for k in pk.slice(0, 10):
		print("SWITCH %-24s %5.1f per player-minute" % [k, int(pairs[k]) / maxf(mins, 1e-6)])
	var names := clips.keys()
	names.sort_custom(func(a, b): return int(clips[a]) > int(clips[b]))
	for n in names.slice(0, 12):
		print("CLIP %-28s %5.1f%%" % [n, 100.0 * int(clips[n]) / maxf(1, total)])
	quit(0)
