class_name EraFootball
extends RefCounted
## Each season's football by era (legacy mode, TODO row 142, phase L5). Director,
## 2026-11-13: "Era rules in engine": the 1990 slice plays 1990's football, tuned
## to real 1990 averages, and every season to 2026 plays its own year's ("its
## simply the start of a 36+ year campaign": the season being played decides,
## never the start year).
##
## A past season's football is a row of data/legacy/era_football.csv: multipliers
## on the match engine's rates (Ratings.T keys, applied in MatchSim._rates() as
## WEATHER_RATES is), fitted so a match of that year makes that year's real team
## rates against what a 2026 match makes against 2026's (the real rates per
## season: tools/balance/afl_year_rates.json; the fit: tools/balance/fit_era.py).
## 2026 on, and a match with no year, plays today's football: no row, no change.
## How a player is rated is untouched: each season's players are rated against
## their own season (L1), so the era's level of the game lives here only.

const PATH := "res://data/legacy/era_football.csv"
## The rates an era row may move (Ratings.T keys). Anything else in the file is
## a note column.
const KEYS := ["chains_per_game", "handball_share", "mark_share_of_kicks", "pressure_base",
		"inside50_goal", "inside50_behind", "hitouts_per_stoppage", "clanger_is_free"]
## The engine's own umpiring chances an era row may scale (MatchSim._era, 1.0
## today): free_rate, the contextual frees (high contact, holding the ball,
## marking contests). Era umpiring paid far more of them: 1990 averaged 25 frees a
## team against 19 in 2026.
const SIM := ["free_rate"]
## The first season today's football is played in: no era row from here on.
const TODAY := 2026

static var _rows := {}
static var _loaded := false
static var _lock := Mutex.new()


## The multipliers on Ratings.T (KEYS) and the umpiring chances (SIM) for a match played in `year` ({} for today's
## football: 2026 on, no year, or a year with no row).
static func rates_for(year: int) -> Dictionary:
	if year <= 0 or year >= TODAY:
		return {}
	_load()
	return (_rows.get(year, {}) as Dictionary).duplicate()


## Interchange players a side names for a match in `year`. Today's bench
## (Ratings.INTERCHANGE) until L4's era rules by year land; that phase owns the
## real counts (data/legacy/era_rules.csv) and wires them in here.
static func interchange(_year: int) -> int:
	return Ratings.INTERCHANGE


## The seasons with an era row, oldest first.
static func years() -> Array:
	_load()
	var out := _rows.keys()
	out.sort()
	return out


static func _load() -> void:
	_lock.lock()
	if not _loaded:
		_loaded = true
		var f := FileAccess.open(PATH, FileAccess.READ)
		if f != null:
			var head := f.get_csv_line()
			while not f.eof_reached():
				var line := f.get_csv_line()
				if line.size() < head.size() or str(line[0]).strip_edges() == "":
					continue
				var row := {}
				for i in range(1, head.size()):
					if (str(head[i]) in KEYS or str(head[i]) in SIM) and str(line[i]).strip_edges() != "":
						row[str(head[i])] = float(line[i])
				_rows[int(line[0])] = row
	_lock.unlock()
