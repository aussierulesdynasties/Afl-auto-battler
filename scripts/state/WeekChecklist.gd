class_name WeekChecklist
extends RefCounted
## The week's jobs on the Hub (director, 2026-11-03: a weekly checklist gives
## the game structure and forward thrust). Routine jobs only, each read from
## real state, each one tap from its screen. Guidance, never a block: Play
## match and Sim the week work with jobs left; Play only says how many.
##
## On in every career (TODO row 51, 2026-11-10: the "weekly_checklist"
## setting is gone).
##
## State: GameState.week_checks = {"week": story_week, "done": {key: true},
## "seen": {key: true}}. A new week starts it empty. "done" is what the coach
## did this week (confirmed the side, opened Training); "seen" remembers that a job
## came up this week, so it stays on the list, ticked, once it is dealt with.

## The week's own record, reset when the week moves on.
static func _week(gs) -> Dictionary:
	var wk: int = gs.story_week()
	if not (gs.week_checks is Dictionary) or int(gs.week_checks.get("week", -1)) != wk:
		gs.week_checks = {"week": wk, "done": {}, "seen": {}}
	return gs.week_checks


## Whether the coach did `key` this week.
static func is_done(gs, key: String) -> bool:
	return gs.season != null and _done(gs, key)


## The coach did `key` this week ("team" via Confirm side, "training").
static func mark(gs, key: String) -> void:
	if gs.season == null:
		return
	(_week(gs)["done"] as Dictionary)[key] = true
	gs.mark_dirty()


static func _done(gs, key: String) -> bool:
	return bool((_week(gs)["done"] as Dictionary).get(key, false))


## A job that comes and goes with state (an open staff job, a card): kept on
## the list for the rest of the week once it came up, ticked when cleared.
static func _seen(gs, key: String, pending: bool) -> bool:
	var seen: Dictionary = _week(gs)["seen"]
	if pending and not seen.has(key):
		seen[key] = true
		gs.mark_dirty()
	return pending or seen.has(key)


## The big call: the week's one weighty decision about the coach's own
## career. A due coach-arc beat first (ClubArcs.big_call); else the most pressing
## of backing a young player, captaincy, the press or an assistant approach
## (BigCalls). {} or {"text", "route", "done", ...}.
static func big_call(gs) -> Dictionary:
	if gs.season == null:
		return {}
	# Loaded here, not named: these read the GameDB autoload, which a test's
	# preload of this script compiles before autoloads exist.
	var arcs = load("res://scripts/state/ClubArcs.gd")
	var arc: Dictionary = arcs.big_call(gs)
	if not arc.is_empty():
		arc["done"] = false
		return arc
	if not arcs.on(gs):
		return {}
	return load("res://scripts/state/BigCalls.gd").pick(gs, _week(gs))


## This week's routine jobs, in order: [{key, text, done, route}]. "route"
## is the Router screen the job lives on, or "" when it is on the Hub itself.
## Empty with no week to play (the season is over).
static func items(gs) -> Array:
	var out: Array = []
	if gs.season == null or gs.season.is_season_over():
		return out
	out.append({"key": "team", "text": "Look over the side", "done": _done(gs, "team"), "route": "selection"})
	out.append({"key": "training", "text": "Check training", "done": _done(gs, "training"), "route": "training"})
	# The open jobs the Coaching button counts.
	var jobs: int = gs.staff_vacancies.size()
	if _seen(gs, "coaching", jobs > 0):
		out.append({"key": "coaching", "text": "Fill the coaching job" if jobs <= 1
				else "Fill %d coaching jobs" % jobs, "done": jobs == 0, "route": "staff"})
	var tribunal: bool = not gs.pending_mro_challenges().is_empty()
	if _seen(gs, "tribunal", tribunal):
		out.append({"key": "tribunal", "text": "Decide on the tribunal", "done": not tribunal, "route": ""})
	if not gs.week_events.is_empty():
		out.append({"key": "club", "text": "Answer the club's questions" if gs.week_events.size() > 1
				else "Answer the club's question", "done": not gs.week_event_pending(), "route": ""})
	return out


## How many of this week's jobs are still open, the big call included: the
## Hub counts every "To do" row it shows.
static func left(gs) -> int:
	var call := big_call(gs)
	var n := 0 if call.is_empty() or bool(call.get("done", false)) else 1
	for it in items(gs):
		if not bool(it["done"]):
			n += 1
	return n
