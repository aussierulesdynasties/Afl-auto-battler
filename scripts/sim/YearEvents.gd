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
##
## The supplements saga (2013's penalties and the 2016 season bans) has its own
## New career switch, Supplements saga (GameState.supplements), apart from
## Controversies (director, 2026-11-13: "its punishment (full 1 year ban of
## list) is far more severe"): an event tagged "switch": "supplements" follows
## that switch only. The banned players are real, named on the public record
## (docs/research/supplements_bans_2016.md).

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
	for k in ["trade_bans", "finals_bans", "budget_cuts", "recorded", "season_bans"]:
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
	if not switched_on(gs, e):
		return false
	if (state(gs)["done"] as Array).has(str(e["id"])):
		return false
	if str(e.get("clubs", "")) != "all" and involved(e, int(gs.season_year)).is_empty():
		return false
	return gs.season.is_regular_done() or int(gs.season.round_index) >= int(e.get("round", 0))


## Is the event's switch on? The supplements saga follows its own switch;
## every other controversy follows Controversies.
static func switched_on(gs, e: Dictionary) -> bool:
	if str(e.get("switch", "")) == "supplements":
		return bool(gs.supplements)
	return not bool(e.get("controversy", false)) or bool(gs.controversies)


## This week: fire every event that is due. Returns the cards for your club.
## Penalties land whether or not you get the card (a sacked coach, stories off).
static func week(gs) -> Array:
	var cards := []
	if gs.season == null:
		return cards
	lift_bans(gs)
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
		"record_list":
			# Who was at the club when it broke: a later ban reaches only them.
			var ids := []
			for q in gs.season.lists.get(club, []):
				ids.append(str(q["id"]))
			(state(gs)["recorded"] as Dictionary)[str(p.get("key", club))] = ids
		"season_ban":
			season_ban(gs, p)
		"top_up":
			top_up(gs, club, int(p.get("max", 0)))


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


## The players a season ban names, found on this season's AFL lists by
## surname and date of birth (a "Paddy" is a "Patrick" in some lists). Where
## the career was running when the scandal broke (record_list), only players
## on that club's list then are named: a save that sent one elsewhere first
## never had him in the program. Where it broke before the career began,
## every named player still listed. Returns [[club, player]].
static func ban_targets(gs, p: Dictionary) -> Array:
	var want := {}
	for n in p.get("players", []):
		want[_who(str(n.get("last", "")), str(n.get("dob", "")))] = true
	var recorded: Dictionary = state(gs)["recorded"]
	var key := str(p.get("key", ""))
	var only: Array = recorded.get(key, []) if recorded.has(key) else []
	var out := []
	for code in gs.season.lists:
		for q in gs.season.lists[code]:
			if not want.has(_who(str(q.get("last", "")), str(q.get("dob", "")))):
				continue
			if recorded.has(key) and not only.has(str(q["id"])):
				continue
			out.append([str(code), q])
	return out


static func _who(last: String, dob: String) -> String:
	return "%s|%s" % [last.to_lower().replace("'", "").strip_edges(), dob.strip_edges()]


## Ban the named players for the whole of this season, finals included,
## wherever they are listed now. They come back next season (lift_bans).
static func season_ban(gs, p: Dictionary) -> void:
	var year := int(gs.season_year)
	var names: PackedStringArray = []
	var ids := []
	for hit in ban_targets(gs, p):
		var q: Dictionary = hit[1]
		q["season_ban"] = year
		ids.append(str(q["id"]))
		names.append("%s (%s)" % [GameDB.player_display_name(q), GameDB.club_short(str(hit[0]))])
	(state(gs)["season_bans"] as Dictionary)[str(year)] = ids
	if names.is_empty():
		gs.add_news("league", "None of the banned players is on an AFL list this season.")
	else:
		gs.add_news("league", "Banned for all of %d: %s." % [year, ", ".join(names)])


## Is he banned for this season (season_ban)?
static func is_banned(q: Dictionary) -> bool:
	return q.has("season_ban")


## The first week of a season past a ban: the banned players are free again,
## wherever they are now.
static func lift_bans(gs) -> void:
	var bans: Dictionary = state(gs)["season_bans"]
	var done: PackedStringArray = []
	for y in bans.keys():
		if int(y) < int(gs.season_year):
			done.append(str(y))
	if done.is_empty():
		return
	var back := 0
	var groups: Array = gs.season.lists.values()
	groups.append(gs.free_agents)
	for list in groups:
		for q in list:
			if (q as Dictionary).has("season_ban") and int(q["season_ban"]) < int(gs.season_year):
				q.erase("season_ban")
				back += 1
	for y in done:
		bans.erase(y)
	if back > 0:
		gs.add_news("league", "The players banned for %s are free to play again." % ", ".join(done))


## The top-up rule (Essendon, 2016: up to ten players for the year): the
## club signs one player for each of its own banned this season, at most
## `most`, the best rated left in the pool the mid-season draft takes from
## (unsigned free agents, passed-over prospects). Each is on the senior
## minimum for this season only: out of contract at its end.
static func top_up(gs, club: String, most: int) -> void:
	if not gs.season.lists.has(club):
		return
	var banned := 0
	for q in gs.season.lists[club]:
		if is_banned(q):
			banned += 1
	var want := mini(banned, most)
	var signed: PackedStringArray = []
	for p in MidseasonDraft.pool(gs):
		if signed.size() >= want:
			break
		if gs.free_agents.has(p):
			gs.free_agents.erase(p)
			for k in ["offers", "market_round", "market_log", "talks"]:
				p.erase(k)
		else:
			gs.draftee_pool.erase(p)
			gs.drafted_draftees[str(p["id"])] = club
			gs._mark_drafted(p, "top_up", 0, club)
			TeamFamiliarity.arrive_draftee(p)
		if not p.has("xp"):
			p["xp"] = 0
			p["xp_games"] = 0
		gs._join(club, p)
		# This season only: the rollover takes one off, so he is out of contract.
		p["contract_years"] = 1
		p["salary"] = RookieList.senior_wage(int(gs.season_year))
		p["top_up"] = int(gs.season_year)
		Workload.reset({club: [p]})
		signed.append(GameDB.player_display_name(p))
	if not signed.is_empty():
		gs.add_news("contract", "%s sign %d top-up player%s for %d: %s." % [GameDB.club_name(club), signed.size(),
				"" if signed.size() == 1 else "s", int(gs.season_year), ", ".join(signed)])
