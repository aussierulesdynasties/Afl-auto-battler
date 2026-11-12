extends RefCounted
## Team selection: auto-pick is unchanged, a named side is what takes the
## field (out of position too), gaps and over-full slots are handled, a player
## you leave out really does not play, and the selection is saved.
## Run through tests/run_selection_tests.gd.

var failures: Array[String] = []
var checks := 0

## Every season and draft here is seeded (C15): a clock seed makes a different
## league each run.
const SUITE_SEED := 2027


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	# These fixtures (Geelong's second ruck off the 18, a club's 21st man) are about the rules, not
	# the director's hand-set ratings (data/ovr_overrides.csv): they play on the data without them.
	GameDB.skip_ovr_overrides = true
	GameDB.reload()
	_t("_test_auto_matches_select_22")
	_t("_test_ruck_selection_integrity")
	_t("_test_named_side")
	_t("_test_formation_layout")
	_t("_test_complete_synergy")
	_t("_test_blooding_net_change")
	_t("_test_blooding_note_fits")
	_t("_test_complete_synergy_reentry")
	_t("_test_gaps_and_overflow")
	_t("_test_left_out_player_sits_out")
	_t("_test_selection_saved")
	_t("_test_with_us_and_milestones")
	_t("_test_fifth_interchange")
	_t("_test_dual_ruck")
	_t("_test_merit_second_position")
	_t("_test_drag_preview_one_line")
	_t("_test_key_posts")
	_t("_test_key_posts_match_sim")
	_t("_test_youth_no_cycle")
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	GameDB.skip_ovr_overrides = false
	GameDB.reload()
	print(Ran.line("Selection", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _ids(arr: Array) -> Array:
	var out := []
	for p in arr:
		out.append(str(p["id"]))
	return out


func _new_season() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))


func _test_auto_matches_select_22() -> void:
	var list: Array = GameDB.club_list("COL")
	var a := Ratings.select_22(list)
	var b := Ratings.select_side(list, {})
	_check(_ids(a["ground"]) == _ids(b["ground"]) and _ids(a["bench"]) == _ids(b["bench"]),
			"With no selection the side is exactly the automatic best 22")


## Automatic selection treats ruck as a specialist position. A higher-OVR
## recognised ruck must not start ahead of a clearly better tap player.
func _test_ruck_selection_integrity() -> void:
	var list: Array = []
	var ruck_ids := []
	for src in GameDB.players:
		var p: Dictionary = src.duplicate(true)
		list.append(p)
		if Ratings.plays_role(p, "RUCK"):
			ruck_ids.append(str(p["id"]))
			p["attr"]["ruck"] = 40
	_check(ruck_ids.size() >= 2, "The league pool contains two recognised rucks for the selection test")
	if ruck_ids.size() < 2:
		return
	var high_ovr: String = str(ruck_ids[0])
	var tapper: String = str(ruck_ids[1])
	for p in list:
		if str(p["id"]) == high_ovr:
			p["overall"] = 99
			p["attr"]["ruck"] = 55
		elif str(p["id"]) == tapper:
			p["overall"] = 50
			p["attr"]["ruck"] = 90
	var side := Ratings.select_22(list)
	var starter := ""
	for p in side["ground"]:
		if str(p["role"]) == "RUCK":
			starter = str(p["id"])
			break
	_check(starter == tapper,
			"Auto-pick starts the best tap ruck, not the highest-OVR recognised ruck")


## The team builder places a selection on the field: the centre square is
## MID (centre and two inside mids), the wings WING, and every line fills its
## spots, 18 different players (director's PC playtest, 2026-10-07).
func _test_formation_layout() -> void:
	_new_season()
	var side := GameState.current_side()
	var spots: Dictionary = load("res://scripts/ui/TeamBuilder.gd").SPOTS
	_check((spots["MID"] as Array) == ["C", "IL", "IR"] and (spots["WING"] as Array) == ["WL", "WR"]
			and (spots["RUCK"] as Array) == ["RUCK"], "The centre square, wings and ruck have their spots")
	var n := 0
	var unique := {}
	for line in ["RUCK", "MID", "WING", "DEF", "FWD"]:
		_check((side[line] as Array).size() == (spots[line] as Array).size(),
				"%s fills its %d spots" % [line, (spots[line] as Array).size()])
		for id in side[line]:
			n += 1
			unique[str(id)] = true
	_check(n == 18 and unique.size() == 18, "Eighteen different players on the field")
	# Auto-pick strategies and the saved Best 23 (GameState).
	for strat in ["best", "rest", "youth"]:
		var r: Dictionary = GameState.auto_pick(strat)
		var count := 0
		for k2 in r["side"]:
			count += (r["side"][k2] as Array).size()
		_check(count == 23 and str(r["note"]) != "", "Auto-pick %s fields 23 and says what it did" % strat)
	_check((GameState.auto_pick("mine")["side"] as Dictionary).is_empty(), "No Best 23 until you save one")
	GameState.set_best23(side)
	var hurt: Dictionary = GameState.list_player(str(side["DEF"][0]))
	hurt["injury_weeks"] = 2
	var mine: Dictionary = GameState.auto_pick("mine")
	_check(not (mine["side"]["DEF"] as Array).has(str(hurt["id"])) and str(mine["note"]).contains("unavailable"),
			"Your Best 23 replaces an injured player, and says so")
	hurt["injury_weeks"] = 0
	_check(GameState.save_career(), "(save with a Best 23)")
	var keep: Dictionary = GameState.best23.duplicate(true)
	GameState.reset()
	_check(GameState.load_career() and GameState.best23 == keep, "Your Best 23 survives a save and load")


## Blooding (director, 2026-11-07: "a bit of a circular word salad"): each
## young player comes in once, for an older starter; a youngster brought in is
## never the next one out, a young starter is never dropped, and the note is
## the net change in one sentence. This list used to cycle: Y1 in for the
## 21-year-old, Y2 in for Y1, Y1 back in for Y2. Ages are fractional (days
## to the season start over 365.25) and the game shows whole years: the
## starter here is 21.6, shown as "21", and a youngster of 21.4 counts as 21.
func _test_blooding_net_change() -> void:
	_new_season()
	var side := GameState.current_side()
	var in23 := {}
	for k in side:
		for id in side[k]:
			in23[str(id)] = true
	for p in GameState.my_list:
		p["age"] = 28
		p["injury_weeks"] = 0
		p["overall"] = 72 if in23.has(str(p["id"])) else 40
	var fwd: Array = side["FWD"]
	var young_starter: Dictionary = GameState.list_player(str(fwd[0]))
	var w1: Dictionary = GameState.list_player(str(fwd[1]))
	var w2: Dictionary = GameState.list_player(str(fwd[2]))
	young_starter["age"] = 21.6
	young_starter["overall"] = 60
	w1["overall"] = 65
	w2["overall"] = 66
	var youngs: Array = []
	for p in GameState.my_list:
		if youngs.size() < 2 and not in23.has(str(p["id"])) and str(p["role"]) == "FWD":
			youngs.append(p)
	_check(youngs.size() == 2, "(two forwards outside the 23)")
	if youngs.size() < 2:
		return
	var y1: Dictionary = youngs[0]
	var y2: Dictionary = youngs[1]
	y1["age"] = 19
	y1["overall"] = 64
	y2["age"] = 21.4
	y2["overall"] = 63
	var pool: Array = GameState.my_list.filter(func(p): return Ratings.available(p))
	var r: Dictionary = GameState.blood_youth(side, pool)
	var out: Dictionary = r["side"]
	var ids := {}
	var n := 0
	for k in out:
		for id in out[k]:
			ids[str(id)] = true
			n += 1
	var name := func(p): return GameDB.player_display_name(p)
	_check(n == 23 and ids.size() == 23, "Blooding still names 23 different players")
	_check(ids.has(str(y1["id"])) and ids.has(str(y2["id"])), "Both young forwards come in")
	_check(not ids.has(str(w1["id"])) and not ids.has(str(w2["id"])), "The two weakest older forwards go out")
	_check(ids.has(str(young_starter["id"])), "A starter of 21.6 (shown as 21) is never dropped to blood another youngster")
	_check(str(r["note"]) == "Blooding %s for %s and %s for %s." % [name.call(y1), name.call(w1),
			name.call(y2), name.call(w2)], "Blooding names each youngster with the man he replaces, once: %s" % r["note"])
	y2["age"] = 22.0
	r = GameState.blood_youth(side, pool)
	_check(str(r["note"]) == "Blooding %s for %s." % [name.call(y1), name.call(w1)],
			"One youngster in, the same sentence: who he replaces (%s)" % r["note"])
	_check(not GameState.is_young(y2) and GameState.is_young({"age": 21.99}) and GameState.is_young({"age": 18.0}),
			"Young is 21 and under in whole years, as the game shows age")
	y1["age"] = 28
	r = GameState.blood_youth(side, pool)
	_check(str(r["note"]) == "No young player is close enough to take a senior spot. This is our best side."
			and r["side"] == side, "Nobody young close enough: the best side, and it says so")


## The blooding note stays within two lines at the 390 px phone width
## (GameState.BLOODING_NOTE_MAX characters) with three of the longest real
## names each way: full names when they fit, surnames when they don't.
func _test_blooding_note_fits() -> void:
	var names := ["Nasiah Wanganeen-Milera", "Archer Day-Wicks", "Lachlan Schultz-Ash",
			"Bailey Laurie-Macdonald", "Jamarra Ugle-Hagan", "Christopher Petracca"]
	var by_id := {}
	for i in range(names.size()):
		var parts: PackedStringArray = names[i].split(" ")
		by_id["L%d" % i] = {"id": "L%d" % i, "name": names[i], "generic_name": names[i], "real_name": names[i],
				"last": parts[1]}
	var note := GameState._blooding_note(["L0", "L1", "L2"], ["L3", "L4", "L5"], by_id)
	_check(note.length() <= GameState.BLOODING_NOTE_MAX and note.begins_with("Blooding Wanganeen-Milera for Laurie-Macdonald, ")
			and note.ends_with(" and Schultz-Ash for Petracca."),
			"Three long names each way fall back to surnames within %d characters (%d: %s)" % [
			GameState.BLOODING_NOTE_MAX, note.length(), note])
	note = GameState._blooding_note(["L1"], ["L5"], by_id)
	_check(note == "Blooding Archer Day-Wicks for Christopher Petracca.", "One each way keeps full names (%s)" % note)


## Complete synergy: a player left out for lacking one trait can come back
## for another the synergy needs. Tall-small needs two aerial forwards and
## two crumbers; the forward line's only crumber is its weakest man, so he is
## the one out while the aerials come in, and the list has one other crumber.
## He must come back (not "Not enough crumbers"), and the note is the net change.
func _test_complete_synergy_reentry() -> void:
	_new_season()
	var side := GameState.current_side()
	var in23 := {}
	for k in side:
		for id in side[k]:
			in23[str(id)] = true
	for p in GameState.my_list:
		p["injury_weeks"] = 0
		p["overall"] = 70 if in23.has(str(p["id"])) else 40
		var attr: Dictionary = p.get("attr", {})
		attr["marking"] = 40
		attr["goalkicking"] = 40
		p["attr"] = attr
	var crumber: Dictionary = GameState.list_player(str(side["FWD"][0]))
	crumber["overall"] = 50
	crumber["attr"]["goalkicking"] = 60
	var spare: Array = []
	for p in GameState.my_list:
		if spare.size() < 3 and not in23.has(str(p["id"])):
			p["role"] = "FWD"
			p["overall"] = 72
			spare.append(p)
	_check(spare.size() == 3, "(three players outside the 23)")
	if spare.size() < 3:
		return
	spare[0]["attr"]["marking"] = 80
	spare[1]["attr"]["marking"] = 80
	spare[2]["attr"]["goalkicking"] = 60
	_check(Traits.of(crumber).has("crumber") and Traits.of(spare[0]).has("aerial") and Traits.of(spare[2]).has("crumber"),
			"(one crumber in the side, two aerials and a crumber outside it)")
	var r: Dictionary = GameState.complete_synergy("tall_small", side)
	var ids := GameState._ids_in(r["side"])
	_check(str(r["problem"]) == "" and Traits.active(GameState._ground_for(r["side"])).has("tall_small"),
			"The crumber left out for an aerial comes back: tall-small is on (%s%s)" % [r["problem"], r["note"]])
	_check(ids.has(str(crumber["id"])) and not str(r["note"]).contains(GameDB.player_display_name(crumber)),
			"He is in the side, and the note is the net change without him (%s)" % r["note"])


## Complete synergy (director, 2026-10-07): it switches the synergy on with a
## legal 23 from available players, or leaves the side alone and says why.
func _test_complete_synergy() -> void:
	# Collingwood's real list can switch on its Lockdown unit; most real lists
	# are short of the traits for the others, and say so.
	GameState.reset()
	GameState.start_season("COL", GameDB.club_list("COL"))
	var side := GameState.current_side()
	var done := 0
	for key in Traits.SYNERGIES:
		if Traits.active(GameState._ground_for(side)).has(key):
			continue
		var r: Dictionary = GameState.complete_synergy(str(key), side)
		if str(r["problem"]) != "":
			_check(r["side"] == side, "%s: can't be done, the side is untouched (%s)" % [key, r["problem"]])
			continue
		done += 1
		var ground: Array = GameState._ground_for(r["side"])
		var ids := {}
		var count := 0
		var fit := true
		for k in r["side"]:
			for id in r["side"][k]:
				ids[str(id)] = true
				count += 1
				if not Ratings.available(GameState.list_player(str(id))):
					fit = false
		_check(Traits.active(ground).has(key) and count == 23 and ids.size() == 23 and fit,
				"%s: completed with 23 different available players (%s)" % [key, r["note"]])
	_check(done >= 1, "At least one synergy can be completed from a real list (%d)" % done)


func _test_named_side() -> void:
	_new_season()
	var side := GameState.current_side()
	# Swap a forward into the midfield and a midfielder forward.
	var fwd := str(side["FWD"][0])
	var mid := str(side["MID"][0])
	side["FWD"][0] = mid
	side["MID"][0] = fwd
	GameState.set_selection(side)
	var squad := GameState.my_squad()
	var roles := {}
	for p in squad.ground:
		roles[str(p["id"])] = str(p["role"])
	_check(roles.get(fwd, "") == "MID" and roles.get(mid, "") == "FWD",
			"Named players play where you put them, out of position too")
	_check(squad.ground.size() == 18 and squad.bench.size() == 5, "It is 18 plus 5")


func _test_gaps_and_overflow() -> void:
	_new_season()
	var side := GameState.current_side()
	var gone := str(side["DEF"][0])
	GameState.list_player(gone)["injury_weeks"] = 3
	# Overfill the forwards with two extra names from the bench.
	(side["FWD"] as Array).append(side["BENCH"][0])
	(side["FWD"] as Array).append(side["BENCH"][1])
	GameState.set_selection(side)
	var squad := GameState.my_squad()
	var ground := _ids(squad.ground)
	var counts := {"RUCK": 0, "MID": 0, "DEF": 0, "FWD": 0}
	for p in squad.ground:
		counts[str(p["role"])] = int(counts[str(p["role"])]) + 1
	_check(not ground.has(gone) and not _ids(squad.bench).has(gone),
			"An unavailable named player sits out")
	_check(counts == {"RUCK": 1, "MID": 5, "DEF": 6, "FWD": 6},
			"Every slot is filled exactly, gap filled and overflow capped (%s)" % str(counts))
	GameState.list_player(gone)["injury_weeks"] = 0


func _test_left_out_player_sits_out() -> void:
	_new_season()
	var side := GameState.current_side()
	var star := str(side["MID"][0])
	(side["MID"] as Array).erase(star)
	side["OUT"] = [star]
	GameState.set_selection(side)
	GameState.advance()
	var res: Dictionary = GameState.last_match
	_check(not (res.get("players", {}) as Dictionary).has(star),
			"A player you leave out records no stats")
	_check(GameState.last_duty(star) == "Reserves", "Left out fit, his XP report says reserves")


func _test_selection_saved() -> void:
	_new_season()
	var side := GameState.current_side()
	(side["MID"] as Array).remove_at(0)
	GameState.set_selection(side)
	GameState.save_career()
	GameState.load_career()
	_check(GameState.my_selection() == side, "The selection survives a save")
	GameState.set_selection({})
	_check(GameState.my_selection().is_empty(), "Auto-pick clears it")


## The profile remembers what a player did for you; a milestone is marked the
## week he reaches it.
func _test_with_us_and_milestones() -> void:
	_new_season()
	var year: int = GameState.season_year
	var id := str(GameState.current_side()["MID"][0])
	var p := GameState.list_player(id)
	p["career"] = {"games": 99, "goals": 30, "through": year - 1, "unknown": [],
			"stints": [["COL", year - 8, year - 6, 40, 10], ["GEE", year - 5, year - 1, 59, 20]]}
	GameState.honour_roll = [
		{"year": year - 3, "my_club": "GEE", "premier": "GEE", "my_bf": [{"id": id}]},
		{"year": year - 2, "my_club": "GEE", "premier": "SYD", "my_bf": [{"id": "someone"}]},
	]
	var w := GameState.with_us(p)
	_check(int(w["games"]) == 59 and int(w["goals"]) == 20 and int(w["since"]) == year - 5,
			"With us counts only his games for your club: %s" % str(w))
	_check(GameState.with_us_text(p) == "With us since %d: 59 games, 20 goals. Carji Greeves Medal %d. Premiership %d." % [
			year - 5, year - 3, year - 3], "With us in words: " + GameState.with_us_text(p))
	var notes := GameState.milestone_notes()
	var found := false
	for n in notes:
		if str(n["player_id"]) == id and str(n["text"]).ends_with("plays his 100th game."):
			found = true
	_check(found, "A player in the side on 99 games has his 100th marked: %s" % str(notes))
	p["career"]["games"] = 97
	var none := true
	for n in GameState.milestone_notes():
		if str(n["player_id"]) == id:
			none = false
	_check(none, "No milestone note on an ordinary week")
	var stranger := {"id": "x", "career": {"games": 10, "goals": 1, "through": year - 1, "unknown": [],
			"stints": [["SYD", year - 2, year - 1, 10, 1]]}}
	_check(GameState.with_us_text(stranger) == "", "Nothing for someone who never played for you")

## 18 + 5 (ARD-M5-001): the fifth interchange player is a full member of the
## 23 - he rotates on, piles up stats, is credited with the game and earns a
## selected player's XP - and a side saved with four on the bench gets five.
func _test_fifth_interchange() -> void:
	for code in ["GEE", "COL"]:
		var sq := Squad.new(code, GameDB.club_list(code), true, code)
		_check(sq.ground.size() == 18 and sq.bench.size() == Ratings.INTERCHANGE and Ratings.INTERCHANGE == 5,
				"%s picks 18 plus 5 (%d + %d)" % [code, sq.ground.size(), sq.bench.size()])
	var played_all := true
	var stats_all := true
	var quiet := []
	var stints := 0
	for seed in [701, 702, 703]:
		var sim := MatchSim.new(Squad.new("GEE", GameDB.club_list("GEE"), true, "GEE"),
				Squad.new("COL", GameDB.club_list("COL"), false, "COL"), seed)
		var bench_ids := [[], []]
		for side in 2:
			for p in (sim.squads[side] as Squad).bench:
				bench_ids[side].append(str(p["id"]))
		var res := sim.run()
		for side in 2:
			for id in bench_ids[side]:
				played_all = played_all and (sim._played[side] as Dictionary).has(id)
				var st: Dictionary = (res["players"] as Dictionary).get(id, {})
				stints += 1
				stats_all = stats_all and float(st.get("distance_run", 0.0)) > 0.0
				if int(st.get("disposals", 0)) + int(st.get("hitouts", 0)) + int(st.get("tackles", 0)) + int(st.get("marks", 0)) == 0:
					quiet.append("%s %s %s" % [seed, id, str(st)])
	_check(played_all, "All five on the bench come on during a match")
	_check(stats_all and quiet.size() * 10 <= stints, "All five on the bench take the field, and almost all get involved (quiet: %s)" % str(quiet))
	# A Running machine side (three Engines, tires 50% slower) barely needs to
	# rotate, but every interchange player still gets on, as in every AFL match.
	var rm_missed := []
	for seed in [701, 702, 703, 704]:
		var sim := MatchSim.new(Squad.new("GEE", GameDB.club_list("GEE"), true, "GEE"),
				Squad.new("COL", GameDB.club_list("COL"), false, "COL"), seed)
		for side in 2:
			if not (sim.synergies[side] as Array).has("running_machine"):
				(sim.synergies[side] as Array).append("running_machine")
		var bench_ids := [[], []]
		for side in 2:
			for p in (sim.squads[side] as Squad).bench:
				bench_ids[side].append(str(p["id"]))
		sim.run()
		for side in 2:
			for id in bench_ids[side]:
				if not (sim._played[side] as Dictionary).has(id):
					rm_missed.append("%d %d %s" % [seed, side, id])
	_check(rm_missed.is_empty(), "A Running machine side gets every interchange player on (missed: %s)" % str(rm_missed))

	# XP and the game count: a round through the real season.
	_new_season()
	var side := GameState.current_side()
	var fifth := str(side["BENCH"][4])
	var out := ""
	for p in GameState.my_list:
		var id := str(p["id"])
		var named := false
		for k in side:
			named = named or (side[k] as Array).has(id)
		if not named and Ratings.available(p):
			out = id
			break
	var mine := {}
	for r in GameState.season.lists["GEE"]:
		mine[str(r["id"])] = r
	var res2 := {"home": "GEE", "away": "COL", "players": {fifth: {"disposals": 8}}}
	var rep := GameState._grant_xp("GEE", GameState.season.lists["GEE"], res2)
	var row5 := {}
	var row_out := {}
	for r in rep["rows"]:
		if str(r["id"]) == fifth:
			row5 = r
		elif str(r["id"]) == out:
			row_out = r
	_check(bool(row5.get("on_bench", false)) and not bool(row5.get("reserves", true))
			and int(row5.get("xp", 0)) == GameState._xp_amount({"disposals": 8}, false, true),
			"The fifth interchange is credited as selected and paid for his own game (%s)" % str(row5))

	# An older save named four on the bench: the fifth is filled on match day.
	var four := GameState.current_side()
	(four["BENCH"] as Array).resize(4)
	GameState.set_selection(four)
	var sq2 := GameState.my_squad()
	var kept := true
	for id in four["BENCH"]:
		kept = kept and _ids(sq2.bench).has(str(id))
	_check(sq2.bench.size() == 5 and kept, "A side saved with four on the bench keeps them and gets a fifth")

## Dual ruck (director, 2026-10-06): when you run it, your second ruck takes
## the fifth interchange spot; it is off until you choose it, kept across a
## reload; AI clubs run it by their own rule (a spare ruck close to the player
## he would replace).
func _test_dual_ruck() -> void:
	_new_season()
	_check(not GameState.dual_ruck(), "Dual ruck is off until you choose it")
	var rucks_on_bench := func() -> int:
		var n := 0
		for p in GameState.my_squad().bench:
			if str(p.get("role", "")) == "RUCK":
				n += 1
		return n
	var spare := 0
	for p in GameState.my_list:
		if str(p.get("role", "")) == "RUCK" and Ratings.available(p):
			spare += 1
	GameState.set_dual_ruck(true)
	var sq := GameState.my_squad()
	_check(spare < 2 or (str((sq.bench[0] as Dictionary).get("role", "")) == "RUCK" and sq.bench.size() == 5),
			"With dual ruck, your second ruck takes a bench spot and the bench is still five")
	_check(GameState.my_selection().is_empty(), "Dual ruck on its own is still the auto-pick")
	GameState.save_career()
	GameState.load_career()
	_check(GameState.dual_ruck() and (spare < 2 or int(rucks_on_bench.call()) >= 1), "Dual ruck survives a reload")
	GameState.set_dual_ruck(false)
	_check(not GameState.dual_ruck(), "Dual ruck can be switched off")

	# The AI's rule: a spare ruck within the margin of the last bench player.
	var list: Array = GameDB.club_list("GEE").duplicate(true)
	var r := []
	for p in list:
		if str(p.get("role", "")) == "RUCK":
			r.append(p)
	if r.size() >= 2:
		var auto_sel := Ratings.select_22(list)
		var forced := Ratings.select_22(list, 1)
		var off := Ratings.select_22(list, 0)
		var has_ruck := func(b: Array) -> bool:
			for p in b:
				if str(p.get("role", "")) == "RUCK":
					return true
			return false
		_check(has_ruck.call(forced["bench"]) and (forced["bench"] as Array).size() == 5, "A dual-ruck call always benches the second ruck")
		# The bench player he would replace: the last in bench order, as the
		# rule reads it (not the lowest-rated, which a reshuffle can split from it).
		var last_ovr := float((off["bench"] as Array)[(off["bench"] as Array).size() - 1]["overall"])
		var spare_ovr := 0.0
		for p in Ratings.by_ruck(r):
			if not _ids(off["ground"]).has(str(p["id"])):
				spare_ovr = float(p["overall"])
				break
		_check(has_ruck.call(auto_sel["bench"]) == (spare_ovr >= last_ovr - Ratings.DUAL_RUCK_MARGIN) or has_ruck.call(off["bench"]),
				"An AI club runs dual ruck when its spare ruck is close enough (spare %.0f, last on the bench %.0f)" % [spare_ovr, last_ovr])


## A second position earns a spot on merit (director, 2026-10-06): a player left
## out who plays forward better than the weakest forward starter takes his
## place; the ruck and the bench's size are untouched, and without the merit
## pass (the audit baseline) he stays out.
func _test_merit_second_position() -> void:
	var list := []
	for p in GameDB.club_list("COL"):
		list.append(p.duplicate(true))
	var auto := Ratings.select_22(list)
	var on := {}
	for g in auto["ground"]:
		on[str(g["id"])] = true
	var best_fwd := {}
	for p in list:
		if str(p["role"]) == "FWD" and (best_fwd.is_empty() or int(p["overall"]) > int(best_fwd["overall"])):
			best_fwd = p
	var spare := {}
	for p in list:
		if not on.has(str(p["id"])) and str(p["role"]) in ["MID", "DEF"] and str(p.get("role2", "")) == "" 				and (p.get("learned", []) as Array).is_empty() and Ratings.available(p):
			spare = p
			break
	_check(not spare.is_empty() and not best_fwd.is_empty(), "Someone is left out of the side")
	if spare.is_empty() or best_fwd.is_empty():
		return
	# He has learned to play forward, and plays it as well as the best forward;
	# his own rating (what orders his own line) is unchanged, so only the
	# merit pass can bring him in.
	spare["role2"] = "FWD"
	spare["attr"] = (best_fwd["attr"] as Dictionary).duplicate()
	Ratings.merit_lines = false
	var before := Ratings.select_22(list)
	Ratings.merit_lines = true
	var after := Ratings.select_22(list)
	var where := ""
	for g in after["ground"]:
		if str(g["id"]) == str(spare["id"]):
			where = str(g["role"])
	var ruck_b := ""
	var ruck_a := ""
	for g in before["ground"]:
		if str(g["role"]) == "RUCK":
			ruck_b = str(g["id"])
	for g in after["ground"]:
		if str(g["role"]) == "RUCK":
			ruck_a = str(g["id"])
	_check(not _ids(before["ground"]).has(str(spare["id"])), "Without the merit pass a second position waits for a line to run short")
	_check(where == "FWD", "On merit, a player who has learned forward is picked there ahead of a weaker forward")
	_check(after["ground"].size() == 18 and after["bench"].size() == Ratings.bench_size and ruck_a == ruck_b,
			"The ruck and the bench's size are untouched")


## Dragging a player shows his name on one line, not a column of single
## letters (director's screenshot, 2026-11-07): the preview never wraps and is
## as wide as the whole name.
func _test_drag_preview_one_line() -> void:
	var name := "Xavier Taylor"
	var l: Label = load("res://scripts/ui/TeamBuilder.gd").drag_preview(name)
	_check(l.autowrap_mode == TextServer.AUTOWRAP_OFF, "The drag preview never wraps")
	var font: Font = l.get_theme_font("font")
	var fs := l.get_theme_font_size("font_size")
	var w := font.get_string_size(name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var one: Label = load("res://scripts/ui/TeamBuilder.gd").drag_preview("X")
	var line_h := one.get_minimum_size().y
	one.free()
	var min_size := l.get_minimum_size()
	_check(min_size.x >= w - 0.5, "The drag preview is as wide as the whole name (%.0f >= %.0f)" % [min_size.x, w])
	_check(is_equal_approx(min_size.y, line_h), "The drag preview is one line tall (%.0f, one line is %.0f)" % [min_size.y, line_h])
	_check(l.get_theme_constant("outline_size") >= 3, "The drag preview is outlined so it reads over the turf")
	l.free()


## Key posts (director, 2026-11-07: "Small defenders placed in key defender
## spots"). The auto-pick puts the line's key position players at full-back
## and centre half-back, full-forward and centre half-forward (index 0 and 5
## of the line, TeamBuilder.SPOTS); a line short of them puts its tallest
## there; a coach's own placement is kept as he set it.
func _key_posts_held(line_ids: Array, line: String, by_id: Dictionary) -> bool:
	var keys := 0
	for id in line_ids:
		if Roles.is_key_post(by_id[str(id)], line):
			keys += 1
	if line_ids.size() < 6:
		return false
	var posts := [str(line_ids[0]), str(line_ids[5])]
	var held := 0
	for id in posts:
		if Roles.is_key_post(by_id[id], line):
			held += 1
	return held == mini(keys, 2)


func _test_key_posts() -> void:
	# The spot order the rule lays out against.
	var spots: Dictionary = load("res://scripts/ui/TeamBuilder.gd").SPOTS
	_check(str(spots["DEF"][0]) == "FB" and str(spots["DEF"][5]) == "CB"
			and str(spots["FWD"][0]) == "FF" and str(spots["FWD"][5]) == "HFF",
			"The line's first and last spots are the key posts")
	# Every club's auto-picked side, as the AI picks it.
	var lines_with_keys := 0
	for code in GameDB.club_order:
		var list: Array = GameDB.club_list(code)
		if list.size() < 23:
			continue  # an expansion club, no list until it is drafted
		var by_id := {}
		for p in list:
			by_id[str(p["id"])] = p
		var sel := Ratings.select_22(list)
		for line in ["DEF", "FWD"]:
			var ids := []
			for p in sel["ground"]:
				if str(p["role"]) == line:
					ids.append(str(p["id"]))
			for id in ids:
				if Roles.is_key_post(by_id[id], line):
					lines_with_keys += 1
					break
			_check(_key_posts_held(ids, line, by_id),
					"%s %s: the key players hold the key posts (%s)" % [code, line, str(ids.map(func(i): return "%s%s" % [GameDB.player_display_name(by_id[i]), "*" if Roles.is_key_post(by_id[i], line) else ""]))])
	_check(lines_with_keys >= 20, "Most lines on real lists have a key player to place (%d)" % lines_with_keys)

	# Your side: every auto-pick strategy, and an AI club's side as you see it.
	_new_season()
	var mine := {}
	for p in GameState.my_list:
		mine[str(p["id"])] = p
	for strat in ["best", "rest", "youth"]:
		var side: Dictionary = GameState.auto_pick(strat)["side"]
		for line in ["DEF", "FWD"]:
			_check(_key_posts_held(side[line], line, mine), "Auto-pick %s: %s key posts held" % [strat, line])
	var cur := GameState.current_side()
	_check(_key_posts_held(cur["DEF"], "DEF", mine) and _key_posts_held(cur["FWD"], "FWD", mine),
			"Your side before you touch it: key posts held")
	var opp: Dictionary = GameState.opponent_side("COL")
	var theirs := {}
	for p in opp["list"]:
		theirs[str(p["id"])] = p
	_check(_key_posts_held(opp["side"]["DEF"], "DEF", theirs) and _key_posts_held(opp["side"]["FWD"], "FWD", theirs),
			"An AI club's side: key posts held")

	# A coach's own placement is never re-shuffled: a flanker named at
	# full-back stays at full-back, through the match-day squad and back.
	var named: Dictionary = cur.duplicate(true)
	var defs: Array = named["DEF"]
	var fb := str(defs[0])
	defs[0] = defs[1]
	defs[1] = fb
	GameState.set_selection(named)
	var order := []
	for p in GameState.my_squad().ground:
		if str(p["role"]) == "DEF":
			order.append(str(p["id"]))
	_check(order == (named["DEF"] as Array) and GameState.current_side()["DEF"] == named["DEF"],
			"Your own placement plays and shows as you set it")
	_check(GameState.save_career() and GameState.load_career() and GameState.current_side()["DEF"] == named["DEF"],
			"Your placement survives a save and load unchanged")
	GameState.set_selection({})

	# Lines built from real players: key defenders and non-key defenders.
	var keys: Array = []
	var smalls: Array = []
	for code in GameDB.club_order:
		for p in GameDB.club_list(code):
			if str(p.get("role", "")) != "DEF":
				continue
			if Roles.is_key_post(p, "DEF"):
				keys.append(p)
			elif smalls.size() < 6:
				smalls.append(p)
	_check(keys.size() >= 2 and smalls.size() == 6, "(real key and non-key defenders to build lines from)")
	if keys.size() < 2 or smalls.size() < 6:
		return

	# A line with no key players: the tallest two take the posts, the better
	# rated first, everyone else keeps his order.
	var line := []
	var heights := [180.0, 195.0, 182.0, 190.0, 185.0, 183.0]
	for i in range(6):
		var c: Dictionary = (smalls[i] as Dictionary).duplicate()
		c["id"] = "k%d" % i
		c["overall"] = 70 - i
		c["height_cm"] = heights[i]
		line.append(c)
	_check(line.all(func(c): return not Roles.is_key_post(c, "DEF")), "(the made-up line has no key defender)")
	var laid: Array = Roles.key_post_order(line, "DEF").map(func(p): return str(p["id"]))
	_check(laid == ["k1", "k0", "k2", "k4", "k5", "k3"],
			"Short of key players, the tallest take the posts (%s)" % str(laid))

	# Five defenders: there is no centre half-back spot (TeamBuilder.SPOTS
	# index 5), so only the full-back post is laid out. The second key
	# defender keeps his own place, never pushed into the back pocket.
	var k1: Dictionary = (keys[0] as Dictionary).duplicate()
	var k2: Dictionary = (keys[1] as Dictionary).duplicate()
	k1["id"] = "K1"
	k1["overall"] = 80
	k2["id"] = "K2"
	k2["overall"] = 75
	var five := [line[0], k2, line[2], k1, line[4]]
	laid = Roles.key_post_order(five, "DEF").map(func(p): return str(p["id"]))
	_check(laid == ["K1", "k0", "K2", "k2", "k4"],
			"Five defenders: the best key defender at full-back, the rest in order (%s)" % str(laid))
	# Six: the second key defender goes to centre half-back, index 5.
	var six := [line[0], k2, line[2], k1, line[4], line[5]]
	laid = Roles.key_post_order(six, "DEF").map(func(p): return str(p["id"]))
	_check(laid == ["K1", "k0", "k2", "k4", "k5", "K2"] and Roles.SECOND_POST == 5,
			"Six defenders: key defenders at full-back and centre half-back (%s)" % str(laid))


## The key posts read key players the way the match does (Matchups): for
## every player on every club list, in both lines, Roles.is_key_post on the
## list player agrees with Matchups on his match-day copy in that line.
func _test_key_posts_match_sim() -> void:
	var n := 0
	var bad: Array = []
	for code in GameDB.club_order:
		for p in GameDB.club_list(code):
			for line in ["DEF", "FWD"]:
				var copy := Ratings._for_slot(p, line)
				var sim := Matchups.is_key_defender(copy) if line == "DEF" else Matchups.is_key_forward(copy)
				n += 1
				if Roles.is_key_post(p, line) != sim:
					bad.append("%s %s" % [GameDB.player_display_name(p), line])
	_check(n > 1000 and bad.is_empty(), "Key posts and the match agree on every player in both lines (%d, off: %s)" % [n, str(bad.slice(0, 5))])

	# The default duel goes to whoever stands in the post: name a non-key
	# defender at full-back and he takes their best key forward.
	_new_season()
	var named: Dictionary = GameState.current_side().duplicate(true)
	var defs: Array = named["DEF"]
	var fb := str(defs[0])
	var flank := str(defs[1])
	defs[0] = flank
	defs[1] = fb
	GameState.set_selection(named)
	var their_ground: Array = Squad.new("COL", GameDB.club_list("COL"), false, "COL").ground
	var mine: Array = GameState.my_squad().ground
	var d := Matchups.defaults(their_ground, mine)
	var first := Matchups.key_forwards(their_ground)
	_check(not first.is_empty() and str(d.get(str(first[0]["id"]), "")) == flank,
			"The man you name at full-back takes their best key forward by default")
	var posts := Matchups.duel_defenders(mine)
	var line_ids := []
	for p in mine:
		if str(p["role"]) == "DEF":
			line_ids.append(str(p["id"]))
	_check(str(posts[0]["id"]) == str(line_ids[0]) and str(posts[1]["id"]) == str(line_ids[5]),
			"The duel defenders are the full-back, then the centre half-back")

	# The desktop oval keeps your placement: the full-back you named is drawn
	# at FB, not re-sorted by rating or by the key posts.
	var ov := FormationView.new()
	var sq := GameState.my_squad()
	var placed: Array = ov._assign(sq.ground, sq.bench, true)
	var at := {}
	for e in placed:
		if not bool(e["bench"]):
			at[str(e["slot"]["key"])] = str(e["player"]["id"])
	var mids: Array = named["MID"]
	_check(at.get("FB", "") == flank and at.get("CB", "") == str(defs[5]) and at.get("FF", "") == str(named["FWD"][0])
			and at.get("C", "") == str(mids[0]),
			"The desktop oval draws your side in your order (FB %s, C %s)" % [at.get("FB", ""), at.get("C", "")])
	ov.free()
	GameState.set_selection({})


## Youth auto-pick never cycles (director's screenshot: "Harry Armstrong for
## Ethan Read; Josh Dolan for Harry Armstrong; Harry Armstrong for Josh
## Dolan"): with a crowd of young players level with the starters, each
## youngster comes in once, nobody swapped out comes back, and the note names
## exactly the net change.
func _test_youth_no_cycle() -> void:
	_new_season()
	var best: Dictionary = GameState.auto_pick("best")["side"]
	var in23 := {}
	for k in best:
		for id in best[k]:
			in23[str(id)] = true
	for p in GameState.my_list:
		p["injury_weeks"] = 0
		p["age"] = 28.0 if in23.has(str(p["id"])) else 19.0
		p["overall"] = 72 if in23.has(str(p["id"])) else 70
	var r: Dictionary = GameState.auto_pick("youth")
	var after := {}
	for k in r["side"]:
		for id in r["side"][k]:
			after[str(id)] = true
	var came: Array = after.keys().filter(func(id): return not in23.has(id))
	var went: Array = in23.keys().filter(func(id): return not after.has(id))
	_check(after.size() == 23 and came.size() == went.size() and came.size() >= 1 and came.size() <= GameState.YOUTH_MAX,
			"Blooding swaps up to %d in for as many out (%d in, %d out)" % [GameState.YOUTH_MAX, came.size(), went.size()])
	var note := str(r["note"])
	var once := true
	# Full names, or surnames when three pairs run past two lines.
	var surnames := false
	if not came.is_empty():
		surnames = not note.contains(GameDB.player_display_name(GameState.list_player(came[0])))
	for id in came + went:
		var p: Dictionary = GameState.list_player(id)
		var nm := GameDB.card_surname(p) if surnames else GameDB.player_display_name(p)
		if note.count(nm) != 1:
			once = false
	_check(once and note.count(" for ") == came.size(), "Each youngster and each man out is named once, no swap back: %s" % note)
