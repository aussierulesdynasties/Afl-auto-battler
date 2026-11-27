extends RefCounted
## Ambitions and the Council-faction wiring (relationship overhaul follow-up,
## director 2026-11-26): every club's players hold ambitions picked from their
## facts and temperament, progress each round, met ones lift opinion and
## Respect, soured ones leave a grievance the fringe faction reads and a trade
## ask; the profile words; two council members clashing on one card; a
## restless line or development coach losing his man-management and acting on
## the cards; council sway on a faction and the season's climate. Run through
## tests/run_ambitions_tests.gd.

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 2061
const Ran := preload("res://tests/functions_ran.gd")


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	GameDB.reload()
	_t("_test_files_check")
	_t("_test_every_club_holds_ambitions")
	_t("_test_temperament_leans")
	_t("_test_met_lifts_opinion_and_respect")
	_t("_test_soured_feeds_factions_and_trades")
	_t("_test_injury_lapses")
	_t("_test_contract_signed")
	_t("_test_leadership_role")
	_t("_test_profile_words")
	_t("_test_clash_on_one_card")
	_t("_test_clash_own_way")
	_t("_test_restless_coach_teeth")
	_t("_test_restless_cards")
	_t("_test_council_sways_faction")
	_t("_test_climate")
	_t("_test_seasons_played")
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	GameState.stories_on = true
	print(Ran.line("Ambitions", self))


func _fresh(club := "GEE") -> void:
	GameState.reset()
	GameState.replay_seed = SUITE_SEED
	GameState.stories_on = false
	GameState.start_season(club, GameDB.club_list(club))
	GameState._settle_week_event()
	GameState.week_event = {}


func _player(code: String, i := 0) -> Dictionary:
	return GameState.season.lists[code][i]


## A round's result with `ids` in the home side of `club` (won or lost).
func _result(club: String, ids: Array, won := true) -> Array:
	var other := ""
	for c in GameState.season.lists:
		if str(c) != club:
			other = str(c)
			break
	var side := []
	for id in ids:
		side.append({"id": id})
	return [{"home": club, "away": other, "score": [90, 60] if won else [60, 90], "roster": [side, []]}]


func _aim(p: Dictionary, k: String, have: int, need: int) -> Dictionary:
	Ambitions.start(p, k, GameState.season_year, GameState.games_played(p))
	var a: Dictionary = p[Ambitions.KEY]
	a["have"] = have
	a["need"] = need
	return a


func _has_mark(id: String, k: String) -> bool:
	for m in Opinion.mods(GameState.relations, Opinion.player_key(id)):
		if str(m.get("k", "")) == k:
			return true
	return false


func _test_files_check() -> void:
	var bad := Ambitions.check(Ambitions.cfg())
	_check(bad.is_empty(), "ambitions.json is sound: %s" % str(bad))
	var fb := Factions.check(Factions.cfg())
	_check(fb.is_empty(), "factions.json is sound: %s" % str(fb))
	var mb := Opinion.check_defs(Opinion.defs())
	_check(mb.is_empty(), "modifiers.json is sound: %s" % str(mb))
	_check(Ambitions.check({"hold_chance": 0, "order": ["x"], "kinds": {}}).size() >= 2,
			"A broken file says what is wrong")


func _test_every_club_holds_ambitions() -> void:
	_fresh()
	var seen := {}
	var clubs := 0
	for code in GameState.season.lists:
		var n := 0
		for p in GameState.season.lists[code]:
			var a := Ambitions.of(p, GameState.season_year)
			_check(not a.is_empty(), "Every player is read for an ambition at %s" % code)
			if str(a.get("state", "")) == "active":
				n += 1
				seen[str(a["k"])] = true
		if n > 0:
			clubs += 1
		_check(n >= 4, "%s players hold ambitions (%d)" % [code, n])
	_check(clubs == GameState.season.lists.size(), "Every club's players hold ambitions (%d clubs)" % clubs)
	_check(seen.size() >= 5, "The kinds spread across the league: %s" % str(seen.keys()))
	# The same rule twice gives the same answer (no reroll on load).
	var p := _player("GEE")
	var before: Dictionary = (p[Ambitions.KEY] as Dictionary).duplicate()
	Ambitions.ensure(GameState)
	_check(p[Ambitions.KEY] == before, "Ensuring again keeps the season's ambition")


func _test_temperament_leans() -> void:
	var p := {"id": "t1", "age": 30.0, "temperament": ["competitor"]}
	var q := {"id": "t2", "age": 30.0, "temperament": ["mercenary"]}
	_check(Ambitions.pull(p, "win_now") > Ambitions.pull(q, "win_now"),
			"A competitor leans to winning now more than a mercenary")
	_check(Ambitions.fits({"age": 19.0}, "senior_spot", 3, false, false), "A kid fits a senior spot")
	_check(not Ambitions.fits({"age": 30.0}, "senior_spot", 200, true, false), "A veteran does not")
	_check(Ambitions.fits({"age": 27.0}, "milestone_push", 92, true, false), "Eight games from 100 is a milestone push")
	_check(not Ambitions.fits({"age": 27.0}, "milestone_push", 60, true, false), "Forty games out is not")


func _test_met_lifts_opinion_and_respect() -> void:
	_fresh()
	var p := _player("GEE", 3)
	_aim(p, "senior_spot", 5, 6)
	var r0 := Promises.respect(GameState)
	var evs := Ambitions.after_round(GameState, _result("GEE", [str(p["id"])]))
	_check(str((p[Ambitions.KEY] as Dictionary)["state"]) == "met", "Six games played: met")
	_check(evs.size() >= 1 and str(evs[0]["e"]) == "met", "The round says so")
	_check(_has_mark(str(p["id"]), "ambition_met"), "He thinks more of you for it")
	_check(Promises.respect(GameState) == r0 + int(Ambitions.cfg()["met_respect"]), "Your Respect grows")
	# A rival club's man by the same rule, and its coach's Respect.
	var code := ""
	for c in GameState.season.lists:
		if str(c) != "GEE":
			code = str(c)
			break
	var q := _player(code, 3)
	_aim(q, "win_now", 11, 12)
	var rr := Promises.respect(GameState, code)
	Ambitions.after_round(GameState, _result(code, [], true))
	_check(str((q[Ambitions.KEY] as Dictionary)["state"]) == "met", "A rival's veteran sees his win")
	_check(Promises.respect(GameState, code) == rr + 1, "Their coach's Respect grows too")


func _test_soured_feeds_factions_and_trades() -> void:
	_fresh()
	var p := _player("GEE", 5)
	p["injury_weeks"] = 0
	_aim(p, "bigger_role", 0, 15)
	GameState.season.round_index = GameState.season.regular_rounds() - 3
	Ambitions.after_round(GameState, _result("GEE", []))
	_check(Ambitions.soured(p, GameState.season_year), "Fifteen games with three rounds left: soured")
	_check(_has_mark(str(p["id"]), "ambition_soured"), "He holds it against you")
	_check(Factions.grieves(GameState.relations, str(p["id"]), str(Factions.kind_cfg("fringe")["grievance"])),
			"The fringe players' grievance reads it")
	# The trade ask: rolled once a season, the same every time it is asked.
	var a1 := Ambitions.asks_out(p, GameState.season_year)
	_check(a1 == Ambitions.asks_out(p, GameState.season_year), "The ask is the same however often it is asked")
	var asked := 0
	for i in 200:
		var x := {"id": "sour%d" % i, Ambitions.KEY: {"k": "bigger_role", "y": 2026, "state": "soured"}}
		if Ambitions.asks_out(x, 2026):
			asked += 1
	_check(asked > 40 and asked < 120, "About ask_out of soured men ask to go (%d of 200)" % asked)


func _test_injury_lapses() -> void:
	_fresh()
	var p := _player("GEE", 6)
	p["injury_weeks"] = 6
	_aim(p, "senior_spot", 0, 6)
	GameState.season.round_index = GameState.season.regular_rounds() - 2
	Ambitions.after_round(GameState, _result("GEE", []))
	_check(str((p[Ambitions.KEY] as Dictionary)["state"]) == "lapsed", "Injured, it lapses")
	_check(not _has_mark(str(p["id"]), "ambition_soured"), "With no hard feelings")
	p["injury_weeks"] = 0


func _test_contract_signed() -> void:
	_fresh()
	var p := _player("GEE", 2)
	p["contract_years"] = 1
	_aim(p, "big_contract", 0, 1)
	GameState._resign(p, 3)
	_check(str((p[Ambitions.KEY] as Dictionary)["state"]) == "met", "Signed on: met")
	_check(_has_mark(str(p["id"]), "ambition_met"), "And he is pleased")
	# A season's close leaves a contract ambition to the signings.
	var q := _player("GEE", 4)
	q["contract_years"] = 1
	_aim(q, "big_contract", 0, 1)
	Ambitions.season_end(GameState)
	_check(str((q[Ambitions.KEY] as Dictionary)["state"]) == "active", "The season's close waits for the signings")


func _test_leadership_role() -> void:
	_fresh()
	var p := _player("GEE", 7)
	_aim(p, "leadership_role", 0, 1)
	Ambitions.season_end(GameState)
	_check(Ambitions.soured(p, GameState.season_year), "Never named to the group by season's end: soured")


func _test_profile_words() -> void:
	_fresh()
	var p := _player("GEE", 3)
	_aim(p, "senior_spot", 2, 6)
	var w := RelationsView.ambition(GameState, p)
	_check(str(w.get("want", "")) == "Wants to play senior football", "The profile says what he wants: %s" % str(w))
	_check(str(w.get("status", "")).begins_with("2 of 6 games so far"), "And where it stands: %s" % str(w.get("status", "")))
	_aim(p, "milestone_push", 0, 4)
	(p[Ambitions.KEY] as Dictionary)["target"] = 100
	w = RelationsView.ambition(GameState, p)
	_check(str(w["want"]) == "Wants to reach 100 games this season", "A milestone names its number")
	_check(RelationsView.ambition(GameState, {"id": "x"}).is_empty(), "No ambition, nothing to say")


## Every member's agenda set: the senior assistant holds the line on
## standards, the development coach brings the kids through, the rest mind
## the bodies (no view on these cards).
func _seat_agendas(club: String) -> void:
	var staff: Dictionary = GameState.club_staff(club)
	for job in staff:
		(staff[job] as Dictionary)["agenda"] = "fitness"
	if staff.has("SA"):
		staff["SA"]["agenda"] = "standards"
	if staff.has("DEV"):
		staff["DEV"]["agenda"] = "youth"
	for job in Council.OFFICE_JOBS:
		GameState.council["office"][club][job]["agenda"] = "fitness"


func _clash_card() -> Dictionary:
	return {"tid": "test_clash", "title": "A test", "options": [
			{"label": "Back the kid", "effects": [{"op": "start_backing"}]},
			{"label": "Stay the course", "effects": [{"op": "forgo_xp"}]},
			{"label": "Lift the standards", "effects": [{"op": "culture", "strand": "standards", "d": 1}]}]}


func _member(club: String, job: String) -> Dictionary:
	for m in Council.members(GameState, club):
		if str(m["job"]) == job:
			return m
	return {}


func _test_clash_on_one_card() -> void:
	_fresh("COL")
	_seat_agendas("COL")
	var card := _clash_card()
	Council.pitch_cards(GameState, [card])
	var p: Dictionary = card.get("pitch", {})
	var c: Dictionary = card.get("clash", {})
	_check(not p.is_empty() and not c.is_empty(), "Two members back the card: %s / %s" % [str(p.get("job")), str(c.get("job"))])
	_check(int(p.get("option", -1)) != int(c.get("option", -1)), "They back different choices")
	var lines := Council.pitch_lines(card)
	_check(Council.said_count(card) == 2, "Both speak in their own words")
	_check(lines.size() == 8, "Each side's stakes and the third way, a number a line (%d)" % lines.size())
	var sa := _member("COL", "SA")
	var dev := _member("COL", "DEV")
	var sa0 := Council.loyalty(GameState, sa)
	var dev0 := Council.loyalty(GameState, dev)
	# Side with whoever backs the standards choice.
	var std_choice := 2
	Council.answered(GameState, card, std_choice)
	var winner := sa if str(p["job"]) == "SA" else dev
	var loser := dev if winner == sa else sa
	var w0 := sa0 if winner == sa else dev0
	var l0 := dev0 if winner == sa else sa0
	_check(Council.loyalty(GameState, winner) - w0 == Opinion.opinion_move(0, 4) or Council.loyalty(GameState, winner) > w0,
			"The one you sided with: loyalty up")
	_check(Council.loyalty(GameState, loser) < l0, "The other: loyalty down")
	var won := Council.loyalty(GameState, winner) - w0
	var lost := Council.loyalty(GameState, loser) - l0
	_check(won == 4 and lost == -3, "+4 and -3 exactly (%d, %d)" % [won, lost])


func _test_clash_own_way() -> void:
	_fresh("COL")
	_seat_agendas("COL")
	var card := _clash_card()
	Council.pitch_cards(GameState, [card])
	var a0 := Promises.authority(GameState)
	Council.answered(GameState, card, 1)
	var sa := _member("COL", "SA")
	var dev := _member("COL", "DEV")
	_check(Council.loyalty(GameState, sa) == 48 and Council.loyalty(GameState, dev) == 48,
			"Your own way: both drop a little (%d, %d)" % [Council.loyalty(GameState, sa), Council.loyalty(GameState, dev)])
	_check(Promises.authority(GameState) == a0 + int(Council.OWN_WAY[1]), "And your Authority builds")
	# A card with one member's view stays as it was.
	var one := {"tid": "solo", "options": [{"label": "A", "effects": [{"op": "start_backing"}]},
			{"label": "B", "effects": [{"op": "forgo_xp"}]}]}
	Council.pitch_cards(GameState, [one])
	_check(not (one.get("pitch", {}) as Dictionary).is_empty() and (one.get("clash", {}) as Dictionary).is_empty(),
			"Only the kids' man has a view on a card without a standards choice")
	_check(Council.said_count(one) == 1 and Council.pitch_lines(one).size() == 4, "One voice, three stakes")


## Push a member's loyalty to about `target` (out of 100).
func _loyal_to(m: Dictionary, target: int) -> void:
	GameState.relations.erase(str(m["key"]))
	var raw := (target - 50) * Opinion.PER_POINT
	Opinion.add_raw(GameState.relations, str(m["key"]), "test", float(raw), 0.0, "council", "Test", GameState.season_year, "Round 1")


func _test_restless_coach_teeth() -> void:
	_fresh()
	var mid := _member("GEE", "MID")
	_check(not mid.is_empty(), "The club has a midfield coach")
	_check(Council.withheld(GameState, "GEE").is_empty(), "A settled staff softens every drop")
	_loyal_to(mid, 30)
	_check(Council.loyalty(GameState, mid) <= Council.RESTLESS_LINE, "Under 35: restless (%d)" % Council.loyalty(GameState, mid))
	var held := Council.withheld(GameState, "GEE")
	_check(held.has("MID"), "The midfield coach's man-management is withheld")
	var mids := Council.attached(GameState, "GEE", "MID")
	_check(not mids.is_empty() and Council.soften_withheld(mids[0], held), "From his midfielders")
	var fwds := Council.attached(GameState, "GEE", "FWD")
	var a_fwd: Dictionary = {}
	for f in fwds:
		if int(f.get("age", 25)) > Council.YOUTH_AGE:
			a_fwd = f
			break
	_check(a_fwd.is_empty() or not Council.soften_withheld(a_fwd, held), "Not from the forwards")
	# A rival club by the same rule.
	var code := "COL"
	var rm := _member(code, "DEF")
	_loyal_to(rm, 20)
	_check(Council.withheld(GameState, code).has("DEF"), "A rival's restless backline coach withholds too")
	# A senior assistant is not a line coach: his disloyalty waits for the season's end.
	var sa := _member("GEE", "SA")
	_loyal_to(sa, 10)
	_check(not Council.withheld(GameState, "GEE").has("SA"), "The senior assistant has no line to withhold from")
	_check(str(Council.restless(GameState, "GEE").get("job", "")) == "MID", "The restless advisor is the line coach")


func _test_restless_cards() -> void:
	_fresh()
	var dev := _member("GEE", "DEV")
	_loyal_to(dev, 28)
	var seats := Council.advisor_seats(GameState)
	_check(seats.has("restless") and str(seats["restless"]["name"]) == str(dev["name"]), "The cards can seat him")
	var facts := ClubStories.club_facts(GameState, 3, "regular")
	_check(int(facts.get("restless_staff", 0)) == 1, "The club's facts say there is one")
	_check(int(facts.get("restless_backing", 0)) == 0, "Backing no group yet")
	var found := 0
	for c in StoryDeck.all():
		if str(c.get("id", "")).begins_with("staff_restless_"):
			found += 1
			var errs := StoryDeck._check_card(c)
			_check(errs.is_empty(), "%s is a sound card: %s" % [str(c["id"]), str(errs)])
	_check(found == 3, "Three cards seat a restless coach (%d)" % found)
	# The card's choices move his loyalty and your standing.
	var before := Council.loyalty(GameState, dev)
	Council.card_loyalty(GameState, "GEE", "won_back")
	_check(Council.loyalty(GameState, dev) > before, "Won back: loyalty up")
	var parts: Array = StoryEngine._effect_parts({"op": "council", "do": "called_out"}, {"restless_name": "Sam Day"})
	_check(parts.size() == 1 and str(parts[0][1]) == "Sam Day's loyalty to you down 5.", "The gate says it: %s" % str(parts))
	parts = StoryEngine._effect_parts({"op": "standing", "a": 2}, {})
	_check(parts.size() == 1 and str(parts[0][1]) == "Your Authority up 2.", "And the standing: %s" % str(parts))


func _test_council_sways_faction() -> void:
	_fresh()
	_seat_agendas("GEE")
	var dev := _member("GEE", "DEV")
	var ids := []
	for p in GameState.season.lists["GEE"]:
		if int(p.get("age", 25)) > Council.YOUTH_AGE and CoachEffects.line_job(p) == "FWD":
			ids.append(str(p["id"]))
		if ids.size() == 3:
			break
	var f := {"k": "fringe", "members": ids, "leader": ids[0], "pressure": 0, "since": 1, "state": "forming"}
	_check(Council.backs_on(GameState, "GEE", dev, f), "A kids' man's agenda matches the fringe players' grievance")
	_check(Council.faction_sway(GameState, "GEE", f) == 0, "A steady development coach says nothing")
	_loyal_to(dev, 25)
	_check(Council.faction_sway(GameState, "GEE", f) == Council.STIR, "Restless, he pushes the group on (+%d)" % Council.STIR)
	_check(Factions.council_sway(GameState, "GEE", f) == Council.STIR, "Factions read it through council_sway")
	_loyal_to(dev, 80)
	_check(Council.faction_sway(GameState, "GEE", f) == -1, "Loyal, he talks it down")
	var g := {"k": "broken_word", "members": ids, "leader": ids[0]}
	_loyal_to(dev, 25)
	_check(Council.faction_sway(GameState, "GEE", g) == 0, "A group his line and agenda have nothing to do with: no say")


func _test_climate() -> void:
	_fresh()
	var list: Array = GameState.season.lists["GEE"]
	var st := Promises.standing(GameState, true)
	st["respect"] = 70
	_check(Factions.climate(GameState, "GEE", list) == -1, "A well-respected club, winning, nobody snubbed: quiet")
	st["respect"] = 30
	_check(Factions.climate(GameState, "GEE", list) == 1, "Low Respect: rough")
	for i in 12:
		Opinion.add_raw(GameState.relations, Opinion.player_key(str(list[i]["id"])), "test_drop", -10.0, 0.0, "selection",
				"Left out", GameState.season_year, "Round 1", "GEE")
	_check(Factions.climate(GameState, "GEE", list) == 2, "Low Respect and men snubbed: rougher")
	_check(Factions.losing_run(["W", "L", "L", "L"]) == 3 and Factions.losing_run(["L", "W"]) == 0, "A losing run counts back from the last game")


## Seasons played through at every club: rough clubs (low Respect or a long
## losing run) see more faction flashpoints than settled ones. Reported, for
## the director's read of the escalation, and checked loosely.
func _test_seasons_played() -> void:
	_fresh()
	var s = GameState.season
	var demands := {}
	var rough := {}
	var guard := 0
	while s.round_index < s.regular_rounds() and guard < 40:
		guard += 1
		GameState.advance()
		for code in GameState.season.lists:
			var c := str(code)
			if Factions.climate(GameState, c, GameState.season.lists[c]) > 0:
				rough[c] = int(rough.get(c, 0)) + 1
		for code in Factions.clubs(GameState):
			for f in Factions.of_club(GameState, str(code)):
				if str(f["state"]) != "forming":
					demands["%s|%s|%d" % [code, f["k"], int(f["since"])]] = str(code)
	var by_club := {}
	for k in demands:
		by_club[demands[k]] = int(by_club.get(demands[k], 0)) + 1
	var rough_clubs := []
	var calm_clubs := []
	for code in GameState.season.lists:
		var c := str(code)
		if int(rough.get(c, 0)) >= 8:
			rough_clubs.append(c)
		else:
			calm_clubs.append(c)
	var rough_n := 0
	for c in rough_clubs:
		rough_n += int(by_club.get(c, 0))
	var calm_n := 0
	for c in calm_clubs:
		calm_n += int(by_club.get(c, 0))
	var ambitions := {"met": 0, "soured": 0, "lapsed": 0, "active": 0}
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			var a := Ambitions.of(p, GameState.season_year)
			var stt := str(a.get("state", ""))
			if ambitions.has(stt):
				ambitions[stt] = int(ambitions[stt]) + 1
	print("Ambitions season: %s" % str(ambitions))
	for code in GameState.season.lists:
		var c := str(code)
		print("  %s respect %d, rough weeks %d, worst losing run %d, flashpoints %d" % [c,
				Promises.respect(GameState, "" if c == GameState.my_club else c), int(rough.get(c, 0)),
				_worst_run(GameState.season.club_results(c)), int(by_club.get(c, 0))])
	print("Factions season: %d flashpoints; %d rough clubs had %d (%.1f each), %d settled clubs had %d (%.1f each)" % [
			demands.size(), rough_clubs.size(), rough_n, float(rough_n) / maxf(1.0, rough_clubs.size()),
			calm_clubs.size(), calm_n, float(calm_n) / maxf(1.0, calm_clubs.size())])
	_check(s.round_index >= s.regular_rounds(), "The season plays through")
	_check(int(ambitions["met"]) > 0 and int(ambitions["soured"]) > 0, "Some ambitions are met and some sour")
	_check(demands.size() <= 18 * 3, "Not every club is at war with its coach (%d)" % demands.size())


func _worst_run(results: Array) -> int:
	var best := 0
	var n := 0
	for r in results:
		n = n + 1 if str(r) == "L" else 0
		best = maxi(best, n)
	return best
