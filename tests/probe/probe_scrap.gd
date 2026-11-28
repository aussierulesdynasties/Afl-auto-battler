extends SceneTree
## Scratch (never commit): replay _result(42) as _test_contacts does and dump the man the
## "runs straight across a loose ball upright" check flags, with the 3 s before it.


func _initialize() -> void:
	_run.call_deferred()


func _fmt(v: Vector2) -> String:
	return "(%.2f,%.2f)" % [v.x, v.y]


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
	gs.replay_seed = 2027
	root.get_node("GameDB").reload()
	var MD = load("res://scripts/ui/match/MatchDirector.gd")
	var suite = load("res://tests/probe/mv_spy.gd").new()
	var res: Dictionary = suite._result(42)
	var d = MD.new()
	d.setup(res, res["events"])
	d.want_contacts = true
	var TEMPO: float = MD.TEMPO
	var hist := []   # ring of the last 60 frames: [time, ball, phase, per-token pos/vel]
	var over := {}
	var last_scoop := {}
	var guard := 0
	var found := 0
	while not d.idle() and guard < 120000:
		guard += 1
		d.advance(0.05)
		for c in d.contacts:
			if c["kind"] == &"ground_ball":
				last_scoop[int(c["who"])] = d.time
		d.contacts.clear()
		var sp: Dictionary = d._phases[d._pi] if d._pi < d._phases.size() else {}
		var st := str(sp.get("t", ""))
		var scrap: bool = str(d.ball["mode"]) in ["loose", "dead"] and int(d.ball.get("holder", -1)) < 0 \
				and (st == "fumble" or (st == "collect" and sp.get("pace", false)) or (st == "wait" and sp.has("scoop")))
		var snap := {"time": d.time, "ball": d.ball["pos"], "bvel": d.ball.get("vel", Vector2.ZERO),
				"mode": str(d.ball["mode"]), "holder": int(d.ball.get("holder", -1)), "ph": sp.duplicate(),
				"pi": d._pi, "k": int(d._beat.get("k", -1)), "pos": [], "vel": [], "feet": []}
		for t in d.tokens:
			snap["pos"].append(t["pos"])
			snap["vel"].append(t["vel"])
			snap["feet"].append(d._on_feet(int(t["id"])))
		hist.append(snap)
		if hist.size() > 80:
			hist.pop_front()
		for t in d.tokens:
			var id := int(t["id"])
			var on_it: bool = scrap and (t["pos"] as Vector2).distance_to(d.ball["pos"]) < 0.6 \
					and (t["vel"] as Vector2).length() >= 0.6 and d._on_feet(id) \
					and (t["vel"] as Vector2).dot((d.ball["pos"] as Vector2) - (t["pos"] as Vector2)) > 0.0 \
					and d.time - float(last_scoop.get(id, -99.0)) >= 1.5 * TEMPO
			if on_it and not over.get(id, false):
				found += 1
				print("OVER %.0f s (time %.2f) id %d side %d num %s zone %s | phase %s | k %d | ball %s mode %s vel %s" % [
						d.time / TEMPO, d.time, id, int(t["side"]), str(t.get("num", "?")), str(t.get("zone", "?")),
						str(sp), int(d._beat.get("k", -1)), _fmt(d.ball["pos"]), str(d.ball["mode"]),
						_fmt(d.ball.get("vel", Vector2.ZERO))])
				print("  token keys: %s" % str(t.keys()))
				print("  scoop_at %.2f scoop_k %s busy %s goal %s cap %s" % [float(t.get("scoop_at", -99.0)),
						str(t.get("scoop_k", "-")), str(d._busy.get(id, false)), str(t.get("goal", "-")), str(t.get("cap", "-"))])
				var k := int(d._beat.get("k", -1))
				for j in range(maxi(k - 3, 0), mini(k + 4, d.events.size())):
					var e: Dictionary = d.events[j]
					print("  ev %d%s %s side %s actor %s fp %s loose_to %s" % [j, " <" if j == k else "", str(e.get("kind", "")),
							str(e.get("side", "")), str(e.get("actor", e.get("player", ""))), str(e.get("fp", "")), str(e.get("loose_to", "-"))])
				print("  phases: %s" % str(d._phases))
				for h in hist:
					print("  t %.2f pi %d k %d %s ball %s %s v %s | him %s v %s (%.2f m/s) feet %s dist %.2f" % [
							float(h["time"]), int(h["pi"]), int(h["k"]), str(h["ph"].get("t", "")), _fmt(h["ball"]), str(h["mode"]),
							_fmt(h["bvel"]), _fmt(h["pos"][id]), _fmt(h["vel"][id]), (h["vel"][id] as Vector2).length(),
							str(h["feet"][id]), (h["pos"][id] as Vector2).distance_to(h["ball"])])
			over[id] = on_it
	print("PSC done, %d overs" % found)
	quit(0)
