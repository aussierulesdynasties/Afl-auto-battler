extends RefCounted
## The rival coach read (director, 2026-11-08; scripts/sim/RivalRead.gd): the
## Assistant's report and the break sheet on the opposition coach. The calls
## are unchanged (the recorded fixture), and every line says what his calls
## really do: the same seeded matches, read at each break and checked against
## the call he then makes. Run through tests/run_rival_read_tests.gd.

var failures: Array[String] = []
var checks := 0
## The runner's tree, for the real tap.
var tree: SceneTree

const SUITE_SEED := 2027
const Identity := preload("res://tests/rival_identity.gd")
const Tap := preload("res://tests/tap.gd")
## Words that would tell the coach what to do, or say their next plan for sure.
const ADVICE := ["you should", "to beat them", "recommend", "your best bet", "should play", "they will play",
		"they'll play", "they'll switch", "will switch"]
## Every line the suite reads, for the no-numbers and no-advice check.
var _said: Array = []


func run() -> void:
	failures.clear()
	checks = 0
	_said.clear()
	GameState.replay_seed = SUITE_SEED
	_t("_test_calls_unchanged")
	_t("_test_reads_match_calls")
	_t("_test_coach_words")
	_t("_test_break_words")
	_t("_test_record_words")
	await _t("_test_in_career")
	_t("_test_plain_words")
	GameState.delete_saved_career()
	CoachEffects.table = {}
	GameState.replay_seed = 0
	print(Ran.line("Rival coach read", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _say(line: String) -> String:
	_said.append(line)
	return line


func _plan(rec: Dictionary, side: int) -> String:
	return MatchSim.plan_key(str(((rec["plans"] as Array)[side] as Dictionary).get("gameplan", "balanced")))


# ---------------------------------------------------------------------------
## The rival coach's calls and the scores are what they were before the read
## (tests/fixtures/rival_identity.json, written from main by
## tools/rival_identity_dump.gd).
func _test_calls_unchanged() -> void:
	var f := FileAccess.open(Identity.FIXTURE, FileAccess.READ)
	_check(f != null, "The calls recorded before the rival coach read are there")
	if f == null:
		return
	var want = JSON.parse_string(f.get_as_text())
	_check(want is Array and (want as Array).size() == Identity.MATCHES,
			"The record holds %d matches" % Identity.MATCHES)
	if not (want is Array) or (want as Array).size() != Identity.MATCHES:
		return
	var same := 0
	var first := ""
	for i in range(Identity.MATCHES):
		var got := JSON.stringify(JSON.parse_string(JSON.stringify(Identity.play(i))))
		if got == JSON.stringify(want[i]):
			same += 1
		elif first == "":
			first = "%s: was %s, now %s" % [str((want[i] as Dictionary).get("match", i)),
					JSON.stringify(want[i]).left(300), got.left(300)]
	_check(same == Identity.MATCHES, "Every seeded match plays as before, every call the same (%d of %d; %s)" % [
			same, Identity.MATCHES, first])


## Each break read says what the rule then plays: his mood exactly when the
## scoreboard drives his next call, his answer to yours exactly when he
## countered; the tagger and loose man named are the men the match uses.
func _test_reads_match_calls() -> void:
	var seen := {"protect": 0, "chase": 0, "lost_q": 0, "counter": 0, "usual": 0, "tag_on_time": 0,
			"fire": 0, "pulled": 0}
	var bad := []
	for i in range(Identity.MATCHES):
		var sim := Identity.stage(i)
		var picks := ["", ""]
		for side in range(2):
			var sq: Squad = sim.squads[side]
			var pick := MatchSim.loose_pick(sq.ground, (sim.squads[1 - side] as Squad).ground)
			picks[side] = str(pick.get("id", ""))
			if picks[side] != str(sim.interceptor[side]):
				bad.append("match %d side %d: the report's loose man %s, the match starts %s" % [
						i, side, picks[side], str(sim.interceptor[side])])
			var named = MatchSim.tagger_for(sq.ground)
			var plays = sim.tagger_of(side)
			if str(named["id"] if named != null else "") != str(plays["id"] if plays != null else ""):
				bad.append("match %d side %d: the report's tagger is not the match's" % [i, side])
		var first_tag := [0, 0]
		var lines := ["", ""]
		while sim.current_quarter <= 4:
			var q := sim.current_quarter
			var whys := [sim.ai_why(0), sim.ai_why(1)]
			var margin := [sim.score(0) - sim.score(1), sim.score(1) - sim.score(0)]
			var before: Dictionary = sim.tactics_history[-1] if not sim.tactics_history.is_empty() else {}
			sim.begin_quarter()
			var rec: Dictionary = sim.tactics_history[-1]
			for side in range(2):
				var sq: Squad = sim.squads[side]
				var st: Dictionary = MatchSim.COACH_STYLES[sq.coach_style]
				var t: Dictionary = (rec["plans"] as Array)[side]
				var plan := _plan(rec, side)
				var why := str((rec["why"] as Array)[side])
				seen[why] = int(seen.get(why, 0)) + 1
				if why != str(whys[side]):
					bad.append("match %d Q%d side %d: read %s, played for %s" % [i, q, side, whys[side], why])
				var want := plan
				match why:
					"protect":
						want = "controlled"
					"chase", "lost_q":
						want = "attacking"
					"counter":
						want = str(MatchSim.COUNTER.get(_plan(before, 1 - side), "")) if not before.is_empty() else ""
						if q < MatchSim.COUNTER_Q:
							bad.append("match %d Q%d: a counter before %s" % [i, q, RivalRead.BREAKS[MatchSim.COUNTER_Q]])
					"usual":
						want = MatchSim.plan_key(str(sim.standing[side]))
				if plan != want:
					bad.append("match %d Q%d side %d: %s means %s, he played %s" % [i, q, side, why, want, plan])
				# The break line (on this side, seen from the other) said his
				# mood exactly when the call was the scoreboard's.
				if q >= 2:
					var line := str(lines[1 - side])
					var tail := RivalRead.mood_tail(why)
					var any_mood := false
					for m in RivalRead.MOODS:
						if line.contains(str(RivalRead.MOODS[m])):
							any_mood = true
					if (tail != "" and not line.ends_with(" " + tail)) or (tail == "" and any_mood):
						bad.append("match %d before Q%d: \"%s\" but he played for %s" % [i, q, line, why])
				if str(t.get("tag_id", "")) != "" and first_tag[side] == 0:
					first_tag[side] = q
					if q < MatchSim.tag_quarter(sq.tactics_read):
						bad.append("match %d side %d: tagged in Q%d, the box line says from %s" % [
								i, side, q, RivalRead.box_line(sq.tactics_read, true)])
					elif q == MatchSim.tag_quarter(sq.tactics_read):
						seen["tag_on_time"] += 1
				if str(t.get("pep", "")) == "fire_up":
					seen["fire"] += 1
					if q < int(st["fire_q"]) or margin[side] >= 0:
						bad.append("match %d Q%d side %d: fired up %d points up" % [i, q, side, margin[side]])
				# "If they're well behind in the second half, they put him back
				# on a man": well behind is the chase margin (loose == chase).
				var well_behind: bool = margin[side] <= -MatchSim.react_margin(sq.tactics_read) * float(st["chase"])
				if picks[side] != "" and well_behind and q >= int(st["loose_q"]):
					seen["pulled"] += 1
					if str(t.get("interceptor_id", "")) != "":
						bad.append("match %d Q%d side %d: %d down late and still a loose man" % [
								i, q, side, -margin[side]])
				if q == 1 and str(sim.interceptor[side]) != picks[side]:
					bad.append("match %d side %d: the first quarter's loose man is not the report's" % [i, side])
			Identity.finish_quarter(sim)
			# The break: each side's line on the other, as the sheet shows it.
			for me in range(2):
				var opp := 1 - me
				var last: Dictionary = sim.tactics_history[-1]
				var line := RivalRead.break_line(sim, me)
				lines[me] = line
				_said.append(line)
				if not line.begins_with("They played %s" % RivalRead.phrase(_plan(last, opp))):
					bad.append("match %d Q%d: \"%s\" is not what they played" % [i, q, line])
				var countered := str((last["why"] as Array)[opp]) == "counter"
				if countered != line.contains(", their answer to your "):
					bad.append("match %d Q%d: \"%s\" (%s)" % [i, q, line, (last["why"] as Array)[opp]])
				if countered:
					var prev: Dictionary = sim.tactics_history[-2]
					var tail := "their answer to your %s %s." % [RivalRead.phrase(_plan(prev, me)),
							RivalRead.in_quarter(int(prev["quarter"]))]
					if not line.contains(tail) or _plan(last, opp) != str(MatchSim.COUNTER.get(_plan(prev, me), "")):
						bad.append("match %d Q%d: \"%s\" should end \"%s\"" % [i, q, line, tail])
	_check(bad.is_empty(), "Every read says what the coach then does (%d disagree: %s)" % [bad.size(), bad.slice(0, 4)])
	_check(int(seen["protect"]) > 0 and int(seen["chase"]) + int(seen["lost_q"]) > 0 and int(seen["counter"]) > 0
			and int(seen["usual"]) > 0, "The seeded matches show every reason he plays a plan: %s" % seen)
	_check(int(seen["tag_on_time"]) > 0 and int(seen["fire"]) > 0 and int(seen["pulled"]) > 0,
			"...and a tag on time, a fire-up and a loose man put back on a man: %s" % seen)


# ---------------------------------------------------------------------------
## His coach's habits: every tendency reads, and reads differently; the words
## stand on the constants the calls use.
func _test_coach_words() -> void:
	var lines := {}
	for style in MatchSim.COACH_STYLES:
		var st: Dictionary = MatchSim.COACH_STYLES[style]
		# loose_line says "well behind" (the chase margin) with no base shift.
		_check(is_equal_approx(float(st["loose"]), float(st["chase"])) and is_zero_approx(float(st["add"])),
				"%s: the loose man is pulled at the chase margin, as the report says" % style)
		var l := _say(RivalRead.coach_line("Sam Coach", str(style)))
		_check(l.begins_with("Sam Coach ") and not lines.has(l), "%s reads in his own words: %s" % [style, l])
		lines[l] = true
		var when := str(RivalRead.PERIODS[int(st["fire_q"])])
		_check(RivalRead.fire_clause(str(style)).contains(when), "%s: the fire-up comes %s" % [style, when])
		_say(RivalRead.loose_line("Jack Spare", str(style)))
	_check(RivalRead.coach_line("", "balanced").begins_with("Their coach goes by the scoreboard"),
			"No senior coach: \"Their coach\"")
	_check(RivalRead.fire_clause("gambler").contains("sooner") and RivalRead.fire_clause("balanced").contains("well behind"),
			"A gambler fires them up sooner than most; the plain rule when well behind")
	_check(RivalRead.habit("stubborn").contains("bigger swing") and RivalRead.habit("reactive").contains("smaller swing")
			and RivalRead.habit("cautious").contains("shuts up shop sooner")
			and RivalRead.habit("gambler").contains("chases sooner"),
			"Each tendency moves the way its numbers do")
	# The box: sharp from the cut the coaching table uses.
	_check(is_equal_approx(MatchSim.TAG_SHARP_READ, CoachEffects.level(CoachEffects.STRONG_CUT)),
			"A sharp box is the strong coaching cut (%.2f)" % CoachEffects.level(CoachEffects.STRONG_CUT))
	for read in Identity.READS:
		var b := _say(RivalRead.box_line(float(read), true))
		var sharp := float(read) >= MatchSim.TAG_SHARP_READ
		_check(b.contains("quickly") == sharp and b.contains(str(RivalRead.BREAKS[MatchSim.tag_quarter(float(read))])),
				"Box %.2f: %s" % [read, b])
		_check(not RivalRead.box_line(float(read), false).contains("tagger"), "No tagger, no tag timing")
	_check(MatchSim.react_margin(1.0) < MatchSim.react_margin(0.0), "A sharper box moves on a smaller swing")
	var c := _say(RivalRead.counter_line())
	_check(c.begins_with("From %s, unless the scoreboard has pushed him" % RivalRead.BREAKS[MatchSim.COUNTER_Q]),
			"The counter waits for %s and gives way to the scoreboard: %s" % [RivalRead.BREAKS[MatchSim.COUNTER_Q], c])
	for k in MatchSim.COUNTER:
		_check(c.contains(CoachReport.plan_label(str(k))), "The counter line names %s" % k)
		_check(not c.contains(CoachReport.plan_label(str(MatchSim.COUNTER[k])) + " beats"),
				"...but never which plan beats it")
	_say(RivalRead.tagger_line("Tom Tag"))
	_say(RivalRead.minder_line())


## The break sheet's words: the counter tail, the mood, the legs reason.
func _test_break_words() -> void:
	_check(_say(RivalRead.played_line("defensive")) == "They played %s." % CoachReport.plan_label("defensive"),
			"A plain quarter: what they played")
	_check(_say(RivalRead.played_line("balanced")) == "They played a balanced game.", "A balanced game")
	_check(_say(RivalRead.played_line("defensive", "attacking", 2)) == "They played %s, their answer to your %s in the second quarter." % [
			CoachReport.plan_label("defensive"), CoachReport.plan_label("attacking")], "The counter tail")
	for mood in RivalRead.MOODS:
		var m := _say(RivalRead.mood_tail(str(mood)))
		_check(m != "", "%s is said" % mood)
		for plan in MatchSim.PLANS:
			_check(not m.contains(CoachReport.plan_label(str(plan))), "%s never names a plan (%s)" % [mood, plan])
	_check(RivalRead.mood_tail("") == "" and RivalRead.mood_tail("counter") == "" and RivalRead.mood_tail("usual") == "",
			"No mood read when the scoreboard is not driving him")
	_check(RivalRead.legs_reason(["balanced", "defensive", "defensive"]) == "they've pressed since quarter time",
			"Pressing since quarter time")
	_check(RivalRead.legs_reason(["attacking"]) == "they've run it through the corridor all game", "The corridor all game")
	_check(RivalRead.legs_reason(["defensive", "attacking"]) == "they've run hard all game", "Both plans that cost legs")
	_check(RivalRead.legs_reason(["defensive", "controlled"]) == "" and RivalRead.legs_reason([]) == "",
			"No reason once their last quarter saved legs")
	var tired := _say(MatchNotes.legs_line(80.0, 50.0, "they've pressed since half time"))
	_check(tired.ends_with("theirs is running on empty: they've pressed since half time."), "The reason follows theirs: %s" % tired)
	_check(not MatchNotes.legs_line(50.0, 80.0, "they've pressed since half time").contains("pressed"),
			"No reason when yours are the more tired")
	for plan in MatchSim.PLANS:
		var legs := RivalRead.legs_clause(str(plan))
		var pace := float((MatchSim.PLANS[plan] as Dictionary).get("pace", 1.0))
		_check((legs == "It costs them legs.") == (pace > 1.0) and (legs == "It saves their legs.") == (pace < 1.0),
				"%s: %s" % [plan, legs])


## Their list and their record: fit, plan knowledge, the season and the
## match against you, the full-time glance.
func _test_record_words() -> void:
	_check(_say(RivalRead.know_line({})) == "They know every plan well.", "Every plan known well")
	var k := _say(RivalRead.know_line({"attacking": 1, "contest": 0, "controlled": 0, "defensive": 2}))
	_check(k == "They know %s only partly and %s and %s barely. The rest they know well." % [
			CoachReport.plan_label("attacking"), CoachReport.plan_label("contest"), CoachReport.plan_label("controlled")], k)
	var story := _say(RivalRead.plan_story("Melbourne", ["defensive", "defensive", "attacking", "attacking"]))
	_check(story == "Melbourne started with %s and switched to %s in the third quarter." % [
			CoachReport.plan_label("defensive"), CoachReport.plan_label("attacking")], story)
	_check(RivalRead.plan_story("they", ["balanced", "balanced"]) == "", "A plain game is not a story")
	_check(_say(RivalRead.plan_story("they", ["controlled", "controlled"], "half")) == "they played %s all half." % CoachReport.plan_label("controlled"),
			"One plan all half")
	_check(_say(RivalRead.plan_story("they", ["balanced", "attacking", "defensive", "controlled"])).contains(", then "),
			"Three switches read in order")
	_check(RivalRead.where("Round 6 · Gather Round") == "in Round 6" and RivalRead.where("Qualifying Final 2") == "in the Qualifying Final"
			and RivalRead.where("Grand Final") == "in the Grand Final", "Where they met")
	var rows := [
		{"l": "Round 1", "v": "COL", "p": ["defensive", "defensive", "attacking", "attacking"], "w": ["usual", "usual", "chase", "chase"]},
		{"l": "Round 2", "v": "GEE", "p": ["defensive", "controlled", "controlled", "controlled"], "w": ["usual", "protect", "protect", "protect"]},
	]
	_check(RivalRead.season_line(rows.slice(0, 1)) == "", "One match is not a season's habit")
	var s := _say(RivalRead.season_line(rows))
	_check(s == "This season: mostly %s, %s when chasing and %s when in front." % [
			CoachReport.plan_label("defensive"), CoachReport.plan_label("attacking"), CoachReport.plan_label("controlled")], s)
	var v := _say(RivalRead.vs_line(rows, "GEE"))
	_check(v == "Against you in Round 2, they started with %s and switched to %s in the second quarter." % [
			CoachReport.plan_label("defensive"), CoachReport.plan_label("controlled")], v)
	_check(RivalRead.vs_line(rows, "SYD") == "", "No line before you have met")
	# record_row: a rival coach's side only.
	var res := {"label": "Round 3", "home": "GEE", "away": "SYD", "tactics_history": [
		{"quarter": 1, "plans": [{"gameplan": "defensive"}, {"gameplan": "attacking"}], "why": ["", "usual"]},
		{"quarter": 2, "plans": [{"gameplan": "defensive"}, {"gameplan": "controlled"}], "why": ["", "counter"]},
	]}
	_check(RivalRead.record_row(res, 0).is_empty(), "Your own calls are not a rival coach's record")
	_check(RivalRead.record_row(res, 1) == {"l": "Round 3", "v": "GEE", "p": ["attacking", "controlled"], "w": ["usual", "counter"]},
			"His calls are: %s" % RivalRead.record_row(res, 1))
	res["tactics_history"] = [{"quarter": 1, "plans": [{"gameplan": "defensive"}, {"gameplan": "attacking"}]}]
	_check(RivalRead.record_row(res, 1).is_empty(), "A match from before the read keeps no record")
	# The full-time glance tells a third-quarter switch (it once stopped at Q2).
	var g := CoachReport.glance({"quarters": 4, "my_code": "GEE", "opp_code": "MEL", "opp_plans": [
		{"gameplan": "defensive"}, {"gameplan": "defensive"}, {"gameplan": "attacking"}, {"gameplan": "attacking"}]}, true)
	var read := " ".join(g.get("read", []))
	_check(read.contains("started with %s and switched to %s in the third quarter." % [
			CoachReport.plan_label("defensive"), CoachReport.plan_label("attacking")]), "The glance tells the switch: %s" % read)


# ---------------------------------------------------------------------------
## In a career: each rival coach's record fills, saves, survives an old save
## and a new year; the report a real tap opens names the tagger and loose man
## the match then plays.
func _test_in_career() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	GameState.advance()
	GameState.advance()
	var clubs: Dictionary = GameState.rival_plans.get("clubs", {})
	_check(int(GameState.rival_plans.get("year", 0)) == GameState.season_year and clubs.size() >= 10,
			"Two rounds in, the rival coaches' records fill (%d clubs)" % clubs.size())
	_check(not clubs.has("GEE"), "Your own club keeps none")
	var rows_ok := true
	for code in clubs:
		for r in clubs[code]:
			if (r["p"] as Array).size() < 4 or (r["w"] as Array).size() != (r["p"] as Array).size():
				rows_ok = false
	_check(rows_ok, "Each match keeps a plan and a reason for every quarter")
	var r1 := ""
	for res in GameState.season_log:
		if str(res.get("label", "")) == "Round 1" and (str(res["home"]) == "GEE" or str(res["away"]) == "GEE"):
			r1 = str(res["away"]) if str(res["home"]) == "GEE" else str(res["home"])
	_check(r1 != "", "Geelong played in Round 1")
	if r1 == "":
		return
	var report := GameState.opponent_report(r1)
	var flat := []
	for part in report:
		for t in part[1]:
			flat.append(_say(str(t)))
	var text := "\n".join(flat)
	_check(text.contains("Against you in Round 1, "), "Their report tells the match against you: %s" % text)
	_check(text.contains("This season: mostly "), "...and their season")
	_check(report.size() == 3 and str(report[2][0]) == "Their coach" and (report[2][1] as Array).size() == 3,
			"Their coach: his habits, his box, his counter")
	# The record is saved, and a save from before it opens with none.
	var before := JSON.stringify(GameState.rival_plans)
	_check(GameState.save_career(), "The career saves")
	GameState.reset()
	_check(GameState.load_career() and JSON.stringify(GameState.rival_plans) == before, "The record comes back as saved")
	var state := CareerSave.read(GameState.save_path)
	state.erase("rival_plans")
	CareerSave.write(state, CareerSave.read_meta(GameState.save_path), GameState.save_path)
	GameState.reset()
	_check(GameState.load_career() and GameState.rival_plans.is_empty(), "A save from before the record opens with none")
	var old_text := str(GameState.opponent_report(r1))
	_check(not old_text.contains("This season:") and not old_text.contains("Against you"),
			"...and its report says nothing of a season it did not keep")
	# Last year's record is never read as this year's.
	GameState.rival_plans = {"year": GameState.season_year - 1, "clubs": clubs}
	_check(GameState.rival_rows(r1).is_empty(), "Last season's record is not this season's")
	GameState.advance()
	_check(int(GameState.rival_plans.get("year", 0)) == GameState.season_year
			and (GameState.rival_rows(r1) as Array).size() <= 1, "A new season's record starts afresh")
	# A real tap opens the report: their coach is in it.
	CoachEffects.table = {}
	GameState._refresh_coach_tactics()
	var opp := str(GameState.my_next_opponent().get("code", ""))
	_check(opp != "", "There is a next opponent")
	tree.root.size = Vector2i(1280, 720)
	var ui: Control = load("res://scenes/SelectionScene.tscn").instantiate()
	tree.root.add_child(ui)
	await _settle()
	var btn: Button = ui.find_child("AssistantReport", true, false)
	var why := "no report button" if btn == null else str(await Tap.tap(btn))
	_check(why == "", "A tap opens the Assistant's report (%s)" % why)
	await _settle()
	var sheet: Node = ui.find_child("AssistantReportSheet", true, false)
	var heads := []
	if sheet != null:
		for l in sheet.find_children("*", "Label", true, false):
			heads.append(str((l as Label).text))
	_check(heads.has("Their coach") and heads.has("Who matters"), "It reads their coach and who matters: %s" % [heads])
	ui.queue_free()
	await _settle()
	# The tagger and loose man it names are the men the match plays.
	var rep := GameState.opponent_report(opp)
	var people: Array = []
	for part in rep:
		if str(part[0]) == "Who matters":
			people = part[1]
	_check(GameState.prepare_interactive_match(), "The match is set up")
	var sim: MatchSim = GameState.pending_sim
	if sim == null:
		return
	var them := 1 - sim.moment_side
	var sq: Squad = sim.squads[them]
	var tagger = sim.tagger_of(them)
	if tagger != null and Roles.is_tagger(tagger):
		_check(people.has(RivalRead.tagger_line(GameDB.player_display_name(tagger))),
				"The report's tagger is theirs: %s" % [people])
	var loose := str(sim.interceptor[them])
	var named := false
	for p in sq.ground:
		if str(p["id"]) == loose and people.has(RivalRead.loose_line(GameDB.player_display_name(p), sq.coach_style)):
			named = true
	var danger := false
	for f in GameState.opponent_people(opp):
		if str(f["key"]) == "danger" and str(f.get("player_id", "")) == loose:
			danger = true
	_check(loose == "" or named or danger, "The report's loose man is the one they start with (%s): %s" % [loose, people])


## No line carries a number (a round's own name aside) or advice.
func _test_plain_words() -> void:
	var digits := RegEx.new()
	digits.compile("\\d")
	var round_no := RegEx.new()
	round_no.compile("Round \\d+")
	var bad := []
	for l in _said:
		var s := round_no.sub(str(l), "Round", true)
		if digits.search(s) != null:
			bad.append(l)
		for w in ADVICE:
			if s.to_lower().contains(w):
				bad.append(l)
	_check(_said.size() > 50 and bad.is_empty(), "%d lines, none with a number or advice: %s" % [_said.size(), bad.slice(0, 3)])


func _settle() -> void:
	for i in range(6):
		await tree.process_frame
