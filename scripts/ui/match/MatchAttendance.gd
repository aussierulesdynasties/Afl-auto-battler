class_name MatchAttendance
extends RefCounted
## How many people come to a match, for the 3D crowd: the stands fill to it (Oval3DCrowd.fill).
## Looks only. Nothing here is saved, nothing here is read by the simulation, and the figure uses
## its own generator, seeded from the match itself, so the same match always draws the same crowd
## and no other draw is disturbed.
##   - Fitted to every real AFL crowd of 2023-2026 (data/attendance.json, built by
##     tools/attendance/fit.py): the ground, each club's pull at home and away, a derby (both
##     clubs from the ground's state) or a neutral ground, the time of day and the finals week.
##   - A ground the AFL has had no crowds at lately (the 1990s grounds, the new ones) draws as a
##     known ground of its size does (the bigger the ground, the smaller the share it fills).
##   - A club with no crowds of its own (Tasmania, a Forge club, a club of the past) draws as an
##     average club.
##   - A Grand Final is a sell-out.
##   - A crowd never passes the ground's capacity.

const PATH := "res://data/attendance.json"
## A sold-out ground still has a few seats free (late, at the bar, in the wrong bay).
const SOLD_OUT := 0.97

static var _data := {}


static func data() -> Dictionary:
	if _data.is_empty():
		var f := FileAccess.open(PATH, FileAccess.READ)
		var parsed = JSON.parse_string(f.get_as_text()) if f != null else null
		_data = parsed if parsed is Dictionary else {}
	return _data


## A ground's capacity (0 when the file does not know it).
static func capacity(ground: String) -> int:
	return int((data().get("capacity", {}) as Dictionary).get(ground, 0))


## The crowd at ground for home v away, kicking off in slot (VignetteKickoff: day, twilight or
## night), in the round named label ("Round 5", "Qualifying Final 1", "Grand Final"). key: the
## match's own number (VignetteKickoff.key_of), which sets its swing. 0 when the ground is unknown.
static func crowd(ground: String, home: String, away: String, slot: String, label: String, key: int) -> int:
	var d := data()
	var cap := capacity(ground)
	if d.is_empty() or cap <= 0:
		return 0
	if label.contains("Grand Final"):
		return int(cap * SOLD_OUT)
	var venues: Dictionary = d.get("venue", {})
	var lv := 0.0
	if venues.has(ground):
		lv = float(venues[ground])
	else:
		var fb: Array = d.get("fallback", [0.0, 1.0])
		lv = float(fb[0]) + float(fb[1]) * log(float(cap))
	lv += float((d.get("home", {}) as Dictionary).get(home, 0.0))
	lv += float((d.get("away", {}) as Dictionary).get(away, 0.0))
	var st := str((d.get("state", {}) as Dictionary).get(ground, ""))
	var cs: Dictionary = d.get("club_state", {})
	var home_local := str(cs.get(home, "VIC")) == st
	var away_local := str(cs.get(away, "VIC")) == st
	if home_local and away_local:
		lv += float(d.get("derby", 0.0))
	elif not home_local and not away_local:
		lv += float(d.get("neutral", 0.0))
	lv += float((d.get("slot", {}) as Dictionary).get(slot, 0.0))
	for week: String in (d.get("finals", {}) as Dictionary):
		if label.begins_with(week):
			lv += float(d["finals"][week])
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("crowd|%d" % key)
	lv += rng.randfn(0.0, float(d.get("swing_sd", 0.0)))
	return mini(int(round(exp(lv))), int(cap * SOLD_OUT))


## The share of the ground's seats that crowd fills (Oval3DCrowd.fill); -1 when unknown.
static func fill(ground: String, n: int) -> float:
	var cap := capacity(ground)
	if cap <= 0 or n <= 0:
		return -1.0
	return clampf(float(n) / float(cap), 0.0, SOLD_OUT)


## A result's crowd (res: home, away, label), at ground in slot, keyed as VignetteKickoff keys it.
static func of_match(res: Dictionary, ground: String, slot: String) -> int:
	var home := str(res.get("home", ""))
	var away := str(res.get("away", ""))
	var label := str(res.get("label", ""))
	var seed_n := 0
	var loop := Engine.get_main_loop()
	var gs: Node = (loop as SceneTree).root.get_node_or_null("GameState") if loop is SceneTree else null
	if gs != null and gs.get("season") != null:
		seed_n = int(gs.get("season").get("seed"))
	return crowd(ground, home, away, slot, label, VignetteKickoff.key_of(seed_n, label, home, away))
