extends RefCounted
## Promises.gd: every promise through one door, the coach's record, and the
## senior coach's Respect and Authority (yours and every rival's, by the same
## rules). Run through tests/run_promises_tests.gd.

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 2031
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
	_t("_test_archetype_lean")
	_t("_test_run_kept")
	_t("_test_run_broken")
	_t("_test_preview_drop_is_read_only")
	_t("_test_drops_build_authority")
	_t("_test_rival_parity")
	_t("_test_card_game_and_board_win")
	_t("_test_season_settles_and_saves")
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	GameState.stories_on = true
	print(Ran.line("Promises", self))


func _fresh() -> void:
	GameState.reset()
	GameState.replay_seed = SUITE_SEED
	GameState.stories_on = false
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	GameState._settle_week_event()
	GameState.week_event = {}


func _kid(p: Dictionary, games: int) -> Dictionary:
	p["career"] = {"games": games, "goals": 0, "stints": [],
			"through": GameState.season_year - 1, "unknown": []}
	for key in ["backed", "expects_game", "injury_weeks", "injury_kind", "suspension_weeks", "rested"]:
		p.erase(key)
	p["morale"] = 70
	return p


## The lowest-rated fit non-ruck: one auto-pick would not name on his own.
func _spare() -> Dictionary:
	var best := {}
	for p in GameState.my_list:
		if str(p["role"]) == "RUCK" or not Ratings.available(p):
			continue
		if best.is_empty() or int(Rating.ovr(p, 0)) < int(Rating.ovr(best, 0)):
			best = p
	return best


func _advance_mine(code := "GEE") -> void:
	var s = GameState.season
	if s != null and s.round_index < s.fixture.size():
		var rm: Array = s.fixture[s.round_index]
		for m in rm.duplicate():
			if str(m["home"]) != code and str(m["away"]) != code:
				rm.erase(m)
	GameState.advance()


func _in_side(id: String) -> bool:
	var side := GameState.current_side()
	for k in side:
		if (side[k] as Array).has(id):
			return true
	return false


func _out_of_side(id: String) -> Dictionary:
	var side := GameState.current_side().duplicate(true)
	for k in side:
		(side[k] as Array).erase(id)
	side["OUT"] = [id]
	return side


# --- The coach's standing ---------------------------------------------------

func _test_archetype_lean() -> void:
	for a in Archetypes.PHILOSOPHICAL:
		var b := Promises.base_for(a)
		_check(int(b[0]) + int(b[1]) == 2 * Promises.START,
				"%s leans one way as far as the other: no archetype starts better off (%s)" % [a, str(b)])
	_check(Promises.base_for("FATH")[0] > Promises.base_for("HARD")[0]
			and Promises.base_for("HARD")[1] > Promises.base_for("FATH")[1],
			"A Father Figure starts with more Respect, a Hardline Disciplinarian with more Authority")
	_check(Promises.base_for("") == [Promises.START, Promises.START], "No archetype: level")
	GameState.reset()
	var s := Promises.standing(GameState)
	_check(int(s["respect"]) == Promises.START and GameState.coach_standing.is_empty(),
			"Before a club, a level reading is shown and nothing is kept")
	_fresh()
	var arch := Promises._arch_p("GEE")
	var st := Promises.standing(GameState)
	_check(st["base"] == Promises.base_for(arch) and int(st["respect"]) == int(Promises.base_for(arch)[0]),
			"Your standing starts at your archetype's base (%s: %s)" % [arch, str(st)])


func _test_run_kept() -> void:
	_fresh()
	var kid := _kid(_spare(), 2)
	var id := str(kid["id"])
	var r0 := Promises.respect(GameState)
	var t0 := Trust.value(GameState.relations, Trust.player_key(id))
	GameState.back_player(id)
	var w := Promises.word(GameState)
	_check(int(w["made"]) == 1 and Promises.respect(GameState) == r0 + int(Promises.MADE[0]),
			"Backing him is a promise made, and builds Respect (%s)" % str(w))
	var owed := Promises.of(GameState, id)
	_check(owed.size() == 1 and str(owed[0]["kind"]) == "run" and int(owed[0]["weeks_left"]) == Backing.RUN_GAMES,
			"His promises read as one run of three games (%s)" % str(owed))
	# Three games he plays, however many rounds that takes: a round he misses
	# injured waits, as the rule says (seed 2031 hurts him in his first game).
	for i in Backing.RUN_GAMES + 6:
		if str(Backing.ledger(kid)[0]["state"]) != "active":
			break
		_advance_mine()
	_check(str(Backing.ledger(kid)[0]["state"]) == "done", "(setup) the run is played out")
	_check(int(w["kept"]) == 1 and int(w["broken"]) == 0, "The record says kept (%s)" % str(w))
	_check(Promises.respect(GameState) >= r0 + int(Promises.MADE[0]) + int(Promises.KEPT["run"][0]),
			"Keeping your word builds Respect (%d -> %d)" % [r0, Promises.respect(GameState)])
	_check(Trust.value(GameState.relations, Trust.player_key(id)) > t0,
			"...and leaves a lasting mark on his opinion of you")
	_check(Promises.of(GameState, id).is_empty(), "Nothing is owed once it is kept")
	var why := ""
	for r in Promises.standing_reasons(GameState):
		if str(r.get("why", "")).begins_with("You kept"):
			why = Promises.reason_text(r)
			break
	_check(why.contains("You kept your word to") and why.contains("Respect +"),
			"The reason reads in football words (%s)" % why)


func _test_run_broken() -> void:
	_fresh()
	var kid := _kid(_spare(), 2)
	var id := str(kid["id"])
	GameState.back_player(id)
	var r0 := Promises.respect(GameState)
	var a0 := Promises.authority(GameState)
	# The permanent part (Trust.base): his live opinion also carries the
	# broken run's fading mark (Opinion), which the line below does not count.
	var t0 := Trust.base(GameState.relations, Trust.player_key(id))
	GameState.set_selection(_out_of_side(id))
	_advance_mine()
	var w := Promises.word(GameState)
	_check(str(Backing.ledger(kid)[0]["state"]) == "broken", "(setup) left out fit, the run breaks")
	_check(int(w["broken"]) == 1 and int(w["kept"]) == 0, "The record says broken (%s)" % str(w))
	_check(Promises.respect(GameState) == r0 + int(Promises.BROKEN["run"][0]),
			"Breaking your word costs Respect (%d -> %d)" % [r0, Promises.respect(GameState)])
	_check(Promises.authority(GameState) >= a0 + int(Promises.BROKEN["run"][1]),
			"...and shows the group you will make the hard call (%d -> %d)" % [a0, Promises.authority(GameState)])
	_check(Trust.base(GameState.relations, Trust.player_key(id)) == t0 + StoryEngine.BROKEN_RUN_TRUST,
			"His permanent trust falls once, as it always did (not twice)")
	_check(Promises.witnesses(GameState, kid).size() <= Promises.WITNESS_MAX
			and Promises.witnesses(GameState, kid).all(func(q): return str(q["role"]) == str(kid["role"]) and q != kid),
			"The players who saw it are his line-mates")


func _test_preview_drop_is_read_only() -> void:
	_fresh()
	var kid := _kid(_spare(), 2)
	var id := str(kid["id"])
	GameState.back_player(id)
	_check(_in_side(id), "(setup) he is in the side on his run")
	var st0: Dictionary = GameState.coach_standing.duplicate(true)
	var rel0: Dictionary = GameState.relations.duplicate(true)
	var w0: Dictionary = GameState.coach_word.duplicate(true)
	var pv := Promises.preview_drop(GameState, id)
	_check(GameState.coach_standing == st0 and GameState.relations == rel0 and GameState.coach_word == w0,
			"The preview changes nothing")
	_check((pv["broken"] as Array).size() == 1 and int(pv["respect"]) == int(Promises.BROKEN["run"][0]),
			"Dropping him would break his run and cost Respect (%s)" % str(pv))
	_check(int(pv["opinion"]) == Trust.opinion_move(Trust.value(GameState.relations, Trust.player_key(id)), StoryEngine.BROKEN_RUN_TRUST),
			"...and says what it does to his opinion of you (%s)" % str(pv))
	var other := ""
	for q in GameState.my_list:
		if str(q["id"]) != id and _in_side(str(q["id"])) and Promises.of(GameState, str(q["id"])).is_empty():
			other = str(q["id"])
			break
	var pv2 := Promises.preview_drop(GameState, other)
	_check((pv2["broken"] as Array).is_empty() and int(pv2["respect"]) == 0 and int(pv2["opinion"]) == 0,
			"A player with no promise breaks nothing (%s)" % str(pv2))
	_check(Promises.preview_drop(GameState, "nobody") == {"respect": 0, "authority": 0, "broken": [], "opinion": 0},
			"An unknown player previews nothing")


func _test_drops_build_authority() -> void:
	_fresh()
	var fit := []
	for p in GameState.my_list:
		if Ratings.available(p):
			fit.append(str(p["id"]))
	var played := {}
	for i in 22:
		played[fit[i]] = true
	Promises.after_match(GameState, played)
	var auto := played.duplicate()
	auto.erase(fit[0])
	auto[fit[22]] = true
	var a_auto := Promises.authority(GameState)
	Promises.after_match(GameState, auto)
	Promises.after_match(GameState, played)
	_check(Promises.authority(GameState) == a_auto, "On Auto-pick the staff's changes are not your drops")
	GameState.set_selection(GameState.current_side())
	var a0 := Promises.authority(GameState)
	_check(a0 == int(Promises.standing(GameState)["base"][1]), "The first side drops nobody")
	var next := played.duplicate()
	next.erase(fit[0])
	next[fit[22]] = true
	Promises.after_match(GameState, next)
	_check(Promises.authority(GameState) == a0 + int(Promises.DROP[1]), "Dropping a fit player builds Authority")
	var hurt := next.duplicate()
	for i in range(1, 5):
		hurt.erase(fit[i])
	Promises.after_match(GameState, hurt, {fit[1]: true})
	_check(Promises.authority(GameState) == a0 + int(Promises.DROP[1]) * (1 + Promises.DROP_ROUND_MAX),
			"No more than %d drops count in a round, and one who could not play is not a drop" % Promises.DROP_ROUND_MAX)


func _test_rival_parity() -> void:
	_fresh()
	# A drop needs a fit man who played last week and not this one: play on until
	# some rival coach has made one (seed 2031: none in two rounds, 9 of 17 in three).
	for i in 6:
		GameState.advance()
		if i >= 1 and GameState.club_standing.values().any(
				func(s): return int(s["authority"]) != int(s["base"][1])):
			break
	var clubs: Dictionary = GameState.club_standing
	_check(clubs.size() >= 16 and not clubs.has("GEE"),
			"Every rival club's senior coach has a standing of his own (%d)" % clubs.size())
	var moved := false
	for code in clubs:
		var s: Dictionary = clubs[code]
		_check(s.has("respect") and s.has("authority") and (s.get("side", []) as Array).size() >= 22,
				"%s's standing follows its side" % code)
		var arch := Promises._arch_p(str(code))
		_check(s["base"] == Promises.base_for(arch), "%s's base is its own archetype's (%s)" % [code, arch])
		if int(s["authority"]) != int(s["base"][1]):
			moved = true
	_check(moved, "Rival coaches' drops move their Authority, as yours do")


func _test_card_game_and_board_win() -> void:
	_fresh()
	var p := _kid(_spare(), 30)
	var id := str(p["id"])
	ClubStories._apply(GameState, {"op": "expects_game", "sting": 12}, p, {}, {})
	_check(p.has("expects_game"), "(setup) the card's op promises him the game")
	var w := Promises.word(GameState)
	_check(int(w["made"]) == 1, "A card's game this week is a promise made (%s)" % str(w))
	var owed := Promises.of(GameState, id)
	_check(owed.size() == 1 and str(owed[0]["kind"]) == "game", "...and reads as one (%s)" % str(owed))
	_advance_mine()
	_check(int(w["kept"]) + int(w["broken"]) == 1, "Settled by the match, once (%s)" % str(w))
	_check(int(w["kept"]) == 1 if _played_last(id) else int(w["broken"]) == 1, "...kept if he played, broken if not")
	_fresh()
	w = Promises.word(GameState)
	ClubStories._apply(GameState, {"op": "promise_win"}, {}, {}, {})
	var r0 := Promises.respect(GameState)
	_advance_mine()
	_check(int(w["made"]) == 1 and int(w["kept"]) + int(w["broken"]) == 1,
			"A win promised to the board is in the record, settled by the result (%s)" % str(w))
	_check(Promises.respect(GameState) == r0, "A promise to the board moves no Respect with the players")


func _played_last(id: String) -> bool:
	return (Promises.standing(GameState).get("side", []) as Array).has(id)


func _test_season_settles_and_saves() -> void:
	_fresh()
	var s := Promises.standing(GameState, true)
	var base: Array = s["base"]
	s["respect"] = int(base[0]) + 20
	s["authority"] = int(base[1]) - 20
	Promises.season_end(GameState)
	_check(int(s["respect"]) == int(base[0]) + 15 and int(s["authority"]) == int(base[1]) - 15,
			"Between seasons the scores settle a quarter of the way back to base (%s)" % str(s))
	Promises.made(GameState, GameState.my_list[0], "run")
	var state := GameState._save_state()
	_check(state.has("coach_word") and state.has("coach_standing") and state.has("club_standing"),
			"The record and every club's standing are saved")
	var word: Dictionary = GameState.coach_word.duplicate(true)
	GameState.save_career()
	GameState.reset()
	_check(GameState.coach_word.is_empty(), "(setup) reset clears it")
	GameState.load_career()
	_check(GameState.coach_word == word and int(GameState.coach_standing.get("respect", -1)) == int(s["respect"]),
			"...and load back as they were")
