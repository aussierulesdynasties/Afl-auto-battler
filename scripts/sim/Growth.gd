class_name Growth
extends RefCounted
## Training and potential, the director's design (docs/DIRECTOR_BIBLE.md,
## "Training and potential, his design (2026-11-17)"; TODO row 204).
##
## Growth is XP earned: a week's XP is two-thirds match, one-third training.
## A kid drafted at 60 who plays every ordinary game reaches his potential
## after the games in PACE (85 and up: 150 games). The same potential earns
## the same rating points a game whatever he was drafted at, so a 70 gets
## there before a 60. XP is priced in rating points (xp_per_point), so the
## pace holds for every role and every rating.
##
## Every attribute but Discipline and Work Rate also moves with his age, a
## little each round (age_round; RATING_REBUILD §4). Once his career is over
## every season's gains are temporary and he falls 2, 3, 2, 3. How long he
## lasts is rolled from real careers with a similar peak (career_last).

## [potential, games to reach it from a draft rating of 60]. 85 and up: 150.
## Between two rows the games fill in a straight line (72 -> 110).
const PACE := [[65, 65], [70, 100], [75, 125], [80, 140], [85, 150]]
const DRAFT_BASE := 60.0
const MATCH_SHARE := 2.0 / 3.0
const TRAIN_SHARE := 1.0 / 3.0
## A VFL (reserves) game is half a senior game's match XP.
const VFL_SHARE := 0.5
## An ordinary senior game's XP (GameState._xp_amount): measured over a
## season (tools/audit/zz_xpgame_impl.gd, seed 301: median 37, 81% of games
## reach it). A good game earns more than a quiet one in the same ratio as
## before; 150 games is the pace of ordinary games.
const ORDINARY_GAME_XP := 37.0

## The fall a season once his career is over: 2, 3, 2, 3 (2.5 a season).
const FALL := [2, 3]
## A season he missed this many games injured takes a quarter of a season off
## his career.
const INJURY_GAMES := 10
const INJURY_CUT := 0.25
## Breakouts: about half a player a club a season, a mid-tier player (rated
## 60 to 75, any age), +4 to +6 that he keeps on each of the three attributes
## his position weighs most (RATING_REBUILD §4).
const BREAKOUTS_PER_CLUB := 0.5
const BREAKOUT_MIN := 60
const BREAKOUT_MAX := 75
const BREAKOUT_JUMP := [4, 6]
const BREAKOUT_ATTRS := 3

## The age curves: each attribute's average move from one season to the next
## at each age, real players 2012-25 (tools/wheelo/league.py). An age the
## file has no row for moves nothing.
const CURVES_CSV := "res://data/age_curves.csv"
## Speed and Strength (director 2026-11-25, question box: "Blueprint curves"):
## Speed holds to 26, -1.5 a season from 27, -3 from 31; Strength holds to
## 31, -1 a season from 32. Their growth before that is XP's.
##   [first age, change a season], latest first.
const SPEED_CURVE := [[31, -3.0], [27, -1.5]]
const STRENGTH_CURVE := [[32, -1.0]]

## {attribute: {age: change a season}}.
static var _curves := {}

## Careers to roll from (data/legacy/classes.csv): drafts in these years,
## all finished.
const CAREER_FROM := 1990
const CAREER_TO := 2008
## Similar peak: within this of his potential, wider while fewer than
## CAREER_MIN careers match.
const CAREER_NEAR := 3
const CAREER_MIN := 10
## The last season the real-player data runs to: a real_last at or past it
## means he was still playing, so his length is rolled.
const DATA_LAST := 2025


## Rating points a game for this potential (ordinary senior games, every game).
static func points_per_game(pot: int) -> float:
	if pot >= int(PACE[PACE.size() - 1][0]):
		return (float(pot) - DRAFT_BASE) / float(PACE[PACE.size() - 1][1])
	if pot <= int(PACE[0][0]):
		return (float(PACE[0][0]) - DRAFT_BASE) / float(PACE[0][1])
	for i in range(PACE.size() - 1):
		var a: Array = PACE[i]
		var b: Array = PACE[i + 1]
		if pot <= int(b[0]):
			var t := float(pot - int(a[0])) / float(int(b[0]) - int(a[0]))
			var games := float(a[1]) + t * float(int(b[1]) - int(a[1]))
			return (float(pot) - DRAFT_BASE) / games
	return 0.0


## Games to his potential from a draft rating of 60 (the pace table read back).
static func games_to_potential(pot: int) -> float:
	var ppg := points_per_game(pot)
	return (float(maxi(pot, int(DRAFT_BASE + 1))) - DRAFT_BASE) / ppg if ppg > 0.0 else 0.0


## The XP one point of his rating costs now: the cheapest of his position's
## rated attributes, priced as training buys them (GameState._cost_for)
## against what a point of that attribute adds to his OVR (its weight at his
## AFL position, Rating.shares, times the stretch's slope where he is).
static func xp_per_point(p: Dictionary) -> float:
	var a: Dictionary = p.get("attr", {})
	var games := float(p.get("gm", 18.0))
	var best := 0.0
	var w := Rating.shares(p)
	var lift := Rating.slope(Rating.raw_of(a, Rating.apos_of(p)))
	for k in w:
		if not a.has(k) or int(a[k]) >= 99:
			continue
		var per := float(w[k]) * lift
		if per <= 0.0:
			continue
		var price := float(cost(int(a[k]), games)) / per
		if best == 0.0 or price < best:
			best = price
	return best


## What one stat point costs at this level (the training price; no potential
## pricing).
static func cost(cur: int, games: float) -> int:
	var exp_mult := clampf(0.70 + games / 40.0, 0.70, 1.20)
	return maxi(int(round(8.0 * TRAIN_COST_SCALE)),
			int(round((8.0 + float(cur) * 0.40) * exp_mult * TRAIN_COST_SCALE)))


## Kept from the old price (GameState.TRAIN_COST_SCALE): it only sets the size
## of an XP point; the pace above sets how fast he grows.
const TRAIN_COST_SCALE := 1.25


## His match XP for the week before his club's multipliers. `game`: 1.0 an
## ordinary senior game (his game's XP over ORDINARY_GAME_XP), VFL_SHARE a
## reserves game, 0 when he did not play.
static func match_xp(p: Dictionary, game: float) -> float:
	if game <= 0.0:
		return 0.0
	return points_per_game(int(p.get("potential", Rating.ovr(p, 60)))) * MATCH_SHARE \
			* game * xp_per_point(p)


## His training XP for the week before his club's multipliers.
static func train_xp(p: Dictionary) -> float:
	return points_per_game(int(p.get("potential", Rating.ovr(p, 60)))) * TRAIN_SHARE \
			* xp_per_point(p)


# ---------------------------------------------------------------------------
# How long he lasts
# ---------------------------------------------------------------------------
static var _careers: Array = []
static var _fine_wine_keys := {}


static func _load_careers() -> void:
	if not _careers.is_empty():
		return
	if _fine_wine_keys.is_empty():
		var fw := FileAccess.open("res://data/fine_wine.csv", FileAccess.READ)
		if fw != null:
			fw.get_csv_line()
			while not fw.eof_reached():
				var r := fw.get_csv_line()
				if r.size() >= 3 and r[0] != "":
					_fine_wine_keys["%s|%s|%s" % [r[0].to_lower(), r[1].to_lower(), r[2]]] = true
	var f := FileAccess.open("res://data/legacy/classes.csv", FileAccess.READ)
	if f == null:
		return
	var head := f.get_csv_line()
	var col := {}
	for i in range(head.size()):
		col[head[i]] = i
	while not f.eof_reached():
		var r := f.get_csv_line()
		if r.size() < head.size():
			continue
		var year := int(r[col["year"]])
		if year < CAREER_FROM or year > CAREER_TO or r[col["last_season"]] == "" or r[col["peak"]] == "":
			continue
		var key := "%s|%s|%s" % [r[col["first"]].to_lower(), r[col["last"]].to_lower(), r[col["dob"]]]
		_careers.append({"peak": int(r[col["peak"]]),
				"seasons": int(r[col["last_season"]]) - year,
				"fine_wine": _fine_wine_keys.has(key)})


## Roll a career length in seasons for this potential, from real careers with
## a similar peak (Fine Wine players from Fine Wine careers), at least
## `at_least` seasons.
static func roll_seasons(pot: int, fine_wine: bool, at_least: int, rng: RandomNumberGenerator) -> int:
	_load_careers()
	var pool := []
	for c in _careers:
		if fine_wine and not bool(c["fine_wine"]):
			continue
		if int(c["seasons"]) >= at_least:
			pool.append(c)
	if pool.is_empty():
		return at_least
	var near := CAREER_NEAR
	var picks := []
	while true:
		picks.clear()
		for c in pool:
			if absi(int(c["peak"]) - pot) <= near:
				picks.append(c)
		if picks.size() >= CAREER_MIN or picks.size() == pool.size():
			break
		near += 1
	return int(picks[rng.randi_range(0, picks.size() - 1)]["seasons"])


## His last season (quarters kept: an injured season takes INJURY_CUT off).
## Rolled once and kept: a real player's own last season while the data has
## it; otherwise from real careers with a similar peak, counted from his draft
## (or his debut), and never before the season he is playing.
static func career_last(p: Dictionary, season_year: int) -> float:
	if p.has("career_last"):
		return float(p["career_last"])
	var last := 0.0
	var real_last := int(p.get("real_last", 0))
	if real_last > 0 and real_last < DATA_LAST:
		last = float(real_last)
	else:
		var start := _first_season(p, season_year)
		var played := maxi(0, season_year - start)
		var rng := Prospects._rng_for("%s|career" % str(p.get("id", "")))
		var pot := int(p.get("potential", Rating.ovr(p, 60)))
		var n := roll_seasons(pot, Traits.fine_wine(p), played + 1, rng)
		last = float(start - 1 + n)
	last = maxf(last, float(season_year))
	p["career_last"] = last
	return last


## The season he first played (or will): his draft year plus one, his debut,
## or this season for a player with neither on record.
static func _first_season(p: Dictionary, season_year: int) -> int:
	if p.has("drafted_year"):
		return int(p["drafted_year"]) + 1
	var debut := str(p.get("debut", ""))
	if debut.length() >= 4:
		var y := int(debut.right(4)) if debut.contains("-") and debut.length() == 10 and debut[2] == "-" else int(debut.left(4))
		if y > 1800:
			return y
	return season_year


# ---------------------------------------------------------------------------
# The summer
# ---------------------------------------------------------------------------
## One player's summer after season `year` (the one just played): an injured
## season shortens his career; once his career is over, the season's gains go
## and he falls, every attribute but Discipline by the same points
## (Rating.shift_to). Returns the rating change.
static func summer(p: Dictionary, year: int) -> int:
	var a: Dictionary = p.get("attr", {})
	var ov := int(Rating.ovr(p, 0))
	if a.is_empty():
		return 0
	var last := career_last(p, year)
	if int(p.get("games_missed_injured", 0)) >= INJURY_GAMES:
		last -= INJURY_CUT
		p["career_last"] = last
	if year >= int(round(last)):
		# His career is over: the season's gains were temporary, and he falls.
		_take_back(a, p.get("season_gains", {}), 1.0)
		p["attr"] = a
		var now := int(Rating.ovr(p))
		var n := int(p.get("decline_n", 0))
		var fall := int(FALL[n % FALL.size()])
		p["decline_n"] = n + 1
		p["attr"] = Rating.shift_to(a, Rating.apos_of(p), float(now - fall))
	return int(Rating.ovr(p)) - ov


## Grow him as if he played `games` ordinary senior games on his position
## plan, by the game's own grant and spending (no club multipliers). For
## audits and tests that need a class some seasons on; the season itself
## grows players game by game (GameState._grant_xp).
static func play_games(p: Dictionary, games: int) -> void:
	var w := Rating.shares(p)
	for g in range(games):
		p["xp_match"] = float(p.get("xp_match", 0.0)) + match_xp(p, 1.0)
		p["xp"] = float(p.get("xp", 0.0)) + train_xp(p)
		GameState._spend_banks(p, w)


## Take `share` of each stat's gains back off, in whole points (half up).
static func _take_back(a: Dictionary, gains: Dictionary, share: float) -> void:
	for k in gains:
		if not a.has(k):
			continue
		var n := float(gains[k]) * share
		var whole := int(floor(n))
		if n - float(whole) >= 0.5:
			whole += 1
		a[k] = clampi(int(a[k]) - whole, 1, 99)


## A club's breakouts this summer: each mid-tier player (rated BREAKOUT_MIN to
## BREAKOUT_MAX) has an equal share of BREAKOUTS_PER_CLUB; one who breaks out
## gains 4 to 6 on each of the three attributes his position weighs most
## (top_weighted) and keeps it. Returns [[id, OVR change]].
## Example: a Midfielder who rolls +5 gains 5 Contested ball, Kicking and
## Handballing (weights 22, 12 and 12 of 100): OVR +2.3.
static func breakouts(code: String, arr: Array, year: int) -> Array:
	var eligible := []
	for p in arr:
		var ov := int(Rating.ovr(p, 0))
		if ov >= BREAKOUT_MIN and ov <= BREAKOUT_MAX and not (p.get("attr", {}) as Dictionary).is_empty():
			eligible.append(p)
	var out := []
	if eligible.is_empty():
		return out
	var chance := BREAKOUTS_PER_CLUB / float(eligible.size())
	var rng := Prospects._rng_for("breakout|%s|%d" % [code, year])
	for p in eligible:
		if rng.randf() >= chance:
			continue
		var jump := rng.randi_range(int(BREAKOUT_JUMP[0]), int(BREAKOUT_JUMP[1]))
		var ov := int(Rating.ovr(p))
		var a: Dictionary = p["attr"]
		for key in top_weighted(Rating.apos_of(p)):
			a[key] = clampi(int(a.get(key, 50)) + jump, 1, 99)
		var story: Array = p.get("breakouts", [])
		story.append([year, int(Rating.ovr(p)) - ov])
		p["breakouts"] = story
		out.append([str(p.get("id", "")), int(Rating.ovr(p)) - ov])
	return out


## The BREAKOUT_ATTRS attributes `apos` weighs most; a tie goes to the one
## first in Attributes.KEYS.
static func top_weighted(apos: String) -> Array:
	var w: Dictionary = Rating.WEIGHTS.get(apos, Rating.WEIGHTS["Midfielder"])
	var keys := []
	for k in Attributes.KEYS:
		if w.has(k):
			keys.append(k)
	keys.sort_custom(func(x, y): return int(w[x]) > int(w[y]) or (int(w[x]) == int(w[y])
			and Attributes.KEYS.find(x) < Attributes.KEYS.find(y)))
	return keys.slice(0, BREAKOUT_ATTRS)


# ---------------------------------------------------------------------------
# Age curves (RATING_REBUILD §4)
# ---------------------------------------------------------------------------
## How far `key` moves in a season he plays at `age` (whole years).
## Example: Kicking at 20 moves +1.37 a season; Speed at 28 moves -1.5.
static func age_change(key: String, age: int) -> float:
	match key:
		"speed":
			return _stepped(SPEED_CURVE, age)
		"strength":
			return _stepped(STRENGTH_CURVE, age)
	return float((_load_curves().get(key, {}) as Dictionary).get(age, 0.0))


static func _stepped(curve: Array, age: int) -> float:
	for step in curve:
		if age >= int(step[0]):
			return float(step[1])
	return 0.0


static func _load_curves() -> Dictionary:
	if not _curves.is_empty():
		return _curves
	var f := FileAccess.open(CURVES_CSV, FileAccess.READ)
	if f == null:
		return _curves
	var head := f.get_csv_line()
	var col := {}
	for i in head.size():
		col[head[i]] = i
	while not f.eof_reached():
		var r := f.get_csv_line()
		if r.size() < head.size() or str(r[0]) == "":
			continue
		var key := str(r[col["attribute"]])
		if not _curves.has(key):
			_curves[key] = {}
		(_curves[key] as Dictionary)[int(r[col["age"]])] = float(r[col["change"]])
	return _curves


## One regular round of ageing for every listed player: each attribute moves
## 1/`rounds` of its season's change at his age, the fractions kept in
## "age_carry" until they make a whole point. A rise waits while his OVR is
## at his POT (no gains at his potential, 11-23).
## Example: Endurance at 20 (+6.04 a season) over 24 rounds moves 0.25 a
## round, a whole point every fourth round.
static func age_round(lists: Dictionary, rounds: int) -> void:
	var share := 1.0 / float(maxi(1, rounds))
	for code in lists:
		for p in lists[code]:
			age_step(p, share)


## Move one player `share` of a season along his age curves.
static func age_step(p: Dictionary, share: float) -> void:
	var a: Dictionary = p.get("attr", {})
	if a.is_empty():
		return
	var age := int(floor(float(p.get("age", 25.0))))
	var pot := int(p.get("potential", 0))
	var carry: Dictionary = p.get("age_carry", {})
	for key in Attributes.KEYS:
		var c := age_change(key, age) * share
		if c == 0.0:
			continue
		if c > 0.0 and pot > 0 and int(Rating.ovr(p, 0)) >= pot:
			continue
		var v := float(carry.get(key, 0.0)) + c
		var whole := int(v) # toward zero: a part point waits
		if whole != 0:
			a[key] = clampi(int(a.get(key, 50)) + whole, 1, 99)
			v -= float(whole)
		carry[key] = v
	p["age_carry"] = carry


## Attributes moved by every season's change from `from_age` up to (not
## including) `to_age`, rounded once at the end, within 1-99: a player made
## at an age past his first season (Prospects._age_into).
## Example: Kicking from 19 to 22 adds the changes at 19, 20 and 21.
static func age_attrs(a: Dictionary, from_age: int, to_age: int) -> Dictionary:
	var out := {}
	for key in a:
		var moved := float(a[key])
		for age in range(from_age, to_age):
			moved += age_change(str(key), age)
		out[key] = clampi(int(round(moved)), 1, 99)
	return out
