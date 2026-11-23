extends SceneTree
## Legacy lore audit: start a career in a past year, play every week of N
## seasons as Sim the week plays them, and write what the game shows about
## each season to a text report (clubs, names, grounds, guernseys, rules,
## finals, awards, coaches, every news story), so a reader can check each
## season against the real one.
##
##   godot --headless --path . --script tools/audit/legacy_lore_audit.gd -- 1990 WBD 3 out.txt

var out: FileAccess
var GS
var DB
var seen_news := {}


func _initialize() -> void:
	_run.call_deferred()


func _w(s: String) -> void:
	out.store_line(s)


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var start := str(args[0]) if args.size() > 0 else "1990"
	var club := str(args[1]) if args.size() > 1 else "WBD"
	var seasons := int(args[2]) if args.size() > 2 else 2
	var path := str(args[3]) if args.size() > 3 else "user://legacy_audit_%s.txt" % start
	GS = root.get_node("GameState")
	DB = root.get_node("GameDB")
	GS.autosave_enabled = false
	GS.save_path = "user://audit_career.save"
	GS.settings_path = "user://audit_settings.cfg"
	out = FileAccess.open(path, FileAccess.WRITE)
	GS.reset(start)
	GS.replay_seed = int(start)
	GS.career_seed = int(start)
	GS.begin_real_lists()
	GS.choose_real_club(club)
	_finish_draft()
	GS.finish_intake_draft()
	for n in range(seasons):
		_season()
		if n == seasons - 1:
			break
		var y: int = GS.season_year
		_w("\n== OFF-SEASON %d ==" % y)
		if GS.begin_intake_draft():
			_finish_draft()
			GS.finish_intake_draft()
		else:
			GS.start_next_season()
		_news()
		if GS.season_year == y:
			_w("!! year did not roll on")
			break
	out.close()
	quit(0)


func _finish_draft() -> void:
	var guard := 0
	while GS.draft != null and not GS.draft.is_finished() and guard < 4000:
		guard += 1
		if GS.draft.is_user_turn():
			if not GS.draft.pick_for_me():
				var board: Array = GS.draft.board("", "", "", "overall", true)
				if board.is_empty() or not GS.draft.pick(board[0]):
					GS.draft._skip_current_pick()
		else:
			GS.draft.auto_until_user_turn()


func _news() -> void:
	var fresh := []
	for item in GS.news:
		var key := "%s|%s|%s" % [item.get("year", ""), item.get("when", ""), item.get("text", "")]
		if seen_news.has(key):
			continue
		seen_news[key] = true
		fresh.push_front(item)
	for item in fresh:
		_w("  NEWS [%s %s %s] %s" % [item.get("year", ""), item.get("when", ""), item.get("kind", ""), item.get("text", "")])


func _season() -> void:
	var s = GS.season
	var y: int = GS.season_year
	_w("\n\n######## SEASON %d (season.year %d, era_year %d) ########" % [y, s.year, DB.era_year])
	_w("rules: rounds %d games %d finalists %d format %s gf %s gather %d" % [s.regular_rounds(), s.games_per_club(),
			s.finalists(), s.finals_format(), s.grand_final_venue(), s.gather_round()])
	_w("era: list_max %d senior %d catA %d catB %d min %d interchange %d subs %d rookie %s FA %s cap %d" % [
			EraRules.list_max(), EraRules.senior_spots(), EraRules.cat_a_spots(), EraRules.cat_b_spots(),
			EraRules.list_min(), EraRules.interchange(), EraRules.substitutes(), str(EraRules.on("rookie_list")),
			str(EraRules.on("free_agency")), GS.salary_cap])
	_w("clubs (%d):" % s.clubs.size())
	var staff := {}
	for cid in GS.coaches:
		var c: Dictionary = GS.coaches[cid]
		if str(c.get("status", "")) == "club" and str(c.get("job", "")) == "SC":
			staff[str(c["club"])] = str(c.get("real_name", ""))
	for code in s.clubs:
		var c: Dictionary = DB.club(code)
		_w("  %s | %s | short %s | ground %s -> %s | guernsey %s | list %d | SC %s" % [code, DB.club_name(code),
				c.get("short", ""), s.home_ground(code), DB.ground_shown(s.home_ground(code), y), c.get("guernsey", ""),
				(s.lists[code] as Array).size(), staff.get(code, "(you)" if code == GS.my_club else "?")])
	# Grounds used this season.
	var venues := {}
	for ri in range(s.fixture.size()):
		for m in s.fixture[ri]:
			var v: String = s.round_venue(ri, str(m["home"]), str(m["away"]))
			var shown: String = DB.ground_shown(v, y)
			venues["%s -> %s" % [v, shown]] = int(venues.get("%s -> %s" % [v, shown], 0)) + 1
	_w("venues: %s" % str(venues))
	_w("real fixture: %s; round 1: %s" % [str(s.is_real_fixture()), str(s.fixture[0]).left(400)])
	_news()
	var guard := 0
	while not s.is_season_over() and guard < 60:
		guard += 1
		var phase: String = GS.advance()
		if GS.last_phase == "finals" or GS.last_phase == "done":
			for r in GS.last_results:
				_w("  FINAL %s: %s v %s at %s" % [r.get("label", ""), r.get("home", ""), r.get("away", ""),
						DB.ground_shown(str(r.get("venue", r.get("ground", ""))), y)])
		_w(" -- %s (%s)" % [GS.last_label, phase])
		_news()
		if phase == "done":
			break
	var lad: Array = s.ladder_sorted()
	var ltxt := []
	for row in lad:
		ltxt.append(str(row["code"]))
	_w("ladder: %s" % ", ".join(ltxt))
	_w("premier: %s runner-up %s" % [GS.premier(), s.finals.get("runner_up", "")])
	_w("awards keys: %s" % str(GS.season_awards.keys()))
	for k in GS.season_awards:
		_w("  AWARD %s: %s" % [k, str(GS.season_awards[k]).left(300)])
	if not GS.honour_roll.is_empty():
		_w("honour: %s" % str(GS.honour_roll[-1]).left(800))
	_w("year_events: %s" % str(GS.year_events).left(1500))
