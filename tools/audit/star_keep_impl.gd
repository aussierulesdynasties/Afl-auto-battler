extends RefCounted
## Do rival clubs keep their stars? (bug bash 2026-11-23: a 2010 Legacy start
## saw Geelong let Corey Enright and Matthew Scarlett go to North Melbourne.)
##
## One autopilot career per start year and seed: the real lists of that year,
## every season played with advance() and every off-season run by the same
## calls the game makes. For each rival club, every player rated `min_ovr` or
## more before the off-season opens who is not retiring is followed through it:
## kept, traded, or let go (and if let go, why: "cap" when the club wanted him
## but could not fit his price, "tested" when he tested free agency with his
## club's offer on the table and took another, else "delist") and where he signed.
## Measurement only: it changes no rule.
##
## Args after the impl name: starts (comma-separated years, default 2010)
## seeds (comma-separated, default 1) seasons (default 3) min_ovr (default 80).
## godot --headless --path . --script tools/audit/run_audit.gd -- star_keep_impl 2010,1995 1,2 3 80
## One STAR line per star who left, one YEAR line per off-season, SUMMARY last.
const Ovr := preload("res://tests/ovr.gd")

var total_stars := 0
var total_lost := {}


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var starts := str(args[1]) if args.size() > 1 else "2010"
	var seeds := str(args[2]) if args.size() > 2 else "1"
	var seasons := int(args[3]) if args.size() > 3 else 3
	var min_ovr := int(args[4]) if args.size() > 4 else 80
	for st in starts.split(",", false):
		for sd in seeds.split(",", false):
			_career(str(st), int(sd), seasons, min_ovr)
	print("SUMMARY stars %d | lost %s" % [total_stars, str(total_lost)])


func _career(start: String, seed: int, seasons: int, min_ovr: int) -> void:
	var gs := GameDB.get_tree().root.get_node("GameState")
	gs.autosave_enabled = false
	gs.reset(start)
	gs.career_seed = seed
	gs.replay_seed = seed
	gs.begin_real_lists()
	# Coach a club far from the stars being watched: the last in the order.
	var order: Array = GameDB.active_clubs(gs.season_year) if gs.season_year > 0 else GameDB.club_order
	gs.choose_real_club(str(order[(seed * 7) % order.size()]))
	_draft(gs)
	gs.finish_intake_draft()
	for y in range(seasons):
		RookieList.settle(gs)
		while not gs.season.is_season_over():
			gs.advance()
		var year: int = gs.season_year
		# Stars on rival lists before the off-season opens.
		var stars := {}
		for code in gs.season.lists:
			if code == gs.my_club:
				continue
			for p in gs.season.lists[code]:
				if int(Ovr.of(p, 0)) >= min_ovr:
					stars[str(p["id"])] = {"club": str(code), "p": p, "ovr": int(Ovr.of(p)),
							"age": float(p.get("age", 0)), "years": int(p.get("contract_years", 1)),
							"salary": int(p.get("salary", 0))}
		# A rival board's letter holds the off-season until it is answered:
		# the coach stays put, as the test suites answer it.
		ClubMoves.settle_letter(gs)
		gs.open_offseason()
		# Who went to test the market, read before anyone signs him (signing
		# clears the marks).
		var testers := {}
		for id in stars:
			if str((stars[id]["p"] as Dictionary).get("home_offer", "")) == stars[id]["club"]:
				testers[id] = true
		var cap_lines := {}
		for code in gs.season.lists:
			cap_lines[str(code)] = "payroll %d cap %d list %d" % [Contracts.payroll(gs.season.lists[code]),
					gs.cap_for(str(code)), (gs.season.lists[code] as Array).size()]
		if gs.begin_intake_draft():
			_draft(gs)
			gs.finish_intake_draft()
		else:
			gs.start_next_season()
		if gs.season_year == year:
			break
		var released := {}
		var traded := {}
		for e in gs.offseason_log:
			var kind := str(e.get("kind", ""))
			if kind == "released":
				released[str(e["id"])] = bool(e.get("wanted", false))
			elif kind == "ai_trade" or kind == "trade":
				for id in (e.get("in", []) as Array) + (e.get("out", []) as Array):
					traded[str(id)] = true
		var retired := {}
		for r in (gs.intake_summary.get("retired", []) as Array):
			retired[str(r["id"])] = true
		var where := {}
		for code in gs.season.lists:
			for p in gs.season.lists[code]:
				where[str(p["id"])] = str(code)
		var lost := 0
		var n := 0
		for id in stars:
			var s: Dictionary = stars[id]
			if retired.has(id):
				continue
			n += 1
			var now := str(where.get(id, "-"))
			if now == s["club"]:
				continue
			# A tester went to the market with his club's offer on the table
			# (GameState.tests_market) and took a better one: free agency, not cap.
			var tested: bool = testers.has(id)
			var how := "traded" if traded.has(id) else ("tested" if tested else
					("cap" if bool(released.get(id, false)) else ("delist" if released.has(id) else "?")))
			lost += 1
			total_lost[how] = int(total_lost.get(how, 0)) + 1
			print("STAR start %s seed %d off %d | %s %s OVR %d age %.0f yrs_left %d salary %d | %s -> %s | %s | club %s" % [
					start, seed, year, id, GameDB.player_display_name(s["p"]), s["ovr"], s["age"], s["years"],
					s["salary"], s["club"], now, how, cap_lines.get(s["club"], "")])
		total_stars += n
		print("YEAR start %s seed %d off %d | rival stars %d | left %d" % [start, seed, year, n, lost])


func _draft(gs) -> void:
	var guard := 0
	while gs.draft != null and not gs.draft.is_finished() and guard < 5000:
		guard += 1
		if gs.draft.is_user_turn():
			if not gs.draft.pick_for_me():
				gs.draft._skip_current_pick()
		else:
			gs.draft.auto_until_user_turn()
