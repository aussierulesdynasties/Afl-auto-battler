class_name TeamFamiliarity
extends RefCounted
## Team familiarity (TODO row 125, director 2026-11-08 and 2026-11-09): teammates
## play better the longer they play together, so a new arrival has growing pains
## and a heavy list turnover costs the whole side. The coach sees it as Team
## Chemistry. Not plan fluency (PreSeason.familiar_mult), and apart from the trait
## line combinations.
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
## Rounds 1 to 7: the cost is gone by the seventh.
const FADE_ROUNDS := 7
## The most this can cost a side: the team step, and every man in it at 50.
const WORST_CUT := TEAM_CUT_AT_70 + CLUB_CUT_AT_70 * (FULL - ARRIVE) / SHORT_AT_70


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


## "Chemistry 70%", or "" at 100.
static func tag(p: Dictionary) -> String:
	return "" if value(p) >= FULL else "Chemistry %d%%" % roundi(value(p))


## "2%", "3.3%".
static func _percent(share: float) -> String:
	var v := snappedf(share * 100.0, 0.1)
	return "%d%%" % roundi(v) if is_equal_approx(v, roundf(v)) else "%.1f%%" % v


## What his familiarity is taking off his footy, "2%".
static func own_percent(p: Dictionary) -> String:
	return _percent(own_cut(p))


## Under his bar on his profile, "" at 100.
static func line(p: Dictionary) -> String:
	if value(p) >= FULL:
		return ""
	return "%s off his footy, up 5%% a game." % own_percent(p)


## The Team Chemistry meter, 1 to 0: the form the whole side is playing with, from what
## each man carries (side_cuts), against the most this can cost a side. So one man at
## 70 barely dents it and the step at 4 men shows as the step it is. Display only.
static func chemistry(side: Array) -> float:
	if side.is_empty():
		return 1.0
	var total := 0.0
	for cut in side_cuts(side).values():
		total += float(cut)
	return clampf(1.0 - total / float(side.size()) / WORST_CUT, 0.0, 1.0)


## The team-wide cost this side carries this round, in points. 0 under the threshold.
static func team_points(side: Array) -> int:
	var men := new_club_men(side)
	return 0 if men.size() < TEAM_ARRIVALS else roundi(float(TEAM_POINTS_AT_70) * _fade(men))


## The cost at each of Rounds 1 to 7, in points: 19 down to 0 on the same straight line.
static func fade_points() -> Array:
	var out := []
	for game in range(FADE_ROUNDS):
		out.append(roundi(float(TEAM_POINTS_AT_70) * float(FADE_ROUNDS - 1 - game) / float(FADE_ROUNDS - 1)))
	return out


## Where this side stands on fade_points, -1 when it carries no team-wide cost.
static func fade_step(side: Array) -> int:
	var men := new_club_men(side)
	if men.size() < TEAM_ARRIVALS:
		return -1
	return roundi((1.0 - _fade(men)) * float(FADE_ROUNDS - 1))


## The one line where a coach signs a man.
static func signing_line() -> String:
	return "From another club: 2%% off his footy in Round 1, up 5%% a game. %d or more in a side: about %d points worse in Round 1, gone by Round 7." % [TEAM_ARRIVALS, TEAM_POINTS_AT_70]


## The one line where a coach drafts a man.
static func draft_line() -> String:
	return "A draftee: 1%% off his footy in Round 1, up 5%% a game. Draftees don't count towards the %d men from other clubs that hurt team chemistry." % TEAM_ARRIVALS
