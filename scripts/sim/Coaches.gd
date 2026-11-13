class_name Coaches
extends RefCounted
## The coaching world: six jobs at every club and one record per coach.
## Pure rules and the Round 1 2026 seed; GameState keeps the records.
##
## Chronology: the seed is researched Round 1 2026 staff (the historical
## source, kept as it is). A career starts in 2027 (GameDB.START_YEAR) from
## that world carried forward one year by continuity: everyone stays where
## the research put them, a stint's first year is the 2026 the research
## records, and your club's senior coach coached 2026 and makes way for you.
## Nothing claims a real 2027 appointment.
##
## One canonical record per coach, in GameState.coaches[cid]. A club's staff
## is never stored: it is read from each record's club and job, so a coach
## can never exist twice (a save writes plain dictionaries by value, and a
## second copy would load as a second coach). Records use cid / skills / job,
## never the id + attr + role that CareerSave takes for a player.
##
##   cid              C_<slug> seeded, C_G<year>_<n> generated, C_P_<player id>
##                    for a future ex-player
##   real_name        the real person ("" for a generated coach)
##   generic_name     his fictional name (an ex-player keeps his player alias)
##   former_player_id the player he was, "" when he was not one of ours
##   skills           {teach, tactics, manage}, 55-92, never shown as numbers
##   spec             MID / RUCK / FWD / DEF / DEV, or "" for the whole game
##   status           club (in a job), free (available), away (working
##                    outside an AFL coaching job), out (unavailable)
##   club, job        where he coaches ("" when not at a club)
##   free_from        the first year an "out" coach is available
##   stints           [[club, job, from, to], ...]; to 0 = still there. A
##                    seeded stint starts at Round 1 2026: what came before
##                    is not claimed.
##   former_sc        he coached an AFL club before 2026
##   note             what an away or out coach is doing, in words
##   origin           seed / generated
##   played           the playing career of a future ex-player coach
##
## What the skills do on the field lives in CoachEffects.gd (teaching ->
## match XP, tactics -> game-plan execution, man-management -> morale when
## left out). The coaching market lives in CoachMarket.gd.

const SEED_CSV := "res://data/coaches_2026.csv"
## The season the researched seed describes (Round 1 2026).
const SEED_YEAR := 2026

const JOBS := ["SC", "SA", "MID", "FWD", "DEF", "DEV"]
## A senior coach's match-day tendency (director, 2026-10-11): readable,
## characteristic calls, never dice. The rule's numbers are
## MatchSim.COACH_STYLES; the names are internal, never shown about a real
## coach (the copy says what he does: "sits on a lead", "goes for broke").
const STYLES := ["balanced", "stubborn", "reactive", "gambler", "cautious"]
## A senior coach this sharp tactically reads the game as it is: balanced.
const STYLE_SHARP := 78
const JOB_LABEL := {
	"SC": "Senior coach", "SA": "Senior assistant", "MID": "Midfield & ruck",
	"FWD": "Forwards", "DEF": "Defence", "DEV": "Development",
}
const SPEC_LABEL := {
	"MID": "Midfield", "RUCK": "Ruck", "FWD": "Forwards", "DEF": "Defence",
	"DEV": "Development", "": "Whole game",
}
const SKILLS := ["teach", "tactics", "manage"]
const SKILL_LABEL := {"teach": "Teaching", "tactics": "Tactics", "manage": "Man-management"}
## What a coach in each job is known for, as a noun ("a strong teacher").
const SKILL_NOUN := {"teach": "teacher", "tactics": "tactician", "manage": "man-manager"}
## The skill a job leans on most: the one a staff row mentions.
const JOB_SKILL := {"SC": "tactics", "SA": "manage", "MID": "teach", "FWD": "teach",
		"DEF": "teach", "DEV": "teach"}

## Grades, highest first. Provisional: tuned to the seeded spread (most
## coaches Good, a quarter Strong or better, a handful Elite).
const GRADES := [[86, "Elite"], [78, "Strong"], [68, "Good"], [0, "Fair"]]

## Role fit: how the three skills weigh in each job.
const FIT_WEIGHTS := {
	"SC": {"tactics": 0.45, "manage": 0.35, "teach": 0.20},
	"SA": {"tactics": 0.35, "manage": 0.35, "teach": 0.30},
	"MID": {"teach": 0.60, "tactics": 0.25, "manage": 0.15},
	"FWD": {"teach": 0.60, "tactics": 0.25, "manage": 0.15},
	"DEF": {"teach": 0.60, "tactics": 0.25, "manage": 0.15},
	"DEV": {"teach": 0.70, "manage": 0.30},
}
## The specialties each line job is built for, and what fit costs without.
const LINE_SPECS := {"MID": ["MID", "RUCK"], "FWD": ["FWD"], "DEF": ["DEF"]}
const LINE_MISMATCH := 8.0
const DEV_LINE_SPEC := 3.0
const DEV_WHOLE_GAME := 6.0

## Coaches' fictional first names: never one a player can have, so a coach
## and a player never share a name. Surnames come from GameDB's list.
const COACH_FIRST_NAMES := ["Graeme", "Darren", "Wayne", "Craig", "Brett", "Shane", "Glenn", "Rodney", "Stephen", "Peter", "Mark", "Paul",
		"Michael", "David", "Andrew", "Simon", "Brad", "Scott", "Damien", "Dean", "Garry", "Neil", "Rohan", "Trevor",
		"Kevin", "Gavin", "Murray", "Leigh", "Clinton", "Justin", "Brendan", "Gerard", "Phillip"]
const COACH_NAME_SEED := 51_2026


static func grade(v) -> String:
	for g in GRADES:
		if float(v) >= float(g[0]):
			return str(g[1])
	return "Fair"


static func skill(c: Dictionary, key: String) -> int:
	return int((c.get("skills", {}) as Dictionary).get(key, 0))


## How well he suits a job, on the skills' scale: the job's blend of his
## skills, less a penalty when his specialty is not the job's line.
static func role_fit(c: Dictionary, job: String) -> float:
	var w: Dictionary = FIT_WEIGHTS.get(job, {})
	var fit := 0.0
	for k in w:
		fit += float(w[k]) * float(skill(c, k))
	var spec := str(c.get("spec", ""))
	if LINE_SPECS.has(job) and not (LINE_SPECS[job] as Array).has(spec):
		fit -= LINE_MISMATCH
	elif job == "DEV" and spec != "DEV":
		fit -= DEV_WHOLE_GAME if spec == "" else DEV_LINE_SPEC
	return fit


## "Strong teacher": the grade of the skill his job leans on.
static func headline(c: Dictionary) -> String:
	var key := str(JOB_SKILL.get(str(c.get("job", "")), "teach"))
	return "%s %s" % [grade(skill(c, key)), SKILL_NOUN[key]]


## How he suits a job, in words, for a shortlist.
static func fit_word(c: Dictionary, job: String) -> String:
	var f := role_fit(c, job)
	if f >= 80.0:
		return "Excellent fit"
	if f >= 72.0:
		return "Good fit"
	if f >= 64.0:
		return "Fair fit"
	return "Poor fit"


static func rep_word(c: Dictionary) -> String:
	var r := int(c.get("rep", 40))
	if r >= 75:
		return "Big name"
	if r >= 55:
		return "Well regarded"
	if r >= 35:
		return "Respected"
	return "Little known"


static func experience_word(c: Dictionary, job: String) -> String:
	var held := CoachMarket.held_level(c)
	var lv := CoachMarket.level(job)
	if held >= lv:
		return "Has done the job"
	if held == lv - 1:
		return "Ready to step up"
	return "New to this level"


## His match-day tendency, kept on his record ("style") once it is first
## read, so it never changes with his ratings or a reload. A coach with no
## style yet (a new record, or a save from before styles) gets one from his
## id: STYLE_SHARP tactics or better is balanced; otherwise one of STYLES by
## a fixed hash of his id, a man-manager (manage 80+) sitting on a lead
## rather than flipping between plans.
static func style(c: Dictionary) -> String:
	var s := str(c.get("style", ""))
	if STYLES.has(s):
		return s
	s = style_of(c)
	c["style"] = s
	return s


## The style `style` would give him, without writing it on his record: for a
## screen read before his first match (a rival coach read, RivalRead).
static func style_of(c: Dictionary) -> String:
	var s := str(c.get("style", ""))
	if STYLES.has(s):
		return s
	var sk: Dictionary = c.get("skills", {})
	if int(sk.get("tactics", 0)) >= STYLE_SHARP:
		s = "balanced"
	else:
		var h := 0
		for ch in str(c.get("cid", "")).to_utf8_buffer():
			h = (h * 31 + int(ch)) % 1000003
		s = str(STYLES[h % STYLES.size()])
		if s == "reactive" and int(sk.get("manage", 0)) >= 80:
			s = "cautious"
	return s


## A club's staff: job -> cid, read from the records.
static func staff(coaches: Dictionary, club: String) -> Dictionary:
	var out := {}
	for cid in coaches:
		var c: Dictionary = coaches[cid]
		if str(c.get("status", "")) == "club" and str(c.get("club", "")) == club:
			out[str(c["job"])] = str(cid)
	return out


## Where he is now, in words: "Forwards coach, Carlton", "Available", ...
static func whereabouts(c: Dictionary) -> String:
	match str(c.get("status", "")):
		"club":
			var job := str(c.get("job", ""))
			var label := str(JOB_LABEL.get(job, job))
			if job != "SC" and job != "SA":
				label += " coach"
			return "%s, %s" % [label, GameDB.club_name(str(c.get("club", "")))]
		"free":
			return "Available"
		"out":
			return str(c.get("note", "")) if str(c.get("note", "")) != "" \
					else "Unavailable until %d" % int(c.get("free_from", 0))
		_:
			return str(c.get("note", "Working outside AFL coaching"))


## The Round 1 2026 coaching world for a career at `my_club`: every seeded
## coach, with that club's real senior coach moved out of the job you now
## hold. Deterministic: the same seed file gives the same records and names.
static func seed(my_club: String) -> Dictionary:
	# A past start (Legacy mode) reads its own season's staff: the real senior
	# coaches, yours making way (director 2026-11-13, "You replace him").
	var file := str(GameDB.COACHES_CSV)
	if file != "" and file != SEED_CSV:
		return seed_era(my_club, file, int(GameDB.START_YEAR))
	var rows := _read_seed()
	var names := _alias_pool()
	var out := {}
	for i in range(rows.size()):
		var r: Dictionary = rows[i]
		var cid := str(r["cid"])
		var status := str(r["status"])
		var club := str(r["club"])
		var job := str(r["job"])
		var c := {
			"cid": cid,
			"real_name": str(r["name"]),
			"generic_name": str(names[i % names.size()]),
			"former_player_id": "",
			"skills": {"teach": int(r["teach"]), "tactics": int(r["tactics"]),
					"manage": int(r["manage"])},
			"spec": str(r["spec"]),
			"status": status,
			"club": club,
			"job": job,
			"free_from": int(r["free_from"]),
			"stints": [],
			"former_sc": int(r["former_sc"]) == 1,
			"note": str(r["note"]),
			"origin": str(r["origin"]),
			"played": {},
		}
		if status == "club":
			(c["stints"] as Array).append([club, job, SEED_YEAR, 0])
		# You are this club's senior coach: the real one is free to be hired.
		if status == "club" and club == my_club and job == "SC":
			c["status"] = "free"
			c["club"] = ""
			c["job"] = ""
			c["former_sc"] = true
			c["stints"] = [[club, "SC", SEED_YEAR, SEED_YEAR]]
			c["note"] = ""
		out[cid] = c
	return out


# ---------------------------------------------------------------------------
# A past season's staff (Legacy mode, TODO row 142 L2)
# ---------------------------------------------------------------------------
## A past season's file names each club's senior coach and its reserves and
## under-19s coaches (data/legacy/1990s/coaches_1990.csv), not the six jobs.
## Every real senior coach starts at the 2026 senior coaches' average, so no
## real coach is rated better or worse than another on a guess; a rating from
## each man's record is the director's call to make later.
const ERA_SC_SKILLS := {"teach": 72, "tactics": 78, "manage": 79}
## A reserves or under-19s coach: new to the senior jobs, at the pathway's centre.
const ERA_SECOND_SKILLS := {"teach": 62, "tactics": 62, "manage": 62}
const ERA_SECOND_ROLES := {"reserves": "Reserves coach", "under_19s": "Under-19s coach",
		"reserves_and_under_19s": "Reserves and under-19s coach"}


## The coaching world of a past season `year` for a career at `my_club`: each
## club's real senior coach in his job, except yours: you replace him, and he
## joins the pool any club may hire from (director 2026-11-13, "You replace
## him", "Joins the coach pool"). The reserves and under-19s coaches are
## working outside the senior jobs and can be hired; the five assistant jobs
## the file does not name are filled by new coaches, as a new club's are.
static func seed_era(my_club: String, path: String, year: int) -> Dictionary:
	var names := _alias_pool()
	var out := {}
	var i := 0
	for r in _read_seed(path):
		var role := str(r.get("role", ""))
		var club := str(GameDB.CLUB_CODE_ALIASES.get(str(r.get("club", "")), str(r.get("club", ""))))
		var real := str(r.get("name", "")).strip_edges()
		if real == "" or (role != "senior" and not ERA_SECOND_ROLES.has(role)):
			continue
		var cid := "C_" + real.to_lower().replace(" ", "_").replace("'", "").replace(".", "")
		if out.has(cid):
			continue
		var c := {
			"cid": cid, "real_name": real,
			"generic_name": str(names[i % names.size()]),
			"former_player_id": "",
			"skills": (ERA_SC_SKILLS if role == "senior" else ERA_SECOND_SKILLS).duplicate(),
			"spec": "" if role == "senior" else "DEV",
			"status": "away", "club": "", "job": "", "free_from": 0, "stints": [],
			"former_sc": role == "senior", "note": "", "origin": "seed", "played": {},
		}
		i += 1
		if role == "senior" and club != my_club:
			c["status"] = "club"
			c["club"] = club
			c["job"] = "SC"
			(c["stints"] as Array).append([club, "SC", year, 0])
		elif role == "senior":
			# Yours: he makes way and is free to be hired.
			c["status"] = "free"
		else:
			c["note"] = "%s, %s" % [ERA_SECOND_ROLES[role], GameDB.club_name(club)]
		out[cid] = c
	# The jobs the file does not name, at every club of the season.
	CoachMarket.fill_with_new(out, GameDB.active_clubs(year), my_club, year - 1, COACH_NAME_SEED)
	return out


static func _read_seed(path := SEED_CSV) -> Array:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_warning("Coaches: cannot read %s" % path)
		return []
	var header := f.get_csv_line()
	var out := []
	while not f.eof_reached():
		var cells := f.get_csv_line()
		if cells.size() < header.size():
			continue
		var r := {}
		for j in range(header.size()):
			r[str(header[j])] = cells[j]
		out.append(r)
	return out


## Every coach alias, in a fixed shuffled order: coach first names with the
## players' surnames. Fixed seed, so a seeded coach's alias never changes.
static func _alias_pool() -> Array:
	var pool := []
	for first in COACH_FIRST_NAMES:
		for last in GameDB.FICTIONAL_LAST_NAMES:
			pool.append("%s %s" % [first, last])
	var rng := RandomNumberGenerator.new()
	rng.seed = COACH_NAME_SEED
	for i in range(pool.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var swap = pool[i]
		pool[i] = pool[j]
		pool[j] = swap
	return pool
