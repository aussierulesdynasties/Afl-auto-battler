class_name ClubMoves
extends RefCounted
## The coach changes clubs (coach arcs phase 2; catalogue arcs 2, 3, 7 and
## 11, docs/research/COACH_ARC_CATALOGUE_2026-11-03.md).
##
## Two steps, so the season he leaves is played out at the club he leaves:
##   season_close  (after the season's close and the coaching offseason): a
##                 sacked coach is offered a job at a struggling club; a coach
##                 who took a rival's offer (arc "poached") is going there.
##                 Every running arc ends at the old club, and the move waits
##                 in coach_arcs.move.
##   apply_move    (at the rollover, before the new lists are built): he is the
##                 new club's coach. That club's AI senior coach takes the job
##                 he left (or, when his assistant was after it, the assistant
##                 does and the AI coach is let go). His career record (seasons,
##                 games, flags, every club, every player he coached) carries on.
## `gs` is GameState; its state lives in gs.coach_arcs (CoachArcs).

## How each arc may end when the coach leaves; any other running arc stays
## behind at the old club ("moved_on").
const MOVE_ENDINGS := {"hot_seat": ["sacked"], "way_back": ["sacked_again"], "poached": ["left"],
		"assistant": ["took_job", "left_friend"]}
## A sacked coach is offered a job at one of the clubs that finished this low.
const SACKED_FROM_BOTTOM := 6


# ---------------------------------------------------------------------------
# The season's close: is he leaving?
# ---------------------------------------------------------------------------
static func season_close(gs) -> void:
	if not ClubArcs.on(gs) or gs.season == null:
		return
	var st := ClubArcs._st(gs)
	var year := int(gs.season_year)
	var sacked := bool(gs.board.get("sacked", false))
	var poach: Dictionary = st["active"].get("poached", {})
	var to := ""
	var why := ""
	if not poach.is_empty() and (poach.get("flags", {}) as Dictionary).has("taking"):
		to = str(poach.get("mem", {}).get("suitor_code", ""))
		why = "poached"
	if to == "" and sacked:
		to = _job_after_sack(gs, st)
		why = "sacked"
	_assistant_leaves(gs, st)
	if to == "":
		return
	# The assistant who may inherit the job (arc "assistant"), named now while
	# the arc still remembers him.
	var heir_id := str((st["active"].get("assistant", {}) as Dictionary).get("mem", {}).get("assistant_id", ""))
	_close_for_move(gs, st)
	st["move"] = {"to": to, "why": why, "from": str(gs.my_club), "year": year, "heir": heir_id}
	if sacked:
		CoachArcs.log_line(st, year, "Season end", "move", "Sacked by %s. %s offer him their senior job." % [
				GameDB.club_name(gs.my_club), GameDB.club_name(to)])
		st["coach"]["sackings"] = int(st["coach"]["sackings"]) + 1
		# The career goes on: the Hub's sacked card is not shown.
		gs.board["sacked"] = false
		gs.board["verdict"] = "Sacked. %s have offered you their senior job." % GameDB.club_name(to)
		gs.add_news(ClubArcs.NEWS_KIND, "Sacked by %s, you have taken the senior job at %s for %d." % [
				GameDB.club_name(gs.my_club), GameDB.club_name(to), year + 1])
	else:
		gs.add_news(ClubArcs.NEWS_KIND, "You leave %s for %s at season's end." % [GameDB.club_name(gs.my_club), GameDB.club_name(to)])


## Every running arc ends at the club he is leaving: by its own rule when that
## rule is about him leaving (MOVE_ENDINGS), otherwise it stays behind.
static func _close_for_move(gs, st: Dictionary) -> void:
	var defs := CoachArcs.all()
	for id in (st["active"] as Dictionary).keys():
		var def := CoachArcs.by_id(defs, str(id))
		var rec: Dictionary = st["active"][id]
		var own := CoachArcs.closing(def, rec, ClubArcs.close_facts(gs, rec), int(gs.season_year))
		# A reunion is about a game already played: it keeps its own ending.
		if (MOVE_ENDINGS.get(str(id), []) as Array).has(own) or str(id) == "reunion":
			ClubArcs._end(gs, st, def, rec, own, "Season end")
			continue
		# An arc with its own line for him leaving says it.
		if (def.get("endings", {}) as Dictionary).has("moved_on"):
			ClubArcs._end(gs, st, def, rec, "moved_on", "Season end")
			continue
		var name := str(rec.get("mem", {}).get("name", ""))
		var line := "%s stays at %s: the coach has moved on." % [name, GameDB.club_name(gs.my_club)] if str(def.get("kind", "")) == "player" and name != "" \
				else "%s stays behind at %s: the coach has moved on." % [str(def.get("name", id)), GameDB.club_name(gs.my_club)]
		CoachArcs.log_line(st, int(gs.season_year), "Season end", str(id), "ENDS (moved_on): " + line)
		CoachArcs.finish(st, str(id), "moved_on", int(gs.season_year))


## The club that gives a sacked coach his next job: one of the bottom clubs on
## the final ladder, not one that has sacked him (seeded, so a reload agrees).
static func _job_after_sack(gs, st: Dictionary) -> String:
	var table: Array = gs.season.ladder_sorted()
	var sacked_him := {}
	for h in st["coach"]["clubs"]:
		if str(h.get("why_left", "")) == "sacked":
			sacked_him[str(h["code"])] = true
	# Not the club his own assistant is leaving to coach.
	var asst: Dictionary = st["active"].get("assistant", {})
	if (asst.get("flags", {}) as Dictionary).has("backed"):
		sacked_him[str(asst.get("mem", {}).get("assistant_code", ""))] = true
	var pool := []
	for i in range(table.size() - 1, -1, -1):
		var code := str(table[i]["code"])
		if code == str(gs.my_club) or sacked_him.has(code):
			continue
		pool.append(code)
		if pool.size() >= SACKED_FROM_BOTTOM:
			break
	if pool.is_empty():
		return ""
	return str(pool[_roll(gs, "sackjob|%d" % int(gs.season_year), pool.size())])


## The assistant (arc "assistant") who was backed to go: he takes the rival's
## senior job now (their coach is let go) and his own job is open.
static func _assistant_leaves(gs, st: Dictionary) -> void:
	var rec: Dictionary = st["active"].get("assistant", {})
	if rec.is_empty() or not (rec.get("flags", {}) as Dictionary).has("backed"):
		return
	var mem: Dictionary = rec.get("mem", {})
	var asst: Dictionary = gs.coaches.get(str(mem.get("assistant_id", "")), {})
	var to := str(mem.get("assistant_code", ""))
	if asst.is_empty() or to == "" or str(asst.get("club", "")) != str(gs.my_club):
		return
	var year := int(gs.season_year)
	var job := str(asst.get("job", "SA"))
	var sc := _senior_coach(gs, to)
	if not sc.is_empty():
		CoachMarket._leave_job(sc, year)
	CoachMarket._appoint(asst, to, "SC", year, int(gs.career_seed))
	if not gs._vacancy_open(job):
		gs.staff_vacancies.append({"job": job, "reason": "%s has left to coach %s." % [str(mem.get("assistant", "")), GameDB.club_name(to)]})


# ---------------------------------------------------------------------------
# The rollover: the move
# ---------------------------------------------------------------------------
static func apply_move(gs) -> void:
	if not ClubArcs.on(gs):
		return
	var st := ClubArcs._st(gs)
	var mv: Dictionary = st["move"]
	var to := str(mv.get("to", ""))
	if to == "" or to == str(gs.my_club):
		st["move"] = {}
		return
	var from := str(gs.my_club)
	var year := int(gs.season_year)
	var seed := int(gs.career_seed)
	# The new club's senior coach makes way: he takes the job left open, or
	# the assistant who was after it does and he is let go.
	var theirs := _senior_coach(gs, to)
	var heir := {}
	var a: Dictionary = st["done"].get("assistant", {})
	if str(a.get("ending", "")) == "took_job" and int(a.get("year", 0)) == year:
		heir = gs.coaches.get(str(mv.get("heir", "")), {})
		# Only while he is still on staff at the club he would take over.
		if str(heir.get("status", "")) != "club" or str(heir.get("club", "")) != from:
			heir = {}
	if not heir.is_empty():
		CoachMarket._appoint(heir, from, "SC", year, seed)
		if not theirs.is_empty():
			CoachMarket._leave_job(theirs, year)
	elif not theirs.is_empty():
		CoachMarket._appoint(theirs, from, "SC", year, seed)
	# His record: the club he leaves, the club he joins.
	var c: Dictionary = st["coach"]
	for h in c["clubs"]:
		if str(h.get("code", "")) == from and int(h.get("to", 0)) == 0:
			h["to"] = year
			h["why_left"] = str(mv.get("why", ""))
			h["chairman"] = str(st["people"].get("chairman", ""))
	(c["clubs"] as Array).append({"code": to, "name": GameDB.club_name(to), "from": year + 1, "to": 0, "why": str(mv.get("why", ""))})
	c["club"] = to
	c["moved"] = {"year": year, "why": str(mv.get("why", "")), "from": from, "to": to}
	st["people"].erase("chairman")
	st["move"] = {}
	# The club he joins: a fresh board (its history of his seasons kept), and
	# nothing left over from the old club's office.
	var hist: Array = gs.board.get("history", [])
	gs.board = {}
	# The old club's honour board is put away and the new club's taken up.
	HonourBoard.change_club(gs, from, to)
	gs.my_club = to
	gs.board = {"confidence": ClubLife.START_CONFIDENCE, "warned": false, "sacked": false, "history": hist}
	gs.staff_vacancies = []
	gs.coach_approaches = []
	gs.trade_requests = {}
	gs.week_events = []
	var old_name := GameDB.club_name(from)
	gs.add_news(ClubArcs.NEWS_KIND, "You are the new senior coach of %s. %s takes over at %s." % [GameDB.club_name(to),
			(GameDB.player_display_name(heir) if not heir.is_empty() else (GameDB.player_display_name(theirs) if not theirs.is_empty() else "A new coach")), old_name])


static func _senior_coach(gs, code: String) -> Dictionary:
	for cid in gs.coaches:
		var c: Dictionary = gs.coaches[cid]
		if str(c.get("status", "")) == "club" and str(c.get("club", "")) == code and str(c.get("job", "")) == "SC":
			return c
	return {}


static func _roll(gs, key: String, n: int) -> int:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("clubmove|%d|%s" % [int(gs.career_seed), key])
	return rng.randi_range(0, maxi(n - 1, 0))


# ---------------------------------------------------------------------------
# Triggers (ClubArcs.trigger)
# ---------------------------------------------------------------------------
## Arc 3: top-4 finishes twice at this club, or last season's flag, and a
## struggling club wants him. At a season's start.
static func poach_trigger(gs, st: Dictionary, tr: Dictionary, season_start: bool) -> Dictionary:
	if not season_start or gs.honour_roll.is_empty():
		return {}
	var since := _club_since(st, str(gs.my_club))
	var tops := 0
	for h in gs.honour_roll:
		if int(h.get("year", 0)) >= since and str(h.get("my_club", "")) == str(gs.my_club) \
				and int(h.get("my_position", 99)) > 0 and int(h.get("my_position", 99)) <= int(tr.get("top", 4)):
			tops += 1
	var flag := str(gs.honour_roll[-1].get("premier", "")) == str(gs.my_club)
	if tops < int(tr.get("top4", 2)) and not flag:
		return {}
	var pool := []
	var finish: Dictionary = gs._last_finish
	var half := maxi(1, finish.size() / 2)
	for code in finish:
		if str(code) != str(gs.my_club) and int(finish[code]) > half and not _coached_at(st, str(code)) \
				and not _senior_coach(gs, str(code)).is_empty():
			pool.append(str(code))
	if pool.is_empty():
		return {}
	pool.sort()
	var code: String = pool[_roll(gs, "suitor|%d" % int(gs.season_year), pool.size())]
	return {"mem": {"suitor": GameDB.club_name(code), "suitor_code": code,
			"suitor_president": ClubArcs._gen_name(int(gs.career_seed), "president|" + code)}}


## Arc 7: this week's opponent is a club he coached before (not while the way
## back, which has its own first meeting, still runs). The same club comes
## round again at most once every `club_every` seasons (counted from when its
## last reunion ended), except a club he won a flag at: in each year a whole
## `anniversary` of seasons on from that flag, it is the premiership reunion,
## whatever the cooldown.
static func reunion_trigger(gs, st: Dictionary, club: Dictionary, ctx: Dictionary, season_start: bool) -> Dictionary:
	if season_start or str(ctx["phase"]) != "regular" or (st["active"] as Dictionary).has("way_back"):
		return {}
	var tr: Dictionary = CoachArcs.by_id(CoachArcs.all(), "reunion").get("trigger", {})
	var year := int(gs.season_year)
	for h in st["coach"]["clubs"]:
		var code := str(h.get("code", ""))
		if code == str(gs.my_club) or int(h.get("to", 0)) == 0 or str(club.get("opp", "")) != GameDB.club_name(code):
			continue
		var flag := anniversary_flag(gs, code, year, int(tr.get("anniversary", 10)))
		if flag > 0 and int(h.get("anniv", 0)) == year:
			flag = 0
		var last := int(h.get("reunion", 0))
		if flag == 0 and last > 0 and year - last < int(tr.get("club_every", 10)):
			continue
		var mem := ClubArcs._old_club_mem(gs, st, code)
		if str(mem["former"]) == "" and flag == 0:
			return {}
		if flag > 0:
			mem["flag_year"] = flag
			mem["flag_years_on"] = year - flag
			mem["flag_reunion"] = true
		return {"mem": mem}
	return {}


## The flag he won at `code` a whole number of `every` seasons before `year`
## (the latest, if more than one), or 0.
static func anniversary_flag(gs, code: String, year: int, every: int) -> int:
	var best := 0
	for h in gs.honour_roll:
		var y := int(h.get("year", 0))
		if every > 0 and y < year and (year - y) % every == 0 and str(h.get("premier", "")) == code \
				and str(h.get("my_club", "")) == code:
			best = maxi(best, y)
	return best


## Arc 11: a senior assistant with a name while the board wavers.
static func assistant_trigger(gs, st: Dictionary, tr: Dictionary, ctx: Dictionary, season_start: bool) -> Dictionary:
	if season_start or str(ctx["phase"]) != "regular" or gs.board_confidence() >= int(tr.get("board_below", 50)):
		return {}
	var best := {}
	var best_id := ""
	for cid in gs.coaches:
		var c: Dictionary = gs.coaches[cid]
		if str(c.get("status", "")) == "club" and str(c.get("club", "")) == str(gs.my_club) and str(c.get("job", "")) == "SA" \
				and int(c.get("rep", 0)) >= int(tr.get("rep_min", 55)) and int(c.get("rep", 0)) > int(best.get("rep", -1)):
			best = c
			best_id = str(cid)
	if best.is_empty():
		return {}
	var pool := []
	for code in gs.season.ladder:
		if str(code) != str(gs.my_club) and not _senior_coach(gs, str(code)).is_empty():
			pool.append(str(code))
	if pool.is_empty():
		return {}
	pool.sort()
	var to: String = pool[_roll(gs, "assistant_to|%d|%s" % [int(gs.season_year), best_id], pool.size())]
	return {"mem": {"assistant": GameDB.player_display_name(best), "assistant_id": best_id,
			"assistant_to": GameDB.club_name(to), "assistant_code": to}}


## The best player still at `code` whom the coach coached there, or "".
static func former_player(gs, st: Dictionary, code: String) -> String:
	var list: Array = gs.season.lists.get(code, []) if gs.season != null else []
	var best := {}
	for p in list:
		if (st["coach"]["coached"] as Dictionary).has(str(p["id"])) and int(p.get("overall", 0)) > int(best.get("overall", -1)):
			best = p
	return GameDB.player_display_name(best) if not best.is_empty() else ""


## The reunion's result, from the round just played against the old club.
static func record_reunion(gs, st: Dictionary) -> void:
	var rec: Dictionary = st["active"].get("reunion", {})
	if rec.is_empty() or gs.season == null or (gs.season.results as Array).is_empty():
		return
	var flags: Dictionary = rec["flags"]
	if flags.has("won") or flags.has("lost") or flags.has("drew"):
		return
	var old := str(rec.get("mem", {}).get("old_code", ""))
	for res in gs.season.results[-1]:
		var side := -1
		if str(res.get("home", "")) == str(gs.my_club) and str(res.get("away", "")) == old:
			side = 0
		elif str(res.get("away", "")) == str(gs.my_club) and str(res.get("home", "")) == old:
			side = 1
		if side < 0:
			continue
		var s: Array = res["score"]
		# A draw is neither: it is recorded only so the result is not read again.
		var mine := int(s[side])
		var theirs := int(s[1 - side])
		flags["won" if mine > theirs else ("drew" if mine == theirs else "lost")] = gs.story_week()


static func _club_since(st: Dictionary, code: String) -> int:
	var since := 0
	for h in st["coach"]["clubs"]:
		if str(h.get("code", "")) == code:
			since = int(h.get("from", 0))
	return since


static func _coached_at(st: Dictionary, code: String) -> bool:
	for h in st["coach"]["clubs"]:
		if str(h.get("code", "")) == code:
			return true
	return false
