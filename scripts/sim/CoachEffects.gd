class_name CoachEffects
extends RefCounted
## What the coaching staff does on the field (Coaching Phase 5). Three small,
## capped modifiers, all read straight from the coach records - nothing is
## stored, so older saves need nothing:
##
##   Teaching        -> match XP (the one place XP is paid, GameState._grant_xp)
##   Tactics         -> how well a game plan is executed, and how sharply an
##                      AI club reads the match when it picks its plan
##   Man-management  -> how much being left out hurts a player's morale
##
## Each works from the coaches in the jobs that fit it, not one staff total:
## the forwards coach teaches the forwards, the development coach the kids
## and the reserves. A coach's skill is centred on 70 (a Good coach adds
## nothing); a vacant job counts as a weak one.

## Skill -> -0.75 .. +1.0 around a Good (70) coach.
static func level(v: float) -> float:
	return clampf((v - 70.0) / 20.0, -0.75, 1.0)


const VACANT := 58.0


static func _skill(staff: Dictionary, job: String, key: String) -> float:
	var c: Dictionary = staff.get(job, {})
	return float((c.get("skills", {}) as Dictionary).get(key, VACANT)) if not c.is_empty() else VACANT


static func _fit(staff: Dictionary, job: String) -> float:
	var c: Dictionary = staff.get(job, {})
	return Coaches.role_fit(c, job) if not c.is_empty() else VACANT


## The line coach for a player: midfield & ruck for mids and rucks.
static func line_job(p: Dictionary) -> String:
	match str(p.get("role", "")):
		"FWD":
			return "FWD"
		"DEF":
			return "DEF"
	return "MID"


# ---------------------------------------------------------------------------
# Teaching
# ---------------------------------------------------------------------------
const TEACH_LINE := 0.06     # his line coach, by fit for the job
const TEACH_DEV := 0.05      # the development coach, for kids and the reserves
const TEACH_DEV_OTHER := 0.02
const TEACH_SA := 0.02       # the senior assistant, a little for everyone
const TEACH_MIN := -0.05
const TEACH_MAX := 0.10
const YOUNG := 22.0
## The grade words' cut-offs (Coaches.GRADES); a test holds them equal.
const GOOD_CUT := 68.0
const STRONG_CUT := 78.0

## A teacher's XP level follows his grade word (4.Q1): Fair (under 68) takes
## XP away, Good (68-77) leaves it as it was, Strong (78+) adds. Outside the
## Good band the curve is the usual level().
static func teach_level(v: float) -> float:
	if v >= GOOD_CUT and v < STRONG_CUT:
		return 0.0
	return level(v)

## Multiplier on one player's match XP: 0.95 .. 1.10.
static func xp_mult(staff: Dictionary, p: Dictionary, on_ground: bool) -> float:
	var young := float(p.get("age", 25.0)) <= YOUNG or not on_ground
	var b := TEACH_LINE * teach_level(_fit(staff, line_job(p)))
	b += (TEACH_DEV if young else TEACH_DEV_OTHER) * teach_level(_fit(staff, "DEV"))
	b += TEACH_SA * teach_level(_skill(staff, "SA", "teach"))
	return 1.0 + clampf(b, TEACH_MIN, TEACH_MAX)


## Teaching no longer moves a player's season training ceiling (director,
## 4.Q1, 2026-11-04): "Teaching is XP scaling, not the season-ceiling point."
## Kept as a neutral step so GameState.season_ceiling and old saves need no change.
static func teach_step(_staff: Dictionary, _p: Dictionary) -> int:
	return 0


# ---------------------------------------------------------------------------
# Tactics
# ---------------------------------------------------------------------------
const EXEC_RANGE := 0.25     # a plan's upside scaled 0.81 .. 1.25

## The club's tactical brain: the senior coach and his assistant. At your
## club you are the senior coach, so it is your assistant's.
static func tactics_skill(staff: Dictionary, mine: bool) -> float:
	if mine:
		return _skill(staff, "SA", "tactics")
	return 0.6 * _skill(staff, "SC", "tactics") + 0.4 * _skill(staff, "SA", "tactics")


## {exec, read}: exec scales how much a plan's upside gives (its costs are
## the plan's own);
## read (-0.75 .. 1) is how sharply an AI club reads the match.
static func tactics(staff: Dictionary, mine: bool) -> Dictionary:
	var l := level(tactics_skill(staff, mine))
	return {"exec": 1.0 + EXEC_RANGE * l, "read": l}


## Every club's tactics for the round's matches, derived fresh from the
## records (never saved). Empty outside a career: matches play as before.
static var table := {}


static func set_table(coaches: Dictionary, clubs: Array, my_club: String) -> void:
	table = {}
	var by := staffs(coaches)
	for club in clubs:
		var staff: Dictionary = by.get(club, {})
		# An AI club's senior coach's tendency, kept on his record from now.
		var sc: Dictionary = staff.get("SC", {})
		if club != my_club and not sc.is_empty():
			Coaches.style(sc)
		table[club] = row(staff, club == my_club)
		if club == my_club or not sc.is_empty():
			table[club]["arch_p"] = philosophical(staff, club == my_club)


## The senior coach's Philosophical archetype (row 119) from a club's staff
## (staffs): yours is held in your record; a rival's comes from his own (it
## moves with him). "" for none. Off match day (pre-season training, practice
## matches) read this, not the table: the table is the round's, and a career
## loaded since has none until its next round.
static func philosophical(staff: Dictionary, mine: bool) -> String:
	if mine:
		return str((my_arch.get("held", {}) as Dictionary).get("p", ""))
	var sc: Dictionary = staff.get("SC", {})
	if sc.is_empty():
		return ""
	return Archetypes.rival_philosophical(Coaches.style_of(sc), sc.get("skills", {}))


## One club's row of the table from its staff (staffs), writing nothing on
## the records: {exec, read, ai, assistant, style}. An AI club's senior
## coach's tendency; yours is you.
static func row(staff: Dictionary, mine: bool) -> Dictionary:
	var t := tactics(staff, mine)
	t["ai"] = not mine
	t["assistant"] = mine
	var sc: Dictionary = staff.get("SC", {})
	t["style"] = Coaches.style_of(sc) if not mine and not sc.is_empty() else "balanced"
	return t


## How well each club knows each plan (GameState.plan_known, the same
## dictionary): club -> {plan: fluency}.
static var known := {}

## Each AI club's usual game this season (GameState.rival_plans "usual", the
## same dictionary): club -> plan. Read into the squad (Squad.usual_plan).
static var usual := {}


## Your coach's archetype record (GameState.coach_arch, the same dictionary).
static var my_arch := {}
## Your game-plan trait (GameState.plan_trait, PlanTraits id); rivals run none.
static var my_trait := ""


## A club's senior coach's two archetypes this round: [Strategic, Philosophical]
## ("" for none). A rival's Strategic is the plan his club usually plays.
static func arch_of(code: String) -> Array:
	var t: Dictionary = for_club(code)
	if t.is_empty():
		return ["", ""]
	var s := str(usual.get(code, "")) if bool(t.get("ai", true)) else ""
	var strat := Archetypes.strategic_for_plan(s) if bool(t.get("ai", true)) 			else str((my_arch.get("held", {}) as Dictionary).get("s", ""))
	return [strat, str(t.get("arch_p", ""))]


static func for_club(code: String) -> Dictionary:
	return table.get(code, {})


## The career's relations (GameState.relations, the same dictionary), for each
## club's culture on match day; empty outside a career, and while the culture
## effects are off (an audit's off arm).
static var relations := {}


## Give a match squad its club's tactics and its Togetherness on match day
## (no-op outside a career).
static func apply(sq: Squad) -> void:
	sq.together = Culture.club_effect(relations, sq.code, "match_contest", "together") 			if not relations.is_empty() else 0.0
	apply_row(sq, for_club(sq.code))


## Give a squad one row of tactics (row): apply's, or a screen's own.
static func apply_row(sq: Squad, t: Dictionary) -> void:
	if t.is_empty():
		return
	sq.usual_plan = str(usual.get(sq.code, "")) if bool(t["ai"]) else ""
	sq.plan_know = {}
	var levels: Dictionary = known.get(sq.code, {})
	for plan in levels:
		sq.plan_know[str(plan)] = PreSeason.familiar_mult(float(levels[plan]))
	sq.tactics_exec = float(t["exec"])
	sq.tactics_read = float(t["read"])
	sq.ai_plans = bool(t["ai"])
	sq.assistant = bool(t.get("assistant", false))
	sq.coach_style = str(t.get("style", "balanced"))
	var ids := arch_of(sq.code) if for_club(sq.code) == t else ["", str(t.get("arch_p", ""))]
	sq.arch = Archetypes.levers(str(ids[0]), str(ids[1]))
	sq.plan_trait = "" if bool(t["ai"]) else my_trait
	sq.tactics_exec *= float(sq.arch.get("exec", 1.0))


## club -> {job: record}, in one pass over the records.
static func staffs(coaches: Dictionary) -> Dictionary:
	var out := {}
	for cid in coaches:
		var c: Dictionary = coaches[cid]
		if str(c.get("status", "")) != "club":
			continue
		var club := str(c.get("club", ""))
		if not out.has(club):
			out[club] = {}
		out[club][str(c.get("job", ""))] = c
	return out


# ---------------------------------------------------------------------------
# Man-management
# ---------------------------------------------------------------------------
const SOFTEN_MAX := 0.40

## How much of the morale a left-out player loses is spared: 0 .. 0.40. A
## poor man-manager spares nothing; he never makes anyone unhappier.
static func soften(staff: Dictionary, p: Dictionary) -> float:
	var m := 0.6 * _skill(staff, "SA", "manage") + 0.4 * _skill(staff, line_job(p), "manage")
	return SOFTEN_MAX * clampf((m - 65.0) / 25.0, 0.0, 1.0)


## A morale loss after the man-management softening (never below 0 lost).
static func softened(loss: int, s: float) -> int:
	return int(round(float(loss) * (1.0 - s)))
