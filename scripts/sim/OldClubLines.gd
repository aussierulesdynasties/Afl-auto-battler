class_name OldClubLines
extends RefCounted
## Storylines before the bounce, beat 3 (director, 2026-11-06, T5.Q9 "Build,
## 100+ games"): a player in this week's sides who meets a club he played
## 100 or more games for. Pure rules from his Career stints (every spell at
## that club, real AFL seasons to 2025 and this career); writes nothing, adds
## no randomness and is never read by the match.
##
## Two kinds, the same fact:
##   yours    one of your side who played 100+ for the opposition
##   theirs   one of their side who played 100+ for you
## A player on 99 games at that club gets no line. One already named by the
## one-who-got-away line (FormerPlayers) is left to that line, so no player is
## told twice.

## Games at the old club before he earns a line (T5.Q9).
const MIN_GAMES := 100
## The pre-match storylines at most, this line and FormerPlayers' together
## (design bible ruling 90: a cap of three a match).
const MATCH_CAP := 3


## His games for `club`, every spell, from his Career stints.
static func stint_games(p: Dictionary, club: String) -> int:
	var g := 0
	for st in Career.of(p).get("stints", []):
		if st is Array and (st as Array).size() >= 4 and str(st[0]) == club:
			g += int(st[3])
	return g


## The old-club rows for a match, the most games first:
## [{"id", "p", "old" (club code), "games", "mine" (true for your player)}].
## `mine` and `theirs` are the two sides' players, `games_at` a
## Callable(p, club) -> int (stint_games when not given), `skip` ids to leave out.
static func rows(mine: Array, theirs: Array, my_club: String, opp_club: String,
		games_at := Callable(), skip := {}) -> Array:
	var out := []
	if my_club == "" or opp_club == "" or my_club == opp_club:
		return out
	for side in [[mine, opp_club, true], [theirs, my_club, false]]:
		var old: String = side[1]
		for p in side[0]:
			if not (p is Dictionary):
				continue
			var id := str(p.get("id", ""))
			if id == "" or skip.has(id) or str(p.get("club", "")) == old:
				continue
			var g := int(games_at.call(p, old)) if games_at.is_valid() else stint_games(p, old)
			if g < MIN_GAMES:
				continue
			out.append({"id": id, "p": p, "old": old, "games": g, "mine": side[2]})
	out.sort_custom(func(a, b):
		if int(a["games"]) != int(b["games"]):
			return int(a["games"]) > int(b["games"])
		return str(a["id"]) < str(b["id"]))
	return out


## "Jack Gunston faces his old club: 239 games for Hawthorn." Your club is
## "you": "Jack Gunston faces his old club: 239 games for you."
## `name` is his display name, `club` the old club's name.
static func line(row: Dictionary, name: String, club: String) -> String:
	var where := club if bool(row.get("mine", false)) else "you"
	return "%s faces his old club: %d games for %s." % [name, int(row.get("games", 0)), where]
