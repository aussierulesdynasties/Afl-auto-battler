extends RefCounted
## The league over seasons under his training and potential design (director
## 2026-11-17). Measurement only. An autopilot career from the real 2026 lists
## (every draft by the AI). Prints, per season:
##   LG|seed|year|phase|players|mean OVR|sd|80+|85+|90+|max|mean best-23 over clubs
##       phase S = season start (after the intake), E = season end
##   GROW|seed|year|age band|players|mean in-season change (S to E)|share that rose
##   SUMMER|seed|year|age band|players|mean summer change (E to next S)|share that fell
##   BREAK|seed|year|breakouts this summer|clubs|per club|mean jump
##   TRACE|seed|year|name|age|OVR at start|OVR at end|POT|career last|skill points bought past POT (held)
##       eight players followed for the whole career: in each age band at the start, the best and
##       the middle-rated; "next" start comes from the following season's line
## Args after the impl name: seeds (comma list) club seasons
## godot --headless --path . --script tools/audit/run_audit.gd -- league_growth_impl 1,2 MEL 10 [2010]

const BANDS := [[17, 22, "22 and under"], [23, 27, "23-27"], [28, 30, "28-30"], [31, 45, "31+"]]

var seed_n := 1
var dataset := ""
var traced: Array = []


func _run_draft(d: Draft) -> void:
	var guard := 0
	while not d.is_finished() and guard < 5000:
		guard += 1
		var c := d._best_ai_pick(d.current_club())
		if c.is_empty() or not d._draft_pick(d.current_club(), c):
			d._skip_current_pick()


func _band(age: float) -> String:
	for b in BANDS:
		if age >= float(b[0]) and age < float(b[1]) + 1.0:
			return str(b[2])
	return "31+"


## {id: [overall, age]} for every listed player, and the LG line.
func _snap(year: int, phase: String) -> Dictionary:
	var lists: Dictionary = GameState.season.lists
	var out := {}
	var ovs: Array = []
	var best := 0.0
	var clubs := 0
	for code in lists:
		var club_ovs: Array = []
		for p in lists[code]:
			var o := int(p["overall"])
			out[str(p["id"])] = [o, float(p.get("age", 25.0))]
			ovs.append(o)
			club_ovs.append(o)
		club_ovs.sort()
		club_ovs.reverse()
		var t := 0.0
		for i in range(mini(23, club_ovs.size())):
			t += float(club_ovs[i])
		best += t / maxf(1.0, mini(23, club_ovs.size()))
		clubs += 1
	var m := 0.0
	for o in ovs:
		m += float(o)
	m /= maxf(1.0, ovs.size())
	var v := 0.0
	var n80 := 0
	var n85 := 0
	var n90 := 0
	var mx := 0
	for o in ovs:
		v += (float(o) - m) * (float(o) - m)
		n80 += 1 if o >= 80 else 0
		n85 += 1 if o >= 85 else 0
		n90 += 1 if o >= 90 else 0
		mx = maxi(mx, o)
	print("LG|%d|%d|%s|%d|%.2f|%.2f|%d|%d|%d|%d|%.2f" % [seed_n, year, phase, ovs.size(), m,
			sqrt(v / maxf(1.0, ovs.size())), n80, n85, n90, mx, best / maxf(1.0, clubs)])
	return out


func _change(tag: String, year: int, a: Dictionary, b: Dictionary, rose: bool) -> void:
	var by := {}
	for id in a:
		if not b.has(id):
			continue
		var band := _band(float(a[id][1]))
		if not by.has(band):
			by[band] = [0, 0.0, 0]
		var d := int(b[id][0]) - int(a[id][0])
		by[band][0] += 1
		by[band][1] += float(d)
		by[band][2] += 1 if ((d > 0) if rose else (d < 0)) else 0
	for bd in BANDS:
		var k := str(bd[2])
		if by.has(k):
			var v: Array = by[k]
			print("%s|%d|%d|%s|%d|%.2f|%.3f" % [tag, seed_n, year, k, v[0], v[1] / v[0], float(v[2]) / v[0]])


func _breakouts(year: int) -> void:
	var n := 0
	var jump := 0.0
	var clubs := 0
	for code in GameState.season.lists:
		clubs += 1
		for p in GameState.season.lists[code]:
			for e in p.get("breakouts", []):
				if int(e[0]) == year:
					n += 1
					jump += float(e[1])
	print("BREAK|%d|%d|%d|%d|%.2f|%.2f" % [seed_n, year, n, clubs, float(n) / maxf(1.0, clubs), jump / maxf(1.0, n)])


func _find(id: String) -> Dictionary:
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			if str(p["id"]) == id:
				return p
	return {}


func _pick_traced() -> void:
	traced = []
	for b in BANDS:
		var band: Array = []
		for code in GameState.season.lists:
			for p in GameState.season.lists[code]:
				if _band(float(p.get("age", 25.0))) == str(b[2]):
					band.append(p)
		band.sort_custom(func(x, y): return int(x["overall"]) > int(y["overall"]))
		if band.size() > 1:
			traced.append(str(band[0]["id"]))
			traced.append(str(band[band.size() / 2]["id"]))


func _trace(year: int, start: Dictionary) -> void:
	for id in traced:
		var p := _find(id)
		var over := 0.0
		for k in p.get("over_gains", {}):
			over += float(p["over_gains"][k])
		if p.is_empty() or not start.has(id):
			continue
		print("TRACE|%d|%d|%s|%.0f|%d|%d|%d|%.1f|%d" % [seed_n, year, GameDB.player_display_name(p),
				float(start[id][1]), int(start[id][0]), int(p["overall"]), int(p.get("potential", 0)),
				float(p.get("career_last", 0.0)), int(over)])


## TOP|seed|year|name OVR/POT ...: the league's ten best at the season's end.
func _top(year: int) -> void:
	var all: Array = []
	for code in GameState.season.lists:
		all += GameState.season.lists[code]
	all.sort_custom(func(a, b): return int(a["overall"]) > int(b["overall"]))
	var bits := PackedStringArray()
	for i in range(mini(10, all.size())):
		bits.append("%s %s %d/%d" % [all[i].get("first", ""), all[i].get("last", ""), int(all[i]["overall"]), int(all[i].get("potential", 0))])
	print("TOP|%d|%d|%s" % [seed_n, year, ", ".join(bits)])


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var seeds := str(args[1]).split(",") if args.size() > 1 else PackedStringArray(["1"])
	var club := str(args[2]) if args.size() > 2 else "MEL"
	var seasons := int(args[3]) if args.size() > 3 else 10
	# A Legacy start ("1990", "2000", "2010", "2020"); today's lists without one.
	dataset = str(args[4]) if args.size() > 4 else ""
	for sd in seeds:
		seed_n = int(sd)
		_career(club, seasons)


func _career(club: String, seasons: int) -> void:
	if dataset == "":
		GameState.reset()
	else:
		GameState.reset(dataset)
	GameState.autosave_enabled = false
	GameState.career_seed = seed_n
	GameState.replay_seed = seed_n
	GameState.begin_real_lists()
	GameState.choose_real_club(club)
	_run_draft(GameState.draft)
	GameState.finish_intake_draft()
	_pick_traced()
	for s in range(seasons):
		var year := GameState.season_year
		var start := _snap(year, "S")
		while not GameState.season.is_season_over():
			GameState.advance()
		var end := _snap(year, "E")
		_top(year)
		_trace(year, start)
		_change("GROW", year, start, end, true)
		if s == seasons - 1:
			break
		# The audit follows the league, not the coach: a sacking with no job
		# left would hold the career on one year (as legacy_lists_probe does).
		if ClubMoves.letter_open(GameState):
			ClubMoves.decline_letter(GameState)
		GameState.board.erase("sacked")
		GameState.open_offseason()
		if GameState.begin_intake_draft():
			_run_draft(GameState.draft)
			GameState.finish_intake_draft()
		elif not GameState.start_next_season():
			push_error("league_growth: the season did not roll on from %d" % year)
			break
		_breakouts(GameState.season_year)
		var next := {}
		for code in GameState.season.lists:
			for p in GameState.season.lists[code]:
				next[str(p["id"])] = [int(p["overall"]), float(p.get("age", 25.0))]
		_change("SUMMER", year, end, next, false)
