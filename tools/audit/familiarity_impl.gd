extends RefCounted
## Team familiarity (TODO row 125): how often do clubs reach four new-club men in a
## selected side? Real yardstick from the row's proposal: of 234 Round 1 sides, 28
## had five or more arrivals counting first-gamers, and six sides averaged four or
## more new-club men across Rounds 1-6.
##
## One career per seed from the seeded League Draft. Computer clubs run themselves.
## With "active" your club also makes up to two trades and two free-agency bids an
## off-season (a typical coach, tools/audit/career_impl.gd's bots, smaller); with
## "auto" it is on autopilot like the rest.
## Every side is read before each of Rounds 1-6, as MatchSim would name it.
## Also proves the rule reaches every move: a man new to a club's list after an
## off-season must carry a familiarity. Measurement only: it changes no rule.
##
## Args after the impl name: seeds (default 301), seasons (default 6), auto|active.
## godot --headless --path . --script tools/audit/run_audit.gd -- familiarity_impl 301,302 6 active

var dyn = load("res://tools/balance/dynasty.gd").new()
var gs: Node
var user := ""
## Tallies over all careers, computer clubs ("cpu") and your club ("you").
var tally := {}
var missing := 0
var arrivals_seen := 0


func run() -> void:
	gs = GameDB.get_tree().root.get_node("GameState")
	var args := OS.get_cmdline_user_args()
	var seeds := str(args[1]) if args.size() > 1 else "301"
	var seasons := int(args[2]) if args.size() > 2 else 6
	var active := args.size() > 3 and str(args[3]) == "active"
	for key in ["cpu", "you"]:
		tally[key] = {"r1": 0, "r1_4": 0, "r1_5_all": 0, "avg_4": 0, "new_sum": 0.0,
				"new_hist": {}, "dft_hist": {}, "fam_at_r1": {}}
	for sd in seeds.split(",", false):
		_career(int(sd), seasons, active)
	_report()


func _ids(list: Array) -> Dictionary:
	var out := {}
	for p in list:
		out[str(p["id"])] = true
	return out


func _bump(d: Dictionary, k: Variant) -> void:
	d[k] = int(d.get(k, 0)) + 1


func _career(seed: int, seasons: int, active: bool) -> void:
	gs.autosave_enabled = false
	gs.reset()
	gs.career_seed = seed
	gs.replay_seed = seed
	var d: Draft = dyn.make_upside_draft(seed, 5)
	user = d.user_club if d.user_club != "" else str(d.draft_order[0])
	gs.draft = d
	gs.start_season(user, [])
	for y in range(seasons):
		_play_season(y > 0)
		var before := {}
		for code in gs.season.lists:
			before[str(code)] = _ids(gs.season.lists[code])
		gs.open_offseason()
		if active:
			_trade_bot(2)
			_fa_bot(2)
		var drafting: bool = gs.begin_intake_draft()
		if drafting:
			var guard := 0
			while not gs.draft.is_finished() and guard < 5000:
				guard += 1
				var code: String = gs.draft.current_club()
				var c: Dictionary = gs.draft._best_ai_pick(code)
				if c.is_empty() or not gs.draft._draft_pick(code, c):
					gs.draft._skip_current_pick()
			gs.finish_intake_draft()
		else:
			gs.start_next_season()
		_check_new(before)
	print("SUMMARY seed %d user %s seasons %d" % [seed, user, seasons])


## Play a season to its end, counting each side before Rounds 1-6 (the first season
## has nobody new: a career starts at 100, so it is not counted).
func _play_season(count: bool) -> void:
	var by_club := {}
	while not gs.season.is_season_over():
		if count and not gs.preseason_active():
			var rnd: int = gs.season.round_index
			if rnd >= 0 and rnd < 6 and not by_club.has(rnd):
				by_club[rnd] = _read_sides(rnd)
		gs.advance()
	if not count:
		return
	var totals := {}
	for rnd in by_club:
		for code in by_club[rnd]:
			var row: Array = by_club[rnd][code]
			totals[code] = float(totals.get(code, 0.0)) + float(row[0])
	for code in totals:
		var t: Dictionary = tally["you" if code == user else "cpu"]
		if float(totals[code]) / max(1, by_club.size()) >= 4.0:
			t["avg_4"] += 1


func _read_sides(rnd: int) -> Dictionary:
	var out := {}
	for code in gs.season.lists:
		var sq := Squad.new(str(code), gs.season.lists[code], false, str(code))
		var side: Array = sq.ground + sq.bench
		var new_men: int = TeamFamiliarity.new_club_men(side).size()
		var draftees := 0
		var first := 0
		for p in side:
			if TeamFamiliarity.value(p) < 100.0 and TeamFamiliarity.is_draftee(p):
				draftees += 1
			elif bool(p.get("team_fam_first", false)):
				first += 1
		out[str(code)] = [new_men, draftees, first]
		var t: Dictionary = tally["you" if str(code) == user else "cpu"]
		_bump(t["new_hist"], new_men)
		_bump(t["dft_hist"], draftees)
		if rnd == 0:
			t["r1"] += 1
			t["new_sum"] += new_men
			if new_men >= TeamFamiliarity.TEAM_ARRIVALS:
				t["r1_4"] += 1
			if new_men + draftees + first >= 5:
				t["r1_5_all"] += 1
			for p in side:
				if TeamFamiliarity.value(p) < 100.0:
					_bump(t["fam_at_r1"], roundi(TeamFamiliarity.value(p)))
			print("ROUND1 year %d club %s user %d | new-club %d draftees %d first-gamers %d" % [
					gs.season_year, code, 1 if str(code) == user else 0, new_men, draftees, first])
	return out


## Everyone new to a list since the off-season opened must be carrying familiarity.
func _check_new(before: Dictionary) -> void:
	for code in before:
		if not gs.season.lists.has(code):
			continue
		for p in gs.season.lists[code]:
			if before[code].has(str(p["id"])):
				continue
			arrivals_seen += 1
			if not p.has("team_fam"):
				missing += 1
				print("MISSING %s at %s, year %d" % [str(p["id"]), code, gs.season_year])


func _trade_bot(most: int) -> void:
	var made := 0
	for code in gs.season.lists.keys():
		if str(code) == user or made >= most:
			continue
		var theirs: Array = (gs.season.lists[code] as Array).duplicate()
		theirs.sort_custom(func(a, b): return int(a["overall"]) > int(b["overall"]))
		var mine: Array = gs.my_list.duplicate()
		mine.sort_custom(func(a, b): return int(a["overall"]) > int(b["overall"]))
		var done := false
		for t in theirs.slice(0, 8):
			if done or float(t.get("age", 25.0)) > 30.0:
				continue
			for i in range(10, mini(30, mine.size())):
				if int(t["overall"]) <= int(mine[i]["overall"]):
					continue
				var v: Dictionary = gs.evaluate_trade(str(code), [str(mine[i]["id"])], [str(t["id"])])
				if bool(v.get("ok", false)) and bool(gs.make_trade(str(code), [str(mine[i]["id"])], [str(t["id"])]).get("ok", false)):
					made += 1
					done = true
					break


func _fa_bot(most: int) -> void:
	var fas: Array = gs.free_agents.duplicate()
	fas.sort_custom(func(a, b): return int(a["overall"]) > int(b["overall"]))
	var bids := 0
	for p in fas.slice(0, 12):
		if bids >= most:
			break
		var terms: Dictionary = gs.free_agent_terms(str(p["id"]))
		if bool(terms.get("refuse", false)):
			continue
		var want: Dictionary = Contracts.wants(p)
		var r: Dictionary = gs.offer_free_agent(str(p["id"]), int(want["salary"]) + int(terms.get("premium", 0)), int(want["years"]))
		if bool(r.get("ok", false)):
			bids += 1


func _report() -> void:
	for key in tally:
		var t: Dictionary = tally[key]
		var n: int = maxi(1, int(t["r1"]))
		print("FAM %s | Round 1 sides %d | 4+ new-club men %d (%.1f%%) | 5+ arrivals with first-gamers and draftees %d (%.1f%%) | averaged 4+ over Rounds 1-6 %d (%.1f%%) | mean new-club men in Round 1 %.2f" % [
				key, t["r1"], t["r1_4"], 100.0 * t["r1_4"] / n, t["r1_5_all"], 100.0 * t["r1_5_all"] / n,
				t["avg_4"], 100.0 * t["avg_4"] / n, t["new_sum"] / n])
		print("FAM %s | sides by new-club men, Rounds 1-6 %s | by draftees %s | familiarity in Round 1 %s" % [
				key, str(t["new_hist"]), str(t["dft_hist"]), str(t["fam_at_r1"])])
	print("FAM arrivals checked %d, without a familiarity %d" % [arrivals_seen, missing])
