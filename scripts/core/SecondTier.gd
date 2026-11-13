class_name SecondTier
extends RefCounted
## The real second tier by season (Legacy mode, TODO row 142, phase L7): what
## the AFL clubs' players played in below the seniors, every season from 1990
## to 2026. The AFL Reserves to 1999, each club's own side; the VFA, the VFL
## and its alignments; the SANFL and WAFL, which took Adelaide's, Port's, West
## Coast's and Fremantle's players back to their old clubs before those clubs
## fielded sides of their own; the north's leagues; today's VFL, SANFL and WAFL.
##
## Two files in one folder (data/legacy/second_tier/, checked by
## tools/check_legacy_second_tier.py), every row sourced:
## leagues.csv  league, name, from, to: the years a league was held (a season
##              not held, the 2020 VFL, is a gap between two rows)
## sides.csv    league, code, name, kind, afl_club, from, to: one side's span
##              in one league. kind is reserves (an AFL club's own side),
##              aligned (a state club an AFL club sends its players to;
##              afl_club may name two, "STK|MEL"), standalone, host (a host
##              system: with a code, the one club that took the AFL club's
##              players that season; blank, they went back to the league's
##              clubs, each to his own) or none (the AFL club's players had no
##              second tier that season; code blank). A blank `to` runs on
##              past 2026.
##
## A season after the last row keeps the last row's shape. Loading is a pure
## read; GameDB.apply_second_tier lays a season's shape over the state leagues.

const KINDS := ["reserves", "aligned", "standalone", "host", "none"]

var leagues: Array = []   # {league, name, from, to}
var sides: Array = []     # {league, code, name, kind, afl_clubs: Array, from, to}


## Read a second-tier folder; an empty or missing folder gives an empty shape.
static func load_dir(dir: String) -> SecondTier:
	var t := SecondTier.new()
	if dir == "":
		return t
	for r in _rows("%s/leagues.csv" % dir):
		t.leagues.append({"league": str(r["league"]), "name": str(r["name"]),
				"from": int(r["from"]), "to": _to(r)})
	for r in _rows("%s/sides.csv" % dir):
		var afl := str(r.get("afl_club", ""))
		t.sides.append({"league": str(r["league"]), "code": str(r["code"]), "name": str(r["name"]),
				"kind": str(r["kind"]), "afl_clubs": Array(afl.split("|", false)),
				"from": int(r["from"]), "to": _to(r)})
	return t


func is_empty() -> bool:
	return sides.is_empty()


## True when `year` falls in a row's span (a blank `to` is open).
static func covers(row: Dictionary, year: int) -> bool:
	return int(row["from"]) <= year and (int(row["to"]) == 0 or year <= int(row["to"]))


## The leagues held in `year`, oldest row first: id -> name.
func leagues_in(year: int) -> Dictionary:
	var out := {}
	for r in leagues:
		if covers(r, year):
			out[r["league"]] = r["name"]
	return out


## The season's shape: league id -> {"name", "clubs": [codes in file order]}.
## Only sides with a code in a league held that year, and only leagues with a
## side: a league whose own clubs the data does not list (the QAFL, where the
## Bears' players went back to their clubs) is no league to lay out, though
## of_club still names it as the players' host.
func shape(year: int) -> Dictionary:
	var held := leagues_in(year)
	var out := {}
	for id in held:
		out[id] = {"name": held[id], "clubs": []}
	for s in sides:
		if str(s["code"]) != "" and covers(s, year) and out.has(s["league"]):
			(out[s["league"]]["clubs"] as Array).append(str(s["code"]))
	for id in held:
		if (out[id]["clubs"] as Array).is_empty():
			out.erase(id)
	return out


## Each side's row in `year`: code -> side row.
func sides_in(year: int) -> Dictionary:
	var held := leagues_in(year)
	var out := {}
	for s in sides:
		if str(s["code"]) != "" and covers(s, year) and held.has(s["league"]):
			out[s["code"]] = s
	return out


## Where an AFL club's players went below the seniors in `year`:
## {"league", "code", "kind"}. Its own side, an aligned or host club first,
## then a host league (code "") or a recorded none (league and code ""); {} when the data has no row.
func of_club(afl_code: String, year: int) -> Dictionary:
	var held := leagues_in(year)
	var fallback := {}
	for s in sides:
		if not covers(s, year) or not (s["afl_clubs"] as Array).has(afl_code):
			continue
		var kind := str(s["kind"])
		var has_club := kind == "reserves" or kind == "aligned" or (kind == "host" and str(s["code"]) != "")
		if has_club and held.has(s["league"]):
			return {"league": str(s["league"]), "code": str(s["code"]), "kind": kind}
		if (kind == "host" or kind == "none") and fallback.is_empty():
			fallback = {"league": str(s["league"]) if kind == "host" else "", "code": "", "kind": kind}
	return fallback


static func _to(r: Dictionary) -> int:
	var v := str(r.get("to", ""))
	return int(v) if v.is_valid_int() else 0


static func _rows(path: String) -> Array:
	var out := []
	if not FileAccess.file_exists(path):
		return out
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return out
	var header := f.get_csv_line()
	while not f.eof_reached():
		var cells := f.get_csv_line()
		if cells.size() < header.size() or str(cells[0]).strip_edges() == "":
			continue
		var d := {}
		for i in range(header.size()):
			d[header[i].strip_edges()] = cells[i].strip_edges()
		out.append(d)
	f.close()
	return out
