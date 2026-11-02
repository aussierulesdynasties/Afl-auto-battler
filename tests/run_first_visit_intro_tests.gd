extends SceneTree
## godot --headless --path . --script tests/run_first_visit_intro_tests.gd
## First-visit intros on the main screens (plan step 3b, register row 27):
## each opens once, "Got it" closes it, tips off opens none, and a device
## that has only seen the old four intros still gets the new ones.
const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")

var _state: Node
var _FV
var _checks := 0
var _failures: Array[String] = []

const SUITE_SEED := 2027
const KEYS := ["draft", "selection", "coaching", "list", "staff", "offseason", "preseason", "season_review"]
const SCENES := {
	"selection": "res://scenes/SelectionScene.tscn",
	"coaching": "res://scenes/CoachingScene.tscn",
	"list": "res://scenes/ListScene.tscn",
	"staff": "res://scenes/StaffScene.tscn",
}


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_FV = load("res://scripts/ui/FirstVisitIntro.gd")
	_state.autosave_enabled = false
	_state.save_path = "user://test_first_visit.save"
	_state.settings_path = "user://test_first_visit_settings.cfg"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(_state.settings_path))
	_state.show_real_names = false
	_state.replay_seed = SUITE_SEED
	_state.reset()
	_state.start_season("COL", root.get_node("GameDB").club_list("COL"))
	root.size = Vector2i(390, 844)
	await _t("_test_every_key_once")
	await _t("_test_tips_off")
	await _t("_test_old_device")
	for key in SCENES:
		await _t("_test_scene", [key])
	print(Ran.line("FirstVisitIntro", self))
	quit(0 if _failures.is_empty() else 1)


func _reset_seen() -> void:
	for key in KEYS:
		_state.set_setting("seen_%s_intro" % key, false)


## Every new key: two or three short lines, shown once, then never again.
func _test_every_key_once() -> void:
	_reset_seen()
	_state.tutorials = true
	for key in KEYS:
		var lines: Array = _FV.TEXT[key][1]
		_check(lines.size() >= 2 and lines.size() <= 3, "%s intro is two or three lines" % key)
		for l in lines:
			_check(str(l).length() <= 120, "%s intro line is short: %s" % [key, l])
		var host := Control.new()
		root.add_child(host)
		var first: Control = _FV.show_if_due(host, key)
		_check(first != null and host.find_child("*IntroOk", true, false) != null, "%s intro opens on the first visit" % key)
		var ok: Button = host.find_child("*IntroOk", true, false)
		if ok != null:
			_check((await Tap.tap(ok)) == "", "%s Got it takes a tap" % key)
		await _settle()
		_check(host.find_child("*Intro", true, false) == null, "%s Got it closes it" % key)
		_check(_FV.show_if_due(host, key) == null, "%s intro does not open a second time" % key)
		host.queue_free()
	await _settle()


## Tips off for this career: no intro opens by itself.
func _test_tips_off() -> void:
	_reset_seen()
	_state.tutorials = false
	for key in KEYS:
		var host := Control.new()
		root.add_child(host)
		_check(_FV.show_if_due(host, key) == null, "Tips off: no %s intro" % key)
		host.queue_free()
	_check(not bool(_state.get_setting("seen_list_intro", false)), "Tips off leaves the intros unseen for later")
	_state.tutorials = true
	await _settle()


## A device that saw the four old intros (and an old career's state, which
## carries no new field) still gets every new one, and the old four stay seen.
func _test_old_device() -> void:
	_reset_seen()
	for old in ["weekly_loop", "momentum", "training", "season_stats"]:
		_state.set_setting("seen_%s_intro" % old, true)
	_state.tutorials = true
	for key in KEYS:
		_check(_state.intro_due(key), "Old device: %s intro is due" % key)
	for old in ["weekly_loop", "momentum", "training", "season_stats"]:
		_check(not _state.intro_due(old), "Old device: %s stays seen" % old)


## The real screen opens its intro on the first visit only.
func _test_scene(key: String) -> void:
	_reset_seen()
	_state.tutorials = true
	var s: Control = load(SCENES[key]).instantiate()
	root.add_child(s)
	await _settle()
	var ok: Button = s.find_child("*IntroOk", true, false)
	_check(ok != null, "%s screen shows its intro on the first visit" % key)
	if ok != null:
		_check(s.handle_back(), "%s screen: Back closes the intro first" % key)
		await _settle()
	_check(s.find_child("*IntroOk", true, false) == null, "%s screen: Back closes it, screen stays" % key)
	_check(s.is_inside_tree(), "%s screen: still open after Back" % key)
	s.queue_free()
	await _settle()
	var again: Control = load(SCENES[key]).instantiate()
	root.add_child(again)
	await _settle()
	_check(again.find_child("*IntroOk", true, false) == null, "%s screen: next visit has no intro" % key)
	again.queue_free()
	await _settle()


func _settle() -> void:
	for i in range(4):
		await process_frame


func _check(ok: bool, what: String) -> void:
	_checks += 1
	if not ok:
		_failures.append(what)
		push_error(what)


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)
