extends RefCounted
## The one attribute list (Director Bible 4.2.30a, docs/RATING_REBUILD.md §2):
## 18 attributes in four groups, every screen's list is Attributes', each
## attribute appears once in every list, and each reads one label everywhere.
## The OVR read from them is tests/test_ratings.gd's. Run through
## tests/run_attributes_tests.gd.

var failures: Array[String] = []
var checks := 0

const ATTRIBUTES := preload("res://scripts/sim/Attributes.gd")


func run() -> void:
	failures.clear()
	checks = 0
	_t("_test_one_list")
	_t("_test_card_rows")
	_t("_test_prose_labels")
	_t("_test_groups_and_callouts")
	_t("_test_play_style_keys")
	_t("_test_screens_use_the_list")
	_t("_test_label")
	print(Ran.line("Attributes", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


## A script's constant, read without naming its class (several reach autoloads).
func _const(path: String, name: String) -> Variant:
	var script: Script = load(path)
	if script == null:
		return null
	return script.get_script_constant_map().get(name)


## Each key of `keys` once, and nothing else.
func _covers_once(keys: Array, what: String) -> void:
	var all: Array = ATTRIBUTES.KEYS
	_check(keys.size() == all.size(),
			"%s has %d entries, the list has %d" % [what, keys.size(), all.size()])
	for k in all:
		_check(keys.count(k) == 1, "%s has %s %d times, not once" % [what, k, keys.count(k)])


func _test_one_list() -> void:
	var keys: Array = ATTRIBUTES.KEYS
	_check(keys.size() == 18, "the rebuild's 18 attributes; got %d" % keys.size())
	var grouped: Array = ATTRIBUTES.PHYSICAL + ATTRIBUTES.TECHNICAL + ATTRIBUTES.FOOTY_IQ + ATTRIBUTES.MENTAL
	_covers_once(grouped, "the four groups")
	for k in keys:
		_check(keys.count(k) == 1, "%s is in the list once" % k)


func _test_card_rows() -> void:
	var rows: Array = ATTRIBUTES.CARD_ROWS
	var keys := []
	for row in rows:
		_check((row as Array).size() == 2 and str(row[1]) != "",
				"a card row is [key, label]: %s" % str(row))
		keys.append(str(row[0]))
	_covers_once(keys, "CARD_ROWS")
	# Group by group, in storage order.
	_check(keys == ATTRIBUTES.KEYS, "the card lists them group by group, Speed to Durability")
	_check(ATTRIBUTES.label("contested_ball") == "Contested ball", "contested_ball reads Contested ball")
	_check(ATTRIBUTES.label("reading_play") == "Reading the play", "reading_play reads Reading the play")


func _test_prose_labels() -> void:
	var prose: Dictionary = ATTRIBUTES.PROSE_LABELS
	_covers_once(prose.keys(), "PROSE_LABELS")
	var differ := []
	for k in prose:
		if str(prose[k]) != ATTRIBUTES.label(str(k)):
			differ.append(str(k))
	differ.sort()
	_check(differ == ["ruck"], "only ruck reads differently in a sentence; got %s" % str(differ))
	_check(prose["ruck"] == "Ruck work", "the sentence word is Ruck work")


func _test_groups_and_callouts() -> void:
	var keys := []
	var groups: Array = ATTRIBUTES.GROUPS
	_check(groups.size() == 4, "the stat guide has the four groups; got %d" % groups.size())
	for g in groups:
		keys.append_array(g[1])
	_covers_once(keys, "GROUPS")
	var callouts: Dictionary = ATTRIBUTES.CALLOUTS
	_check(callouts.keys() == ["DEF", "MID", "FWD", "RUCK"], "a callout for each line")
	for line in callouts:
		_check((callouts[line] as Array).size() == 3, "%s calls out three" % line)
		for pair in callouts[line]:
			_check(ATTRIBUTES.KEYS.has(str(pair[0])), "%s callout %s is an attribute" % [line, pair[0]])


func _test_play_style_keys() -> void:
	var style: Array = ATTRIBUTES.PLAY_STYLE_KEYS
	var expected := []
	for k in ATTRIBUTES.KEYS:
		if k != "discipline" and k != "durability":
			expected.append(k)
	var a := style.duplicate()
	a.sort()
	expected.sort()
	_check(a == expected, "plays like compares every key but discipline and durability")
	for k in style:
		_check(style.count(k) == 1, "%s is compared once" % k)


## Each screen's list is the one list, not a copy of it.
func _test_screens_use_the_list() -> void:
	var cases := [
		["res://scripts/ui/PlayerSheet.gd", "ATTR_ROWS", ATTRIBUTES.CARD_ROWS],
		["res://scripts/state/GameState.gd", "TRAIN_STATS", ATTRIBUTES.CARD_ROWS],
		["res://scripts/sim/PlayerProfile.gd", "ATTR_LABELS", ATTRIBUTES.PROSE_LABELS],
		["res://scripts/ui/FormationView.gd", "CALLOUT_ATTRS", ATTRIBUTES.CALLOUTS],
		["res://scripts/ui/StatGuide.gd", "GROUPS", ATTRIBUTES.GROUPS],
		["res://scripts/sim/PlaysLike.gd", "KEYS", ATTRIBUTES.PLAY_STYLE_KEYS],
	]
	_check(cases.size() == 6, "six screens and models use the list")
	for c in cases:
		var got: Variant = _const(str(c[0]), str(c[1]))
		_check(got != null, "%s has %s" % [c[0], c[1]])
		_check(got == c[2], "%s.%s is the Attributes list" % [c[0].get_file(), c[1]])


func _test_label() -> void:
	var guide: Script = load("res://scripts/ui/StatGuide.gd")
	_check(guide != null, "the stat guide loads")
	for row in ATTRIBUTES.CARD_ROWS:
		var k := str(row[0])
		_check(ATTRIBUTES.label(k) == str(row[1]), "%s reads %s" % [k, row[1]])
		_check(str(guide.call("_label_for", k)) == str(row[1]),
				"the stat guide names %s as the card does" % k)
	_check(ATTRIBUTES.label("not_an_attribute") == "not_an_attribute",
			"an unknown key reads as itself")
