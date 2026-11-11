extends RefCounted
## The concussion medical panel (director, 2026-11-11: "if a player gets 5 or
## more concussions within a 5 year period, they should have to pass a medical
## retirement check"; flat odds each time; straight after the fifth).
## The count over a moving five-season window, no sitting at four, a sitting at
## five and at each one after, flat seeded odds, a failed sitting ends the
## career that week for any club, the coach is told with the odds, an old save
## loads, and no other dice move. Run through tests/run_medical_panel_tests.gd.

var failures: Array[String] = []
var checks := 0

## Every season here is seeded: a clock seed makes a different league each run.
const SUITE_SEED := 4411


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	GameDB.reload()
	_t("_test_window_moves")
	_t("_test_flat_odds")
	_t("_test_shown_percentage")
	_t("_test_no_sitting_at_four")
	_t("_test_sits_at_five_and_each_after")
	_t("_test_not_cleared_ends_career")
	_t("_test_rivals_get_it")
	_t("_test_through_a_round")
	_t("_test_old_save_loads")
	_t("_test_no_other_dice_move")
	GameState.replay_seed = 0
	print(Ran.line("Medical panel", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _career(club := "FRE") -> void:
	GameState.reset()
	GameState.career_seed = SUITE_SEED
	GameState.start_season(club, GameDB.club_list(club))
	GameState.last_label = "Round 3"


## `n` concussions on his record, one a season, the latest `back` seasons ago.
func _past(p: Dictionary, n: int, back := 1) -> void:
	for i in range(n):
		CareerFacts.add(GameState.career_facts, str(p["id"]), CareerFacts.row(
				GameState.season_year - back - i, "Round 9", "injury", str(p.get("club", "")), "", "concussion"))


## A concussion this week, as the match's injuries hand it on.
func _concuss(p: Dictionary, club: String) -> void:
	p["injury_weeks"] = Injuries.CONCUSSION_MIN
	p["injury_kind"] = "concussion"
	GameState._log_injuries([{"id": str(p["id"]), "club": club, "weeks": Injuries.CONCUSSION_MIN,
			"kind": "concussion"}], GameState.last_label)


## A player of `club` whose sitting on concussion number `nth` of his career
## goes the way asked (and the next one too, when `then` is given).
func _pick(club: String, nth: int, want: bool, then = null) -> Dictionary:
	for p in GameState.season.lists[club]:
		var id := str(p["id"])
		if GameState.career_facts.has(id):
			continue
		if MedicalPanel.cleared(GameState.career_seed, id, GameState.season_year, nth) != want:
			continue
		if then != null and MedicalPanel.cleared(GameState.career_seed, id, GameState.season_year, nth + 1) != then:
			continue
		return p
	return {}


func _medical_news() -> Array:
	return GameState.news.filter(func(n): return str(n.get("kind", "")) == "medical")


func _on_a_list(id: String) -> bool:
	for arr in [GameState.my_list] + GameState.season.lists.values() + GameState.league_lists.values():
		for p in arr:
			if str(p.get("id", "")) == id:
				return true
	return false


func _test_window_moves() -> void:
	var store := {}
	for y in [2026, 2027, 2028, 2029, 2030]:
		CareerFacts.add(store, "a", CareerFacts.row(y, "Round 2", "injury", "FRE", "", "concussion"))
	CareerFacts.add(store, "a", CareerFacts.row(2030, "Round 5", "injury", "FRE", "", "hamstring"))
	CareerFacts.add(store, "a", CareerFacts.row(2030, "Round 7", "injury", "FRE", "", ""))
	_check(MedicalPanel.count(store, "a", 2030) == 5,
			"Five concussions in this season and the four before all count (%d)" % MedicalPanel.count(store, "a", 2030))
	_check(MedicalPanel.count(store, "a", 2031) == 4,
			"A season on, the one from six seasons ago no longer counts (%d)" % MedicalPanel.count(store, "a", 2031))
	_check(MedicalPanel.count(store, "a", 2035) == 0 and MedicalPanel.count_ever(store, "a") == 5,
			"Five seasons on none of them count, though all five stay on his record")
	_check(MedicalPanel.count(store, "nobody", 2030) == 0, "A player with no record has had none")
	_check(MedicalPanel.count(store, "a", 2029) == 4, "A concussion from a later season is not counted early")
	_check(not MedicalPanel.sits(4) and MedicalPanel.sits(5) and MedicalPanel.sits(7),
			"The panel sits at five and above, never at four")


func _test_flat_odds() -> void:
	var by_nth := {}
	var all := 0
	var total := 0
	for nth in [5, 6, 9]:
		var ok := 0
		for i in range(4000):
			if MedicalPanel.cleared(SUITE_SEED + i % 7, "p%d" % i, 2026 + i % 5, nth):
				ok += 1
		by_nth[nth] = float(ok) / 4000.0
		all += ok
		total += 4000
	var share := float(all) / float(total)
	_check(absf(share - MedicalPanel.CLEAR_CHANCE) < 0.02,
			"Over %d sittings the share cleared is the stated chance (%.3f against %.2f)" % [
					total, share, MedicalPanel.CLEAR_CHANCE])
	for nth in by_nth:
		_check(absf(float(by_nth[nth]) - MedicalPanel.CLEAR_CHANCE) < 0.03,
				"The odds are flat: sitting on concussion %d clears %.3f" % [nth, by_nth[nth]])
	var same := true
	for i in range(200):
		if MedicalPanel.cleared(77, "p%d" % i, 2030, 5) != MedicalPanel.cleared(77, "p%d" % i, 2030, 5):
			same = false
	_check(same, "The same career, player, season and concussion always gets the same answer")


func _test_shown_percentage() -> void:
	var pct := "%d%%" % int(round(MedicalPanel.CLEAR_CHANCE * 100.0))
	_check(MedicalPanel.warning(2) == "" and MedicalPanel.warning(0) == "",
			"Below %d the count is not shown" % MedicalPanel.SHOWN_FROM)
	_check(MedicalPanel.warning(4).contains(pct) and MedicalPanel.warning(4).begins_with("4 concussions in 5 years. One more"),
			"At four the line says one more brings the panel, with the chance: %s" % MedicalPanel.warning(4))
	_check(MedicalPanel.warning(3).contains("Two more") and MedicalPanel.warning(3).contains(pct),
			"At three it says two more: %s" % MedicalPanel.warning(3))
	_check(MedicalPanel.warning(5).contains("sits again") and MedicalPanel.warning(5).contains(pct),
			"At five it says another one brings it again: %s" % MedicalPanel.warning(5))
	for cleared in [true, false]:
		var row := {"name": "Sam Hale", "count": 5, "cleared": cleared, "pct": MedicalPanel.clear_pct()}
		_check(MedicalPanel.result_line(row).contains(pct) and MedicalPanel.result_short(row).contains(pct),
				"The week's result states the chance (%s)" % MedicalPanel.result_short(row))
		_check(MedicalPanel.result_line(row).begins_with("Sam Hale had his 5th concussion in 5 years"),
				"It opens on his name and the count: %s" % MedicalPanel.result_line(row))
	# The sheet shows the same line for a player on four.
	_career()
	var p: Dictionary = GameState.my_list[0]
	_past(p, 4)
	var host := Control.new()
	host.size = Vector2(390, 844)
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.add_child(host)
	var sheet := PlayerSheet.open(host, p)
	var label := host.find_child("ProfileConcussions", true, false) as Label
	_check(label != null and label.text == MedicalPanel.warning(4) and label.text.contains(pct),
			"The player sheet shows it: %s" % (label.text if label != null else "no line"))
	if sheet != null and is_instance_valid(sheet):
		sheet.queue_free()
	host.queue_free()
	var clean: Dictionary = GameState.my_list[1]
	var host2 := Control.new()
	host2.size = Vector2(390, 844)
	tree.root.add_child(host2)
	PlayerSheet.open(host2, clean)
	_check(host2.find_child("ProfileConcussions", true, false) == null,
			"A player with none has no such line")
	host2.queue_free()


func _test_no_sitting_at_four() -> void:
	_career()
	var p: Dictionary = GameState.my_list[2]
	_past(p, 3)
	_concuss(p, "FRE")
	_check(GameState.concussions_in_window(p) == 4, "He is on four in five years")
	_check(GameState.last_medical.is_empty() and _medical_news().is_empty() and _on_a_list(str(p["id"])),
			"Four brings no sitting and no news; he stays on the list")
	_check(int(p.get("injury_weeks", 0)) == Injuries.CONCUSSION_MIN, "He serves the normal protocol")
	# Five on his record, but one of them six seasons ago: still no sitting.
	var q: Dictionary = GameState.my_list[3]
	_past(q, 3)
	CareerFacts.add(GameState.career_facts, str(q["id"]), CareerFacts.row(
			GameState.season_year - 5, "Round 1", "injury", "FRE", "", "concussion"))
	_concuss(q, "FRE")
	_check(MedicalPanel.count_ever(GameState.career_facts, str(q["id"])) == 5
			and GameState.concussions_in_window(q) == 4 and GameState.last_medical.is_empty(),
			"Five in six seasons is four in the window: no sitting")
	# Other injuries never count.
	var r: Dictionary = GameState.my_list[4]
	_past(r, 4)
	GameState._log_injuries([{"id": str(r["id"]), "club": "FRE", "weeks": 3, "kind": "hamstring"}], "Round 3")
	_check(GameState.last_medical.is_empty(), "A hamstring on top of four concussions brings no sitting")


func _test_sits_at_five_and_each_after() -> void:
	_career()
	var p := _pick("FRE", 5, true, true)
	_check(not p.is_empty(), "A Fremantle player the panel clears twice exists in this seed")
	if p.is_empty():
		return
	var id := str(p["id"])
	_past(p, 4)
	_concuss(p, "FRE")
	_check(GameState.last_medical.size() == 1 and int(GameState.last_medical[0]["count"]) == 5
			and bool(GameState.last_medical[0]["cleared"]),
			"The fifth in five years brings the panel that week: %s" % [GameState.last_medical])
	_check(_on_a_list(id) and int(p.get("injury_weeks", 0)) == Injuries.CONCUSSION_MIN
			and not GameState.departed_names.has(id),
			"Cleared, he stays on the list and serves the normal protocol")
	var news := _medical_news()
	_check(news.size() == 1 and str(news[0]["text"]).contains("cleared him to play on")
			and str(news[0]["text"]).contains("%d%%" % MedicalPanel.clear_pct())
			and str(news[0]["text"]).begins_with(GameDB.player_display_name(p)),
			"The coach is told that week, with the chance: %s" % [news])
	_check(GameState.my_medical_lines().size() == 1
			and str(GameState.my_medical_lines()[0]).contains("cleared to play on"),
			"The week's injury surface carries it: %s" % [GameState.my_medical_lines()])
	# The next one is another sitting at the same odds.
	p["injury_weeks"] = 0
	_concuss(p, "FRE")
	_check(GameState.last_medical.size() == 2 and int(GameState.last_medical[1]["count"]) == 6
			and int(GameState.last_medical[1]["pct"]) == MedicalPanel.clear_pct(),
			"A sixth brings the panel again at the same stated chance")
	_check(_medical_news().size() == 2 and _on_a_list(id), "Cleared again, he plays on")
	# A week later the surface no longer repeats it.
	GameState.last_label = "Round 4"
	_check(GameState.my_medical_lines().is_empty(), "Next week the notice is gone")


func _test_not_cleared_ends_career() -> void:
	_career()
	var p := _pick("FRE", 5, false)
	_check(not p.is_empty(), "A Fremantle player the panel does not clear exists in this seed")
	if p.is_empty():
		return
	var id := str(p["id"])
	var who := GameDB.player_display_name(p)
	var before := GameState.my_list.size()
	_past(p, 4)
	_concuss(p, "FRE")
	_check(GameState.last_medical.size() == 1 and not bool(GameState.last_medical[0]["cleared"]),
			"The panel sat and did not clear him")
	_check(not _on_a_list(id) and GameState.my_list.size() == before - 1
			and (GameState.season.lists["FRE"] as Array).size() == before - 1,
			"He is off every list that week and the list is one short (%d of %d)" % [GameState.my_list.size(), before])
	_check(GameState.departed_names.has(id) and int(p.get("contract_years", -1)) == 0
			and not p.has("injury_weeks"),
			"His career is over through the career-over path: his name is kept, his contract ends")
	var news := _medical_news()
	_check(news.size() == 1 and str(news[0]["text"]).begins_with(who)
			and str(news[0]["text"]).contains("did not clear him")
			and str(news[0]["text"]).contains("%d%% chance of being cleared" % MedicalPanel.clear_pct())
			and str(news[0].get("club", "")) == "FRE",
			"The coach is told that week, with the chance: %s" % [news])
	_check(GameState.my_medical_lines().size() == 1
			and str(GameState.my_medical_lines()[0]).contains("not cleared, career over"),
			"The week's injury surface carries it: %s" % [GameState.my_medical_lines()])
	var story := NewsFront.story(news[0], "FRE")
	_check(str(story.get("headline", "")).contains(who) and str(story.get("headline", "")).contains("career"),
			"The news front leads with it: %s" % story.get("headline", ""))
	# The list is still a list a side can be picked from, and the season plays on.
	var picked := Ratings.select_side(GameState.my_list, {"MID": [id]})
	var side: Array = (picked["ground"] as Array) + (picked["bench"] as Array)
	var has_him := side.any(func(s): return str(s.get("id", "")) == id)
	_check(side.size() >= 22 and not has_him,
			"A full side is picked without him, even when he is still named (%d)" % side.size())
	var round_before := GameState.season.round_index
	GameState.advance()
	_check(GameState.season.round_index == round_before + 1 and not _on_a_list(id),
			"The next round plays with the list a player short")
	_check(GameState.save_career() and GameState.load_career() and not _on_a_list(id)
			and GameState.departed_names.has(id),
			"Saved and loaded, he is still retired")
	GameState.delete_saved_career()


func _test_rivals_get_it() -> void:
	_career()
	var rival := "MEL"
	var p := _pick(rival, 5, false)
	_check(not p.is_empty(), "A Melbourne player the panel does not clear exists in this seed")
	if p.is_empty():
		return
	var id := str(p["id"])
	var who := GameDB.player_display_name(p)
	var before := (GameState.season.lists[rival] as Array).size()
	_past(p, 4)
	_concuss(p, rival)
	_check(not _on_a_list(id) and (GameState.season.lists[rival] as Array).size() == before - 1
			and GameState.departed_names.has(id),
			"A rival's player who is not cleared is retired the same way")
	var news := _medical_news()
	_check(news.size() == 1 and str(news[0]["text"]).contains(who)
			and str(news[0]["text"]).contains(GameDB.club_name(rival))
			and str(news[0]["text"]).contains("played his last game"),
			"League news carries a rival's medical retirement: %s" % [news])
	_check(GameState.my_medical_lines().is_empty(), "It is not listed among your own players' sittings")
	# A rival who is cleared plays on at his club.
	var q := _pick(rival, 5, true)
	if not q.is_empty():
		_past(q, 4)
		_concuss(q, rival)
		_check(_on_a_list(str(q["id"])) and GameState.last_medical.size() == 2
				and bool(GameState.last_medical[1]["cleared"]),
				"A rival's player who is cleared plays on")
	var theirs := Ratings.select_side(GameState.season.lists[rival])
	_check((theirs["ground"] as Array).size() + (theirs["bench"] as Array).size() >= 22,
			"The rival still fields a full side")


## The round's own path: the match hands on a concussion, the panel sits once
## the round is counted, and a retired player is not among the week's injured.
func _test_through_a_round() -> void:
	_career()
	var p := _pick("FRE", 5, false)
	var q := _pick("FRE", 5, true)
	_check(not p.is_empty() and not q.is_empty(), "One player for each answer exists in this seed")
	if p.is_empty() or q.is_empty():
		return
	_past(p, 4)
	_past(q, 4)
	var res := {"home": "FRE", "away": "MEL", "round": 2, "label": "Round 3", "injuries": [
			{"side": 0, "id": str(p["id"]), "weeks": 2, "kind": "concussion"},
			{"side": 0, "id": str(q["id"]), "weeks": 2, "kind": "concussion"}]}
	GameState._process_injuries([res])
	_check(GameState.last_medical.size() == 2, "Both fifth concussions bring the panel (%d)" % GameState.last_medical.size())
	var hurt := GameState.last_injuries.map(func(r): return str(r["id"]))
	_check(hurt.has(str(q["id"])) and not hurt.has(str(p["id"])),
			"The cleared player is among the week's injured; the retired one is not")
	_check(_on_a_list(str(p["id"])), "He is still on the list while the round is being counted")
	GameState._settle_medical()
	_check(not _on_a_list(str(p["id"])) and _on_a_list(str(q["id"])),
			"Once the round is counted he is gone and the cleared player stays")
	_check(GameState.my_medical_lines().size() == 2, "Both sittings are on the week's surface")
	# The next round's injuries clear last week's sittings.
	GameState._process_injuries([{"home": "FRE", "away": "MEL", "round": 3, "label": "Round 4", "injuries": []}])
	_check(GameState.last_medical.is_empty(), "Next round starts with no sittings")


const OLD_SAVE_FIXTURE := "res://tests/fixtures/career_v1_2026-09-30.save.gz"


func _test_old_save_loads() -> void:
	# A real save from the 2026-09-30 build: no sittings, nobody near the panel.
	GameState.delete_saved_career()
	var gz := FileAccess.get_file_as_bytes(OLD_SAVE_FIXTURE)
	var raw := gz.decompress_dynamic(-1, FileAccess.COMPRESSION_GZIP)
	var f := FileAccess.open(GameState.save_path, FileAccess.WRITE)
	f.store_buffer(raw)
	f.close()
	GameState.reset()
	_check(GameState.load_career(), "The older save opens")
	var most := 0
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			most = maxi(most, GameState.concussions_in_window(p))
	_check(GameState.last_medical.is_empty() and most == 0 and GameState.my_medical_lines().is_empty(),
			"It has no sittings and nobody has a counted concussion (most %d)" % most)
	GameState.advance()
	_check(GameState.season.round_index == 3, "It keeps playing")
	GameState.delete_saved_career()
	# An injury an older save kept as a bare year has no kind: never a concussion.
	_career()
	var p: Dictionary = GameState.my_list[0]
	p["injury_log"] = [GameState.season_year, GameState.season_year, GameState.season_year,
			GameState.season_year - 1, GameState.season_year - 1, GameState.season_year - 2]
	_check(GameState.save_career() and GameState.load_career(), "A career with an old injury record saves and loads")
	p = GameState.list_player(str(p["id"]))
	_check(GameState.concussions_in_window(p) == 0 and MedicalPanel.warning(GameState.concussions_in_window(p)) == "",
			"Six old injuries with no kind recorded are not concussions")
	# A save written before the panel has no last_medical; one written after keeps it.
	var state: Dictionary = GameState._save_state()
	state.erase("last_medical")
	_check(GameState._restore_career(state) and GameState.last_medical.is_empty(),
			"A save without the key loads with no sittings")
	var q := _pick("FRE", 5, true)
	if not q.is_empty():
		_past(q, 4)
		_concuss(q, "FRE")
		_check(GameState.save_career() and GameState.load_career() and GameState.last_medical.size() == 1
				and GameState.my_medical_lines().size() == 1 and GameState.concussions_in_window(GameState.list_player(str(q["id"]))) == 5,
				"The week's sitting and his count survive a save and load")
	GameState.delete_saved_career()


## The panel draws from its own seeded dice: the shared dice and a seeded
## season's results are the same whether or not it sits.
func _test_no_other_dice_move() -> void:
	seed(9001)
	var plain := [randi(), randi(), randi()]
	seed(9001)
	var with := []
	for i in range(3):
		MedicalPanel.cleared(SUITE_SEED, "p%d" % i, 2030, 5)
		with.append(randi())
	_check(plain == with, "A sitting leaves the shared dice where they were")
	# Two identical seeded careers; in the second, every player the panel would
	# clear is one concussion from it, so it sits (and clears) through the
	# rounds. Until a sitting retires someone (a different list from then on)
	# every result must be identical.
	var a := _rounds(false)
	var b := _rounds(true)
	var compared := 0
	var sat_before := false
	for i in range(mini(a["results"].size(), b["results"].size())):
		if int(b["retired_before"][i]) > 0:
			break
		_check(a["results"][i] == b["results"][i], "Round %d is identical with the panel sitting" % (i + 1))
		compared += 1
		if int(b["sat_before"][i]) > 0:
			sat_before = true
	_check(compared >= 1, "At least one round was compared (%d)" % compared)
	_check(int(a["sat"]) == 0, "Nobody was near the panel in the plain career (%d sittings)" % int(a["sat"]))
	_check(sat_before, "A round after a sitting was compared (sittings %d, compared %d)" % [int(b["sat"]), compared])
	print("  no-other-dice: compared %d rounds, sittings in the loaded career %d, a compared round followed a sitting: %s" % [
			compared, int(b["sat"]), sat_before])


func _rounds(loaded: bool) -> Dictionary:
	GameState.reset()
	GameState.career_seed = SUITE_SEED
	GameState.replay_seed = SUITE_SEED
	GameState.start_season("FRE", GameDB.club_list("FRE"))
	if loaded:
		for code in GameState.season.lists:
			for p in GameState.season.lists[code]:
				if MedicalPanel.cleared(GameState.career_seed, str(p["id"]), GameState.season_year, 5):
					_past(p, 4)
	var out := {"results": [], "sat_before": [], "retired_before": [], "sat": 0}
	var sat := 0
	var retired := 0
	for i in range(6):
		out["sat_before"].append(sat)
		out["retired_before"].append(retired)
		GameState.advance()
		out["results"].append(var_to_str(GameState.last_results.map(func(r): return [
				r.get("home"), r.get("away"), r.get("score"), r.get("injuries")])))
		for row in GameState.last_medical:
			sat += 1
			if not bool(row["cleared"]):
				retired += 1
	out["sat"] = sat
	return out
