class_name LegacyRollover
extends RefCounted
## A Legacy career's rollovers, 1990 to 2026 (TODO row 142, phase L8): each
## year's real draft class in the open draft, each new club's real
## state-league foundation, and the Fitzroy merger. The sim makes the picks, the later careers and the
## retirements: an alternative history from real starting points (director
## 2026-11-10). A career on today's data never reaches any of this.
##
## Data: data/legacy/classes.csv and entry_lists.csv, built by
## tools/legacy_1990s/build_rollovers.py; entry_attributes.csv, the
## established foundation players' 18 attributes, by tools/wheelo/attributes.py.

const CLASSES_CSV := "res://data/legacy/classes.csv"
const ENTRY_CSV := "res://data/legacy/entry_lists.csv"
const ENTRY_ATTRIBUTES_CSV := "res://data/legacy/entry_attributes.csv"

## The Fitzroy merger (director 2026-11-11): "it always happens unless you are
## regularly competing in finals, and even then, the story beat still happens
## (with a slim chance of the merge going ahead no matter what) / if youre
## struggling though, no choice, the merge happens whether you want it to or not".
const MERGED := "FIT"
const MERGED_INTO := "BRL"
## Talks open at the start of this season; the merger is settled after it.
const TALKS_YEAR := 1996
## "Regularly competing in finals": finals in this many of the last three seasons.
const FINALS_NEEDED := 2
## The slim chance the merger goes ahead anyway, in percent.
const MERGE_ANYWAY_PCT := 10
## Fitzroy players the Brisbane Lions take (the real merger's eight).
const LIONS_TAKE := 8

static var _classes := {}   # year -> Array of class rows
static var _entries := {}   # "code|year" -> Array of entry rows
static var _entry_attrs := {}   # "year|code|first|last" -> attributes row
static var _later := {}     # "real name|dob" -> the last off-season a real list took him


## True for a career started on a past season's data.
static func on() -> bool:
	return GameDB.DATA_SEASON < int(Datasets.get_set(Datasets.DEFAULT).get("data_season", 2026))


static func _load() -> void:
	if not _classes.is_empty():
		return
	for r in GameDB._read_dicts(CLASSES_CSV):
		var y := int(r.get("year", "0"))
		if not _classes.has(y):
			_classes[y] = []
		(_classes[y] as Array).append(r)
	for r in GameDB._read_dicts(ENTRY_CSV):
		var key := "%s|%s" % [str(r.get("club", "")), str(r.get("year", ""))]
		if not _entries.has(key):
			_entries[key] = []
		(_entries[key] as Array).append(r)
	for r in GameDB._read_dicts(ENTRY_ATTRIBUTES_CSV):
		_entry_attrs["%s|%s|%s|%s" % [str(r.get("year", "")), str(r.get("club", "")), str(r.get("first", "")),
				str(r.get("last", ""))]] = r
	# When a real list last took each man: his class's draft, or the
	# off-season before a new club's first list (career_ahead).
	for y in _classes:
		for r in _classes[y]:
			_note_later(r, int(y))
	for key in _entries:
		for r in _entries[key]:
			_note_later(r, int(str(r.get("year", "0"))) - 1)


static func _note_later(r: Dictionary, off: int) -> void:
	var dob := str(r.get("dob", ""))
	if dob.length() < 10:
		return
	var k := "%s %s|%s" % [str(r.get("first", "")), str(r.get("last", "")), dob]
	_later[k] = maxi(int(_later.get(k, 0)), off)


## Whether a real man delisted in `year`'s off-season really played on: his
## last real season is later, or a real draft or new club's first list took
## him in this off-season or after. Such a man goes into the drafts before his
## career can end (GameState._close_free_agency), at every club alike.
static func career_ahead(p: Dictionary, year: int) -> bool:
	return int(p.get("real_last", 0)) > year or taken_later(p, year)


## Whether a real draft or new club's first list took him in `year`'s
## off-season or after (not just a later last season).
static func taken_later(p: Dictionary, year: int) -> bool:
	if not on():
		return false
	_load()
	var dob := str(p.get("dob", ""))
	if str(p.get("real_name", "")) == "" or dob.length() < 10:
		return false
	return int(_later.get("%s|%s" % [str(p["real_name"]), dob], 0)) >= year


## The real class drafted at the end of `year`, if this career has one.
static func has_class(year: int) -> bool:
	if not on():
		return false
	_load()
	return _classes.has(year)


## Whether `code`, entering in `year`, has a real state-league foundation.
static func has_foundation(code: String, year: int) -> bool:
	if not on():
		return false
	_load()
	return _entries.has("%s|%d" % [code, year])


# ---------------------------------------------------------------------------
# The draft class
# ---------------------------------------------------------------------------
## The real class drafted at the end of `year` as prospects: rated from his
## draft position like any class, his potential from his best real season
## (the "Informed" ruling, director 2026-11-11). A mature-age pick is in his
## own class however old he is (Prospects.age_pool).
static func real_class(year: int) -> Array:
	_load()
	var out := []
	for r in _classes.get(year, []):
		var rank := int(r.get("rank", "0"))
		var p := {}
		p["first"] = str(r.get("first", ""))
		p["last"] = str(r.get("last", ""))
		p["real_name"] = "%s %s" % [p["first"], p["last"]]
		p["generic_name"] = ""
		p["name"] = ""
		p["id"] = "R%d_%03d" % [year, rank]
		var origin := str(r.get("origin", ""))
		p["club"] = origin
		p["num"] = rank
		p["src"] = "U18"
		for k in GameDB.STAT_KEYS:
			p[k] = 0.0
		p["height_cm"] = float(str(r.get("height_cm", "0")).to_int())
		p["weight_kg"] = 0.0
		var dob := str(r.get("dob", ""))
		p["dob"] = dob if dob.length() >= 10 else "%04d-07-01" % (year - 18)
		# age_pool adds the year a class waits in the pool: he arrives at his
		# age at the next season's start, as the real 2026 class is aged.
		p["age"] = float(Prospects.days_between(str(p["dob"]), "%d-03-01" % (year + 1))) / 365.25 - 1.0
		p["real_class"] = true
		var role := str(r.get("role", ""))
		p["role"] = role if role in ["RUCK", "MID", "DEF", "FWD"] else GameDB.listed_role(p)
		p["role2"] = ""
		p["real_pos"] = Ratings.ROLE_SHORT_TO_POS.get(str(p["role"]), "MID")
		p["debut"] = ""
		p["height_source"] = "draft class"
		p["draft_year"] = year
		p["draft_rank"] = rank
		p["draft_team"] = origin
		p["draft_league"] = ""
		p["draft_state"] = ""
		var tie := str(r.get("tie", ""))
		p["tied_club"] = str(r.get("club", "")) if tie != "" else ""
		p["tied_type"] = tie
		for k in ["u18_gm", "u18_di", "u18_gl", "u18_mk", "u18_tk", "u18_if50", "u18_ho"]:
			p[k] = 0.0
		p["note"] = ""
		p["data_src"] = "real class %d" % year
		p["draft_class"] = true
		if str(r.get("peak", "")) != "":
			p["real_peak"] = int(str(r["peak"]))
		# His last real season (build_rollovers): he retires about then, as
		# a start list's real player does (Prospects.should_retire).
		if str(r.get("last_season", "")) != "":
			p["real_last"] = int(str(r["last_season"]))
		Prospects.project(p)
		out.append(p)
	GameDB.assign_aliases(out)
	return out


# ---------------------------------------------------------------------------
# A new club's state-league foundation
# ---------------------------------------------------------------------------
## `code`'s state-league foundation for its first season, `year`: the
## players of its real first list that no draft class brings in. A new club
## builds the rest of its list by the game's expansion rules (ExpansionBuild):
## its concession picks in the open draft and the out-of-contract players it
## signs, from wherever the save has them. Nobody joins it because he really
## did (director, 2026-11-13: "the sim will not replicate historical draftee
## clubs"). Each takes his 18 attributes from his last AFL season before
## `year` (entry_attributes.csv), or is rated as a prospect if he has none. At most
## Expansion.foundation_size (a club entering before the expansion
## concessions signs its whole first senior list), the best of them; the rest go into the draft
## before `year` (returned as "pool"); fewer, and the club tops up with
## state-league signings as any new club does.
## Returns {"list": players, "pool": players for the draft}.
static func foundation(gs, code: String, year: int) -> Dictionary:
	_load()
	var list := []
	var established := []
	var n := 0
	for r in _entries.get("%s|%d" % [code, year], []):
		n += 1
		var p := _new_player(code, year, n, r)
		if str(r.get("src", "")) != "":
			established.append([p, r])
		list.append(p)
	# Each on his src season's stats (tools/wheelo/attributes.py), as the
	# starts' listed players are (GameDB._apply_attributes).
	for e in established:
		var p: Dictionary = e[0]
		var r: Dictionary = e[1]
		var role := str(r.get("role", ""))
		if role in ["RUCK", "MID", "DEF", "FWD"]:
			p["role"] = role
		var row: Dictionary = _entry_attrs.get("%d|%s|%s|%s" % [year, code, str(r.get("first", "")),
				str(r.get("last", ""))], {})
		if row.is_empty():
			push_warning("LegacyRollover: no attributes for %s %s (%s %d); rated as a prospect" % [
					str(r.get("first", "")), str(r.get("last", "")), code, year])
			Prospects.project(p)
			p.erase("projected")
		else:
			var a := {}
			for k in Attributes.KEYS:
				a[k] = clampi(int(row.get(k, 50)), 1, 99)
			p["attr"] = a
			p["apos"] = str(row.get("apos", ""))
			p["speed_src"] = str(row.get("speed_src", ""))
			p["role"] = Rating.line_of(str(p["apos"]))
			var line2 := str(row.get("line2", ""))
			p["role2"] = line2 if line2 != str(p["role"]) else ""
		# Unknown up to the season he joins; every season after is counted.
		p["career"] = Career.from_source("?", year - 1)
		p["data_club"] = code
		Potential.assign(p)
	GameDB.assign_aliases(list)
	GameDB.register_draftees(list)
	list.sort_custom(func(a, b): return int(Rating.ovr(a, 0)) > int(Rating.ovr(b, 0)))
	var pool := []
	var size := Expansion.foundation_size(code)
	while list.size() > size:
		var p: Dictionary = list.pop_back()
		p["club"] = ""
		p["draft_year"] = year - 1
		pool.append(p)
	if list.size() < size:
		var more: Array = Expansion.foundation_list(code, year - 1, int(gs.career_seed))
		list.append_array(more.slice(0, size - list.size()))
	for p in list:
		p["club"] = code
		if str(p.get("note", "")) == "":
			p["note"] = "State-league signing, %d" % (year - 1)
	return {"list": list, "pool": pool}


## A player new to the career, as GameDB builds a list addition.
static func _new_player(code: String, year: int, n: int, r: Dictionary) -> Dictionary:
	var p := {}
	p["first"] = str(r.get("first", ""))
	p["last"] = str(r.get("last", ""))
	p["real_name"] = "%s %s" % [p["first"], p["last"]]
	p["generic_name"] = ""
	p["name"] = ""
	# A state-league signing, as ExpansionBuild names one (FND_).
	p["id"] = "FND_%s_L%d_%03d" % [code, year, n]
	p["club"] = code
	p["num"] = int(str(r.get("num", "0")).to_int())
	p["src"] = "LIST"
	for k in GameDB.STAT_KEYS:
		p[k] = 0.0
	p["height_cm"] = float(str(r.get("height_cm", "0")).to_int())
	p["weight_kg"] = 0.0
	var dob := str(r.get("dob", ""))
	p["dob"] = dob
	# Aged at his first season's start, as the league has just been aged.
	p["age"] = float(Prospects.days_between(dob, "%d-03-01" % year)) / 365.25 if dob.length() >= 10 else 22.0
	p["debut"] = ""
	p["height_source"] = "club list" if p["height_cm"] > 0.0 else ""
	var list_type := str(r.get("list", ""))
	p["list_type"] = list_type
	if list_type == "rookie":
		p["rookie_list"] = true
	if str(r.get("peak", "")) != "":
		p["real_peak"] = int(str(r["peak"]))
	# His last real season (build_rollovers): he retires about then, as a
	# start list's or a class's real player does (Prospects.should_retire).
	# He really played the club's first season, so his career runs to it.
	if str(r.get("last_season", "")) != "":
		p["real_last"] = int(str(r["last_season"]))
		p["real_first"] = year
	var role := str(r.get("role", ""))
	p["role"] = role if role in ["RUCK", "MID", "DEF", "FWD"] else GameDB.listed_role(p)
	p["role2"] = ""
	p["real_pos"] = Ratings.ROLE_SHORT_TO_POS.get(str(p["role"]), "MID")
	p["draft_year"] = year - 1
	p["draft_team"] = ""
	p["draft_league"] = ""
	p["draft_state"] = ""
	p["tied_club"] = ""
	p["tied_type"] = ""
	for k in ["u18_gm", "u18_di", "u18_gl", "u18_mk", "u18_tk", "u18_if50", "u18_ho"]:
		p[k] = 0.0
	p["note"] = ""
	var src := str(r.get("src", ""))
	if src != "":
		var blank := []
		for k in GameDB.STAT_KEYS:
			if r.has(k) and str(r[k]) != "":
				p[k] = float(str(r[k]))
			else:
				blank.append(k)   # not recorded that season
		p["blank"] = blank
		p["stats_year"] = int(src)
		p["draft_rank"] = 0
		p["data_src"] = "listed %d, rated on the %s season" % [year, src]
		return p
	# Rated as the prospect he still is, as GameDB rates a list addition with
	# no senior game: a young one about a mid-first-round pick, older lower.
	var h := absi(hash(str(p["id"])))
	var age := float(p["age"])
	var rank := 22 + h % 20
	if age >= 21.5:
		rank = 45 + h % 15
	elif list_type == "rookie" or age >= 20.5:
		rank = 35 + h % 15
	p["draft_rank"] = rank
	p["data_src"] = "listed %d, no senior game" % year
	Prospects.project(p)
	# An expansion list's player past his first season's age is aged by the
	# curves, as the generated top-ups beside him are (blueprint §4).
	Prospects._age_into(p)
	return p


# ---------------------------------------------------------------------------
# Fitzroy and the Brisbane Bears
# ---------------------------------------------------------------------------
static func _st(gs) -> Dictionary:
	if not (gs.legacy is Dictionary):
		gs.legacy = {}
	if not gs.legacy.has("finals"):
		gs.legacy["finals"] = {}
	return gs.legacy


## Record the clubs that played finals in the season just played.
static func note_finals(gs) -> void:
	if not on() or gs.season == null:
		return
	var rows: Array = gs.season.ladder_sorted()
	var fin := []
	# A season with no games played (a test skips one) has no finalists: a
	# level table would read as the first clubs in alphabetical order.
	if rows.all(func(r): return int(r.get("p", 0)) == 0):
		rows = []
	for i in range(mini(gs.season.finalists(), rows.size())):
		fin.append(str(rows[i]["code"]))
	_st(gs)["finals"][str(gs.season_year)] = fin


## Seasons from `years` in which `code` played finals.
static func finals_in(gs, code: String, years: Array) -> int:
	var fin: Dictionary = _st(gs)["finals"]
	var n := 0
	for y in years:
		if (fin.get(str(y), []) as Array).has(code):
			n += 1
	return n


## Whether this career still has the merger to come.
static func _merger_ahead(gs) -> bool:
	return on() and GameDB.clubs.has(MERGED) and GameDB.clubs.has(MERGED_INTO) \
			and str(_st(gs).get("fitzroy", "")) == ""


## The talks open before TALKS_YEAR: the story, with the odds both ways and
## where Fitzroy stand.
static func talks_line(gs) -> String:
	var y1 := TALKS_YEAR - 2
	var y2 := TALKS_YEAR - 1
	var stay := 100 - MERGE_ANYWAY_PCT
	var had := finals_in(gs, MERGED, [y1, y2])
	var line := "Fitzroy's board has opened merger talks with the Brisbane Bears. The decision comes after the %d season: if Fitzroy have played finals in two of %d, %d and %d, there is a %d%% chance they play on in %d and a %d%% chance the merger goes ahead anyway; if not, they merge (100%%). " % [
			TALKS_YEAR, y1, y2, TALKS_YEAR, stay, TALKS_YEAR + 1, MERGE_ANYWAY_PCT]
	if had >= FINALS_NEEDED:
		line += "With finals in %d and %d, they have done enough: %d%% they play on, %d%% they merge." % [y1, y2, stay, MERGE_ANYWAY_PCT]
	elif had == 0:
		line += "They missed the finals in %d and %d, so there is no way out: Fitzroy merge with the Bears after the %d season (100%%)." % [y1, y2, TALKS_YEAR]
	else:
		var played := y1 if finals_in(gs, MERGED, [y1]) == 1 else y2
		line += "They played finals in %d only: make the finals in %d and it is %d%% they play on; miss them and they merge (100%%)." % [
				played, TALKS_YEAR, stay]
	return line


## At the rollover into `next_year`. Into TALKS_YEAR: the talks open (news).
## Into the year after: the merger is settled before the coach moves (a
## Fitzroy coach goes to the Brisbane Lions), and the lists after the season
## is closed (merge_lists).
static func before_moves(gs, next_year: int) -> void:
	if not _merger_ahead(gs):
		return
	if next_year == TALKS_YEAR:
		gs.add_news("legacy", talks_line(gs))
		return
	if next_year != TALKS_YEAR + 1:
		return
	_decide(gs)


## When the TALKS_YEAR off-season opens, before any club re-signs: the merger
## is settled and, as in 1996, Fitzroy's best go to the Brisbane Lions and the
## rest into that year's National Draft. A coach at Fitzroy keeps the old
## order (decided at the rollover, the rest to free agency), since his club
## has a list to run until he moves.
static func settle_merger(gs) -> void:
	if not _merger_ahead(gs) or int(gs.season_year) != TALKS_YEAR or str(gs.my_club) == MERGED:
		return
	note_finals(gs)
	_decide(gs)
	if str(_st(gs).get("fitzroy", "")) == "merged":
		_merge(gs, true)


## True once `code` has merged away (Fitzroy, its list gone): from the 1996
## off-season on it has no seat at a draft and holds no pick.
static func merged_away(gs, code: String) -> bool:
	# Outside Legacy there is no merger: asking must not create a legacy record.
	return on() and code == MERGED and bool(_st(gs).get("merge_done", false))


## Merge or play on: finals in two of the last three seasons give a
## MERGE_ANYWAY_PCT chance of merging; fewer, and they merge.
static func _decide(gs) -> void:
	var st := _st(gs)
	var regular := finals_in(gs, MERGED, [TALKS_YEAR - 2, TALKS_YEAR - 1, TALKS_YEAR]) >= FINALS_NEEDED
	var merge := true
	if regular:
		var rng := RandomNumberGenerator.new()
		rng.seed = hash("fitzroy-merger|%d" % int(gs.career_seed))
		merge = rng.randi_range(1, 100) <= MERGE_ANYWAY_PCT
	st["fitzroy"] = "merged" if merge else "stays"
	st["fitzroy_regular"] = regular
	if not merge:
		keep_fitzroy()
		gs.add_news("legacy", stays_line())
		return
	if str(gs.my_club) == MERGED and ClubArcs.on(gs):
		var arcs: Dictionary = ClubArcs._st(gs)
		if str((arcs.get("move", {}) as Dictionary).get("to", "")) == "":
			arcs["move"] = {"to": MERGED_INTO, "why": "merger"}


## After the season is closed: Fitzroy's best go to the Brisbane Lions, the
## rest to free agency, and no coach is left at a club that is gone.
static func merge_lists(gs) -> void:
	if not on():
		return
	canon_moves(gs, int(gs.season_year) + 1)
	_sweep_leftovers(gs)
	if str(_st(gs).get("fitzroy", "")) != "merged" or bool(_st(gs).get("merge_done", false)):
		return
	_merge(gs, false)


## Fitzroy's best LIONS_TAKE go to the Brisbane Lions. The rest go into this
## year's National Draft (`to_draft`, the 1996 order) or to free agency.
## Anyone retiring at the rollover ends his career here, as his list closes.
static func _merge(gs, to_draft: bool) -> void:
	var st := _st(gs)
	st["merge_done"] = true
	var fit: Array = gs.league_lists.get(MERGED, [])
	var ranked := fit.filter(func(q): return not gs.retiring_now(q))
	if to_draft:
		for p in fit:
			if gs.retiring_now(p):
				gs._career_over(p, "retired")
	else:
		ranked = fit.duplicate()
	ranked.sort_custom(func(a, b): return int(Rating.ovr(a, 0)) > int(Rating.ovr(b, 0)))
	var lions: Array = gs.league_lists.get(MERGED_INTO, [])
	var taken := []
	for i in range(ranked.size()):
		var p: Dictionary = ranked[i]
		if i < LIONS_TAKE:
			p["club"] = MERGED_INTO
			p["joined"] = TALKS_YEAR + 1
			# The merger screen says which side he came from (MergerCutScene).
			p["merged_from"] = MERGED
			lions.append(p)
			taken.append(GameDB.player_display_name(p))
		elif to_draft:
			p["club"] = ""
			p["draft_year"] = int(gs.season_year)
			p["fitzroy_left"] = true
			p["contract_years"] = 0
			p.erase("rookie_list")
			# A leftover drafted in an earlier season (R1990_245) is in
			# drafted_draftees from that draft: cleared, he can be drafted
			# again, and age_pool keeps him instead of dropping him as taken.
			gs.drafted_draftees.erase(str(p["id"]))
			gs.draftee_pool.append(p)
		else:
			p["released_by"] = MERGED
			p["contract_years"] = 0
			p.erase("rookie_list")
			gs.free_agents.append(p)
	fit.clear()
	# Off the league's lists altogether, or free agency would sign players to
	# a club that no longer exists; mid off-season, off the season's lists
	# too, which the league's are rebuilt from.
	gs.league_lists.erase(MERGED)
	if to_draft and gs.season != null:
		gs.season.lists.erase(MERGED)
	gs.unique_jumpers(lions)
	for cid in gs.coaches:
		var c: Dictionary = gs.coaches[cid]
		if str(c.get("status", "")) == "club" and str(c.get("club", "")) == MERGED:
			CoachMarket._leave_job(c, int(gs.season_year))
	var head := "Fitzroy and the Brisbane Bears have merged."
	if bool(st.get("fitzroy_regular", false)):
		head = "Fitzroy played finals often enough to stand alone, but the board took the merger anyway (the %d%% chance)." % MERGE_ANYWAY_PCT
	gs.add_news("legacy", "%s The Brisbane Lions play from %d and take Fitzroy's best %d players: %s. The rest of Fitzroy's list %s." % [
			head, TALKS_YEAR + 1, taken.size(), _and(taken),
			("go into the %d National Draft" % int(gs.season_year)) if to_draft
			else ("are free agents" if EraRules.on("free_agency") else "are delisted")])


## Fitzroy's leftovers nobody drafted: one young enough stays in the pool for
## next year's draft; one who would age out of it (22) ends his career here,
## on the record, never silently.
static func _sweep_leftovers(gs) -> void:
	var keep := []
	for p in gs.draftee_pool:
		if bool(p.get("fitzroy_left", false)) and not gs.drafted_draftees.has(str(p["id"])) \
				and float(p.get("age", 30.0)) + 1.0 >= 22.0 and not p.has("relisted"):
			# One who really played on waits for the Rookie Draft first.
			if career_ahead(p, int(gs.season_year)):
				p["relisted"] = int(gs.season_year)
			else:
				gs._career_over(p, "delisted")
				continue
		keep.append(p)
	gs.draftee_pool = keep


## Fitzroy fought the merger off: they play on, and the Bears stay the Bears.
static func keep_fitzroy(lions := false) -> void:
	GameDB.keep_club(MERGED)
	if lions:
		GameDB.unpin_era(MERGED_INTO)
	else:
		GameDB.pin_era(MERGED_INTO, TALKS_YEAR)
	separate_colours()


## The news when Fitzroy play on (after the coach moves; nothing moves).
static func stays_line() -> String:
	return "Fitzroy have fought off the merger and play on in %d, beside the Brisbane Bears." % (TALKS_YEAR + 1)


## A loaded career puts back what its rollovers changed in GameDB.
static func restore(gs) -> void:
	if on() and str(_st(gs).get("fitzroy", "")) == "stays":
		keep_fitzroy(str(_st(gs).get("brand", "")) == "lions")


# ---------------------------------------------------------------------------
# Fitzroy play on: the Bears' coach picks the name (director, 2026-11-13)
# ---------------------------------------------------------------------------
const BRAND_TID := "legacy_brand"


## "bears coaches should be given the choice to rebrand to lions or stay as
## bears" (director, 2026-11-13): in the first week after Fitzroy fight the
## merger off, a coach at the Bears gets one card. It is asked once; left
## unanswered, the club stays the Bears. A Bears side the sim runs stays the
## Bears. The name and look only: play never changes.
static func week(gs) -> void:
	canon_week(gs)
	if not on() or str(gs.my_club) != MERGED_INTO or gs.season == null:
		return
	var st := _st(gs)
	if str(st.get("fitzroy", "")) != "stays" or bool(st.get("brand_asked", false)):
		return
	st["brand_asked"] = true
	gs.week_events.append(brand_card())


## The card itself (also for tests and captures).
static func brand_card() -> Dictionary:
	return {"tid": BRAND_TID, "title": "Bears or Lions?",
		"text": "Fitzroy have fought off the merger, so the Bears stand alone in %d. The board leaves the club's name to you: become the Brisbane Lions, in maroon, blue and gold, or stay the Brisbane Bears, in maroon and gold. It changes the name, the guernsey and the colours, never how the side plays. You make this call once." % (TALKS_YEAR + 1),
		"options": [
			{"label": "Become the Lions", "effects": [], "result": "From %d the club is the Brisbane Lions." % (TALKS_YEAR + 1)},
			{"label": "Stay the Bears", "effects": [], "result": "The Bears it is: maroon and gold, as ever."}],
		"unanswered": {"hint": "Leave it and the club stays the Bears."},
		"facts": {}}


## The coach's answer to the card (GameState.resolve_card).
static func answered(gs, card: Dictionary, choice: int) -> void:
	canon_answered(gs, card, choice)
	if str(card.get("tid", "")) != BRAND_TID:
		return
	var lions := choice == 0
	_st(gs)["brand"] = "lions" if lions else "bears"
	keep_fitzroy(lions)
	if lions:
		gs.add_news("legacy", "The Brisbane Bears are now the Brisbane Lions, in maroon, blue and gold.")


# ---------------------------------------------------------------------------
# Fitzroy beside Brisbane: guernseys apart (director, 2026-11-13)
# ---------------------------------------------------------------------------
## The most a colour is reshaded, in value (0-1) each way.
const SHADE_MAX := 0.2
const SHADE_STEP := 0.02


## "if the lions/bears and fitzroy guernseys clash you can slightly change the
## colours of each (still same look, just slightly reshaded to emphasise
## differences)" (director, 2026-11-13). When both play and their guernseys
## clash by the match's own check (PitchView.DISC_CLASH on the two home
## kits), Fitzroy's colours go a shade darker and Brisbane's a shade brighter,
## step by step until they no longer clash, at most SHADE_MAX. Hue, design and
## which colour goes where never change.
static func separate_colours() -> void:
	GameDB.shade_colours(MERGED, {})
	GameDB.shade_colours(MERGED_INTO, {})
	if not GameDB.clubs.has(MERGED) or not GameDB.clubs.has(MERGED_INTO):
		return
	if kit_gap() >= PitchView.DISC_CLASH:
		return
	var fit := GameDB.club_colours(MERGED)
	var bri := GameDB.club_colours(MERGED_INTO)
	var step := SHADE_STEP
	while step <= SHADE_MAX + 0.0001:
		GameDB.shade_colours(MERGED, _shaded(fit, -step))
		GameDB.shade_colours(MERGED_INTO, _shaded(bri, step))
		if kit_gap() >= PitchView.DISC_CLASH:
			return
		step += SHADE_STEP


## How far apart the two home guernseys look on the ground.
static func kit_gap() -> float:
	return PitchView.disc_distance(PitchView.with_trim(MERGED, GameDB.club_guernsey(MERGED)),
			PitchView.with_trim(MERGED_INTO, GameDB.club_guernsey(MERGED_INTO)))


static func _shaded(cols: Array, by: float) -> Dictionary:
	var out := {}
	var keys := ["primary", "secondary", "accent"]
	for i in range(mini(cols.size(), keys.size())):
		var c: Color = cols[i]
		out[keys[i]] = Color.from_hsv(c.h, c.s, clampf(c.v + by, 0.0, 1.0), c.a)
	return out


static func _and(names: Array) -> String:
	if names.size() <= 1:
		return "".join(names)
	return "%s and %s" % [", ".join(names.slice(0, names.size() - 1)), names[-1]]


# ---------------------------------------------------------------------------
# Canon stories (director, 2026-11-13; the moves redesigned 2026-11-25)
# ---------------------------------------------------------------------------
## "historical trades arent in the sim. make the gold coast and lance franklin
## trades canon events that CAN be stopped"; who stops it: "His coach, with
## odds"; then "make Scully another", Dangerfield, Brodie Grundy, Zach Merrett,
## Chris Judd, Lachie Neale and Joe Daniher; and "storylines around Liam Jurrah
## and Cyril Rioli where they will either make an early retirement or be
## convinced to play on"; "just have a story no matter where he is".
##
## The moves (director, 2026-11-25): "historical trades are never meant to
## occur NECESSARILY to the same club as happened IRL, only coincidentally
## maybe, the event is simply "Dangerfield is requesting a trade to Victoria"
## and then theres options for us to either try to keep him, or get max
## value". Each fires from wherever the sim has him, in round CANON_ROUND of
## the season before `year`, as one of three stories ("The real story"):
##  - "trade": he requests a trade to the kind of club `asks` names ("The kind
##    of club"). Out of contract, his deal runs one more season so he can be
##    traded. Kept (KEEP_PCT), he stays on the keep deal. Not kept, half the
##    time he insists on his real club, which alone bids, a fair offer we must
##    take ("Half the time", "A fair offer"); otherwise every club that meets
##    his ask bids and we pick ("Pick from offers"). None taken by the close
##    of trades, the best goes through; no club able to bid, he stays ("Best
##    offer goes through").
##  - "free_agent": he tests free agency; his contract ends that season. Kept,
##    he stays on the keep deal; otherwise he signs with the best bidder and
##    his club gets the compensation pick ("Keep or compensation").
##  - "new_club": he weighs an offer to join the new club next season; his
##    contract ends that season. Kept, he stays; otherwise he joins it and his
##    club gets the compensation the new clubs pay.
## Already where his story would take him, nothing happens ("No story"). At a
## rival club the same dice decide, and the bids go to the club that values
## him most and fits his pay ("Same dice, best bid").
## Kind "retire": he retires at that rollover unless talked round (KEEP_PCT).
const CANON := [
	{"id": "ablett_gcs", "kind": "move", "story": "new_club", "first": "Gary", "last": "Ablett", "dob": "1984-05-14", "to": "GCS", "year": 2011},
	{"id": "scully_gws", "kind": "move", "story": "new_club", "first": "Tom", "last": "Scully", "dob": "1991-05-15", "to": "GWS", "year": 2012},
	{"id": "judd_car", "kind": "move", "story": "trade", "asks": "state", "first": "Chris", "last": "Judd", "dob": "1983-09-08", "to": "CAR", "year": 2008},
	{"id": "franklin_syd", "kind": "move", "story": "free_agent", "first": "Lance", "last": "Franklin", "dob": "1987-01-30", "to": "SYD", "year": 2014},
	{"id": "dangerfield_gee", "kind": "move", "story": "trade", "asks": "state", "first": "Patrick", "last": "Dangerfield", "dob": "1990-04-05", "to": "GEE", "year": 2016},
	{"id": "neale_brl", "kind": "move", "story": "trade", "asks": "state", "first": "Lachie", "last": "Neale", "dob": "1993-05-24", "to": "BRL", "year": 2019},
	{"id": "daniher_brl", "kind": "move", "story": "free_agent", "first": "Joe", "last": "Daniher", "dob": "1994-03-04", "to": "BRL", "year": 2021},
	{"id": "grundy_mel", "kind": "move", "story": "trade", "asks": "first_ruck", "first": "Brodie", "last": "Grundy", "dob": "1994-04-15", "to": "MEL", "year": 2023},
	{"id": "grundy_syd", "kind": "move", "story": "trade", "asks": "first_ruck", "first": "Brodie", "last": "Grundy", "dob": "1994-04-15", "to": "SYD", "year": 2024},
	{"id": "merrett_flag", "kind": "move", "story": "trade", "asks": "flag", "first": "Zach", "last": "Merrett", "dob": "1995-10-03", "to": "", "year": 2026},
	{"id": "jurrah_home", "kind": "retire", "first": "Liam", "last": "Jurrah", "dob": "1988-09-22", "year": 2014,
		"pitch": "walking away from the game to go home to the Territory"},
	{"id": "rioli_home", "kind": "retire", "first": "Cyril", "last": "Rioli", "dob": "1989-07-14", "year": 2019,
		"pitch": "retiring early to go home to Darwin, to family"},
]
const CANON_ROUND := 18
const CANON_TID := "legacy_canon"
## Try to keep him: the chance he stays, and what a move's keeping deal costs.
const KEEP_PCT := 50
const KEEP_RAISE_PCT := 50
const KEEP_YEARS := 4
## Keeping a trade story fails: the chance he insists on his real club
## ("Half the time").
const INSIST_PCT := 50
## A state as a request names it: [the place, its clubs].
const STATE_WORDS := {
	"VIC": ["Victoria", "Victorian"], "QLD": ["Queensland", "Queensland"],
	"SA": ["South Australia", "South Australian"], "WA": ["Western Australia", "West Australian"],
	"NSW": ["New South Wales", "New South Wales"], "TAS": ["Tasmania", "Tasmanian"]}


static func canon(id: String) -> Dictionary:
	for m in CANON:
		if str(m["id"]) == id:
			return m
	return {}


static func _canon_st(gs) -> Dictionary:
	var st := _st(gs)
	if not st.has("canon"):
		st["canon"] = {}
	return st["canon"]


## Where the sim has him now: {"p", "club"}, or {} when he is on no list.
static func canon_find(gs, m: Dictionary) -> Dictionary:
	for c in gs.league_lists:
		for p in gs.league_lists[c]:
			if _is_him(m, p):
				return {"p": p, "club": str(c)}
	return {}


static func _is_him(m: Dictionary, p: Dictionary) -> bool:
	if str(p.get("real_name", "")) != "%s %s" % [str(m["first"]), str(m["last"])]:
		return false
	return str(p.get("dob", "")) == "" or str(p.get("dob", "")) == str(m["dob"])


## The bigger deal that keeps a player another club wants: his asking price
## plus KEEP_RAISE_PCT, a season.
static func keep_salary(p: Dictionary) -> int:
	return ceili(Contracts.asking_salary(p) * (100 + KEEP_RAISE_PCT) / 100.0)


## Can `club` pay him the keep deal and still hold the room to fill its list
## (GameState._keep_cap, "Hold room")?
static func keep_fits(gs, club: String, p: Dictionary) -> bool:
	if gs.season == null or not gs.season.lists.has(club):
		return false
	var list: Array = gs.season.lists[club]
	var rest := list.filter(func(q): return q != p)
	return keep_salary(p) + Contracts.payroll(rest) <= int(gs._keep_cap(club, list))


static func _keep_deal(p: Dictionary) -> void:
	p["salary"] = keep_salary(p)
	p["contract_years"] = KEEP_YEARS


## A seeded draw, 1-100: the career's, so a reload cannot change it.
static func _roll(gs, tag: String, id: String) -> int:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("%s|%s|%d" % [tag, id, int(gs.career_seed)])
	return rng.randi_range(1, 100)


## The club tries to keep him: KEEP_PCT he stays. A trade story that fails
## rolls again: INSIST_PCT he insists on his real club.
static func _keep_rolls(gs, m: Dictionary, e: Dictionary) -> void:
	var id := str(m["id"])
	e["fight"] = true
	e["roll"] = _roll(gs, "canon", id)
	e["kept"] = int(e["roll"]) <= KEEP_PCT
	e["insist"] = false
	if not bool(e["kept"]) and str(m.get("story", "")) == "trade":
		e["insist_roll"] = _roll(gs, "canon_insist", id)
		e["insist"] = int(e["insist_roll"]) <= INSIST_PCT


# --- What he asks for ---------------------------------------------------------
static func _asked_state(m: Dictionary) -> String:
	return str(TradeRequests.CLUB_STATES.get(str(m["to"]), ""))


## Would `list` make him its first ruck: no other ruckman there as good?
static func _first_ruck(p: Dictionary, list: Array) -> bool:
	for q in list:
		if q == p or str(q.get("id", "")) == str(p.get("id", "")):
			continue
		if (str(q.get("role", "")) == "RUCK" or str(q.get("role2", "")) == "RUCK") \
				and Rating.ovr(q, 0) >= Rating.ovr(p, 0):
			return false
	return true


## Does `club` give him what his trade request asks for?
static func _meets(gs, m: Dictionary, p: Dictionary, club: String) -> bool:
	match str(m.get("asks", "")):
		"state":
			return str(gs._club_states().get(club, "")) == _asked_state(m)
		"first_ruck":
			return gs.season != null and gs.season.lists.has(club) and _first_ruck(p, gs.season.lists[club])
		"flag":
			return gs.club_phase(club) == "contending"
	return false


## He already has what his story asks for ("No story").
static func _has_it(gs, m: Dictionary, p: Dictionary, from: String) -> bool:
	if str(m.get("story", "")) == "trade":
		return _meets(gs, m, p, from)
	return from == str(m.get("to", ""))


## The clubs this season that meet his request, his own aside.
static func canon_clubs(gs, m: Dictionary, p: Dictionary, from: String) -> Array:
	var out := []
	if gs.season == null:
		return out
	for c in gs.season.lists:
		if str(c) != from and _meets(gs, m, p, str(c)):
			out.append(str(c))
	out.sort()
	return out


## His real club, when it plays this season and is not his own.
static func _insist_club(gs, m: Dictionary, from: String) -> String:
	var to := str(m.get("to", ""))
	if to == "" or to == from or gs.season == null or not gs.season.lists.has(to):
		return ""
	return to


static func _ask_words(m: Dictionary) -> String:
	match str(m.get("asks", "")):
		"state":
			return "a trade to %s" % str(STATE_WORDS.get(_asked_state(m), ["home", ""])[0])
		"first_ruck":
			return "a trade to a club that will make him its first ruck"
		"flag":
			return "a trade to a side chasing the flag"
	return "a trade"


static func _clubs_words(m: Dictionary) -> String:
	match str(m.get("asks", "")):
		"state":
			return "the %s clubs" % str(STATE_WORDS.get(_asked_state(m), ["", "other"])[1])
		"first_ruck":
			return "the clubs that would make him first ruck"
		"flag":
			return "the sides chasing the flag"
	return "the other clubs"


static func _cap(s: String) -> String:
	return s.substr(0, 1).to_upper() + s.substr(1)


# --- The season before: the story breaks ---------------------------------------
## This week: each story that is due fires once. A retirement is set now (the
## season's close retires him); a move sets his contract as the story has it.
## You get the card if you coach his club.
static func canon_week(gs) -> void:
	if not on() or gs.season == null:
		return
	var cst := _canon_st(gs)
	for m in CANON:
		if int(gs.season_year) != int(m["year"]) - 1 or int(gs.season.round_index) < CANON_ROUND:
			continue
		if cst.has(m["id"]):
			continue
		var at := canon_find(gs, m)
		if at.is_empty():
			# He is on no list (retired, delisted): nobody is asked, so no news
			# of him follows at the rollover.
			cst[m["id"]] = {"missing": true}
			continue
		var e := {"asked": true}
		cst[m["id"]] = e
		var p: Dictionary = at["p"]
		var from := str(at["club"])
		if str(m["kind"]) == "retire":
			p["retiring"] = int(m["year"])
			p["retire_talk"] = {"year": int(m["year"]), "stays": false, "reason": "He wants to go home."}
		elif not _canon_start(gs, m, e, p, from):
			continue
		if from == str(gs.my_club) and not gs.is_sacked():
			e["card"] = true
			gs.week_events.append(canon_card(gs, m, p, from))
		elif str(m["kind"]) == "move":
			gs.add_news("legacy", break_line(gs, m, p, from))


## A move's story starts: false when he already has what it asks for.
static func _canon_start(gs, m: Dictionary, e: Dictionary, p: Dictionary, from: String) -> bool:
	if _has_it(gs, m, p, from):
		e["none"] = true
		return false
	e["live"] = true
	e["from"] = from
	if str(m["story"]) == "trade":
		p["contract_years"] = maxi(2, int(p.get("contract_years", 1)))
	else:
		p["contract_years"] = 1
	return true


## The news at a rival club: "Patrick Dangerfield (Adelaide) is requesting a
## trade to Victoria."
static func break_line(_gs, m: Dictionary, p: Dictionary, from: String) -> String:
	var who := "%s (%s)" % [GameDB.player_display_name(p), GameDB.club_name(from)]
	match str(m["story"]):
		"free_agent":
			return "%s is testing free agency at season's end." % who
		"new_club":
			return "%s is weighing an offer to join %s next season." % [who, GameDB.club_name(str(m["to"]))]
	return "%s is requesting %s." % [who, _ask_words(m)]


## The card (also for tests and captures). Each option carries a "key": "keep"
## or "go". The keep option is there only when the club can pay the keep deal.
static func canon_card(gs, m: Dictionary, p: Dictionary, from: String) -> Dictionary:
	var who := GameDB.player_display_name(p)
	var y := int(m["year"])
	if str(m["kind"]) == "retire":
		return {"tid": CANON_TID, "canon": str(m["id"]), "title": "%s thinks of going home" % who,
			"text": "%s is thinking about %s at the end of the season. The club can try to talk %s into playing on in %d." % [who, str(m["pitch"]), who, y],
			"options": [
				{"key": "keep", "label": "Ask for one more season", "effects": [],
					"rule": "%d%% %s plays on in %d. %d%% %s retires anyway." % [KEEP_PCT, who, y, 100 - KEEP_PCT, who],
					"result": "The club has made its case. %s answers at season's end." % who},
				{"key": "go", "label": "Back the call to go home", "effects": [],
					"rule": "%s retires at season's end." % who,
					"result": "The club backs the call. %s retires at season's end." % who}],
			"unanswered": {"hint": "Leave it and %s retires." % who},
			"facts": {}}
	var stays := "%d%% %s stays, on %d more seasons at %s a season (asking %s)." % [
			KEEP_PCT, who, KEEP_YEARS, Contracts.money(keep_salary(p)), Contracts.money(Contracts.asking_salary(p))]
	var room := keep_fits(gs, from, p)
	var no_room := "" if room else " We don't have the cap room to keep him on %s a season." % Contracts.money(keep_salary(p))
	var title := ""
	var text := ""
	var lose := ""
	var go := {}
	var hint := ""
	match str(m["story"]):
		"trade":
			var clubs := _clubs_words(m)
			var real := _insist_club(gs, m, from)
			title = "%s requests a trade" % who
			text = "%s is requesting %s for next season. The club can try to keep him, or take the best of the offers %s make when trades open. If we take none by the close of trades, the best goes through; if no club can make one, he stays." % [
					who, _ask_words(m), clubs]
			if real != "":
				var half := int((100 - KEEP_PCT) * INSIST_PCT / 100.0)
				lose = "%d%% he insists on %s, and we must take their offer. %d%% %s make offers and we pick one." % [
						half, GameDB.club_name(real), 100 - KEEP_PCT - half, clubs]
			else:
				lose = "%d%% %s make offers and we pick one." % [100 - KEEP_PCT, clubs]
			go = {"key": "go", "label": "Get the most for %s" % who, "effects": [],
					"rule": "%s make offers when trades open, and we pick one." % _cap(clubs),
					"result": "The club will hear offers for %s when trades open." % who}
			hint = "Leave it and the club hears offers for %s when trades open." % who
		"free_agent":
			var comp := str(gs.projected_compensation(p).get("reason", ""))
			title = "%s tests free agency" % who
			text = "%s is testing free agency. His contract ends this season, and every club can bid for him." % who
			lose = "%d%% he leaves as a free agent at season's end. %s" % [100 - KEEP_PCT, comp]
			go = {"key": "go", "label": "Let %s go" % who, "effects": [],
					"rule": "%s leaves as a free agent at season's end and signs with the club that offers most. %s" % [who, comp],
					"result": "The club wishes %s well. He leaves as a free agent at season's end." % who}
			hint = "Leave it and %s leaves as a free agent." % who
		_:
			var to := GameDB.club_name(str(m["to"]))
			var comp := str(ExpansionBuild.compensation(gs, p)["line"])
			title = "%s weighs a new club's offer" % who
			text = "%s is weighing an offer to join a new club next season: %s, in their first season, %d. His contract ends this season." % [who, to, y]
			lose = "%d%% he joins %s for %d. %s" % [100 - KEEP_PCT, to, y, comp]
			go = {"key": "go", "label": "Let %s go" % who, "effects": [],
					"rule": "%s joins %s for %d. %s" % [who, to, y, comp],
					"result": "The club wishes %s well at %s from %d." % [who, to, y]}
			hint = "Leave it and %s joins %s." % [who, to]
	var options := []
	if room:
		options.append({"key": "keep", "label": "Try to keep %s" % who, "effects": [],
				"rule": "%s %s" % [stays, lose],
				"result": "The club has made its offer. %s answers at season's end." % who})
	options.append(go)
	return {"tid": CANON_TID, "canon": str(m["id"]), "title": title, "text": text + no_room,
		"options": options, "unanswered": {"hint": hint}, "facts": {}}


## Your answer to the card (GameState.resolve_card, through answered()).
static func canon_answered(gs, card: Dictionary, choice: int) -> void:
	if str(card.get("tid", "")) != CANON_TID:
		return
	var id := str(card.get("canon", ""))
	var m := canon(id)
	var cst := _canon_st(gs)
	var e: Dictionary = cst.get(id, {"asked": true})
	cst[id] = e
	var opts: Array = card.get("options", [])
	# A card saved before the options had keys: the first was to keep him.
	var key := "keep" if choice == 0 else "go"
	if choice >= 0 and choice < opts.size() and (opts[choice] as Dictionary).has("key"):
		key = str(opts[choice]["key"])
	e["fight"] = key == "keep"
	if key != "keep" or m.is_empty():
		return
	_keep_rolls(gs, m, e)
	if not bool(e["kept"]):
		return
	var at := canon_find(gs, m)
	if at.is_empty():
		return
	var p: Dictionary = at["p"]
	if str(m["kind"]) == "retire":
		p["play_on"] = int(m["year"])
		p["retire_talk"] = {"year": int(m["year"]), "stays": true, "reason": "The club talked him into another season."}
	else:
		_keep_deal(p)


# --- The off-season: the story plays out ----------------------------------------
## The off-season opens (GameState.open_offseason, before the new clubs settle
## and anyone re-signs): each live move goes its way. Kept, he stays. A free
## agent goes to free agency; a new club's man is set to join it; a trade
## story waits for the trade period (canon_requests).
static func canon_offseason(gs) -> void:
	if not on() or gs.season == null:
		return
	var cst := _canon_st(gs)
	for m in CANON:
		if str(m["kind"]) != "move" or int(m["year"]) != int(gs.season_year) + 1:
			continue
		var e: Dictionary = cst.get(m["id"], {})
		if e.has("step") or e.has("none"):
			continue
		var at := canon_find(gs, m)
		if at.is_empty() or gs.retiring_now(at["p"]):
			continue
		var p: Dictionary = at["p"]
		var from := str(at["club"])
		if not gs.season.lists.has(from):
			continue
		cst[m["id"]] = e
		if not e.has("live"):
			# Saved before the story broke this way: it breaks now. One the
			# club already kept (the old card's keep deal) keeps his deal.
			e["asked"] = true
			if bool(e.get("kept", false)):
				e["live"] = true
			elif not _canon_start(gs, m, e, p, from):
				continue
		e["from"] = from
		var mine := from == str(gs.my_club) and bool(e.get("card", false))
		if not mine and not e.has("fight"):
			_keep_rolls(gs, m, e)
			if bool(e["kept"]) and not keep_fits(gs, from, p):
				# No room for the keep deal: as a club that hears offers.
				e["kept"] = false
				e["insist"] = false
				e["no_room"] = true
			elif bool(e["kept"]):
				_keep_deal(p)
		var who := GameDB.player_display_name(p)
		if bool(e.get("kept", false)):
			e["step"] = "kept"
			gs.add_news("legacy", "%s stays at %s, on %d more seasons at %s a season." % [
					who, GameDB.club_name(from), KEEP_YEARS, Contracts.money(int(p.get("salary", 0)))])
			continue
		match str(m["story"]):
			"free_agent":
				e["step"] = "free_agent"
				p["story_left"] = int(gs.season_year)
				gs._release(from, p, true, false)
				if from == str(gs.my_club):
					HonourBoard.leave(gs, p, "free_agent")
				gs.add_news("legacy", "%s leaves %s to test free agency." % [who, GameDB.club_name(from)])
			"new_club":
				var to := str(m["to"])
				if not ExpansionBuild.building(gs).has(to):
					e["step"] = "stayed"
					continue
				e["step"] = "joining"
				var st := ExpansionBuild.state(gs, to)
				(st["targets"] as Array).insert(0, {"id": str(p["id"]), "club": from, "year": int(gs.season_year),
						"name": who, "status": "joining", "canon": true})
			_:
				e["step"] = "request"


## The trade period opens (GameState.open_offseason, after the year's own
## requests): each trade story becomes a request. Insisting, he names his real
## club alone; otherwise every club that meets his ask.
static func canon_requests(gs) -> void:
	if not on() or gs.season == null:
		return
	var cst := _canon_st(gs)
	for m in CANON:
		var e: Dictionary = cst.get(m["id"], {})
		if str(e.get("step", "")) != "request" or int(m["year"]) != int(gs.season_year) + 1:
			continue
		var at := canon_find(gs, m)
		if at.is_empty():
			continue
		var p: Dictionary = at["p"]
		var from := str(at["club"])
		var real := _insist_club(gs, m, from) if bool(e.get("insist", false)) else ""
		var to: Array = [real] if real != "" else canon_clubs(gs, m, p, from)
		e["step"] = "requested"
		if to.is_empty():
			gs.add_news("legacy", "%s stays at %s: no club meets his request." % [
					GameDB.player_display_name(p), GameDB.club_name(from)])
			continue
		var ask := {"club": from, "to": to, "why": "story", "canon": str(m["id"]), "insist": real != ""}
		gs.trade_requests[str(p["id"])] = ask
		gs.add_news("trade", request_line(gs, p, ask))


## A story request in a line (GameState._request_line).
static func request_line(gs, p: Dictionary, ask: Dictionary) -> String:
	var who := "%s (%s)" % [GameDB.player_display_name(p), GameDB.club_name(str(ask["club"]))]
	var names: Array = (ask["to"] as Array).map(func(c): return GameDB.club_name(str(c)))
	var to := str(names[-1]) if names.size() < 2 else ", ".join(names.slice(0, -1)) + " or " + str(names[-1])
	if bool(ask.get("insist", false)):
		return "%s insists on a trade to %s." % [who, to]
	var line := "%s is requesting %s: %s." % [who, _ask_words(canon(str(ask.get("canon", "")))), to]
	if str(ask["club"]) == str(gs.my_club):
		line += " If we take none of the offers by the close of trades, the best goes through."
	return line


## A story request no club met: he stays.
static func story_stays_line(p: Dictionary, from: String) -> String:
	return "%s stays at %s: no club could make an offer." % [GameDB.player_display_name(p), GameDB.club_name(from)]


## A new club leaves him alone: his story takes him there or keeps him home
## (ExpansionBuild._candidate).
static func canon_reserved(gs, p: Dictionary) -> bool:
	if not on():
		return false
	for m in CANON:
		if str(m["kind"]) != "move" or int(m["year"]) != int(gs.season_year) + 1 or not _is_him(m, p):
			continue
		return not (_canon_st(gs).get(m["id"], {}) as Dictionary).has("none")
	return false


## At the rollover into `year`: the news of each retirement story. The moves
## have played out in the off-season (canon_offseason).
static func canon_moves(gs, year: int) -> void:
	var cst := _canon_st(gs)
	for m in CANON:
		if int(m["year"]) != year or str(m["kind"]) != "retire":
			continue
		var e: Dictionary = cst.get(m["id"], {})
		if e.has("done"):
			continue
		e["done"] = true
		cst[m["id"]] = e
		var who := "%s %s" % [str(m["first"]), str(m["last"])]
		if e.has("asked") and not bool(e.get("kept", false)):
			gs.add_news("legacy", "%s has retired, %s." % [who, str(m["pitch"]).replace("retiring early", "early").replace("walking away from the game", "walking away")])
		elif bool(e.get("kept", false)):
			gs.add_news("legacy", "%s has been talked into playing on in %d." % [who, year])
