extends RefCounted
## Match-day weather against the evidence (ARD-M4-016, measurement only).
## Drafted leagues, one home-and-away season each; every match is played four
## times on the same seed - a perfect day, wet, windy, hot - so each condition's
## change is paired. Per side-match: the box score, accuracy and the change
## against a perfect day, beside the real games' change (row 61:
## tools/balance/afl_weather_rates.json, AFL 2016-25 against a perfect day).
## Env: WX_DRAFTS (default 21,22).

const STATS := ["score", "goals", "behinds", "disposals", "kicks", "handballs", "marks",
		"contested_marks", "tackles", "clangers", "intercepts", "inside50", "clearances",
		"one_percenters", "metres_gained"]
## The real games' change against a perfect day, by condition and stat, in per
## cent ({} for a stat the reference does not hold).
const REFERENCE := "res://tools/balance/afl_weather_rates.json"
const REF_KEY := {"inside50": "inside_50s"}


func real_change() -> Dictionary:
	var out := {}
	var f := FileAccess.open(REFERENCE, FileAccess.READ)
	if f == null:
		return out
	var ref: Dictionary = JSON.parse_string(f.get_as_text())
	for c in ref["change_vs_perfect"]:
		out[c] = {}
		for k in STATS:
			var row = (ref["change_vs_perfect"][c] as Dictionary).get(REF_KEY.get(k, k))
			if row is Dictionary and (row as Dictionary).has("change"):
				out[c][k] = 100.0 * float(row["change"])
	return out


func run() -> void:
	var lb = load("res://tools/balance/league_balance.gd").new()
	var codes: Array = lb.clubs()
	var drafts := [21, 22]
	if OS.get_environment("WX_DRAFTS") != "":
		drafts = []
		for s in OS.get_environment("WX_DRAFTS").split(","):
			drafts.append(int(s))
	var sums := {}
	var n := 0
	# WX_HOME_PLAN: the home side plays this plan in every match, for the plan
	# by condition matrix (compare its home margins with a run without it).
	var plan := OS.get_environment("WX_HOME_PLAN")
	var margin := {}
	for c in Weather.CONDITIONS:
		sums[c] = {}
	for d in drafts:
		var lists: Dictionary = lb.drafted_lists(int(d))["lists"]
		var season := Season.new(codes, lists, int(d) * 7 + 1)
		for ri in range(season.fixture.size()):
			var mi := 0
			for m in season.fixture[ri]:
				mi += 1
				var match_seed := int(d) * 100000 + ri * 100 + mi
				for c in Weather.CONDITIONS:
					var sim := season.match_sim(str(m["home"]), str(m["away"]), match_seed,
							[true, false], false, c)
					if plan != "":
						sim.set_tactics(0, {"gameplan": plan})
					var res := sim.run()
					margin[c] = float(margin.get(c, 0.0)) + float(res["score"][0]) - float(res["score"][1])
					for side in range(2):
						var t: Dictionary = res["team"][side]
						var row: Dictionary = sums[c]
						for k in STATS:
							var v := float(res["score"][side]) if k == "score" else float(t.get(k, 0.0))
							row[k] = float(row.get(k, 0.0)) + v
				n += 2
	print("weather_impl: %d side-matches per condition (drafts %s)" % [n, str(drafts)])
	var base: Dictionary = sums["perfect"]
	var header := "%-16s" % "per side-match"
	for c in Weather.CONDITIONS:
		header += "%12s" % c
	print(header)
	for k in STATS:
		var line := "%-16s" % k
		for c in Weather.CONDITIONS:
			var v := float((sums[c] as Dictionary).get(k, 0.0)) / float(maxi(1, n))
			var b := float(base.get(k, 0.0)) / float(maxi(1, n))
			line += "%12s" % ("%.1f" % v if c == "perfect" else "%.1f %+.0f%%" % [v, (v / maxf(0.001, b) - 1.0) * 100.0])
		print(line)
	var real := real_change()
	for k in STATS:
		var line := "%-16s" % ("real " + k)
		for c in Weather.CONDITIONS:
			var v = (real.get(c, {}) as Dictionary).get(k)
			line += "%12s" % ("" if v == null else "%+.0f%%" % float(v))
		if line.strip_edges() != "real " + k:
			print(line)
	var acc := "%-16s" % "accuracy"
	for c in Weather.CONDITIONS:
		var g := float((sums[c] as Dictionary).get("goals", 0.0))
		var b2 := float((sums[c] as Dictionary).get("behinds", 0.0))
		acc += "%12s" % ("%.1f%%" % (100.0 * g / maxf(1.0, g + b2)))
	print(acc)
	var mg := "%-16s" % ("home margin" + ("" if plan == "" else " (" + plan + ")"))
	for c in Weather.CONDITIONS:
		mg += "%12s" % ("%+.2f" % (float(margin.get(c, 0.0)) / float(maxi(1, n / 2))))
	print(mg)
	print("real accuracy change: wet -1.8, windy -1.0, hot -0.7 points (" + REFERENCE + ")")
