extends RefCounted
## How often the reads the coach is shown on other clubs turn out true (row
## T1.R26 L3). Measurement only: it reads a career's off-season and changes
## nothing in it, so a career with it replays exactly as one without.
##
## tools/balance/dynasty.gd calls `record` as each off-season opens (the
## market is on the table, your club has not acted). Two reads:
##
##   pot   The POT range your recruiters give another club's player or a free
##         agent (GameState.pot_view, DraftScouting.pot_read): for every club
##         as the reader, at every Recruiting budget level, whether his true
##         potential sits inside the range shown, and how far outside.
##   fa    The free-agency gate's "the best other" figure (what the best
##         rival offer on the table is worth to him): whether an offer that
##         beats it still leads once rivals have answered, and how far the
##         rivals go.
##
## tools/balance/rival_reads_report.py adds the seasons up.

## Senior games played, by bucket floor.
const GAMES := [0, 50, 100, 150]


func record(gs, user: String) -> Dictionary:
	return {"pot": _pot(gs), "fa": _fa(gs, user)}


# ---------------------------------------------------------------------------
# The POT range on another club's player
# ---------------------------------------------------------------------------
## Counts keyed "level|games bucket|g or f (growth left, or finished)|l or m
## (on a list, or on the market)": [reads, misses, points missed by, worst
## miss, half-width total].
func _pot(gs) -> Dictionary:
	var out := {}
	var clubs: Array = gs.season.lists.keys()
	var levels: Array = ClubBudget.SCOUT_UNCERTAINTY
	for reader in clubs:
		for code in clubs:
			if code == reader:
				continue
			for p in gs.season.lists[code]:
				_pot_one(out, p, str(reader), int(gs.career_seed), levels, "l")
		for p in gs.free_agents:
			_pot_one(out, p, str(reader), int(gs.career_seed), levels, "m")
	return out


func _pot_one(out: Dictionary, p: Dictionary, reader: String, seed: int, levels: Array, where: String) -> void:
	var ov := int(p.get("overall", 50))
	var pot := maxi(ov, int(p.get("potential", ov)))
	var games := float((p.get("career", {}) as Dictionary).get("games", p.get("gm", 0.0)))
	var bucket := 0
	for g in GAMES:
		if games >= float(g):
			bucket = int(g)
	for li in range(levels.size()):
		var r := DraftScouting.pot_read(p, reader, seed, float(levels[li]))
		var rg: Array = r["range"]
		var miss := 0
		if pot < int(rg[0]):
			miss = int(rg[0]) - pot
		elif pot > int(rg[1]):
			miss = pot - int(rg[1])
		var key := "%d|%d|%s|%s" % [li, bucket, "g" if pot > ov else "f", where]
		var c: Array = out.get(key, [0, 0, 0, 0, 0])
		c[0] += 1
		c[1] += int(miss > 0)
		c[2] += miss
		c[3] = maxi(int(c[3]), miss)
		c[4] += int(rg[1]) - int(rg[0])
		out[key] = c


# ---------------------------------------------------------------------------
# Free agency: the best other offer, before and after rivals answer
# ---------------------------------------------------------------------------
## One row per free agent with a rival offer on the table that your club
## could bid for. Worths are dollars a season to him (Contracts.worth_to_him).
##   shown     the best rival offer now: the gate's "the best other"
##   open      the cheapest offer of yours, over the term he wants, that he
##             would take and that leads the table; open_w its worth
##   answered  how many rivals improved or matched once it was made
##   after     the best rival offer after they answer
##   held      your opening offer still leads after they answer
##   final     the cheapest second offer that leads again; final_w its worth
##   after2    the best rival offer after they answer that one
##   won       he chooses you after the second offer
##   ceiling   the most any rival on the table could make its offer worth
##             (its limit a season, over the term he wants)
func _fa(gs, user: String) -> Array:
	var rows := []
	for p in gs.free_agents:
		var id := str(p["id"])
		if bool(gs.free_agent_terms(id).get("refuse", false)) or str(p.get("released_by", "")) == user:
			continue
		var rivals := []
		for o in p.get("offers", []):
			if str(o["club"]) != user and not bool(o.get("withdrawn", false)):
				rivals.append((o as Dictionary).duplicate())
		if rivals.is_empty():
			continue
		var wanted := int(Contracts.wants(p)["years"])
		var mine := {"club": user, "salary": 0, "years": wanted, "role": gs.fa_role(p, user),
				"finish_t": gs._finish_t(user), "amb": gs.culture_effect(user, "free_agent_score")}
		var ceiling := 0
		var limits := {}
		for o in rivals:
			var most: int = gs.offer_max(p, o)
			limits[str(o["club"])] = most
			# Its dearest answer: it raises in the market's steps from its own
			# offer and never past its limit (Contracts.rival_response).
			var top: Dictionary = o.duplicate()
			var steps := maxi(0, most - int(o["salary"])) / Contracts.SALARY_STEP
			top["salary"] = int(o["salary"]) + steps * Contracts.SALARY_STEP
			top["years"] = maxi(int(o["years"]), wanted)
			ceiling = maxi(ceiling, Contracts.worth_to_him(p, top))
		var row := {"id": id, "ovr": int(p.get("overall", 0)), "rivals": rivals.size(),
				"shown": _best_worth(p, rivals), "ceiling": ceiling}
		var floor_salary := Contracts.lowest(p, wanted)
		var open := _cheapest_lead(p, mine, rivals, floor_salary)
		if open < 0:
			continue
		mine["salary"] = open
		row["open"] = open
		row["open_w"] = Contracts.worth_to_him(p, mine)
		row["answered"] = _answer(p, mine, rivals, limits)
		row["after"] = _best_worth(p, rivals)
		row["held"] = _leads(p, mine, rivals)
		if not bool(row["held"]):
			var final := _cheapest_lead(p, mine, rivals, open)
			if final < 0:
				row["won"] = false
				rows.append(row)
				continue
			mine["salary"] = final
			row["final"] = final
			row["final_w"] = Contracts.worth_to_him(p, mine)
			_answer(p, mine, rivals, limits)
			row["after2"] = _best_worth(p, rivals)
		row["won"] = _leads(p, mine, rivals)
		rows.append(row)
	return rows


func _best_worth(p: Dictionary, rivals: Array) -> int:
	var best := 0
	for o in rivals:
		if not bool(o.get("withdrawn", false)):
			best = maxi(best, Contracts.worth_to_him(p, o))
	return best


func _leads(p: Dictionary, mine: Dictionary, rivals: Array) -> bool:
	for o in rivals:
		if not bool(o.get("withdrawn", false)) and not Contracts.prefers(p, mine, o):
			return false
	return true


## The cheapest salary from `from` up, in the market's steps, at which your
## offer leads every rival's; -1 when forty steps do not get there.
func _cheapest_lead(p: Dictionary, mine: Dictionary, rivals: Array, from: int) -> int:
	var trial: Dictionary = mine.duplicate()
	for i in range(41):
		trial["salary"] = from + i * Contracts.SALARY_STEP
		if _leads(p, trial, rivals):
			return int(trial["salary"])
	return -1


## The rivals answer your leading offer once, as GameState._rival_round has
## them: each makes the cheapest offer inside its limit that he would prefer,
## or withdraws when your salary is past that limit. Returns how many moved.
func _answer(p: Dictionary, mine: Dictionary, rivals: Array, limits: Dictionary) -> int:
	var moves := []
	for o in rivals:
		if not bool(o.get("withdrawn", false)):
			moves.append([o, Contracts.rival_response(p, o, mine, int(limits[str(o["club"])]))])
	var moved := 0
	for m in moves:
		var o: Dictionary = m[0]
		var r: Dictionary = m[1]
		match str(r["action"]):
			"improve", "match":
				o["salary"] = int(r["salary"])
				o["years"] = int(r["years"])
				moved += 1
			"withdraw":
				o["withdrawn"] = true
	return moved
