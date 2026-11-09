class_name TeamFamiliarity
extends RefCounted
## Team familiarity (TODO row 125, director 2026-11-08 and 2026-11-09): teammates
## play better the longer they play together, so a new arrival has growing pains
## and a heavy list turnover costs the whole side. Not plan fluency
## (PreSeason.familiar_mult) and not "synergy" (the trait synergies).
##
## A player carries "team_fam" (50..100) only while he is short of 100: no key is
## 100, so everyone on a list when a career starts, and every player in an older
## save, is full. "team_fam_kind" is "draftee" for the smaller cut; "team_fam_first"
## marks a man who arrived without a senior game, until he plays one.
##
## Every club lives by this: the cut reaches the match in MatchSim.fit, the same
## place morale does, and GameState ticks it for all clubs after each round.

const FULL := 100.0
const ARRIVE := 50.0
const ROUND_ONE := 70.0
## 70, 75 .. 95, then 100 from game 7. Reserves count half.
const SENIOR_GAME := 5.0
const RESERVES_GAME := 2.5
## Form lost at 70, scaling in a straight line with the shortfall from 100
## (2% at 70 is 3.3% at 50 and one sixth of 2% at 95).
const CLUB_CUT_AT_70 := 0.02
const DRAFTEE_CUT_AT_70 := 0.01
const SHORT_AT_70 := FULL - ROUND_ONE
## New-club men in the selected side at which the team-wide cost starts: a flat
## step, not per extra man. First-gamers and draftees do not count.
const TEAM_ARRIVALS := 4
## The team-wide form cut for a side whose arrivals are at 70, sized with
## tools/balance.sh (--arrivals) to 11 points of margin averaged across Rounds 1-6.
const TEAM_CUT_AT_70 := 0.11
## What that cut measures at 70, in points of margin, for the coach's copy.
const TEAM_POINTS_AT_70 := 19


static func value(p: Dictionary) -> float:
	return float(p.get("team_fam", FULL))


## He moved to a new club: back to the start, at the new-club rate.
static func arrive_club(p: Dictionary, first_gamer := false) -> void:
	p["team_fam"] = ARRIVE
	p.erase("team_fam_kind")
	p.erase("team_fam_first")
	if first_gamer:
		p["team_fam_first"] = true


## He was drafted (or signed out of the state leagues): the smaller cut.
static func arrive_draftee(p: Dictionary) -> void:
	p["team_fam"] = ARRIVE
	p["team_fam_kind"] = "draftee"
	p.erase("team_fam_first")


## The pre-season is done: everyone short of 70 is lifted to it, except a man
## still injured as it ends, who stays where he is until he plays.
static func round_one(list: Array) -> void:
	for p in list:
		if value(p) < ROUND_ONE and int(p.get("injury_weeks", 0)) <= 0:
			p["team_fam"] = ROUND_ONE


## A game played: `senior`, or in the reserves.
static func after_game(p: Dictionary, senior: bool) -> void:
	if senior:
		p.erase("team_fam_first")
	if not p.has("team_fam"):
		return
	var f := value(p) + (SENIOR_GAME if senior else RESERVES_GAME)
	if f >= FULL:
		clear(p)
	else:
		p["team_fam"] = f


static func clear(p: Dictionary) -> void:
	p.erase("team_fam")
	p.erase("team_fam_kind")
	p.erase("team_fam_first")


static func is_draftee(p: Dictionary) -> bool:
	return str(p.get("team_fam_kind", "")) == "draftee"


## What his own familiarity takes off everything he does, as a share (0.02 is 2%).
static func own_cut(p: Dictionary) -> float:
	var rate := DRAFTEE_CUT_AT_70 if is_draftee(p) else CLUB_CUT_AT_70
	return rate * (FULL - value(p)) / SHORT_AT_70 * MatchSim._tv("fam_own", 1.0)


## The men in a selected side who count towards the team-wide cost.
static func new_club_men(side: Array) -> Array:
	var out := []
	for p in side:
		if value(p) < FULL and not is_draftee(p) and not bool(p.get("team_fam_first", false)):
			out.append(p)
	return out


## How far along the fade a group is: 1 with its men at 70, 1/6 at 95, 0 at 100.
## Capped at Round 1's size: a man kept at 50 by injury costs his own form more,
## never the side more than the Round 1 step.
static func _fade(men: Array) -> float:
	if men.is_empty():
		return 0.0
	var short := 0.0
	for p in men:
		short += FULL - value(p)
	return minf(short / float(men.size()) / SHORT_AT_70, 1.0)


## The team-wide form cut for a selected side (ground and bench), 0 under four.
static func team_cut(side: Array) -> float:
	var men := new_club_men(side)
	if men.size() < TEAM_ARRIVALS:
		return 0.0
	return MatchSim._tv("fam_team", TEAM_CUT_AT_70) * _fade(men)


## The whole-game cut each man in a side plays with: id -> share. Empty for a side
## with no arrivals, so a settled list plays exactly as it did.
static func side_cuts(side: Array) -> Dictionary:
	var team := team_cut(side)
	var out := {}
	for p in side:
		var cut := team + own_cut(p)
		if cut != 0.0:
			out[str(p["id"])] = cut
	return out


## "Familiarity 70%", or "" at 100.
static func tag(p: Dictionary) -> String:
	return "" if value(p) >= FULL else "Familiarity %d%%" % roundi(value(p))


## "2%", "3.3%".
static func _percent(share: float) -> String:
	var v := snappedf(share * 100.0, 0.1)
	return "%d%%" % roundi(v) if is_equal_approx(v, roundf(v)) else "%.1f%%" % v


## His profile's line: what it is doing to his footy and how it comes back.
static func line(p: Dictionary) -> String:
	if value(p) >= FULL:
		return ""
	return "%s. Still learning his teammates: %s off his footy, back 5%% a game." % [
			tag(p), _percent(own_cut(p))]


## What the side's new-club men cost it, said before it bites: "" under three.
## Facts only, whichever way the coach goes.
static func side_line(side: Array) -> String:
	var men := new_club_men(side)
	var n := men.size()
	if n < TEAM_ARRIVALS - 1:
		return ""
	var pts := roundi(float(TEAM_POINTS_AT_70) * _fade(men))
	if n >= TEAM_ARRIVALS:
		return "%d men new to the club in this side. From four, the whole side is still learning each other: about %d points this week, easing each game. First-gamers and draftees don't count." % [n, pts]
	return "%d men new to the club in this side. A fourth and the whole side is still learning each other: about %d points this week, easing each game. First-gamers and draftees don't count." % [n, pts]


## The rule, on the trade and free-agency screens.
static func signing_line() -> String:
	return "A man from another club starts at familiarity 50%%, 70%% by Round 1 with a full pre-season, then up 5%% a game to 100%%. It takes 2%% off his footy at 70%%. Four or more new-club men in a side cost the whole side about %d points in Round 1, easing to nothing by Round 7." % TEAM_POINTS_AT_70


## The rule, on the draft screens.
static func draft_line() -> String:
	return "A draftee starts at familiarity 50%, 70% by Round 1 with a full pre-season, then up 5% a game to 100%. It takes 1% off his footy at 70%. Draftees don't count towards the four new men that cost a whole side."
