class_name ReservesForm
extends RefCounted
## Form in the reserves, and the form marks on Team selection (director,
## 2026-11-12: "team select should highlight the 3 players in the side in the
## worst form, and the 3 players in reserve in the best form"; a reserve's
## form is "Reserves games").
##
## Each week your club plays, every player left out but fit (the reserves test
## of the match XP, GameState._grant_xp) turns out in the twos: a game line
## from his own ratings and a roll, rated on the senior Player Rating scale
## (MatchNotes.rating). Display only: it never changes a match, XP,
## development or any other sim number. Its roll is its own generator, seeded
## from the career, the match and the player, so no other draw in the career
## moves and a replay rolls the same game.
##
## GameState keeps the record, reserves_log: player id -> {"last": [game x3],
## "sum", "n", "key"}. A game is {"pts", "d" (disposals), "g" (goals),
## "h" (hitouts)}; "key" is the match the latest game was played beside.

const GAMES := 3              # the reserves games a mark counts back over, as senior form (GameState.FORM_GAMES)
const MARKS := 3              # players marked each way
const SENIOR_MIN_GAMES := 5   # senior games this season before his form is read (GameState.player_form)

## A role's game in the twos at an ordinary level for a senior-list player:
## the counts MatchNotes.RATING_POINTS rates.
const LINE := {
	"MID": {"kicks": 13.0, "handballs": 10.0, "marks": 4.0, "tackles": 5.0, "inside50": 4.0, "clangers": 3.0, "goals": 0.7},
	"FWD": {"kicks": 8.0, "handballs": 4.0, "marks": 6.0, "tackles": 3.0, "inside50": 2.0, "clangers": 2.0, "goals": 2.2, "behinds": 1.5},
	"DEF": {"kicks": 12.0, "handballs": 6.0, "marks": 6.0, "tackles": 2.0, "rebounds": 5.0, "one_percenters": 4.0, "spoils": 2.0, "clangers": 2.0, "goals": 0.1},
	"RUCK": {"kicks": 6.0, "handballs": 7.0, "marks": 3.0, "tackles": 3.0, "hitouts": 28.0, "clangers": 2.0, "goals": 0.4},
}


## The roll's seed: the career, the match and the player.
static func seed_for(career_seed: int, match_key: String, id: String) -> int:
	return hash([career_seed, match_key, id])


## One game in the twos: {"pts", "d", "g", "h"}.
static func game(p: Dictionary, seed: int) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var role := str(p.get("role", "MID"))
	var base: Dictionary = LINE.get(role, LINE["MID"])
	# A better player stands out more against the twos; the day can go either way.
	var q := clampf((float(p.get("overall", 60)) - 55.0) / 30.0, 0.0, 1.3)
	var m := clampf(0.75 + 0.5 * q + rng.randfn(0.0, 0.22), 0.3, 1.8)
	var st := {}
	for k in base:
		var v := float(base[k]) * (m if k != "clangers" else 1.0)
		if k == "goals" or k == "behinds":
			st[k] = maxi(0, int(round(v + rng.randfn(0.0, 0.8))))
		else:
			st[k] = maxi(0, int(round(v + rng.randfn(0.0, 1.5))))
	return {
		"pts": MatchNotes.rating(st),
		"d": int(st.get("kicks", 0)) + int(st.get("handballs", 0)),
		"g": int(st.get("goals", 0)),
		"h": int(st.get("hitouts", 0)),
	}


## Add a game to his record in `log` (changed in place).
static func record(log: Dictionary, id: String, g: Dictionary, match_key: String) -> void:
	var f: Dictionary = log.get(id, {"last": [], "sum": 0, "n": 0})
	var last: Array = f["last"]
	last.append(g)
	f["last"] = last.slice(maxi(0, last.size() - GAMES))
	f["sum"] = int(f["sum"]) + int(g["pts"])
	f["n"] = int(f["n"]) + 1
	f["key"] = match_key
	log[id] = f


## A game in football words: "Kicked 3 and 22 touches in the twos".
static func line(g: Dictionary) -> String:
	var parts := PackedStringArray()
	if int(g.get("h", 0)) >= 10:
		parts.append("%d hitouts" % int(g["h"]))
	if int(g.get("g", 0)) > 0:
		parts.append("kicked %d" % int(g["g"]))
	parts.append("%d touches" % int(g.get("d", 0)))
	var s := " and ".join(parts) if parts.size() <= 2 else "%s, %s and %s" % [parts[0], parts[1], parts[2]]
	return s.substr(0, 1).to_upper() + s.substr(1) + " in the twos"


## The marks: the MARKS players in `side_ids` whose last GAMES senior games
## sit furthest below their own season, and the MARKS players in `reserve_ids`
## (fit, not in the side) whose last GAMES reserves games sit furthest above
## their own reserves season, if they played in the twos at the club's latest
## match (`latest_key`). {"cold": {id: {"recent", "season", "gap"}},
## "hot": {id: {"recent", "season", "gap", "games", "last"}}}. Fewer qualify, fewer marked.
static func marks(side_ids: Array, reserve_ids: Array, form_log: Dictionary,
		reserves_log: Dictionary, latest_key: String) -> Dictionary:
	var cold := []
	for id in side_ids:
		var f: Dictionary = form_log.get(str(id), {})
		var last: Array = f.get("last", [])
		var n := int(f.get("n", 0))
		if last.size() < GAMES or n < SENIOR_MIN_GAMES:
			continue
		var recent := 0.0
		for x in last:
			recent += float(x)
		recent /= float(last.size())
		var season := float(f["sum"]) / float(n)
		if recent < season:
			cold.append({"id": str(id), "recent": int(round(recent)), "season": int(round(season)),
					"gap": recent - season})
	cold.sort_custom(func(a, b):
		return float(a["gap"]) < float(b["gap"]) or (float(a["gap"]) == float(b["gap"]) and str(a["id"]) < str(b["id"])))
	var hot := []
	for id in reserve_ids:
		var f: Dictionary = reserves_log.get(str(id), {})
		var last: Array = f.get("last", [])
		var n := int(f.get("n", 0))
		if last.size() < GAMES or n < SENIOR_MIN_GAMES or latest_key == "" or str(f.get("key", "")) != latest_key:
			continue
		var recent := 0.0
		for g in last:
			recent += float((g as Dictionary).get("pts", 0))
		recent /= float(last.size())
		var season := float(f["sum"]) / float(n)
		if recent > season:
			hot.append({"id": str(id), "recent": int(round(recent)), "season": int(round(season)),
					"gap": recent - season, "games": last.size(), "last": last.back()})
	hot.sort_custom(func(a, b):
		return float(a["gap"]) > float(b["gap"]) or (float(a["gap"]) == float(b["gap"]) and str(a["id"]) < str(b["id"])))
	var out := {"cold": {}, "hot": {}}
	for r in cold.slice(0, MARKS):
		out["cold"][r["id"]] = r
	for r in hot.slice(0, MARKS):
		out["hot"][r["id"]] = r
	return out


## The cold mark's short form, for a tile: "Form -23".
static func cold_short(r: Dictionary) -> String:
	return "Form %d" % (int(r["recent"]) - int(r["season"]))


## The cold mark in full: "Last 3 games: 38 a game. This season: 61."
static func cold_full(r: Dictionary) -> String:
	return "Match rating, last %d games: %d a game. This season: %d a game." % [GAMES, int(r["recent"]), int(r["season"])]


## The hot mark's short form, for a card, as the side's: "Form +12".
static func hot_short(r: Dictionary) -> String:
	return "Form +%d" % (int(r["recent"]) - int(r["season"]))


## The hot mark in full: "Match rating in the reserves, last 3 games: 82 a game. This season: 70 a game. Latest: ..."
static func hot_full(r: Dictionary) -> String:
	return "Match rating in the reserves, last %d games: %d a game. This season: %d a game. Latest: %s." % [
			GAMES, int(r["recent"]), int(r["season"]), line(r["last"]).to_lower().trim_suffix(" in the twos")]


## His form on his profile, a sentence each: the senior games this season
## (his last GAMES against his season) and his games in the twos. [] when he
## has played neither this season.
static func profile_lines(form_log: Dictionary, reserves_log: Dictionary, id: String) -> PackedStringArray:
	var out := PackedStringArray()
	var f: Dictionary = form_log.get(id, {})
	var n := int(f.get("n", 0))
	if n > 0:
		var last: Array = f.get("last", [])
		var recent := 0.0
		for x in last:
			recent += float(x)
		recent /= float(maxi(1, last.size()))
		out.append("Seniors: %d a game over his last %s, %d over %s this season." % [int(round(recent)),
				"game" if last.size() == 1 else "%d games" % last.size(),
				int(round(float(f["sum"]) / float(n))), "1 game" if n == 1 else "%d games" % n])
	var r: Dictionary = reserves_log.get(id, {})
	var rn := int(r.get("n", 0))
	if rn > 0:
		var rlast: Array = r.get("last", [])
		var rrecent := 0.0
		for g in rlast:
			rrecent += float((g as Dictionary).get("pts", 0))
		rrecent /= float(maxi(1, rlast.size()))
		out.append("Reserves: %d a game over his last %s, %d over %s this season. Latest: %s." % [int(round(rrecent)),
				"game" if rlast.size() == 1 else "%d games" % rlast.size(),
				int(round(float(r["sum"]) / float(rn))), "1 game" if rn == 1 else "%d games" % rn,
				line(rlast.back()).to_lower().trim_suffix(" in the twos")])
	return out
