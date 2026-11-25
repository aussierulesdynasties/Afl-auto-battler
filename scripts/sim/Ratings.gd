class_name Ratings
extends RefCounted
## Derives 1-99 attributes, position, overall rating and draft value from raw
## AFL Tables season stats.
##
## Direct port of tools/sim_harness.py::derive_ratings, which stays a live
## mirror (tools/build_history.py and render_preview.py import it): a rating
## constant that changes here changes there too.

## Tunables - single source of truth for match balance. The copy in
## tools/sim_harness.py (dict `T`) is stale since 2026-10-08; do not mirror
## match tunables there. Guard: tests/run_calibration_tests.gd.
const T := {
	"chains_per_game": 200,          # possession chains across BOTH teams
	"max_touches_per_chain": 14,
	"forward50_line": 35.0,          # metres from the centre square
	"goal_line": 85.0,
	"metres_gain_mean": 9.7,         # base metres per effective disposal
	"tackle_retention": 0.44,        # attacking team wins the ball back
	"pressure_base": 0.160,          # chance a touch is tackled
	"clanger_per_chain": 0.625,     # chance the chain ends in an error
	"clanger_is_free": 0.43,         # ...of which are free kicks against
	"mark_share_of_kicks": 0.240,    # 0.280 before the D50 chip (2026-11-14): chips are marked 2.8x as often; 0.327 before the D50 clearing kick (2026-11-07): marks per kick back to real (0.43)
	"handball_share": Skills.HANDBALL_SHARE,
	"inside50_goal": 0.262,          # of inside-50 entries (0.279 before frees in 50 became set shots, backlog item 24; 0.269 before forward archetypes, ARD-M3-002)
	"inside50_behind": 0.180,
	"stoppage_share": 0.42,          # chains that begin at a genuine stoppage
	"hitouts_per_stoppage": 0.78,    # split between the two rucks
	"clearance_per_stoppage": 0.76,  # to the team that wins the stoppage (0.815 before every feature was on: 38.9 a team, real 36.1)
	"one_percenter_share": 0.72,     # of inside-50 entries that yield a 1% (0.78 before the row 136 spoils tuning added credits)
	"rebound_on_exit": 0.55,         # defensive-half chains that yield a reb50
	"shooter_power": 0.5,            # how strongly shots go to the best kicks
	"shrink_games": 5.0,             # sample-size shrink for per-game rates
	"shrink_accuracy": 14.0,         # sample-size shrink for goal conversion
	"home_ground_bonus": 0.030,
	"contest_swing": 360.0,          # higher == less sensitive to strength
	"contest_clamp": 0.60,           # max stoppage win probability
}

## Match flow (row 11, director 2026-10-10): stoppages come from contests that
## lock up, a won ball is played on, chains are shorter and more numerous. These
## replace the same keys in T for every match. Measured against main's current calibration
## (after #885): docs/research/MATCH_FLOW_AUDIT_2026-11-04.md has the bands, and
## three still fall short. These are absolute values, not offsets: a later change
## to T for these keys does not reach a match until FLOW is updated too
## (tests/test_match_flow.gd checks every key here still exists in T).
const FLOW := {
	"chains_per_game": 255,         # 275 before kicks went longer (row 201 gap 6)
	"max_touches_per_chain": 10,
	"metres_gain_mean": 11.3,
	"tackle_retention": 0.25,
	"inside50_goal": 0.255,         # 0.235 before the D50 clearing kick (2026-11-07): goals per entry back to real (0.24)
	"inside50_behind": 0.175,
}

## (metric name, source stat column). "hb" is special-cased as di - ki.
const METRIC_SPECS := [
	["disposals_pg", "di"], ["kicks_pg", "ki"], ["marks_pg", "mk"],
	["handballs_pg", "hb"], ["goals_pg", "gl"], ["behinds_pg", "bh"],
	["hitouts_pg", "ho"], ["tackles_pg", "tk"], ["rebounds_pg", "rb"],
	["inside50s_pg", "if50"], ["clearances_pg", "cl"], ["clangers_pg", "cg"],
	["frees_for_pg", "ff"], ["frees_against_pg", "fa"], ["brownlow_pg", "br"],
	["contested_pg", "cp"], ["contested_marks_pg", "cm"],
	["marks_inside50_pg", "mi"], ["one_percenters_pg", "onepct"],
	["bounces_pg", "bo"], ["goal_assists_pg", "ga"],
]

## On-ground structure: 18 players = 6 DEF, 6 MID, 6 FWD, where the ruck is
## counted with midfield (1 RUCK + 5 MID). Order matters - select_22() fills
## slots in this sequence.
const GROUND_SLOTS := [["RUCK", 1], ["MID", 5], ["DEF", 6], ["FWD", 6]]
## The match-day squad is 18 on the ground plus five interchange - 23, with
## no substitute role (ARD-M5-001, director 2026-10-06). Every bench player
## rotates, covers injuries and plays as fully as the other four.
const INTERCHANGE := 5
## The bench size selection uses: INTERCHANGE, changed only by audits that
## compare squad sizes on the same seeds (tools/audit/interchange_impl.gd).
static var bench_size := INTERCHANGE


## The season's bench: bench_size in the game's league, the year's interchange
## count in a Legacy season (EraRules: two to 1993, three 1994-97, four
## 1998-2010, three 2011-15, four 2016-25).
static func bench() -> int:
	return EraRules.interchange() if EraRules.is_era(EraRules.year) else bench_size


## Substitutes named beside the bench in a Legacy season (EraRules): one in
## 2011-15 and 2021-25, none in the game's league.
static func subs() -> int:
	return EraRules.substitutes()
## Audits only: false reproduces the old bench (best of the rest, no line
## cover, no dual ruck) for a before/after comparison.
static var bench_rules := true
## A second position (natural or learned) earns a spot on merit: a player
## left out who plays a line better than its weakest starter takes that spot
## (director, 2026-10-06). Audits only: false gives the old order, where a
## second position was used only once a line ran out of its own players.
static var merit_lines := true
## The lines an auto-picked bench covers before taking the best of the rest.
const BENCH_COVER := ["FWD", "DEF", "MID"]
## How close (OVR) a spare ruck must be for an AI club to run dual ruck.
const DUAL_RUCK_MARGIN := 5.0
const LIST_SIZE := 44

## Stats a past season never recorded (director 2026-11-15, "No invented
## stats": "an unrecorded stat stays blank and counts for nothing"). AFL
## Tables kept no rebound 50s, contested possessions, clearances and the rest
## before 1998 (tools/legacy_1990s/build_start.py). GameDB.reload sets it
## from the dataset's blank columns; it holds for the whole career. Every
## blend below drops an unrecorded stat and shares its weight among the
## recorded ones. Empty for today's data. Mirrored in tools/sim_harness.py.
static var unrecorded := {}
## A skill built only from unrecorded stats (contested and creating before
## 1998) has no record: it is left at his position's average (50, ruling 18),
## shown as a dash on his card (attr_unrecorded) and counts for nothing in his
## overall (unknown_attrs).
static var unknown_attrs := {}
## Each skill's blend of rates normalised within his line: [weight, metric].
## Intercept, speed and star power are not kept by AFL Tables (ruling 18):
## 50 unless the rating file gives them.
const ATTR_BLENDS := {
	"kicking": [[1.0, "kicks_pg"]],
	"handballing": [[1.0, "handballs_pg"]],
	"contested_marking": [[1.0, "contested_marks_pg"]],
	"uncontested_marking": [[1.0, "uncontested_marks_pg"]],
	"contested": [[0.375, "contested_pg"], [0.4375, "clearances_pg"], [0.1875, "contested_share"]],
	"pressure": [[1.0, "tackles_pg"]],
	"carry": [[1.0, "bounces_pg"]],
	"goalkicking": [[1.0, "goals_pg"]],
	"accuracy": [[1.0, "accuracy"]],
	"creating": [[2.0 / 3.0, "goal_assists_pg"], [1.0 / 3.0, "inside50s_pg"]],
	"ruck": [[1.0, "hitouts_pg"]],
	"discipline": [[0.70, "frees_against_pg"], [0.30, "clangers_pg"]],
	"durability": [[0.55, "games"], [0.45, "time_on_ground"]],
}
## The position reading's blends (FWD, MID, DEF in pick_role's order).
const ROLE_BLENDS := {
	"FWD": [[0.50, "goals_pg"], [0.26, "marks_inside50_pg"], [0.14, "goal_assists_pg"], [0.10, "behinds_pg"]],
	"MID": [[0.42, "disposals_pg"], [0.30, "contested_pg"], [0.28, "clearances_pg"]],
	"DEF": [[0.42, "rebounds_pg"], [0.30, "one_percenters_pg"], [0.20, "marks_pg"], [0.08, "goals_pg", true]],
}
## Metrics read from a stat other than their own column.
const METRIC_STAT := {"contested_share": "cp", "time_on_ground": "pctp", "uncontested_marks_pg": "cm"}


static func metric_recorded(metric: String) -> bool:
	if unrecorded.is_empty():
		return true
	if METRIC_STAT.has(metric):
		return not unrecorded.has(METRIC_STAT[metric])
	for spec in METRIC_SPECS:
		if spec[0] == metric:
			return not unrecorded.has(spec[1])
	return true


## A blend over the recorded metrics only, their weights rescaled to sum as
## before; -1.0 when none of them was recorded.
static func blend(q: Dictionary, terms: Array) -> float:
	var total := 0.0
	var kept := 0.0
	var v := 0.0
	for t in terms:
		total += float(t[0])
		if not metric_recorded(str(t[1])):
			continue
		kept += float(t[0])
		var x := float(q[t[1]])
		v += float(t[0]) * ((1.0 - x) if t.size() > 2 else x)
	if kept <= 0.0:
		return -1.0
	return v * total / kept


## Which stats a pool never recorded: a column blank on most of its rows
## (GameDB marks each player's blank cells in "blank").
static func find_unrecorded(players: Array) -> Dictionary:
	var count := {}
	for p in players:
		for k in p.get("blank", []):
			count[k] = int(count.get(k, 0)) + 1
	var out := {}
	for k in count:
		if int(count[k]) * 2 > players.size():
			out[k] = true
	return out


## Set the career's unrecorded stats and the attributes left with no record.
static func set_unrecorded(stats: Dictionary) -> void:
	unrecorded = stats
	unknown_attrs = {}
	for attr in ATTR_BLENDS:
		var any := false
		for t in ATTR_BLENDS[attr]:
			any = any or metric_recorded(str(t[1]))
		if not any:
			unknown_attrs[attr] = true


## Raw season columns every player dict carries. GameDB.STAT_KEYS must match;
## prospects (no AFL stats) get these zero-filled for the display rows.
const STATS_ZERO_KEYS := ["gm", "ki", "mk", "hb", "di", "gl", "bh", "ho", "tk", "rb",
		"if50", "cl", "cg", "ff", "fa", "br", "cp", "up", "cm", "mi",
		"onepct", "bo", "ga", "pctp"]

## Engine role -> the three-letter position tag used by the CSVs.
const ROLE_SHORT_TO_POS := {"RUCK": "RUC", "MID": "MID", "DEF": "DEF", "FWD": "FWD"}

## Games of evidence the overall-confidence shrink should assume. Prospects
## are projections (no sample to shrink); players who have completed a
## simulated season carry their bumped "sample" so a small 2026 games count
## cannot suppress them forever. Everything else keeps its real season games.
## Body of work (director 2026-11-15, "3 seasons, every start"): a real
## player is rated on his last three seasons, not the data season alone - the
## data season and the two before it (2026, 2025 and 2024 for today's data),
## each weighted by the games behind it and by how recent (RECORD_W, by years
## before the data season). It moves him up or down; a player with no earlier
## season on record keeps his one season. His attributes are refitted to it and
## his rating then counts at least a full sample (an injury year must not sink
## Treloar, Hogan or Darcy, director 2026-10-08). Real players only, once,
## when the data loads (GameDB), after their history.
const RECORD_W := {0: 1.0, 1: 0.75, 2: 0.5}
const RECORD_SHORT := 14.0


## `season` is the data season (GameDB.DATA_SEASON): the one his numbers are from.
static func record_level(p: Dictionary, season := 2026) -> float:
	var gm := float(p.get("gm", 0.0))
	var num := float(p.get("overall", 0)) * gm * float(RECORD_W[0])
	var den := gm * float(RECORD_W[0])
	var seen := false
	for h in p.get("history", []):
		var back := season - int(h[0])
		if back > 0 and RECORD_W.has(back) and int(h[2]) > 0:
			num += float(h[1]) * float(h[2]) * float(RECORD_W[back])
			den += float(h[2]) * float(RECORD_W[back])
			seen = true
	return num / den if seen and den > 0.0 else -1.0


static func rate_on_record(p: Dictionary, season := 2026) -> void:
	if bool(p.get("generated", false)) or bool(p.get("projected", false)) or not p.has("attr"):
		return
	var level := record_level(p, season)
	if level < 0.0 or absf(level - float(p.get("overall", 0))) < 0.5:
		return
	var role := str(p.get("role", "MID"))
	p["season_overall"] = int(p.get("overall", 0))   # what the data season alone said
	var games := maxf(RECORD_SHORT, effective_games(p))
	p["attr"] = Prospects.fit_attributes(p["attr"], role, level, games)
	p["sample"] = games
	p["overall"] = rate_overall(p["attr"], role, games)
	p["value"] = salary_value(p["overall"])
	p["rated_on_record"] = true


## Honours (director 2026-11-13, "Add honours", TODO row 142): a past start's
## stats miss what made some players great - Paul Roos, Fitzroy's captain and
## a two-time All-Australian, rated 71 on his 1989 numbers. The data's honours
## score (tools/legacy_1990s/build_start.py: a club best-and-fairest, an All-
## Australian or Team of the Year pick, a Brownlow top 3, each a point, 4th to
## 10th half, over the three seasons before the start, the last in full, then
## 0.75 and 0.5) sets a floor under his rating: HONOURS_FLOOR plus
## HONOURS_PER_POINT a point, at most HONOURS_CAP. Only ever a lift; his
## attributes are refitted to it, so he plays to it. Today's data carries no
## honours, so a 2026 start is untouched. Real players only, once, when the
## data loads (GameDB), after rate_on_record.
## The line is set from the record (bug bash 2026-11-23, "gun players were in
## the mid 70s"): over 1987-2025 an All-Australian rated a median 82-84 in his
## season, a Brownlow top 3 85-87, a club champion 79 (tools/ratings_check.py),
## so one point is 80, not the 77 that held 2009's All-Australians and club
## champions at a wall of 77. Kept in step with tools/legacy_1990s/
## build_start.py's HONOURS_*, which sets a real peak the same way.
const HONOURS_FLOOR := 75.0
const HONOURS_PER_POINT := 5.0
const HONOURS_CAP := 92.0


static func honours_floor(score: float) -> int:
	return int(round(minf(HONOURS_CAP, HONOURS_FLOOR + HONOURS_PER_POINT * score)))


static func rate_on_honours(p: Dictionary) -> void:
	var score := float(p.get("honours", 0.0))
	if score <= 0.0 or bool(p.get("generated", false)) or bool(p.get("projected", false)) 			or not p.has("attr"):
		return
	var floor_ovr := honours_floor(score)
	if int(p.get("overall", 0)) >= floor_ovr:
		return
	var role := str(p.get("role", "MID"))
	if not p.has("season_overall"):
		p["season_overall"] = int(p.get("overall", 0))   # what the data season alone said
	# Honours speak for a full season, as the record does (rate_on_record).
	var games := maxf(RECORD_SHORT, effective_games(p))
	var fitted := Prospects.fit_attributes(p["attr"], role, float(floor_ovr), games)
	p["attr"] = top_up_to(fitted, role, floor_ovr, games)
	p["sample"] = games
	# His overall is what his skills say, as on every load (GameState.
	# _recompute_ratings): a label lifted over his skills fell a point on load.
	p["overall"] = rate_overall(p["attr"], role, games)
	p["value"] = salary_value(p["overall"])
	p["rated_on_honours"] = true


## The fit shifts every skill by one offset and rounds each, which can leave
## the skills a point under the target (120 honoured players across the 1990,
## 2000, 2010 and 2020 starts, each one point short, bug bash 2026-11-25).
## Closes that point one skill at a time, as GameDB.set_player_ovr closes a
## hand-set rating; temperament (Prospects.UNRATED_KEYS) stays. The director's
## call (2026-11-25): "Top up his skills".
static func top_up_to(a: Dictionary, role: String, target: int, games: float) -> Dictionary:
	var out := a.duplicate()
	for _round in range(20):
		for k in out:
			if rate_overall(out, role, games) >= target:
				return out
			if k in Prospects.UNRATED_KEYS or int(out[k]) >= 99:
				continue
			out[k] = int(out[k]) + 1
	return out


## A past start's injured star (bug bash 2026-11-23: Tony Liberatore, the
## 1990 Brownlow medallist, rated 55 on his one 1989 game and asked for a
## trade to get a game). A real player whose data season was cut short
## (Potential flags him "rehab": under REHAB_GAMES games and a real peak
## REHAB_PEAK_GAP above it) has had his rehab summer before the career's
## first season: he starts where the rehab year takes him (Potential.
## rehab_pull of the gap to his potential), as TradeValue already judges him.
## Real players with a real peak only, once, when the data loads (GameDB),
## after Potential.assign.
const REHAB_FROM_AGE := 23.0


static func rate_on_rehab(p: Dictionary) -> void:
	if not bool(p.get("rehab", false)) or float(p.get("real_peak", 0)) <= 0.0 or not p.has("attr"):
		return
	# A young player's short season is his development, not an injury: his
	# real peak comes through growth (REHAB_FROM_AGE).
	if float(p.get("age", 0.0)) < REHAB_FROM_AGE:
		return
	var ovr := float(p.get("overall", 0))
	var gap := float(p.get("potential", ovr)) - ovr
	if gap <= 0.0:
		return
	var target := ovr + gap * Potential.rehab_pull(float(p.get("age", 26.0)))
	var role := str(p.get("role", "MID"))
	if not p.has("season_overall"):
		p["season_overall"] = int(ovr)   # what the data season alone said
	var games := maxf(RECORD_SHORT, effective_games(p))
	p["attr"] = Prospects.fit_attributes(p["attr"], role, target, games)
	p["sample"] = games
	p["overall"] = mini(int(p.get("potential", 99)), maxi(int(ovr), rate_overall(p["attr"], role, games)))
	p["value"] = salary_value(p["overall"])
	p["rated_on_rehab"] = true
	p.erase("rehab")


static func effective_games(p: Dictionary) -> float:
	if p.has("sample"):
		return maxf(1.0, float(p["sample"]))
	if bool(p.get("projected", false)):
		return 14.0
	return maxf(1.0, float(p.get("gm", 0.0)))

## The 16 skills (Skills.KEYS).
const ATTR_KEYS := Skills.KEYS

## How much each skill counts in a player's overall, by engine line: the mix
## of skills that best matches the AFL Player Rating against his position,
## measured on every 2012-2025 season (tools/wheelo/fit.py::game_fit; ruling 2:
## a 2012+ player's overall is his AFL Player Rating against his position).
## No skill counts against a player; each line's shares add to 1.0. A real
## player's attributes are refitted so this gives his rated overall
## (GameDB, Prospects.fit_attributes); a generated player, or one whose
## skills change, is rated by it. Mirrored in tools/sim_harness.py.
const ROLE_WEIGHTS := {
	"RUCK": {"kicking": 0.097, "handballing": 0.018, "contested_marking": 0.081, "contested": 0.225,
			"pressure": 0.049, "intercept": 0.054, "carry": 0.024, "goalkicking": 0.023, "accuracy": 0.059,
			"creating": 0.070, "ruck": 0.187, "discipline": 0.043, "durability": 0.022, "star": 0.048},
	"FWD": {"kicking": 0.083, "handballing": 0.030, "contested_marking": 0.032, "contested": 0.177,
			"pressure": 0.058, "intercept": 0.056, "carry": 0.067, "goalkicking": 0.112, "accuracy": 0.072,
			"creating": 0.147, "discipline": 0.049, "durability": 0.050, "star": 0.067},
	"MID": {"kicking": 0.066, "handballing": 0.019, "contested_marking": 0.027, "contested": 0.236,
			"pressure": 0.082, "intercept": 0.072, "carry": 0.070, "goalkicking": 0.058, "accuracy": 0.057,
			"creating": 0.155, "discipline": 0.072, "durability": 0.018, "star": 0.068},
	"DEF": {"kicking": 0.124, "handballing": 0.055, "contested_marking": 0.041, "contested": 0.161,
			"pressure": 0.014, "intercept": 0.174, "carry": 0.074, "goalkicking": 0.050, "accuracy": 0.002,
			"creating": 0.128, "ruck": 0.004, "discipline": 0.053, "durability": 0.052, "star": 0.068},
}
## The same fit's scale: a line's middle overall, its average share-weighted
## skill (0..1) and overall points per unit of it.
const LINE_FIT := {
	"RUCK": {"mid": 63.22, "mean": 0.5518, "slope": 145.62},
	"FWD": {"mid": 63.20, "mean": 0.5077, "slope": 162.96},
	"MID": {"mid": 63.19, "mean": 0.5142, "slope": 142.95},
	"DEF": {"mid": 63.18, "mean": 0.4952, "slope": 166.95},
}
## Overall bounds (the AFL Player Rating scale, tools/wheelo/wheelo.py).
const OVR_MIN := 30
const OVR_MAX := 99


# ---------------------------------------------------------------------------
# Small maths helpers
# ---------------------------------------------------------------------------
static func percentile(vals: Array, q: float) -> float:
	var s := vals.duplicate()
	s.sort()
	if s.is_empty():
		return 0.0
	var i := q * float(s.size() - 1)
	var lo := int(floorf(i))
	var hi := mini(s.size() - 1, lo + 1)
	return float(s[lo]) + (float(s[hi]) - float(s[lo])) * (i - float(lo))


## Shrink a raw season total toward the league per-player-per-game rate so a
## two-game sample cannot outrank a 25-game sample.
static func shrunk_rate(total: float, games: float, league_rate: float,
		k: float) -> float:
	return (total + k * league_rate) / (games + k)


static func scale_attr(v: float) -> int:
	return int(round(1.0 + 98.0 * clampf(v, 0.0, 1.0)))


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------
## Deliberately NOT a percentile rank: most of these stats are zero for the
## majority of the pool (hit-outs, bounces, marks inside 50), so a percentile
## rank would hand a *high* score to a zero. Capped linear scaling against the
## 98th percentile keeps zero == zero.
static func build_norm_params(players: Array, keys: Array) -> Dictionary:
	var params := {}
	for k in keys:
		var vals := []
		for p in players:
			vals.append(p["rates"][k])
		var invert: bool = k == "clangers_pg" or k == "frees_against_pg"
		var e := {"invert": invert}
		match k:
			"accuracy":
				e["mode"] = "range"; e["lo"] = 0.22; e["hi"] = 0.82
			"games":
				e["mode"] = "range"; e["lo"] = 0.0; e["hi"] = 26.0
			"time_on_ground":
				e["mode"] = "range"; e["lo"] = 0.30; e["hi"] = 0.95
			"brownlow_pg":
				e["mode"] = "cap"; e["ref"] = percentile(vals, 1.0)
			_:
				e["mode"] = "cap"; e["ref"] = percentile(vals, 0.98)
		if e["mode"] == "cap" and float(e["ref"]) <= 0.0:
			e["ref"] = 1.0
		params[k] = e
	return params


static func norm(params: Dictionary, metric: String, v: float) -> float:
	var e: Dictionary = params[metric]
	var x := 0.0
	if e["mode"] == "range":
		var span := float(e["hi"]) - float(e["lo"])
		if is_zero_approx(span):
			span = 1.0
		x = (v - float(e["lo"])) / span
	else:
		x = v / float(e["ref"])
	if e["invert"]:
		x = 1.0 - x
	return clampf(x, 0.0, 1.0)


# ---------------------------------------------------------------------------
# League rates
# ---------------------------------------------------------------------------
## Average *per player per game* rate for each metric. This is the shrinkage
## target. It must NOT be the team-per-game figure: shrinking a player's
## disposals toward 364 (a whole team's output) makes fringe players superhuman.
static func player_league_rates(players: Array) -> Dictionary:
	var gm := 0.0
	for p in players:
		gm += maxf(1.0, p["gm"])
	gm = maxf(1.0, gm)
	var out := {}
	for spec in METRIC_SPECS:
		var metric: String = spec[0]
		var stat: String = spec[1]
		var total := 0.0
		for p in players:
			total += p["di"] - p["ki"] if stat == "hb" else p[stat]
		out[metric] = total / gm
	return out


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
## Mutates each player dict, adding: rates, norm, attr, role, role_scores,
## overall, value. Call once at boot on the full player pool.
## `reference` is an already-rated pool whose league rates and normalisation
## the new players are scaled against without changing it (list additions
## rated on their record, GameDB._rate_established_additions).
static func derive_all(players: Array, reference: Array = []) -> Array:
	if players.is_empty():
		return players
	var league := player_league_rates(reference + players)
	var k_games: float = T["shrink_games"]
	var k_acc: float = T["shrink_accuracy"]

	# ---- per-game rates ---------------------------------------------------
	for p in players:
		var gm := maxf(1.0, p["gm"])
		var r := {}
		for spec in METRIC_SPECS:
			var metric: String = spec[0]
			var stat: String = spec[1]
			var total: float = p["di"] - p["ki"] if stat == "hb" else p[stat]
			r[metric] = shrunk_rate(total, gm, league[metric], k_games)
		var shots: float = p["gl"] + p["bh"]
		r["accuracy"] = (p["gl"] + k_acc * 0.52) / (shots + k_acc)
		r["contested_share"] = (p["cp"] + 40.0) / (maxf(1.0, p["di"]) + 100.0)
		r["games"] = gm
		r["time_on_ground"] = p["pctp"] / 100.0
		r["uncontested_marks_pg"] = shrunk_rate(maxf(0.0, p["mk"] - p["cm"]), gm,
				maxf(0.0, league["marks_pg"] - league["contested_marks_pg"]), k_games)
		r["score_involved_pg"] = shrunk_rate(
				p["gl"] + p["bh"] + p["ga"] + p["mi"], gm, 4.0, k_games)
		p["rates"] = r

	# ---- normalisation params over the whole pool --------------------------
	var keys: Array = players[0]["rates"].keys()
	var params := build_norm_params(reference + players, keys)

	for p in players:
		var q := {}
		for k in keys:
			q[k] = norm(params, k, p["rates"][k])
		p["norm"] = q

		# ---- role classification ------------------------------------------
		var hitouts_pg: float = p["ho"] / maxf(1.0, p["gm"])
		var scores := {}
		for role in ROLE_BLENDS:
			scores[role] = maxf(0.0, blend(q, ROLE_BLENDS[role]))
		# Ruck is gated on actual hit-out volume, not on a normalised score:
		# without the gate every tall forward gets classified as a ruckman.
		scores["RUCK"] = (0.25 + 0.85 * q["hitouts_pg"]) if hitouts_pg >= 7.0 else -1.0
		p["role_scores"] = scores
		p["role"] = listed_primary(p, pick_role(scores))
		var fix := "%s|%s %s" % [p.get("club", ""), p.get("first", ""), p.get("last", "")]
		if ROLE_CORRECTIONS.has(fix):
			p["role"] = ROLE_CORRECTIONS[fix]
		p["role2"] = assign_secondary(p)

	# ---- 1-99 attributes: each against his own line -------------------------
	# Ruling 18: what AFL Tables does not keep (intercept possessions, speed,
	# coaches votes, hit-outs to advantage) is left out, at the middle (50).
	var by_line := {}
	for p in reference + players:
		var line := str(p.get("role", "MID"))
		if not by_line.has(line):
			by_line[line] = []
		by_line[line].append(p)
	var line_params := {}
	for line in by_line:
		line_params[line] = build_norm_params(by_line[line], keys)
	for p in players:
		var lq := {}
		var lp: Dictionary = line_params[str(p["role"])]
		for k in keys:
			lq[k] = norm(lp, k, p["rates"][k])
		var a := {}
		var unknown := []
		for key in ATTR_BLENDS:
			var v := blend(lq, ATTR_BLENDS[key])
			a[key] = scale_attr(v) if v >= 0.0 else 50
			if v < 0.0:
				unknown.append(key)
		a["intercept"] = 50
		a["speed"] = 50
		a["star"] = 50
		# Shown blank on his card, never as the stand-in value (director
		# 2026-11-15, "I never okayed invented stats").
		if unknown.is_empty():
			p.erase("attr_unrecorded")
		else:
			p["attr_unrecorded"] = unknown
		var adj := float(ATTR_ADJUSTMENTS.get("%s|%s %s" % [p.get("club", ""), p.get("first", ""), p.get("last", "")], 1.0))
		if adj != 1.0:
			for k in a:
				a[k] = clampi(int(round(float(a[k]) * adj)), 1, 99)
		p["attr"] = a

		# ---- overall + draft value ----------------------------------------
		p["overall"] = rate_overall(a, str(p["role"]), float(p["gm"]))
		p["value"] = salary_value(p["overall"])

	return players


## Players the stat classifier clearly gets wrong: listed and played as
## forwards, but a light goal year reads as midfield on the numbers. Only
## unambiguous cases (first positions); the listing otherwise only adds a
## second position (listed_secondary). Mirrored in tools/sim_harness.py.
const ROLE_CORRECTIONS := {
	"RIC|Maurice Rioli": "FWD",
	"WBD|Cody Weightman": "FWD",
}


## Director's player-data balance corrections: every skill scaled by the
## factor, capped at 99, before OVR is rated (on the rating file's skills,
## GameDB._apply_rating_stats, when it names him). Named players only; never a
## reason to change the generation model. Mirrored in tools/sim_harness.py.
## Bowey's factor is the smallest that lifts his OVR 5% (86 to 90 on the
## Wheelo ratings); his POT 5% is the "+5%" row in data/potential_overrides.csv.
const ATTR_ADJUSTMENTS := {
	"MEL|Harvey Langford": 1.15,
	"MEL|Jake Bowey": 1.036,
	"PAD|Connor Rozee": 1.10,
}


## His club's listing is his first position (director, 2026-11-06, T8.Q11,
## TODO row 91): a listed forward or defender is a forward or defender,
## whatever one season's numbers read. A listed forward with heavy possession
## is still a forward who can go through the middle (assign_secondary gives
## him MID second when his numbers clear that gate). Only a ruck reading
## stands, since it is gated on real hit-out volume. Listed midfielders and
## rucks, and players with no listing, keep the numbers' reading.
## A past start (Legacy) also keeps a listed midfielder in the midfield
## (listed_lines): its listing is the position he is known for
## (data/legacy/positions.csv), and before the 2000s most of the numbers that
## read a defender (rebound 50s, one percenters) are estimates (director
## 2026-11-15: "some are out of position like Garry Lyon in defence").
## Mirrored in tools/sim_harness.py.
const TODAY_LISTED_LINES := ["FWD", "DEF"]
const PAST_LISTED_LINES := ["FWD", "DEF", "MID"]
## GameDB.reload sets it: PAST_LISTED_LINES for a past start.
static var listed_lines: Array = TODAY_LISTED_LINES


static func listed_primary(p: Dictionary, role: String) -> String:
	var listed := str(p.get("real_pos", ""))
	if listed in listed_lines and role != "RUCK":
		return listed
	return role


## First-max wins, matching the Python harness's insertion order
## (FWD, MID, DEF, RUCK) so ties resolve identically.
static func pick_role(scores: Dictionary) -> String:
	var best := "MID"
	var best_v := -INF
	for role in ["FWD", "MID", "DEF", "RUCK"]:
		var v: float = scores[role]
		if v > best_v:
			best_v = v
			best = role
	return best


## His skills mixed by his line's shares (ROLE_WEIGHTS) on the AFL Player
## Rating scale (LINE_FIT), then a confidence shrink toward the middle for a
## short sample. Must match tools/sim_harness.py::rate_overall.
static func rate_overall(a: Dictionary, role: String, games: float) -> int:
	var w: Dictionary = ROLE_WEIGHTS.get(role, ROLE_WEIGHTS["MID"])
	var f: Dictionary = LINE_FIT.get(role, LINE_FIT["MID"])
	var b := 0.0
	var total := 0.0
	var kept := 0.0
	for key in w:
		total += float(w[key])
		if unknown_attrs.has(key):
			continue   # no record in his era: counts for nothing
		kept += float(w[key])
		b += float(w[key]) * (float(a.get(key, 50)) - 1.0) / 98.0
	if kept > 0.0:
		b *= total / kept
	var mid := float(f["mid"])
	var overall := mid + float(f["slope"]) * (b - float(f["mean"]))
	var conf: float = minf(1.0, games / 14.0)
	overall = mid + (overall - mid) * (0.40 + 0.60 * conf)
	return clampi(int(round(overall)), OVR_MIN, OVR_MAX)


## How much one point of `key` moves his rating in `role` (rate_overall is a
## straight line in each skill, so this is the same at every level): 0 for a
## skill the role does not count. Growth prices XP in rating points with it.
static func overall_per_point(role: String, key: String, games: float) -> float:
	var w: Dictionary = ROLE_WEIGHTS.get(role, ROLE_WEIGHTS["MID"])
	if not w.has(key) or unknown_attrs.has(key):
		return 0.0
	var f: Dictionary = LINE_FIT.get(role, LINE_FIT["MID"])
	var total := 0.0
	var kept := 0.0
	for k in w:
		total += float(w[k])
		if not unknown_attrs.has(k):
			kept += float(w[k])
	var conf: float = minf(1.0, games / 14.0)
	return float(f["slope"]) * float(w[key]) / 98.0 * (total / kept) * (0.40 + 0.60 * conf)


## Second role only when the season numbers clear a gate. Empty string means
## one role. Must match tools/sim_harness.py::assign_secondary.
static func assign_secondary(p: Dictionary) -> String:
	var scores: Dictionary = p["role_scores"]
	var primary := str(p["role"])
	var best := ""
	var best_v := -1.0
	for role in ["FWD", "MID", "DEF", "RUCK"]:
		if role == primary:
			continue
		var sc: float = float(scores.get(role, -1.0))
		if sc < 0.0 or not _secondary_ok(p, primary, role, sc):
			continue
		if sc > best_v:
			best_v = sc
			best = role
	if best == "":
		best = listed_secondary(p)
	return best


## The line his club lists him in, as a second position, for a player the
## numbers read as a midfielder: a listed forward who kicks goals or marks
## inside 50, a listed defender who wins it back (rebound 50s and one
## percenters). His club's listing is the evidence; his own numbers have to
## back it up. Never changes his first position, rating or type.
## Mirrored in tools/sim_harness.py.
const LISTED_FWD_GOALS := 0.35      # goals a game
const LISTED_FWD_MARKS_I50 := 0.5   # marks inside 50 a game
const LISTED_DEF_ACTIONS := 2.0     # rebound 50s + one percenters a game


static func listed_secondary(p: Dictionary) -> String:
	if str(p.get("role", "")) != "MID":
		return ""
	var listed := str(p.get("real_pos", ""))
	var games := maxf(1.0, float(p.get("gm", 0.0)))
	if listed == "FWD" and (float(p.get("gl", 0.0)) / games >= LISTED_FWD_GOALS
			or float(p.get("mi", 0.0)) / games >= LISTED_FWD_MARKS_I50):
		return "FWD"
	if listed == "DEF" and (float(p.get("rb", 0.0)) + float(p.get("onepct", 0.0))) / games >= LISTED_DEF_ACTIONS:
		return "DEF"
	return ""


static func _secondary_ok(p: Dictionary, primary: String, role: String, sc: float) -> bool:
	var primary_sc: float = float(p["role_scores"].get(primary, 0.0))
	var games := maxf(1.0, float(p["gm"]))
	if role == "FWD":
		if sc < 0.46 or (int(p["gl"]) < 12 and int(p["mi"]) < 18):
			return false
		return sc >= primary_sc * 0.50
	if role == "MID":
		if sc < 0.52 or float(p["di"]) / games < 16.0:
			return false
		return sc >= primary_sc * 0.58
	if role == "DEF":
		if sc < 0.50 or (float(p["rb"]) + float(p["onepct"])) / games < 3.2:
			return false
		return sc >= primary_sc * 0.60
	if role == "RUCK":
		return float(p["ho"]) / games >= 5.0 and sc >= 0.75
	return false


static func role_tag(p: Dictionary) -> String:
	var primary := str(p.get("role", ""))
	var tag := primary
	for r in second_positions(p):
		if str(r) != primary:
			tag += "/" + str(r)
	return tag


## Every position he can be picked in: his own, his second, and any he has
## learned in training (GameState: learning another position).
static func positions(p: Dictionary) -> Array:
	var out := [str(p.get("own_role", p.get("role", "")))]
	for r in second_positions(p):
		if not out.has(r):
			out.append(r)
	return out


## His second position and any learned after it.
static func second_positions(p: Dictionary) -> Array:
	var out := []
	var r2 := str(p.get("role2", ""))
	if r2 != "":
		out.append(r2)
	for r in p.get("learned", []):
		if str(r) != "" and not out.has(str(r)):
			out.append(str(r))
	# A Unicorn plays forward, midfield and back (Traits.is_unicorn).
	if Traits.is_unicorn(p):
		var own := str(p.get("own_role", p.get("role", "")))
		for line in Traits.UNICORN_LINES:
			if line != own and not out.has(line):
				out.append(line)
	return out


static func plays_role(p: Dictionary, role: String) -> bool:
	if role == "":
		return true
	return str(p.get("role", "")) == role or second_positions(p).has(role)


## Plausible annual AFL salary from the overall rating. This is the simple
## list-management base salary used by the game, not a claim to reproduce
## every real AFL payment (match payments/ASAs are deliberately out of scope).
## The curve preserves the old 1-10 salary tiers while expressing them in
## football money: depth at the senior floor, established players in the
## hundreds of thousands, and genuine stars above $1m.
static func salary_value(overall: int) -> int:
	# Annual salary the market pays for a rating: it rises smoothly between
	# these points (no cliff for one rating point), from the senior minimum.
	var points := [[40, 155000], [48, 255000], [55, 335000], [61, 415000],
			[67, 515000], [73, 625000], [79, 740000], [85, 875000], [90, 1030000], [99, 1250000]]
	if overall <= int(points[0][0]):
		return int(points[0][1])
	for i in range(1, points.size()):
		if overall <= int(points[i][0]):
			var lo: Array = points[i - 1]
			var hi: Array = points[i]
			var t := float(overall - int(lo[0])) / float(int(hi[0]) - int(lo[0]))
			return int(round(lerpf(float(lo[1]), float(hi[1]), t) / 5000.0)) * 5000
	return int(points[points.size() - 1][1])


# ---------------------------------------------------------------------------
# Squad selection
# ---------------------------------------------------------------------------
## Best 18 on the ground respecting the 1R/5M/6D/6F structure, plus
## INTERCHANGE (5) on the bench: the match-day 23. (The name predates the
## fifth interchange.) Structural shortfalls (a list with no recognised ruckman, say) are
## backfilled by overall rating so a team always fields 18.
## `dual`: run a second ruck on the bench - 1 yes (a coach's call: he takes
## the first bench spot), 0 no, -1 the AI's rule (only when the spare ruck is
## within DUAL_RUCK_MARGIN of the bench player he would replace).
static func select_22(list_players: Array, dual := -1) -> Dictionary:
	var pool := list_players.duplicate()
	# A player promised a game this week (a kid given his chance, a talk) or a
	# run (Backing) is first in line for his own position; then the best
	# available.
	var promised := {}
	for p in pool:
		if p.has("expects_game") or Backing.is_active(p):
			promised[p["id"]] = true
	pool.sort_custom(func(a, b):
		var pa: bool = promised.has(a["id"])
		if pa != promised.has(b["id"]):
			return pa
		return float(a["overall"]) * Workload.selection_factor(a) > float(b["overall"]) * Workload.selection_factor(b))

	var ground: Array = []
	var used := {}
	for slot in GROUND_SLOTS:
		var role: String = slot[0]
		var need: int = slot[1]
		var added := 0
		# Ruck is a specialist job: among recognised primary/secondary rucks,
		# pick the best tap player rather than the highest overall. This keeps
		# a high-OVR part-timer from displacing the side's actual best ruck.
		if role == "RUCK":
			var recognised := []
			for p in pool:
				if plays_role(p, "RUCK") and not used.has(p["id"]):
					recognised.append(p)
			# The best tap player first, but a promised ruck is first in line.
			var first := []
			var others := []
			for p in by_ruck(recognised):
				if promised.has(p["id"]):
					first.append(p)
				else:
					others.append(p)
			for p in first + others:
				if added >= need:
					break
				ground.append(_for_slot(p, role))
				used[p["id"]] = true
				added += 1
		else:
			for p in pool:
				if added >= need:
					break
				if str(p["role"]) == role and not used.has(p["id"]):
					ground.append(_for_slot(p, role))
					used[p["id"]] = true
					added += 1
			# A MID/FWD can fill a forward slot once the primary forwards are gone.
			for p in pool:
				if added >= need:
					break
				if second_positions(p).has(role) and not used.has(p["id"]):
					ground.append(_for_slot(p, role))
					used[p["id"]] = true
					added += 1
		# No recognised ruck on the list: the best tap player available goes
		# up as an emergency, not simply the best overall player.
		if role == "RUCK" and added < need:
			for p in by_ruck(pool):
				if added >= need:
					break
				if not used.has(p["id"]):
					ground.append(_for_slot(p, role))
					used[p["id"]] = true
					added += 1
	if merit_lines:
		_merit_swaps(pool, ground, used, promised)
	for p in pool:
		if ground.size() >= 18:
			break
		if not used.has(p["id"]):
			ground.append(_for_slot(p, str(p["role"])))
			used[p["id"]] = true

	# The bench covers the lines first - a forward, a defender and a
	# midfielder, the best of each left - then the best of the rest, so a
	# tired forward is relieved by a forward, as on a real interchange bench.
	# Dual ruck: the second ruck takes the first spot.
	var bench: Array = []
	var spare_ruck: Dictionary = {}
	for p in by_ruck(pool):
		if not used.has(p["id"]) and str(p.get("role", "")) == "RUCK":
			spare_ruck = p
			break
	if dual == 1 and bench_rules and not spare_ruck.is_empty():
		bench.append(spare_ruck)
		used[spare_ruck["id"]] = true
	for line in (BENCH_COVER if bench_rules else []):
		for p in pool:
			if bench.size() >= bench():
				break
			if not used.has(p["id"]) and str(p.get("role", "")) == line:
				bench.append(p)
				used[p["id"]] = true
				break
	for p in pool:
		if bench.size() >= bench():
			break
		if not used.has(p["id"]):
			bench.append(p)
			used[p["id"]] = true

	# The AI's call: a second ruck earns the last spot when he is close to
	# the player he'd replace.
	if dual == -1 and bench_rules and not spare_ruck.is_empty() and not used.has(spare_ruck["id"]) \
			and bench.size() >= bench() and bench() > BENCH_COVER.size():
		var last: Dictionary = bench[bench.size() - 1]
		if float(spare_ruck["overall"]) >= float(last["overall"]) - DUAL_RUCK_MARGIN:
			used.erase(last["id"])
			bench[bench.size() - 1] = spare_ruck
			used[spare_ruck["id"]] = true

	ground = ground.slice(0, 18)
	key_posts(ground)
	Roles.mark_wings(ground)
	return {"ground": ground, "bench": bench}


## The auto-pick's key posts (Roles.key_post_order): each line's players are
## re-laid in their own places in `ground`, so the line reads in spot order.
static func key_posts(ground: Array) -> void:
	for line in ["DEF", "FWD"]:
		var at: Array = []
		var line_players: Array = []
		for i in range(ground.size()):
			if str(ground[i].get("role", "")) == line:
				at.append(i)
				line_players.append(ground[i])
		var laid := Roles.key_post_order(line_players, line)
		for k in range(at.size()):
			ground[at[k]] = laid[k]


## True when a player can take the field (not injured, suspended or rested).
static func available(p: Dictionary) -> bool:
	return int(p.get("injury_weeks", 0)) <= 0 \
			and int(p.get("suspension_weeks", 0)) <= 0 \
			and not p.has("season_ban") \
			and not bool(p.get("rested", false))


## The match-day 22. With an empty selection the best available side is
## picked automatically (select_22). A selection is
## {"RUCK": [ids], "MID": [...], "WING": [...], "DEF": [...], "FWD": [...],
## "BENCH": [...], "OUT": [ids]} - WING names two of the five midfielders
## (Roles), MID the centre square: named players take their slots (any player can be named in
## any position), and a gap - an injured or departed player, or a slot left
## short - goes to the best-suited fit player, from the named bench and the
## players not named alike (director, 2026-11-15: "best player suited gets
## the spot, idc whether they came from the bench or reserves"), and only as a
## last resort to one marked OUT (a promise's swap). Best suited is the
## automatic way: his own position first, then his second, then anyone, each
## by rating and freshness. Injured players never play.
static func select_side(list_players: Array, selection: Dictionary = {}) -> Dictionary:
	var pool: Array = []
	for p in list_players:
		if available(p):
			pool.append(p)
	# The dual-ruck call travels with the selection; a selection that is only
	# that call is still the auto-pick.
	var dual := -1
	if selection.has("DUAL_RUCK"):
		dual = 1 if bool(selection["DUAL_RUCK"]) else 0
		selection = selection.duplicate()
		selection.erase("DUAL_RUCK")
	# A role trial rides with the selection like the dual-ruck call: under the
	# auto-pick he plays his trial position (his own becomes his second).
	var trial: Dictionary = {}
	if selection.has("TRIAL"):
		trial = selection["TRIAL"]
		selection = selection.duplicate()
		selection.erase("TRIAL")
	if selection.is_empty():
		if not trial.is_empty():
			pool = _with_trial(pool, trial)
		return select_22(pool, dual)
	pool.sort_custom(func(a, b):
		return float(a["overall"]) * Workload.selection_factor(a) > float(b["overall"]) * Workload.selection_factor(b))
	var by_id := {}
	for p in pool:
		by_id[str(p["id"])] = p
	var ground: Array = []
	var used := {}
	for slot in GROUND_SLOTS:
		var role: String = slot[0]
		var added := 0
		# Wings are two of the five midfield spots.
		var named: Array = selection.get(role, [])
		if role == "MID":
			named = (selection.get("WING", []) as Array) + named
		for id in named:
			if added >= int(slot[1]):
				break
			var p = by_id.get(str(id))
			if p == null or used.has(str(id)):
				continue
			ground.append(_for_slot(p, role))
			used[str(id)] = true
			added += 1
	# Fill order for gaps: 0 the bench and the unnamed alike (best suited
	# wins), 1 players marked OUT.
	var tier := {}
	for id in selection.get("OUT", []):
		if by_id.has(str(id)) and not used.has(str(id)):
			tier[str(id)] = 1
	for pass_tier in [0, 1]:
		for slot in GROUND_SLOTS:
			var role: String = slot[0]
			var have := 0
			for g in ground:
				if str(g["role"]) == role:
					have += 1
			if role == "RUCK":
				# A missing named ruck is filled by the best available recognised
				# ruck in this selection tier, not whichever ruck has the best OVR.
				var recognised := []
				for p in pool:
					var id := str(p["id"])
					if not used.has(id) and int(tier.get(id, 0)) == pass_tier and plays_role(p, "RUCK"):
						recognised.append(p)
				for p in by_ruck(recognised):
					if have >= int(slot[1]):
						break
					var id := str(p["id"])
					ground.append(_for_slot(p, role))
					used[id] = true
					have += 1
			else:
				for key in ["role", "role2"]:
					for p in pool:
						if have >= int(slot[1]):
							break
						var id := str(p["id"])
						if used.has(id) or int(tier.get(id, 0)) != pass_tier:
							continue
						if (str(p.get("role", "")) == role) if key == "role" else second_positions(p).has(role):
							ground.append(_for_slot(p, role))
							used[id] = true
							have += 1
			for p in (by_ruck(pool) if role == "RUCK" else pool):
				if have >= int(slot[1]):
					break
				var id := str(p["id"])
				if used.has(id) or int(tier.get(id, 0)) != pass_tier:
					continue
				ground.append(_for_slot(p, role))
				used[id] = true
				have += 1
	var bench: Array = []
	for id in selection.get("BENCH", []):
		if bench.size() >= bench():
			break
		if by_id.has(str(id)) and not used.has(str(id)):
			bench.append(by_id[str(id)])
			used[str(id)] = true
	for pass_tier in [0, 1]:
		for p in pool:
			if bench.size() >= bench():
				break
			var id := str(p["id"])
			if not used.has(id) and int(tier.get(id, 0)) == pass_tier:
				bench.append(p)
				used[id] = true
	Roles.mark_wings(ground, selection.get("WING", []))
	return {"ground": ground, "bench": bench}


## The side "Best side on form" names for a simmed week (director, 2026-11-15:
## "100% of the selection should be determined only by form, thats what the
## copy says it does"). `form`: player id -> his form, the match rating a game
## over his last games (PlayerCondition.form: seniors, else the twos; -1 when
## he has played neither this season). Each line takes the players in the best
## form who play it (his own position, then his second, then anyone); the
## bench the next best. Rating plays no part, except to order the players
## with no game yet, who come after everyone with form. A promised player
## (a run, a talk) is still first in line, as in select_22: a promise made
## stands. Returns a selection: {"RUCK", "MID", "DEF", "FWD", "BENCH": [ids]}.
static func select_on_form(list_players: Array, form: Dictionary) -> Dictionary:
	var pool: Array = []
	var promised := {}
	for p in list_players:
		if available(p):
			pool.append(p)
			if p.has("expects_game") or Backing.is_active(p):
				promised[str(p["id"])] = true
	var score := func(p: Dictionary) -> float:
		var v := float(form.get(str(p["id"]), -1))
		return v if v >= 0.0 else -1000.0 + float(p.get("overall", 0))
	pool.sort_custom(func(a, b):
		var pa := promised.has(str(a["id"]))
		if pa != promised.has(str(b["id"])):
			return pa
		var sa: float = score.call(a)
		var sb: float = score.call(b)
		if sa != sb:
			return sa > sb
		return str(a["id"]) < str(b["id"]))
	var sel := {"RUCK": [], "MID": [], "DEF": [], "FWD": [], "BENCH": []}
	var used := {}
	for pass_kind in ["own", "second", "any"]:
		for slot in GROUND_SLOTS:
			var role: String = slot[0]
			for p in pool:
				if (sel[role] as Array).size() >= int(slot[1]):
					break
				var id := str(p["id"])
				if used.has(id):
					continue
				var fits: bool = (str(p.get("role", "")) == role or (role == "RUCK" and plays_role(p, "RUCK"))) if pass_kind == "own" 						else (second_positions(p).has(role) if pass_kind == "second" else true)
				if fits:
					(sel[role] as Array).append(id)
					used[id] = true
	for p in pool:
		if (sel["BENCH"] as Array).size() >= bench():
			break
		if not used.has(str(p["id"])):
			(sel["BENCH"] as Array).append(str(p["id"]))
			used[str(p["id"])] = true
	return sel


## His rating playing `line`: his own rating in his own line, else what his
## attributes make him there.
static func line_rating(p: Dictionary, line: String) -> float:
	if str(p.get("role", "")) == line or (p.get("attr", {}) as Dictionary).is_empty():
		return float(p.get("overall", 0))
	return float(rate_overall(p["attr"], line, effective_games(p)))


## The merit pass of the auto-pick: in the midfield, back and forward lines,
## the best player left out who can play the line (a second position) takes
## the place of its weakest starter when he rates higher there. A promised
## starter keeps his place; the ruck slot, the dual ruck and the bench's line
## cover are untouched (the dropped starter goes back to the pool and can make
## the bench).
static func _merit_swaps(pool: Array, ground: Array, used: Dictionary, promised: Dictionary) -> void:
	var by_id := {}
	for p in pool:
		by_id[p["id"]] = p
	for line in ["MID", "DEF", "FWD"]:
		# Who is left out and can play the line, valued once (most lines have
		# nobody, and the line is skipped without rating anyone).
		var cands := {}
		for p in pool:
			if not used.has(p["id"]) and second_positions(p).has(line):
				cands[p["id"]] = line_rating(p, line) * Workload.selection_factor(p)
		if cands.is_empty():
			continue
		var starters := {}
		for g in ground:
			if str(g["role"]) == line and not promised.has(g["id"]) and by_id.has(g["id"]):
				var q: Dictionary = by_id[g["id"]]
				starters[g["id"]] = line_rating(q, line) * Workload.selection_factor(q)
		for guard in range(6):
			var weak := -1
			var weak_v := INF
			for i in range(ground.size()):
				var id = ground[i]["id"]
				if str(ground[i]["role"]) == line and starters.has(id) and float(starters[id]) < weak_v:
					weak_v = float(starters[id])
					weak = i
			if weak < 0:
				break
			var best = null
			var best_v := weak_v
			for id in cands:
				if not used.has(id) and float(cands[id]) > best_v:
					best_v = float(cands[id])
					best = id
			if best == null:
				break
			used.erase(ground[weak]["id"])
			starters.erase(ground[weak]["id"])
			ground[weak] = _for_slot(by_id[best], line)
			used[best] = true
			starters[best] = best_v


## Players ordered by ruck work, best first (ties by overall), for filling
## an empty ruck spot with the nearest thing to a ruckman.
static func by_ruck(players: Array) -> Array:
	var out := players.duplicate()
	out.sort_custom(func(a, b):
		var ra := float(a["attr"]["ruck"])
		var rb := float(b["attr"]["ruck"])
		if ra != rb:
			return ra > rb
		return int(a["overall"]) > int(b["overall"]))
	return out


## The pool with each trial player listed in his trial position: his own
## position becomes his second, so every pick path treats him as a player of
## the new role. {id: role}.
static func _with_trial(pool: Array, trial: Dictionary) -> Array:
	var out := []
	for p in pool:
		var role := str(trial.get(str(p["id"]), ""))
		if role == "" or role == str(p.get("role", "")):
			out.append(p)
			continue
		var c: Dictionary = p.duplicate()
		c["own_role"] = str(p.get("own_role", p.get("role", "")))
		c["role2"] = str(p.get("role", ""))
		c["role"] = role
		out.append(c)
	return out


## Copy so the match-day slot does not rewrite the list player's natural role.
static func _for_slot(p: Dictionary, slot: String) -> Dictionary:
	var copy := p.duplicate()
	copy["list_tag"] = role_tag(p)
	# His own position, kept through every re-slotting (a copy of a copy
	# would otherwise take the last slot as his position). Display only.
	copy["own_role"] = str(p.get("own_role", p.get("role", "")))
	copy["role"] = slot
	return copy
