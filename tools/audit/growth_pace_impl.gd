extends RefCounted
## The director's pace (Growth.PACE, 2026-11-17): a kid at 60 who plays every
## ordinary game reaches his potential after 65 / 100 / 125 / 140 / 150 games.
## Grows one player per role and potential by the game's own grant and
## spending (Growth.match_xp, train_xp, GameState._spend_banks), no club
## multipliers, and prints the games he took. Arms: by position, and his
## training third all off-position (a focus on speed, outside every rating:
## the director's 225 games to 85).
## Run: godot --headless --path . --script tools/audit/run_audit.gd -- growth_pace_impl
const ROLES := ["MID", "FWD", "DEF", "RUCK"]
const POTS := [65, 70, 72, 75, 80, 85, 90, 95]
const OFF := {"MID": "speed", "FWD": "speed", "DEF": "speed", "RUCK": "speed"}   # outside every rating


func run() -> void:
	GameState.reset()
	GameState.autosave_enabled = false
	GameState.career_seed = 301
	GameState.start_season("MEL", GameDB.club_list("MEL"))
	var base := {}
	for p in GameDB.players:
		var r := str(p.get("role", ""))
		if ROLES.has(r) and not base.has(r) and not (p.get("attr", {}) as Dictionary).is_empty():
			base[r] = p
	for arm in ["position", "all_off"]:
		for r in ROLES:
			var line := PackedStringArray()
			for pot in POTS:
				line.append("%d:%s" % [pot, _games(base[r], int(pot), arm)])
			print("PACE|%s|%s|%s" % [arm, r, " ".join(line)])


func _games(src: Dictionary, pot: int, arm: String) -> String:
	var p: Dictionary = src.duplicate(true)
	p["id"] = "pace_%s_%d" % [str(p["role"]), pot]
	p["gm"] = 18.0
	p["sample"] = 18.0
	p.erase("project")
	p.erase("peak_year")
	var role := str(p["role"])
	for k in p["attr"]:
		p["attr"][k] = 60      # every attribute 60 reads OVR 60
	var start := int(Rating.ovr(p))
	p["potential"] = pot
	p["xp"] = 0.0
	p["xp_match"] = 0.0
	var own: Dictionary = Rating.shares(p)
	var off := {str(OFF[role]): 1.0}
	for g in range(1, 400):
		p["xp_match"] = float(p["xp_match"]) + Growth.match_xp(p, 1.0)
		var t := Growth.train_xp(p)
		if arm == "position":
			p["xp"] = float(p["xp"]) + t
			GameState._spend_banks(p, own)
		elif arm == "all_off":
			p["xp"] = float(p["xp"]) + t
			GameState._spend_banks(p, off)
		if int(Rating.ovr(p)) >= pot:
			return "%d(from %d)" % [g, start]
	return ">400(at %d)" % int(Rating.ovr(p))
