class_name CoachOfYear
extends RefCounted
## Coach of the Year: the coaches' own award for the home-and-away season,
## given the week it ends, before the finals begin (director, 2026-11-13: "it
## is awarded for the home and away season only, finals results arent
## considered, and the award is given out after the conclusion of the home and
## away season immediately").
##
## Judged on how far a club beat what was expected of it (Director Bible 160,
## 2026-10-08), from the home-and-away season alone:
##   ladder      where the club finished the home-and-away season
##   last        its finish last year (0 when the save has none)
##   expect      where its list ranked on paper before Round 1 (club_expect)
##   goal_met    whether it met its board's goal (ClubLife.goal_met)
##   streak      its longest winning run of the home-and-away season
## The director's cases (2026-11-13): "its not always teh coach whose team
## finishes first (though often, it is). if a team goes from bottom four to top
## four, chances are their coach will win the award", "or if a team goes on a
## long winning streak to make finals, their coach will win the award most of
## the time".
##
## Every senior coach is eligible, yours and every rival's, judged by the same
## rule. The winner is drawn, never certain: each club's weight is
## exp(score), and JUDGES_SPREAD of the odds is shared evenly among the
## finalists, so the best case is the likely winner and never the sure one
## (bible: decisions move the odds, never the certainty). The weights were
## tuned on the seeded sample in tests/run_coach_of_year_tests.gd (a ladder
## model with real AFL spreads: the top side about 19 wins, the bottom about
## 4) to the director's words: the minor premier's coach wins about 45% of
## seasons, a bottom-four-to-top-four coach about two in three, a coach whose
## run of 10 or more wins carried his side into the finals about 60%.
## Nothing here touches a match.

## Each ladder place a club finished above where its list ranked on paper.
const W_EXPECT := 0.22
## Each ladder place a club climbed on last year's finish.
const W_CLIMB := 0.12
## The minor premiership.
const W_MINOR := 1.0
## A top-four finish.
const W_TOP4 := 0.5
## Bottom four last year to top four this year: the model case.
const W_BOTTOM_TO_TOP := 6.0
## A winning run this long or longer, into the finals.
const STREAK_LONG := 10
const W_STREAK := 6.0
## Each win the run goes past STREAK_LONG.
const W_STREAK_EXTRA := 0.3
## The board's goal met.
const W_GOAL := 0.3
## Missing the finals: the coaches rarely look past the finalists.
const W_NO_FINALS := -4.0
## The share of the odds the judges spread evenly over the finalists: no
## season's standout is ever a certainty (about 92% at most).
const JUDGES_SPREAD := 0.08


## One club's score: how far its home-and-away season beat expectation.
## `f` is {ladder, last, expect, goal_met, streak}; `clubs` and `finalists` are
## the season's.
static func score(f: Dictionary, clubs: int, finalists: int) -> float:
	var pos := int(f.get("ladder", clubs))
	var last := int(f.get("last", 0))
	var s := W_EXPECT * float(int(f.get("expect", ClubLife.default_rank(clubs))) - pos)
	if last > 0:
		s += W_CLIMB * float(maxi(0, last - pos))
	if pos == 1:
		s += W_MINOR
	if pos <= 4:
		s += W_TOP4
	if bottom_to_top(f, clubs):
		s += W_BOTTOM_TO_TOP
	if long_streak(f, finalists):
		s += W_STREAK + W_STREAK_EXTRA * float(int(f.get("streak", 0)) - STREAK_LONG)
	if bool(f.get("goal_met", false)):
		s += W_GOAL
	if pos > finalists:
		s += W_NO_FINALS
	return s


## From the bottom four last year to the top four this year.
static func bottom_to_top(f: Dictionary, clubs: int) -> bool:
	var last := int(f.get("last", 0))
	return last > clubs - 4 and int(f.get("ladder", clubs)) <= 4


## A winning run of STREAK_LONG or more by a club that made the finals.
static func long_streak(f: Dictionary, finalists: int) -> bool:
	return int(f.get("streak", 0)) >= STREAK_LONG and int(f.get("ladder", 99)) <= finalists


## Each club's chance of the award, code -> 0..1, from `facts` (code -> the
## facts `score` reads): exp(score) shares, with JUDGES_SPREAD of the whole
## shared evenly among the finalists.
static func odds(facts: Dictionary, clubs: int, finalists: int) -> Dictionary:
	var scores := {}
	var top := -INF
	var in_finals := 0
	for code in facts:
		scores[code] = score(facts[code], clubs, finalists)
		top = maxf(top, float(scores[code]))
		if int((facts[code] as Dictionary).get("ladder", clubs)) <= finalists:
			in_finals += 1
	var tot := 0.0
	for code in scores:
		scores[code] = exp(float(scores[code]) - top)
		tot += float(scores[code])
	var spread := JUDGES_SPREAD if in_finals > 0 else 0.0
	for code in scores:
		var share := (1.0 - spread) * float(scores[code]) / tot
		if spread > 0.0 and int((facts[code] as Dictionary).get("ladder", clubs)) <= finalists:
			share += spread / float(in_finals)
		scores[code] = share
	return scores


## The winning club, drawn by `odds` with `seed`: the same season always
## names the same coach. "" when there are no facts.
static func pick(facts: Dictionary, clubs: int, finalists: int, seed: int) -> String:
	var o := odds(facts, clubs, finalists)
	var codes := o.keys()
	codes.sort()   # a fixed order, so the draw does not ride on dictionary order
	if codes.is_empty():
		return ""
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var x := rng.randf()
	for code in codes:
		x -= float(o[code])
		if x <= 0.0:
			return str(code)
	return str(codes[codes.size() - 1])


## The longest winning run in a club's home-and-away results (Season.results,
## one array of matches per round). A draw or a loss ends a run.
static func longest_streak(rounds: Array, code: String) -> int:
	var best := 0
	var run := 0
	for rnd in rounds:
		for res in rnd:
			var side := -1
			if str(res.get("home", "")) == code:
				side = 0
			elif str(res.get("away", "")) == code:
				side = 1
			if side < 0 or res.has("tag"):
				continue
			var sc: Array = res.get("score", [0, 0])
			if int(sc[side]) > int(sc[1 - side]):
				run += 1
				best = maxi(best, run)
			else:
				run = 0
	return best


## Why he won, in one football line, no scores (Director Bible 160): the
## strongest of the cases he met. `club` is the club's name.
static func line(f: Dictionary, club: String, clubs: int, finalists: int) -> String:
	var pos := int(f.get("ladder", 0))
	var last := int(f.get("last", 0))
	var expect := int(f.get("expect", 0))
	if bottom_to_top(f, clubs):
		return "Took %s from %s last year to %s." % [club, PreSeason.ordinal(last), PreSeason.ordinal(pos)]
	if long_streak(f, finalists):
		return "%d straight wins carried %s into the finals." % [int(f.get("streak", 0)), club]
	if pos == 1:
		return "%s finished on top of the ladder." % club
	if expect > pos:
		return "%s finished %s, picked for %s on paper." % [club, PreSeason.ordinal(pos), PreSeason.ordinal(expect)]
	if last > pos:
		return "%s climbed from %s to %s." % [club, PreSeason.ordinal(last), PreSeason.ordinal(pos)]
	return "%s finished %s." % [club, PreSeason.ordinal(pos)]
