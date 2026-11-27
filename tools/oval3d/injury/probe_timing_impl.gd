extends RefCounted


func run(args: Array) -> void:
	var seeds: Array = []
	for a in args:
		seeds.append(int(a))
	if seeds.is_empty():
		seeds = range(1, 21)
	var keys := {}
	var n_inj := 0
	for seed in seeds:
		var sim := MatchSim.new(Squad.new("RIC", GameDB.club_list("RIC"), true, "RIC"),
				Squad.new("SYD", GameDB.club_list("SYD"), false, "SYD"), seed)
		var res := sim.run()
		res["home"] = "RIC"
		res["away"] = "SYD"
		var evs: Array = res["events"]
		for ev in evs:
			for k in ev:
				if str(k).ends_with("_id") or str(k) == "duel":
					keys[k] = int(keys.get(k, 0)) + 1
		var d := MatchDirector.new()
		d.setup(res, evs.duplicate())
		var at := {}
		var guard := 0
		while not d.idle() and guard < 400000:
			guard += 1
			for e in d.advance(1.0 / 30.0):
				var i := evs.find(e)
				if i >= 0:
					at[i] = d.time
		for i in range(evs.size()):
			var ev: Dictionary = evs[i]
			if str(ev["kind"]) != "injury":
				continue
			n_inj += 1
			var hurt := str(ev["player_id"])
			var last := -1
			for j in range(i - 1, -1, -1):
				var e: Dictionary = evs[j]
				if str(e.get("kind", "")) in ["sub", "injury", "moment"]:
					continue
				var named := false
				for k in e:
					if (str(k).ends_with("_id") or str(k) == "player_id") and str(e[k]) == hurt:
						named = true
				if named:
					last = j
					break
			var sub_k := i - 1 if i > 0 and str(evs[i - 1]["kind"]) == "sub" else -1
			var t_inj := float(at.get(i, -1.0))
			var t_last := float(at.get(last, -1.0))
			print("INJ seed %d k %d q %d min %d kind %s weeks %d last %d (%s) gap_ev %d gap_s %.1f sub %d next %s" % [
				seed, i, int(ev["q"]), int(ev["min"]), str(res["injuries"][0]["kind"]) if false else "", 0, last,
				str(evs[last]["kind"]) if last >= 0 else "-", i - last, t_inj - t_last, sub_k,
				str(evs[i + 1]["kind"]) if i + 1 < evs.size() else "-"])
		# Director seconds per event, this match.
		print("PACE seed %d events %d time %.0f s" % [seed, evs.size(), d.time])
	print("KEYS ", keys)
	print("INJURIES ", n_inj)
