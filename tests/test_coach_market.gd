extends RefCounted
## The coaching world moving (CoachMarket.gd, Coaching Phase 3): move rules,
## eligibility, hiring, sackings, retirement, vacancy chains, your staff
## being poached, released and replaced, generation, expansion, archive and
## save/load. Run through tests/run_coach_market_tests.gd.

var failures: Array[String] = []
var checks := 0

## Every season and draft here is seeded (C15): a clock seed makes a different
## league each run.
const SUITE_SEED := 2027
const Y := 2026
const SEED := 4242


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	_t("_test_move_rules")
	_t("_test_eligibility")
	_t("_test_hiring")
	_t("_test_senior_coach_decisions")
	_t("_test_retirement_and_pruning")
	_t("_test_vacancy_chain")
	_t("_test_your_staff")
	_t("_test_generation_and_expansion")
	_t("_test_long_run")
	_t("_test_game_flow")
	_t("_test_assistant_contracts")
	_t("_test_your_expiring_staff")
	_t("_test_approaches_market")
	_t("_test_approaches_flow")
	_t("_test_staff_promises")
	_t("_test_ai_clubs_counter")
	_t("_test_promise_flow")
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	print(Ran.line("Coach market", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _coach(cid: String, status: String, club: String, job: String, skills := [72, 72, 72], spec := "") -> Dictionary:
	var c := {"cid": cid, "real_name": "", "generic_name": cid, "former_player_id": "", "spec": spec,
		"skills": {"teach": skills[0], "tactics": skills[1], "manage": skills[2]},
		"status": status, "club": club, "job": job, "free_from": 0, "stints": [],
		"former_sc": job == "SC", "note": "", "origin": "generated", "played": {},
		"born": Y - 45, "rep": 50, "since": Y - 2, "fail_streak": 0, "protect_to": 0,
		"sacked_by": {}, "moves": []}
	if status == "club":
		(c["stints"] as Array).append([club, job, Y - 2, 0])
	if job == "SC":
		c["sc_since"] = Y - 2
		c["contract_to"] = Y + 2
	return c


func _test_move_rules() -> void:
	_check(CoachMarket.move_kind("DEV", "FWD") == "promotion" and CoachMarket.move_kind("FWD", "SA") == "promotion"
			and CoachMarket.move_kind("SA", "SC") == "promotion", "Development, line, assistant, senior: each a promotion")
	_check(CoachMarket.move_kind("FWD", "DEF") == "lateral" and CoachMarket.move_kind("SA", "SA") == "lateral",
			"Forwards to defence is lateral")
	_check(CoachMarket.move_kind("SC", "SA") == "demotion", "Senior coach to assistant is a demotion")
	var fwd := _coach("A", "club", "ADE", "FWD")
	fwd["rep"] = 60
	_check(not CoachMarket.would_take(fwd, "CAR", "DEF", Y), "An employed coach turns down a sideways move")
	var took := false
	for club in ["CAR", "COL", "ESS", "FRE", "GEE", "HAW", "MEL", "NTH"]:
		if CoachMarket.would_take(fwd, club, "SA", Y):
			took = true
	_check(took, "An employed line coach takes a senior assistant's job (at some clubs, not every offer appeals)")
	var sc := _coach("S", "club", "ADE", "SC")
	_check(not CoachMarket.would_take(sc, "CAR", "SA", Y), "An employed senior coach never steps down")
	var free_sc := _coach("F", "free", "", "")
	free_sc["former_sc"] = true
	_check(CoachMarket.would_take(free_sc, "CAR", "SA", Y), "An out-of-work former senior coach can be an assistant")
	var fresh := _coach("N", "club", "ADE", "DEV")
	fresh["since"] = Y
	_check(not CoachMarket.would_take(fresh, "CAR", "FWD", Y), "A coach one season into a job is not promoted away")


func _test_eligibility() -> void:
	var sa := _coach("SA1", "club", "ADE", "SA")
	_check(CoachMarket.sc_eligible(sa, Y), "A senior assistant of two seasons can be a senior coach")
	sa["since"] = Y
	_check(not CoachMarket.sc_eligible(sa, Y), "...not after one")
	var line := _coach("L1", "club", "ADE", "MID", [70, 70, 70])
	_check(not CoachMarket.sc_eligible(line, Y), "An ordinary line coach is not a senior coach candidate")
	line["rep"] = 80
	line["skills"] = {"teach": 80, "tactics": 84, "manage": 82}
	_check(CoachMarket.sc_eligible(line, Y), "...an exceptional one can be")
	var dev := _coach("D1", "club", "ADE", "DEV", [90, 90, 90])
	dev["rep"] = 90
	_check(not CoachMarket.would_take(dev, "CAR", "SC", Y), "A development coach does not jump to senior coach")


func _test_hiring() -> void:
	var a := _coach("H1", "free", "", "", [84, 84, 84])
	a["former_sc"] = true
	a["rep"] = 70
	var b := _coach("H2", "free", "", "", [60, 60, 60])
	b["former_sc"] = true
	b["rep"] = 30
	var s1 := CoachMarket.hire_score(a, "CAR", "SC", Y, SEED)
	_check(s1 == CoachMarket.hire_score(a, "CAR", "SC", Y, SEED), "The same vacancy scores the same every time (no reload rerolls)")
	var always := true
	for i in range(30):
		if CoachMarket.hire_score(b, "CAR", "SC", Y, i) > CoachMarket.hire_score(a, "CAR", "SC", Y, i):
			always = false
	_check(always, "Chance never beats a big gap in fit and reputation")
	var inside := _coach("I1", "club", "CAR", "SA")
	var outside := _coach("I2", "club", "COL", "SA")
	_check(CoachMarket.hire_score(inside, "CAR", "SC", Y, 0) - CoachMarket.hire_score(outside, "CAR", "SC", Y, 0)
			> CoachMarket.hire_score(inside, "COL", "SC", Y, 0) - CoachMarket.hire_score(outside, "COL", "SC", Y, 0) - 0.2,
			"A club's own settled senior assistant has an edge for its senior job")
	var sacked := _coach("K1", "free", "", "")
	sacked["former_sc"] = true
	sacked["sacked_by"] = {"CAR": Y}
	sacked["last_sacked"] = Y
	_check(not CoachMarket.would_take(sacked, "CAR", "SC", Y) and CoachMarket.would_take(sacked, "COL", "SC", Y),
			"A sacked coach does not go straight back to that club, but is hireable elsewhere")


func _league(my := "") -> Dictionary:
	var coaches := {}
	var clubs: Array = GameDB.active_clubs(Y)
	for club in clubs:
		for job in Coaches.JOBS:
			if job == "SC" and club == my:
				continue
			var cid := "%s_%s" % [club, job]
			coaches[cid] = _coach(cid, "club", club, job, [72, 72, 72],
					{"MID": "MID", "FWD": "FWD", "DEF": "DEF", "DEV": "DEV"}.get(job, ""))
	for i in range(50):
		var cid := "FREE_%d" % i
		coaches[cid] = _coach(cid, "free", "", "", [62 + i % 12, 62 + (i * 3) % 12, 62 + (i * 7) % 12],
				["MID", "FWD", "DEF", "DEV", ""][i % 5])
		if i % 10 == 0:
			coaches[cid]["former_sc"] = true
			coaches[cid]["rep"] = 65
	return coaches


func _results(met: bool) -> Dictionary:
	var r := {}
	for club in GameDB.active_clubs(Y):
		r[club] = {"met": met, "severe": false, "finals": false}
	return r


func _test_senior_coach_decisions() -> void:
	var coaches := _league()
	coaches["ADE_SC"]["fail_streak"] = 1
	coaches["BRL_SC"]["fail_streak"] = 1
	coaches["BRL_SC"]["protect_to"] = Y + 1
	coaches["CAR_SC"]["fail_streak"] = 1
	coaches["CAR_SC"]["sc_since"] = Y   # his first season
	var res := _results(false)
	var out := CoachMarket.offseason({"coaches": coaches, "archive": {}, "year": Y, "my_club": "",
			"clubs": GameDB.active_clubs(Y + 1), "results": res, "premier": "", "seed": SEED})
	_check(str(coaches["ADE_SC"]["status"]) != "club" and coaches["ADE_SC"]["sacked_by"].has("ADE"),
			"Two failed seasons: the senior coach is sacked")
	_check(str(coaches["BRL_SC"]["status"]) == "club", "A premiership coach is protected")
	_check(str(coaches["CAR_SC"]["status"]) == "club", "A first season does not count toward a sacking")
	# Everyone failing twice: every club acts for itself, no league-wide cap.
	var all := _league()
	for cid in all:
		if str(all[cid]["job"]) == "SC":
			all[cid]["fail_streak"] = 1
	var out2 := CoachMarket.offseason({"coaches": all, "archive": {}, "year": Y, "my_club": "",
			"clubs": GameDB.active_clubs(Y + 1), "results": res, "premier": "", "seed": SEED})
	_check(int(out2["log"]["sackings"]) > 5,
			"No sacking cap: every club with two failed seasons sacks its coach (%d)" % int(out2["log"]["sackings"]))
	# Renewal has no dice: a club keeps its coach unless a candidate who would
	# take the job beats him by more than CHANGE_COST; the same inputs decide alike.
	var c5 := _league()
	var inc: Dictionary = c5["COL_SC"]
	var own := CoachMarket.hire_score(inc, "COL", "SC", Y, SEED)
	var rival := CoachMarket.best_candidate_score(c5, "COL", "SC", Y, SEED, str(inc["cid"]))
	_check(CoachMarket.renews(c5, inc, Y, SEED) == (own + CoachMarket.CHANGE_COST > rival),
			"Renewal follows the hiring scores, not a roll")
	_check(CoachMarket.renews(c5, inc, Y, SEED) == CoachMarket.renews(c5, inc, Y, SEED + 99),
			"Renewal does not depend on the seed")
	# Contract expiry: a coach who met his goal is renewed.
	var c3 := _league()
	c3["COL_SC"]["contract_to"] = Y
	CoachMarket.offseason({"coaches": c3, "archive": {}, "year": Y, "my_club": "",
			"clubs": GameDB.active_clubs(Y + 1), "results": _results(true), "premier": "", "seed": SEED})
	_check(str(c3["COL_SC"]["status"]) == "club" and int(c3["COL_SC"]["contract_to"]) > Y,
			"A successful senior coach's expiring contract is renewed")
	# A premiership earns protection.
	var c4 := _league()
	CoachMarket.offseason({"coaches": c4, "archive": {}, "year": Y, "my_club": "",
			"clubs": GameDB.active_clubs(Y + 1), "results": _results(true), "premier": "GEE", "seed": SEED})
	_check(int(c4["GEE_SC"]["protect_to"]) == Y + CoachMarket.PREMIER_PROTECTION, "A flag protects the coach for three seasons")


func _test_retirement_and_pruning() -> void:
	var coaches := _league()
	# No term ends this year, so no extra job opens for the long-unemployed.
	for cid in coaches:
		if str(coaches[cid].get("status", "")) == "club":
			coaches[cid]["contract_to"] = Y + 5
	coaches["ESS_FWD"]["born"] = Y + 1 - 70
	coaches["FREE_3"]["unemployed_since"] = Y + 1 - CoachMarket.UNEMPLOYED_YEARS
	coaches["FREE_10"]["unemployed_since"] = Y + 1 - CoachMarket.UNEMPLOYED_YEARS   # a former senior coach
	coaches["FREE_10"]["rep"] = 0   # hiring is by merit now: never the best left for the job ESS_FWD opens
	var archive := {}
	CoachMarket.offseason({"coaches": coaches, "archive": archive, "year": Y, "my_club": "",
			"clubs": GameDB.active_clubs(Y + 1), "results": _results(true), "premier": "", "seed": SEED})
	_check(not coaches.has("ESS_FWD"), "A coach retires by 70")
	_check(not coaches.has("FREE_3") and not archive.has("FREE_3"), "An ordinary coach out of work for four seasons leaves")
	_check(not coaches.has("FREE_10") and archive.has("FREE_10"), "...a former senior coach is archived")
	var staff := Coaches.staff(coaches, "ESS")
	_check(staff.has("FWD"), "The retiree's job is filled")


func _test_vacancy_chain() -> void:
	var coaches := _league()
	# ADE's senior coach goes; the chain below it must end with every job filled.
	coaches["ADE_SC"]["fail_streak"] = 1
	var res := _results(true)
	res["ADE"] = {"met": false, "severe": false, "finals": false}
	var out := CoachMarket.offseason({"coaches": coaches, "archive": {}, "year": Y, "my_club": "",
			"clubs": GameDB.active_clubs(Y + 1), "results": res, "premier": "", "seed": SEED})
	var full := true
	for club in GameDB.active_clubs(Y + 1):
		if Coaches.staff(coaches, club).size() != 6:
			full = false
	_check(full, "After a chain of moves every club has all six jobs filled")
	var twice := false
	for cid in coaches:
		if (coaches[cid]["moves"] as Array).size() > 1:
			twice = true
	_check(not twice, "Nobody moves twice in one offseason")
	_check(int(out["log"]["sc_changes"]) >= 1, "The senior job was filled")


func _test_your_staff() -> void:
	var my := "GEE"
	var coaches := _league(my)
	# Make your assistants the obvious picks for promotions everywhere.
	for job in ["FWD", "DEF", "MID", "DEV"]:
		var c: Dictionary = coaches["%s_%s" % [my, job]]
		c["skills"] = {"teach": 90, "tactics": 90, "manage": 90}
		c["rep"] = 90
	for club in ["ADE", "BRL", "CAR", "COL", "ESS"]:
		coaches["%s_SA" % club]["status"] = "retired_test"
		coaches["%s_SA" % club]["club"] = ""
	var out := CoachMarket.offseason({"coaches": coaches, "archive": {}, "year": Y, "my_club": my,
			"clubs": GameDB.active_clubs(Y + 1), "results": _results(true), "premier": "", "seed": SEED})
	var lost := int(out["log"]["poached_from_you"])
	_check(lost >= 1 and lost <= CoachMarket.MAX_POACHED_FROM_YOU, "Your assistants can be poached, at most two a year (%d)" % lost)
	_check((out["vacancies"] as Array).size() >= lost, "Each poached job waits for you")
	var news := " ".join(PackedStringArray(out["news"]))
	_check(news.contains("Your "), "The news tells you who left")
	var mine := Coaches.staff(coaches, my)
	_check(not mine.has("SC"), "No senior coach record at your club: that is you")
	# Shortlist, appoint, auto-fill.
	var job := str((out["vacancies"] as Array)[0]["job"])
	var sl := CoachMarket.shortlist(coaches, my, job, Y, SEED)
	_check(sl.size() >= 3 and sl.size() <= 5, "A shortlist of three to five (%d)" % sl.size())
	CoachMarket.appoint_mine(coaches, str(sl[0]), my, job, Y, SEED)
	_check(Coaches.staff(coaches, my).get(job, "") == str(sl[0]), "Appointing fills the job")
	var rj := str(Coaches.staff(coaches, my).keys()[0])
	var rcid := str(Coaches.staff(coaches, my)[rj])
	var left := CoachMarket.release(coaches, rcid, Y)
	_check(left == rj and not Coaches.staff(coaches, my).has(rj), "Releasing an assistant opens his job")
	_check(not CoachMarket.shortlist(coaches, my, rj, Y, SEED).has(rcid),
			"...and he is not offered back to you")
	CoachMarket.auto_fill(coaches, my, rj, Y, SEED)
	_check(Coaches.staff(coaches, my).has(rj), "Auto-fill fills it")


func _test_generation_and_expansion() -> void:
	var coaches := _league()
	for cid in coaches.keys():
		if str(cid).begins_with("FREE_"):
			coaches.erase(cid)
	var out := CoachMarket.offseason({"coaches": coaches, "archive": {}, "year": Y, "my_club": "",
			"clubs": GameDB.active_clubs(Y + 1), "results": _results(true), "premier": "", "seed": SEED})
	var pool := 0
	var gen_ok := true
	for cid in coaches:
		var c: Dictionary = coaches[cid]
		if str(c["status"]) == "free" or str(c["status"]) == "away":
			pool += 1
		if str(c["origin"]) == "generated" and str(cid).begins_with("C_G"):
			var a := CoachMarket.age(c, Y + 1)
			if a < 32 or a > 48 or int(c["skills"]["teach"]) > 74 + 2:
				gen_ok = false
	_check(pool >= CoachMarket.POOL_MIN, "An empty market is topped up (%d available)" % pool)
	_check(gen_ok and int(out["log"]["generated"]) > 0, "Generated coaches are 32-48 with modest skills")
	# Tasmania enters in 2028: all six jobs filled at the 2027 offseason.
	var c2 := _league()
	CoachMarket.offseason({"coaches": c2, "archive": {}, "year": 2027, "my_club": "",
			"clubs": GameDB.active_clubs(2028), "results": _results(true), "premier": "", "seed": SEED})
	_check(Coaches.staff(c2, "TAS").size() == 6, "An expansion club starts fully staffed")


func _test_long_run() -> void:
	var coaches: Dictionary = Coaches.seed("GEE")
	var archive := {}
	var rng := RandomNumberGenerator.new()
	rng.seed = 5
	var sc_changes := 0
	var internal := 0
	var unfilled := 0
	for y in range(Y, Y + 30):
		var res := {}
		for club in GameDB.active_clubs(y):
			var met := rng.randf() < 0.62
			res[club] = {"met": met, "severe": false, "finals": false}
		var out := CoachMarket.offseason({"coaches": coaches, "archive": archive, "year": y, "my_club": "GEE",
				"clubs": GameDB.active_clubs(y + 1), "results": res, "premier": "", "seed": SEED})
		sc_changes += int(out["log"]["sc_changes"])
		internal += int(out["log"]["internal_sc"])
		var open: Array = []
		for v in out["vacancies"]:
			open.append(str(v["job"]))
		while not open.is_empty():
			var left := CoachMarket.auto_fill(coaches, "GEE", str(open.pop_front()), y, SEED)
			if left != "":
				open.append(left)
		for club in GameDB.active_clubs(y + 1):
			if Coaches.staff(coaches, club).size() != (5 if club == "GEE" else 6):
				unfilled += 1
	var elite := 0
	var n := 0
	for cid in coaches:
		for k in ["teach", "tactics", "manage"]:
			n += 1
			if int(coaches[cid]["skills"][k]) >= 86:
				elite += 1
	_check(unfilled == 0, "Thirty seasons: no club ever short of a coach")
	_check(sc_changes >= 30 and sc_changes <= 150, "Senior coach changes are steady, not constant (%d in 30)" % sc_changes)
	print("coach_market: senior coach changes in 30 seasons = %d" % sc_changes)
	_check(internal > 0 and internal < sc_changes, "Some senior appointments are internal, not all (%d of %d)" % [internal, sc_changes])
	_check(coaches.size() < 260, "The coaching records do not balloon (%d)" % coaches.size())
	_check(float(elite) / n < 0.08, "Elite stays rare (%.1f%%)" % (100.0 * elite / n))


## The home-and-away rounds skipped (nothing under test is decided in them),
## the finals played through to the season's real close, where the coaching
## world moves (GameState._coaching_offseason).
func _play_finals() -> void:
	GameState.season.round_index = GameState.season.fixture.size()
	GameState.ensure_finals()
	var guard := 0
	while not GameState.season.is_season_over() and guard < 10:
		GameState.advance()
		guard += 1


## The season marked over by hand, no match played: what the contract calls
## read (GameState.can_release_staff). The real close is _test_game_flow's.
func _mark_season_over() -> void:
	GameState.season.round_index = GameState.season.fixture.size()
	GameState.ensure_finals()
	GameState.season.finals["done"] = true


func _test_game_flow() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	_play_finals()
	_check(GameState.season.is_season_over(), "The season plays out")
	var ran := true
	for cid in GameState.coaches:
		if not GameState.coaches[cid].has("rep"):
			ran = false
	var staffed := true
	for club in GameDB.active_clubs(GameState.season_year + 1):
		if club != "GEE" and Coaches.staff(GameState.coaches, club).size() != 6:
			staffed = false
	_check(ran and staffed, "The coaching world moved at the season's close and every club is staffed")
	_check(GameState.can_release_staff(), "Staff can be released in the offseason")
	var staff := GameState.club_staff("GEE")
	var fwd: Dictionary = staff.get("FWD", {})
	if not fwd.is_empty():
		GameState.release_staff(str(fwd["cid"]))
	_check(GameState._vacancy_open("FWD"), "Releasing your forwards coach opens the job")
	_check(GameState.save_career() and GameState.load_career(), "The career saves and loads after the offseason")
	_check(GameState._vacancy_open("FWD"), "The open job survives a save")
	var records_ok := true
	for cid in GameState.coaches:
		var c: Dictionary = GameState.coaches[cid]
		if c.has("attr") or c.has("id") or str(c.get("cid", "")) != str(cid):
			records_ok = false
	_check(records_ok, "Coach records stay coach records after a reload")
	GameState._fill_open_staff()
	_check(GameState.staff_vacancies.is_empty() and GameState.club_staff("GEE").size() == 5,
			"A new season never starts with one of your jobs empty")


## Assistants have terms: staggered so about a third end each season, two
## or three seasons on appointment, and an AI club keeps a well-regarded one
## and most of the rest. Yours wait for you.
func _test_assistant_contracts() -> void:
	var coaches: Dictionary = Coaches.seed("GEE")
	var ends := {}
	var assistants := 0
	for cid in coaches:
		var c: Dictionary = coaches[cid]
		CoachMarket.ensure_fields(c, Y)
		if str(c.get("status", "")) == "club" and str(c.get("job", "")) != "SC":
			assistants += 1
			var t := int(c.get("contract_to", -1)) - Y
			ends[t] = int(ends.get(t, 0)) + 1
	var share := float(ends.get(0, 0)) / maxf(1, assistants)
	_check(ends.keys().all(func(k): return int(k) >= 0 and int(k) <= 2) and share > 0.2 and share < 0.5,
			"Assistants' terms are staggered: about a third end this season (%s)" % str(ends))
	var mine_before := {}
	for cid in coaches:
		var c: Dictionary = coaches[cid]
		if str(c.get("club", "")) == "GEE" and str(c.get("job", "")) != "SC":
			mine_before[cid] = int(c["contract_to"])
	var out := CoachMarket.offseason({"coaches": coaches, "archive": {}, "year": Y, "my_club": "GEE",
			"clubs": GameDB.active_clubs(Y + 1), "results": _results(true), "premier": "", "seed": SEED})
	var lapsed := int(out["log"].get("assistant_expired", 0))
	_check(lapsed > 0 and lapsed < int(ends.get(0, 0)), "Some AI assistants are let go at the end of a term, most are kept (%d)" % lapsed)
	var untouched := true
	for cid in mine_before:
		var c: Dictionary = coaches[cid]
		if str(c.get("club", "")) == "GEE" and int(c.get("contract_to", -9)) != int(mine_before[cid]):
			untouched = false
	_check(untouched, "Your assistants' terms wait for you")
	var fresh := _coach("NEWA", "free", "", "", [70, 70, 70], "MID")
	coaches["NEWA"] = fresh
	CoachMarket._appoint(fresh, "CAR", "MID", Y, SEED)
	var term := int(fresh.get("contract_to", 0)) - Y
	_check(term == 2 or term == 3, "An appointed assistant signs for two or three seasons (%d)" % term)
	var old := _coach("OLDA", "club", "CAR", "DEF")
	old["born"] = Y - 63
	_check(int(CoachMarket.assistant_stance(old, Y)["years"]) == 1, "An assistant near retirement signs for one more season")


## In the off-season your expiring assistants show; re-signing keeps him on
## his terms, and one you leave undecided stays when the next season starts.
func _test_your_expiring_staff() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	_check(GameState.expiring_staff().is_empty(), "No contract talk during the season")
	_mark_season_over()
	var staff := GameState.club_staff("GEE")
	var jobs := staff.keys().filter(func(j): return str(j) != "SC")
	var a: Dictionary = staff[jobs[0]]
	var b: Dictionary = staff[jobs[1]]
	a["contract_to"] = GameState.season_year
	b["contract_to"] = GameState.season_year
	var exp := GameState.expiring_staff()
	_check(exp.has(a) and exp.has(b), "Your assistants at the end of their term are listed")
	GameState.resign_staff(str(a["cid"]))
	_check(int(a["contract_to"]) > GameState.season_year and not GameState.expiring_staff().has(a),
			"Re-signing keeps him for at least another season")
	var y := GameState.season_year
	GameState._settle_staff_contracts()
	_check(int(b["contract_to"]) > y and str(b.get("club", "")) == "GEE", "An undecided assistant stays on his terms")
	GameState.reset()


## Rival approaches for your coaches (director, 2026-10-07): a coach you kept
## is never poached, one you let go takes the job he was offered when it
## opens, and one whose job never opens stays with you.
func _test_approaches_market() -> void:
	var my := "GEE"
	var coaches := _league(my)
	for job in ["FWD", "DEF", "MID", "DEV"]:
		var c: Dictionary = coaches["%s_%s" % [my, job]]
		c["skills"] = {"teach": 90, "tactics": 90, "manage": 90}
		c["rep"] = 90
	for club in ["ADE", "BRL", "CAR", "COL", "ESS"]:
		coaches["%s_SA" % club]["status"] = "retired_test"
		coaches["%s_SA" % club]["club"] = ""
	var kept := {}
	for job in ["SA", "DEF", "MID", "DEV"]:
		kept["%s_%s" % [my, job]] = true
	var out := CoachMarket.offseason({"coaches": coaches, "archive": {}, "year": Y, "my_club": my,
			"clubs": GameDB.active_clubs(Y + 1), "results": _results(true), "premier": "", "seed": SEED,
			"protected": kept, "promised": {"GEE_FWD": ["CAR", "SA"]}})
	var fwd: Dictionary = coaches["GEE_FWD"]
	_check(str(fwd["club"]) == "CAR" and str(fwd["job"]) == "SA",
			"The coach you let go takes the job he was offered (%s %s)" % [fwd["club"], fwd["job"]])
	var stayed := true
	for cid in kept:
		if str(coaches[cid]["club"]) != my:
			stayed = false
	_check(stayed, "Every coach you kept is still yours")
	_check(int(out["log"]["poached_from_you"]) == 1, "Only the one you let go left (%d)" % int(out["log"]["poached_from_you"]))
	# A job that never opens: he stays, and the news says so.
	coaches = _league(my)
	out = CoachMarket.offseason({"coaches": coaches, "archive": {}, "year": Y, "my_club": my,
			"clubs": GameDB.active_clubs(Y + 1), "results": _results(true), "premier": "", "seed": SEED,
			"protected": {}, "promised": {"GEE_DEF": ["BRL", "SC"]}})
	_check(str(coaches["GEE_DEF"]["club"]) == my, "A move to a job that never opens falls through")
	_check(" ".join(PackedStringArray(out["news"])).contains("fell through"), "...and the news says so")
	# The chance he stays: an opportunity beats a plea; a senior job is hardest to turn down.
	var c: Dictionary = coaches["GEE_MID"]
	_check(CoachMarket.stay_chance(c, "promote", "FWD", Y) > CoachMarket.stay_chance(c, "stay", "FWD", Y)
			and CoachMarket.stay_chance(c, "promote", "SC", Y) < CoachMarket.stay_chance(c, "promote", "FWD", Y),
			"Senior assistant keeps him more often than asking; a senior coach's job is the hardest to keep him from")
	_check(CoachMarket.stays(c, "promote", "FWD", Y, 1) == CoachMarket.stays(c, "promote", "FWD", Y, 999)
			and CoachMarket.stays(c, "promote", "FWD", Y, 1) == (CoachMarket.stay_chance(c, "promote", "FWD", Y) >= CoachMarket.STAY_BAR),
			"Whether he stays follows the offer and his years with you, never a roll")
	_check(CoachMarket.stay_chance(c, "stay", "SA", Y, {"met": true, "finals": true, "flag": true})
			> CoachMarket.stay_chance(c, "stay", "SA", Y, {"met": false}),
			"A winning club keeps its coach more readily than a losing one")
	# Contract terms follow performance: a goal met and a big reputation earn longer.
	var plain := c.duplicate(true)
	plain["rep"] = 50
	var star := c.duplicate(true)
	star["rep"] = CoachMarket.REP_LONG_TERM
	_check(CoachMarket.term_years(plain, "SC") == 2 and CoachMarket.term_years(plain, "SC", true) == 3
			and CoachMarket.term_years(star, "SC", true) == 4 and CoachMarket.term_years(star, "MID", true) == 3,
			"Coach contract terms follow performance (goal met, reputation)")
	# A step up appeals by his record, not a roll.
	var low := plain.duplicate(true)
	low["rep"] = CoachMarket.keen_bar("SA") - 1
	var keen := plain.duplicate(true)
	keen["rep"] = CoachMarket.keen_bar("SA")
	_check(CoachMarket.keen_bar("SA") > CoachMarket.keen_bar("MID") and int(low["rep"]) < int(keen["rep"]),
			"A bigger step up asks a bigger reputation")


func _test_approaches_flow() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	# The home-and-away rounds are skipped (they decide nothing here) and the
	# first finals week is played: the week's close is where rivals'
	# approaches are looked for once the home-and-away season is done.
	GameState.season.round_index = GameState.season.fixture.size()
	GameState.ensure_finals()
	GameState.advance()
	var guard := 0
	_check(GameState.coach_approach_year == GameState.season_year,
			"Rivals' approaches are looked for once the home-and-away season is done")
	var staff := GameState.club_staff("GEE")
	var mid: Dictionary = staff.get("MID", {})
	_check(not mid.is_empty(), "You have a midfield coach to be approached")
	if mid.is_empty():
		return
	GameState.coach_approaches = [{"cid": str(mid["cid"]), "from_job": "MID", "club": "ADE", "job": "SA",
			"choice": "", "kept": false, "text": ""}]
	_check(GameState.coach_approaches_open() == 1, "One approach waits for your answer")
	_check(GameState.approach_promote_block(0) != "" or not staff.has("SA"),
			"Senior assistant can't be offered while someone holds it")
	var said := GameState.answer_approach(0, "go")
	_check(said.contains("Adelaide") and GameState.coach_approaches_open() == 0, "Letting him go is answered in words (%s)" % said)
	_check(GameState.answer_approach(0, "stay") == said, "An answer stands")
	_check(GameState.save_career() and GameState.load_career()
			and str(GameState.coach_approaches[0]["choice"]) == "go", "Approaches survive a save")
	_check(not GameState._protected_coaches().has(str(mid["cid"])), "The one you let go is not protected")
	while not GameState.season.is_season_over() and guard < 80:
		GameState.advance()
		guard += 1
	_check(GameState.coach_approaches.is_empty(), "The off-season settles the approaches")
	var moved: Dictionary = GameState.coaches.get(str(mid["cid"]), {})
	var news := ""
	for n in GameState.news:
		news += str(n) + " "
	_check((str(moved.get("club", "")) == "ADE" and str(moved.get("job", "")) == "SA") or news.contains("fell through"),
			"He joins Adelaide, or the move falls through and the news says so")


## Row 117 (T5.Q16): a succession promise with a timeframe, kept or broken,
## and a broken one costs trust.
func _test_staff_promises() -> void:
	var coaches := _league("GEE")
	var c: Dictionary = coaches["GEE_MID"]
	var stay := CoachMarket.stay_chance(c, "stay", "SA", Y)
	var promise := CoachMarket.stay_chance(c, "promise", "SA", Y)
	var promote := CoachMarket.stay_chance(c, "promote", "SA", Y)
	_check(stay < promise and promise < promote, "A promise weighs between a plea and the job now (%.2f %.2f %.2f)" % [stay, promise, promote])
	CoachMarket.make_promise(c, Y)
	_check(CoachMarket.holds_promise(c, "GEE") and int(c["promise"]["by"]) == Y + CoachMarket.PROMISE_SEASONS,
			"The promise names the job and the season it is due")
	# Kept: he gets the job and the promise is done, his trust untouched.
	var kept := c.duplicate(true)
	CoachMarket._appoint(kept, "GEE", "SA", Y, SEED)
	_check(not kept.has("promise") and CoachMarket.broken_by(kept, "GEE") == 0, "Giving him the job keeps the promise")
	# Broken: someone else gets it.
	var lines := CoachMarket.settle_promises(coaches, "GEE", "SA", "GEE_FWD")
	_check(lines.size() == 1 and str(lines[0]).contains("promised"), "Giving the job to another breaks it, in words (%s)" % [lines])
	_check(not c.has("promise") and CoachMarket.broken_by(c, "GEE") == 1, "A broken promise is remembered")
	var after := CoachMarket.stay_chance(c, "promise", "SA", Y)
	_check(is_equal_approx(promise - after, CoachMarket.BROKEN_TRUST), "...and every later offer from you weighs less (%.2f -> %.2f)" % [promise, after])
	# Out of time: the market breaks an AI club's promise when it falls due.
	coaches = _league("GEE")
	var ade: Dictionary = coaches["ADE_FWD"]
	CoachMarket.make_promise(ade, Y - 1)
	CoachMarket.offseason({"coaches": coaches, "archive": {}, "year": Y, "my_club": "GEE",
			"clubs": GameDB.active_clubs(Y + 1), "results": _results(true), "premier": "", "seed": SEED})
	_check(str(ade["job"]) == "SA" or CoachMarket.broken_by(ade, "ADE") == 1,
			"A promise that falls due is kept or broken, never left hanging (%s, broken %d)" % [ade["job"], CoachMarket.broken_by(ade, "ADE")])
	# One head assistant per club, after a whole off-season of moves.
	var per := {}
	for cid in coaches:
		var k: Dictionary = coaches[cid]
		if str(k.get("status", "")) == "club" and str(k["job"]) == "SA":
			per[str(k["club"])] = int(per.get(str(k["club"]), 0)) + 1
	var bad := per.values().filter(func(n): return int(n) != 1)
	_check(bad.is_empty() and per.size() == GameDB.active_clubs(Y + 1).size(), "Every club has exactly one senior assistant")


## AI clubs follow the same rules: their coach is approached, they answer with
## a promise, he weighs it as yours would, and the promise is kept first.
func _test_ai_clubs_counter() -> void:
	var c := _coach("X", "club", "ADE", "FWD")
	var good := {"met": true, "finals": true}
	var held := CoachMarket.ai_counter(c, "FWD", Y, good)
	_check(held == CoachMarket.stays(c, "promise", "FWD", Y, 0, good), "An AI club's counter is weighed by your rule")
	_check(not held or CoachMarket.holds_promise(c, "ADE"), "...and it is a promise, with a timeframe")
	var sa := _coach("Y", "club", "ADE", "SA")
	CoachMarket.ai_counter(sa, "SC", Y, good)
	_check(not sa.has("promise"), "Its senior assistant is asked to stay, not promised his own job")
	# Approached and held: a strong coach at an AI club turns a rival down.
	var coaches := _league("GEE")
	for k in ["ADE_FWD"]:
		coaches[k]["rep"] = 90
		coaches[k]["skills"] = {"teach": 92, "tactics": 92, "manage": 92}
		coaches[k]["since"] = Y - 8
	var res := _results(true)
	for club in res:
		res[club]["finals"] = true
	var out := CoachMarket.offseason({"coaches": coaches, "archive": {}, "year": Y, "my_club": "GEE",
			"clubs": GameDB.active_clubs(Y + 1), "results": res, "premier": "ADE", "seed": SEED})
	_check(int(out["log"]["held"]) >= 0 and out["log"].has("broken"), "The market counts approaches held and promises broken")
	# A promised coach gets his club's senior assistant job when it opens.
	coaches = _league("GEE")
	CoachMarket.make_promise(coaches["ADE_DEV"], Y)
	coaches["ADE_SA"]["status"] = "retired_test"
	coaches["ADE_SA"]["club"] = ""
	CoachMarket.offseason({"coaches": coaches, "archive": {}, "year": Y, "my_club": "GEE",
			"clubs": GameDB.active_clubs(Y + 1), "results": _results(true), "premier": "", "seed": SEED})
	_check(str(coaches["ADE_DEV"]["club"]) == "ADE" and str(coaches["ADE_DEV"]["job"]) == "SA"
			and not coaches["ADE_DEV"].has("promise"), "An AI club keeps its promise when the job opens")


## Your answer: approach, promise (counter), the promise kept or broken,
## departure, and the save.
func _test_promise_flow() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var staff := GameState.club_staff("GEE")
	var mid: Dictionary = staff.get("MID", {})
	var fwd: Dictionary = staff.get("FWD", {})
	_check(not mid.is_empty() and not fwd.is_empty() and staff.has("SA"), "You have line coaches and a senior assistant")
	if mid.is_empty() or fwd.is_empty():
		return
	GameState.coach_approaches = [
		{"cid": str(mid["cid"]), "from_job": "MID", "club": "ADE", "job": "MID", "choice": "", "kept": false, "text": ""},
		{"cid": str(fwd["cid"]), "from_job": "FWD", "club": "CAR", "job": "SA", "choice": "", "kept": false, "text": ""}]
	_check(GameState.approach_promise_block(0) == "", "You can promise a line coach the senior assistant's job")
	var w := GameState.approach_weight(0, "promise")
	_check(w > GameState.approach_weight(0, "stay") and w < GameState.approach_weight(0, "promote"),
			"The card's weights rank promise between the plea and the job")
	mid["since"] = GameState.season_year - 10   # long-serving: he takes your word
	w = GameState.approach_weight(0, "promise")
	var said := GameState.answer_approach(0, "promise")
	_check((w >= 50) == said.contains("promised"), "He stays on a promise exactly when it weighs 50 or more (%d: %s)" % [w, said])
	_check(not said.contains("promised") or CoachMarket.holds_promise(mid, "GEE"), "Kept on a promise, he holds it")
	_check(GameState.approach_promise_block(0) != "" or not said.contains("promised"), "...and can't be promised twice")
	var gone := GameState.answer_approach(1, "go")
	_check(gone.contains("Carlton") and not GameState._protected_coaches().has(str(fwd["cid"])), "Letting one go leaves him free to depart")
	_check(GameState.save_career() and GameState.load_career(), "The career saves and loads")
	var back: Dictionary = GameState.coaches.get(str(mid["cid"]), {})
	if not said.contains("promised"):
		return
	_check(CoachMarket.holds_promise(back, "GEE"), "The promise survives a save")
	# Broken: the senior assistant's job goes to someone else.
	var other := ""
	for cid in GameState.coaches:
		var k: Dictionary = GameState.coaches[cid]
		if str(k.get("status", "")) == "free":
			other = str(cid)
			break
	GameState.staff_vacancies.append({"job": "SA", "reason": "test"})
	GameState.appoint_staff("SA", other)
	_check(CoachMarket.broken_by(back, "GEE") == 1 and not CoachMarket.holds_promise(back, "GEE"),
			"Giving his promised job to another breaks the promise")
	var news := ""
	for n in GameState.news:
		news += str(n) + " "
	_check(news.contains("weigh your word less"), "...and the news says what it cost")
	_check(GameState.save_career() and GameState.load_career()
			and CoachMarket.broken_by(GameState.coaches[str(mid["cid"])], "GEE") == 1, "A broken promise survives a save")
