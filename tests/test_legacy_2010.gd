extends RefCounted
## The 2010 start (Legacy mode, TODO row 142: "then the 2000, 2010 and 2020
## starts"): a career starts at a real 2010 club on its real list, rated on
## 2009, takes over from that club's real 2010 senior coach, plays the season
## and rolls into 2011, where Gold Coast enter as the sim's own expansion.
## Run through tests/run_legacy_2010_tests.gd.

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 2010
const CLUB := "STK"


func run() -> void:
	failures.clear()
	checks = 0
	_t("_test_the_2010_row")
	_t("_test_start_2010")
	_t("_test_rolls_into_2011")
	GameState.reset()
	print("legacy_2010: %d checks, %d failures" % [checks, failures.size()])
	for f in failures:
		print("  FAIL: " + f)


func _t(name: String) -> void:
	call(name)


func _check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures.append(what)
		push_error(what)


func _test_the_2010_row() -> void:
	_check(Datasets.ready("2010") and Datasets.ready_ids().has("2010"),
			"The year step offers 2010 (%s)" % str(Datasets.ready_ids()))
	var row := Datasets.get_set("2010")
	_check(int(row.get("data_season", 0)) == 2009 and int(row.get("start_year", 0)) == 2010,
			"2010's lists are rated on 2009 and the first season is 2010")
	for key in Datasets.FILE_KEYS:
		var path := Datasets.file("2010", key)
		_check(path == "" or FileAccess.file_exists(path), "2010's %s file ships (%s)" % [key, path])


## A 2010 career at CLUB, as Choose your club starts it; returns the ids of
## the club's real 2010 list.
func _start() -> Dictionary:
	GameState.reset("2010")
	GameState.replay_seed = SUITE_SEED
	GameState.career_seed = SUITE_SEED
	GameState.begin_real_lists()
	var want := {}
	for p in GameDB.club_list(CLUB) + GameDB.club_additions(CLUB):
		want[str(p["id"])] = true
	GameState.choose_real_club(CLUB)
	var guard := 0
	while GameState.draft != null and not GameState.draft.is_finished() and guard < 400:
		guard += 1
		if GameState.draft.is_user_turn():
			var board: Array = GameState.draft.board("", "", "", "overall", true)
			if board.is_empty() or not GameState.draft.pick(board[0]):
				break
	GameState.finish_intake_draft()
	return want


func _coach(name: String) -> Dictionary:
	for cid in GameState.coaches:
		if str(GameState.coaches[cid].get("real_name", "")) == name:
			return GameState.coaches[cid]
	return {}


func _test_start_2010() -> void:
	var want := _start()
	_check(GameState.season != null and GameState.season_year == 2010 and GameState.my_club == CLUB,
			"A 2010 career starts in 2010 at St Kilda (%d, %s)" % [GameState.season_year, GameState.my_club])
	_check(GameState.season.clubs.size() == 16 and not GameState.season.clubs.has("GCS")
			and not GameState.season.clubs.has("GWS"),
			"Sixteen clubs play 2010, no Gold Coast or GWS yet (%d)" % GameState.season.clubs.size())
	var mine := {}
	for p in GameState.my_list:
		mine[str(p["id"])] = true
	var missing := 0
	for id in want:
		if not mine.has(id):
			missing += 1
	_check(want.size() >= 40 and missing <= 3,
			"St Kilda start on their real 2010 list (%d of %d on it)" % [want.size() - missing, want.size()])
	var names := {}
	for p in GameState.my_list:
		names[str(p.get("name", ""))] = int(p.get("overall", 0))
	_check(names.has("Nick Riewoldt") and names.has("Lenny Hayes"),
			"Riewoldt and Hayes are on it")
	# Rated on 2009: Gary Ablett, the 2009 Brownlow medallist, is among the best.
	var ablett := 0
	var better := 0
	for p in (GameState.season.lists["GEE"] as Array):
		if str(p.get("name", "")) == "Gary Ablett":
			ablett = int(p.get("overall", 0))
	for club in GameState.season.clubs:
		for p in (GameState.season.lists[club] as Array):
			if int(p.get("overall", 0)) > ablett:
				better += 1
	_check(ablett >= 80 and better <= 10, "Gary Ablett rates among the league's best (%d, %d above him)" % [ablett, better])
	# You replace Ross Lyon; the other fifteen keep their real senior coach.
	var lyon := _coach("Ross Lyon")
	_check(not lyon.is_empty() and str(lyon.get("status", "")) == "free" and str(lyon.get("club", "")) == "",
			"You replace Ross Lyon, and he is in the coach pool (%s)" % str(lyon.get("status", "missing")))
	var real_sc := 0
	for club in GameState.season.clubs:
		if club == CLUB:
			continue
		var cid := str(Coaches.staff(GameState.coaches, club).get("SC", ""))
		if cid != "" and str(GameState.coaches[cid].get("real_name", "")) != "":
			real_sc += 1
	_check(real_sc == 15, "The other 15 clubs keep their real 2010 senior coach (%d)" % real_sc)
	var pad := str(Coaches.staff(GameState.coaches, "PAD").get("SC", ""))
	_check(pad != "" and str(GameState.coaches[pad].get("real_name", "")) == "Mark Williams",
			"Port Adelaide's is Mark Williams, who began 2010 in the job")
	# Rated from their records before 2010 (director 2026-11-13, "Rate from records").
	var mick := _coach("Mick Malthouse")
	var hardwick := _coach("Damien Hardwick")
	_check(int(mick.get("skills", {}).get("tactics", 0)) > int(hardwick.get("skills", {}).get("tactics", 0)),
			"Malthouse's record rates above first-year Hardwick's (%d vs %d)" % [
				int(mick.get("skills", {}).get("tactics", 0)), int(hardwick.get("skills", {}).get("tactics", 0))])
	var caps := 0
	for club in GameState.season.clubs:
		for p in (GameState.season.lists[club] as Array):
			if Leadership.role_2026(p) == "captain":
				caps += 1
	_check(caps >= 15, "The clubs' real 2010 captains carry the armband's record (%d)" % caps)


func _test_rolls_into_2011() -> void:
	_start()
	var guard := 0
	while not GameState.season.is_season_over() and guard < 60:
		guard += 1
		GameState.advance()
	_check(GameState.season.is_season_over(), "The 2010 season plays out (%d weeks)" % guard)
	_check(GameState.start_next_season(), "The 2010 career rolls on")
	_check(GameState.season_year == 2011 and GameState.my_club == CLUB and GameDB.dataset_id == "2010",
			"It is 2011 at St Kilda, still the career begun in 2010 (%d, %s, set %s)" % [
				GameState.season_year, GameState.my_club, GameDB.dataset_id])
	_check(GameState.season.clubs.has("GCS") and not GameState.season.clubs.has("GWS")
			and GameState.season.clubs.size() == 17,
			"Gold Coast enter in 2011, GWS not yet (%d clubs)" % GameState.season.clubs.size())
	var gcs: Array = GameState.season.lists.get("GCS", [])
	_check(gcs.size() >= 30, "Gold Coast have a list (%d)" % gcs.size())
	_check(Coaches.staff(GameState.coaches, CLUB).get("SC", "") == "", "St Kilda's senior job is still yours")
