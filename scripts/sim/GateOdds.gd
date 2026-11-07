class_name GateOdds
extends RefCounted
## What each match-day call does for you and what it costs, with the size as a
## percentage, in football words (bible §4, director 2026-10-18: "full
## transparency behind each decision and the impact it will have"; "both
## options carrying positives and negatives"). Every figure is worked out from
## the constant the sim itself uses; no template here holds a number of its
## own (tests/run_matchup_tests.gd, _gate_odds). Nothing here says which
## option is better. A plan's gain is as written, for a list that suits it.

const GAIN := "Gain: %s"
const COST := "Cost: %s"

# The hub's options beside an opposition fact (FactOptions).
const TAG_GAIN := "%s keeps %s of his ball on a Tagger, %s on anyone else"
## Who the tag gain is about when the fact names nobody (a midfield fact).
const TAG_TARGET_ANY := "the man you tag"
const TAG_COST := "your tagger gives up %s of his own ball and contest work"
const MINDER_GAIN := "their loose man reaches %s of his contests, %s with a Defensive forward"
const MINDER_COST := "your forward is a target %s less often"
const LOOSE_GAIN := "a top reader gets to %s of their entries"
const LOOSE_COST := "your loose defender leaves his man on %s of entries, and space opens if he is late"
const PLAN_GAIN := {
	"attacking": "shots %s more accurate, %s more ground a kick",
	"defensive": "%s more pressure where they start, their shots %s less accurate",
	"contest": "a %s better chance at every stoppage",
	"controlled": "%s fewer clangers, %s less pressure felt, legs %s fresher",
}
const PLAN_COST := {
	"attacking": "%s more clangers, legs tire %s faster, their shots %s more accurate",
	"defensive": "your shots %s less accurate, legs tire %s faster, %s less pressure in your back third",
	"contest": "%s less ground a kick, their shots %s more accurate",
	"controlled": "%s less ground a kick",
}

# Who tags (the pre-bounce and break sheets).
const TAG_GIVES := "%s of his own ball and contest work"
const TAG_NOTE := "%s tags %s: he gives up %s of his own game."

# Skip to full time.
const SKIP_FIRST := "Skip plays the match on the plan you took in, no tag, no talk. Nothing changed here is kept; every call in the match takes 'no change'."
const SKIP_LATER := "Skip plays the rest on last quarter's calls and talk. Nothing changed here is kept; every call in the match takes 'no change'."

# The in-match risk cards.
const BURST_GAIN := {
	"surge": "a %s better chance at every contest, your shots %s more accurate",
	"hold": "%s fewer clangers, %s less pressure felt, their shots %s less accurate",
	"stack": "a %s better chance at each centre bounce (never above %s)",
	"flood": "their shots %s less accurate",
}
const BURST_COST := {
	"surge": "their shots %s more accurate, legs tire %s faster",
	"hold": "your shots %s less accurate, %s less ground a kick",
	"stack": "their shots %s more accurate meanwhile",
	"flood": "your shots %s less accurate, %s less ground a kick",
}
const FOR_MINUTES := ", for about %d minutes"
const TO_SIREN := ", to the final siren"
const TO_BREAK := ", to the break"
const NONE_GAIN := "no extra risk at either end"
const NONE_COST_RUN := "their run goes on at the current odds"
const NONE_COST_BOUNCE := "no extra edge at the bounce or behind the ball"


static func pct(share: float) -> String:
	return Conditioning.pct(absf(share))


static func gain(s: String) -> String:
	return GAIN % s


static func cost(s: String) -> String:
	return COST % s


static func _plan_v(plan: String, key: String, fallback := 1.0) -> float:
	return float((MatchSim.PLANS.get(plan, {}) as Dictionary).get(key, fallback))


## A plan's gain and cost as written: [gain, cost] ("" when it has none here).
static func plan_lines(plan: String) -> Array:
	var v := func(k: String) -> float: return _plan_v(plan, k) - 1.0
	match plan:
		"attacking":
			return [PLAN_GAIN[plan] % [pct(v.call("goal")), pct(v.call("gain"))],
					PLAN_COST[plan] % [pct(v.call("clangers")), pct(v.call("pace")), pct(v.call("exposed"))]]
		"defensive":
			var zone: Array = MatchSim.PRESS_PLAN_ZONE
			return [PLAN_GAIN[plan] % [pct(float(zone[0]) - 1.0), pct(v.call("opp_goal"))],
					PLAN_COST[plan] % [pct(v.call("goal")), pct(v.call("pace")), pct(1.0 - float(zone[2]))]]
		"contest":
			return [PLAN_GAIN[plan] % pct(_plan_v(plan, "contest", 0.0)),
					PLAN_COST[plan] % [pct(v.call("gain")), pct(v.call("exposed"))]]
		"controlled":
			return [PLAN_GAIN[plan] % [pct(v.call("clangers")), pct(v.call("taken")), pct(v.call("pace"))],
					PLAN_COST[plan] % pct(v.call("gain"))]
	return ["", ""]


## The tag's [gain, cost]; `target` names the man tagged (their player the
## fact is about), or "" when the fact names nobody.
static func tag_lines(target := "") -> Array:
	var who := target if target != "" else TAG_TARGET_ANY
	return [TAG_GAIN % [who, pct(Roles.TAG_WITH_TAGGER), pct(Roles.TAG_PLAIN)], TAG_COST % tag_gives_pct()]


## The share of his own game a tagger gives up: his contest worth
## (TAGGER_COST) and his ball (1 - TAGGER_BALL), one figure when they agree.
static func tag_gives_pct() -> String:
	var contest := pct(MatchSim.TAGGER_COST)
	var ball := pct(1.0 - MatchSim.TAGGER_BALL)
	return contest if contest == ball else "%s of his ball and %s" % [ball, contest]


static func tag_gives() -> String:
	return TAG_GIVES % tag_gives_pct()


## What the man on him keeps with `tagger` on him at `legs` (MatchSim._tag_share).
static func tag_kept(tagger: Dictionary, legs: float) -> float:
	return Roles.TAG_PLAIN - (Roles.TAG_PLAIN - Roles.TAG_WITH_TAGGER) * MatchSim.tag_hold(tagger, legs)


## The line under the tag call: the cost, whoever goes (each man's hold is on
## his own card, MatchNotes.tagger_card).
static func tag_note(who_name: String, target_name: String) -> String:
	return TAG_NOTE % [who_name, target_name, tag_gives_pct()]


static func minder_lines() -> Array:
	var roam: Dictionary = MatchSim.MINDER_ROAM
	return [MINDER_GAIN % [pct(float(roam["other"])), pct(float(roam["specialist"]))],
			MINDER_COST % pct(1.0 - float(MatchSim.MINDER_INVOLVE))]


static func loose_lines() -> Array:
	var reach := MatchSim.ROAM_REACH if MatchSim.zone_intercepts else 1.0
	return [LOOSE_GAIN % pct((MatchSim.LOOSE_REACH_MIN + MatchSim.LOOSE_REACH_RANGE) * reach),
			LOOSE_COST % pct(MatchSim.LOOSE_GO * reach)]


static func skip_line(q: int) -> String:
	return SKIP_FIRST if q <= 1 else SKIP_LATER


## How long a burst lasts: every call ends at the break, so one that outlasts
## the quarter runs to the break (the siren in the last quarter).
static func burst_time(kind: String, minutes_left: int, last := true) -> String:
	var chains := int((MatchSim.BURSTS.get(kind, {}) as Dictionary).get("chains", 0))
	var mins := roundi(float(chains) * float(MatchSim.GAME_MINUTES) / float(Ratings.T["chains_per_game"]))
	if minutes_left >= 0 and mins >= minutes_left:
		return TO_SIREN if last else TO_BREAK
	return FOR_MINUTES % mins


static func burst_lines(kind: String, minutes_left := -1, last := true) -> Array:
	var t := burst_time(kind, minutes_left, last)
	match kind:
		"surge":
			return [BURST_GAIN[kind] % [pct(MatchSim.SURGE_CONTEST), pct(MatchSim.SURGE_GOAL - 1.0)] + t,
					BURST_COST[kind] % [pct(MatchSim.SURGE_OPP_GOAL - 1.0), pct(MatchSim.SURGE_PACE - 1.0)]]
		"hold":
			return [BURST_GAIN[kind] % [pct(1.0 - MatchSim.HOLD_CLANGERS), pct(1.0 - MatchSim.HOLD_TAKEN),
					pct(1.0 - MatchSim.HOLD_OPP_GOAL)] + t,
					BURST_COST[kind] % [pct(1.0 - MatchSim.HOLD_GOAL), pct(1.0 - MatchSim.BACK_GAIN)]]
		"stack":
			return [BURST_GAIN[kind] % [pct(MatchSim.STACK_CONTEST), pct(float(Ratings.T["contest_clamp"]))] + t,
					BURST_COST[kind] % pct(MatchSim.STACK_OPP_GOAL - 1.0)]
		"flood":
			return [BURST_GAIN[kind] % pct(1.0 - MatchSim.FLOOD_OPP_GOAL) + t,
					BURST_COST[kind] % [pct(1.0 - MatchSim.FLOOD_GOAL), pct(1.0 - MatchSim.BACK_GAIN)]]
	return ["", ""]
