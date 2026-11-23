class_name RealFinals
extends RefCounted
## Where the real finals were played, 1990-2025 (Legacy mode, bug bash
## 2026-11-23): data/legacy/finals.csv, built from the AFL Tables season pages
## by tools/legacy_fixtures/build_finals.py.
##
## The game draws its own finals from its own ladder, so its finalists are not
## the real ones. What it keeps from history is where each week's finals went:
## a Victorian club's home final was never at its suburban ground but at the
## grounds Victorian clubs really hosted at that week (the MCG, Waverley Park
## to 1998, Docklands from 2000, Kardinia Park for Geelong in 2013, the
## Queensland hub in 2020 and the other states in 2021), and an interstate club
## went to Melbourne the weeks one really did (West Coast at Waverley in 1990
## and 1991, Brisbane at the MCG in the 2004 preliminary final) or left home
## (Sydney in Launceston in 2021).
##
## A final is one row {"year", "week", "kind", "label", "home", "away",
## "ground", "date", "own", "in_vic"}; `own` is the club whose own ground it was
## (only that club is sent there), `in_vic` whether the ground is in Victoria.

const PATH := "res://data/legacy/finals.csv"
const VIC_CLUBS := {"CAR": true, "COL": true, "ESS": true, "FIT": true, "GEE": true, "HAW": true,
		"MEL": true, "NTH": true, "RIC": true, "STK": true, "WBD": true}

static var _by_year := {}   # year -> Array of rows, week then date order
static var _loaded := false


## Whether the table has `year`'s finals.
static func has_year(year: int) -> bool:
	_load()
	return _by_year.has(year)


## `year`'s real finals (a copy), week then date order; [] for a year without.
static func for_year(year: int) -> Array:
	_load()
	return (_by_year.get(year, []) as Array).duplicate(true)


## The ground for the game's final `tag` (QF1, EF2, SF, PF1 ...) in finals week
## `week` of `year`, hosted by `host` against `away` whose own ground is
## `host_ground`. "" when history has nothing to say (keep the host's ground).
## The Grand Final is not here (SeasonRules gf_venue).
##
## The tag's place among the week's finals of its kind (QF2 is the second
## qualifying final) picks among the real ones, so the same final always gets
## the same ground whoever else is playing that week.
static func venue(year: int, week: int, tag: String, host: String, away: String, host_ground: String) -> String:
	_load()
	if not _by_year.has(year) or tag == "GF":
		return ""
	var kind := tag.rstrip("0123456789")
	var i: int = maxi(0, int(tag.substr(kind.length())) - 1) if tag.length() > kind.length() else 0
	var rows: Array = _by_year[year]
	var kind_rows := rows.filter(func(r): return int(r["week"]) == week and str(r["kind"]) == kind)
	if VIC_CLUBS.has(host):
		# The grounds Victorian clubs hosted at: this kind of final that week,
		# else any final that week, else any final that year.
		for pool in [kind_rows, rows.filter(func(r): return int(r["week"]) == week), rows]:
			var usable := (pool as Array).filter(func(r): return _hosts_for(r, host))
			if not usable.is_empty():
				return str(usable[i % usable.size()]["ground"])
		return ""
	# An interstate host stays home unless the matching real final left home:
	# that very club taken elsewhere, or an interstate club brought to
	# Victoria to play a Victorian one.
	if i >= kind_rows.size():
		return ""
	var r: Dictionary = kind_rows[i]
	var real_host := str(r["home"])
	if VIC_CLUBS.has(real_host) or str(r["own"]) == real_host:
		return ""
	if real_host == host and str(r["ground"]) != host_ground:
		return str(r["ground"])
	if int(r["in_vic"]) == 1 and VIC_CLUBS.has(away):
		return str(r["ground"])
	return ""


## Whether real final `r` was a Victorian club's home final that `host` (a
## Victorian club) can be sent to: a shared ground, or `host`'s own.
static func _hosts_for(r: Dictionary, host: String) -> bool:
	return (VIC_CLUBS.has(str(r["home"])) and str(r["kind"]) != "GF"
			and (str(r["own"]) == "" or str(r["own"]) == host))


static func _load() -> void:
	if _loaded:
		return
	_loaded = true
	_by_year = {}
	if not FileAccess.file_exists(PATH):
		push_error("RealFinals: missing %s" % PATH)
		return
	var f := FileAccess.open(PATH, FileAccess.READ)
	if f == null:
		return
	var head := Array(f.get_csv_line())
	while not f.eof_reached():
		var line := f.get_csv_line()
		if line.size() < head.size():
			continue
		var row := {}
		for k in range(head.size()):
			row[str(head[k])] = line[k]
		var y := int(row["year"])
		if not _by_year.has(y):
			_by_year[y] = []
		(_by_year[y] as Array).append(row)
