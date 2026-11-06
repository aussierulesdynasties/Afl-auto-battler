class_name MatchKickoff
extends RefCounted
## Play match: the one way into your live match, from the hub (Skip to full
## time, a response tapped beside an opposition fact) and from the match preview's
## Continue (director, 2026-11-07: the preview is its own step before the setup).
## The pre-match scene goes up while the match is set up underneath, then the
## match-day setup opens.

## How long the pre-match scene runs before the side goes through the banner: a
## moment of the warm-up, time to jog in to the huddle unhurried and stand together,
## then the run - still a couple of seconds of match day, not a wait (a tap goes straight
## to the run).
const PRE_MATCH_SECONDS := 3.8

## True from the tap until the next screen is up: a second tap does nothing, and
## Back waits (the side is on its way out). The hub and the preview clear it when
## they open (reset).
static var busy := false


static func reset() -> void:
	busy = false


## The match you are about to play, or {} if you have none coming up
## (missed the finals, or already eliminated). Unified across the home and
## away season and the finals so the hub card, the preview and the start share it.
static func upcoming_match() -> Dictionary:
	var season: Season = GameState.season
	if season == null or season.is_season_over():
		return {}
	if not season.is_regular_done():
		var round_matches: Array = season.fixture[season.round_index]
		for m in round_matches:
			if m["home"] == GameState.my_club or m["away"] == GameState.my_club:
				var up := {"home": m["home"], "away": m["away"],
						"label": season.round_label(season.round_index), "tag": "",
						"weather": season.weather_for(str(m["home"]), str(m["away"]), season.round_index)}
				if season.round_index == season.gather_round():
					up["venue"] = season.round_venue(season.round_index, str(m["home"]), str(m["away"]))
				return up
		return {}
	for m in season.finals_week_matches():
		if str(m["home"]) == "" or str(m["away"]) == "":
			continue
		if m["home"] == GameState.my_club or m["away"] == GameState.my_club:
			return {"home": m["home"], "away": m["away"],
					"label": str(m["label"]), "tag": str(m["tag"]),
					"venue": season.finals_venue(m),
					"weather": season.weather_for(str(m["home"]), str(m["away"]),
							Season.REGULAR_ROUNDS + int(season.finals["week"]), m)}
	return {}


## Start your match. Returns false (nothing changed) when there is no match to
## play live, so the caller sims the round. `replace`: the match takes this
## screen's place in the back stack, so full time's Continue goes to the hub.
static func start(tree: SceneTree, replace := false) -> bool:
	if busy:
		return true
	var m := upcoming_match()
	if m.is_empty():
		return false
	busy = true
	# A response chosen under a fact opens this match on that call before the
	# first bounce, so Skip plays it the Watch way this once (the saved choice
	# stays); the button said "Play match" (HubScene._play_label).
	var way := GameState.match_way()
	if way == "skip" and not GameState.call_intent.is_empty():
		way = "watch"
	if not GameState.vignettes_on() or way == "skip":
		# Vignettes off (Settings), or Skip chosen: no banner scene, straight
		# to the match.
		if not GameState.prepare_interactive_match():
			busy = false
			return false
		GameState.match_way_live = way
		_go(replace)
		return true
	# The pre-match scene goes up in this frame: a couple of seconds of
	# match day (warm-up, final words, through the banner) while the match
	# is set up underneath. A tap sends them through the banner at once.
	var mine := GameState.my_club
	var opp := str(m["away"]) if str(m["home"]) == mine else str(m["home"])
	var season: Season = GameState.season
	# Everyone named runs out: the 18 on the ground and the interchange.
	var opp_squad := Squad.new(opp, season.lists[opp], false, opp, season.selections.get(opp, {}))
	var opp_ground: Array = opp_squad.ground + opp_squad.bench
	var heading := "%s  ·  %s v %s" % [str(m["label"]), GameDB.club_name(str(m["home"])),
			GameDB.club_name(str(m["away"]))]
	# The banner's occasion (Banners.pick): finals week, marquee game, must-win, spoon
	# bowl, milestones (GameState.banner_context).
	var label := str(m["label"])
	var banner_ctx := GameState.banner_context(m)
	# Gather Round: the warm-up is at the host ground the match is staged at.
	if str(m.get("venue", "")) != "" and label.ends_with(GatherRound.NAME):
		VignetteGround.use_match(m)
	var scene := PreMatchVignette.open(tree.root, mine, opp,
			GameState.my_squad().ground + GameState.my_squad().bench, opp_ground, heading,
			PreMatchVignette.is_final(label), banner_ctx)
	# Home-and-away rounds and finals both play live with the coach box.
	await tree.process_frame
	if not GameState.prepare_interactive_match():
		scene.get_parent().queue_free()
		busy = false
		return false
	GameState.match_way_live = way
	scene.play_through(PRE_MATCH_SECONDS)
	await scene.done
	_go(replace)
	return true


static func _go(replace: bool) -> void:
	if replace:
		Router.replace("match")
	else:
		Router.go("match")
