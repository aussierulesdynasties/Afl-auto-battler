extends SceneTree
## godot --headless --path . --script tests/run_plays_like_tests.gd
## "Plays like: <real AFL player>" on every draftee (director, 2026-11-12):
## the rule (scripts/sim/PlaysLike.gd) uses position, height and the ratings
## at max potential with their level, each proven on made-up players where
## only that fact differs; over 500 generated prospects the name is a real
## player of the same position, of about the prospect's level, never himself,
## the same on a second ask and after the lists age; and the line is on the
## National Draft, League Draft, Rookie Draft and mid-season draft screens on
## a phone, found after a real tap (tests/tap.gd).

const Tap := preload("res://tests/tap.gd")
const SUITE_SEED := 2045
const PHONE := Vector2i(390, 844)
## The named player's overall at his peak is within this many points of the
## prospect's POT for at least NEAR_SHARE of the generated prospects.
const LEVEL_BAND := 3.0
const NEAR_SHARE := 0.9
const FIRST_YEAR := 2045
const CLASSES := 11

var _state: Node
var _db: Node
var PL
var Pr
var Rt
var _checks := 0
var _failures: Array[String] = []
var _prospects: Array = []


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _settle(n := 6) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	PL = load("res://scripts/sim/PlaysLike.gd")
	Pr = load("res://scripts/sim/Prospects.gd")
	Rt = load("res://scripts/sim/Ratings.gd")
	_state.autosave_enabled = false
	_state.save_path = "user://test_plays_like.save"
	_state.settings_path = "user://test_plays_like.cfg"
	_state.delete_saved_career()
	_state.replay_seed = SUITE_SEED
	root.size = PHONE
	for y in range(FIRST_YEAR, FIRST_YEAR + CLASSES):
		_prospects.append_array(Pr.generate_class(y, 7))
	_t("_test_position_decides")
	_t("_test_height_decides")
	_t("_test_spread_decides")
	_t("_test_level_decides")
	_t("_test_durability_is_not_compared")
	_t("_test_strengths_count_for_more")
	_t("_test_pool_is_the_real_lists")
	_t("_test_500_generated_prospects")
	_t("_test_never_himself")
	_t("_test_two_real_players_one_name")
	_t("_test_same_after_the_lists_age")
	_t("_test_its_own_line_not_his_name")
	_t("_test_another_dataset_has_a_pool")
	await _t("_test_nobody_to_compare")
	await _t("_test_scouting_list_tap")
	await _t("_test_national_draft_tap")
	await _t("_test_league_draft_tap")
	await _t("_test_rookie_draft_sheet")
	await _t("_test_midseason_draft_sheet")
	_state.delete_saved_career()
	_state.replay_seed = 0
	print(Ran.line("Plays like", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(1 if not _failures.is_empty() else 0)


# --- made-up players: one fact differs at a time ---------------------------

## A player with every rated attribute at `base`, then `bumps` added.
func _man(id: String, role: String, cm: float, pot: int, bumps := {}, base := 60) -> Dictionary:
	var a := {}
	for key in Pr.ATTR_KEYS:
		a[key] = base + int(bumps.get(key, 0))
	var ovr: int = Rt.rate_overall(a, role, 14.0)
	return {"id": id, "real_name": "Real " + id, "generic_name": "Alias " + id, "role": role,
			"height_cm": cm, "attr": a, "overall": mini(ovr, pot), "potential": pot}


func _named(p: Dictionary, men: Array) -> String:
	var e: Dictionary = PL.nearest(p, PL.build_pool(men))
	return str(e.get("id", ""))


const BULL := {"contested": 18, "pressure": 8, "carry": -10, "disposal": -8}
const RUNNER := {"carry": 18, "disposal": 10, "contested": -12, "pressure": -8}


func _test_position_decides() -> void:
	var me := _man("me", "MID", 186.0, 80, BULL)
	me["real_name"] = ""
	# The forward is the same man in every number; the midfielder is not.
	var fwd := _man("fwd", "FWD", 186.0, 80, BULL)
	var mid := _man("mid", "MID", 189.0, 84, RUNNER)
	_check(_named(me, [fwd, mid]) == "mid", "A midfielder is likened to a midfielder, not to a forward with his exact ratings and height")
	me["role"] = "FWD"
	_check(_named(me, [fwd, mid]) == "fwd", "The same man listed as a forward is likened to the forward")
	me["role"] = "RUCK"
	_check(_named(me, [fwd, mid]) != "", "With no real player of his position, every real player is compared (one is still named)")
	_check(_named(me, []) == "" and PL.nearest(me, []).is_empty(), "Nobody to compare with: no name")


func _test_height_decides() -> void:
	var me := _man("me", "DEF", 190.0, 80, BULL)
	me["real_name"] = ""
	# Similar height first: the exact ratings 10 cm away lose to near ratings 2 cm away.
	var twin_tall := _man("twin_tall", "DEF", 200.0, 80, BULL)
	var close := _man("close", "DEF", 192.0, 82, {"contested": 14, "pressure": 8, "carry": -8, "disposal": -8})
	_check(_named(me, [twin_tall, close]) == "close", "A real player within 4 cm is preferred to one 10 cm taller with the exact ratings")
	# Inside the band, height is still part of the distance.
	var plus1 := _man("plus1", "DEF", 191.0, 80, BULL)
	var plus3 := _man("plus3", "DEF", 193.0, 80, BULL)
	_check(_named(me, [plus3, plus1]) == "plus1" and _named(me, [plus1, plus3]) == "plus1",
			"Of two real players with the same ratings, the one nearer his height is named, whatever the order")
	# Nobody within 4 cm: the whole position is compared and height still counts.
	var plus6 := _man("plus6", "DEF", 196.0, 80, BULL)
	var plus12 := _man("plus12", "DEF", 202.0, 80, BULL)
	_check(_named(me, [plus12, plus6]) == "plus6", "With nobody within 4 cm, the nearer height of two equal players is named")
	me["height_cm"] = 199.0
	_check(_named(me, [twin_tall, close]) == "twin_tall", "Make him 199 cm and the 200 cm player is named instead")
	# A small forward with a star's ceiling: no real player is both of his level
	# and his height, and he is still not likened to a key forward of his level.
	var small := _man("me", "FWD", 176.0, 91, RUNNER)
	small["real_name"] = ""
	var key_fwd := _man("key_fwd", "FWD", 196.0, 91, RUNNER)
	var small_fwd := _man("small_fwd", "FWD", 170.0, 89, {"carry": 14, "disposal": 8, "contested": -8, "pressure": -4})
	_check(_named(small, [key_fwd, small_fwd]) == "small_fwd",
			"A 176 cm forward with 91 POT is likened to the 170 cm forward of 89, not the 196 cm forward with his exact ratings")
	var tall_small: float = PL.distance(PL.profile(small), PL.profile(key_fwd, true))
	_check(tall_small >= 20.0 * PL.CM_POINTS + 16.0 * PL.FAR_POINTS - 0.01,
			"20 cm costs %.1f rating points: 0.5 a centimetre and 2 more for each beyond 4" % tall_small)


func _test_spread_decides() -> void:
	var me := _man("me", "MID", 186.0, 82, BULL)
	me["real_name"] = ""
	var bull := _man("bull", "MID", 186.0, 82, BULL)
	var runner := _man("runner", "MID", 186.0, 82, RUNNER)
	_check(_named(me, [runner, bull]) == "bull", "Same position, height and level: the contested bull is likened to the bull")
	var other := _man("me", "MID", 186.0, 82, RUNNER)
	other["real_name"] = ""
	_check(_named(other, [runner, bull]) == "runner", "And the runner to the runner")
	# The spread is read at his max potential, not at tonight's rating.
	var raw := _man("me", "MID", 186.0, 82, BULL, 40)
	raw["real_name"] = ""
	_check(int(raw["overall"]) < 70 and _named(raw, [runner, bull]) == "bull",
			"A raw prospect (%d now, 82 POT) is compared as he will be at 82" % int(raw["overall"]))


func _test_level_decides() -> void:
	var men := []
	for pot in [62, 70, 78, 86, 94]:
		men.append(_man("pot%d" % pot, "MID", 186.0, pot, BULL))
	var named := []
	for pot in [63, 71, 77, 85, 93]:
		var me := _man("me", "MID", 186.0, pot, BULL)
		me["real_name"] = ""
		named.append(_named(me, men))
	_check(named == ["pot62", "pot70", "pot78", "pot86", "pot94"],
			"The same build at five ceilings names five real players, each of about that level (%s)" % str(named))
	# Level is his POT itself, not what his ratings can be lifted to. A raw
	# ruck's ratings cannot be lifted 40 points, and he is still likened to a
	# real ruck of about his POT (the real lists).
	for case in [[200.0, 81], [206.0, 92]]:
		var raw := _man("me", "RUCK", float(case[0]), int(case[1]), {"ruck": 20, "contested": 10}, 22)
		raw["real_name"] = ""
		var prof: Dictionary = PL.profile(raw)
		var lifted := 0.0
		for x in prof["vec"]:
			lifted += float(x)
		lifted /= float((prof["vec"] as PackedFloat32Array).size())
		var got: Dictionary = PL.nearest(raw, _db.plays_like_pool)
		var best_gap := INF
		for e in _db.plays_like_pool:
			if str(e["role"]) == "RUCK":
				best_gap = minf(best_gap, absf(float(e["peak"]) - float(case[1])))
		_check(int(raw["overall"]) <= int(case[1]) - 30 and float(prof["peak"]) == float(case[1]) and lifted < float(case[1]) - 8.0,
				"A raw ruck (%d now, %d POT) is compared at %d although his ratings only lift to about %d" % [
				int(raw["overall"]), int(case[1]), int(prof["peak"]), int(lifted)])
		_check(not got.is_empty() and absf(float(got["peak"]) - float(case[1])) <= maxf(PL.NEAR_LEVEL, best_gap + 1.0),
				"He is likened to a real ruck of about %d: %s, peak %d (the nearest real ruck is %d away)" % [
				int(case[1]), str(got.get("real_name", "")), int(got.get("peak", 0)), int(best_gap)])
	# Level and height are weighed together: his twin in height 12 points better
	# loses to a player of his level 8 cm taller.
	var mine := _man("me", "MID", 186.0, 72, BULL)
	mine["real_name"] = ""
	var star := _man("star", "MID", 186.0, 84, BULL)
	var peer := _man("peer", "MID", 194.0, 73, BULL)
	_check(_named(mine, [star, peer]) == "peer", "A 72 POT prospect is likened to the 73 a head taller, not the 84 of his exact height")
	# Raising a prospect across the board moves the name to a higher-rated real player.
	var pool: Array = _db.plays_like_pool
	var higher := 0
	var lower := 0
	var tried := 0
	for p in _prospects.slice(0, 120):
		if int(p["potential"]) > 78:
			continue
		tried += 1
		var up: Dictionary = p.duplicate(true)
		up["potential"] = int(p["potential"]) + 12
		var was: Dictionary = PL.nearest(p, pool)
		var now: Dictionary = PL.nearest(up, pool)
		if float(now["peak"]) > float(was["peak"]):
			higher += 1
		elif float(now["peak"]) < float(was["peak"]):
			lower += 1
	_check(tried >= 30, "Enough generated prospects with room to raise (%d)" % tried)
	_check(lower == 0 and higher >= int(ceil(tried * 0.95)),
			"12 more points of POT names a higher-rated real player (%d of %d higher, %d lower)" % [higher, tried, lower])


func _test_durability_is_not_compared() -> void:
	var left_out := []
	for key in Pr.ATTR_KEYS:
		if not PL.KEYS.has(key) and not Pr.UNRATED_KEYS.has(key):
			left_out.append(key)
	_check(left_out == ["durability"] and PL.KEYS.size() == Pr.ATTR_KEYS.size() - Pr.UNRATED_KEYS.size() - 1,
			"Durability is the one rated attribute left out (%s; %d compared)" % [str(left_out), PL.KEYS.size()])
	var me := _man("me", "MID", 186.0, 82, BULL)
	me["real_name"] = ""
	me["attr"]["durability"] = 95
	# The runner shares his durability; the bull has none of it.
	var runner := _man("runner", "MID", 186.0, 82, RUNNER)
	runner["attr"]["durability"] = 95
	var bull := _man("bull", "MID", 186.0, 82, BULL)
	bull["attr"]["durability"] = 30
	_check(_named(me, [runner, bull]) == "bull", "A durable bull is likened to the bull who is often hurt, not the durable runner")


func _test_strengths_count_for_more() -> void:
	# Each real player misses him by 20 points in one attribute: one in the
	# thing he is best at, the other in something he is ordinary at.
	var me := _man("me", "MID", 186.0, 80, {"carry": 25})
	me["real_name"] = ""
	var no_run := _man("no_run", "MID", 186.0, 80, {"carry": 5})
	var no_mark := _man("no_mark", "MID", 186.0, 80, {"carry": 25, "marking": -20})
	for q in [me, no_run, no_mark]:
		q["overall"] = 80   # compared as rated: nobody is lifted
	var a: Dictionary = PL.profile(me)
	_check(PL.rating_gap(a, PL.profile(no_run, true)) > PL.rating_gap(a, PL.profile(no_mark, true)) + 2.0,
			"A 20 point miss in his best attribute is a wider gap than a 20 point miss in an ordinary one (%.1f against %.1f)" % [
			PL.rating_gap(a, PL.profile(no_run, true)), PL.rating_gap(a, PL.profile(no_mark, true))])
	_check(_named(me, [no_run, no_mark]) == "no_mark", "The line-breaker is likened to the real player who also carries the ball")


# --- the real lists and 500 generated prospects ------------------------------

func _test_pool_is_the_real_lists() -> void:
	var pool: Array = _db.plays_like_pool
	_check(pool.size() >= 600, "The pool is the launch lists (%d real players)" % pool.size())
	var real := {}
	for q in _db.players:
		real[str(q["id"])] = q
	var roles := {}
	var bad := 0
	var eg := ""
	for e in pool:
		roles[str(e["role"])] = true
		var q: Dictionary = real.get(str(e["id"]), {})
		if q.is_empty() or str(q["real_name"]) != str(e["real_name"]) or float(e["height"]) <= 0.0 \
				or bool(q.get("projected", false)) or float(e["peak"]) < float(q["overall"]) - 1.0:
			bad += 1
			eg = "%s peak %d, today %d" % [str(e["real_name"]), int(e["peak"]), int(q.get("overall", 0))]
	_check(bad == 0, "Every entry is a listed real player with a height, senior ratings and a peak no lower than today (%d are not: %s)" % [bad, eg])
	_check(roles.size() == 4, "All four positions have real players (%s)" % str(roles.keys()))


func _test_500_generated_prospects() -> void:
	var pool: Array = _db.plays_like_pool
	_check(_prospects.size() >= 500, "At least 500 generated prospects (%d)" % _prospects.size())
	var real_names := {}
	for q in _db.players:
		real_names[str(q["real_name"])] = true
	var names := {}
	var wrong_role := 0
	var not_real := 0
	var moved := 0
	var in_band := 0
	var near_cm := 0
	var far_cm_unforced := 0
	var far_level_unforced := 0
	var worst_level := 0.0
	var worst_cm := 0.0
	var lacks_strength := 0
	var times := {}
	for p in _prospects:
		var e: Dictionary = PL.nearest(p, pool)
		if e.is_empty() or not real_names.has(str(e["real_name"])):
			not_real += 1
			continue
		names[str(e["real_name"])] = true
		if str(e["role"]) != str(p["role"]):
			wrong_role += 1
		if str((PL.nearest(p.duplicate(true), pool) as Dictionary)["id"]) != str(e["id"]) \
				or PL.line(p) != PL.LABEL + str(PL.shown_name(e, pool)):
			moved += 1
		# Level is measured against his POT itself.
		var gap := absf(float(e["peak"]) - float(p["potential"]))
		if gap <= LEVEL_BAND:
			in_band += 1
		worst_level = maxf(worst_level, gap)
		var cm := absf(float(e["height"]) - float(p["height_cm"]))
		if cm <= PL.NEAR_CM:
			near_cm += 1
		worst_cm = maxf(worst_cm, cm)
		# A real player of his position inside both bands exists: the name is inside both.
		if pool.any(func(c): return str(c["role"]) == str(p["role"]) and absf(float(c["height"]) - float(p["height_cm"])) <= 4.0 and absf(float(c["peak"]) - float(p["potential"])) <= 5.0):
			if cm > 4.0:
				far_cm_unforced += 1
			if gap > 5.0:
				far_level_unforced += 1
		# His best attribute at his peak, and how far under it the named player is.
		var mine: PackedFloat32Array = PL.profile(p)["vec"]
		var top := 0
		for i in range(mine.size()):
			if mine[i] > mine[top]:
				top = i
		if mine[top] - float((e["vec"] as PackedFloat32Array)[top]) >= 15.0:
			lacks_strength += 1
		times[str(e["real_name"])] = int(times.get(str(e["real_name"]), 0)) + 1
	var n := _prospects.size()
	var most := 0
	for k in times:
		most = maxi(most, int(times[k]))
	_check(far_level_unforced == 0, "Nobody is likened to a player more than 5 from his POT when one within 5 and within 4 cm exists (%d)" % far_level_unforced)
	_check(worst_level <= 8.0, "No named player's peak is more than 8 from the prospect's POT (widest %d)" % int(worst_level))
	_check(worst_cm <= 10.0, "No named player is more than 10 cm from the prospect (widest %d)" % int(worst_cm))
	_check(lacks_strength <= int(n * 0.12),
			"The prospect's best attribute is 15 or more points lower in the named player for at most 12%% (%d of %d)" % [lacks_strength, n])
	_check(most <= int(n * 0.03), "No real player is named for more than 3%% of prospects (most %d of %d)" % [most, n])
	_check(not_real == 0, "Every prospect is likened to a real player from the lists (%d are not)" % not_real)
	_check(wrong_role == 0, "Always a real player of his own position (%d are not)" % wrong_role)
	_check(moved == 0, "Asked again, and through the line the screens show, the name is the same (%d moved)" % moved)
	_check(names.size() >= 40, "500 prospects name at least 40 different real players (%d)" % names.size())
	_check(in_band >= int(ceil(n * NEAR_SHARE)),
			"The named player's peak overall is within %d of the prospect's POT for at least 90%% (%d of %d)" % [int(LEVEL_BAND), in_band, n])
	_check(far_cm_unforced == 0, "Nobody is likened to a player more than 4 cm off when one within 5 of his POT and within 4 cm exists (%d)" % far_cm_unforced)
	var intl := _prospects.filter(func(p): return p.has("intl"))
	_check(intl.size() >= 5, "The generated classes hold international prospects (%d)" % intl.size())
	for p in intl:
		_check(PL.line(p) != "", "International prospect %s has a line" % _db.player_display_name(p))
	_check(near_cm >= int(ceil(n * 0.95)), "At least 95%% are likened to a player within 4 cm (%d of %d)" % [near_cm, n])


func _test_never_himself() -> void:
	var pool: Array = _db.plays_like_pool
	var listed: Array = _db.players
	_check(listed.size() >= 600 and _db.draftees.size() >= 40, "The real lists and the real 2026 class are loaded")
	var himself := 0
	var unnamed := 0
	for p in listed + _db.draftees:
		var e: Dictionary = PL.nearest(p, pool)
		if e.is_empty():
			unnamed += 1
		elif str(e["real_name"]) == str(p.get("real_name", "")) or str(e["id"]) == str(p["id"]):
			himself += 1
	_check(himself == 0, "No real player or real draftee is likened to himself (%d are)" % himself)
	_check(unnamed == 0, "Every real player and real draftee has a name to show (%d have none)" % unnamed)


func _test_same_after_the_lists_age() -> void:
	var sample: Array = _prospects.slice(0, 60)
	var before := []
	for p in sample:
		before.append(PL.line(p))
	# A career ages and retrains the listed players in place; the comparison
	# is with the lists as they were at the start.
	for q in _db.players:
		q["overall"] = maxi(30, int(q["overall"]) - 15)
		q["potential"] = int(q["overall"])
		q["age"] = float(q["age"]) + 15.0
		for key in q["attr"]:
			q["attr"][key] = maxi(1, int(q["attr"][key]) - 15)
	var after := []
	for p in sample:
		after.append(PL.line(p))
	_check(after == before, "Fifteen seasons on the lists changes nobody's line")
	_db.reload()
	_state.reset()
	var reloaded := []
	for p in sample:
		reloaded.append(PL.line(p))
	_check(reloaded == before, "A reload of the data gives the same lines")
	# No club in it: the line reads the same whoever coaches.
	_state.my_club = "FRE"
	var fre: String = PL.line(sample[0])
	_state.my_club = "MEL"
	_check(PL.line(sample[0]) == fre and fre != "", "Fremantle and Melbourne read the same line")
	_state.my_club = ""


func _test_its_own_line_not_his_name() -> void:
	var p: Dictionary = _prospects[0]
	var line: String = PL.line(p)
	_check(line.begins_with("Plays like: ") and line.length() > "Plays like: ".length(), "The line reads \"Plays like: <name>\" (%s)" % line)
	_check(not _db.player_display_name(p).to_lower().contains("plays like"), "His display name still carries no \"plays like\"")
	# The longest line fits a phone row beside its button.
	var UK = load("res://scripts/ui/UiKit.gd")
	for key in ["real_name"]:
		var widest := ""
		var w := 0.0
		for c in _db.plays_like_pool:
			var l: Label = UK.lbl("Plays like: " + str(c[key]), UK.SECONDARY)
			root.add_child(l)
			if l.get_combined_minimum_size().x > w:
				w = l.get_combined_minimum_size().x
				widest = str(c[key])
			l.free()
		_check(w > 0.0 and w <= 270.0, "\"Plays like: %s\" (the widest %s) is %.0f px: one line in a 390 phone row beside its button" % [widest, key, w])


# --- the draft screens, by real taps -------------------------------------------

func _whole(l: Label) -> bool:
	if l == null or not is_instance_valid(l) or not l.is_visible_in_tree():
		return false
	if l.get_visible_line_count() < l.get_line_count():
		return false
	var r := l.get_global_rect()
	return r.position.x >= -0.5 and r.end.x <= float(root.size.x) + 0.5 and r.size.x > 0.0


## The label is the next line down from the one before it in his row (named
## `above`, when given), and inside that row's box.
func _under_the_line_above(l: Label, above := "") -> bool:
	var box := l.get_parent() as Control
	if box == null or l.get_index() == 0:
		return false
	var prev := box.get_child(l.get_index() - 1) as Control
	if prev == null or (above != "" and not str(prev.name).begins_with(above)):
		return false
	var r := l.get_global_rect()
	return r.position.y >= prev.get_global_rect().end.y - 0.5 and box.get_global_rect().grow(0.5).encloses(r)


## A phone-width row's line is right, whole and under his name, not in it.
func _check_row_line(host: Node, p: Dictionary, what: String, above := "") -> void:
	var l := host.find_child("PlaysLike_" + str(p["id"]), true, false) as Label
	_check(l != null, "%s: %s has a Plays like line" % [what, _db.player_display_name(p)])
	if l == null:
		return
	_check(l.text == PL.line(p), "%s: it names the real player the rule gives (%s)" % [what, l.text])
	_check(_whole(l), "%s: the line is whole on a 390 wide phone (%s)" % [what, l.text])
	_check(_under_the_line_above(l, above), "%s: it sits under %s, inside his row (%s)" % [what, "the line above it" if above == "" else above, l.text])


func _fresh_career(club := "FRE") -> void:
	_state.reset()
	_state.career_seed = SUITE_SEED
	_state.replay_seed = SUITE_SEED
	_state.start_season(club, _db.club_list(club))
	_state.tutorials = false
	_state.set_setting("seen_weekly_loop_intro", true)


func _open_and_check_detail(ui: Control, p: Dictionary, what: String) -> void:
	var inspect := ui.find_child("Inspect_" + str(p["id"]), true, false) as Button
	_check(inspect != null, "%s: his row is on the board" % what)
	if inspect == null:
		return
	var why: String = await Tap.tap(inspect)
	_check(why == "", "%s: a real tap opens him (%s)" % [what, why])
	await _settle()
	var detail := ui.find_child("PlayerDetail", true, false)
	_check(detail != null, "%s: his details open" % what)
	if detail == null:
		return
	var l := detail.find_child("DetailPlaysLike", true, false) as Label
	_check(l != null and l.text == PL.line(p) and l.text != "", "%s: his details say %s" % [what, PL.line(p)])
	_check(_whole(l), "%s: the line in his details is whole on the phone" % what)
	var name_l := detail.find_child("DetailName", true, false) as Label
	_check(name_l != null and not name_l.text.to_lower().contains("plays like")
			and l != null and l.get_global_rect().position.y >= name_l.get_global_rect().end.y - 0.5,
			"%s: it is its own line under his name" % what)
	var close := detail.find_child("DetailClose", true, false) as Button
	why = await Tap.tap(close)
	_check(why == "", "%s: a real tap on Close reaches it (%s)" % [what, why])
	await _settle()
	_check(ui.find_child("PlayerDetail", true, false) == null or not (ui.find_child("PlayerDetail", true, false) as Control).is_visible_in_tree(),
			"%s: his details close" % what)


func _test_national_draft_tap() -> void:
	_fresh_career()
	_state.season.round_index = _state.season.fixture.size()
	_state.open_offseason()
	# An international prospect is in this class (they come with the generated classes).
	var abroad: Dictionary = (_prospects.filter(func(p): return p.has("intl"))[0] as Dictionary).duplicate(true)
	abroad["id"] = "pl_test_intl"
	abroad["draft_year"] = _state.season_year
	_state.draftee_pool.append(abroad)
	_check(_state.begin_intake_draft(), "The National Draft opens")
	var draft = _state.draft
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _settle()
	var done := ui.find_child("MeetingDone", true, false) as Button
	_check(done != null, "The draft meeting opens first")
	if done != null:
		var missed: String = await Tap.tap(done)
		_check(missed == "", "A real tap on To the draft reaches it (%s)" % missed)
		await _settle()
	_check(ui.find_child("DraftMeeting", true, false) == null, "The meeting is closed and the board is in reach")
	var board: Array = draft.board("", "", "", "overall", true)
	_check(board.size() >= 30, "The class is on the board (%d)" % board.size())
	var rows := 0
	for p in board:
		if ui.find_child("Inspect_" + str(p["id"]), true, false) != null:
			rows += 1
			_check_row_line(ui, p, "National Draft", "Kind_")
	_check(rows == board.size(), "Every prospect row was checked (%d of %d)" % [rows, board.size()])
	var intl := board.filter(func(p): return str(p["id"]) == "pl_test_intl")
	_check(intl.size() == 1 and (intl[0] as Dictionary).has("intl"), "The international prospect is on the board")
	await _open_and_check_detail(ui, board[0], "National Draft")
	if intl.size() == 1:
		await _open_and_check_detail(ui, intl[0], "National Draft, international")
	# Once he is ours: the My list tab names him and still says who he plays like.
	var guard := 0
	while not draft.is_finished() and str(draft.current_club()) != "FRE" and guard < 400:
		guard += 1
		var c: Dictionary = draft._best_ai_pick(draft.current_club())
		if c.is_empty() or not draft._draft_pick(draft.current_club(), c):
			draft._skip_current_pick()
	var ours: Dictionary = draft.board("", "", "", "overall", true)[0]
	_check(str(draft.current_club()) == "FRE" and draft.pick(ours), "Fremantle's pick comes and takes %s" % _db.player_display_name(ours))
	ui.call("_refresh")   # the picks above were made under the screen
	await _settle()
	var tab := ui.find_child("Tab_squad", true, false) as Button
	var tab_missed: String = await Tap.tap(tab)
	_check(tab_missed == "", "A real tap opens My list (%s)" % tab_missed)
	await _settle()
	var picked := ui.find_child("PickedName_" + str(ours["id"]), true, false)
	_check(picked != null and (picked as Control).is_visible_in_tree(), "My list names the pick")
	if picked != null:
		_check_row_line(_row_of(picked), ours, "My list")
	ui.queue_free()
	await _settle()


func _test_league_draft_tap() -> void:
	_state.reset()
	_state.replay_seed = SUITE_SEED
	_state.tutorials = false
	_state.draft = load("res://scripts/sim/Draft.gd").new(_db.all_players_sorted(),
			_db.active_clubs(2027).duplicate(), SUITE_SEED)
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _settle()
	var choose := ui.find_child("Choose_FRE", true, false) as Button
	var missed: String = await Tap.tap(choose)
	_check(missed == "", "A real tap chooses Fremantle (%s)" % missed)
	await _settle()
	var rows := ui.find_children("Inspect_*", "Button", true, false)
	_check(rows.size() >= 20, "The League Draft board shows its players (%d)" % rows.size())
	var first := {}
	for b in rows:
		var id := str(b.name).trim_prefix("Inspect_")
		var p: Dictionary = ui.call("_player_by_id", id)
		if first.is_empty():
			first = p
		_check_row_line(ui, p, "League Draft", "Kind_")
	_check(not first.is_empty(), "A player to open")
	if not first.is_empty():
		await _open_and_check_detail(ui, first, "League Draft")
	ui.queue_free()
	await _settle()
	_state.draft = null


func _test_rookie_draft_sheet() -> void:
	_fresh_career()
	_state.season.round_index = _state.season.fixture.size()
	var ok: bool = _state.begin_intake_draft()
	_check(ok, "The National Draft opens before the Rookie Draft")
	if not ok:
		return
	var draft = _state.draft
	while not draft.is_finished():
		var candidate: Dictionary = draft._best_ai_pick(draft.current_club())
		if candidate.is_empty() or not draft._draft_pick(draft.current_club(), candidate):
			draft._skip_current_pick()
	_check(_state.finish_intake_draft(), "The rollover commits")
	var RL = load("res://scripts/state/RookieList.gd")
	var MD = load("res://scripts/state/MidseasonDraft.gd")
	_check(RL.waiting(_state), "A rookie pick waits")
	if not RL.waiting(_state):
		return
	if _state.needs_season_wrap():
		_state.begin_season_from_wrap()
	var path := "res://scenes/PreSeasonScene.tscn" if _state.preseason_active() else "res://scenes/HubScene.tscn"
	var scene: Control = load(path).instantiate()
	root.add_child(scene)
	await _settle()
	var sheet := scene.get_node_or_null("RookieDraft")
	_check(sheet != null, "The Rookie Draft sheet opens")
	if sheet != null:
		var shown: Array = MD.pool(_state).slice(0, 8)
		_check(shown.size() >= 3, "Players are left to take (%d)" % shown.size())
		var drawn := sheet.find_children("RookiePick_*", "Button", true, false)
		var lines := sheet.find_children("PlaysLike_*", "Label", true, false)
		_check(drawn.size() == shown.size() and lines.size() == drawn.size(),
				"Rookie Draft: the sheet draws those %d players and every row has a line (%d rows, %d lines)" % [shown.size(), drawn.size(), lines.size()])
		for p in shown:
			_check(sheet.find_child("RookiePick_" + str(p["id"]), true, false) != null, "Rookie Draft: %s has a row" % _db.player_display_name(p))
			_check_row_line(sheet, p, "Rookie Draft")
		# The line takes nothing from the button: a real tap on Pick still lands.
		var btn := sheet.find_child("RookiePick_%s" % str(shown[0]["id"]), true, false) as Button
		var why: String = await Tap.tap(btn)
		_check(why == "", "Rookie Draft: a real tap on Pick reaches it (%s)" % why)
		await _settle()
	scene.queue_free()
	await _settle()


func _test_midseason_draft_sheet() -> void:
	_fresh_career()
	var MD = load("res://scripts/state/MidseasonDraft.gd")
	var Ct = load("res://scripts/sim/Contracts.gd")
	var year: int = _state.season_year
	# Last year's leftovers, so players are left when our turn comes.
	var class_now: Array = _state.draftee_pool.filter(func(p): return int(p.get("draft_year", year)) == year)
	for i in mini(25, class_now.size()):
		(class_now[class_now.size() - 1 - i] as Dictionary)["draft_year"] = year - 1
	while (_state.season.lists["FRE"] as Array).size() >= Ct.MAX_LIST:
		(_state.season.lists["FRE"] as Array).pop_back()
	var guard := 0
	while _state.season.round_index < MD.DRAFT_AFTER and guard < 40:
		_state.advance()
		guard += 1
	_check(MD.waiting(_state), "Our mid-season pick waits")
	if not MD.waiting(_state):
		return
	MD.close_carnival(_state)   # the carnival sheet was read when it came
	for card in _state.week_events:
		(card as Dictionary)["popped"] = true
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	var sheet := hub.find_child("MidseasonDraft", true, false)
	_check(sheet != null, "The mid-season draft sheet opens on the hub")
	if sheet != null:
		var shown: Array = MD.pool(_state).slice(0, 8)
		_check(shown.size() >= 3, "Players are left to take (%d)" % shown.size())
		var drawn := sheet.find_children("MidseasonPick_*", "Button", true, false)
		var lines := sheet.find_children("PlaysLike_*", "Label", true, false)
		_check(drawn.size() == shown.size() and lines.size() == drawn.size(),
				"Mid-season draft: the sheet draws those %d players and every row has a line (%d rows, %d lines)" % [shown.size(), drawn.size(), lines.size()])
		for p in shown:
			_check(sheet.find_child("MidseasonPick_" + str(p["id"]), true, false) != null, "Mid-season draft: %s has a row" % _db.player_display_name(p))
			_check_row_line(sheet, p, "Mid-season draft")
		var btn := sheet.find_child("MidseasonPick_%s" % str(shown[0]["id"]), true, false) as Button
		var why: String = await Tap.tap(btn)
		_check(why == "", "Mid-season draft: a real tap on Pick reaches it (%s)" % why)
		await _settle()
	hub.queue_free()
	await _settle()


## The nearest box above `n` that holds a Plays like line (his row).
func _row_of(n: Node) -> Node:
	var at := n.get_parent()
	while at != null and at.find_children("PlaysLike_*", "Label", true, false).is_empty():
		at = at.get_parent()
	return at if at != null else n


# --- the other screens and the empty cases ---------------------------------------

func _test_two_real_players_one_name() -> void:
	var a := _man("twin_a", "DEF", 190.0, 80, BULL)
	var b := _man("twin_b", "DEF", 199.0, 80, BULL)
	var c := _man("other", "DEF", 191.0, 80, RUNNER)
	a["real_name"] = "Sam Twin"
	a["club"] = "FRE"
	b["real_name"] = "Sam Twin"
	b["club"] = "MEL"
	var pool: Array = PL.build_pool([a, b, c])
	_check(PL.shown_name(pool[0], pool) == "Sam Twin (%s)" % _db.club_short("FRE")
			and PL.shown_name(pool[1], pool) == "Sam Twin (%s)" % _db.club_short("MEL"),
			"Two real players with one name are told apart by club (%s, %s)" % [PL.shown_name(pool[0], pool), PL.shown_name(pool[1], pool)])
	_check(PL.shown_name(pool[2], pool) == "Real other", "A name only one real player has stays bare")
	# One of them can be likened to the other; neither to himself.
	_check(_named(a, [a, b]) == "twin_b" and _named(b, [a, b]) == "twin_a", "Each Sam Twin can be likened to the other, never to himself")
	# The same man under another id (a real draftee who is also listed) is still himself.
	var again: Dictionary = a.duplicate(true)
	again["id"] = "twin_a_draftee"
	_check(_named(again, [a, c]) == "other", "His own name at his own height is himself, whatever the id")
	# The real lists: any shared name is shown with a club, and the line carries it.
	var real: Array = _db.plays_like_pool
	var seen := {}
	var shared := []
	for e in real:
		if seen.has(str(e["real_name"])):
			shared.append(e)
			shared.append(seen[str(e["real_name"])])
		seen[str(e["real_name"])] = e
	_check(shared.size() >= 2, "The real lists hold two players with one name (%d entries)" % shared.size())
	var shown := {}
	for e in shared:
		shown[PL.shown_name(e, real)] = true
		_check(str(PL.shown_name(e, real)).ends_with("(%s)" % _db.club_short(str(e["club"]))), "%s is shown with his club" % PL.shown_name(e, real))
	_check(shown.size() == shared.size(), "Every shared name reads differently (%s)" % str(shown.keys()))


func _test_another_dataset_has_a_pool() -> void:
	# The stand-in for a Legacy set (tests/test_dataset.gd): a players file and nothing else.
	var DS = load("res://scripts/core/Datasets.gd")
	DS.add("test_plays_like_1989", {"data_season": 1989, "start_year": 1990, "start_date": "1990-03-01",
			"players": "res://tests/fixtures/dataset_1989_players.csv"})
	_db.reload("test_plays_like_1989")
	var pool: Array = _db.plays_like_pool
	_check(_db.players.size() >= 40 and pool.size() >= 30,
			"A set with only a players file still has real players to compare with (%d of %d listed)" % [pool.size(), _db.players.size()])
	var named := 0
	for p in _prospects.slice(0, 40):
		if str(PL.line(p)).begins_with(PL.LABEL):
			named += 1
	_check(named == 40, "Every prospect in that league has a line (%d of 40)" % named)
	DS.remove("test_plays_like_1989")
	_db.reload()
	_state.reset()
	_check(_db.plays_like_pool.size() >= 600, "Back on the 2026 lists (%d)" % _db.plays_like_pool.size())


func _test_nobody_to_compare() -> void:
	var PLL = load("res://scripts/ui/PlaysLikeLine.gd")
	var UK = load("res://scripts/ui/UiKit.gd")
	_fresh_career()
	var kept: Array = _db.plays_like_pool
	_db.plays_like_pool = []
	var p: Dictionary = _prospects[0]
	_check(PL.line(p) == "" and PLL.make(p) == null, "With no real player to compare, there is no line")
	var above: Label = UK.lbl("His name", 14)
	var got: Control = PLL.under(above, p)
	_check(got == above, "A sheet row is then his name alone")
	above.free()
	# A screen opened in that state shows its rows without the line.
	var sc: Control = load("res://scenes/ScoutingScene.tscn").instantiate()
	root.add_child(sc)
	await _settle()
	_check(sc.find_children("ClassAdd_*", "Button", true, false).size() >= 30
			and sc.find_children("PlaysLike_*", "Label", true, false).is_empty(),
			"The scouting list still shows the class, with no Plays like line")
	sc.queue_free()
	await _settle()
	_db.plays_like_pool = kept


func _test_scouting_list_tap() -> void:
	_fresh_career()
	var sc: Control = load("res://scenes/ScoutingScene.tscn").instantiate()
	root.add_child(sc)
	await _settle()
	var adds := sc.find_children("ClassAdd_*", "Button", true, false)
	_check(adds.size() >= 30, "The scouting list shows the coming class (%d)" % adds.size())
	var by_id := {}
	for q in _state.draftee_pool:
		by_id[str(q["id"])] = q
	var first := {}
	for b in adds:
		var p: Dictionary = by_id.get(str(b.name).trim_prefix("ClassAdd_"), {})
		_check(not p.is_empty(), "Scouting list: %s is a prospect of the class" % b.name)
		if p.is_empty():
			continue
		if first.is_empty():
			first = p
		_check_row_line(sc, p, "Scouting list")
	if first.is_empty():
		sc.queue_free()
		return
	# The line takes nothing from the button, and follows him onto your list.
	var add := sc.find_child("ClassAdd_" + str(first["id"]), true, false) as Button
	var missed: String = await Tap.tap(add)
	_check(missed == "", "Scouting list: a real tap on Add reaches it (%s)" % missed)
	await _settle()
	var listed := sc.find_child("ScoutRow_" + str(first["id"]), true, false)
	_check(listed != null, "He is on your list")
	if listed != null:
		_check_row_line(listed, first, "Scouting list, listed")
	sc.queue_free()
	await _settle()

