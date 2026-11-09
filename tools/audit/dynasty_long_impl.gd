extends RefCounted
## Two long-career questions from the same seeded careers (T8.88 / P-80 the fun
## floor, T8.50 what long careers do with 90+ ceilings). Measurement only.
##
## A career is tools/balance/dynasty.gd's: the upside League Draft for a seeded
## club, then each season played through the shipped code. MANAGE and COACH pick
## the bot: MANAGE=full COACH=1 is the competent coach (AI-style match-day calls,
## contracts, free agency and trading up every off-season), MANAGE=none COACH=0
## the untouched autopilot. A sacked coach takes the first job offered (as a
## headless run does in GameState._sacking_settled) and the record follows him:
## a flag counts if the coach won it, wherever he was by then.
##
## Args after the impl name: seeds (comma-separated, default 301) seasons (20).
## Lines, for tools/audit/dynasty_long_agg.py:
##   FF      seed season year club ladder clubs finals premier rank22 sacked
##   POTCUT  seed season year dim key n pot90 ovr90 (season start, every list)
##   PL      seed|id|src|year0|age0|ovr0|pot0|club0|role0|age90|ovr90|maxpot|peak|peak_age|last_age|last_ovr|last_pot|seasons|active
##   SUMMARY seed manage coach seasons_played flags sacks seconds
## PL src: the rule behind a real player's POT (headroom, peak, pedigree,
## override), real_draftee (the 2026 draft pool) or generated (later classes,
## expansion lists).
## godot --headless --path . --script tools/audit/run_audit.gd -- dynasty_long_impl 301,302 20

var dyn = load("res://tools/balance/dynasty.gd").new()
var _src := {}


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var seeds := str(args[1]) if args.size() > 1 else "301"
	var seasons := int(args[2]) if args.size() > 2 else 20
	var manage := OS.get_environment("MANAGE") if OS.get_environment("MANAGE") != "" else "full"
	var coach := OS.get_environment("COACH") != "0"
	_read_sources()
	for sd in seeds.split(",", false):
		_career(int(sd), seasons, manage, coach)


func _read_sources() -> void:
	var overridden := {}
	GameDB._each_override_row(GameDB.POTENTIAL_CSV, "potential", GameDB.all_players_sorted(), func(p, _cell):
		overridden[str(p["id"])] = true)
	for p in GameDB.all_players_sorted():
		_src[str(p["id"])] = "override" if overridden.has(str(p["id"])) else source_of(p)
	for p in GameDB.all_draftees_sorted():
		_src[str(p["id"])] = "real_draftee"


## Which rule set this player's POT, as potdist_impl reads it.
static func source_of(p: Dictionary) -> String:
	var pot := float(p.get("potential", 0))
	var peak := Potential.recent_peak(p)
	if peak > 0.0 and absf(roundf(peak) - pot) <= 0.5:
		return "peak"
	var head := float(p.get("overall", 0)) + Potential._headroom(float(p.get("age", 26.0)))
	return "headroom" if pot <= head + 3.5 else "pedigree"


func _career(seed: int, seasons: int, manage: String, coach: bool) -> void:
	var t0 := Time.get_ticks_msec()
	var gs := GameDB.get_tree().root.get_node("GameState")
	gs.autosave_enabled = false
	gs.reset()
	gs.career_seed = seed
	gs.replay_seed = seed
	var d: Draft = dyn.make_upside_draft(seed, 5)
	gs.draft = d
	gs.start_season(d.user_club if d.user_club != "" else str(d.draft_order[0]), [])
	dyn._traded = {}
	var track := {}
	var flags := 0
	var sacks := 0
	var played := 0
	for y in range(seasons):
		_scan(gs, seed, y + 1, track)
		var rank22 := _rank22(gs)
		var club: String = gs.my_club
		while not gs.season.is_season_over() and not gs.is_sacked():
			dyn._play_week(gs, club, coach)
		played += 1
		var rows: Array = gs.season.ladder_sorted()
		var ladder := 0
		for i in rows.size():
			if str(rows[i]["code"]) == club:
				ladder = i + 1
		var premier := str(gs.season.finals.get("premier", ""))
		var sacked: bool = gs.is_sacked()
		print("FF %d %d %d %s %d %d %d %d %d %d" % [seed, y + 1, gs.season_year, club, ladder, rows.size(),
				1 if ladder >= 1 and ladder <= 8 else 0, 1 if premier == club else 0, rank22, 1 if sacked else 0])
		flags += 1 if premier == club else 0
		sacks += 1 if sacked else 0
		if y == seasons - 1:
			break
		if sacked and not ClubMoves.take_first_offer(gs):
			print("CAREER_OVER %d no job offered after season %d" % [seed, y + 1])
			break
		if not gs.offseason_open():
			gs.open_offseason()
		var mgmt: Dictionary = dyn._manage(gs, gs.my_club, manage)
		if not dyn._offseason(gs, gs.my_club, mgmt):
			print("CAREER_OVER %d off-season %d did not complete" % [seed, y + 1])
			break
	_final_lines(gs, seed, track)
	print("SUMMARY %d %s %d %d %d %d %d" % [seed, manage, 1 if coach else 0, played, flags, sacks,
			(Time.get_ticks_msec() - t0) / 1000])


## Where the club's best 22 ranks among the lists at the season's start.
func _rank22(gs) -> int:
	var lists: Dictionary = gs.season.lists
	var codes := lists.keys()
	var score := {}
	for c in codes:
		var ovr := []
		for p in lists[c]:
			ovr.append(int(p["overall"]))
		ovr.sort()
		ovr.reverse()
		var t := 0.0
		for i in range(mini(22, ovr.size())):
			t += float(ovr[i])
		score[c] = t
	codes.sort_custom(func(a, b): return float(score[a]) > float(score[b]))
	return codes.find(gs.my_club) + 1


func _age_band(age: float) -> String:
	if age < 21.0:
		return "18-20"
	if age < 24.0:
		return "21-23"
	if age < 27.0:
		return "24-26"
	if age < 30.0:
		return "27-29"
	return "30+"


## Every listed player at the season's start: counts by age, role, club and
## source, and each player's running record.
func _scan(gs, seed: int, season: int, track: Dictionary) -> void:
	var year: int = gs.season_year
	var cuts := {}
	for code in gs.season.lists:
		for p in gs.season.lists[code]:
			var id := str(p["id"])
			var ovr := int(p["overall"])
			var pot := int(p.get("potential", ovr))
			var age := float(p.get("age", 25.0))
			var role := str(p.get("role", "MID"))
			var src := str(_src.get(id, "generated"))
			if not track.has(id):
				track[id] = {"src": src, "year0": year, "age0": age, "ovr0": ovr, "pot0": pot, "club0": str(code),
						"role0": role, "age90": -1.0, "ovr90": -1, "maxpot": pot, "peak": ovr, "peak_age": age,
						"seasons": 0}
			var r: Dictionary = track[id]
			r["seasons"] = int(r["seasons"]) + 1
			r["last_age"] = age
			r["last_ovr"] = ovr
			r["last_pot"] = pot
			r["last_year"] = year
			r["maxpot"] = maxi(int(r["maxpot"]), pot)
			if pot >= 90 and float(r["age90"]) < 0.0:
				r["age90"] = age
				r["ovr90"] = ovr
			if ovr > int(r["peak"]):
				r["peak"] = ovr
				r["peak_age"] = age
			for pair in [["all", "all"], ["age", _age_band(age)], ["role", role], ["club", str(code)], ["src", src]]:
				var key := "%s %s" % pair
				if not cuts.has(key):
					cuts[key] = [0, 0, 0]
				cuts[key][0] += 1
				cuts[key][1] += 1 if pot >= 90 else 0
				cuts[key][2] += 1 if ovr >= 90 else 0
	var keys := cuts.keys()
	keys.sort()
	for key in keys:
		print("POTCUT %d %d %d %s %d %d %d" % [seed, season, year, key, cuts[key][0], cuts[key][1], cuts[key][2]])


func _final_lines(gs, seed: int, track: Dictionary) -> void:
	var year: int = gs.season_year
	for id in track:
		var r: Dictionary = track[id]
		print("PL %d|%s|%s|%d|%.1f|%d|%d|%s|%s|%.1f|%d|%d|%d|%.1f|%.1f|%d|%d|%d|%d" % [seed, id, r["src"], r["year0"], r["age0"],
				r["ovr0"], r["pot0"], r["club0"], r["role0"], r["age90"], r["ovr90"], r["maxpot"], r["peak"], r["peak_age"],
				r["last_age"], r["last_ovr"], r["last_pot"], r["seasons"], 1 if int(r["last_year"]) == year else 0])
