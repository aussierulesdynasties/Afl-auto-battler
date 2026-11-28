extends RefCounted
## Scratch audit (never commit): every release over 8 m from its logged spot on seeds 1-12,
## with the restart that began its chain, so the class of drift can be counted, not guessed.

func run() -> void:
	var gs = Engine.get_main_loop().root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
	var suite = load("res://tests/test_match_visual.gd").new()
	gs.replay_seed = 2027
	Engine.get_main_loop().root.get_node("GameDB").reload()
	suite._result(42)
	var lo := int(OS.get_environment("TW_LO")) if OS.get_environment("TW_LO") != "" else 1
	var hi := int(OS.get_environment("TW_HI")) if OS.get_environment("TW_HI") != "" else 12
	var by_class := {}
	var total := 0
	for seed in range(lo, hi + 1):
		var res: Dictionary = suite._result(seed)
		var evs: Array = res["events"]
		var played: Dictionary = suite._play(res, evs, 1.0 / 60.0 * 4.0, false)
		var d: MatchDirector = played["director"]
		var n8 := 0
		var n15 := 0
		for a in d.arrivals:
			var off := absf((a["pos"] as Vector2).x - float(a["want_x"]))
			total += 1
			if off <= 8.0:
				continue
			n8 += 1
			if off > 15.0:
				n15 += 1
			var k := int(a["idx"])
			var pk: int = d._prev_real(k)
			var chain := "?"
			# Walk back to the restart that began this chain.
			var j := k
			var guard := 0
			while j >= 0 and guard < 40:
				guard += 1
				var r: String = d._restart(j)
				if r != "open":
					chain = "%s@%d" % [r, j]
					break
				j = d._prev_real(j)
			var cls := "%s after %s" % [str(a["kind"]), chain.split("@")[0]]
			by_class[cls] = int(by_class.get(cls, 0)) + 1
			var pkind := "" if pk < 0 else str((evs[pk] as Dictionary).get("kind", ""))
			print("TW seed %d idx %d %s off %.1f (at %.1f want %.1f) prev %s chain %s steps %d" % [seed, k,
					str(a["kind"]), off, (a["pos"] as Vector2).x, float(a["want_x"]), pkind, chain, k - j])
		print("TW seed %d arrivals %d over8 %d over15 %d" % [seed, d.arrivals.size(), n8, n15])
	print("TW total arrivals %d" % total)
	print("TW by class %s" % str(by_class))
