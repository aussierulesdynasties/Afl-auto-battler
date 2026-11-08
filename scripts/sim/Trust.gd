class_name Trust
extends RefCounted
## How far a person trusts you, the coach, and why (club-life stories, phase 1).
##
## One model for every relationship: phase 1 keys your players ("p:<id>");
## later phases add rival coaches ("c:"), journalists ("j:") and board figures
## ("b:") to the same map. The map lives in GameState.relations and is saved
## with the career; a person with no entry is neutral, so an older save loads
## with everyone neutral.
##
## The game shows it as his opinion of you, a number out of 100 (opinion();
## director 2026-11-08): 50 when nothing has passed between you. Every change
## keeps its reason ("You dropped him after three games"), so the player can
## always look up why. It has no passive effect and never drifts back toward 50
## on its own: it moves only through your choices, and it changes what those
## choices do only where they say so (a talk lands harder with a player who
## trusts you; below 50 he may refuse to re-sign, Contracts.refuse_chance).

const LOWEST := -100
const HIGHEST := 100
## The most one moment can move it, either way (StoryDeck checks every card).
const STEP_MAX := 20
## Reasons kept per person, newest last.
const LOG_KEEP := 8

## Bands, highest first: [floor, key, words]. Neutral says nothing.
const BANDS := [
	[50, "close", "Trusts you completely"],
	[20, "trusts", "Trusts you"],
	[-19, "neutral", ""],
	[-49, "wary", "Wary of you"],
	[LOWEST, "lost", "Stopped listening"],
]

## What trust does to a lift that depends on it (a talk, a promise): it lands
## harder with a player who trusts you, softer with one who doesn't.
const LIFT_SCALE := {"close": 1.4, "trusts": 1.2, "neutral": 1.0, "wary": 0.7, "lost": 0.4}

## Trust per point of the opinion the game shows (opinion()).
const PER_POINT := 2
const OPINION_LINE := "Opinion of you %d/100"
## A reason's move, in the opinion the game shows.
const OPINION_MOVE := "Opinion of you %+d."


static func player_key(id: String) -> String:
	return "p:" + id


static func value(rel: Dictionary, key: String) -> int:
	return int((rel.get(key, {}) as Dictionary).get("t", 0))


## His opinion of you as the game shows it, 0..100 (director 2026-11-08).
static func opinion(t: int) -> int:
	return roundi(50.0 + float(t) / float(PER_POINT))


## What a trust move of `d` does to the opinion the game shows, from trust `t`
## (after one moment's limit and the ends of the scale). An even move is always
## half its size; an odd one depends on where he starts.
static func opinion_move(t: int, d: int) -> int:
	return opinion(clampi(t + clampi(d, -STEP_MAX, STEP_MAX), LOWEST, HIGHEST)) - opinion(t)


## "Opinion of you 62/100".
static func opinion_line(t: int) -> String:
	return OPINION_LINE % opinion(t)


## The lowest opinion a band starts at ("trusts" is 60).
static func band_opinion(key: String) -> int:
	for b in BANDS:
		if str(b[1]) == key:
			return opinion(int(b[0]))
	return 0


static func band(t: int) -> String:
	for b in BANDS:
		if t >= int(b[0]):
			return str(b[1])
	return "lost"


## Move trust by `d` (clamped to one moment's limit) and keep the reason.
## Returns what actually changed.
static func change(rel: Dictionary, key: String, d: int, why: String, year: int, when: String) -> int:
	if d == 0:
		return 0
	var entry: Dictionary = rel.get(key, {})
	var before := int(entry.get("t", 0))
	var after := clampi(before + clampi(d, -STEP_MAX, STEP_MAX), LOWEST, HIGHEST)
	if after == before:
		return 0   # already at the end of the scale: nothing moved, nothing to keep
	entry["t"] = after
	var log: Array = entry.get("log", [])
	# "o": what the opinion the game shows moved, kept so the reason says it exactly.
	log.append({"y": year, "w": when, "d": after - before, "o": opinion(after) - opinion(before), "why": why})
	while log.size() > LOG_KEEP:
		log.pop_front()
	entry["log"] = log
	rel[key] = entry
	return after - before


## His reasons, newest first: [{"y", "w", "d", "o", "why"}] ("o" from 2026-11-08 on).
static func reasons(rel: Dictionary, key: String) -> Array:
	var log: Array = ((rel.get(key, {}) as Dictionary).get("log", []) as Array).duplicate()
	log.reverse()
	return log


## One reason as the profile lists it: "Round 5, 2026. You promised him a game
## and left him out. Opinion of you -4." A reason kept before the opinion was
## shown has only the trust move: half of it, rounded away from zero.
static func reason_text(r: Dictionary) -> String:
	var why := str(r.get("why", "")).strip_edges()
	if why != "" and not why.ends_with("."):
		why += "."
	var d := int(r.get("d", 0))
	var o := int(r.get("o", signi(d) * ceili(absf(float(d)) / 2.0)))
	var head := "%s, %d. %s" % [str(r.get("w", "")), int(r.get("y", 0)), why]
	return head if o == 0 else "%s %s" % [head, OPINION_MOVE % o]


## A lift that depends on trust, scaled by his band. Only lifts scale; a cost
## is the same whoever pays it.
static func scaled(d: int, t: int) -> int:
	if d <= 0:
		return d
	return maxi(1, roundi(float(d) * float(LIFT_SCALE[band(t)])))
