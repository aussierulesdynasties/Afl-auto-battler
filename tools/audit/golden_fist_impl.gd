extends RefCounted
## Golden Fist path audit (T5.Q11c): over many drafted leagues, one full
## season each (home-and-away plus finals, as the award counts), which path
## wins the Danny Frawley Golden Fist and how often an intercept defender
## reaches the top three. Measurement only: the rule is Awards.golden_fist.
## godot --headless --path . --script tools/audit/run_audit.gd -- golden_fist_impl [seeds]
##   seeds: comma-separated draft seeds (default 41..60)


func _season(draft_seed: int, lb) -> Dictionary:
	var lists: Dictionary = lb.drafted_lists(draft_seed)["lists"]
	var codes: Array = lb.clubs()
	var season := Season.new(codes, lists, draft_seed * 7 + 1)
	var players := {}
	for c in codes:
		for p in lists[c]:
			players[str(p["id"])] = p
	var book := {}
	while not season.is_regular_done():
		for res in season.play_round():
			StatBook.add_match(book, res)
	season.start_finals()
	var guard := 0
	while not bool(season.finals.get("done", false)) and guard < 8:
		for res in season.play_finals_week():
			StatBook.add_match(book, res)
		guard += 1
	var rows: Array = Awards.golden_fist(book, players)
	# For comparison only: the same two rates scored as z-scores (each path
	# over its own spread), to see whether a mean-only scale favours a path.
	var el := []
	for id in book:
		if str((players.get(str(id), {}) as Dictionary).get("role", "")) == "DEF" \
				and int(book[id]["games"]) >= Awards.AA_MIN_GAMES:
			var c := {}
			for k in Awards.FIST_WORDS:
				c[k] = StatBook.total(book[id], k)
			var g := int(book[id]["games"])
			el.append({"l": Awards._fist_rate(c, Awards.FIST_LOCKDOWN, g),
					"i": Awards._fist_rate(c, Awards.FIST_INTERCEPT, g)})
			# One raw line per eligible defender, so other scales can be
			# compared offline from the same seasons (grep "^DEF ").
			print("DEF %s" % JSON.stringify({"seed": draft_seed, "id": str(id), "games": g, "counts": c,
					"one_pct": StatBook.total(book[id], "one_percenters"),
					"contested_marks": StatBook.total(book[id], "contested_marks")}))
	var z_path := "-"
	if el.size() > 1:
		var ml := 0.0
		var mi := 0.0
		for e in el:
			ml += float(e["l"])
			mi += float(e["i"])
		ml /= el.size()
		mi /= el.size()
		var vl := 0.0
		var vi := 0.0
		for e in el:
			vl += pow(float(e["l"]) - ml, 2)
			vi += pow(float(e["i"]) - mi, 2)
		var sl := sqrt(vl / el.size())
		var si := sqrt(vi / el.size())
		var best := -INF
		for e in el:
			var zl := (float(e["l"]) - ml) / maxf(1e-9, sl)
			var zi := (float(e["i"]) - mi) / maxf(1e-9, si)
			if maxf(zl, zi) > best:
				best = maxf(zl, zi)
				z_path = "intercept" if zi > zl else "lockdown"
	return {"rows": rows, "players": players, "eligible": el.size(), "z_path": z_path}


func run() -> void:
	var seeds := []
	var a := OS.get_cmdline_user_args()
	if a.size() > 1 and str(a[1]) != "":
		for s in str(a[1]).split(","):
			seeds.append(int(s))
	else:
		for s in range(41, 61):
			seeds.append(s)
	var lb = load("res://tools/balance/league_balance.gd").new()
	var t0 := Time.get_ticks_msec()
	var wins_int := 0
	var top3_int := 0
	var top10_int := 0
	var n := 0
	var z_int := 0
	print("| seed | winner | path | games | line | 2nd path | 3rd path | intercept in top 10 | eligible | z-score winner path |")
	print("|---|---|---|---|---|---|---|---|---|---|")
	for d in seeds:
		var out := _season(d, lb)
		var rows: Array = out["rows"]
		if rows.is_empty():
			print("| %d | none | | | | | | | %d |" % [d, out["eligible"]])
			continue
		n += 1
		var w: Dictionary = rows[0]
		var p: Dictionary = out["players"].get(str(w["id"]), {})
		if str(w["path"]) == "intercept":
			wins_int += 1
		for i in range(mini(3, rows.size())):
			if str(rows[i]["path"]) == "intercept":
				top3_int += 1
		var t10 := 0
		for r in rows:
			if str(r["path"]) == "intercept":
				t10 += 1
		top10_int += t10
		if str(out["z_path"]) == "intercept":
			z_int += 1
		print("| %d | %s %s (%s) | %s | %d | %s | %s | %s | %d | %d | %s |" % [d, str(p.get("first", "")),
				str(p.get("last", "")), str(w["club"]), str(w["path"]), int(w["games"]),
				Awards.golden_fist_line(w), str(rows[1]["path"]) if rows.size() > 1 else "-",
				str(rows[2]["path"]) if rows.size() > 2 else "-", t10, int(out["eligible"]), str(out["z_path"])])
	print("SUMMARY seasons=%d intercept_wins=%d intercept_top3=%d/%d intercept_top10=%d/%d zscore_intercept_wins=%d secs=%d" % [
			n, wins_int, top3_int, n * 3, top10_int, n * 10, z_int, (Time.get_ticks_msec() - t0) / 1000])
