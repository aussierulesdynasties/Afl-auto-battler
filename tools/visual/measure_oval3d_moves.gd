extends SceneTree
## Kicks, handballs and marks on the 3D oval (row 198): does each one play its clip, start it
## ahead of the touch, and meet the ball?
##   godot --headless --path . --script tools/visual/measure_oval3d_moves.gd -- [SECONDS] [SEED]
## Fremantle v St Kilda (seed 31 unless given) at 60 frames a second on the MetaHuman body. For
## every touch the director makes (MatchDirector.contacts: kick, handball, mark): which clip was
## playing, whether it started before the touch (planned) or at it (late: no warning), how far the
## clip's contact frame was from the touch (s), and in the frame of the touch how far the drawn ball
## was from the boot or the palms (m). Summary lines MOVES (one per kind) for a PR or a test.

const DT := 1.0 / 60.0


func _initialize() -> void:
	_run.call_deferred()
	create_timer(3000.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var secs := float(args[0]) if args.size() > 0 else 300.0
	var seed := int(args[1]) if args.size() > 1 else 31
	var O = load("res://scripts/ui/match/Oval3D.gd")
	O.player_glb = "res://assets/oval3d/player_mh.glb"
	O.loops_glb = "res://assets/oval3d/player_mh.glb"
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
	var stats := {}     # kind -> {n, clip, planned, off: [] (s the picture's contact lags the touch), gap: []}
	var t := 0.0
	var touched := {}   # player -> [kind, time of the director's touch, started ahead]
	var crossed := {}   # player -> [kind, time his clip reached its contact, gap then, clip, held]
	var last_t := {}    # player -> his move clip's time last frame
	var held := []      # s a move waited short of its contact for a late touch
	var drop_at := {}   # player -> [time his kick's ball left his hands, its height then]
	var drops := []     # [real s from hands to boot, m fallen, the g that implies]
	var moving_t := {}  # player -> last time he was drawn moving
	var in_take := {}   # player -> in a two-man take now
	var run_downs := []  # [t, tackler, carrier, tackler's drawn pace, carrier's] of each chase-down take
	var idle := []      # s each tackler stood still before his take began
	while t < secs:
		d.advance(DT)
		for c in d.contacts:
			var kind := str(c["kind"])
			var who := int(c["who"])
			if kind in ["kick", "handball", "mark"] and who >= 0:
				if not stats.has(kind):
					stats[kind] = {"n": 0, "clip": 0, "planned": 0, "off": [], "gap": []}
				stats[kind]["n"] = int(stats[kind]["n"]) + 1
				var o0: Dictionary = anim._once[who]
				touched[who] = [kind, t, not o0.is_empty() and str(o0.get("how", "")) == kind]
		oval.sync(DT)
		t += DT
		for who in range(anim.players.size()):
			var o: Dictionary = anim._once[who]
			# The tackler's run-in: how long he stood (the idle clip) before the take began.
			if (anim.players[who]["anim"] as AnimationPlayer).current_animation != "idle":
				moving_t[who] = t
			var pr_w: Dictionary = anim._in[who]
			if not pr_w.is_empty() and int(pr_w["who"]) == who and not in_take.has(who):
				idle.append(t - float(moving_t.get(who, t)))
				if OS.get_environment("MOVES_EACH") != "" and anim.director._pi < anim.director._phases.size():
					var ph: Dictionary = anim.director._phases[anim.director._pi]
					print("  take geometry: phase %s gap to carrier, behind him = %s" % [str(ph.get("t", "")), str(ph.get("_geo", []))])
				if anim.director.chasing_down():
					run_downs.append([t, who, int(pr_w["victim"]), (anim._pace[who] as Vector2).length(), (anim._pace[int(pr_w["victim"])] as Vector2).length()])
				if OS.get_environment("MOVES_EACH") != "":
					print("  take t=%.2f who=%d victim=%d stood %.2f s" % [t, who, int(pr_w["victim"]), t - float(moving_t.get(who, t))])
			if pr_w.is_empty():
				in_take.erase(who)
			else:
				in_take[who] = true
			if o.is_empty() or str(o.get("how", "")) == "":
				last_t.erase(who)
				drop_at.erase(who)
				continue
			if o.has("drop") and not drop_at.has(who):
				drop_at[who] = [t - DT, (o["drop"] as Vector3).y]
			var now := float(o["t"])
			var before := float(last_t.get(who, -1.0))
			last_t[who] = now
			if before < float(o["touch"]) and now >= float(o["touch"]):
				var m: Dictionary = anim._moments[str(o["anim"])]
				var limb: Vector3 = (anim.players[who]["node"] as Node3D).transform * anim._limb(anim.players[who], str(m["limb"]))
				crossed[who] = [str(o["how"]), t, oval.ball.position.distance_to(limb), str(o["anim"]), float(o.get("held", 0.0))]
				if o.has("drop") and drop_at.has(who):
					# The drop from his hands to the boot, in real seconds: the fall's own g.
					# The fall as timed when he let go (real s); a touch that came early re-times
					# what is left of it, never slower than gravity (Oval3DAnim._arrive).
					var fall_t := float(o["drop_fall"])
					var fall_h: float = float(drop_at[who][1]) - float(oval.ball.position.y)
					drops.append([fall_t, fall_h, 2.0 * fall_h / maxf(fall_t * fall_t, 1e-4)])
					if OS.get_environment("MOVES_EACH") != "":
						print("  drop t=%.2f who=%d %s fall %.3f s planned %.3f s over %.2f m rate %.2f held %.2f" % [t, who,
								str(o["anim"]), fall_t, float(o["drop_span"]), fall_h, float(o.get("rate", 1.0)), float(o.get("held", 0.0))])
				drop_at.erase(who)
		for who in touched.keys():
			if not crossed.has(who) or str(crossed[who][0]) != str(touched[who][0]):
				if t - float(touched[who][1]) > 2.0:
					if OS.get_environment("MOVES_EACH") != "":
						print("  MISSED %s t=%.2f who=%d once=%s in=%s" % [touched[who][0], touched[who][1], who, str(anim._once[who].get("anim", "")), str(not (anim._in[who] as Dictionary).is_empty())])
					touched.erase(who)
				continue
			var kind: String = touched[who][0]
			var st: Dictionary = stats[kind]
			st["clip"] = int(st["clip"]) + 1
			if touched[who][2]:
				st["planned"] = int(st["planned"]) + 1
			var lag := float(crossed[who][1]) - float(touched[who][1])
			(st["off"] as Array).append(lag)
			(st["gap"] as Array).append(float(crossed[who][2]))
			held.append(float(crossed[who][4]))
			if OS.get_environment("MOVES_EACH") != "":
				print("  %s t=%.2f who=%d %s lag=%.3f gap=%.3f ahead=%s held=%.2f" % [kind, t, who, crossed[who][3], lag, crossed[who][2], touched[who][2], crossed[who][4]])
			touched.erase(who)
			crossed.erase(who)
	for kind in stats:
		var st: Dictionary = stats[kind]
		var gaps: Array = st["gap"]
		gaps.sort()
		var offs: Array = st["off"]
		offs.sort()
		var med := func(a: Array) -> float: return float(a[a.size() / 2]) if a.size() > 0 else -1.0
		var p90 := func(a: Array) -> float: return float(a[int(a.size() * 0.9)]) if a.size() > 0 else -1.0
		print("MOVES %s: %d touches, %d reached their contact with the clip (%d started ahead of the touch), picture lags the touch (negative: early) median %.3f s p90 %.3f s, ball to %s median %.3f m p90 %.3f m" % [
				kind, st["n"], st["clip"], st["planned"], med.call(offs), p90.call(offs),
				"boot" if kind == "kick" else "palms", med.call(gaps), p90.call(gaps)])
	if drops.size() > 0:
		var ts: Array = drops.map(func(d): return float(d[0]))
		var hs: Array = drops.map(func(d): return float(d[1]))
		var gs: Array = drops.map(func(d): return float(d[2]))
		ts.sort(); hs.sort(); gs.sort()
		print("MOVES drop hand to boot: %d kicks, fall median %.3f s (p10 %.3f p90 %.3f), height median %.2f m, implied g median %.1f m/s2 (p10 %.1f p90 %.1f; real 9.8)" % [
				drops.size(), ts[ts.size() / 2], ts[int(ts.size() * 0.1)], ts[int(ts.size() * 0.9)], hs[hs.size() / 2],
				gs[gs.size() / 2], gs[int(gs.size() * 0.1)], gs[int(gs.size() * 0.9)]])
	print("MOVES chase-down tackles from behind: %d of %d takes %s" % [run_downs.size(), idle.size(),
			str(run_downs.map(func(r): return "t=%.1f %d on %d at %.1f vs %.1f m/s" % r))])
	idle.sort()
	if idle.size() > 0:
		print("MOVES tackler stood still before the take: %d takes, median %.2f s, p90 %.2f s, max %.2f s, %d over 0.3 s" % [
				idle.size(), idle[idle.size() / 2], idle[int(idle.size() * 0.9)], idle[-1], idle.filter(func(v): return v > 0.3).size()])
	held.sort()
	if held.size() > 0:
		print("MOVES held short of contact for a late touch: median %.3f s, p90 %.3f s, max %.3f s, %d of %d over 0.1 s" % [
				held[held.size() / 2], held[int(held.size() * 0.9)], held[-1], held.filter(func(v): return v > 0.1).size(), held.size()])
	quit(0)
