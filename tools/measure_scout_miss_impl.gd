extends RefCounted
## Body of tools/measure_scout_miss.gd, loaded at run time so the autoloads exist.


func run(db: Node) -> void:
	var levels: Array = ClubBudget.SCOUT_UNCERTAINTY
	for li in range(levels.size()):
		var mult := float(levels[li])
		var n := 0
		var ov_miss := 0
		var pot_miss := 0
		var worst := 0
		for year in range(2027, 2037):
			for p in Prospects.generate_class(year, 1000 + year):
				var v := DraftScouting.projection(p, "COL", 77 + year, mult)
				var ov := int(p["overall"])
				var pot := maxi(ov, int(p.get("potential", ov)))
				n += 1
				var om := _out(ov, v["overall"])
				var pm := _out(pot, v["potential"])
				ov_miss += int(om > 0)
				pot_miss += int(pm > 0)
				worst = maxi(worst, maxi(om, pm))
		var ln := 0
		var l_miss := 0
		var l_worst := 0
		for s in [11, 22, 33]:
			var d := Draft.new(db.all_players_sorted(), db.active_clubs(2026).duplicate(), s)
			var me := str(d.draft_order[5])
			d.scouting_mults[me] = mult
			d.start_for_user(me)
			for p in d.pool:
				if d.picked.has(str(p["id"])):
					continue
				var v := d.user_view(p)
				ln += 1
				var lm := maxi(_out(int(p["overall"]), v["overall"]),
						_out(maxi(int(p["overall"]), int(p.get("potential", p["overall"]))), v["potential"]))
				l_miss += int(lm > 0)
				l_worst = maxi(l_worst, lm)
		print("level %d (x%.2f): national n=%d OVR miss %.1f%% POT miss %.1f%% worst %d | league n=%d miss %.1f%% worst %d" % [
				li, mult, n, 100.0 * ov_miss / n, 100.0 * pot_miss / n, worst, ln, 100.0 * l_miss / ln, l_worst])


func _out(truth: int, rng: Array) -> int:
	if truth < int(rng[0]):
		return int(rng[0]) - truth
	if truth > int(rng[1]):
		return truth - int(rng[1])
	return 0
