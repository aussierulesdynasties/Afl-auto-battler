extends RefCounted
const Ovr := preload("res://tests/ovr.gd")
## Training plans and the stat guide: plans spend a player's XP after every
## game (there is no Manual: cut 2026-11-03), single-stat focus touches only that stat, changing a
## plan spends banked XP at once, the club plan applies to anyone without his
## own, plans survive a save, and every stat has a full guide entry. Stat
## focus (row 97): one stat focus a season, locked until the next
## season opens, about a third of his training; old saves keep one focus.
## Run through tests/run_training_tests.gd.

var failures: Array[String] = []
var checks := 0

## Every season and draft here is seeded (C15): a clock seed makes a different
## league each run.
const SUITE_SEED := 2027


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	GameDB.reload()
	_t("_test_default_plan_spends")
	_t("_test_focus")
	_t("_test_changing_plans")
	_t("_test_plans_survive_save")
	_t("_test_plans_match_the_engine")
	_t("_test_archetypes_differ")
	_t("_test_traits_through_training")
	_t("_test_old_plans_migrate")
	_t("_test_training_news")
	_t("_test_reserves_development")
	_t("_test_department_development")
	_t("_test_stat_guide_complete")
	_t("_test_dual_role_plans")
	_t("_test_training_multiselect")
	_t("_test_plan_is_not_identity")
	_t("_test_learning_a_position")
	_t("_test_unicorn")
	_t("_test_rival_projects")
	_t("_test_project_endings")
	_t("_test_pass_margin_tightened")
	_t("_test_retraining_is_additive")
	_t("_test_season_record")
	_t("_test_teaching_moves_the_ceiling")
	_t("_test_stat_focus_once_a_season")
	_t("_test_stat_focus_split")
	_t("_test_stat_focus_unlocks_next_season")
	_t("_test_stat_focus_old_saves")
	_t("_test_stat_focus_club_move")
	_t("_test_focus_grows_a_trait")
	_t("_test_rivals_grow_traits")
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	print(Ran.line("Training", self))


## The weights of the position he would count as in `line` (Rating.spot_position).
func _line_weights(p: Dictionary, line: String) -> Dictionary:
	return Rating.WEIGHTS[Rating.spot_position(Rating.apos_of(p), line)]


## Puts his own OVR `gap` above his rating at `line`. Both are read from the
## same attributes (RATING_REBUILD), so only the attributes one side weighs
## and the other does not move: the new line's own ones first, else his.
func _gap_to(p: Dictionary, line: String, gap: int) -> void:
	var own_w: Dictionary = Rating.WEIGHTS[Rating.apos_of(p)]
	var there_w := _line_weights(p, line)
	var there_only := there_w.keys().filter(func(k): return not own_w.has(k))
	var own_only := own_w.keys().filter(func(k): return not there_w.has(k))
	var a: Dictionary = p["attr"]
	for _i in 200:
		var d := gap - (int(Rating.ovr(p, 0)) - GameState.rating_as(p, line))
		if d == 0:
			return
		var s := 1 if d > 0 else -1
		if not there_only.is_empty():
			for k in there_only:
				a[k] = clampi(int(a.get(k, 50)) - s, 1, 99)
		else:
			for k in own_only:
				a[k] = clampi(int(a.get(k, 50)) + s, 1, 99)


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _new_season() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))


## A season at the first club with PROJECT_MAX players who can learn a
## position and have no second one: since the attributes rate every
## position (RATING_REBUILD), Geelong's 2026 list has none.
func _learning_season() -> void:
	for code in GameDB.CLUB_ORDER:
		GameState.reset()
		GameState.start_season(str(code), GameDB.club_list(str(code)))
		var n := 0
		for q in GameState.my_list:
			if str(q.get("role2", "")) == "" and not GameState.learnable_jobs(q).is_empty():
				n += 1
		if n >= GameState.PROJECT_MAX:
			return


func _snapshot() -> Dictionary:
	var out := {}
	for p in GameState.my_list:
		out[str(p["id"])] = (p["attr"] as Dictionary).duplicate()
	return out


func _test_default_plan_spends() -> void:
	_new_season()
	_check(GameState.default_train_plan == "position", "New careers start on the Position plan")
	var before := _snapshot()
	# His pace (director 2026-11-17) buys a stat point every few games, so
	# six games, not two.
	var bought := 0
	var auto := {"by_player": {}}
	var lines := 0
	var at_pot := {}
	for i in range(6):
		for q in GameState.my_list:
			if int(q.get("potential", 0)) > 0 and int(Ovr.of(q)) >= int(q["potential"]):
				at_pot[str(q["id"])] = true
		GameState.advance()
		var week: Dictionary = GameState.last_training_report.get("auto", {})
		bought += int(week.get("points", 0))
		lines += 1 if GameState.training_summary_line() != "" else 0
		for id in week.get("by_player", {}):
			var had: Dictionary = auto["by_player"].get(id, {})
			for k in week["by_player"][id]:
				had[k] = int(had.get(k, 0)) + int(week["by_player"][id][k])
			auto["by_player"][id] = had
	var changed := 0
	var unspent := []
	for p in GameState.my_list:
		if p["attr"] != before[str(p["id"])]:
			changed += 1
		# A low-potential player earns a point every ten or so games at his
		# pace (director 2026-11-17), so the plan's promise is that nobody
		# is left holding the XP for a point it could have bought. At his
		# potential he buys nothing (director 2026-11-23, "Gains stop at
		# potential") and keeps it banked.
		if int(p.get("potential", 0)) > 0 and int(Ovr.of(p)) >= int(p["potential"]):
			continue
		# A man who sat at his potential banked it; a round's age change
		# (Growth.age_round) after the week's spend can take him a point under
		# it, and the bank buys that back the next week.
		if at_pot.has(str(p["id"])):
			continue
		var w := {"xp": GameState.plan_weights(p),
				"xp_match": Rating.shares(p)}
		for bank in w:
			# The plan saves for the stat with the most weight per XP.
			var price := 0
			var ratio := 0.0
			for k in w[bank]:
				if not (p["attr"] as Dictionary).has(k) or int(p["attr"][k]) >= 99:
					continue
				var c := Growth.cost(int(p["attr"][k]), float(p.get("gm", 18.0)))
				if float(w[bank][k]) / float(c) > ratio:
					ratio = float(w[bank][k]) / float(c)
					price = c
			if price > 0 and float(p.get(bank, 0.0)) >= float(price):
				unspent.append("%s %s %.0f" % [p.get("name", ""), bank, float(p[bank])])
	_check(changed > 0 and unspent.is_empty(),
			"The Position plan spends every point a player has saved for (%d rose; unspent %s)" % [changed, unspent])
	_check(bought > 0, "The report counts what the plans bought (%d points)" % bought)
	_check(lines > 0, "The results screens get a summary line in a week someone rose (%d of 6)" % lines)
	# Position plan follows the role's priorities.
	var ruck := {}
	for p in GameState.my_list:
		if str(p["role"]) == "RUCK" and (auto["by_player"] as Dictionary).has(str(p["id"])):
			ruck = p
	if not ruck.is_empty():
		var gains: Dictionary = auto["by_player"][str(ruck["id"])]
		var allowed: Dictionary = Rating.shares(ruck)
		var only_ruck_stats := true
		for k in gains:
			if not allowed.has(k):
				only_ruck_stats = false
		_check(only_ruck_stats, "A ruck on the Position plan trains ruck stats")


func _test_focus() -> void:
	_new_season()
	var defender := _first_of("DEF")
	var mid := _first_of("MID")
	GameState.set_player_plan(str(defender["id"]), "manual")
	_check(not defender.has("train_plan") and GameState.plan_for(defender) == "position",
			"Manual is no longer a plan: asking for it leaves him on Position plan")
	_check(not GameState.TRAIN_PLANS.any(func(r): return str(r["key"]) == "manual"),
			"No Manual row in the plans")
	GameState.set_player_plan(str(mid["id"]), "outside_mid")
	var mid_attr: Dictionary = (mid["attr"] as Dictionary).duplicate()
	# Injuries (seeded from the clock) or a week's card can leave him short
	# of a point after three games, so spend a known amount under his plan.
	mid["xp"] = float(mid["xp"]) + 400.0
	GameState.apply_plan_to(mid)
	var allowed: Dictionary = GameState.plan_weights(mid, "outside_mid")
	var only_plan := true
	var moved := false
	for k in mid_attr:
		if int(mid["attr"][k]) != int(mid_attr[k]):
			moved = true
			if not allowed.has(k):
				only_plan = false
	_check(moved and only_plan, "An archetype plan trains only its own attributes")


## Hold a player at his season limit so his plan cannot spend: his XP banks
## and the XP tests can count it.
func _hold(id: String) -> void:
	var p := GameState.list_player(id)
	p["season_start_ov"] = int(Ovr.of(p)) - 30


## Spend what is in his training bank (p["xp"]) on `w`, the game's own way.
func _spend(p: Dictionary, w: Dictionary) -> Dictionary:
	return GameState._spend_banks(p, w)


func _first_of(role: String) -> Dictionary:
	for p in GameState.my_list:
		if str(p["role"]) == role:
			return p
	return {}


func _test_changing_plans() -> void:
	_new_season()
	# Bank XP directly (nothing in the game banks it now) on two developing players.
	var p: Dictionary = {}
	for q in GameState.my_list:
		var room := int(q.get("potential", 0)) - int(Ovr.of(q))
		if room >= 3 and p.is_empty():
			p = q
	p["xp"] = float(p.get("xp", 0)) + 400.0
	var banked := float(p["xp"])
	var own := "inside_mid" if str(p["role"]) == "MID" else ("key_def" if str(p["role"]) == "DEF" \
			else ("key_fwd" if str(p["role"]) == "FWD" else "position"))
	var gains := GameState.set_player_plan(str(p["id"]), own)
	_check(not gains.is_empty() and float(p["xp"]) < banked,
			"Switching a player's plan spends his banked XP straight away")
	var other: Dictionary = {}
	for q in GameState.my_list:
		var room := int(q.get("potential", 0)) - int(Ovr.of(q))
		if q != p and room >= 3 and other.is_empty():
			other = q
	other["xp"] = float(other.get("xp", 0)) + 400.0
	var other_xp := float(other["xp"])
	var result := GameState.set_default_plan("position")
	_check(float(other["xp"]) < other_xp and int(result.get("points", 0)) > 0,
			"Switching the club plan spends banked XP for everyone on it")
	_check(GameState.plan_for(p) == own or own == "position", "A player's own plan wins over the club plan")
	GameState.set_player_plan(str(p["id"]), "")
	_check(GameState.plan_for(p) == "position" and not p.has("train_plan"),
			"Choosing Club plan clears a player's own plan")


func _test_plans_survive_save() -> void:
	_new_season()
	var fwd := _first_of("FWD")
	var mid := _first_of("MID")
	GameState.set_player_plan(str(fwd["id"]), "key_fwd")
	GameState.advance()
	var fwd_state := [int(fwd["xp"]), int(Ovr.of(fwd)), int(fwd["potential"]), (fwd["attr"] as Dictionary).duplicate()]
	GameState.save_career()
	GameState.load_career()
	var q := GameState.list_player(str(fwd["id"]))
	_check(GameState.plan_for(q) == "key_fwd", "A player's own plan survives a save")
	_check([int(q["xp"]), int(Ovr.of(q)), int(q["potential"]), q["attr"]] == fwd_state,
			"XP, rating, potential and attributes survive a save unchanged")
	GameState.set_default_plan("inside_mid")
	_check(GameState.default_train_plan == "position", "Only Position plan can be the club plan")


## One round with no week-event card in the way (a card can pay the whole
## list XP, which would blur the per-game figures).
func _round() -> void:
	GameState.week_event = {}
	GameState.advance()


## Pin `id` into the senior side (true) or leave him out (false).
func _pick(id: String, senior: bool) -> void:
	var side := GameState.current_side()
	var in_side := false
	for k in side:
		if (side[k] as Array).has(id):
			in_side = true
			if not senior:
				(side[k] as Array).erase(id)
	if senior and not in_side:
		var arr: Array = side[str(GameState.list_player(id)["role"])]
		arr[arr.size() - 1] = id
	side["OUT"] = [] if senior else [id]
	GameState.set_selection(side)




func _row(id: String) -> Dictionary:
	for row in GameState.last_training_report.get("rows", []):
		if str(row["id"]) == id:
			return row
	return {}


## Players left out of the senior side develop in the reserves (director
## 2026-11-17: a VFL game earns half a senior game's match XP); injured and
## rested players earn nothing; a suspended player still trains. The award is
## paid once a round and survives a save.
func _test_reserves_development() -> void:
	_new_season()
	GameState.board_patience = "fair"
	GameState.rival_recruiting = "shrewd"
	var side := GameState.current_side()
	var senior := str(side["MID"][0])
	var named := {}
	for k in side:
		for id in side[k]:
			named[str(id)] = true
	var spare := []
	for p in GameState.my_list:
		if not named.has(str(p["id"])) and Ratings.available(p):
			spare.append(str(p["id"]))
	# The depth player is the last fit spare, not the first: the first is the
	# one a late withdrawal calls up (an injury on the day put him in the 22).
	var depth: String = spare[spare.size() - 1]
	var hurt: String = spare[0]
	var banned: String = spare[1]
	GameState.list_player(hurt)["injury_weeks"] = 5
	GameState.list_player(banned)["suspension_weeks"] = 5

	# One round.
	_pick(senior, true)
	_round()
	var s_row := _row(senior)
	_check(bool(s_row.get("on_ground", false)) and not bool(s_row.get("reserves", true)),
			"A selected player is on the ground, not in the reserves")
	_check(float(s_row.get("match_xp", 0.0)) > 0.0 and float(s_row.get("train_xp", 0.0)) > 0.0,
			"A senior game pays match XP and training XP")
	_check(bool(_row(depth)["reserves"]) and _vfl_half(depth),
			"A fit player left out earns a reserves game: match XP the size of his training week (%s)" % str(_row(depth)))
	_check(GameState.last_duty(depth) == "Reserves", "His duty reads Reserves")
	_check(GameState.xp_gain_for(hurt) == 0 and float(_row(hurt).get("train_xp", 1.0)) == 0.0
			and not bool(_row(hurt)["reserves"]),
			"An injured player earns nothing (%s)" % str(_row(hurt)))
	_check(GameState.last_duty(hurt) == "Not selected", "An injured player is not in the reserves")
	_check(float(_row(banned).get("match_xp", 1.0)) == 0.0 and float(_row(banned).get("train_xp", 0.0)) > 0.0
			and not bool(_row(banned)["reserves"]),
			"A suspended player trains but plays no game (%s)" % str(_row(banned)))
	var report := GameState.last_training_report
	var counted := 0
	for row in report["rows"]:
		if bool(row["reserves"]):
			counted += 1
	_check(counted > 0 and int(report["reserves_count"]) == counted, "The report counts the reserves (%d)" % counted)
	_check(GameState.reserves_summary_line() == "%d %s developing in the reserves." % [counted, "player kept" if counted == 1 else "players kept"]
			and not GameState.reserves_summary_line().contains("XP"),
			"The results screens get a reserves line, with no XP in it (%s)" % GameState.reserves_summary_line())

	# The same match cannot pay twice.
	var once := _paid(depth)
	GameState._grant_match_xp(GameState.last_match)
	_check(_paid(depth) == once, "A round's XP is paid once only")

	# A rested player is not available either.
	var rested: String = spare[2]
	GameState.list_player(rested)["rested"] = true
	for i in range(3):
		_pick(depth, false)
		GameState.list_player(hurt)["injury_weeks"] = 5
		if i == 0:
			_round()
			_check(GameState.xp_gain_for(rested) == 0, "A rested player earns nothing")
		elif i == 2:
			# Difficulty never changes development: the third reserves game is
			# played on the hardest dials and pays the same share.
			GameState.board_patience = "ruthless"
			GameState.rival_recruiting = "cutthroat"
			_round()
			_check(bool(_row(depth)["reserves"]) and _vfl_half(depth),
					"Reserves XP is the same share on Ruthless and Cut-throat (%s)" % str(_row(depth)))
			GameState.board_patience = "fair"
			GameState.rival_recruiting = "shrewd"
		else:
			_round()

	# A save between rounds neither repeats nor loses the award.
	var before_save := _bank(depth)
	var paid := _paid(depth)
	GameState.save_career()
	GameState.load_career()
	_check(is_equal_approx(_bank(depth), before_save), "Banked reserves XP survives a save")
	GameState._grant_match_xp(GameState.last_match)
	_check(_paid(depth) == paid, "A reloaded save does not pay the last round again")
	_pick(depth, false)
	_round()
	_check(bool(_row(depth)["reserves"]) and _vfl_half(depth), "The next round after a load pays one reserves game")

	# Back in the senior side, the senior rate returns.
	_pick(depth, true)
	_round()
	_check(bool(_row(depth).get("on_ground", false)) and not bool(_row(depth)["reserves"])
			and float(_row(depth).get("match_xp", 0.0)) > 0.0,
			"Recalled, he earns senior match XP again (%s)" % str(_row(depth)))


## A reserves game's match XP is half a senior game's: two-thirds of a week
## halved, so the same size as his training third.
func _vfl_half(id: String) -> bool:
	var row := _row(id)
	var t := float(row.get("train_xp", 0.0))
	return t > 0.0 and absf(float(row.get("match_xp", 0.0)) - t) < 0.001 * t


## What sits in his two banks.
func _bank(id: String) -> float:
	var p := GameState.list_player(id)
	return float(p.get("xp", 0.0)) + float(p.get("xp_match", 0.0))


## How many weeks he has been paid for.
func _paid(id: String) -> int:
	return int(GameState.list_player(id).get("xp_games", 0))


func _test_department_development() -> void:
	_new_season()
	# Hold coach teaching at par so this check isolates the club allocation.
	var staff := GameState.club_staff(GameState.my_club)
	for coach in staff.values():
		for key in ["teach", "tactics", "manage"]:
			coach["skills"][key] = 70
		coach["spec"] = {"MID": "MID", "FWD": "FWD", "DEF": "DEF", "DEV": "DEV"}.get(
				str(coach["job"]), "")
	var kid: Dictionary = GameState.my_list[0]
	kid["age"] = 20
	kid["xp"] = 0
	var result := {"home": GameState.my_club, "away": "COL", "players": {}}

	GameState.department_budget["development"] = 0
	var low: Dictionary = GameState._grant_xp(GameState.my_club, GameState.my_list, result)
	var low_gain := 0
	for row in low["rows"]:
		if str(row["id"]) == str(kid["id"]):
			low_gain = int(row["xp"])
	kid["xp"] = 0
	GameState.department_budget["development"] = 3
	var elite: Dictionary = GameState._grant_xp(GameState.my_club, GameState.my_list, result)
	var elite_gain := 0
	for row in elite["rows"]:
		if str(row["id"]) == str(kid["id"]):
			elite_gain = int(row["xp"])
	_check(elite_gain > low_gain,
			"Development funding directly changes a young player's XP (%d Minimal, %d Elite)" % [
			low_gain, elite_gain])
	GameState.department_budget["development"] = ClubBudget.STANDARD


func _test_stat_guide_complete() -> void:
	var complete := true
	for row in GameState.TRAIN_STATS:
		var info: Array = StatGuide.STATS.get(str(row[0]), [])
		if info.size() != 1:
			complete = false
			continue
		for text in info:
			if str(text).length() < 10:
				complete = false
	_check(complete, "Every trainable stat has a guide line")
	var labels_ok := true
	for row in GameState.train_plan_options():
		if GameState.train_plan_label(str(row[0])) == "" or GameState.train_plan_description(str(row[0])) == "":
			labels_ok = false
	_check(labels_ok, "Every plan has a label and a description")



## Every plan spends only on what the engine uses for the role it is offered
## to: the role core behind OVR, or a stat behind a trait that role can earn.
func _test_plans_match_the_engine() -> void:
	_new_season()
	var ok := true
	var bad := []
	for row in GameState.TRAIN_PLANS:
		if not row.has("weights"):
			continue
		for role in row["roles"]:
			for k in row["weights"]:
				if k == "star" or k == "durability" or not GameState.stat_useful_for_role(str(role), str(k)):
					ok = false
					bad.append("%s/%s/%s" % [row["key"], role, k])
	_check(ok, "Every archetype trains only attributes its role uses in a match %s" % str(bad))
	var pos_ok := true
	for role in ["MID", "DEF", "FWD", "RUCK"]:
		var p := _first_of(role)
		if p.is_empty():
			continue
		var w: Dictionary = GameState.plan_weights(p, "position")
		if w != Rating.shares(p):
			pos_ok = false
		for key in GameState.plans_for(p):
			for k in GameState.plan_weights(p, key):
				if not (p["attr"] as Dictionary).has(k):
					pos_ok = false
	_check(pos_ok, "Position plan trains each role's OVR core, and no plan names an attribute a player lacks")
	var d := {}
	for p in GameState.my_list:
		if str(p["role"]) == "DEF" and str(p.get("role2", "")) == "":
			d = p
			break
	var offered: Array = GameState.plans_for(d)
	_check(offered.has("position") and offered.has("key_def") and not offered.has("manual")
			and not offered.has("key_fwd") and not offered.has("inside_mid"),
			"A pure defender is offered defender plans, not forward or midfield ones (%s)" % str(offered))
	d["train_plan"] = "key_fwd"
	_check(GameState.plan_for(d) == "position", "A plan for another role falls back to Position plan")
	d.erase("train_plan")


## Two plans for the same player make different footballers.
func _test_archetypes_differ() -> void:
	_new_season()
	var mid := _first_of("MID")
	var built := {}
	for plan in ["inside_mid", "outside_mid"]:
		var p: Dictionary = mid.duplicate(true)
		p["train_plan"] = plan
		p["potential"] = 99   # room to grow: the plan is tested, not his ceiling
		p["xp"] = 4000
		built[plan] = _spend(p, GameState.plan_weights(p, plan))
	var inside: Dictionary = built["inside_mid"]
	var outside: Dictionary = built["outside_mid"]
	_check(int(inside.get("contested_ball", 0)) > int(outside.get("contested_ball", 0)) + 5
			and int(outside.get("work_rate", 0)) > int(inside.get("work_rate", 0)) + 5,
			"Inside midfielders build contested ball, wings build their running game (%s / %s)" % [str(inside), str(outside)])
	var fwd := _first_of("FWD")
	var small: Dictionary = fwd.duplicate(true)
	small["potential"] = 99
	small["xp"] = 4000
	var sg := _spend(small, GameState.plan_weights(small, "small_fwd"))
	_check(not sg.has("contested_marking"), "A small forward never trains contested marking (it would stop him crumbing)")


## Traits are still reached through the plan that suits them.
func _test_traits_through_training() -> void:
	_new_season()
	var fwd: Dictionary = _first_of("FWD").duplicate(true)
	fwd["attr"]["contested_marking"] = Traits.SMALL_MAX_CM - 5
	fwd["attr"]["forward_craft"] = int(Traits.DEFS["crumber"]["min"]) - 4
	fwd["role2"] = ""
	fwd["potential"] = 99
	fwd["xp"] = 2500
	_check(not Traits.has(fwd, "crumber"), "(setup) no Crumber yet")
	_spend(fwd, GameState.plan_weights(fwd, "small_fwd"))
	_check(Traits.has(fwd, "crumber"), "Small forward training unlocks Crumber")
	var d: Dictionary = _first_of("DEF").duplicate(true)
	# Controlled fixture: only Reading the play is buyable, so this tests the plan/trait
	# path rather than whichever real defender happens to be first in the list.
	d["potential"] = 99
	d["gm"] = 0
	d["attr"]["reading_play"] = 74
	d["attr"]["pressure"] = 99
	d["xp"] = 3000
	_spend(d, GameState.plan_weights(d, "key_def"))
	_check(int(d["attr"]["reading_play"]) >= 80 and Traits.of(d).has("interceptor") or Traits.of(d).filter(func(k): return k != "wet_weather").size() >= 2,
			"Key defender training reaches Interceptor (%d)" % int(d["attr"]["reading_play"]))


## Saves from before the overhaul: removed plans and off-role plans fall
## back to Position plan, and Manual (cut 2026-11-03) - his own or a Manual
## club plan he followed - becomes the plan closest to how he is built.
func _test_old_plans_migrate() -> void:
	_new_season()
	var a: Dictionary = GameState.my_list[0]
	var b: Dictionary = GameState.my_list[1]
	var c: Dictionary = GameState.my_list[2]
	a["train_plan"] = "focus_marking"
	b["train_plan"] = "star"
	c.erase("train_plan")
	# A forward hand-trained into a target: marking and goals far above the rest.
	var f: Dictionary = {}
	for q in GameState.my_list:
		if str(q["role"]) == "FWD" and str(q.get("role2", "")) == "" and q != a and q != b and q != c:
			f = q
			break
	for k in ["contested_marking", "forward_craft", "goalkicking"]:
		f["attr"][k] = 95
	f["train_plan"] = "manual"
	f["potential"] = 99
	f["xp"] = 2000
	GameState.default_train_plan = "manual"
	GameState.save_career()
	GameState.load_career()
	var a2 := GameState.list_player(str(a["id"]))
	var b2 := GameState.list_player(str(b["id"]))
	var c2 := GameState.list_player(str(c["id"]))
	_check(GameState.default_train_plan == "position", "The club plan loads as Position plan")
	var f2 := GameState.list_player(str(f["id"]))
	var c_plan := GameState.plan_for(c2)
	_check(c_plan != "manual" and GameState.plan_valid_for(c2, c_plan),
			"A player who followed a Manual club plan gets a real plan (%s)" % c_plan)
	_check(GameState.plan_for(f2) == "key_fwd", "A hand-trained target forward maps to Key forward (%s)" % GameState.plan_for(f2))
	var nobody_manual := true
	for q in GameState.my_list:
		if GameState.plan_for(q) == "manual" or str(q.get("train_plan", "")) == "manual":
			nobody_manual = false
	_check(nobody_manual, "Nobody loads on Manual")
	f2["season_start_ov"] = int(Ovr.of(f2))
	var xp_before := int(f2["xp"])
	GameState.apply_plan_to(f2)
	_check(int(f2["xp"]) < xp_before, "His banked XP is spent under the new plan")
	_check(not a2.has("train_plan") and not b2.has("train_plan")
			and GameState.plan_for(a2) == "position" and GameState.plan_for(b2) == "position",
			"Removed plans (single-stat focus, Star power) fall back to Position plan")


## After a game the report says what training changed, in a line.
func _test_training_news() -> void:
	_new_season()
	var p := _first_of("MID")
	p["xp"] = 3000
	var ov := int(Ovr.of(p))
	var out := GameState.apply_train_plans()
	var rose := false
	for r in out["rises"]:
		if str(r[0]) == str(p["id"]) and int(r[1]) == ov and int(r[2]) > ov:
			rose = true
	_check(rose, "A rating rise is reported with before and after")
	GameState.last_training_report = {"auto": out}
	var line := GameState.training_summary_line()
	_check(line.begins_with("Training:") and line.contains("OVR"), "The summary line reports it (%s)" % line)
	# Every riser is named with his from-to, however many (director, 2026-10-19).
	var many := []
	for q in GameState.my_list.slice(0, 13):
		many.append([str(q["id"]), 70, 71])
	GameState.last_training_report = {"auto": {"rises": many, "traits": [], "at_pot": []}}
	var names := GameState.training_rise_lines()
	var all_named := names.size() == 13
	for q in GameState.my_list.slice(0, 13):
		all_named = all_named and names.has("%s 70 to 71" % GameDB.player_display_name(q))
	_check(all_named, "All 13 risers are named with from and to (%d listed)" % names.size())
	_check(not GameState.training_summary_line().contains("more"), "The summary never says 'N more'")
	GameState.last_training_report = {"auto": {"points": 5, "rises": [], "traits": []}}
	_check(GameState.training_summary_line() == "", "Stat points alone are not news")
	# Bug bash 5: a trait pushed out by the five-trait cap is news too.
	var q: Dictionary = GameState.my_list[0]
	GameState.last_training_report = {"auto": {"rises": [], "traits": [], "lost": [[str(q["id"]), "engine"]], "at_pot": []}}
	var lost_line := GameState.training_summary_line()
	_check(lost_line.contains("lost Engine") and lost_line.contains("five traits"),
			"A trait lost to the five-trait cap is announced (%s)" % lost_line)


## A dual-role player can train toward either of his roles: a ruck who also
## defends gets the Ruck plan and the defender archetypes; nobody gets a plan
## for a role he does not play.
## Long-press group selection only offers a focus that makes sense for every
## selected player, then applies that focus to the whole group.
func _test_training_multiselect() -> void:
	_new_season()
	var mids := []
	var defender := {}
	for p in GameState.my_list:
		if str(p.get("role", "")) == "MID" and mids.size() < 2:
			mids.append(p)
		elif str(p.get("role", "")) == "DEF" and str(p.get("role2", "")) != "MID" and defender.is_empty():
			defender = p
	_check(mids.size() == 2 and not defender.is_empty(), "(setup) group training has two mids and a defender")

	var scene = load("res://scripts/ui/TrainingScene.gd").new()
	scene._bulk_selected = {
		str(mids[0]["id"]): true,
		str(defender["id"]): true,
	}
	var mixed: Array = scene._bulk_plans()
	_check(mixed.has("position") and not mixed.has("manual")
			and not mixed.has("inside_mid") and not mixed.has("key_def"),
			"A mixed-position group only gets plans valid for everyone (%s)" % str(mixed))

	scene._bulk_selected = {
		str(mids[0]["id"]): true,
		str(mids[1]["id"]): true,
	}
	var same_line: Array = scene._bulk_plans()
	_check(same_line.has("inside_mid") and same_line.has("outside_mid"),
			"Two midfielders can share a midfield development focus (%s)" % str(same_line))

	for p in mids:
		p["xp"] = 0
	scene._apply_bulk_plan("inside_mid")
	_check(GameState.plan_for(mids[0]) == "inside_mid" and GameState.plan_for(mids[1]) == "inside_mid",
			"One group action assigns the plan to every selected player")
	scene._toggle_bulk(str(mids[0]["id"]))
	_check(scene._bulk_selected.size() == 1 and not scene._bulk_selected.has(str(mids[0]["id"])),
			"Once group selection is active, a tap can remove a player")
	scene._toggle_bulk(str(mids[0]["id"]))
	_check(scene._bulk_selected.size() == 2,
			"A player can be added back to the selected training group")
	scene.free()


func _test_dual_role_plans() -> void:
	var balta := {}
	for p in GameDB.players:
		if str(p.get("role", "")) == "RUCK" and str(p.get("role2", "")) == "DEF":
			balta = p
			break
	_check(not balta.is_empty(), "A ruck who defends is on a list")
	var plans := GameState.plans_for(balta)
	_check(plans.has("ruck") and plans.has("key_def") and plans.has("rebound_def"),
			"%s can train as a ruck or a defender (%s)" % [str(balta.get("real_name", "")), str(plans)])
	_check(not plans.has("inside_mid") and not plans.has("key_fwd"), "...and nothing he does not play")
	var def_ruck := {"role": "DEF", "role2": "RUCK", "attr": {}}
	_check(GameState.plans_for(def_ruck).has("ruck"), "A defender who pinch-hits in the ruck can train the ruck")
	_check(not GameState.plans_for({"role": "MID", "role2": "FWD"}).has("ruck"), "A midfielder has no ruck plan")
	var bad := 0
	for p in GameDB.players:
		for role in [str(p.get("role", "")), str(p.get("role2", ""))]:
			if role == "":
				continue
			var ok := false
			for k in GameState.plans_for(p):
				if (GameState._plan_row(k)["roles"] as Array).has(role):
					ok = true
			if not ok:
				bad += 1
	_check(bad == 0, "Every role a player plays has a plan of its own (%d missing)" % bad)


## A training plan is a plan, not what the player is: however hard a medium defender trains
## on that plan he stays a defender who is not typed a key defender.
func _test_plan_is_not_identity() -> void:
	_new_season()
	var small := {}
	for p in GameState.my_list:
		if str(p.get("role", "")) == "DEF" and float(p.get("height_cm", 0.0)) > 0.0 \
				and float(p["height_cm"]) < PlayerProfile.KEY_DEF_CM:
			small = p
			break
	_check(not small.is_empty(), "(setup) a medium defender to train")
	if small.is_empty():
		return
	GameState.set_player_plan(str(small["id"]), "key_def")
	for i in range(12):
		small["xp"] = int(small.get("xp", 0)) + 300
		GameState.apply_train_plans()
	_check(str(small["role"]) == "DEF" and PlayerProfile.player_type(small) != "Key defender",
			"A %.0f cm defender on the key defender plan is still not a key defender (%s)" % [
				float(small["height_cm"]), PlayerProfile.player_type(small)])


## Learning another position (M5-003 / RC-003, director rules 2026-10-06): a
## plausible job for his size, POT 70 for a second position and 90 for a
## third, PROJECT_WEEKS fit weeks, then he earns it within PROJECT_PASS of his
## own rating or it has not taken. Two at once a club, one a season a player.
func _test_learning_a_position() -> void:
	# The job follows his size.
	var tall := {"height_cm": 200.0}
	var mid_h := {"height_cm": 187.0}
	var small := {"height_cm": 177.0}
	_check(GameState.learn_job_for(tall, "FWD") == "key_fwd" and GameState.learn_job_for(small, "FWD") == "small_fwd"
			and GameState.learn_job_for(mid_h, "FWD") == "fwd", "A forward's job follows his height")
	_check(GameState.learn_job_for(tall, "DEF") == "key_def" and GameState.learn_job_for(small, "DEF") == "small_def"
			and GameState.learn_job_for(mid_h, "DEF") == "small_def", "Only a tall player learns key defence; under 191 cm it is small defence")
	_check(GameState.learn_job_for(mid_h, "RUCK") == "" and GameState.learn_job_for(tall, "RUCK") == "ruck",
			"The ruck takes a ruckman's height")
	# POT gates.
	_learning_season()
	var cand := {}
	for q in GameState.my_list:
		if str(q.get("role2", "")) == "" and int(q.get("potential", 0)) >= 70 and not GameState.learnable_jobs(q).is_empty():
			cand = q
			break
	_check(not cand.is_empty(), "Someone on the list can learn a position")
	if cand.is_empty():
		return
	var pot := int(cand["potential"])
	cand["potential"] = 69
	_check(GameState.learnable_jobs(cand).is_empty(), "Under POT 70 a player cannot learn a second position")
	cand["potential"] = pot
	var job: String = GameState.learnable_jobs(cand)[0]
	var role: String = GameState.LEARN_JOBS[job]["role"]
	_check(GameState.plans_for(cand).has(GameState.LEARN_PREFIX + job), "Training offers it as a plan")
	GameState.set_player_plan(str(cand["id"]), GameState.LEARN_PREFIX + job)
	_check(GameState.project_job(cand) == job and GameState.project_progress(cand) == "Week 0 of %d" % GameState.PROJECT_WEEKS,
			"Choosing it starts the project")
	_check(GameState.learnable_jobs(cand).is_empty(), "One project at a time")
	var line: String = load("res://scripts/ui/TrainingScene.gd")._project_line(cand)
	var ahead := GameState.rating_as(cand, role) >= int(Ovr.of(cand)) - GameState.PROJECT_PASS
	_check(line.begins_with("Week 0 of %d" % GameState.PROJECT_WEEKS)
			and line.contains("up to the standard" if ahead else "within %d by week" % GameState.PROJECT_PASS),
			"Training shows the standard he is chasing, or that he has reached it (%s)" % line)
	# The price (director 2026-11-17): while he learns, both his banks split
	# four ways, a quarter to each of the top two stats of his own position
	# and of the new one (a stat in both gets two quarters).
	var split := GameState._learn_split(cand)
	var share_sum := 0.0
	for k in split:
		share_sum += float(split[k])
	_check(absf(share_sum - 1.0) < 0.001 and split.size() >= 2 and split.size() <= 4,
			"While he learns, his XP splits four ways (%s)" % str(split))
	var keep_attr: Dictionary = (cand["attr"] as Dictionary).duplicate()
	cand["xp"] = 300.0
	cand["xp_match"] = 300.0
	GameState.apply_plan_to(cand)
	var off_split := []
	for k in keep_attr:
		if int(cand["attr"][k]) != int(keep_attr[k]) and not split.has(k):
			off_split.append(k)
	_check(float(cand["xp"]) == 0.0 and float(cand["xp_match"]) == 0.0 and off_split.is_empty(),
			"Both banks go into the split, and only its stats move (%s)" % str(off_split))
	cand["attr"] = keep_attr
	cand.erase("xp_split")
	# Club limit.
	var started := 1
	for q in GameState.my_list:
		if started >= GameState.PROJECT_MAX or q == cand:
			continue
		var jobs := GameState.learnable_jobs(q)
		if not jobs.is_empty():
			GameState.set_player_plan(str(q["id"]), GameState.LEARN_PREFIX + str(jobs[0]))
			started += 1
	var more := 0
	for q in GameState.my_list:
		more += GameState.learnable_jobs(q).size()
	_check(started < GameState.PROJECT_MAX or more == 0, "A club runs at most %d at once" % GameState.PROJECT_MAX)
	# Injured weeks do not count.
	cand["injury_weeks"] = 2
	GameState._project_week(cand)
	_check(int(cand["project"]["weeks"]) == 0, "A week injured does not count")
	cand["injury_weeks"] = 0
	# A project survives a save.
	GameState.save_career()
	GameState.load_career()
	cand = GameState.list_player(str(cand["id"]))
	_check(GameState.project_job(cand) == job, "The project survives a save")
	# Pass: rate him within PROJECT_PASS there, run the weeks out.
	var attr: Dictionary = cand["attr"]
	for k in _line_weights(cand, role):
		attr[k] = maxi(int(attr[k]), 90)
	var res := {}
	for i in range(GameState.PROJECT_WEEKS):
		res = GameState._project_week(cand)
	_check(bool(res.get("learned", false)) and str(cand.get("role2", "")) == role and Ratings.plays_role(cand, role),
			"Close enough at the end: he can be picked there (%s)" % str(res))
	_check(GameState.project_job(cand) == "" and str(cand.get("train_plan", "")) == "", "Then he goes back to the club plan")
	var kept := _last_project_fact(str(cand["id"]))
	_check(str(kept.get("d", "")) == job and str(kept.get("out", "")) == "learned"
			and str(kept.get("at", "")).begins_with("Round") and str(kept.get("club", "")) == GameState.my_club,
			"The decision and its outcome are kept as a career fact (%s)" % str(kept))
	_check(GameState.learnable_jobs(cand).is_empty(), "One project a season")
	# Fail: a fresh player, kept well short.
	var other := {}
	for q in GameState.my_list:
		if q != cand and GameState.project_job(q) != "":
			other = q
	if not other.is_empty():
		var orole := GameState.project_role(other)
		_gap_to(other, orole, 10)
		var r2 := {}
		other["injury_weeks"] = 0
		for i in range(GameState.PROJECT_WEEKS):
			r2 = GameState._project_week(other)
		_check(not bool(r2.get("learned", true)) and not Ratings.plays_role(other, orole),
				"Well short at the end: it has not taken (%s)" % str(r2))
		_check(str(_last_project_fact(str(other["id"])).get("out", "")) == "not taken",
				"A project that did not take is kept as one too")
	# Switching away ends it.
	_new_season()
	var s2 := {}
	for q in GameState.my_list:
		if not GameState.learnable_jobs(q).is_empty():
			s2 = q
			break
	if not s2.is_empty():
		GameState.set_player_plan(str(s2["id"]), GameState.LEARN_PREFIX + str(GameState.learnable_jobs(s2)[0]))
		GameState.set_player_plan(str(s2["id"]), "position")
		_check(GameState.project_job(s2) == "" and GameState.learnable_jobs(s2).is_empty(),
				"Switching plan ends the project; this season's chance is spent")


## A Unicorn is born, not trained (director, 2026-10-08): a hand-picked few
## and a rare tall draft prospect. He plays forward, midfield and back, and on
## the ground fills one missing place in one synergy, in his line for a line
## synergy.
func _test_unicorn() -> void:
	var u := Ovr.to({"id": "U1", "role": "MID", "role2": "FWD", "potential": 87,  "attr": {"contested_ball": 60}}, 70)
	_check(GameState.learn_pot_needed(u) == 88 and int(u["potential"]) < 88,
			"A third position takes POT 88 (director 2026-11-26)")
	u["learned"] = ["DEF"]
	_check(not Traits.is_unicorn(u) and Ratings.role_tag(u) == "MID/FWD/DEF",
			"Learning forward, midfield and back is not a Unicorn: that is born")
	_check(GameState.learn_pot_needed(u) == -1, "Three positions is the most")
	var born := {"id": "U0", "role": "RUCK", "unicorn": true, "attr": {}}
	_check(Traits.is_unicorn(born) and Traits.of(born).has("unicorn")
			and Ratings.positions(born).has("FWD") and Ratings.positions(born).has("MID")
			and Ratings.positions(born).has("DEF"), "A born Unicorn can be picked at forward, midfield and back")
	# The director's three at the start, and nobody else; a move keeps it.
	var start := []
	for p in GameDB.players:
		if Traits.is_unicorn(p):
			start.append("%s %s" % [p["first"], p["last"]])
	start.sort()
	_check(start == ["Luke Jackson", "Mark Blicavs", "Sam Darcy"], "The Unicorns at the start: %s" % str(start))
	var moved := {"first": "Luke", "last": "Jackson", "club": "COL"}
	GameDB.mark_unicorns([moved])
	_check(Traits.is_unicorn(moved), "A Unicorn keeps it wherever the draft sends him (a save from before)")
	var fake := {"first": "Luke", "last": "Jackson", "generated": true}
	GameDB.mark_unicorns([fake])
	_check(not Traits.is_unicorn(fake), "A generated player who shares the name is not one")
	# Rare in later classes: about two in five, its tallest non-ruck 194 cm+.
	var with_one := 0
	var bad := ""
	for y in range(2027, 2057):
		var n := 0
		for p in Prospects.generate_class(y, 77):
			if Traits.is_unicorn(p):
				n += 1
				if str(p["role"]) == "RUCK" or float(p["height_cm"]) < Prospects.UNICORN_MIN_CM:
					bad = "%d: %s %.0f" % [y, p["role"], float(p["height_cm"])]
		if n > 1:
			bad = "%d: %d in one class" % [y, n]
		with_one += 1 if n == 1 else 0
	_check(bad == "" and with_one >= 6 and with_one <= 18,
			"A Unicorn in %d of 30 classes, never more than one, always tall (%s)" % [with_one, bad])
	u["unicorn"] = true
	# Built from the synergy rules, so the test holds whatever the counts are.
	var er: Dictionary = Traits.SYNERGIES["engine_room"]["needs"]
	var bulls := []
	for i in range(int(er["bull"]) - 1):
		bulls.append({"id": "B%d" % i, "role": "MID", "attr": {"contested_ball": 99}})
	_check(not Traits.active(bulls).has("engine_room"), "One contested bull short is not an Engine room")
	var with_u := Traits.active(bulls + [u])
	_check(with_u.has("engine_room"), "A Unicorn fills the missing bull (%s)" % str(with_u))
	_check(Traits.wildcards(bulls + [u]).size() == 1, "...and fills only one synergy")
	# A forward-line synergy one short: the Unicorn counts only playing forward.
	var ts: Dictionary = Traits.SYNERGIES["tall_small"]["needs"]
	var fwds := []
	for i in range(int(ts["aerial"])):
		fwds.append({"id": "A%d" % i, "role": "FWD", "attr": {"contested_marking": 99}})
	for i in range(int(ts["crumber"]) - 1):
		fwds.append({"id": "C%d" % i, "role": "FWD", "attr": {"forward_craft": 99, "contested_marking": Traits.SMALL_MAX_CM - 8}})
	var u_mid := u.duplicate(true)
	u_mid["id"] = "U2"
	_check(not Traits.active(fwds + [u_mid]).has("tall_small"), "A Unicorn in the midfield cannot fill a forward-line synergy")
	var u_fwd := u.duplicate(true)
	u_fwd["role"] = "FWD"
	u_fwd["own_role"] = "MID"
	_check(Traits.active(fwds + [u_fwd]).has("tall_small"), "Playing forward, he can")


## Rival clubs learn positions too, up to PROJECT_MAX at once, by the same
## gates, only for players who give up nothing for it.
func _test_rival_projects() -> void:
	_new_season()
	var list := []
	for code in GameState.season.lists:
		if str(code) != GameState.my_club:
			list = GameState.season.lists[code]
			break
	GameState._ai_projects(list)
	var learners := []
	for q in list:
		if GameState.project_job(q) != "":
			learners.append(q)
	_check(learners.size() <= GameState.PROJECT_MAX, "A rival club runs at most %d projects" % GameState.PROJECT_MAX)
	if learners.is_empty():
		return
	var l: Dictionary = learners[0]
	_check(int(l.get("potential", 0)) >= GameState.PROJECT_POT[1], "Rivals keep to the POT gate")
	l["injury_weeks"] = 0
	var w := int(l["project"]["weeks"])
	GameState._ai_projects(list)
	var n := 0
	for q in list:
		if int(q.get("project_year", 0)) == GameState.season_year:
			n += 1
	_check(n == learners.size() and int(l["project"]["weeks"]) == w + 1, "No second start; his weeks count game by game")


## The pass margin, tightened (row 93, T8.Q15, director 2026-11-06: "Tighten
## pass margin"): a project that ends with his rating there 3 below his own
## passed at the old margin of 3 and no longer takes; one that ends within
## PROJECT_PASS still does. Reach and the price stay where they were.
func _test_pass_margin_tightened() -> void:
	_check(GameState.PROJECT_PASS == 1, "The pass margin is 1 (was 3)")
	_check(GameState.PROJECT_REACH == 6, "Reach is unchanged: a move within 6 may be tried")
	_learning_season()
	var cand := {}
	var job := ""
	for q in GameState.my_list:
		var jobs := GameState.learnable_jobs(q)
		if not jobs.is_empty():
			cand = q
			job = str(jobs[0])
			break
	_check(not cand.is_empty(), "Someone on the list can learn a position")
	if cand.is_empty():
		return
	var role := str(GameState.LEARN_JOBS[job]["role"])
	var keep: Dictionary = (cand["attr"] as Dictionary).duplicate()
	# 3 behind at the verdict: learned at the old margin, not now.
	GameState._start_project(cand, job)
	_gap_to(cand, role, 3)
	var r := GameState._finish_project(cand, false)
	_check(int(r.get("own", 0)) - int(r.get("there", 0)) == 3,
			"The case: he ends 3 below his own rating there, a pass at the old margin (%s)" % str(r))
	_check(not bool(r.get("learned", true)) and not Ratings.plays_role(cand, role),
			"3 behind no longer takes: he cannot be picked there (%s)" % str(r))
	# Exactly PROJECT_PASS behind: still learned.
	GameState._start_project(cand, job)
	_gap_to(cand, role, GameState.PROJECT_PASS)
	r = GameState._finish_project(cand, false)
	_check(bool(r.get("learned", false)) and Ratings.plays_role(cand, role),
			"%d behind still takes: he can be picked there (%s)" % [GameState.PROJECT_PASS, str(r)])
	cand["attr"] = keep


## A project survives a save mid-way, ends when he changes clubs (his chance
## for the season stays spent), and is judged where it stands when the
## season ends. A learned third position counts wherever positions matter.
func _test_project_endings() -> void:
	_learning_season()
	var learners := []
	for q in GameState.my_list:
		var jobs := GameState.learnable_jobs(q)
		if not jobs.is_empty():
			GameState.set_player_plan(str(q["id"]), GameState.LEARN_PREFIX + str(jobs[0]))
			learners.append(q)
	_check(learners.size() == GameState.PROJECT_MAX, "(setup) two projects under way")
	if learners.size() < 2:
		return
	learners[0]["project"]["weeks"] = 3
	var id0 := str(learners[0]["id"])
	GameState.save_career()
	GameState.load_career()
	var back := GameState.list_player(id0)
	_check(GameState.project_job(back) != "" and int(back["project"]["weeks"]) == 3,
			"A project survives a save mid-way")
	# A move to another club ends it; the season's chance stays spent.
	var mover := GameState.list_player(str(learners[1]["id"]))
	var other := ""
	for code in GameState.season.lists:
		if str(code) != GameState.my_club:
			other = str(code)
			break
	GameState.my_list.erase(mover)
	GameState._join(other, mover)
	_check(GameState.project_job(mover) == "" and int(mover.get("project_year", 0)) == GameState.season_year
			and GameState.active_projects() == 1, "A new club ends his project; the chance is spent")
	var moved := _last_project_fact(str(mover["id"]))
	_check(str(moved.get("out", "")) == "ended by a move" and str(moved.get("club", "")) == GameState.my_club,
			"A project ended by a move is kept, with the club that set it")
	(GameState.season.lists[other] as Array).erase(mover)
	# The season ends before week 8: he is judged where he stands.
	GameState.open_offseason()
	_check(GameState.project_job(back) == "", "An unfinished project is judged when the season ends")
	_check(str(_last_project_fact(id0).get("at", "")) == "Season end",
			"A project judged at the season's end is kept as judged then")
	# A third position learned counts for the ruck, the bench and the midfield.
	var u := {"id": "U2", "role": "FWD", "role2": "DEF", "learned": ["RUCK"]}
	_check(MatchSim._is_ruckman(u) and Roles.is_mid({"role": "FWD", "role2": "DEF", "learned": ["MID"]}),
			"A learned third position counts as his own")


## Teaching (director, 4.Q1, 2026-11-04): teaching is XP scaling, never a
## ceiling step (there is no season ceiling now, director 2026-11-17).
func _test_teaching_moves_the_ceiling() -> void:
	var coach := func(teach: int): return {"skills": {"teach": teach, "tactics": 70, "manage": 70}}
	var kid := {"role": "MID", "age": 19.0}
	var vet := {"role": "MID", "age": 28.0}
	for staff in [{"MID": coach.call(90), "DEV": coach.call(90)}, {"MID": coach.call(70), "DEV": coach.call(70)}, {}]:
		_check(CoachEffects.teach_step(staff, kid) == 0 and CoachEffects.teach_step(staff, vet) == 0,
				"No teaching staff moves a ceiling")


## A player's most recent project fact (CareerFacts), or {}.
func _last_project_fact(id: String) -> Dictionary:
	var all := CareerFacts.of(GameState.career_facts, id, "project")
	return all[-1] if not all.is_empty() else {}


## Retraining adds a position and never takes one away (director,
## 2026-10-07): a second and then a third position learned keep his first
## position and every earlier one, no attribute falls as a consequence, and
## all of it survives a save.
func _test_retraining_is_additive() -> void:
	_learning_season()
	var cand := {}
	for q in GameState.my_list:
		if str(q.get("role2", "")) == "" and not GameState.learnable_jobs(q).is_empty():
			cand = q
			break
	_check(not cand.is_empty(), "Someone on the list can learn a position")
	if cand.is_empty():
		return
	var id := str(cand["id"])
	cand["potential"] = 95
	var first := str(cand["role"])
	var learned_roles := []
	for n in range(2):
		var jobs := GameState.learnable_jobs(cand)
		if jobs.is_empty():
			# A third position needs a job in reach; bring the line he would learn within it.
			for r in ["MID", "FWD", "DEF", "RUCK"]:
				if not Ratings.positions(cand).has(r) and GameState.learn_job_for(cand, r) != "":
					for k in _line_weights(cand, r):
						cand["attr"][k] = maxi(int(cand["attr"][k]), 90)
					break
			jobs = GameState.learnable_jobs(cand)
		_check(not jobs.is_empty(), "Position %d is open to learn" % (n + 2))
		if jobs.is_empty():
			return
		var job: String = jobs[0]
		var role: String = GameState.LEARN_JOBS[job]["role"]
		GameState.set_player_plan(id, GameState.LEARN_PREFIX + job)
		for k in _line_weights(cand, role):
			cand["attr"][k] = maxi(int(cand["attr"][k]), 90)
		# Level with his own rating there, whatever the out-of-position cut.
		_gap_to(cand, role, 0)
		var before: Dictionary = (cand["attr"] as Dictionary).duplicate()
		var res := {}
		for i in range(GameState.PROJECT_WEEKS):
			res = GameState._project_week(cand)
		_check(bool(res.get("learned", false)), "Position %d is learned (%s)" % [n + 2, str(res)])
		learned_roles.append(role)
		var fell := []
		for k in before:
			if int(cand["attr"][k]) < int(before[k]):
				fell.append(k)
		_check(fell.is_empty(), "Learning %s lowers none of his attributes (%s)" % [role, str(fell)])
		var all := Ratings.positions(cand)
		var kept := all.has(first) and str(cand["role"]) == first
		for r in learned_roles:
			kept = kept and all.has(r) and Ratings.plays_role(cand, r)
		_check(kept, "After %d learned he still plays every position he had (%s)" % [n + 1, str(all)])
		cand.erase("project_year")
	GameState.save_career()
	GameState.load_career()
	var back := GameState.list_player(id)
	var after := Ratings.positions(back)
	_check(after.has(first) and after.has(learned_roles[0]) and after.has(learned_roles[1]),
			"Every learned position survives a save (%s)" % str(after))


# --- Stat focus (row 97, T1.Q7, director 2026-11-06) -------------------------

## A young player with room to grow and a stat his role uses that his plan
## weights least, so the focus visibly changes where his points go.
func _focus_subject() -> Array:
	for q in GameState.my_list:
		if str(q.get("role2", "")) != "" or int(q.get("age", 30)) > 24:
			continue
		if int(q.get("potential", 0)) - int(Ovr.of(q)) < 6:
			continue
		var w: Dictionary = GameState.plan_weights(q)
		var low := ""
		for k in GameState.focus_options(q):
			if low == "" or float(w.get(k, 0.0)) < float(w.get(low, 0.0)):
				low = k
		if low != "":
			return [q, low]
	return [{}, ""]


func _other_focus(p: Dictionary, not_this: String) -> String:
	for k in GameState.focus_options(p):
		if k != not_this:
			return k
	return ""


func _test_stat_focus_once_a_season() -> void:
	_new_season()
	var pick := _focus_subject()
	var p: Dictionary = pick[0]
	var key := str(pick[1])
	_check(not p.is_empty(), "A young developing player with a focusable stat exists")
	if p.is_empty():
		return
	var id := str(p["id"])
	_check(not GameState.focus_locked(p), "No focus is locked before the coach picks one")
	var cant := ""
	for row in GameState.TRAIN_STATS:
		if not GameState.focus_options(p).has(str(row[0])):
			cant = str(row[0])
	if cant != "":
		_check(not GameState.set_stat_focus(id, cant), "A stat his role does not use cannot be his focus (%s)" % cant)
	_check(GameState.set_stat_focus(id, key), "The coach locks in a focus (%s)" % key)
	_check(GameState.stat_focus(p) == key and GameState.focus_locked(p), "His focus is set and locked this season")
	var other := _other_focus(p, key)
	_check(other != "", "He has a second stat to try")
	_check(not GameState.set_stat_focus(id, other), "A second pick in the same season is refused")
	_check(GameState.stat_focus(p) == key, "The first focus stands after a refused change")
	GameState.save_career()
	GameState.load_career()
	var p2 := GameState.list_player(id)
	_check(GameState.stat_focus(p2) == key and GameState.focus_locked(p2), "The focus and its lock survive a save")
	_check(not GameState.set_stat_focus(id, other), "Still locked after a reload")


## His focus takes all his training XP; his match XP still goes into his
## position (director, 2026-11-17).
func _test_stat_focus_split() -> void:
	_new_season()
	var pick := _focus_subject()
	var p: Dictionary = pick[0]
	var key := str(pick[1])
	var id := str(p["id"])
	var before: Dictionary = (p["attr"] as Dictionary).duplicate()
	_check(GameState.set_stat_focus(id, key), "Focus set for the split test")
	p["xp"] = 600.0
	p["xp_match"] = 0.0
	GameState.apply_plan_to(p)
	var others := 0
	for k in before:
		if k != key and int(p["attr"][k]) != int(before[k]):
			others += 1
	_check(int(p["attr"][key]) > int(before[key]) and others == 0,
			"His training all goes into his focus (%s %d to %d; %d other stats moved)" % [key, int(before[key]), int(p["attr"][key]), others])
	var mid: Dictionary = (p["attr"] as Dictionary).duplicate()
	p["xp_match"] = 600.0
	GameState.apply_plan_to(p)
	var role_w: Dictionary = Rating.shares(p)
	var on_role := 0
	var off_role := 0
	for k in mid:
		var d := int(p["attr"][k]) - int(mid[k])
		if d > 0:
			if role_w.has(k):
				on_role += d
			else:
				off_role += d
	_check(on_role > 0 and off_role == 0, "His match XP still buys his position's stats (%d points, %d off it)" % [on_role, off_role])


func _test_stat_focus_unlocks_next_season() -> void:
	_new_season()
	var pick := _focus_subject()
	var p: Dictionary = pick[0]
	var key := str(pick[1])
	var id := str(p["id"])
	_check(GameState.set_stat_focus(id, key), "Focus set before the rollover")
	var year := GameState.season_year
	GameState._ensure_league_lists()
	GameState._start_next_season(year + 1, 0)
	var p2 := GameState.list_player(id)
	_check(GameState.season_year == year + 1, "The next season opened (%d after %d)" % [GameState.season_year, year])
	_check(not p2.is_empty(), "He is still on the list in the new season (%s, %s)" % [id, str(p.get("club", ""))])
	if p2.is_empty():
		return
	_check(not GameState.focus_locked(p2), "The new season unlocks his focus")
	_check(GameState.stat_focus(p2) == key, "Last season's focus carries on until the coach picks again")
	var other := _other_focus(p2, key)
	_check(GameState.set_stat_focus(id, other), "A new focus can be picked in the new season (%s)" % other)
	_check(GameState.focus_locked(p2) and GameState.stat_focus(p2) == other, "And it locks again")


func _test_stat_focus_old_saves() -> void:
	_new_season()
	var a: Dictionary = {}
	var b: Dictionary = {}
	for q in GameState.my_list:
		if str(q.get("role2", "")) != "":
			continue
		if a.is_empty() and GameState.focus_options(q).has("contested_marking"):
			a = q
		elif b.is_empty() and GameState.focus_options(q).size() >= 2:
			b = q
	_check(not a.is_empty() and not b.is_empty(), "Two players for the old-save test")
	if a.is_empty() or b.is_empty():
		return
	# An old single-stat plan (cut 2026-11-03).
	a["train_plan"] = "focus_marking"
	# A save holding several focuses: the first his role can use stays.
	var opts: Array = GameState.focus_options(b)
	var useless := ""
	for row in GameState.TRAIN_STATS:
		if not opts.has(str(row[0])):
			useless = str(row[0])
	var several := [useless] if useless != "" else []
	several.append_array([opts[1], opts[0]])
	b["train_focus"] = several
	GameState.save_career()
	GameState.load_career()
	var a2 := GameState.list_player(str(a["id"]))
	var b2 := GameState.list_player(str(b["id"]))
	_check(GameState.plan_for(a2) == "position", "The old focus plan still falls back to Position plan")
	_check(GameState.stat_focus(a2) == "contested_marking" and str(a2.get("train_focus", "")) == "contested_marking",
			"His old marking plan becomes his stat focus, Contested marking")
	_check(not GameState.focus_locked(a2), "A migrated focus is open to change this season")
	_check(b2.get("train_focus") is String and str(b2["train_focus"]) == str(opts[1]),
			"Several focuses keep the first he can use (%s)" % [b2.get("train_focus")])


func _test_stat_focus_club_move() -> void:
	_new_season()
	var pick := _focus_subject()
	var p: Dictionary = pick[0]
	_check(GameState.set_stat_focus(str(p["id"]), str(pick[1])), "Focus set before the move")
	p["xp"] = int(p.get("xp", 0)) + 300
	GameState.apply_plan_to(p)
	var dest := "COL" if GameState.my_club != "COL" else "CAR"
	GameState._join(dest, p)
	_check(not p.has("train_focus") and not p.has("train_focus_year"),
			"A club move clears his focus: the new club's coach decides")


## The season record the summer reads (Growth.summer, director 2026-11-17):
## every point bought goes into season_gains, none is bought at his potential
## (director 2026-11-23, "Gains stop at potential"), and the rollover clears
## the records on every list and for free agents.
func _test_season_record() -> void:
	_new_season()
	var one: Dictionary = (_first_of("MID") as Dictionary).duplicate(true)
	one.erase("season_gains")
	one["potential"] = int(Ovr.of(one)) + 20
	one["xp"] = 400.0
	var bought := _spend(one, Rating.shares(one))
	_check(not bought.is_empty() and (one.get("season_gains", {}) as Dictionary) == bought,
			"Below his potential, training keeps the season's gains (%s / %s)" % [str(bought), str(one.get("season_gains", {}))])
	var past: Dictionary = (_first_of("MID") as Dictionary).duplicate(true)
	past.erase("season_gains")
	past["potential"] = int(Ovr.of(past))
	past["xp"] = 400.0
	var at_pot := int(Ovr.of(past))
	var past_bought := _spend(past, Rating.shares(past))
	# Gains stop at his potential (director 2026-11-23, "Gains stop at potential").
	_check(past_bought.is_empty() and int(Ovr.of(past)) == at_pot and float(past["xp"]) == 400.0,
			"At his potential he buys nothing and keeps his XP banked (%s, %d)" % [str(past_bought), int(Ovr.of(past))])
	var fa: Dictionary = (_first_of("FWD") as Dictionary).duplicate(true)
	fa["id"] = "record_fa"
	fa["season_gains"] = {"contested_ball": 3}
	GameState.free_agents.append(fa)
	for p in GameState.my_list:
		p["season_gains"] = {"kicking": 1}
	GameState._start_next_season(GameState.season_year + 1, 0)
	var stale := 0
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			if p.has("season_gains"):
				stale += 1
	for p in GameState.free_agents:
		if p.has("season_gains"):
			stale += 1
	_check(stale == 0, "The rollover clears every season record, free agents' too (%d left)" % stale)
	_new_season()


func _mean_attr(players: Array, key: String) -> float:
	var s := 0.0
	for p in players:
		s += float(p["attr"][key])
	return s / maxf(1.0, float(players.size()))



## Row 103: a stat focus names the trait it grows him toward and how far.
func _test_focus_grows_a_trait() -> void:
	_new_season()
	var p := {}
	var bull_min := int(Traits.DEFS["bull"]["min"])
	for q in GameState.my_list:
		if str(q["role"]) == "MID" and int(q["attr"]["contested_ball"]) < bull_min and not Traits.of(q).has("bull"):
			p = q
			break
	_check(not p.is_empty(), "A midfielder short of Contested bull")
	if p.is_empty():
		return
	var ft := GameState.focus_trait(p, "contested_ball")
	_check(str(ft.get("key", "")) == "bull" and int(ft["gap"]) == bull_min - int(p["attr"]["contested_ball"]),
			"A contested focus grows him toward Contested bull, and says how far")
	_check(GameState.focus_trait(p, "ruck").is_empty(), "A midfielder's ruck focus names no trait")
	p["attr"]["contested_ball"] = 99
	_check(GameState.focus_trait(p, "contested_ball").is_empty() or Traits.of(p).size() >= Traits.MAX_GOOD,
			"Once he has it the focus names it no more")
	# Bug bash 5: Defensive forward is a forward's own job, so a midfielder who
	# also plays forward is never pointed at it.
	var mf := {"id": "b5_df", "role": "MID", "role2": "FWD", "attr": {"pressure": 70}}
	_check(str(GameState.focus_trait(mf, "pressure").get("key", "")) != "def_forward",
			"A pressure focus never points a midfielder at Defensive forward")


## Every club gets it: a rival player near a synergy trait puts his focus on
## it, keeps it, and his training lifts that stat.
func _test_rivals_grow_traits() -> void:
	_new_season()
	var p := {}
	var stat := ""
	for code in GameState.season.lists:
		if str(code) == GameState.my_club:
			continue
		for q in GameState.season.lists[code]:
			var s := GameState._ai_trait_focus(q)
			if s != "":
				p = q
				stat = s
				break
		if not p.is_empty():
			break
	_check(not p.is_empty(), "Some rival player is working toward a synergy trait")
	if p.is_empty():
		return
	_check(str(p.get("train_focus", "")) == stat and GameState._ai_trait_focus(p) == stat, "He keeps his focus")
	var ft := GameState.focus_trait(p, stat)
	_check(not ft.is_empty() and int(ft["gap"]) <= GameState.AI_TRAIT_REACH, "It is a trait within reach")
	var before := int(p["attr"][stat])
	# A season's XP to spend.
	p["xp"] = float(p.get("xp", 0)) + 3000.0
	GameState.ai_spend_xp(p)
	_check(int(p["attr"][stat]) > before, "His training lifts the focus stat (%d to %d)" % [before, int(p["attr"][stat])])
