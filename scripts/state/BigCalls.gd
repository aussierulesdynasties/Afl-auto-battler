class_name BigCalls
extends RefCounted
## The Hub's weekly "one big call" when no coach-arc beat is due (director,
## 2026-11-03, plan 3a: backing a young player, captaincy, press answers and
## assistant approaches are promoted into it). Each candidate is read from real
## state; the most pressing one is picked and kept for the rest of the week, then
## ticked once it is dealt with.
##
## Shows in every career (TODO row 51).

## Most pressing first: the press waits for no one, an approach has to be answered
## before the season ends, a club cannot go without a captain, a young player's
## run is the coach's to give, a pre-season captaincy review can wait.
const ORDER := ["press", "approach", "captain_vacant", "backing", "captain_review"]


## Every candidate that is live now: {kind: {text, route, ref}}. The press
## and approach are answered on the Hub itself (the conference overlay and the
## approach cards), so their route is "hub": tapping reloads it in place.
static func candidates(gs) -> Dictionary:
	var out := {}
	if gs.season == null or gs.my_club == "" or gs.season.is_season_over():
		return out
	if gs.media_conference_pending():
		out["press"] = {"text": "Face the press", "route": "hub", "ref": ""}
	for a in gs.coach_approaches:
		if str((a as Dictionary).get("choice", "")) == "":
			out["approach"] = {"text": "Answer %s's approach for your %s" % [GameDB.club_name(str(a["club"])),
					CoachMarket._job_word(str(a["from_job"]))], "route": "hub", "ref": str(a["cid"])}
			break
	var rec: Dictionary = gs.captaincy_record(gs.my_club)
	if Captaincy.ids(rec, "captain").is_empty():
		out["captain_vacant"] = {"text": "Name a captain", "route": "list", "ref": ""}
	elif not gs.captaincy_mid_season() and int(rec.get("since", gs.season_year)) < gs.season_year:
		out["captain_review"] = {"text": "Review the captaincy for %d" % gs.season_year, "route": "list", "ref": ""}
	var young := ready_to_back(gs)
	if not young.is_empty():
		out["backing"] = {"text": "Back %s with a run of games?" % GameDB.player_display_name(young),
				"route": "selection", "ref": str(young["id"])}
	return out


## How far under the 22nd-best rating on the list a young player can be and
## still be ready to hold a spot.
const FRINGE := 3


## The best young player who could be backed and is good enough to hold a spot:
## rated within FRINGE of the list's 22nd best. {} when there is none.
static func ready_to_back(gs) -> Dictionary:
	var roster: Array = gs.club_roster(gs.my_club)
	if roster.size() < 22:
		return {}
	var ovrs: Array = []
	for p in roster:
		ovrs.append(int((p as Dictionary).get("overall", 0)))
	ovrs.sort()
	ovrs.reverse()
	var bar: int = int(ovrs[21]) - FRINGE
	var best := {}
	for p in roster:
		var ov := int(p.get("overall", 0))
		if ov >= bar and gs.can_back(p) and (best.is_empty() or ov > int(best.get("overall", 0))):
			best = p
	return best


## Is this week's call dealt with?
static func done(gs, kind: String, ref: String) -> bool:
	match kind:
		"press":
			return not gs.media_conference_pending()
		"approach":
			for a in gs.coach_approaches:
				if str(a.get("cid", "")) == ref:
					return str(a.get("choice", "")) != ""
			return true
		"captain_vacant":
			return not Captaincy.ids(gs.captaincy_record(gs.my_club), "captain").is_empty()
		"captain_review":
			return WeekChecklist.is_done(gs, "captaincy")
		"backing":
			var p: Dictionary = gs.list_player(ref)
			return p.is_empty() or Backing.is_active(p)
	return true


## This week's one call: {text, route, done, kind}, or {}. The first pick of the
## week is kept in week_checks["big_call"], so the call never changes under the coach.
static func pick(gs, week: Dictionary) -> Dictionary:
	var held = week.get("big_call", {})
	if not (held is Dictionary) or held.is_empty():
		var live := candidates(gs)
		held = {}
		for k in ORDER:
			if live.has(k):
				held = (live[k] as Dictionary).duplicate()
				held["kind"] = k
				break
		if held.is_empty():
			return {}
		week["big_call"] = held
		gs.mark_dirty()
	var out: Dictionary = (held as Dictionary).duplicate()
	out["done"] = done(gs, str(held["kind"]), str(held.get("ref", "")))
	return out
