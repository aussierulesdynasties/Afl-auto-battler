class_name Datasets
extends RefCounted
## Which real league a career starts from (Legacy mode, TODO row 142). Each
## dataset is one season of real data - the lists, their ratings, the draft
## class - and the year the career then plays. GameDB.reload(id) loads one;
## the save keeps its id, and loading the save loads that set again.
##
## Every decade loads the same way: a row here names the data season (the
## season the lists are rated on, the one just played), the first playable
## year, the date ages are taken at, and the files. A file left out is a file
## that era has none of (no list additions in 1990, no overrides), never an
## error; only the players file is required.

const DEFAULT := "2026"

## Keys every row may carry, each a res:// path or left out:
## players (required): season totals plus bio, the players_enriched schema
## draftees: the real draft class taken after the data season
## history: draft pedigree, rated past seasons and career stints
## origin: each player's home state
## list_additions, list_addition_stats: listed players with no game that season
## list_types: which players who played that season were on a rookie list
## departures, club_moves: who left or changed club before the first season
## ladder: the data season's final ladder (no "year" column needed)
## ovr_overrides, potential_overrides: the director's hand-set numbers
## coaches: the season's coaching staff (Coaches.seed reads either format:
##   2026's researched six jobs, or a past season's club,role,name rows)
## leadership: the season's captains and vice-captains (Leadership)
## A row without coaches or leadership uses 2026's (a test league).
const FILE_KEYS := ["players", "draftees", "history", "origin", "list_additions", "list_addition_stats",
		"list_types", "departures", "club_moves", "ladder", "ovr_overrides", "potential_overrides",
		"coaches", "leadership"]

## One more key, a folder rather than a file: state_leagues, the VFL, SANFL and
## WAFL of the data season (TODO row 128; data/state_leagues/, built by
## tools/state_leagues/build.py). A row without it plays with no state leagues,
## exactly as before they existed.
const STATE_LEAGUES_KEY := "state_leagues"

## And a Legacy start's second tier (TODO row 142, L7): the folder of each
## season's real leagues and sides below the AFL (data/legacy/second_tier/,
## SecondTier). Each season start lays that season's shape over the state
## leagues; a row with a state_leagues folder never reads it.
const SECOND_TIER_KEY := "second_tier"

const _TABLE := {
	# Today's start: the completed 2026 season, careers from 2027.
	"2026": {
		"data_season": 2026, "start_year": 2027, "start_date": "2027-03-01",
		"players": "res://data/players_enriched_2026.csv",
		"draftees": "res://data/draftees_2026.csv",
		"history": "res://data/player_history_2026.csv",
		"origin": "res://data/player_origin_2026.csv",
		"list_additions": "res://data/list_additions_2026.csv",
		"list_addition_stats": "res://data/list_additions_stats.csv",
		"list_types": "res://data/list_types_2026.csv",
		"departures": "res://data/departures_2026.csv",
		"club_moves": "res://data/club_moves_2026.csv",
		"ladder": "res://data/ladder_2026.csv",
		"ovr_overrides": "res://data/ovr_overrides.csv",
		"potential_overrides": "res://data/potential_overrides.csv",
		"coaches": "res://data/coaches_2026.csv",
		"leadership": "res://data/leadership_2026.csv",
		"state_leagues": "res://data/state_leagues",
	},
	# The 2010 start: lists rated on 2009, coaches rated from their records
	# before 2010, the 2010 captains (tools/legacy_2010s/build_start.py and
	# build_leaders.py; TODO row 142). Gold Coast (2011) and GWS (2012) enter
	# as the sim's own expansion.
	"2010": {
		"data_season": 2009, "start_year": 2010, "start_date": "2010-03-01",
		"players": "res://data/legacy/2010/players_2010.csv",
		"coaches": "res://data/legacy/2010/coaches_2010.csv",
		"leadership": "res://data/legacy/2010/captains_2010.csv",
		"history": "res://data/legacy/2010/history_2010.csv",
		"list_additions": "res://data/legacy/2010/list_additions_2010.csv",
		"list_addition_stats": "res://data/legacy/2010/list_addition_stats_2010.csv",
		"second_tier": "res://data/legacy/second_tier",
	},
	# The 1990 start: lists rated on 1989, the season just played, built by
	# tools/legacy_1990s/build_start.py (TODO row 142, phase L1).
	"1990": {
		"data_season": 1989, "start_year": 1990, "start_date": "1990-03-01",
		"players": "res://data/legacy/1990/players_1990.csv",
		# The 1990 senior coaches (yours makes way, TODO row 142 L2) and the
		# clubs' 1990 captains and vice-captains.
		"coaches": "res://data/legacy/1990s/coaches_1990.csv",
		"leadership": "res://data/legacy/1990s/captains_1990.csv",
		"history": "res://data/legacy/1990/history_1990.csv",
		"list_additions": "res://data/legacy/1990/list_additions_1990.csv",
		"list_addition_stats": "res://data/legacy/1990/list_addition_stats_1990.csv",
		"second_tier": "res://data/legacy/second_tier",
	},
}

## Sets added at runtime (tests load a small fixture league this way).
static var _added := {}


## The row for a dataset id, or {} when there is none.
static func get_set(id: String) -> Dictionary:
	if _added.has(id):
		return _added[id]
	return _TABLE.get(id, {})


## True when the dataset is known and its players file ships in this build.
static func ready(id: String) -> bool:
	var d := get_set(id)
	return not d.is_empty() and FileAccess.file_exists(str(d.get("players", "")))


## Every dataset this build can start, oldest data first.
static func ready_ids() -> Array:
	var out := []
	for id in _TABLE.keys() + _added.keys():
		if ready(str(id)) and not out.has(id):
			out.append(id)
	out.sort_custom(func(a, b): return int(get_set(a)["data_season"]) < int(get_set(b)["data_season"]))
	return out


## A dataset's file for `key`, or "" when the era has none.
static func file(id: String, key: String) -> String:
	return str(get_set(id).get(key, ""))


static func add(id: String, row: Dictionary) -> void:
	_added[id] = row


static func remove(id: String) -> void:
	_added.erase(id)
