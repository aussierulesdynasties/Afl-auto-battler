class_name YearEvents
extends RefCounted
## The league's real year events, 1990 to 2026 (Legacy L10, TODO row 142):
## each fires in its own season of a career, whatever year the career began,
## as a front-page story; the clubs it names get a card where it is a coach's
## call; and a controversy's real penalty lands (a fine, lost draft picks, a
## finals ban, a trade ban) when the career has Controversies on (director:
## "real penalties land", behind a switch at game creation, club level only).
##
## The data is data/legacy/year_events.json, ported from
## docs/research/era_dramas/dramas.csv (its rows say which). An event fires in
## the first week of its season at or past its round; one with a round past the
## home-and-away season fires once that season is done, before the finals.
## Personal conduct names the club only, never a person.

const PATH := "res://data/legacy/year_events.json"
## A draft pick the league took away: no club holds it, and the draft skips it.
const FORFEIT := Draft.FORFEIT
## A fine's bite on next season's football budget is the fine's share of that
## year's salary cap, taken from the board's annual budget (ClubBudget.ANNUAL_M),
## within these bounds ($m).
const CUT_MIN_M := 0.1
const CUT_MAX_M := 3.0
const ERA_RULES := "res://data/legacy/era_rules.csv"
const NEWS_WEIGHT := 70

static var _cache: Array = []
static var _caps: Dictionary = {}


static func all() -> Array:
	if _cache.is_empty():
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(PATH)) if FileAccess.file_exists(PATH) else null
		if parsed is Array:
			for e in parsed:
				if e is Dictionary:
					_cache.append(e)
	return _cache


## Every card the events carry, as story-card templates (StoryDeck.validate checks them).
static func cards() -> Array:
	var out := []
	for e in all():
		if (e as Dictionary).has("card"):
			out.append(StoryDeck.normalise(e["card"]))
	return out


static func state(gs) -> Dictionary:
	if not (gs.year_events is Dictionary):
		gs.year_events = {}
	for k in ["done"]:
		if not gs.year_events.has(k):
			gs.year_events[k] = []
	for k in ["trade_bans", "finals_bans", "budget_cuts"]:
		if not gs.year_events.has(k):
			gs.year_events[k] = {}
	return gs.year_events


## The clubs an event names that play this season ("all": every club).
static func involved(e: Dictionary, year: int) -> Array:
	var active: Array = GameDB.active_clubs(year)
	var clubs = e.get("clubs", [])
	if str(clubs) == "all":
		return active.duplicate()
	var out := []
	for c in clubs:
		if active.has(str(c)):
			out.append(str(c))
	return out


static func is_due(gs, e: Dictionary) -> bool:
	if int(e.get("season", 0)) != int(gs.season_year):
		return false
	if bool(e.get("controversy", false)) and not bool(gs.controversies):
		return false
	if (state(gs)["done"] as Array).has(str(e["id"])):
		return false
	if str(e.get("clubs", "")) != "all" and involved(e, int(gs.season_year)).is_empty():
		return false
	return gs.season.is_regular_done() or int(gs.season.round_index) >= int(e.get("round", 0))


## This week: fire every event that is due. Returns the cards for your club.
## Penalties land whether or not you get the card (a sacked coach, stories off).
static func week(gs) -> Array:
	var cards := []
	if gs.season == null:
		return cards
	for e in all():
		if not is_due(gs, e):
			continue
		var c := fire(gs, e)
		if not c.is_empty():
			cards.append(c)
	return cards


## Fire one event: the news, its penalties, and your card if your club is in it.
static func fire(gs, e: Dictionary) -> Dictionary:
	(state(gs)["done"] as Array).append(str(e["id"]))
	var year := int(gs.season_year)
	var clubs := involved(e, year)
	var beats: Array = (e.get("beats", []) as Array).duplicate()
	var lead := "" if str(e.get("clubs", "")) == "all" or clubs.is_empty() else str(clubs[0])
	gs.add_news("league_story", "%s. %s" % [str(e["headline"]), " ".join(PackedStringArray(beats))], "",
			{"headline": str(e["headline"]), "beats": beats, "club": lead, "weight": NEWS_WEIGHT,
			"angle": "year", "year_event": str(e["id"])})
	for p in e.get("penalties", []):
		if clubs.has(str(p.get("club", ""))):
			_penalty(gs, p)
	if not e.has("card") or not clubs.has(str(gs.my_club)) or not bool(gs.stories_on) or gs.is_sacked():
		return {}
	var t := StoryDeck.normalise(e["card"])
	var ctx: Dictionary = ClubStories.context(gs)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(str(t["id"]))
	var card := StoryEngine.build([], t, {"kind": "club"}, ctx["club"], rng, gs.story_week())
	card["year_event"] = str(e["id"])
	return card


static func _penalty(gs, p: Dictionary) -> void:
	var club := str(p.get("club", ""))
	match str(p.get("op", "")):
		"fine":
			if club == str(gs.my_club):
				var cut := fine_cut_m(int(p.get("amount", 0)), int(gs.season_year))
				var into := str(int(gs.season_year) + 1)
				var cuts: Dictionary = state(gs)["budget_cuts"]
				cuts[into] = snappedf(float(cuts.get(into, 0.0)) + cut, 0.1)
				gs.add_news("board", "The fine comes out of next season's football budget: the board has $%.1fm to spend, not $%.1fm." % [
						ClubBudget.ANNUAL_M - float(cuts[into]), ClubBudget.ANNUAL_M])
		"lose_pick":
			lose_pick(gs, club, int(p.get("year", gs.season_year)), int(p.get("round", 1)), str(p.get("to", "")))
		"finals_ban":
			var bans: Dictionary = state(gs)["finals_bans"]
			var key := str(gs.season_year)
			if not bans.has(key):
				bans[key] = []
			if not (bans[key] as Array).has(club):
				(bans[key] as Array).append(club)
		"trade_ban":
			(state(gs)["trade_bans"] as Dictionary)[club] = int(p.get("until", gs.season_year))


## A fine as a cut to next season's football budget ($m): its share of that
## year's salary cap, of the board's annual budget, to one decimal.
static func fine_cut_m(amount: int, year: int) -> float:
	var cap := cap_for_year(year)
	if amount <= 0 or cap <= 0:
		return 0.0
	return clampf(snappedf(float(amount) / float(cap) * ClubBudget.ANNUAL_M, 0.1), CUT_MIN_M, CUT_MAX_M)


## The real salary cap of a year (data/legacy/era_rules.csv); the game's own
## cap outside the table.
static func cap_for_year(year: int) -> int:
	if _caps.is_empty() and FileAccess.file_exists(ERA_RULES):
		var f := FileAccess.open(ERA_RULES, FileAccess.READ)
		f.get_csv_line()   # the header
		while not f.eof_reached():
			var row := f.get_csv_line()
			if row.size() < 4 or row[0] != "salary_cap":
				continue
			for y in range(int(row[2]), int(row[3]) + 1):
				_caps[y] = int(row[1])
	return int(_caps.get(year, Contracts.salary_cap_for_year(year)))


## The league takes `club`'s pick in `year`'s draft, round `rnd`: to `to` (a
## club) or to no one. A club that traded that pick away loses another it holds
## in the same round, if it has one.
static func lose_pick(gs, club: String, year: int, rnd: int, to: String) -> void:
	var owner := to if to != "" else FORFEIT
	var own := "%d:%d:%s" % [year, rnd, club]
	if gs.pick_owner_of(year, rnd, club) == club:
		gs.pick_owner[own] = owner
		return
	for key in gs.pick_owner.keys():
		var parts := str(key).split(":")
		if int(parts[0]) == year and int(parts[1]) == rnd and str(gs.pick_owner[key]) == club:
			gs.pick_owner[key] = owner
			return


## The clubs the league has thrown out of this season's finals.
static func finals_banned(gs) -> Array:
	if not (gs.year_events is Dictionary):
		return []
	return ((gs.year_events.get("finals_bans", {}) as Dictionary).get(str(gs.season_year), []) as Array).duplicate()


## Can `club` trade players in this season? (The league froze Sydney's trades.)
static func trade_banned(gs, club: String) -> bool:
	if not (gs.year_events is Dictionary):
		return false
	var bans: Dictionary = gs.year_events.get("trade_bans", {})
	return bans.has(club) and int(gs.season_year) <= int(bans[club])


## Next season's football budget cut for your club ($m), or 0.
static func budget_cut_m(gs, year: int) -> float:
	if not (gs.year_events is Dictionary):
		return 0.0
	return float((gs.year_events.get("budget_cuts", {}) as Dictionary).get(str(year), 0.0))
