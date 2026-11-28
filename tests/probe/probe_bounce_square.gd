extends SceneTree
## Scratch probe (never commit): over BS_N seeded matches, at every centre bounce, are the men the
## sim sends to the bounce (_centre_attendees) the men the replay stands in the centre square
## (slots R, C, RR, RV, with each interchange taking the slot of the man he replaces)? Where does the
## replay stand the ones it misses, and how many wingers does each side have on the ground?

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	var db = root.get_node("GameDB")
	db.reload()
	var SPY = load("res://tests/probe/ms_spy.gd")
	var SQ = load("res://scripts/sim/Squad.gd")
	var MD = load("res://scripts/ui/match/MatchDirector.gd")
	var square := ["R", "C", "RR", "RV"]
	var clubs: Array = []
	for c in db.clubs.keys():
		if (db.club_list(c) as Array).size() >= 22:
			clubs.append(c)
	var n := int(OS.get_environment("BS_N")) if OS.get_environment("BS_N") != "" else 40
	var bounces := 0
	var men := 0
	var missed := 0
	var missed_at := {}
	var wing_hist := {}
	var missed_by_q := {}
	var bounces_by_q := {}
	var matches := 0
	var shown := 0
	for s in range(1, n + 1):
		var a: String = clubs[s % clubs.size()]
		var b: String = clubs[(s * 7 + 3) % clubs.size()]
		if a == b:
			continue
		var sa = SQ.new(a, db.club_list(a), true, a)
		var sb = SQ.new(b, db.club_list(b), false, b)
		var sim = SPY.new(sa, sb, s)
		var res: Dictionary = sim.run()
		matches += 1
		var evs: Array = res["events"]
		var d = MD.new()
		d.setup(res, evs)
		# The replay's slot for each man on, per side, walked through the log's interchanges.
		var slot_of := [{}, {}]
		for t in d.tokens:
			(slot_of[int(t["side"])] as Dictionary)[int(t["num"])] = str(t["slot"])
		var by_at := {}
		for r in sim.spy:
			var key := "%d_%d" % [int(r["at"]), int(r["side"])]
			if not by_at.has(key):
				by_at[key] = r
		var after_restart := true
		for i in range(evs.size()):
			var ev: Dictionary = evs[i]
			var kind := str(ev.get("kind", ""))
			if kind == "sub":
				var sd := int(ev.get("side", -1))
				var so: Dictionary = slot_of[sd]
				var off := int(ev.get("off_num", -1))
				if so.has(off):
					so[int(ev.get("num", -1))] = so[off]
					so.erase(off)
				continue
			if kind == "moment" or kind == "injury":
				continue
			if after_restart and absf(float(ev.get("fp", 1.0))) < 0.5:
				var q := int(ev.get("q", 0))
				for side in range(2):
					var key2 := "%d_%d" % [i, side]
					if not by_at.has(key2):
						continue
					var r2: Dictionary = by_at[key2]
					bounces += 1
					bounces_by_q[q] = int(bounces_by_q.get(q, 0)) + 1
					var wk := "%d wings of %d mids" % [int(r2["wings"]), int(r2["mids"])]
					wing_hist[wk] = int(wing_hist.get(wk, 0)) + 1
					for num in r2["nums"]:
						men += 1
						var sl := str((slot_of[side] as Dictionary).get(int(num), "none"))
						if not square.has(sl):
							missed += 1
							missed_by_q[q] = int(missed_by_q.get(q, 0)) + 1
							var grp := "wing" if sl.begins_with("W") else ("none" if sl == "none" else "other " + sl)
							missed_at[grp] = int(missed_at.get(grp, 0)) + 1
							if shown < 6:
								shown += 1
								print("BS example seed %d ev %d side %d #%d stands at %s" % [s, i, side, int(num), sl])
			after_restart = kind in ["goal", "quarter"]
	print("BS matches %d side-bounces %d men at the bounce %d" % [matches, bounces, men])
	print("BS men the replay stands outside the square %d (%.1f%%)" % [missed, 100.0 * missed / maxf(1.0, men)])
	print("BS where they stand %s" % str(missed_at))
	print("BS by quarter missed %s of side-bounces %s" % [str(missed_by_q), str(bounces_by_q)])
	print("BS wing counts at the bounce %s" % str(wing_hist))
	quit(0)
