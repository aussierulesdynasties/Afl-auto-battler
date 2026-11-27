class_name Council
extends RefCounted
## The Council: the eight people who run a club's football department with
## its senior coach (relationship overhaul, the Council phase, director
## 2026-11-26, DIRECTOR_BIBLE 5.169-5.177, decisions 5 and 6).
##
## Eight seats at every one of the 18 clubs: the six coaching jobs
## (Coaches.JOBS: senior coach, senior assistant, midfield, forwards, backline,
## development) plus a List Manager and a Head of High Performance. At your
## club the senior coach is you, so seven people sit around your table.
##
## What each member brings:
##   agenda    what he pushes for (data/relations/agendas.json): bring the kids
##             through, win now, standards, look after the players, mind the
##             bodies, build the list. Picked from his id and job.
##   manner    how he says it: blunt, measured or warm. His own signed voice
##             on the cards (decision 5).
##   loyalty   his opinion of his senior coach, in the Opinion shape at
##             gs.relations["s:<id>"] (a permanent part and fading marks), so
##             it fades every round with everything else (Opinion.fade_round).
##   players   the men attached to him, read from his job and never stored:
##             the line coaches and their line, the development coach and the
##             kids, the senior assistant and the leadership group, the list
##             manager and the men in their first year at the club.
##
## Where the people are kept: the six coaching jobs are the coach records in
## gs.coaches (Coaches.gd); their agenda and manner are read from id and job
## (coach_agenda), never written onto the record. The two new
## seats are gs.council["office"][club][job] = {id, name, agenda, manner,
## since}: generated people with fictional names, replaced when they leave.
##
## What the Council does:
##   - On a week's card, at most one member backs the choice his agenda suits
##     best, in his own words (pitch). The card shows what taking or passing
##     his advice does: taking it lifts his loyalty, going against it costs
##     loyalty and builds your Authority (Promises.move). Never "best".
##   - After every round, at every club, the youth and win-now members read
##     the side that was picked (after_round): a side with kids in it suits
##     one, a side with its best men left out crosses the other. The same rule
##     at every club (2026-11-09).
##   - At the season's close a member whose loyalty has fallen to WALK_LINE
##     walks out (season_end), at every club. Losing a coach, by a walk-out,
##     the market or your release, leaves a mark on the players attached to
##     him (staff_gone).
##   - A faction's pressure each round leans on the council (faction_sway):
##     loyal members tied to it (its men, or an agenda that matches its
##     grievance) talk it down, restless ones back it and push it on.
##   - In season, a line or development coach at RESTLESS_LINE or under takes
##     his man-management away (withheld: no softening when his men are
##     dropped) and acts on his own on the cards (the "restless" advisor:
##     a leak to the papers, a word in the board's ear, backing a group).
##   - Two members can back competing choices on one card (clash).
## Nothing here reaches the match: loyalty and agendas never touch MatchSim,
## and a player's mark from losing his coach reaches morale only by the
## opinion drift every club already has (ClubLife.drift_morale).

const AGENDAS_PATH := "res://data/relations/agendas.json"

## The seats in table order, and the job each one is.
const SEATS := ["senior_coach", "senior_assistant", "line_coach", "fwd_coach", "def_coach",
		"development", "list_manager", "high_performance"]
const SEAT_JOB := {"senior_coach": "SC", "senior_assistant": "SA", "line_coach": "MID",
		"fwd_coach": "FWD", "def_coach": "DEF", "development": "DEV",
		"list_manager": "LM", "high_performance": "HP"}
## The two seats that are not coaching jobs.
const OFFICE_JOBS := ["LM", "HP"]
const OFFICE_LABEL := {"LM": "List manager", "HP": "Head of high performance"}
## What a seat is called in a sentence ("Sam Day, the development coach").
const ROLE_WORD := {"SC": "senior coach", "SA": "senior assistant", "MID": "midfield coach",
		"FWD": "forwards coach", "DEF": "backline coach", "DEV": "development coach",
		"LM": "list manager", "HP": "head of high performance"}
const MANNERS := ["blunt", "measured", "warm"]

## Where a member's loyalty sits in gs.relations.
const KEY_PREFIX := "s:"
## A member this disloyal (shown loyalty, 0-100) walks out at the season's close.
const WALK_LINE := 25
## Loyal and disloyal, for a faction's sway and the Staff screen's words.
const LOYAL_LINE := 65
const RESTLESS_LINE := 35
## The most a council moves a faction's pressure down in one round, and up.
const SWAY_MAX := 2
const STIR_MAX := 4
## How hard each restless member tied to a group pushes it on, a round.
const STIR := 2
## The coaches whose disloyalty bites in season (withheld, restless).
const TEETH_JOBS := ["MID", "FWD", "DEF", "DEV"]
## A pitch needs its choice to suit him by this much more than every other.
const PITCH_MARGIN := 2
## What going against a member's advice builds: [Respect, Authority].
const OVERRULE := [0, 1]
## Two members backing different choices on one card (a clash): the one you
## side with gains (advice_taken), the other loses (advice_passed_over); a
## third choice of your own costs both a little (advice_both_overruled) and
## builds your Authority by OWN_WAY.
const OWN_WAY := [0, 2]
## The kids a youth member wants to see in a side, and the fewest he puts up with.
const YOUTH_AGE := 21
const YOUTH_SERVED := 5
const YOUTH_CROSSED := 1
## How many of the club's best fit men a win-now member will see left out
## before he says so, and none at all suits him.
const BEST_LEFT_OUT := 3
## The list manager's men: in their first season at the club.
const NEW_MAN_SEASONS := 1

static var _agendas: Dictionary = {}


# ---------------------------------------------------------------------------
# The agendas (data)
# ---------------------------------------------------------------------------

static func agendas() -> Dictionary:
	if _agendas.is_empty():
		var f := FileAccess.open(AGENDAS_PATH, FileAccess.READ)
		if f != null:
			var d: Variant = JSON.parse_string(f.get_as_text())
			if d is Dictionary:
				_agendas = (d as Dictionary).get("agendas", {})
	return _agendas


static func agenda(k: String) -> Dictionary:
	return agendas().get(k, {})


static func agenda_label(k: String) -> String:
	return str(agenda(k).get("label", ""))


## What is wrong with the agendas file, in words ([] when it is sound).
static func check_agendas(d: Dictionary) -> Array:
	var bad := []
	if d.is_empty():
		return ["no agendas"]
	var held := {}
	for k in d:
		var a: Dictionary = d[k] if d[k] is Dictionary else {}
		if str(a.get("label", "")) == "" or str(a.get("about", "")) == "":
			bad.append("%s: needs a label and an about line" % k)
		var jobs: Dictionary = a.get("jobs", {})
		for j in jobs:
			if not SEAT_JOB.values().has(j) or j == "SC":
				bad.append("%s: %s is not a council job a member can hold" % [k, j])
			elif float(jobs[j]) > 0.0:
				held[j] = true
		if (a.get("weigh", {}) as Dictionary).is_empty():
			bad.append("%s: nothing weighs with him" % k)
		var voice: Dictionary = a.get("voice", {})
		for m in MANNERS:
			var lines: Array = voice.get(m, [])
			if lines.is_empty():
				bad.append("%s: no %s voice" % [k, m])
			for line in lines:
				if str(line).ends_with(".") or str(line).strip_edges() == "":
					bad.append("%s: a %s line must be words with no full stop" % [k, m])
	for j in SEAT_JOB.values():
		if j != "SC" and not held.has(j):
			bad.append("no agenda for the %s" % ROLE_WORD[j])
	return bad


## A member's agenda and manner, picked once from his job and his id: the
## same person always wants the same thing.
static func pick_agenda(id: String, job: String) -> String:
	var keys := agendas().keys()
	keys.sort()
	var total := 0.0
	for k in keys:
		total += float((agenda(k).get("jobs", {}) as Dictionary).get(job, 0))
	if total <= 0.0:
		return "win_now" if agendas().has("win_now") else (str(keys[0]) if not keys.is_empty() else "")
	var roll := _roll("agenda|" + id) * total
	for k in keys:
		roll -= float((agenda(k).get("jobs", {}) as Dictionary).get(job, 0))
		if roll < 0.0:
			return k
	return str(keys[-1])


static func pick_manner(id: String) -> String:
	return MANNERS[int(_roll("manner|" + id) * MANNERS.size()) % MANNERS.size()]


static func _roll(key: String) -> float:
	return float(hash(key) & 0x7fffffff) / float(0x7fffffff)


# ---------------------------------------------------------------------------
# Who sits where
# ---------------------------------------------------------------------------

static func seat_of(job: String) -> String:
	for s in SEAT_JOB:
		if SEAT_JOB[s] == job:
			return s
	return ""


static func role_word(job: String) -> String:
	return str(ROLE_WORD.get(job, job))


## Give every club its list manager and head of high performance. Run when a season starts and on load;
## nothing it adds changes a match. Returns how many people were added.
static func ensure(gs) -> int:
	if gs.season == null:
		return 0
	if not (gs.council is Dictionary):
		gs.council = {}
	if not (gs.council.get("office") is Dictionary):
		gs.council["office"] = {}
	var office: Dictionary = gs.council["office"]
	var added := 0
	for code in gs.season.lists:
		var club := str(code)
		if not (office.get(club) is Dictionary):
			office[club] = {}
		for job in OFFICE_JOBS:
			if not ((office[club] as Dictionary).get(job) is Dictionary):
				office[club][job] = _new_office(gs, club, job)
				added += 1
	return added


## A coach's agenda and manner: read from his id and the job he holds, never
## written onto his record (the coach records stay as CoachMarket keeps them).
## A coach promoted to a new job takes up that job's brief. A record that
## carries its own "agenda" or "manner" (a test, a later card) keeps it.
static func coach_agenda(c: Dictionary) -> String:
	var own := str(c.get("agenda", ""))
	if agendas().has(own):
		return own
	var job := str(c.get("job", ""))
	return pick_agenda(str(c.get("cid", "")), job if job != "" and job != "SC" else "SA")


static func coach_manner(c: Dictionary) -> String:
	var own := str(c.get("manner", ""))
	return own if MANNERS.has(own) else pick_manner(str(c.get("cid", "")))


## A new list manager or head of high performance: a fictional name, never a
## real person's (none is researched).
static func _new_office(gs, club: String, job: String) -> Dictionary:
	var n := int(gs.council.get("hired", 0)) + 1
	gs.council["hired"] = n
	var id := "O_%s_%s_%d" % [club, job, n]
	var seed := int(gs.career_seed) if "career_seed" in gs else 0
	var rec := {"id": id, "name": CoachMarket._gen_name(id, seed), "job": job,
			"since": int(gs.season_year)}
	rec["agenda"] = pick_agenda(id, job)
	rec["manner"] = pick_manner(id)
	return rec


## The people around a club's table, in seat order: [{seat, job, id, name,
## role, agenda, manner, key, coach}] (coach: the coach record, or {} for an
## office seat). Your own seat is left out at your club. An empty seat is
## left out.
static func members(gs, club: String) -> Array:
	var out := []
	var staff: Dictionary = gs.club_staff(club) if gs.has_method("club_staff") else {}
	var office: Dictionary = ((gs.council if gs.council is Dictionary else {}).get("office", {}) as Dictionary).get(club, {})
	var mine := club == str(gs.my_club)
	for seat in SEATS:
		var job := str(SEAT_JOB[seat])
		if job == "SC" and mine:
			continue
		if OFFICE_JOBS.has(job):
			var o: Dictionary = office.get(job, {})
			if o.is_empty():
				continue
			out.append({"seat": seat, "job": job, "id": str(o["id"]), "name": str(o["name"]),
					"role": role_word(job), "agenda": str(o.get("agenda", "")), "manner": str(o.get("manner", "measured")),
					"key": KEY_PREFIX + str(o["id"]), "coach": {}})
			continue
		var c: Dictionary = staff.get(job, {})
		if c.is_empty():
			continue
		out.append({"seat": seat, "job": job, "id": str(c.get("cid", "")), "name": GameDB.player_display_name(c),
				"role": role_word(job), "agenda": coach_agenda(c), "manner": coach_manner(c),
				"key": KEY_PREFIX + str(c.get("cid", "")), "coach": c})
	return out


## The cards' advisors, {seat: {"name", "role"}} (StoryEngine.advisor_facts):
## every filled seat at your club.
static func advisor_seats(gs) -> Dictionary:
	var out := {}
	for m in members(gs, str(gs.my_club)):
		out[str(m["seat"])] = {"name": str(m["name"]), "role": str(m["role"])}
	# A line or development coach gone restless can act on his own: the
	# leak, the board's ear and the players' group cards seat him.
	var r := restless(gs, str(gs.my_club))
	if not r.is_empty():
		out["restless"] = {"name": str(r["name"]), "role": str(r["role"])}
	return out


## A member's loyalty to the senior coach, 0-100 as the game shows it (50 is level).
static func loyalty(gs, m: Dictionary) -> int:
	return Opinion.opinion(Opinion.value(gs.relations, str(m["key"])))


static func loyalty_word(v: int) -> String:
	if v >= LOYAL_LINE:
		return "Loyal to you"
	if v <= WALK_LINE:
		return "Ready to walk"
	if v <= RESTLESS_LINE:
		return "Restless"
	return "Steady"


## The players attached to a job at a club, read from the list now.
static func attached(gs, club: String, job: String) -> Array:
	var list: Array = gs.season.lists.get(club, []) if gs.season != null else []
	var out := []
	match job:
		"MID", "FWD", "DEF":
			for p in list:
				if CoachEffects.line_job(p) == job:
					out.append(p)
		"DEV":
			for p in list:
				if int(p.get("age", 25)) <= YOUTH_AGE:
					out.append(p)
		"SA":
			var lead: Dictionary = ClubStories.leader_ids(gs, club, list) if gs.has_method("captaincy_record") else {}
			for p in list:
				if lead.has(str(p["id"])):
					out.append(p)
		"LM":
			for p in list:
				if _new_man(gs, p, club):
					out.append(p)
	return out


static func _new_man(gs, p: Dictionary, _club: String) -> bool:
	# Joined or drafted in the last off-season (ClubStories._new_here's rule).
	var came := maxi(int(p.get("joined", 0)), int(p.get("drafted_year", 0)))
	return came >= int(gs.season_year) - NEW_MAN_SEASONS


# ---------------------------------------------------------------------------
# The cards: a member backs a choice in his own words
# ---------------------------------------------------------------------------

## How much a choice's effects suit an agenda (agendas.json "weigh").
static func suits(ag: String, effects: Array) -> int:
	var w: Dictionary = agenda(ag).get("weigh", {})
	var total := 0
	for e in effects:
		if not (e is Dictionary):
			continue
		var op := str(e.get("op", ""))
		if op == "odds":
			total += suits(ag, e.get("hit", []))
			continue
		var d := float(e.get("d", 0))
		var sign := "+" if d > 0 else ("-" if d < 0 else "")
		if op == "culture":
			total += int(w.get("culture:%s:%s" % [str(e.get("strand", "")), sign], 0))
			continue
		total += int(w.get(op, 0))
		if sign != "":
			total += int(w.get("%s:%s" % [op, sign], 0))
	return total


## The member who backs one choice on this card, as the card carries it:
## {seat, job, id, name, role, agenda, option, line, key} or {} when nobody
## has a clear view. At most one per card: the member whose agenda sets one
## choice furthest ahead of the rest (by PITCH_MARGIN at least), the table's
## order breaking a tie. A card with one choice, or already answered, has none.
static func pitch(gs, card: Dictionary) -> Dictionary:
	var opts: Array = card.get("options", [])
	if opts.size() < 2 or bool(card.get("resolved", false)) or str(gs.my_club) == "":
		return {}
	var best := {}
	var best_gap := 0
	for m in members(gs, str(gs.my_club)):
		var scores := []
		for o in opts:
			scores.append(suits(str(m["agenda"]), (o as Dictionary).get("effects", [])))
		var top := -1
		for i in scores.size():
			if top < 0 or int(scores[i]) > int(scores[top]):
				top = i
		if int(scores[top]) <= 0:
			continue
		var gap := 999
		for i in scores.size():
			if i != top:
				gap = mini(gap, int(scores[top]) - int(scores[i]))
		if gap < PITCH_MARGIN or gap <= best_gap:
			continue
		best_gap = gap
		best = m.duplicate()
		best["option"] = top
	if best.is_empty():
		return {}
	return _signed(best, card)


## A member's pitch as the card carries it: his line in his own voice.
static func _signed(m: Dictionary, card: Dictionary) -> Dictionary:
	var best := m.duplicate()
	var lines: Array = (agenda(str(best["agenda"])).get("voice", {}) as Dictionary).get(str(best["manner"]), [])
	var line := ""
	if not lines.is_empty():
		line = str(lines[int(_roll("voice|%s|%s" % [str(best["id"]), str(card.get("tid", card.get("title", "")))]) * lines.size()) % lines.size()])
	best.erase("coach")
	best["line"] = line
	return best


## The member who backs a different choice from `first` on the same card, so
## the two clash: {} when nobody does. His choice must suit him by
## PITCH_MARGIN more than the one `first` backs; the widest gap wins, the
## table's order breaking a tie. At most two members a card.
static func clash(gs, card: Dictionary, first: Dictionary) -> Dictionary:
	var opts: Array = card.get("options", [])
	if first.is_empty() or opts.size() < 2:
		return {}
	var against := int(first.get("option", -1))
	var best := {}
	var best_gap := PITCH_MARGIN - 1
	for m in members(gs, str(gs.my_club)):
		if str(m["id"]) == str(first.get("id", "")):
			continue
		var scores := []
		for o in opts:
			scores.append(suits(str(m["agenda"]), (o as Dictionary).get("effects", [])))
		var top := -1
		for i in scores.size():
			if i != against and (top < 0 or int(scores[i]) > int(scores[top])):
				top = i
		if top < 0 or int(scores[top]) <= 0:
			continue
		var gap := int(scores[top]) - int(scores[against])
		if gap <= best_gap:
			continue
		best_gap = gap
		best = m.duplicate()
		best["option"] = top
	return {} if best.is_empty() else _signed(best, card)


## Give each of a week's cards its pitch (when someone has a view).
static func pitch_cards(gs, cards: Array) -> void:
	for card in cards:
		if not (card is Dictionary) or (card as Dictionary).has("pitch"):
			continue
		var p := pitch(gs, card)
		if not p.is_empty():
			card["pitch"] = p
			# A second member who wants the other way makes it a clash.
			var c := clash(gs, card, p)
			if not c.is_empty():
				card["clash"] = c


## The card's lines for its pitch: who backs which choice and why (one line
## each, two when members clash), then what taking or going against the advice
## does, one number a line (the decision gate shows the size, never which is
## better). [] when nobody backs a choice. said_count says how many of the
## first lines are the members' own words.
static func pitch_lines(card: Dictionary) -> Array:
	var p: Dictionary = card.get("pitch", {})
	var opts: Array = card.get("options", [])
	if p.is_empty() or int(p.get("option", -1)) < 0 or int(p["option"]) >= opts.size():
		return []
	var c: Dictionary = card.get("clash", {})
	if not c.is_empty() and (int(c.get("option", -1)) < 0 or int(c["option"]) >= opts.size()):
		c = {}
	var take := int(round(float(Opinion.def("advice_taken").get("v", 0))))
	# Named, never "his": the council has women in it. One effect, one number
	# a line (copy voice, style guide 5.1).
	var first := str(p["name"]).get_slice(" ", 0)
	if c.is_empty():
		var pass_v := int(round(float(Opinion.def("advice_overruled").get("v", 0))))
		return [_said(p, opts), "Take %s advice: loyalty %+d." % [CopyRules.possessive(first), take],
				"Go against %s: loyalty %d." % [first, pass_v],
				"Go against %s: your Authority %+d." % [first, int(OVERRULE[1])]]
	var other := str(c["name"]).get_slice(" ", 0)
	if other == first:
		first = str(p["name"])
		other = str(c["name"])
	var lose := int(round(float(Opinion.def("advice_passed_over").get("v", 0))))
	var out := [_said(p, opts), _said(c, opts)]
	for pair in [[first, other], [other, first]]:
		out.append("Take %s advice: %s loyalty %+d." % [CopyRules.possessive(pair[0]), CopyRules.possessive(pair[0]), take])
		out.append("Take %s advice: %s loyalty %d." % [CopyRules.possessive(pair[0]), CopyRules.possessive(pair[1]), lose])
	if opts.size() > 2:
		var both := int(round(float(Opinion.def("advice_both_overruled").get("v", 0))))
		out.append("Go your own way: %s and %s loyalty %d each." % [first, other, both])
		out.append("Go your own way: your Authority %+d." % int(OWN_WAY[1]))
	return out


## How many of pitch_lines' first lines are a member's own words (1, or 2 in a
## clash; 0 with none).
static func said_count(card: Dictionary) -> int:
	if (card.get("pitch", {}) as Dictionary).is_empty():
		return 0
	return 2 if not (card.get("clash", {}) as Dictionary).is_empty() else 1


static func _said(p: Dictionary, opts: Array) -> String:
	var label := str((opts[int(p["option"])] as Dictionary).get("label", ""))
	var said := "%s, %s, backs \"%s\"" % [str(p["name"]), str(p["role"]), label]
	if str(p.get("line", "")) != "":
		said += ": \"%s.\"" % str(p["line"])
	else:
		said += "."
	return said


## The coach answered a card a member had backed a choice on.
static func answered(gs, card: Dictionary, choice: int) -> void:
	var p: Dictionary = card.get("pitch", {})
	if p.is_empty():
		return
	var when := str(gs.last_label) if str(gs.last_label) != "" else "Week %d" % int(gs.story_week())
	var src := "card:%s|%d" % [str(card.get("tid", "")), int(gs.story_week())]
	var c: Dictionary = card.get("clash", {})
	if not c.is_empty():
		_answered_clash(gs, card, p, c, choice, when, src)
		return
	if choice == int(p.get("option", -1)):
		Opinion.add(gs.relations, str(p["key"]), "advice_taken", int(gs.season_year), when, str(gs.my_club),
				1.0, src)
		card["pitch_taken"] = true
	else:
		Opinion.add(gs.relations, str(p["key"]), "advice_overruled", int(gs.season_year), when, str(gs.my_club),
				1.0, src)
		Promises.move(gs, int(OVERRULE[0]), int(OVERRULE[1]),
				"You overruled your %s, %s" % [str(p["role"]), str(p["name"])])
		card["pitch_taken"] = false


## Two members clashed on the card: the one you sided with gains, the other
## loses; a choice of your own costs both a little and builds your Authority.
static func _answered_clash(gs, card: Dictionary, p: Dictionary, c: Dictionary, choice: int, when: String,
		src: String) -> void:
	var year := int(gs.season_year)
	var club := str(gs.my_club)
	if choice == int(p.get("option", -1)) or choice == int(c.get("option", -1)):
		var won := p if choice == int(p["option"]) else c
		var lost := c if won == p else p
		Opinion.add(gs.relations, str(won["key"]), "advice_taken", year, when, club, 1.0, src)
		Opinion.add(gs.relations, str(lost["key"]), "advice_passed_over", year, when, club, 1.0, src, 1.0,
				"You took %s side" % CopyRules.possessive(str(won["name"])))
		card["pitch_taken"] = won == p
		card["clash_taken"] = won == c
		return
	for m in [p, c]:
		Opinion.add(gs.relations, str(m["key"]), "advice_both_overruled", year, when, club, 1.0, src)
	Promises.move(gs, int(OWN_WAY[0]), int(OWN_WAY[1]),
			"You went your own way over %s and %s" % [str(p["name"]), str(c["name"])])
	card["pitch_taken"] = false
	card["clash_taken"] = false


# ---------------------------------------------------------------------------
# After every round, every club
# ---------------------------------------------------------------------------

## The youth and win-now members read the side each club picked. `results`
## are the round's matches with their rosters (GameState). Same rule at every
## club; returns how many marks were added (tests).
static func after_round(gs, results: Array) -> int:
	if gs.season == null:
		return 0
	var added := 0
	var when := str(gs.last_label) if str(gs.last_label) != "" else "Round %d" % int(gs.season.round_index)
	for res in results:
		var roster: Array = (res as Dictionary).get("roster", [[], []])
		for side in range(2):
			var club := str(res.get("home" if side == 0 else "away", ""))
			if club == "" or not gs.season.lists.has(club) or roster.size() <= side:
				continue
			var played := {}
			for r in roster[side]:
				played[str(r["id"])] = true
			added += _read_side(gs, club, played, when)
	return added


static func _read_side(gs, club: String, played: Dictionary, when: String) -> int:
	var list: Array = gs.season.lists[club]
	var kids := 0
	for p in list:
		if played.has(str(p["id"])) and int(p.get("age", 25)) <= YOUTH_AGE:
			kids += 1
	# The club's best fit men by rating, and how many of them sat out.
	var fit := []
	for p in list:
		if int(p.get("injury_weeks", 0)) <= 0:
			fit.append(p)
	fit.sort_custom(func(a, b): return int(Rating.ovr(a, 0)) > int(Rating.ovr(b, 0)))
	var best_out := 0
	for i in mini(22, fit.size()):
		if not played.has(str(fit[i]["id"])):
			best_out += 1
	var added := 0
	for m in members(gs, club):
		var k := ""
		var why := ""
		match str(m["agenda"]):
			"youth":
				if kids >= YOUTH_SERVED:
					k = "agenda_served"
					why = "Kids picked in the side"
				elif kids <= YOUTH_CROSSED:
					k = "agenda_crossed"
					why = "No room for the kids in the side"
			"win_now":
				if best_out >= BEST_LEFT_OUT:
					k = "agenda_crossed"
					why = "The best side was not picked"
		if k == "":
			continue
		Opinion.add(gs.relations, str(m["key"]), k, int(gs.season_year), when, club, 1.0, "side", 1.0, why)
		added += 1
	return added


## The pressure a club's council puts on a faction each round (Factions.gd).
## A member counts on a group when he is attached to one of its men (his line,
## his kids, his leaders) or his agenda matches the group's grievance (the
## kind's "agendas" in factions.json). Each loyal one talks it down a point;
## each restless one (loyalty RESTLESS_LINE or under) backs it and pushes it
## on by STIR. At most SWAY_MAX down and STIR_MAX up a round. `f` is the
## faction ({k: kind, members: [ids], ...}).
static func faction_sway(gs, club: String, f: Dictionary) -> int:
	var ids := {}
	for id in f.get("members", []):
		ids[str(id)] = true
	if ids.is_empty():
		return 0
	var sway := 0
	for m in members(gs, club):
		if not backs_on(gs, club, m, f, ids):
			continue
		var v := loyalty(gs, m)
		if v >= LOYAL_LINE:
			sway -= 1
		elif v <= RESTLESS_LINE:
			sway += STIR
	return clampi(sway, -SWAY_MAX, STIR_MAX)


## Is a member's line or agenda tied to this group?
static func backs_on(gs, club: String, m: Dictionary, f: Dictionary, ids := {}) -> bool:
	var kinds_agendas: Array = Factions.kind_cfg(str(f.get("k", ""))).get("agendas", [])
	if kinds_agendas.has(str(m.get("agenda", ""))):
		return true
	if ids.is_empty():
		for id in f.get("members", []):
			ids[str(id)] = true
	for p in attached(gs, club, str(m["job"])):
		if ids.has(str(p["id"])):
			return true
	return false


# ---------------------------------------------------------------------------
# A disloyal coach in season: no softening for his men, and a voice of his own
# ---------------------------------------------------------------------------

## The jobs whose man-management stops softening a drop: a line coach (MID,
## FWD, DEF) or the development coach whose loyalty is RESTLESS_LINE or under.
## {job: true}. The same at every club.
static func withheld(gs, club: String) -> Dictionary:
	var out := {}
	for m in members(gs, club):
		if TEETH_JOBS.has(str(m["job"])) and loyalty(gs, m) <= RESTLESS_LINE:
			out[str(m["job"])] = true
	return out


## Does a disloyal coach take his man-management away from this player? His
## line's coach, or (21 and under) the development coach.
static func soften_withheld(p: Dictionary, held: Dictionary) -> bool:
	if held.is_empty():
		return false
	if held.has(CoachEffects.line_job(p)):
		return true
	return held.has("DEV") and int(p.get("age", 25)) <= YOUTH_AGE


## The club's most disloyal line or development coach, the cards' "restless"
## advisor: {} when none is RESTLESS_LINE or under.
static func restless(gs, club: String) -> Dictionary:
	var best := {}
	var low := RESTLESS_LINE + 1
	for m in members(gs, club):
		if not TEETH_JOBS.has(str(m["job"])):
			continue
		var v := loyalty(gs, m)
		if v < low:
			low = v
			best = m
	return best


## The group at the club the restless coach is backing ({} for none).
static func restless_backs(gs, club: String) -> Dictionary:
	var m := restless(gs, club)
	if m.is_empty():
		return {}
	for f in Factions.of_club(gs, club):
		if backs_on(gs, club, m, f):
			return f
	return {}


## A card moves the restless coach's loyalty ("called_out" or "won_back").
static func card_loyalty(gs, club: String, k: String, why := "") -> float:
	var m := restless(gs, club)
	if m.is_empty():
		return 0.0
	var when := str(gs.last_label) if str(gs.last_label) != "" else "Week %d" % int(gs.story_week())
	return Opinion.add(gs.relations, str(m["key"]), k, int(gs.season_year), when, club, 1.0,
			"card:%s|%d" % [k, int(gs.story_week())], 1.0, why)


# ---------------------------------------------------------------------------
# The season's close: walk-outs and staff who are gone
# ---------------------------------------------------------------------------

## Where every council member is now: {id: [club, job]} (before the market).
static func posts(gs) -> Dictionary:
	var out := {}
	if gs.season == null:
		return out
	for code in gs.season.lists:
		for m in members(gs, str(code)):
			out[str(m["id"])] = [str(code), str(m["job"])]
	return out


## Members at WALK_LINE or under walk out, at every club, before the market
## fills the jobs. A coach leaves his job (an AI club's is filled by the
## market, yours opens for you to fill); a list manager or head of high
## performance is replaced. Returns [{club, job, name, id}] who walked.
static func season_end(gs) -> Array:
	var gone := []
	if gs.season == null:
		return gone
	ensure(gs)
	for code in gs.season.lists:
		var club := str(code)
		for m in members(gs, club):
			if str(m["job"]) == "SC" or loyalty(gs, m) > WALK_LINE:
				continue
			gone.append({"club": club, "job": str(m["job"]), "name": str(m["name"]), "id": str(m["id"])})
			if OFFICE_JOBS.has(str(m["job"])):
				gs.council["office"][club][str(m["job"])] = _new_office(gs, club, str(m["job"]))
			else:
				var c: Dictionary = m["coach"]
				CoachMarket.ensure_fields(c, int(gs.season_year))
				CoachMarket._leave_job(c, int(gs.season_year))
			gs.relations.erase(str(m["key"]))
			staff_gone(gs, club, str(m["job"]), str(m["name"]), "walked")
	return gone


## A coach or office member left `club`: the men attached to his job take a
## mark (how much by why he went: "sacked" by you, "walked" out, "left" for
## the market). Same rule at every club.
static func staff_gone(gs, club: String, job: String, name: String, how: String) -> int:
	var k := "coach_sacked" if how == "sacked" else "coach_left"
	var why := ""
	match how:
		"sacked":
			why = "You let his coach, %s, go" % name
		"walked":
			why = "His coach, %s, walked out" % name
		_:
			why = "His coach, %s, left the club" % name
	if OFFICE_JOBS.has(job):
		why = why.replace("His coach", "The %s" % role_word(job)).replace("his coach", "the %s" % role_word(job))
	var n := 0
	var when := "%d off-season" % int(gs.season_year)
	for p in attached(gs, club, job):
		Opinion.add(gs.relations, Opinion.player_key(str(p["id"])), k, int(gs.season_year), when, club,
				Temperament.scale(p, "bond"), "staff:" + job, 1.0, why)
		n += 1
	return n


## After the market: every member who is no longer where he was (`before`,
## from posts) is gone from that club; his players take it, and a coach who
## moved clubs starts his loyalty afresh with his new senior coach. Members
## who walked or were sacked were marked already (`done`: their ids).
static func after_market(gs, before: Dictionary, done := {}) -> int:
	var now := posts(gs)
	var n := 0
	for id in before:
		var was: Array = before[id]
		var is_now: Array = now.get(id, [])
		if not is_now.is_empty() and str(is_now[0]) == str(was[0]):
			continue
		gs.relations.erase(KEY_PREFIX + str(id))
		if done.has(id):
			continue
		var c: Dictionary = gs.coaches.get(id, {})
		var name := GameDB.player_display_name(c) if not c.is_empty() else ""
		if name == "":
			continue
		staff_gone(gs, str(was[0]), str(was[1]), name, "left")
		n += 1
	return n
