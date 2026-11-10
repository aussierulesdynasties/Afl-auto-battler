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
	"res://scripts/sim/SkipOrders.gd": [2, "auto-pick", "row 134: renamed with the Auto-pick button"],
	"res://scripts/state/GameState.gd": [2, "starter, projection", "rows 134 and 138"],
	"res://scripts/ui/CoachingScene.gd": [1, "payroll", "row 134: coaching"],
	"res://scripts/ui/DraftScene.gd": [1, "projection", "row 136: draft"],
	"res://scripts/ui/OffseasonScene.gd": [1, "payroll", "row 137: contracts and trades"],
	"res://scripts/ui/PreSeasonScene.gd": [10, "starter", "row 136: pre-season"],
	"res://scripts/ui/SelectionScene.gd": [4, "auto-pick", "row 134: renamed with the Auto-pick button"],
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
