class_name GateOdds
extends RefCounted
## What each match-day call does for you and what it costs, with the size as a
## percentage, in football words (bible §4, director 2026-10-18: "full
## transparency behind each decision and the impact it will have"; "both
## options carrying positives and negatives"). Every figure is worked out from
## the constant the sim itself uses; no template here holds a number of its
## own (tests/run_matchup_tests.gd, _gate_odds). Nothing here says which
## option is better.

const GAIN := "Gain: %s"
const COST := "Cost: %s"

# Who tags (the pre-bounce and break sheets).
const TAG_GIVES := "%s of his own ball and contest work"
const TAG_NOTE := "%s tags %s: he gives up %s of his own game."
# The call when their midfielder is kicking a bag.
const TAG_HOT_GAIN := "%s keeps %s of his ball with %s on him, until you call it off"
const TAG_HOT_COST := "%s gives up %s"
const TAG_LEAVE_GAIN := "your midfielders play their own game"
const TAG_LEAVE_COST := "%s keeps all of his ball"

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
	return Roles.tag_keep(tagger, legs)


## The line under the tag call: the cost, whoever goes (each man's hold is on
## his own card, MatchNotes.tagger_card).
static func tag_note(who_name: String, target_name: String) -> String:
	return TAG_NOTE % [who_name, target_name, tag_gives_pct()]


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
