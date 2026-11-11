class_name CustomPlan
extends RefCounted
## Your own game plan (director, 2026-11-12): a sixth plan in How we play,
## beside the five, that the coach builds once by picking exactly one strength
## and one cost from the lists below, and may name. It replaces the plan; it
## never stacks on one.
##
## The director: "a custom gameplan feature, where the player can create their
## own unique gameplan that impacts real stats in the matches. By picking from
## a list of unique positives and negatives"; "the game plan must not be able to
## directly counter another gameplan though. it must be more neutral like
## 'balanced' or more aptly, 'win contest'"; "1 strength, 1 cost".
##
## Neutral: it is in no counter (MatchSim.COUNTER), it never sets off the
## press's side effects, and Controlled Tempo and Attack Corridor treat it as
## any plan with no press. Like any plan, its strength grows or shrinks with
## the coaches' execution, the list (it asks nothing special of a list, like
## Balanced: fit 1.0), how well the club knows it and the weather; its cost
## stays as written (MatchSim._gt).
##
## Every lever is one the match already had (the game-plan traits it
## replaces, split into their strengths and their costs). Each size is a named
## const so a balance pass can find it. A strength and a cost on the same lever
## would cancel out, so they cannot go together (clash).
##
## Every club gets it: some rival coaches build one for the season, picked on
## seeded dice (ai_pick).

const KEY := "custom"
const DEFAULT_NAME := "Our plan"
const NAME_MAX := 22

## The sizes. Strengths (each as written, before the list, the coaches and the
## weather scale it):
const SHARP_GOAL := 1.04          # your shots: 4% more often a goal
const FAST_START_GOAL := 1.12     # Q1: your shots 12% more often a goal
const LATE_GOAL := 1.12           # Q4 (and extra time): your shots 12% more often a goal
const LOCKDOWN_OPP_GOAL := 0.96   # their shots: 4% less often a goal
const CLEAN_CLANGERS := 0.85      # 15% fewer clangers
const STOPPAGE_WIN := 0.03        # 3% better chance at every stoppage
const SQUEEZE_PRESS := 1.07       # 7% more pressure on them through the middle third (15% screened +7.4 margin)
const FIT_LEGS := 0.90            # legs drain 10% slower
const LONG_REACH := 1.10          # every kick reaches 10% further
const FWD_TURNOVER := 1.20        # their rushed kicks in your forward third: 20% likelier to turn over
const FRONT_MOMENTUM := 1.25      # well in front, the run of play's edge 25% stronger
const COMEBACK_PEP := 1.5         # behind, Fire them up's lift half again
## Costs (as written, always):
const SLOW_GAIN := 0.94           # your disposals: 6% less ground
const LOOSE_CLANGERS := 1.12      # 12% more clangers
const STOPPAGE_LOSS := -0.03      # 3% worse chance at every stoppage
const LEAKY_OPP_GOAL := 1.05      # their shots: 5% more often a goal
const LEAD_OPP_GOAL := 1.08       # while you lead, their shots: 8% more often a goal
const BREAK_GOAL := 1.20          # a chain of theirs that breaks out of its back third unpressured: 20% likelier a goal
const LATE_LEGS := 1.10           # Q4: legs drain 10% quicker
const INJ := 1.15                 # 15% more injuries
const READ_ICEPT := 1.15          # their intercept marks off your kicks: 15% more often
const FLAT_PEP := 0.5             # behind, Fire them up's lift halved

## Each entry: its name, its lever (a MatchSim._gt key), the size, the gate
## ("" always, "q1" first quarter, "q4" last quarter and extra time, "lead"
## while the side leads, "lead_big" while it leads by more than
## MatchSim.RUNAWAY_LEAD), whether the size is added (a share of a chance) or
## multiplied, and its line: the size goes in at %s, in football words.
##   goal: your shots' goal chance   opp_goal: theirs   clangers   stoppage:
##   stoppage win chance   mid_press: pressure they meet in the middle third
##   legs: how fast legs drain   reach: how far a kick goes   fwd_turnover: a
##   rushed disposal of theirs in your forward third turning over   momentum:
##   the run of play's edge while it is yours   pep: Fire them up's lift
##   gain: metres a disposal   broken: their goal chance after breaking out of
##   their back third unpressured   inj: injury chance   icept: their
##   intercept marks off your kicks
const STRENGTHS := {
	"sharp": {"name": "Sharp shooting", "lever": "goal", "size": SHARP_GOAL, "gate": "",
			"line": "Your shots go through %s more often."},
	"fast_start": {"name": "Fast starters", "lever": "goal", "size": FAST_START_GOAL, "gate": "q1",
			"line": "First quarter: your shots go through %s more often."},
	"late": {"name": "Strong finish", "lever": "goal", "size": LATE_GOAL, "gate": "q4",
			"line": "Last quarter: your shots go through %s more often."},
	"lockdown": {"name": "Lock the door", "lever": "opp_goal", "size": LOCKDOWN_OPP_GOAL, "gate": "",
			"line": "Their shots go through %s less often."},
	"clean": {"name": "Clean hands", "lever": "clangers", "size": CLEAN_CLANGERS, "gate": "",
			"line": "%s fewer of your own clangers."},
	"stoppage": {"name": "Stoppage numbers", "lever": "stoppage", "size": STOPPAGE_WIN, "gate": "", "add": true,
			"line": "A %s better chance at every stoppage."},
	"squeeze": {"name": "Midfield squeeze", "lever": "mid_press", "size": SQUEEZE_PRESS, "gate": "",
			"line": "%s more pressure on them through the middle."},
	"fitness": {"name": "Fitness base", "lever": "legs", "size": FIT_LEGS, "gate": "",
			"line": "Legs last %s longer."},
	"long": {"name": "Long kicking", "lever": "reach", "size": LONG_REACH, "gate": "",
			"line": "Every kick reaches %s further."},
	"fwd_press": {"name": "Forward pressure", "lever": "fwd_turnover", "size": FWD_TURNOVER, "gate": "",
			"line": "Your forwards turn their rushed kicks over %s more often."},
	"front": {"name": "Front-runners", "lever": "momentum", "size": FRONT_MOMENTUM, "gate": "lead_big",
			"line": "More than %d points up, the run of play counts %s more for you."},
	"comeback": {"name": "Never say die", "lever": "pep", "size": COMEBACK_PEP, "gate": "",
			"line": "Behind, Fire them up lifts you at the contest %s more."},
}
const COSTS := {
	"slow": {"name": "Slow ball", "lever": "gain", "size": SLOW_GAIN, "gate": "",
			"line": "Your disposals gain %s less ground."},
	"loose": {"name": "Loose hands", "lever": "clangers", "size": LOOSE_CLANGERS, "gate": "",
			"line": "%s more of your own clangers."},
	"stoppage": {"name": "Light at stoppages", "lever": "stoppage", "size": STOPPAGE_LOSS, "gate": "", "add": true,
			"line": "A %s worse chance at every stoppage."},
	"leaky": {"name": "Open at the back", "lever": "opp_goal", "size": LEAKY_OPP_GOAL, "gate": "",
			"line": "Their shots go through %s more often."},
	"sit": {"name": "Sit on a lead", "lever": "opp_goal", "size": LEAD_OPP_GOAL, "gate": "lead",
			"line": "While you lead, their shots go through %s more often."},
	"break": {"name": "Open on the break", "lever": "broken", "size": BREAK_GOAL, "gate": "",
			"line": "When they get out of their back third with nobody on them, that chain goes through %s more often."},
	"fade": {"name": "Fade late", "lever": "legs", "size": LATE_LEGS, "gate": "q4",
			"line": "Last quarter: legs go %s quicker."},
	"injuries": {"name": "Injury toll", "lever": "inj", "size": INJ, "gate": "",
			"line": "%s more injuries."},
	"read": {"name": "Kicks get read", "lever": "icept", "size": READ_ICEPT, "gate": "",
			"line": "They take intercept marks off your kicks %s more often."},
	"flat": {"name": "Drop their heads", "lever": "pep", "size": FLAT_PEP, "gate": "",
			"line": "Behind, Fire them up lifts you at the contest %s less."},
}
## The order the lists show in.
const STRENGTH_IDS := ["sharp", "fast_start", "late", "lockdown", "clean", "stoppage",
		"squeeze", "fitness", "long", "fwd_press", "front", "comeback"]
const COST_IDS := ["slow", "loose", "stoppage", "leaky", "sit", "break", "fade",
		"injuries", "read", "flat"]

## The share of rival coaches who build a plan of their own for a season.
const AI_SHARE := 0.25


## A plan as saved: {"name", "s", "c"}, cleaned. A pick that is not on the
## list, or a pair that clashes, is dropped ("").
static func clean(plan) -> Dictionary:
	if not (plan is Dictionary):
		return {}
	var s := str((plan as Dictionary).get("s", ""))
	var c := str((plan as Dictionary).get("c", ""))
	if not STRENGTHS.has(s):
		s = ""
	if not COSTS.has(c):
		c = ""
	if s != "" and c != "" and clash(s, c):
		c = ""
	var nm := name_clean(str((plan as Dictionary).get("name", "")))
	if s == "" and c == "" and nm == "":
		return {}
	return {"name": nm, "s": s, "c": c}


## A name as kept: trimmed, at most NAME_MAX characters ("" = the default).
static func name_clean(nm: String) -> String:
	return nm.strip_edges().left(NAME_MAX).strip_edges()


## Built: one strength and one cost that go together.
static func ready(plan) -> bool:
	var p := clean(plan)
	return not p.is_empty() and str(p["s"]) != "" and str(p["c"]) != ""


## The plan's name: the coach's own, or DEFAULT_NAME.
static func name_of(plan) -> String:
	var nm := name_clean(str((plan as Dictionary).get("name", ""))) if plan is Dictionary else ""
	return nm if nm != "" else DEFAULT_NAME


## A strength and a cost on the same lever cancel out: they cannot go together.
static func clash(s: String, c: String) -> bool:
	if not STRENGTHS.has(s) or not COSTS.has(c):
		return false
	return str(STRENGTHS[s]["lever"]) == str(COSTS[c]["lever"])


static func entry(id: String, strength: bool) -> Dictionary:
	return (STRENGTHS if strength else COSTS).get(id, {})


## An entry's share: what it moves, as a fraction (0.04 for 4%).
static func share(e: Dictionary) -> float:
	if e.is_empty():
		return 0.0
	var v := float(e["size"])
	return absf(v) if bool(e.get("add", false)) else absf(v - 1.0)


## An entry's line with its size, `scale` times the written share (a
## strength's for this list today; a cost always 1.0).
static func line(id: String, strength: bool, scale := 1.0) -> String:
	var e := entry(id, strength)
	if e.is_empty():
		return ""
	var p := GateOdds.pct(share(e) * scale)
	var t := str(e["line"])
	if str(e["gate"]) == "lead_big":
		return t % [int(MatchSim.RUNAWAY_LEAD), p]
	return t % p


## A built plan's [gain, cost] as clauses for a gate ("Gain: %s"): the
## strength at `up` times its written size (MatchSim.upside_scale), the cost
## as written. [] when not built.
static func texts(plan, up := 1.0) -> Array:
	if not ready(plan):
		return []
	var p := clean(plan)
	return [clause(line(str(p["s"]), true, up)), clause(line(str(p["c"]), false))]


## A line as a clause: no full stop, a small first letter.
static func clause(s: String) -> String:
	s = s.trim_suffix(".")
	return s.left(1).to_lower() + s.substr(1)


## The lever value `e` puts on `key`, `scale` times its written move: `d`
## when it pulls another lever.
static func lever(e: Dictionary, key: String, d: float, scale := 1.0) -> float:
	if e.is_empty() or str(e["lever"]) != key:
		return d
	var v := float(e["size"])
	if bool(e.get("add", false)):
		return v * scale
	return 1.0 + (v - 1.0) * scale


## Whether a rival club's coach builds a plan of his own this season: seeded
## on the club and the year, so the same career always gives the same answer.
static func ai_builds(code: String, year: int) -> bool:
	var r := RandomNumberGenerator.new()
	r.seed = hash("custom_plan|%s|%d" % [code, year])
	return r.randf() < AI_SHARE


## The plan a rival club's coach builds: a strength, then a cost that goes
## with it, on seeded dice. Named for the club's own plan.
static func ai_pick(code: String, year: int) -> Dictionary:
	var r := RandomNumberGenerator.new()
	r.seed = hash("custom_pick|%s|%d" % [code, year])
	var s := str(STRENGTH_IDS[r.randi_range(0, STRENGTH_IDS.size() - 1)])
	var costs := COST_IDS.filter(func(c): return not clash(s, str(c)))
	var c := str(costs[r.randi_range(0, costs.size() - 1)])
	return {"name": "", "s": s, "c": c}


## A rival's plan as the coach scouting them reads it, by name, with no
## numbers (the Assistant's report carries none, tests/test_rival_read.gd; the
## sizes are on the plan list).
static func rival_line(plan) -> String:
	if not ready(plan):
		return ""
	var p := clean(plan)
	return "Their usual game is a plan of their own: %s, at the cost of %s." % [
			str(STRENGTHS[p["s"]]["name"]).to_lower(), str(COSTS[p["c"]]["name"]).to_lower()]
