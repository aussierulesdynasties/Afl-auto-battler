class_name VignetteKickoff
extends RefCounted
## When a match is played, as the match scenes draw it: by day, at twilight or at night
## (director, 2026-11-12: "night games added"; before this every ground was drawn under
## lights). Presentation only. Nothing here is saved, nothing here is read by the
## simulation, and the pick uses its own generator, seeded from the match itself, so the
## same match always gets the same sky and no other draw is disturbed.
##   - A ground hosts day, twilight and night matches as often as it really did in 2026
##     (data/kickoff_by_venue.json, built by tools/visual/build_kickoff_shares.py).
##   - A Grand Final is a day game.
##   - A hot day is never a night game.
##   - A ground with its roof closed keeps its lights: it is drawn lit whatever the hour.

const DAY := "day"
const TWILIGHT := "twilight"
const NIGHT := "night"
const SLOTS := [DAY, TWILIGHT, NIGHT]

## Capture tools and tests only: draw this slot instead of the match's ("" = the match's).
static var forced_slot := ""

## The match being shown (use_match): its ground, its own key and its label. With no match
## set, every scene is a night game, as they all were before.
static var venue := ""
static var key := 0
static var label := ""
static var has_match := false

## The slot the ground was last drawn in (VignetteGround.draw_ground sets it each frame),
## for what is drawn after the ground without knowing the weather: the ball.
static var shown := NIGHT

static var _data := {}


static func data() -> Dictionary:
	if _data.is_empty():
		var f := FileAccess.open("res://data/kickoff_by_venue.json", FileAccess.READ)
		var parsed = JSON.parse_string(f.get_as_text()) if f != null else null
		_data = parsed if parsed is Dictionary else {"default": {DAY: 0.0, TWILIGHT: 0.0, NIGHT: 1.0}, "venues": {}}
	return _data


## A ground's share of day, twilight and night matches: its own when it hosted enough
## matches to mean something, else the league's.
static func shares(ground: String) -> Dictionary:
	var d := data()
	var own: Dictionary = (d.get("venues", {}) as Dictionary).get(ground, {})
	if int(own.get("games", 0)) >= int(d.get("min_games", 6)):
		return own
	return d.get("default", {})


## A match's key: the same match gives the same number in every session.
static func key_of(season_seed: int, match_label: String, home: String, away: String) -> int:
	return hash("kickoff|%d|%s|%s|%s" % [season_seed, match_label, home, away])


## Day, twilight or night for a match at ground in this weather. match_key: key_of.
## match_label: the round's label ("Grand Final").
static func slot(ground: String, weather: String, match_key: int, match_label := "") -> String:
	if match_label.contains("Grand Final"):
		return DAY
	var share := shares(ground)
	var weights := [float(share.get(DAY, 0.0)), float(share.get(TWILIGHT, 0.0)), float(share.get(NIGHT, 0.0))]
	if weather == "hot":
		weights[2] = 0.0
	var total: float = weights[0] + weights[1] + weights[2]
	if total <= 0.0:
		return DAY if weather == "hot" else NIGHT
	var rng := RandomNumberGenerator.new()
	rng.seed = match_key
	var roll := rng.randf() * total
	for i in range(3):
		roll -= float(weights[i])
		if roll < 0.0:
			return SLOTS[i]
	return SLOTS[2] if float(weights[2]) > 0.0 else DAY


## Show this match from now on (the statics outlive the scene). res: a match or its
## result, with home, away and label (the pre-match and the match pass the same three, so
## both get the same sky). ground: where it is played (VignetteGround.ground_of).
## This file names no other class, so a script that only wants the ball can load it.
static func use_match(res: Dictionary, ground := "") -> void:
	var home := str(res.get("home", ""))
	var away := str(res.get("away", ""))
	has_match = home != "" and away != ""
	venue = ground if has_match else ""
	label = str(res.get("label", ""))
	var seed_n := 0
	var loop := Engine.get_main_loop()
	var gs: Node = (loop as SceneTree).root.get_node_or_null("GameState") if loop is SceneTree else null
	if gs != null and gs.get("season") != null:
		seed_n = int(gs.get("season").get("seed"))
	key = key_of(seed_n, label, home, away)


## The slot to draw now, in this weather: the forced one, else the match's, else night.
static func now(weather: String) -> String:
	if forced_slot != "":
		return forced_slot
	if not has_match:
		return NIGHT
	return slot(venue, weather, key, label)


## How much daylight a slot has: 1 by day, 0 at night, part of the way at twilight.
static func daylight(s: String) -> float:
	match s:
		DAY:
			return 1.0
		TWILIGHT:
			return 0.45
	return 0.0


## How strongly the ground's lights show: full at night, coming on at twilight, off by day.
static func lights(s: String) -> float:
	match s:
		DAY:
			return 0.0
		TWILIGHT:
			return 0.6
	return 1.0
