extends RefCounted
## The game league's season, as a fingerprint: the fixture (every match and its
## venue, the Gather Round) and a whole season simulated through the finals
## (every score, venue, tag and label, the ladder, the bracket's slots and the
## premier). tests/test_season_rules.gd compares it with the hashes recorded
## from the code before season rules existed (P4), so the 2026 league stays
## byte-identical. Uses only the Season API that predates season rules.

## Seeds whose fixture is fingerprinted, and the ones played through the finals.
const FIXTURE_SEEDS := [1, 2, 3, 2027, 90210]
const PLAYED_SEEDS := [2027, 7]


static func lists(codes: Array) -> Dictionary:
	var out := {}
	for c in codes:
		out[c] = GameDB.club_list(str(c))
	return out


static func fixture_text(season: Season) -> String:
	var rounds := []
	for r in range(season.fixture.size()):
		var ms := []
		for m in season.fixture[r]:
			ms.append([str(m["home"]), str(m["away"]), season.round_venue(r, str(m["home"]), str(m["away"]))])
		rounds.append(ms)
	return JSON.stringify({"rounds": rounds, "gather": season.gather_round()})


static func _res(res: Dictionary) -> Array:
	return [str(res.get("home", "")), str(res.get("away", "")), res.get("score", []),
			int(res.get("round", 0)), str(res.get("label", "")), str(res.get("venue", "")),
			str(res.get("tag", "")), bool(res.get("decided_on_ladder", false))]


static func played_text(season: Season) -> String:
	var regular := []
	while not season.is_regular_done():
		var week := []
		for res in season.play_round():
			week.append(_res(res))
		regular.append(week)
	var ladder := []
	for row in season.ladder_sorted():
		ladder.append(JSON.stringify(row))
	season.start_finals()
	var finals := []
	var guard := 0
	while not season.is_season_over() and guard < 12:
		guard += 1
		var week := []
		for res in season.play_finals_week():
			week.append(_res(res))
		finals.append(week)
	var slots: Dictionary = season.finals.get("slots", {})
	var keys := slots.keys()
	keys.sort()
	var s := []
	for k in keys:
		s.append([str(k), str(slots[k])])
	return JSON.stringify({"regular": regular, "ladder": ladder, "top": season.finals.get("top", []),
			"finals": finals, "slots": s, "premier": str(season.finals.get("premier", "")),
			"week": int(season.finals.get("week", 0))})


## {"fixture:<seed>": md5, "played:<seed>": md5} for the league of `year`'s clubs.
static func digest(year := 2027) -> Dictionary:
	var codes: Array = GameDB.active_clubs(year).duplicate()
	var l := lists(codes)
	var out := {}
	for sd in FIXTURE_SEEDS:
		out["fixture:%d" % sd] = fixture_text(Season.new(codes.duplicate(), l, sd)).md5_text()
	for sd in PLAYED_SEEDS:
		out["played:%d" % sd] = played_text(Season.new(codes.duplicate(), l, sd)).md5_text()
	return out
