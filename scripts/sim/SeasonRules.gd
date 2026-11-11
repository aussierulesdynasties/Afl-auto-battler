class_name SeasonRules
extends RefCounted
## The shape of a season by year (legacy mode, TODO row 142): how many rounds
## and games, how many clubs make the finals and how the finals are drawn,
## where the Grand Final is played, whether there is a Gather Round, and what
## happens to a drawn final.
##
## The real seasons 1990-2025 are rows of data/season_rules.csv (read from the
## AFL Tables season pages: games per club, rounds, finalists, the finals
## pairings and venues). Any other year (2026 on, or a season with no year)
## gets DEFAULT, the game's own league: 24 rounds, ten finalists with the
## wildcard round, the Grand Final at the MCG, a Gather Round, extra time.
## Every decade loads the same way: one table, keyed by year, read by Season.

const PATH := "res://data/season_rules.csv"

## The game's league (2026 on). games 0: the fixture's own rule (one bye at an
## even club count, two at an odd one).
const DEFAULT := {
	"year": 0, "rounds": 24, "games": 0, "finalists": 10, "finals": "wildcard10",
	"gf_venue": "MCG", "gather_round": true, "drawn_finals": "extra_time",
}

## The finals brackets. Each is its weeks in order; each week its matches as
## [tag, label, home side, away side, order by ladder]. A side is a slot:
##   "S3"     the club that finished 3rd
##   "W_QF1"  the winner (L_ the loser) of the final tagged QF1
##   "HI_EF"  the higher-placed of the two elimination final winners (LO_EF the
##            lower), for the final six
##   "RW2"    the 2nd-placed of week one's winners (RL1 the 1st-placed loser),
##            for the McIntyre final eight
## "order by ladder" true: the higher-placed club is listed first and hosts.
const BRACKETS := {
	# The game's league: ten finalists, a wildcard round, then the AFL final eight.
	"wildcard10": [
		[["WC1", "Wildcard Final 1", "S7", "S10", false], ["WC2", "Wildcard Final 2", "S8", "S9", false]],
		[["QF1", "Qualifying Final 1", "S1", "S4", false], ["QF2", "Qualifying Final 2", "S2", "S3", false],
				# Wildcard winners reseed by original ladder position: the winner
				# of 7v10 takes the 7th seed, the winner of 8v9 the 8th.
				["EF1", "Elimination Final 1", "S5", "W_WC2", false],
				["EF2", "Elimination Final 2", "S6", "W_WC1", false]],
		[["SF1", "Semi Final 1", "L_QF1", "W_EF1", false], ["SF2", "Semi Final 2", "L_QF2", "W_EF2", false]],
		[["PF1", "Preliminary Final 1", "W_QF1", "W_SF2", false], ["PF2", "Preliminary Final 2", "W_QF2", "W_SF1", false]],
		[["GF", "Grand Final", "W_PF1", "W_PF2", false]],
	],
	# The AFL final eight, 2000-2025.
	"afl8": [
		[["QF1", "Qualifying Final 1", "S1", "S4", false], ["QF2", "Qualifying Final 2", "S2", "S3", false],
				["EF1", "Elimination Final 1", "S5", "S8", false], ["EF2", "Elimination Final 2", "S6", "S7", false]],
		[["SF1", "Semi Final 1", "L_QF1", "W_EF1", false], ["SF2", "Semi Final 2", "L_QF2", "W_EF2", false]],
		[["PF1", "Preliminary Final 1", "W_QF1", "W_SF2", false], ["PF2", "Preliminary Final 2", "W_QF2", "W_SF1", false]],
		[["GF", "Grand Final", "W_PF1", "W_PF2", false]],
	],
	# The McIntyre final eight, 1994-1999: 1v8, 2v7, 3v6, 4v5; the two
	# lowest-placed losers go out and the two highest-placed winners rest a week.
	"mcintyre8": [
		[["QF1", "Qualifying Final 1", "S1", "S8", false], ["QF2", "Qualifying Final 2", "S2", "S7", false],
				["QF3", "Qualifying Final 3", "S3", "S6", false], ["QF4", "Qualifying Final 4", "S4", "S5", false]],
		[["SF1", "Semi Final 1", "RW3", "RL1", false], ["SF2", "Semi Final 2", "RW4", "RL2", false]],
		[["PF1", "Preliminary Final 1", "RW1", "W_SF2", false], ["PF2", "Preliminary Final 2", "RW2", "W_SF1", false]],
		[["GF", "Grand Final", "W_PF1", "W_PF2", true]],
	],
	# The final six, 1992-1993: the qualifying final's two clubs both go on.
	"final6": [
		[["QF", "Qualifying Final", "S1", "S2", false], ["EF1", "Elimination Final 1", "S3", "S6", false],
				["EF2", "Elimination Final 2", "S4", "S5", false]],
		[["SF1", "Semi Final 1", "W_QF", "HI_EF", false], ["SF2", "Semi Final 2", "L_QF", "LO_EF", false]],
		[["PF", "Preliminary Final", "L_SF1", "W_SF2", true]],
		[["GF", "Grand Final", "W_SF1", "W_PF", true]],
	],
	# The final six as 1991 drew its first week: 3rd v 4th and 5th v 6th.
	"final6_1991": [
		[["QF", "Qualifying Final", "S1", "S2", false], ["EF1", "Elimination Final 1", "S3", "S4", false],
				["EF2", "Elimination Final 2", "S5", "S6", false]],
		[["SF1", "Semi Final 1", "W_QF", "HI_EF", false], ["SF2", "Semi Final 2", "L_QF", "LO_EF", false]],
		[["PF", "Preliminary Final", "L_SF1", "W_SF2", true]],
		[["GF", "Grand Final", "W_SF1", "W_PF", true]],
	],
	# The McIntyre final five, to 1990: the minor premier waits for the
	# qualifying final's winner in the second semi.
	"mcintyre5": [
		[["QF", "Qualifying Final", "S2", "S3", false], ["EF", "Elimination Final", "S4", "S5", false]],
		[["SF1", "Semi Final 1", "L_QF", "W_EF", false], ["SF2", "Semi Final 2", "S1", "W_QF", false]],
		[["PF", "Preliminary Final", "L_SF2", "W_SF1", true]],
		[["GF", "Grand Final", "W_SF2", "W_PF", true]],
	],
}

## Each bracket's weeks as a coach names them.
const WEEK_NAMES := {
	"wildcard10": ["Wildcard Round", "Qualifying and Elimination Finals", "Semi Finals",
			"Preliminary Finals", "Grand Final"],
	"afl8": ["Qualifying and Elimination Finals", "Semi Finals", "Preliminary Finals", "Grand Final"],
	"mcintyre8": ["Qualifying Finals", "Semi Finals", "Preliminary Finals", "Grand Final"],
	"final6": ["Qualifying and Elimination Finals", "Semi Finals", "Preliminary Final", "Grand Final"],
	"final6_1991": ["Qualifying and Elimination Finals", "Semi Finals", "Preliminary Final", "Grand Final"],
	"mcintyre5": ["Qualifying and Elimination Finals", "Semi Finals", "Preliminary Final", "Grand Final"],
}

static var _rows: Array = []
static var _loaded := false


## The rules of `year`'s season: a copy of DEFAULT with the year's row over it.
static func for_year(year: int) -> Dictionary:
	var out := DEFAULT.duplicate()
	out["year"] = year
	for row in rows():
		if year >= int(row["from_year"]) and year <= int(row["to_year"]):
			for k in ["rounds", "games", "finalists", "finals", "gf_venue", "gather_round", "drawn_finals"]:
				out[k] = row[k]
			break
	return out


## The table's rows, typed, read once.
static func rows() -> Array:
	if _loaded:
		return _rows
	_loaded = true
	_rows = []
	if not FileAccess.file_exists(PATH):
		push_error("SeasonRules: missing %s" % PATH)
		return _rows
	var f := FileAccess.open(PATH, FileAccess.READ)
	if f == null:
		return _rows
	var head := Array(f.get_line().strip_edges().split(","))
	while not f.eof_reached():
		var line := f.get_line().strip_edges()
		if line == "":
			continue
		var cells := Array(line.split(","))
		var row := {}
		for i in range(mini(head.size(), cells.size())):
			row[head[i]] = cells[i]
		for k in ["from_year", "to_year", "rounds", "games", "finalists"]:
			row[k] = int(row.get(k, "0"))
		row["gather_round"] = str(row.get("gather_round", "0")) == "1"
		_rows.append(row)
	f.close()
	return _rows


## The bracket of a format (DEFAULT's when the name is unknown).
static func bracket(format: String) -> Array:
	return BRACKETS.get(format, BRACKETS[DEFAULT["finals"]])


## How many weeks a format's finals take.
static func finals_weeks(format: String) -> int:
	return bracket(format).size()


## Every final's tag in a format, in the order they are played.
static func tags(format: String) -> Array:
	var out := []
	for week in bracket(format):
		for m in week:
			out.append(m[0])
	return out


## A finals week's name ("Semi Finals"), 1-based; "" past the last.
static func week_name(format: String, week: int) -> String:
	var names: Array = WEEK_NAMES.get(format, WEEK_NAMES[DEFAULT["finals"]])
	return str(names[week - 1]) if week >= 1 and week <= names.size() else ""


## Whether a final drawn at the end of normal time is played again the next
## week (true) or goes to extra time (false): every final in 1990, the Grand
## Final alone from 1991 to 2015, none since.
static func replays_draw(drawn_finals: String, tag: String) -> bool:
	if drawn_finals == "replay_all":
		return true
	return drawn_finals == "replay_gf" and tag == "GF"
