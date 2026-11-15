extends RefCounted
## The legacy_lists_probe body, loaded at runtime (autoloads exist by then).


func _probe(gs, ds: String) -> void:
	gs.reset(ds)
	gs.replay_seed = 7
	gs.career_seed = 7
	gs.begin_real_lists()
	var club: String = (gs.league_lists.keys() as Array)[0]
	gs.choose_real_club(club)
	var guard := 0
	while gs.draft != null and not gs.draft.is_finished() and guard < 400:
		guard += 1
		if gs.draft.is_user_turn():
			var board: Array = gs.draft.board("", "", "", "overall", true)
			if board.is_empty() or not gs.draft.pick(board[0]):
				break
		else:
			gs.draft.auto_until_user_turn()
	gs.finish_intake_draft()
	var y: int = gs.season_year
	print("=== set '%s' season %d, my club %s, cap %d, list max %d min %d" % [ds, y, club, gs.salary_cap,
			Contracts.max_list(), Contracts.min_list()])
	var tot := {"n": 0, "pay": 0.0}
	for code in gs.season.lists:
		var l: Array = gs.season.lists[code]
		tot["n"] += l.size()
		tot["pay"] += float(Contracts.payroll(l)) / float(gs.cap_for(code))
	var nc: int = gs.season.lists.size()
	print("  start: avg list %.1f, avg payroll %.1f%% of cap" % [float(tot["n"]) / nc, 100.0 * float(tot["pay"]) / nc])
	gs.season.round_index = gs.season.fixture.size()
	gs.ensure_finals()
	guard = 0
	while not gs.season.is_season_over() and guard < 60:
		guard += 1
		gs.advance()
	# Count before the market touches the lists: as open_offseason sees them.
	var pre := {}
	for code in gs.season.lists:
		pre[code] = (gs.season.lists[code] as Array).duplicate()
	var old_cap: int = gs.salary_cap
	# A rival board's letter holds the off-season; he stays put.
	if ClubMoves.letter_open(gs):
		ClubMoves.decline_letter(gs)
	gs.board.erase("sacked")
	gs.open_offseason()
	print("  offseason open %s (over %s, sacked %s, letter %s, offers %d)" % [str(gs.offseason_open()), str(gs.season.is_season_over()),
			str(gs.is_sacked()), str(ClubMoves.letter_open(gs)), ClubMoves.offers(gs).size()])
	var all_pay := 0
	for p in pre[club]:
		all_pay += int(p.get("salary", 0))
	print("  MY CLUB room as shown now %d (cap %d, payroll %d); the old count: %d (cap %d, everyone %d)" % [
			gs.cap_room(), gs.cap_for(club), gs.my_payroll(), old_cap - all_pay, old_cap, all_pay])
	var rows := []
	var sums := {"ret": 0, "young": 0, "exp": 0, "pay": 0.0, "ask": 0.0, "real": 0}
	for code in pre:
		var l: Array = pre[code]
		var ret := 0
		var young := 0
		var real := 0
		var exp := 0
		var keep_pay := 0
		var ask := 0
		for p in l:
			if gs.retiring_now(p):
				ret += 1
				if float(p.get("age", 0)) < 27.0:
					young += 1
				if int(p.get("real_last", 0)) > 0:
					real += 1
				continue
			if int(p.get("contract_years", 1)) <= 1:
				exp += 1
				ask += Contracts.asking_salary(p)
			else:
				keep_pay += int(p.get("salary", 0))
		var cap: int = gs.cap_for(code)
		sums["ret"] += ret; sums["young"] += young; sums["exp"] += exp; sums["real"] += real
		sums["pay"] += float(keep_pay) / cap
		sums["ask"] += float(ask) / cap
		if code == club:
			print("  MY CLUB %s list %d: retiring %d (under 27: %d, by real record %d), expiring %d, signed-on payroll %.1f%% of cap, expiring asks %.1f%%, room %d, cap %d" % [
					code, l.size(), ret, young, real, exp, 100.0 * keep_pay / cap, 100.0 * ask / cap, cap - keep_pay, cap])
	print("  league avg per club: retiring %.1f (under 27 %.1f, real-record %.1f), expiring %.1f, signed-on payroll %.1f%%, expiring asks %.1f%%" % [
			float(sums["ret"]) / nc, float(sums["young"]) / nc, float(sums["real"]) / nc, float(sums["exp"]) / nc,
			100.0 * sums["pay"] / nc, 100.0 * sums["ask"] / nc])
	print("  next-season cap %d (offseason salary_cap %d)" % [Contracts.salary_cap_for_year(y + 1), gs.salary_cap])
