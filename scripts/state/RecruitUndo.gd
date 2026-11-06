class_name RecruitUndo
extends RefCounted
## Undo for a delisting, a free-agent signing and a re-signing (TODO row 119,
## 4.R76 / P-09: "undo where a thumb can slip ... until the week advances.
## Trades keep their confirm step").
##
## What can be undone: an action that settled something - you released a
## player, a free agent signed with you, your expiring player re-signed. An
## offer that ended in a counter, a walk-out or "on the table" is not: undoing
## it would let the coach learn a player's price for free, and the risk of an
## offer is the coach's (bible, principle 1).
##
## How long: until the week moves on. In the off-season, where these actions
## live, that is the national draft starting (begin_intake_draft closes free
## agency); in the season it is advance(). Any other change to the list or the
## market after the action (a trade, a rival's move, another offer that did not
## settle) also ends it: an undo never rewinds anything but its own action.
##
## Not saved: a reload clears it (GameState.reset). A snapshot carries a copy
## of the whole free-agent pool, which would bloat every save and be written as
## duplicate players; the save is a checkpoint, and an undo is for the slip you
## just made.
##
## Snapshots restore in place: the same player dictionaries and the same list
## arrays get their old contents back, so nothing that holds a reference
## (my_list is season.lists[my_club], screens holding a player) goes stale.

const MAX_STEPS := 10


## Everything a release, a free-agent signing or a re-signing can change.
static func snapshot(gs: Node, subject_id: String) -> Dictionary:
	var lists := {}
	# Parallel arrays, not a Dictionary keyed by player: a dictionary key is
	# hashed by content, so a player changed by the action would not be found.
	var refs := []
	var copies := []
	if gs.season != null:
		for code in gs.season.lists:
			var list: Array = gs.season.lists[code]
			lists[code] = list.duplicate()
	for group in [gs.my_list, gs.free_agents]:
		for p in group:
			refs.append(p)
			copies.append((p as Dictionary).duplicate(true))
	var facts: Variant = null
	if gs.career_facts.has(subject_id):
		facts = (gs.career_facts[subject_id] as Array).duplicate(true)
	return {
		"lists": lists,
		"free_agents": gs.free_agents.duplicate(),
		"refs": refs,
		"copies": copies,
		"news": gs.news.duplicate(true),
		"offseason_log": gs.offseason_log.duplicate(true),
		"compensation": gs.compensation.duplicate(true),
		"fa_lost": gs.fa_lost.duplicate(true),
		"market_stats": gs.market_stats.duplicate(true),
		"targets_signed": gs._targets_signed.duplicate(true),
		"fa_last_why": gs.fa_last_why,
		"subject": subject_id,
		"before": fingerprint(gs),
		"facts": facts,
	}


## A short fingerprint of the list and the market: changes with any move of a
## player between lists, any contract or offer, any news line. Ratings and
## caches the screens fill in are left out, so looking at a player never hides
## the undo.
static func fingerprint(gs: Node) -> int:
	if gs.season == null:
		return 0
	var parts := [gs.season_year, gs.offseason_open(), gs.news.size(),
			gs.news[0] if not gs.news.is_empty() else {}, gs.compensation.size()]
	var codes: Array = gs.season.lists.keys()
	codes.sort()
	for code in codes:
		var ids := []
		for p in gs.season.lists[code]:
			ids.append(str(p.get("id", "")))
		parts.append([code, ids])
	for group in [gs.my_list, gs.free_agents]:
		for p in group:
			parts.append([str(p.get("id", "")), p.get("club", ""), p.get("salary", 0),
					p.get("contract_years", 0), p.get("resigned", false), p.get("talks", {}),
					p.get("offers", []), p.get("market_round", 0), p.get("released_by", ""),
					p.get("morale", 0)])
	return hash(parts)


## Put back everything `snap` holds, in place.
static func restore(gs: Node, snap: Dictionary) -> void:
	var refs: Array = snap["refs"]
	var copies: Array = snap["copies"]
	for i in refs.size():
		var d: Dictionary = refs[i]
		d.clear()
		d.merge((copies[i] as Dictionary).duplicate(true))
	var lists: Dictionary = snap["lists"]
	for code in lists:
		if gs.season.lists.has(code):
			(gs.season.lists[code] as Array).assign(lists[code])
	gs.free_agents.assign(snap["free_agents"])
	gs.news.assign(snap["news"])
	gs.offseason_log.assign(snap["offseason_log"])
	gs.compensation.assign(snap["compensation"])
	gs.fa_lost.assign(snap["fa_lost"])
	gs.market_stats = (snap["market_stats"] as Dictionary).duplicate(true)
	gs._targets_signed = (snap["targets_signed"] as Dictionary).duplicate(true)
	gs.fa_last_why = str(snap["fa_last_why"])
	var sid := str(snap["subject"])
	if snap["facts"] == null:
		gs.career_facts.erase(sid)
	else:
		gs.career_facts[sid] = (snap["facts"] as Array).duplicate(true)
	# Market caches are rebuilt from the restored lists on the next pass.
	gs._bars = {}
	gs._fa_phase = {}


## Record a settled action. `kind`: "release", "sign" or "resign".
static func push(gs: Node, snap: Dictionary, kind: String, p: Dictionary) -> void:
	# Steps stack only while nothing else happened between them.
	if not gs.recruit_undo.is_empty() and int((gs.recruit_undo.back() as Dictionary)["after"]) != int(snap["before"]):
		gs.recruit_undo.clear()
	gs.recruit_undo.append({"kind": kind, "id": str(p.get("id", "")),
			"name": GameDB.player_display_name(p), "snap": snap, "after": fingerprint(gs)})
	while gs.recruit_undo.size() > MAX_STEPS:
		gs.recruit_undo.pop_front()


## The newest step is still undoable: the off-season is open and nothing has
## changed the list or the market since it.
static func valid(gs: Node) -> bool:
	if gs.recruit_undo.is_empty() or not gs.offseason_open():
		return false
	return int((gs.recruit_undo.back() as Dictionary)["after"]) == fingerprint(gs)


## {"kind", "id", "name"} of the step Undo would reverse, or {}.
static func last(gs: Node) -> Dictionary:
	if not valid(gs):
		gs.recruit_undo.clear()
		return {}
	var e: Dictionary = gs.recruit_undo.back()
	return {"kind": str(e["kind"]), "id": str(e["id"]), "name": str(e["name"])}


## Reverse the newest step. Returns {"ok", "kind", "reason"}.
static func undo(gs: Node) -> Dictionary:
	if not valid(gs):
		gs.recruit_undo.clear()
		return {"ok": false, "kind": "", "reason": "There is nothing to undo."}
	var e: Dictionary = gs.recruit_undo.pop_back()
	restore(gs, e["snap"])
	var name := str(e["name"])
	var reason := ""
	match str(e["kind"]):
		"release":
			reason = "Delisting undone: %s is back on your list." % name
		"sign":
			reason = "Signing undone: %s is a free agent again." % name
		"resign":
			reason = "Re-signing undone: %s is out of contract again." % name
	# The step below is valid again only if it still matches what is restored.
	if not gs.recruit_undo.is_empty() and int((gs.recruit_undo.back() as Dictionary)["after"]) != fingerprint(gs):
		gs.recruit_undo.clear()
	return {"ok": true, "kind": str(e["kind"]), "reason": reason}
