extends SceneTree
## godot --headless --path . --script tests/run_copy_rules_tests.gd
## The copy voice (director, 2026-11-10: option B, the senior coach's briefing; style guide §5.1).
## One banned list, scripts/core/CopyRules.gd, walked over every copy source: story cards and the
## string literals of the UI, sim and state scripts. A known hit sits in ALLOW with the copy pass
## that clears it (docs/TODO.md); the count must match exactly, so a new hit fails and a fixed one
## makes its allow-list entry shrink in the same PR. Each screen pass pins its rewritten lines.
## Seeded by design: it reads source files only, nothing random runs.

var _checks := 0
var _failures: Array[String] = []

## data/tales holds the phrase banks of the story layer (a career, the league news, a season's
## shape): every phrase there reaches the screen, so the banks are walked like the story cards.
const SOURCES := ["res://data/stories", "res://data/tales", "res://scripts/ui", "res://scripts/sim", "res://scripts/state"]
## The phrase banks that must be among the files read (a moved or renamed bank fails by name).
const TALES := ["res://data/tales/career.json", "res://data/tales/league.json", "res://data/tales/season.json"]

## Known hits, per file: [count, words, the pass that rewrites them]. Each reason names its copy
## voice row in docs/TODO.md (131-140, the screen passes).
const ALLOW := {
	"res://data/stories/leadership.json": [1, "should", "row 140: a player's own question, reported"],
	"res://data/stories/media.json": [2, "should", "row 140: a pundit's view, reported"],
	"res://scripts/sim/MatchSim.gd": [1, "should", "row 131: a shot's likelihood at the gate"],
	"res://scripts/sim/PlanTraits.gd": [1, "starters", "kept: the Fast Starters trait (a side that starts quickly, AFL usage), not the line-up sense"],
	"res://scripts/state/GameState.gd": [1, "projection", "row 138"],
	"res://scripts/ui/DraftScene.gd": [1, "projection", "row 136: draft"],
	"res://scripts/ui/OffseasonScene.gd": [1, "payroll", "row 137: contracts and trades"],
	"res://scripts/ui/PreSeasonScene.gd": [10, "starter", "row 136: pre-season"],
	"res://scripts/ui/StatGuide.gd": [1, "projection", "row 139: stats and menus"],
	"res://scripts/ui/TrainingScene.gd": [1, "should", "row 135: training"],
}

## The hub pass (copy voice pass 2): every rewritten line, and the line it replaced.
const HUB_NEW := [
	"Our week", "This is home base. Who we play next is up top.",
	"Pick the side in Team. Set how we play in Coaching.",
	"The week's open jobs sit here. Tap one to go to it; it ticks when done.",
	"The list is a guide, never a gate. Play match or Sim the week, jobs left or not.",
	"Our %d list is set.", "Start the season", "No game for us in Round %d.",
	"We have a week off while the rest of the series plays on.",
	"Our finals campaign is over. Play out the series to see who lifts the cup.",
	"\"Season over\"", "We missed the top %d. Play out the finals to see who lifts the cup.",
	"\"Our coach\"", "Our %s. They have offered him the %s job.", "He weighs it %d out of 100",
	"Play the semi-finals", "Play the preliminary finals", "Play the Grand Final",
	"Playing the semi-finals...", "Playing the preliminary finals...",
	"Our pick. Whoever we take signs a rookie deal to the end of next season.",
	"Sim the week without picking and we pass.", "Sim the week...",
]
const HUB_OLD := [
	"\"Your week\"", "Check the next opponent", "Each week a short list here", "whenever you are ready",
	"Your %d list is set.", "Begin season", "No game for you", "You have a week off",
	"Your finals campaign", "Season over for you", "You missed the top", "\"Your coach\"",
	"\"Your %s. They have", "%d of 100", "Play semi finals", "Play the prelims", "Play Grand Final",
	"Playing the semi finals", "Playing the prelims", "Your pick: whoever you take",
	"Simming the week...",
]

## The team builder and coaching pass (copy voice pass 5): per file, the rewritten lines and the
## lines they replaced. Auto-pick is the Match committee now, on every screen that names it.
const TEAM_PASS := {
	"res://scripts/ui/SelectionScene.gd": [[
		"\"Match committee\"", "Dual ruck on. The match committee names a second ruck on the bench.",
		"One ruck. The match committee fills the bench with the best of the rest.",
		"Our side is confirmed for this week.", "\"Our team\"",
		"Projected: %s as they would line up this week. They name their side on match day. They kick the other way.",
		"Picked at match committee until you move someone.",
		"Saved as your Best 23. Choose it any week from Match committee.",
		"Back to the side from before match committee.",
		"Leave the player out while he is fit and the promise breaks. It stings.",
	], ["\"Auto-pick\"", "Auto-pick names", "Auto-pick fills", "Side confirmed for", "\"Your team\"", "(projected:",
		"Picked for you", "from Auto-pick", "before the auto-pick", "Leave a fit player out"]],
	"res://scripts/ui/CoachingScene.gd": [[
		"Each plan buys an edge and gives something up. The note below says which.",
		"Each plan runs on one of our list's strengths. That is our side as picked, against every list in the league.",
		"\"Also on our list\"", "After three games, how we win and get beaten shows here.",
		"One strength and one cost, on top of our plan, every match. Or none.",
		"No part of our game is costing us regularly.", "No one part of our game stands above the league.",
		"%s of the %s salary cap",
	], ["gives something up;", "one of your list's", "Also on your list", "how your side wins", "on top of your plan",
		"of your game", "payroll %s"]],
	"res://scripts/ui/FirstVisitIntro.gd": [[
		"Our match-day 23 for this week. The match committee picks it until you move someone.",
		"Move players on and off the ground to set the side you want.",
		"Our game plan: how we play every week, set against what our list is good at.",
		"Each plan suits some lists more than others. We can change it before any match.",
	], ["Your match-day 23", "is picked for you", "the team you want", "Your game plan: how your side",
		"Pick the plan that suits"]],
	"res://scripts/sim/SkipOrders.gd": [[
		"The match committee picks the side in place of one you named.",
		"The match committee picks the side in place of one you named, and keeps picking it for the finals until you name another.",
	], ["Auto-pick"]],
	"res://scripts/state/GameState.gd": [[
		"Nobody needs a break. This is our best side.", "Not enough fresh players to rest anyone. This is our best side.",
		"No saved Best 23 yet. Set a side and save it.", "Our Best 23. Replacing unavailable players: %s.",
		"\"Our Best 23.\"", "No young player is close enough to take a senior spot. This is our best side.",
	], ["this is your best side", "arrange a side and save it", "\"Your Best 23", "a starter's spot"]],
}


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


func _run() -> void:
	await process_frame
	_t("_test_rules")
	_t("_test_sources")
	_t("_test_hub_pass")
	_t("_test_team_pass")
	print(Ran.line("Copy rules", self))
	quit(0 if _failures.is_empty() else 1)


## The list catches whole words in any case, leaves look-alikes alone, keeps OVR and POT, and
## lets the broadcaster's feed shout.
func _test_rules() -> void:
	_check(CopyRules.words_in("We should press higher") == ["should"], "'should' is advice")
	_check(CopyRules.words_in("Shoulder: two weeks").is_empty(), "'Shoulder' is not 'should'")
	_check(CopyRules.words_in("Our ROSTER, our Payroll") == ["roster", "payroll"], "any case, in order")
	_check(CopyRules.words_in("Auto-pick names him") == ["auto-pick"], "a feature name is caught")
	_check(CopyRules.words_in("The best  choice here") == ["best choice"], "a verdict across spaces")
	_check(CopyRules.words_in("Best 22 · Best and fairest").is_empty(), "'Best 22' is football, not a verdict")
	_check(CopyRules.check("Pick 4 · 72 OVR · 81 POT").is_empty(), "OVR and POT stay (director, 2026-11-10)")
	_check(CopyRules.check("His opinion of you: 61/100") == ["/100"], "a raw meter reads 'out of 100'")
	_check(CopyRules.check("He weighs it 61 out of 100").is_empty(), "'out of 100' passes")
	_check(CopyRules.check("player_id | 3") == ["|", "_"], "code marks never reach the screen")
	_check(CopyRules.check("What a goal!") == ["!"], "no shouting in the coach's voice")
	_check(CopyRules.check("What a goal!", true).is_empty(), "the broadcaster's feed may shout")


## Every copy source, against the list: only the known hits in ALLOW, each at its exact count.
func _test_sources() -> void:
	var lit := RegEx.create_from_string("\"([^\"\\n]*)\"")
	var found := {}
	var lines := {}
	var read := {}
	for dir in SOURCES:
		for path in _files(dir):
			var text := FileAccess.get_file_as_string(path)
			var strings: Array = []
			if path.ends_with(".json"):
				_json_strings(JSON.parse_string(text), strings)
			else:
				for line in text.split("\n"):
					if line.strip_edges().begins_with("#"):
						continue
					for m in lit.search_all(line):
						if m.get_string(1).contains(" "):
							strings.append(m.get_string(1))
			read[path] = strings.size()
			for s in strings:
				var hits := CopyRules.words_in(str(s))
				if hits.is_empty():
					continue
				found[path] = int(found.get(path, 0)) + hits.size()
				if not lines.has(path):
					lines[path] = []
				lines[path].append("%s: \"%s\"" % [", ".join(PackedStringArray(hits)), str(s).left(90)])
	for path in found:
		var allowed := int((ALLOW.get(path, [0]) as Array)[0])
		_check(int(found[path]) == allowed, "%s has %d banned words (allowed %d): %s" % [
				path, int(found[path]), allowed, " | ".join(PackedStringArray(lines[path]))])
	for path in ALLOW:
		_check(found.has(path), "%s is clean now: drop it from ALLOW" % path)
	for path in TALES:
		_check(int(read.get(path, 0)) > 0, "%s is read, phrase by phrase (%d strings)" % [path, int(read.get(path, 0))])
	# The list bites on a bank: a banned word in a phrase shaped like the season bank's is caught.
	var bank: Array = []
	_json_strings({"angles": {"surge": {"slots": ["run"], "coach": ["We should have won our last {run} games."]}}}, bank)
	var caught: Array = []
	for s in bank:
		caught.append_array(CopyRules.words_in(str(s)))
	_check(caught == ["should"], "A banned word in a bank's phrase is caught (%s)" % str(caught))


## The hub pass: each rewritten line is in the hub's source, and none of the old ones is.
func _test_hub_pass() -> void:
	var src := FileAccess.get_file_as_string("res://scripts/ui/HubScene.gd")
	for s in HUB_NEW:
		_check(src.contains(str(s)), "the hub says: %s" % s)
	for s in HUB_OLD:
		_check(not src.contains(str(s)), "the hub no longer says: %s" % s)


## The team builder and coaching pass: each rewritten line is in its source, and none of the old ones.
func _test_team_pass() -> void:
	for path in TEAM_PASS:
		var src := FileAccess.get_file_as_string(path)
		var name := str(path).get_file()
		for s in TEAM_PASS[path][0]:
			_check(src.contains(str(s)), "%s says: %s" % [name, s])
		for s in TEAM_PASS[path][1]:
			_check(not src.contains(str(s)), "%s no longer says: %s" % [name, s])


func _files(dir: String) -> Array:
	var out: Array = []
	var d := DirAccess.open(dir)
	if d == null:
		return out
	for f in d.get_files():
		if f.ends_with(".gd") or f.ends_with(".json"):
			out.append(dir.path_join(f))
	for sub in d.get_directories():
		out.append_array(_files(dir.path_join(sub)))
	out.sort()
	return out


func _json_strings(v: Variant, out: Array) -> void:
	if v is String:
		out.append(v)
	elif v is Dictionary:
		for k in v:
			_json_strings(v[k], out)
	elif v is Array:
		for e in v:
			_json_strings(e, out)
