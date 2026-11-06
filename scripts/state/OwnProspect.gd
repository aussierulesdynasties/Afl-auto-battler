class_name OwnProspect
extends RefCounted
## The career's own created prospect, followed (row 64, ruling 4.Q8; Director
## Bible 5.13 #135 and ruling 49). The coach creates him at New Career (Club
## Forge, ARD-M7-008, GameState.add_custom_prospect); he enters the first
## National Draft class like anyone else. This file only tells his story:
## "create someone you care about, watch where they are drafted, follow
## whether they become a star, journeyman, role player or bust".
##
## Lightweight follow, no dashboard: a few lines in the league news at the
## moments that matter (he nominates for the draft, where he goes or that he
## was overlooked, his debut, a move or a delisting, each season's games and
## goals, the end of his career), his draft-board row and his profile marked
## "Created by you". Milestones and awards stay the normal ones. Nothing here
## touches the draft, the AI, his ratings or any club's list: it only reads.
##
## Switch "custom_prospect_story" (off by default). Off, nothing is written,
## shown or saved, and the game is exactly as before.

const FEATURE := "custom_prospect_story"
## The news kind of every line about him (NewsFront gives it a headline).
const KIND := "own_prospect"
## The mark on his draft-board row and profile.
const TAG := "Created by you"


static func on() -> bool:
	return Features.on(FEATURE)


## Whether `p` is the coach's created prospect (any career, any club).
static func is_own(p: Dictionary) -> bool:
	return bool(p.get("user_created", false))


## The mark his draft row and profile wear: TAG when the switch is on and he
## is the created prospect, else "".
static func tag(p: Dictionary) -> String:
	return TAG if on() and is_own(p) else ""


## Where he is now: {"at": "club" | "free" | "gone" | "pool" | "", "club",
## "p"}. "" means none of these: he aged out of the draft pool unpicked.
static func locate(gs) -> Dictionary:
	var id: String = gs.custom_prospect_id
	if id == "":
		return {"at": "", "club": "", "p": {}}
	var sources: Array = []
	if gs.season != null:
		sources.append(gs.season.lists)
	sources.append(gs.league_lists)
	for lists in sources:
		for code in lists:
			for p in lists[code]:
				if p is Dictionary and str(p.get("id", "")) == id:
					return {"at": "club", "club": str(code), "p": p}
	for p in gs.free_agents:
		if str(p.get("id", "")) == id:
			return {"at": "free", "club": "", "p": p}
	if gs.departed_names.has(id):
		var card = gs.departed_names[id]
		return {"at": "gone", "club": "", "p": card if card is Dictionary else {}}
	for p in gs.draftee_pool:
		if str(p.get("id", "")) == id and not gs.drafted_draftees.has(id):
			return {"at": "pool", "club": "", "p": p}
	# A real-lists start keeps the opening class in the draft's own pool.
	if gs.draft != null:
		for p in gs.draft.pool:
			if p is Dictionary and str(p.get("id", "")) == id:
				return {"at": "pool", "club": "", "p": p}
	return {"at": "", "club": "", "p": {}}


## Look at where he is and tell what changed since the last look. Called
## wherever he can move: his creation, the end of a national draft
## (`draft_year` > 0: still in the pool means he was overlooked), each
## round, a trade and the rollover. The first look only records him.
static func check(gs, draft_year := 0) -> void:
	if not on() or gs.custom_prospect_id == "":
		return
	var now := locate(gs)
	var seen: Dictionary = gs.custom_prospect_story
	var p: Dictionary = now["p"]
	var name := GameDB.player_display_name(p) if not p.is_empty() else str(seen.get("name", ""))
	var at := str(now["at"])
	var club := str(now["club"])
	if seen.is_empty():
		seen = {"at": at, "club": club, "name": name, "games": 0, "goals": 0}
		if at == "pool":
			_say(gs, nominated_line(p, gs.season_year), "")
		gs.custom_prospect_story = seen
		_note_totals(gs, seen, now)
		return
	var was := str(seen.get("at", ""))
	var was_club := str(seen.get("club", ""))
	if at == "club" and was != "club":
		_say(gs, signed_line(p, club, was), club)
	elif at == "club" and club != was_club:
		_say(gs, "%s has moved from %s to %s." % [name, GameDB.club_name(was_club), GameDB.club_name(club)], club)
	elif at == "free" and was == "club":
		_say(gs, "%s is off %s's list and looking for a new club." % [name, GameDB.club_name(was_club)], was_club)
	elif at == "gone" and was != "gone":
		_say(gs, over_line(name, int(seen.get("games", 0)), int(seen.get("goals", 0))), was_club)
	elif at == "" and was == "pool":
		_say(gs, "%s's time in the draft pool is over: no club took him." % name, "")
	elif at == "pool" and draft_year > 0 and int(seen.get("overlooked", 0)) != draft_year:
		seen["overlooked"] = draft_year
		_say(gs, "%s was overlooked in the %d National Draft." % [name, draft_year], "")
	seen["at"] = at
	seen["club"] = club
	if name != "":
		seen["name"] = name
	if at == "club":
		var games: int = gs.games_played(p)
		if int(seen.get("games", 0)) == 0 and games > 0:
			_say(gs, "%s made his AFL debut for %s." % [name, GameDB.club_name(club)], club)
		# The season line belongs to a club he was already at: one that has
		# just drafted or signed him after the finals had no season of his.
		if was == "club" and club == was_club:
			_season_line(gs, seen, p, club)
	_note_totals(gs, seen, now)
	gs.custom_prospect_story = seen


## The line the day he nominates: where he comes from and the draft he is in.
static func nominated_line(p: Dictionary, year: int) -> String:
	var name := GameDB.player_display_name(p)
	var team := str(p.get("draft_team", "")).strip_edges()
	if team == "":
		return "%s has nominated for the %d National Draft." % [name, year]
	return "%s, from %s, has nominated for the %d National Draft." % [name, team, year]


## The line the day a club takes him: the pick in a National Draft, the
## mid-season rookie draft, or a plain signing.
static func signed_line(p: Dictionary, club: String, was: String) -> String:
	var name := GameDB.player_display_name(p)
	var cname := GameDB.club_name(club)
	var pick := int(p.get("drafted_pick", 0))
	var kind := str(p.get("drafted_type", ""))
	if was == "pool" and kind == "national" and pick > 0:
		return "%s have taken %s with pick %d in the %d National Draft." % [cname, name, pick, int(p.get("drafted_year", 0))]
	if was == "pool" and kind == MidseasonDraft.KIND:
		return "%s have taken %s in the mid-season rookie draft." % [cname, name]
	return "%s have signed %s." % [cname, name]


static func over_line(name: String, games: int, goals: int) -> String:
	if games <= 0:
		return "%s's playing career is over without a senior game." % name
	return "%s's playing career is over: %d game%s and %d goal%s." % [name, games,
			"" if games == 1 else "s", goals, "" if goals == 1 else "s"]


## Once a season, when it is over: his games and goals for his club.
static func _season_line(gs, seen: Dictionary, p: Dictionary, club: String) -> void:
	if gs.season == null or not gs.season.is_season_over():
		return
	var year: int = gs.season_year
	if int(seen.get("season_line", 0)) == year:
		return
	seen["season_line"] = year
	_say(gs, season_line(GameDB.player_display_name(p), club, year, gs.season_tally.get(str(p.get("id", "")), {})), club)


static func season_line(name: String, club: String, year: int, tally: Dictionary) -> String:
	var games := int(tally.get("games", 0))
	var goals := int(tally.get("goals", 0))
	if games <= 0:
		return "%s did not play a senior game for %s in %d." % [name, GameDB.club_name(club), year]
	return "%s's %d: %d game%s and %d goal%s for %s." % [name, year, games, "" if games == 1 else "s",
			goals, "" if goals == 1 else "s", GameDB.club_name(club)]


## His career games and goals as last seen, for the line when it ends.
static func _note_totals(gs, seen: Dictionary, now: Dictionary) -> void:
	if str(now["at"]) != "club":
		return
	var p: Dictionary = now["p"]
	seen["games"] = gs.games_played(p)
	seen["goals"] = gs.career_goals_before(p)


static func _say(gs, text: String, club: String) -> void:
	gs.add_news(KIND, text)
	gs.news[0]["club"] = club
