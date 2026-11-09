class_name PremiershipInk
extends RefCounted
## Premiership-year tattoos (TODO row 73; Director Bible 6.63, Q16): some
## premiership players get the year inked on the bicep, others never do.
##
##  - Who: the men who played in the winning Grand Final side (its 23), not the
##    whole list - a recognised premiership player, as Ricciuto's 1998 was.
##  - Once: at his first flag his choice is made and stored on him
##    (p["flag_ink"]): false, he never gets one; an Array, the years on his arm.
##    No re-roll after that, on reload or at a later flag.
##  - After that each later flag adds its year automatically, oldest first,
##    each year once (a result processed twice adds nothing).
##  - It is on the player, so it goes with him to a new club and into the save.
##  - The choice comes from his id alone, on its own stream, never the match
##    RNG; the sim never reads it. Cosmetic only: no rating, morale, loyalty or
##    contract effect.

## How many first-time premiership players get the tattoo: the one place the
## rate lives. Director, 2026-11-10 (Q16): about 1 in 5.
const SHARE := 0.2

const KEY := "flag_ink"


## Whether he gets it at his first flag: from his id alone, on its own stream.
static func adopts(id: String, share := SHARE) -> bool:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("premiership-ink|" + id)
	return rng.randf() < share


## Records a flag won in `year` on p: the first decides, later ones add a year.
static func record_flag(p: Dictionary, year: int, share := SHARE) -> void:
	var got = p.get(KEY)
	if got is Array:
		if not (got as Array).has(year):
			(got as Array).append(year)
			(got as Array).sort()
		return
	if got is bool:
		return    # decided at his first flag: no
	p[KEY] = [year] if adopts(str(p.get("id", "")), share) else false


## The years on his arm, oldest first ([] for none).
static func years(p: Dictionary) -> Array:
	var got = p.get(KEY)
	return (got as Array).duplicate() if got is Array else []


## The premiership players of a Grand Final result: the winning side's men who
## played (Awards.norm_smith reads the same roster): the side named `premier`,
## else the result's winner (MatchSim.result: 0 home, 1 away, -1 a draw).
## [] when neither names a side.
static func premiership_ids(gf: Dictionary, premier := "") -> Array:
	var codes := [str(gf.get("home", "")), str(gf.get("away", ""))]
	var side := codes.find(premier) if premier != "" else int(gf.get("winner", -1))
	var roster: Array = gf.get("roster", [])
	var played: Dictionary = gf.get("players", {})
	var out := []
	if side < 0 or side >= roster.size():
		return out
	for r in roster[side]:
		var id := str(r.get("id", "")) if r is Dictionary else str(r)
		if id != "" and played.has(id):
			out.append(id)
	return out


## After the Grand Final: each premiership player found in `players` (id ->
## player dict) records the flag.
static func record_grand_final(gf: Dictionary, premier: String, players: Dictionary, year: int,
		share := SHARE) -> void:
	for id in premiership_ids(gf, premier):
		if players.has(id):
			record_flag(players[id], year, share)
