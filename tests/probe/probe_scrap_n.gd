extends SceneTree
## Scratch (never commit): count, over several matches, the men the "runs straight across a
## loose ball upright" check would flag, and the kind of event each was about to make.
## Seeds from AFL_SEEDS (comma list).


func _initialize() -> void:
	_run.call_deferred()


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
	var TEMPO: float = MD.TEMPO
	var seeds := OS.get_environment("AFL_SEEDS").split(",", false)
	var total := 0
	var by_kind := {}
	for s in seeds:
		var res: Dictionary = suite._result(int(s))
		var d = MD.new()
		d.setup(res, res["events"])
		d.want_contacts = true
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
			for t in d.tokens:
				var id := int(t["id"])
				var on_it: bool = scrap and (t["pos"] as Vector2).distance_to(d.ball["pos"]) < 0.6 \
						and (t["vel"] as Vector2).length() >= 0.6 and d._on_feet(id) \
						and (t["vel"] as Vector2).dot((d.ball["pos"] as Vector2) - (t["pos"] as Vector2)) > 0.0 \
						and d.time - float(last_scoop.get(id, -99.0)) >= 1.5 * TEMPO
				if on_it and not over.get(id, false):
					found += 1
					var k := int(d._beat.get("k", -1))
					var nk: int = d._next_real(k) if k >= 0 else -1
					var nkind := str((d.events[nk] as Dictionary).get("kind", "")) if nk >= 0 else "-"
					var okind := str((d.events[k] as Dictionary).get("kind", "")) if k >= 0 else "-"
					# In a fumble the beat is the spilled event and the gatherer's is the next; in a
					# collect or scoop wait the beat is the gatherer's own event.
					var gkind := nkind if st == "fumble" else okind
					by_kind[gkind] = int(by_kind.get(gkind, 0)) + 1
					print("OVER seed %s %.0f s id %d phase %s beat %s next %s" % [s, d.time / TEMPO, id, st, okind, nkind])
				over[id] = on_it
		print("PSN seed %s: %d" % [s, found])
		total += found
	print("PSN total %d over %d matches, by next kind %s" % [total, seeds.size(), str(by_kind)])
	quit(0)
