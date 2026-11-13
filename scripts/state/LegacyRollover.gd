class_name LegacyRollover
extends RefCounted
## A Legacy career's rollovers, 1990 to 2026 (TODO row 142, phase L8): each
## year's real draft class, each new club on its real first list, and the
## Fitzroy merger. The sim makes the picks, the later careers and the
## retirements: an alternative history from real starting points (director
## 2026-11-10). A career on today's data never reaches any of this.
##
## Data: data/legacy/classes.csv and entry_lists.csv, built by
## tools/legacy_1990s/build_rollovers.py.

const CLASSES_CSV := "res://data/legacy/classes.csv"
const ENTRY_CSV := "res://data/legacy/entry_lists.csv"

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


## The real class drafted at the end of `year`, if this career has one.
static func has_class(year: int) -> bool:
	if not on():
		return false
	_load()
	return _classes.has(year)


## Whether `code` enters in `year` on its real list.
static func has_entry(code: String, year: int) -> bool:
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
		Prospects.project(p)
		out.append(p)
	GameDB.assign_aliases(out)
	return out


# ---------------------------------------------------------------------------
# A new club's real list
# ---------------------------------------------------------------------------
## `code`'s real list for its first season, `year`, after the league has aged
## into it. A player the career already has (a real player on the 1990 lists
## or in an earlier class) moves to the new club from wherever the sim has
## him, as he really did; one the sim has retired stays retired. Everyone else
## (a real prospect no club in the sim drafted among them) is new to the career: rated on his last AFL season before `year`, fitted to
## his rating on that season's own scale, or as a prospect if he has none.
## Returns {"list", "moved": [[player, from]], "missing": [names the sim retired]}.
static func entry_list(gs, code: String, year: int) -> Dictionary:
	_load()
	var list := []
	var moved := []
	var missing := []
	var established := []
	var n := 0
	for r in _entries.get("%s|%d" % [code, year], []):
		n += 1
		if str(r.get("known", "")) == "1":
			var found := _take_known(gs, r)
			if found.is_empty() and _retired(gs, r):
				missing.append("%s %s" % [str(r.get("first", "")), str(r.get("last", ""))])
				continue
			if found.is_empty():
				# The career never had him, or lost him undrafted from a pool:
				# he comes as a new player, as an unknown one does.
				list.append(_new_player(code, year, n, r))
				continue
			var p: Dictionary = found["p"]
			if str(found["from"]) != "":
				moved.append([p, str(found["from"])])
			_join(p, code, r)
			list.append(p)
			continue
		var p := _new_player(code, year, n, r)
		if str(r.get("src", "")) != "":
			established.append([p, r])
		list.append(p)
	if not established.is_empty():
		var rows := []
		for e in established:
			rows.append(e[0])
		Ratings.derive_all(rows, GameDB.players)
		for e in established:
			var p: Dictionary = e[0]
			var r: Dictionary = e[1]
			var role := str(r.get("role", ""))
			if role in ["RUCK", "MID", "DEF", "FWD"] and role != str(p["role"]):
				p["role"] = role
				p["role2"] = Ratings.assign_secondary(p)
			# His rating that season on that season's own scale (as the 1990
			# lists are rated on 1989's), not on the career's first season's.
			var ovr := str(r.get("ovr", ""))
			if ovr != "":
				p["attr"] = Prospects.fit_attributes(p["attr"], str(p["role"]), float(ovr.to_int()), float(p["gm"]))
			p["overall"] = Ratings.rate_overall(p["attr"], str(p["role"]), float(p["gm"]))
			p["value"] = Ratings.salary_value(int(p["overall"]))
			p["career"] = Career.from_source("?")
			p["data_club"] = code
			Potential.assign(p)
	var fresh := list.filter(func(q): return str(q.get("id", "")).begins_with("E%d_" % year))
	GameDB.assign_aliases(fresh)
	GameDB.register_draftees(fresh)
	gs.unique_jumpers(list)
	return {"list": list, "moved": moved, "missing": missing}


## A known real player, taken from wherever the sim has him: {"p", "from"}
## ("from" is the club he leaves, "" from free agency or the draft pool), or
## {} when the sim has retired him.
static func _take_known(gs, r: Dictionary) -> Dictionary:
	var name := "%s %s" % [str(r.get("first", "")), str(r.get("last", ""))]
	var dob := str(r.get("dob", ""))
	var same := func(p: Dictionary) -> bool:
		if str(p.get("real_name", "")) != name:
			return false
		return dob == "" or str(p.get("dob", "")) == "" or str(p.get("dob", "")) == dob
	for c in gs.league_lists:
		var arr: Array = gs.league_lists[c]
		for i in range(arr.size()):
			if same.call(arr[i]):
				var p: Dictionary = arr[i]
				arr.remove_at(i)
				return {"p": p, "from": str(c)}
	for i in range(gs.free_agents.size()):
		if same.call(gs.free_agents[i]):
			var p: Dictionary = gs.free_agents[i]
			gs.free_agents.remove_at(i)
			return {"p": p, "from": ""}
	for i in range(gs.draftee_pool.size()):
		if same.call(gs.draftee_pool[i]):
			var p: Dictionary = gs.draftee_pool[i]
			gs.draftee_pool.remove_at(i)
			return {"p": p, "from": ""}
	return {}


## Whether the sim has retired (or delisted for good) the real player of `r`.
static func _retired(gs, r: Dictionary) -> bool:
	var name := "%s %s" % [str(r.get("first", "")), str(r.get("last", ""))]
	for id in gs.departed_names:
		if str((gs.departed_names[id] as Dictionary).get("real_name", "")) == name:
			return true
	return false


## A known player joins the new club on a fresh deal (ensure_contracts).
static func _join(p: Dictionary, code: String, r: Dictionary) -> void:
	p["club"] = code
	p["num"] = int(str(r.get("num", "0")).to_int())
	for k in ["contract_years", "talks", "rookie_list", "released_by", "comp_eligible", "joined"]:
		p.erase(k)
	p["joined"] = int(GameDB.enter_year(code))


## A player new to the career, as GameDB builds a list addition.
static func _new_player(code: String, year: int, n: int, r: Dictionary) -> Dictionary:
	var p := {}
	p["first"] = str(r.get("first", ""))
	p["last"] = str(r.get("last", ""))
	p["real_name"] = "%s %s" % [p["first"], p["last"]]
	p["generic_name"] = ""
	p["name"] = ""
	p["id"] = "E%d_%s_%03d" % [year, code, n]
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
	p["height_source"] = "club list"
	var list_type := str(r.get("list", ""))
	p["list_type"] = list_type
	if list_type == "rookie":
		p["rookie_list"] = true
	if str(r.get("peak", "")) != "":
		p["real_peak"] = int(str(r["peak"]))
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
		for k in GameDB.STAT_KEYS:
			if r.has(k) and str(r[k]) != "":
				p[k] = float(str(r[k]))
		p["stats_year"] = int(src)
		p["draft_rank"] = 0
		p["data_src"] = "listed %d, rated on his %s season" % [year, src]
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
	return p


## The news line for a club entering on its real list.
static func entry_line(gs, code: String, year: int, got: Dictionary) -> String:
	var list: Array = got["list"]
	var line := "%s (the %s) join the competition for %d, their first season, on their real list of %d players." % [
			GameDB.club_name(code), GameDB.club_short(code), year, list.size()]
	var yours := []
	var others := 0
	for m in got["moved"]:
		if str(m[1]) == str(gs.my_club):
			yours.append(GameDB.player_display_name(m[0]))
		else:
			others += 1
	if not yours.is_empty():
		line += " From your list they take %s, as they really did." % _and(yours)
	if others > 0:
		line += " %d %s join them from other clubs." % [others, "player" if others == 1 else "players"]
	return line


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
	if not on() or str(_st(gs).get("fitzroy", "")) != "merged" or bool(_st(gs).get("merge_done", false)):
		return
	var st := _st(gs)
	st["merge_done"] = true
	var fit: Array = gs.league_lists.get(MERGED, [])
	var ranked := fit.duplicate()
	ranked.sort_custom(func(a, b): return int(a.get("overall", 0)) > int(b.get("overall", 0)))
	var lions: Array = gs.league_lists.get(MERGED_INTO, [])
	var taken := []
	for i in range(ranked.size()):
		var p: Dictionary = ranked[i]
		if i < LIONS_TAKE:
			p["club"] = MERGED_INTO
			p["joined"] = TALKS_YEAR + 1
			lions.append(p)
			taken.append(GameDB.player_display_name(p))
		else:
			p["released_by"] = MERGED
			p["contract_years"] = 0
			p.erase("rookie_list")
			gs.free_agents.append(p)
	fit.clear()
	# Off the league's lists altogether, or free agency would sign players to
	# a club that no longer exists.
	gs.league_lists.erase(MERGED)
	gs.unique_jumpers(lions)
	for cid in gs.coaches:
		var c: Dictionary = gs.coaches[cid]
		if str(c.get("status", "")) == "club" and str(c.get("club", "")) == MERGED:
			CoachMarket._leave_job(c, int(gs.season_year))
	var head := "Fitzroy and the Brisbane Bears have merged."
	if bool(st.get("fitzroy_regular", false)):
		head = "Fitzroy played finals often enough to stand alone, but the board took the merger anyway (the %d%% chance)." % MERGE_ANYWAY_PCT
	gs.add_news("legacy", "%s The Brisbane Lions play from %d and take Fitzroy's best %d players: %s. The rest of Fitzroy's list are free agents." % [
			head, TALKS_YEAR + 1, taken.size(), _and(taken)])


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
