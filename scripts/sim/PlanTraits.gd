class_name PlanTraits
extends RefCounted
## Game-plan traits (director, 2026-11-10): your club may run one, or none. Each
## has one strength and one matched cost, both on a match lever that already
## exists (MatchSim._gt). The director's own example set the form: "accuracy is
## 15% higher in the last quarter, give up 5% more momentum".
##
## Sizes are the director's first guesses, not tuned: "we will balance test them
## vigorously later, for now just build and ship" (TODO section Z). Every size
## is a named const so the balance pass can find it.
##
## Rival clubs run none (they keep their usual plan only).

const IDS := ["fortress", "kick_mark", "cluster", "stoppage_kings", "fast_starters",
		"chaos_ball", "hard_trainers", "long_bombers", "front_runners", "never_say_die"]

const NAME := {
	"fortress": "Fortress", "kick_mark": "Kick-Mark Masters", "cluster": "The Cluster",
	"stoppage_kings": "Stoppage Kings", "fast_starters": "Fast Starters",
	"chaos_ball": "Chaos Ball", "hard_trainers": "Hard Trainers",
	"long_bombers": "Long Bombers", "front_runners": "Front-Runners",
	"never_say_die": "Never Say Die",
}

## The sizes (first guesses, director 2026-11-10).
const FORTRESS_OPP_GOAL := 0.92        # their shots: 8% less often a goal
const FORTRESS_GAIN := 0.94            # your disposals: 6% fewer metres
const KICK_MARK_CLANGERS := 0.85       # 15% fewer clangers
const KICK_MARK_STOPPAGE := -0.03      # 3 points off your stoppage win chance
const CLUSTER_MID_PRESS := 1.15        # 15% more pressure through the middle third
const CLUSTER_BROKEN := 1.20           # a chain that breaks out of its back third: 20% likelier a goal
const STOPPAGE_KINGS_STOPPAGE := 0.03  # 3 points on your stoppage win chance
const STOPPAGE_KINGS_EXPOSED := 1.05   # their shots: 5% more often a goal
const FAST_STARTERS_GOAL := 1.08       # Q1: your shots 8% more often a goal
const FAST_STARTERS_STOPPAGE := 0.02   # Q1: 2 points on your stoppage win chance
const FAST_STARTERS_LEGS := 1.10       # Q4: legs go 10% quicker
const CHAOS_TURNOVER := 1.20           # a rushed kick in your forward third: 20% likelier to turn over
const CHAOS_CLANGERS := 1.12           # 12% more clangers
const HARD_TRAINERS_LEGS := 0.90       # legs go 10% slower
const HARD_TRAINERS_INJ := 1.15        # 15% more injuries
const LONG_BOMBERS_RANGE := 8.0        # metres on every kick's reach
const LONG_BOMBERS_ICEPT := 1.15       # their intercept marks off your kicks: 15% more often
const FRONT_RUNNERS_MOMENTUM := 1.25   # the run of play's edge, 25% stronger when 25+ points up
const FRONT_RUNNERS_PEP := 0.5         # Fire them up's lift while chasing: halved
const NEVER_SAY_DIE_PEP := 1.5         # Fire them up's lift while chasing: half again
const NEVER_SAY_DIE_OPP_GOAL := 1.05   # while you lead, their shots: 5% more often a goal

## Each trait's levers (MatchSim._gt keys) as [size, gate]. Gates: "" always,
## "q1" first quarter, "q4" last quarter (and extra time), "lead" while the side
## leads, "lead_big" while it leads by more than MatchSim.runaway_lead.
##   opp_goal, exposed: their shots' goal chance (x)   gain: metres a disposal (x)
##   clangers (x)   stoppage: stoppage win chance (+)   mid_press: pressure they
##   meet in the middle third (x)   broken: their goal chance after breaking out
##   of their back third unpressured (x)   goal: your shots' goal chance (x)
##   legs: how fast legs drain (x)   fwd_turnover: a rushed disposal in your
##   forward third turning over (x)   inj: injury chance (x)   range: kick reach
##   (+ m)   icept: their intercept marks off your kicks (x)   momentum: the run
##   of play's edge while it is yours (x)   pep: Fire them up's lift (x)
const LEVERS := {
	"fortress": {"opp_goal": [FORTRESS_OPP_GOAL, ""], "gain": [FORTRESS_GAIN, ""]},
	"kick_mark": {"clangers": [KICK_MARK_CLANGERS, ""], "stoppage": [KICK_MARK_STOPPAGE, ""]},
	"cluster": {"mid_press": [CLUSTER_MID_PRESS, ""], "broken": [CLUSTER_BROKEN, ""]},
	"stoppage_kings": {"stoppage": [STOPPAGE_KINGS_STOPPAGE, ""], "exposed": [STOPPAGE_KINGS_EXPOSED, ""]},
	"fast_starters": {"goal": [FAST_STARTERS_GOAL, "q1"], "stoppage": [FAST_STARTERS_STOPPAGE, "q1"],
			"legs": [FAST_STARTERS_LEGS, "q4"]},
	"chaos_ball": {"fwd_turnover": [CHAOS_TURNOVER, ""], "clangers": [CHAOS_CLANGERS, ""]},
	"hard_trainers": {"legs": [HARD_TRAINERS_LEGS, ""], "inj": [HARD_TRAINERS_INJ, ""]},
	"long_bombers": {"range": [LONG_BOMBERS_RANGE, ""], "icept": [LONG_BOMBERS_ICEPT, ""]},
	"front_runners": {"momentum": [FRONT_RUNNERS_MOMENTUM, "lead_big"], "pep": [FRONT_RUNNERS_PEP, ""]},
	"never_say_die": {"pep": [NEVER_SAY_DIE_PEP, ""], "opp_goal": [NEVER_SAY_DIE_OPP_GOAL, "lead"]},
}

## What each trait does for you and what it costs, in football words, with the
## size. Never which is better: every one has both.
const UPSIDE := {
	"fortress": "Their shots go through 8% less often.",
	"kick_mark": "15% fewer clangers.",
	"cluster": "15% more pressure on them through the middle.",
	"stoppage_kings": "Your stoppage win chance is 3 points higher.",
	"fast_starters": "First quarter: your shots go through 8% more often and your stoppage win chance is 2 points higher.",
	"chaos_ball": "Your forwards' pressure turns their rushed kicks over 20% more often.",
	"hard_trainers": "Legs last 10% longer.",
	"long_bombers": "Every kick reaches 8 metres further.",
	"front_runners": "More than 24 points up, the run of play counts 25% more for you.",
	"never_say_die": "Behind, Fire them up lifts you at the contest 50% more.",
}
const COST := {
	"fortress": "Your disposals gain 6% less ground.",
	"kick_mark": "Your stoppage win chance is 3 points lower.",
	"cluster": "When they get out of their back third with nobody on them, that chain goes through 20% more often.",
	"stoppage_kings": "Their shots go through 5% more often.",
	"fast_starters": "Last quarter: legs go 10% quicker.",
	"chaos_ball": "12% more of your own clangers.",
	"hard_trainers": "15% more injuries.",
	"long_bombers": "They take intercept marks off your kicks 15% more often.",
	"front_runners": "Behind, Fire them up lifts you at the contest half as much.",
	"never_say_die": "While you lead, their shots go through 5% more often.",
}
## What you see on the ground (the oval and the match feed).
const LOOKS := {
	"fortress": "A deep backline; short, sideways chains going forward.",
	"kick_mark": "Uncontested marks in a chain; beaten at the ball-ups.",
	"cluster": "A tight web through the middle; space in their forward line when it breaks.",
	"stoppage_kings": "Mids piling into the ball-ups; a spare man for them on the rebound.",
	"fast_starters": "A sharp first quarter; heavy legs late.",
	"chaos_ball": "A swarm inside your forward 50; more of your own kicks spilled.",
	"hard_trainers": "Legs hold in the last quarter; more players helped off.",
	"long_bombers": "Long kicks into the 50; more of them marked by their defenders.",
	"front_runners": "Goals come in runs when you're well ahead; flat when you're chasing.",
	"never_say_die": "A surge when you're behind; sitting back when you're in front.",
}
## Where a real side played it.
const BASIS := {
	"fortress": "Lyon's St Kilda: the best defence in four seasons.",
	"kick_mark": "Hawthorn 2012-15: kept the ball, lost the contest.",
	"cluster": "Clarkson's 2008 zone, worked out by 2009.",
	"stoppage_kings": "Clearance-heavy midfields that leak on the rebound.",
	"fast_starters": "Sides that jump early and fade.",
	"chaos_ball": "Richmond 2017-20.",
	"hard_trainers": "The big-load pre-seasons.",
	"long_bombers": "Long-kicking corridor sides.",
	"front_runners": "Sides that bank a big lead and fold when chasing.",
	"never_say_die": "The great comebacks.",
}
## Running none.
const NONE_LINE := "No trait: your game plan as written."


static func valid(id: String) -> String:
	return id if LEVERS.has(id) else ""


static func name_of(id: String) -> String:
	return str(NAME.get(id, ""))
