extends RefCounted
## What each attribute makes the engine record (director 2026-11-15: rate each
## player type on the stats the game keeps - hit-outs to advantage, metres
## gained, intercepts, pressure acts, distance run and the rest, StatBook.KEYS).
## Plays one home-and-away season on the real 2026 lists (seed TS_SEED,
## default 1) and prints one line per player who played:
##   ROW id|club|name|role|height|games|attr k=v;...|stat k=total;...
## tools/audit/type_stats_report.py fits each stat a game on the attributes.
## Measurement only; changes nothing.


func run() -> void:
	var lb = load("res://tools/balance/league_balance.gd").new()
	var codes: Array = lb.clubs()
	var lists: Dictionary = lb.real_lists()
	var sd := int(OS.get_environment("TS_SEED")) if OS.get_environment("TS_SEED") != "" else 1
	var season := Season.new(codes, lists, sd * 7 + 1)
	var who := {}
	for c in codes:
		for p in lists[c]:
			who[str(p["id"])] = p
	var tot := {}
	var games := {}
	for ri in range(season.fixture.size()):
		var mi := 0
		for m in season.fixture[ri]:
			mi += 1
			var sim: MatchSim = season.match_sim(str(m["home"]), str(m["away"]), sd * 100000 + ri * 100 + mi)
			var res := sim.run()
			var stats: Dictionary = res["players"]
			for side in range(2):
				for r in (res["roster"][side] as Array):
					var id := str(r["id"])
					var st: Dictionary = stats.get(id, {})
					if st.is_empty():
						continue
					games[id] = int(games.get(id, 0)) + 1
					var t: Dictionary = tot.get(id, {})
					for k in StatBook.KEYS:
						t[k] = float(t.get(k, 0.0)) + float(st.get(k, 0.0))
					tot[id] = t
	for id in tot:
		var p: Dictionary = who.get(id, {})
		if p.is_empty():
			continue
		var a: PackedStringArray = []
		for k in (p["attr"] as Dictionary):
			a.append("%s=%d" % [k, int(p["attr"][k])])
		var s: PackedStringArray = []
		for k in StatBook.KEYS:
			s.append("%s=%d" % [k, int(tot[id][k])])
		print("ROW %s|%s|%s|%s|%d|%d|%s|%s" % [id, str(p.get("club", "")), str(p.get("name", "")),
				str(p.get("role", "")), int(p.get("height_cm", 0)), int(games[id]), ";".join(a), ";".join(s)])
