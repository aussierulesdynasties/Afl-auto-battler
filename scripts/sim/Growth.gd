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
## Past his peak a summer takes back part of what he trained past his
## potential, climbing to all of it by his last real season; after that every
## season's gains are temporary and he falls 2, 3, 2, 3. How long he lasts is
## rolled from real careers with a similar peak (career_last).

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

## The take-away past his peak: this share of what he trained past his
## potential in the first summer after it, climbing to all of it by his last
## real season.
const TAKE_FIRST := 0.4
## The fall a season once his career is over: 2, 3, 2, 3 (2.5 a season).
const FALL := [2, 3]
## A season he missed this many games injured takes a quarter of a season off
## his career.
const INJURY_GAMES := 10
const INJURY_CUT := 0.25
## Breakouts: about half a player a club a season, a mid-tier player (rated
## 60 to 75, any age), +5 to +8 that he keeps.
const BREAKOUTS_PER_CLUB := 0.5
const BREAKOUT_MIN := 60
const BREAKOUT_MAX := 75
const BREAKOUT_JUMP := [5, 8]

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
## rating stats, priced as training buys them (GameState._cost_for) against
## what a point of that stat adds to his rating (Ratings.overall_per_point).
static func xp_per_point(p: Dictionary, role := "") -> float:
	if role == "":
		role = str(p.get("role", "MID"))
	var a: Dictionary = p.get("attr", {})
	var games := float(p.get("gm", 18.0))
	var conf_games := Ratings.effective_games(p)
	var best := 0.0
	var w: Dictionary = Ratings.ROLE_WEIGHTS.get(role, Ratings.ROLE_WEIGHTS["MID"])
	for k in w:
		if not a.has(k) or int(a[k]) >= 99:
			continue
		var per := Ratings.overall_per_point(role, str(k), conf_games)
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
## reserves game, 0 when he did not play. `per_point`: his xp_per_point when
## the caller has it already (a week prices it once for both XPs).
static func match_xp(p: Dictionary, game: float, per_point := -1.0) -> float:
	if game <= 0.0:
		return 0.0
	if per_point < 0.0:
		per_point = xp_per_point(p)
	return points_per_game(int(p.get("potential", Rating.ovr(p, 60)))) * MATCH_SHARE \
			* game * per_point


## His training XP for the week before his club's multipliers.
static func train_xp(p: Dictionary, per_point := -1.0) -> float:
	if per_point < 0.0:
		per_point = xp_per_point(p)
	return points_per_game(int(p.get("potential", Rating.ovr(p, 60)))) * TRAIN_SHARE \
			* per_point


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
## season shortens his career; past his peak, part of what he trained past his
## potential goes; once his career is over, the season's gains go and he
## falls. Returns the rating change.
static func summer(p: Dictionary, year: int) -> int:
	var a: Dictionary = p.get("attr", {})
	var ov := int(Rating.ovr(p, 0))
	if a.is_empty():
		return 0
	var last := career_last(p, year)
	if int(p.get("games_missed_injured", 0)) >= INJURY_GAMES:
		last -= INJURY_CUT
		p["career_last"] = last
	var role := str(p.get("role", "MID"))
	var games := Ratings.effective_games(p)
	if year >= int(round(last)):
		# His career is over: the season's gains were temporary, and he falls.
		_take_back(a, p.get("season_gains", {}), 1.0)
		p["attr"] = a
		var now := Ratings.rate_overall(a, role, games)
		var n := int(p.get("decline_n", 0))
		var fall := int(FALL[n % FALL.size()])
		p["decline_n"] = n + 1
		p["attr"] = Prospects.fit_attributes(a, role, float(now - fall), games)
	elif p.has("peak_year") and not (p.get("over_gains", {}) as Dictionary).is_empty():
		var peak := int(p["peak_year"])
		var span := maxf(1.0, round(last) - float(peak))
		var f := clampf(TAKE_FIRST + (1.0 - TAKE_FIRST) * float(year - peak) / span, TAKE_FIRST, 1.0)
		_take_back(a, p["over_gains"], f)
		p["attr"] = a
	p["overall"] = Ratings.rate_overall(p["attr"], role, games)
	p["value"] = Ratings.salary_value(int(Rating.ovr(p)))
	return int(Rating.ovr(p)) - ov


## Grow him as if he played `games` ordinary senior games on his position
## plan, by the game's own grant and spending (no club multipliers). For
## audits and tests that need a class some seasons on; the season itself
## grows players game by game (GameState._grant_xp).
static func play_games(p: Dictionary, games: int) -> void:
	var w: Dictionary = Ratings.ROLE_WEIGHTS.get(str(p.get("role", "MID")), Ratings.ROLE_WEIGHTS["MID"])
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
## jumps 5 to 8 and keeps it. Returns [[id, jump]].
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
		var role := str(p.get("role", "MID"))
		var games := Ratings.effective_games(p)
		var ov := int(Rating.ovr(p))
		p["attr"] = Prospects.fit_attributes(p["attr"], role, float(ov + jump), games)
		p["overall"] = Ratings.rate_overall(p["attr"], role, games)
		p["value"] = Ratings.salary_value(int(Rating.ovr(p)))
		var story: Array = p.get("breakouts", [])
		story.append([year, int(Rating.ovr(p)) - ov])
		p["breakouts"] = story
		out.append([str(p.get("id", "")), int(Rating.ovr(p)) - ov])
	return out
