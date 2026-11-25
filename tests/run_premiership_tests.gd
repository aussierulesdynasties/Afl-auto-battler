extends SceneTree
## godot --headless --path . --script tests/run_premiership_tests.gd
## The premiership ceremony (director, 2026-11-25; design bible 161): the Grand
## Final's siren opens a stage in the premiers' colours before full time (his
## pick: Full goosebumps, no crowd dip). Proves: who gets a ceremony and what
## it says, its beats and its time to the final frame, the
## final frame fits a phone for all 18 clubs at every text size, a tap anywhere
## jumps to the final frame, a real finger reaches Continue at any moment,
## Android Back leaves, Reduced motion shows the final frame at once, the cup
## comes before a legend's farewell and full time opens still after it, another
## club's flag plays in its colours, and the hub's sim path opens it first.
## Classes are reached through load() and autoload nodes.

const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")
const SUITE_SEED := 2027
## The longest facts a ceremony can carry, for the layout's worst case.
const LONG := [
	"Beat Greater Western Sydney by 100 points after extra time, 25.18 (168) to 10.8 (68).",
	"Norm Smith Medal: Christopher Mayne-Wellington (Greater Western Sydney)",
	"Captains: Alexander Witherden-Smith, Bartholomew McDonald and Christopher Ashcroft",
	"The club's 17th premiership, its first since 1990, ending the longest wait in its history.",
]

var _state: Node
var _db: Node
var _uk: Object
var _feel: Object
var _pc: Object
var _checks := 0
var _failures: Array[String] = []
var _week := {}


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _settle(n := 6) -> void:
	for i in range(n):
		await process_frame


func _wait(secs: float) -> void:
	await create_timer(secs).timeout


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_uk = load("res://scripts/ui/UiKit.gd")
	_feel = load("res://scripts/ui/Feel.gd")
	_pc = load("res://scripts/ui/match/PremiershipCeremony.gd")
	_state.autosave_enabled = false
	_state.save_path = "user://test_premiership.save"
	_state.settings_path = "user://test_premiership.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	_state.replay_seed = SUITE_SEED
	root.size = Vector2i(390, 844)
	_feel.test_motion = true
	_feel.force_phone = true
	_state.set_reduced_motion(false)
	_state.set_screen_shake_on(true)
	await _settle()

	await _t("_test_facts")
	await _t("_test_casing")
	await _t("_test_beats")
	await _t("_test_layout_every_club")
	await _t("_test_tap_elsewhere")
	await _t("_test_continue_taps")
	await _t("_test_back")
	await _t("_test_reduced")
	await _t("_test_shake_off")
	await _t("_test_cup_before_farewell")
	await _t("_test_other_club_flag")
	await _t("_test_hub_sim_path")
	await _t("_test_gf_draw_none")

	_feel.test_motion = false
	_feel.force_phone = false
	_state.set_reduced_motion(false)
	_state.set_text_size("standard")
	print(Ran.line("Premiership", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(1 if not _failures.is_empty() else 0)


# --- Set-up ---------------------------------------------------------------------

## One seeded career plays round 1 once; each test starts from a fresh copy.
func _prime_week() -> void:
	if _week.is_empty():
		_state.reset()
		_state.replay_seed = SUITE_SEED
		_state.start_season("COL", _db.club_list("COL"))
		_state.advance()
		_week = {"match": _state.last_match.duplicate(true), "results": _state.last_results.duplicate(true)}
	_state.last_match = (_week["match"] as Dictionary).duplicate(true)
	_state.last_results = (_week["results"] as Array).duplicate(true)
	_state.last_injuries = []
	_state.last_mro = []


## The week's game made a Grand Final: your score and theirs as [goals, behinds].
func _gf(mine: Array, theirs: Array, extra := {}) -> Dictionary:
	_prime_week()
	var res: Dictionary = _state.last_match
	var me := 0 if str(res["home"]) == _state.my_club else 1
	var goals := [0, 0]
	var behinds := [0, 0]
	goals[me] = int(mine[0])
	behinds[me] = int(mine[1])
	goals[1 - me] = int(theirs[0])
	behinds[1 - me] = int(theirs[1])
	res["goals"] = goals
	res["behinds"] = behinds
	res["score"] = [goals[0] * 6 + behinds[0], goals[1] * 6 + behinds[1]]
	res["tag"] = "GF"
	res["label"] = "Grand Final"
	res.merge(extra, true)
	_state.last_match = res
	var rest: Array = []
	for r in _state.last_results:
		rest.append(res if _state.is_my_match(r) else r)
	_state.last_results = rest
	return res


func _opp(res: Dictionary) -> String:
	return str(res["away"]) if str(res["home"]) == _state.my_club else str(res["home"])


## Review match on a Grand Final: the ceremony opens as the scene does.
func _open_match(res: Dictionary, farewell := {}) -> Control:
	_state.last_match = res
	_state.last_pos_before = _state.my_position()
	_state.review_requested = true
	_feel.clear()
	var scene: Control = load("res://scenes/MatchScene.tscn").instantiate()
	if not farewell.is_empty():
		scene.set("_farewell", farewell)
	root.add_child(scene)
	return scene


## A bare stage: the ceremony over a host the size of the match's space under
## the scoreboard, with two score labels to beat.
func _open_bare(f: Dictionary, opts := {}, area := Vector2(390, 734)) -> Dictionary:
	var host := Control.new()
	host.name = "CeremonyHost"
	host.position = Vector2(0, 844.0 - area.y)
	host.size = area
	root.add_child(host)
	var pulse: Array = [Label.new(), Label.new()]
	for l in pulse:
		(l as Label).text = "88"
		host.add_child(l)
	var o := {"pulse": pulse}
	o.merge(opts, true)
	await process_frame
	_feel.clear()
	var t0 := Time.get_ticks_usec()
	var c: Control = _pc.open(host, f, o)
	return {"host": host, "c": c, "t0": t0, "pulse": pulse}


func _facts_for(premier: String, callouts: Array = LONG) -> Dictionary:
	var year: int = _state.season_year
	return {"premier": premier, "loser": "CAR" if premier != "CAR" else "COL", "year": year,
		"eyebrow": "%d Grand Final" % year, "callouts": callouts.duplicate()}


func _ceremony(n: Node) -> Control:
	return n.find_child("PremiershipCeremony", true, false) as Control


func _alpha_chain(n: Node) -> float:
	var a := 1.0
	while n != null:
		if n is CanvasItem:
			a *= (n as CanvasItem).modulate.a
		n = n.get_parent()
	return a


## Every piece in its final place: solid, full size, on its base, no flash,
## no shake.
func _at_rest_ok(c: Control) -> String:
	if not bool(c.get("at_rest")):
		return "not at rest"
	if float(c.get("_flash_a")) > 0.001:
		return "flash %.2f" % float(c.get("_flash_a"))
	var content: Control = c.get("_content")
	if absf(content.position.x) > 0.01:
		return "content shaken %.2f" % content.position.x
	for it in c.call("_items"):
		var n := it as Control
		if not is_equal_approx(n.modulate.a, 1.0) or not n.scale.is_equal_approx(Vector2.ONE):
			return "%s alpha %.2f scale %.2f" % [n.name, n.modulate.a, n.scale.x]
		if n.has_meta("_pc_base") and n.position.distance_to(n.get_meta("_pc_base")) > 0.01:
			return "%s off its place by %.1f" % [n.name, n.position.distance_to(n.get_meta("_pc_base"))]
	var art: Control = c.get("_flag_art")
	if art != null and not art.scale.is_equal_approx(Vector2.ONE):
		return "flag unfurled to %.2f" % art.scale.y
	return ""


## Watch until the final frame (or `limit` seconds): when it came, the
## brightest flash, the most the scorebug grew.
## Game time, not the wall clock: run_tests.sh runs suites at --fixed-fps 60,
## where headless frames come faster than real time. `t0` is kept for callers.
func _run_to_rest(c: Control, _t0: int, limit: float, pulse: Array = []) -> Dictionary:
	var out := {"secs": -1.0, "flash": 0.0, "pulse": 1.0}
	var secs := 0.0
	while secs < limit:
		await process_frame
		secs += root.get_process_delta_time()
		if not is_instance_valid(c):
			break
		out["flash"] = maxf(float(out["flash"]), float(c.get("_flash_a")))
		for l in pulse:
			out["pulse"] = maxf(float(out["pulse"]), (l as Control).scale.x)
		if bool(c.get("at_rest")):
			out["secs"] = secs
			break
	return out


# --- Tests ----------------------------------------------------------------------

## Who gets a ceremony, and what it says.
func _test_facts() -> void:
	_prime_week()
	var plain: Dictionary = _state.last_match.duplicate(true)
	_check((_pc.facts(plain) as Dictionary).is_empty(), "A home-and-away game gets no ceremony")
	var res := _gf([13, 5], [8, 5])
	var f: Dictionary = _pc.facts(res)
	var opp := _opp(res)
	var lines: Array = f.get("callouts", [])
	_check(str(f.get("premier", "")) == _state.my_club and str(f.get("loser", "")) == opp,
			"A Grand Final win: your club are premiers (%s)" % str(f.get("premier", "")))
	_check(str(f.get("eyebrow", "")) == "%d Grand Final" % _state.season_year and int(f.get("year", 0)) == _state.season_year,
			"The eyebrow names the year's Grand Final (%s)" % str(f.get("eyebrow", "")))
	_check(not lines.is_empty() and str(lines[0]).begins_with("Beat %s by 30 points, " % _db.club_name(opp)),
			"The first fact is the score in words (%s)" % (str(lines[0]) if not lines.is_empty() else "none"))
	var ns: Dictionary = _state.norm_smith_for(res)
	var has_medal := false
	for l in lines:
		if str(l).begins_with("Norm Smith Medal: "):
			has_medal = true
	_check(has_medal == (not ns.is_empty()),"The Norm Smith line is there when the medal is (%s)" % str(lines))
	for l in lines:
		_check(str(l) != "" and str(l) == str(l).strip_edges(), "No fact is blank (%s)" % str(l))
	var et: Dictionary = _pc.facts(_gf([13, 5], [12, 5], {"extra_time": true}))
	_check(str((et.get("callouts", [""]) as Array)[0]).contains("by 6 points after extra time"),
			"An extra-time win says so (%s)" % str(et.get("callouts", [])))
	var one: Dictionary = _pc.facts(_gf([10, 6], [10, 5]))
	_check(str((one.get("callouts", [""]) as Array)[0]).contains("by 1 point,"), "One point is singular (%s)" % str(one.get("callouts", [])))
	_check((_pc.facts(_gf([10, 5], [10, 5], {"replay_due": true})) as Dictionary).is_empty(),
			"A level Grand Final to be replayed gets no ceremony")
	_check((_pc.facts(_gf([10, 5], [10, 5])) as Dictionary).is_empty(),
			"A level Grand Final with no extra time and no ladder call gets none")
	# Level after extra time: the higher-ranked side, from the bracket, then the ladder.
	var season: Object = _state.season
	var keep: Dictionary = (season.get("finals") as Dictionary).duplicate(true)
	var lvl := _gf([12, 5], [12, 5], {"extra_time": true})
	season.set("finals", {"slots": {"W_GF": opp}, "top": []})
	var by_slot: Dictionary = _pc.facts(lvl)
	_check(str(by_slot.get("premier", "")) == opp and str((by_slot.get("callouts", [""]) as Array)[0]).begins_with("Level with "),
			"Level after extra time: the bracket's winner gets the flag, in words (%s)" % str(by_slot.get("callouts", [])))
	season.set("finals", {"slots": {}, "top": [opp, _state.my_club]})
	_check(str((_pc.facts(lvl) as Dictionary).get("premier", "")) == opp, "...or the higher on the ladder")
	season.set("finals", {"slots": {}, "top": [_state.my_club, opp]})
	_check(str((_pc.facts(_gf([12, 5], [12, 5], {"decided_on_ladder": true})) as Dictionary).get("premier", "")) == _state.my_club,
			"A Grand Final decided on the ladder goes to the higher side")
	season.set("finals", keep)


## The Grand Final's outcome line in sentence case (was "2026 PREMIERS").
func _test_casing() -> void:
	var res := _gf([13, 5], [8, 5])
	var want := "Premiers in %d" % _state.season_year
	var past: String = _state.call("_past_finals_outcome_line", res, "GF", true)
	_check(past == want, "Past formats: %s (%s)" % [want, past])
	var season: Object = _state.season
	var keep: Dictionary = (season.get("finals") as Dictionary).duplicate(true)
	season.set("finals", {"slots": {"W_GF": _state.my_club}, "top": []})
	var now: String = _state.finals_outcome_line(res)
	season.set("finals", keep)
	_check(now == want, "This format: %s (%s)" % [want, now])


## On a bare stage: the beats in order, the sounds, the time to the final
## frame, the flash, the scorebug's beat, and the final frame itself.
func _test_beats() -> void:
	_prime_week()
	var b: Dictionary = await _open_bare(_facts_for("COL"))
	var c: Control = b["c"]
	_check((c.get("_callouts") as Array).size() == 4, "Four facts to stage")
	var watch: Dictionary = await _run_to_rest(c, int(b["t0"]), 9.0, b["pulse"])
	var secs := float(watch["secs"])
	_check(absf(secs - 6.27) <= 0.15, "The final frame at 6.27 s (%.2f s)" % secs)
	var beats := ["pc_pulse", "pc_sweep", "pc_settle", "pc_tint", "pc_unfurl", "pc_flash", "pc_shake", "pc_streamers", "pc_settled"]
	var last := -1
	for tag in beats:
		var at: int = (_feel.moved as Array).find(tag)
		_check(at > last, "%s plays, after the beat before it (%s)" % [tag, str(_feel.moved)])
		last = maxi(last, at)
	_check(c.get("heard") == ["roar"], "The crowd roars once, no siren on the match (%s)" % str(c.get("heard")))
	_check(_feel.heard.has("land"), "The sting sounds (%s)" % str(_feel.heard))
	_check(absf(float(watch["flash"]) - 0.30) <= 0.03, "The flash peaks at 0.30 in the club's colour (%.2f)" % float(watch["flash"]))
	_check(float(watch["pulse"]) > 1.03 and float(watch["pulse"]) <= 1.061, "The scorebug beats once to 1.06 (%.3f)" % float(watch["pulse"]))
	await _wait(0.6)   # the last tweens finish
	var why := _at_rest_ok(c)
	_check(why == "", "The final frame is solid, full size and still (%s)" % why)
	for l in b["pulse"]:
		_check((l as Control).scale.is_equal_approx(Vector2.ONE), "The scorebug back to its size")
	_check(is_instance_valid(c) and c.is_inside_tree(), "It waits for Continue at the final frame")
	(b["host"] as Node).queue_free()
	await _settle()


## The final frame on a phone, for every club, at standard and largest text,
## with the longest facts: nothing over the band, everything above Continue
## and on screen, no line wider than the column.
func _test_layout_every_club() -> void:
	_prime_week()
	var clubs: Array = _db.active_clubs(_state.season_year)
	_check(clubs.size() == 18, "18 clubs to lay out (%d)" % clubs.size())
	# The space the match gives it under the scoreboard.
	var scene := _open_match(_gf([13, 5], [8, 5]))
	await _settle()
	var mc := _ceremony(scene)
	var area := mc.size if mc != null else Vector2(390, 734)
	_check(mc != null and area.y > 500.0, "The match's space under the scoreboard (%s)" % str(area))
	scene.queue_free()
	await _settle()
	_state.set_reduced_motion(true)
	var worst := 1e9
	var worst_at := ""
	for key in ["standard", "largest"]:
		_state.set_text_size(key)
		for code in clubs:
			var b: Dictionary = await _open_bare(_facts_for(str(code)), {}, area)
			var c: Control = b["c"]
			await process_frame
			var top := float(c.get("_band_top"))
			var bottom := float(c.get("_band_bottom"))
			var cont: Control = c.get("_continue")
			var labels: Array = [c.get("_eyebrow"), c.get("_premiers"), c.get("_club")] + (c.get("_callouts") as Array)
			var bad: Array = []
			for it in labels:
				var l := it as Label
				var r := Rect2(l.position, l.size)
				if r.end.y > top + 0.5 and r.position.y < bottom - 0.5:
					bad.append("%s over the band" % l.name)
				if r.end.y > cont.position.y + 0.5:
					bad.append("%s under Continue" % l.name)
				if r.position.x < -0.5 or r.end.x > c.size.x + 0.5 or r.position.y < -0.5:
					bad.append("%s off screen %s" % [l.name, str(r)])
				if l.autowrap_mode == TextServer.AUTOWRAP_OFF and l.get_minimum_size().x > c.size.x - 31.5:
					bad.append("%s wider than the column (%.0f)" % [l.name, l.get_minimum_size().x])
			for it in [c.get("_trophy"), c.get("_flag")]:
				var g := (it as Control).get_global_rect()
				var y0 := g.position.y - c.get_global_rect().position.y
				if y0 < top - 0.5 or y0 + g.size.y > bottom + 0.5:
					bad.append("%s outside the band" % (it as Node).name)
			var crest: Control = c.get("_crest")
			if crest.position.y < bottom - 0.5:
				bad.append("the crest over the band")
			var last := labels[labels.size() - 1] as Label
			var gap := cont.position.y - (last.position.y + last.size.y)
			if gap < worst:
				worst = gap
				worst_at = "%s %s" % [code, key]
			_check(bad.is_empty(), "%s at %s text: the final frame fits (%s)" % [code, key, ", ".join(bad)])
			(b["host"] as Node).queue_free()
			await process_frame
	print("  premiership layout: tightest gap above Continue %.0f px (%s)" % [worst, worst_at])
	_state.set_text_size("standard")
	_state.set_reduced_motion(false)
	await _settle()


## A tap anywhere but Continue, mid-run: every piece to its final place, the
## scorebug back, the streamers gone, and the ceremony waits.
func _test_tap_elsewhere() -> void:
	var b: Dictionary = await _open_bare(_facts_for("RIC"))
	var c: Control = b["c"]
	await _wait(1.6)
	_check(bool(c.get("_sweeping")), "At 1.6 s the light is sweeping")
	var why: String = await Tap.tap_at(c, Vector2(c.size.x / 2.0, 60.0), true)
	await _settle()
	_check(why == "" and _feel.moved.has("pc_rest"), "A real tap on the stage reaches it (%s)" % why)
	_check(_at_rest_ok(c) == "", "...and jumps to the final frame (%s)" % _at_rest_ok(c))
	_check(not bool(c.get("_sweeping")) and float(c.get("_settle_k")) == 1.0, "...the light gone, the stripes in the band")
	_check(is_instance_valid(c) and c.is_inside_tree() and not _feel.moved.has("pc_leave"), "...and it waits for Continue")
	(b["host"] as Node).queue_free()
	await _settle()
	b = await _open_bare(_facts_for("RIC"))
	c = b["c"]
	await _wait(4.1)
	_check(is_instance_valid(c.get("_streamers")), "At 4.1 s the streamers are falling")
	why = await Tap.tap_at(c, Vector2(c.size.x / 2.0, 60.0), true)
	await _settle()
	_check(why == "" and c.get("_streamers") == null and c.find_child("PremiershipStreamers", true, false) == null,
			"A tap stops the streamers (%s)" % why)
	(b["host"] as Node).queue_free()
	await _settle()


## A real finger on Continue at the first frame, mid-impact (the stamp's flash
## at 3.8 s) and at the final frame: the ceremony goes and full time opens,
## still.
func _test_continue_taps() -> void:
	for when in [0.0, 3.85, -1.0]:
		var scene := _open_match(_gf([13, 5], [8, 5]))
		var c := _ceremony(scene)
		_check(c != null, "A Grand Final opens the ceremony (at %.2f)" % when)
		if c == null:
			scene.queue_free()
			await _settle()
			continue
		var ft: Control = scene.find_child("FullTime", true, false)
		_check(ft != null and not ft.visible, "Full time waits under it, hidden")
		if when > 0.0:
			await _wait(when)
		elif when < 0.0:
			await _wait(6.6)
		var mid: bool = when > 0.0 and not bool(c.get("at_rest")) and float(c.get("_flash_a")) > 0.0
		if when > 0.0:
			_check(mid, "At 3.85 s the stamp's flash is on (%.2f)" % float(c.get("_flash_a")))
		elif when < 0.0:
			_check(bool(c.get("at_rest")), "At 6.6 s it is at the final frame")
		var why: String = await Tap.tap(c.find_child("CeremonyContinue", true, false))
		await _settle()
		# Sounds from here on are full time's (the ceremony's own tags are pc_).
		var h0: int = (_feel.heard as Array).size()
		var gone := _ceremony(scene) == null
		_check(why == "" and gone, "A real tap on Continue at %s leaves the ceremony (%s)" % [
				"frame 1" if when == 0.0 else ("mid-impact" if mid else "the final frame"), why])
		_check(ft != null and ft.is_visible_in_tree(), "...and full time shows")
		await _wait(1.2)
		var loud: Array = []
		for tag in ["ft_slam", "ft_slam_heavy", "ft_flash", "ft_shake", "ft_snap", "ft_sink", "ft_settle"]:
			if _feel.moved.has(tag):
				loud.append(tag)
		var after: Array = (_feel.heard as Array).slice(h0)
		_check(_feel.moved.has("ft_still") and loud.is_empty() and not after.has("land"),
				"...still: no slam, flash, shake or sting (%s, heard after %s)" % [str(_feel.moved), str(after)])
		var v: Control = scene.find_child("Verdict", true, false)
		_check(v != null and is_equal_approx(_alpha_chain(v), 1.0) and is_equal_approx(v.scale.x, 1.0), "...the verdict there at once")
		scene.queue_free()
		await _settle()


## Android Back leaves the ceremony, as Continue does, and stays on the match.
func _test_back() -> void:
	var scene := _open_match(_gf([13, 5], [8, 5]))
	await _wait(0.15)
	var took: bool = scene.call("handle_back")
	await _settle()
	_check(took and _ceremony(scene) == null and _feel.moved.has("pc_leave"), "Back on the match leaves the ceremony")
	var ft: Control = scene.find_child("FullTime", true, false)
	_check(ft != null and ft.is_visible_in_tree() and scene.is_inside_tree(), "...onto full time, on the match")
	var beat: Array = []
	for v in ["_score_home", "_score_away"]:
		var l := scene.get(v) as Control
		beat.append(l.scale.x if l != null else -1.0)
	_check(beat == [1.0, 1.0], "...with the scorebug back to its size, left mid-beat (%s)" % str(beat))
	scene.queue_free()
	await _settle()


## Reduced motion: the final frame at once, the sting alone, nothing moves.
func _test_reduced() -> void:
	_state.set_reduced_motion(true)
	var b: Dictionary = await _open_bare(_facts_for("CAR"))
	var c: Control = b["c"]
	_check(_at_rest_ok(c) == "", "Reduced motion: the final frame on the first frame (%s)" % _at_rest_ok(c))
	await _wait(0.5)
	_check(_feel.moved.is_empty(), "...nothing moves (%s)" % str(_feel.moved))
	_check(_feel.heard.has("land") and (c.get("heard") as Array).is_empty(), "...the sting alone (%s, %s)" % [str(_feel.heard), str(c.get("heard"))])
	_check(c.get("_streamers") == null, "...no streamers")
	(b["host"] as Node).queue_free()
	await _settle()
	_state.set_reduced_motion(false)


## Screen shake off: the stamp at 3.8 s flashes but does not shake.
func _test_shake_off() -> void:
	_state.set_screen_shake_on(false)
	var b: Dictionary = await _open_bare(_facts_for("HAW"))
	await _wait(4.0)
	_check(_feel.moved.has("pc_flash") and not _feel.moved.has("pc_shake"), "Shake off: a flash, no shake (%s)" % str(_feel.moved))
	(b["host"] as Node).queue_free()
	await _settle()
	_state.set_screen_shake_on(true)


## The cup first, then the legend's farewell, then full time, still.
func _test_cup_before_farewell() -> void:
	var res := _gf([13, 5], [8, 5])
	var sq: Object = _state.my_squad()
	var mine: Array = (sq.get("ground") as Array) + (sq.get("bench") as Array)
	var man: Dictionary = mine[0]
	var fw := {"ms": {"player": "Smith", "games": 200, "id": str(man["id"])}, "man": man,
			"opp": _opp(res), "mine": mine, "theirs": []}
	var scene := _open_match(res, fw)
	await _settle()
	var c := _ceremony(scene)
	_check(c != null and root.find_child("FarewellVignette", true, false) == null, "The cup comes first; the farewell waits")
	if c == null:
		scene.queue_free()
		await _settle()
		return
	var why: String = await Tap.tap(c.find_child("CeremonyContinue", true, false))
	await _settle()
	var fv := root.find_child("FarewellVignette", true, false)
	_check(why == "" and fv != null and not _feel.moved.has("ft_still"), "Continue: the legend's farewell, full time still waiting (%s)" % why)
	if fv != null:
		fv.call("finish_now")
	await _settle(10)
	var order: Array = _feel.moved
	_check(order.has("pc_leave") and order.has("ft_still") and order.find("pc_leave") < order.find("ft_still"),
			"...then full time, still (%s)" % str(order))
	scene.queue_free()
	await _settle()
	var left := root.find_child("Farewell", true, false)
	if left != null:
		left.queue_free()
	await _settle()


## Another club's flag: the full ceremony, in the winner's colours.
func _test_other_club_flag() -> void:
	var res := _gf([8, 5], [13, 5])
	var opp := _opp(res)
	var scene := _open_match(res)
	await _wait(2.4)
	var c := _ceremony(scene)
	_check(c != null and str(c.get("_premier")) == opp, "Another club's flag gets the ceremony too (%s)" % (str(c.get("_premier")) if c != null else "none"))
	if c != null:
		var mat: ShaderMaterial = c.get("_mat")
		var cols: Array = _db.club_colours(opp)
		_check(mat.get_shader_parameter("col_a") == cols[0] and mat.get_shader_parameter("col_b") == cols[1],
				"...in %s's colours" % opp)
		var club: Label = c.find_child("CeremonyClub", true, false)
		_check(club != null and club.text == _db.club_name(opp), "...with their name (%s)" % (club.text if club != null else "missing"))
		_check(_feel.moved.has("pc_sweep") and _feel.moved.has("pc_settle"), "...played in full (%s)" % str(_feel.moved))
	scene.queue_free()
	await _settle()


## Sim the week on a Grand Final: the ceremony first, with its own siren,
## then the week's results.
func _test_hub_sim_path() -> void:
	_gf([14, 8], [9, 6])
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	_feel.clear()
	hub.call("_after_sim")
	await _settle()
	var c := _ceremony(hub)
	_check(c != null and (c.get("heard") as Array).has("siren") and hub.find_child("RoundResults", true, false) == null,
			"The hub's Grand Final: the ceremony first, with the siren (%s)" % (str(c.get("heard")) if c != null else "none"))
	if c != null:
		var why: String = await Tap.tap(c.find_child("CeremonyContinue", true, false))
		await _settle()
		_check(why == "" and _ceremony(hub) == null and hub.find_child("RoundResults", true, false) != null,
				"...then Continue opens the week's results (%s)" % why)
	# Back leaves it the same way.
	var rr := hub.find_child("RoundResults", true, false)
	if rr != null:
		rr.queue_free()
		await _settle()
	hub.call("_after_sim")
	await _settle()
	var took: bool = hub.call("handle_back")
	await _settle()
	_check(took and _ceremony(hub) == null and hub.find_child("RoundResults", true, false) != null, "Back on the hub's ceremony opens the results")
	hub.queue_free()
	await _settle()


## A Grand Final draw to be replayed: no ceremony, full time as ever.
func _test_gf_draw_none() -> void:
	var scene := _open_match(_gf([10, 5], [10, 5], {"replay_due": true}))
	await _wait(1.2)
	var ft: Control = scene.find_child("FullTime", true, false)
	var played := false
	for tag in _feel.moved:
		if str(tag).begins_with("ft_") and str(tag) != "ft_still":
			played = true
	_check(_ceremony(scene) == null and ft != null and ft.is_visible_in_tree(), "A drawn Grand Final: no ceremony, full time")
	_check(played and not _feel.moved.has("ft_still"), "...with its own motion (%s)" % str(_feel.moved))
	scene.queue_free()
	await _settle()
