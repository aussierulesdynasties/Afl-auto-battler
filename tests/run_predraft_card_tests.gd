extends SceneTree
## godot --headless --path . --script tests/run_predraft_card_tests.gd
## The recruiting panel's "Before the draft" card (what the list does well,
## the prospects recruiting liked) meets the coach before his first National
## Draft pick the first time he opens the draft, after the press interview, in
## every start that opens on the National Draft; backing out to the menu and
## coming back (in memory or from the save on disk) never shows it twice.
## Director, 2026-11-12: "on a fresh save i loaded the draft, didnt select any
## players, backed out to main menu, reloaded the save and Then and only then did
## a 'before the draft' card pop up". Every step is a finger's tap (tests/tap.gd).
const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")

const SUITE_SEED := 4117
const CLUB := "MEL"
const SAVE := "user://test_predraft_card.save"
const SETTINGS := "user://test_predraft_card_settings.cfg"

var _state: Node
var _router: Node
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_router = root.get_node("Router")
	_state.save_path = SAVE
	_state.settings_path = SETTINGS
	root.size = Vector2i(390, 844)
	await _t("_test_real_lists_card_first_time")
	await _t("_test_rebuild_card_first_time")
	await _t("_test_club_tap_without_interview")
	await _t("_test_redraft_never_shows_it")
	_state.autosave_enabled = false
	_state.delete_saved_career()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SETTINGS))
	print(Ran.line("Predraft card", self))
	quit(0 if _failures.is_empty() else 1)


## A fresh device and a new career set on New career (by a tap), begun as its
## Start does (Main._start_new_career), autosave on as in the game.
func _new_career(start: String, challenge := "none") -> void:
	_state.autosave_enabled = false
	_state.delete_saved_career()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SETTINGS))
	_state.replay_seed = SUITE_SEED
	_state.reset()
	_state.autosave_enabled = true
	_router.stack = []
	_router.go("main")
	await _settle()
	_check((await Tap.tap(current_scene.find_child("NewCareer", true, false))) == "", "New career takes a tap (%s)" % start)
	await _settle()
	current_scene.set("_pick_start", start)
	current_scene.set("_pick_challenge", challenge)
	current_scene.call("_start_new_career")
	await _at("draft")


func _at(route: String) -> void:
	for i in range(900):
		if _router.current() == route and not bool(root.get_node("ScreenTransition").busy):
			break
		await process_frame
	await _settle()


func _off(route: String) -> void:
	for i in range(900):
		if _router.current() != route and not bool(root.get_node("ScreenTransition").busy):
			break
		await process_frame
	await _settle()


func _card() -> Node:
	var n := current_scene.find_child("DraftMeeting", true, false)
	return null if n == null or n.is_queued_for_deletion() else n


## The coach's picks so far in this draft.
func _my_picks() -> int:
	var n := 0
	var d = _state.draft
	if d != null:
		for pk in d.pick_history:
			n += 1 if str(pk["club"]) == _state.coach_club() else 0
	return n


## The club tile, by a tap; the press interview after it, every answer tapped.
func _take_club_and_sit_interview(label: String) -> void:
	var tile: Control = current_scene.find_child("Choose_" + CLUB, true, false)
	_check(tile != null, "%s: Choose your club offers %s" % [label, CLUB])
	_check(_card() == null, "%s: no card over Choose your club" % label)
	_check((await Tap.tap(tile)) == "", "%s: the club tile takes a tap" % label)
	await _off("draft")
	_check(_router.current() == "interview", "%s: the press interview comes first (at %s)" % [label, _router.current()])
	if _router.current() != "interview":
		return
	var nf := current_scene.find_child("CoachName", true, false) as LineEdit
	nf.text = "Pat Reid"
	nf.text_changed.emit(nf.text)
	var taps: String = await Tap.tap(current_scene.find_child("InterviewStart", true, false))
	await _settle()
	for a in [1, 0, 2, 1, 3, 0, 1]:
		taps += await Tap.tap(current_scene.find_child("InterviewAnswer%d" % a, true, false))
		await _settle()
	taps += await Tap.tap(current_scene.find_child("InterviewDone", true, false))
	await _at("draft")
	_check(taps == "" and not _state.interview_due, "%s: the interview is answered by taps (%s)" % [label, taps])


## On the board with the card up: it is the first thing, before any pick; its
## To the draft closes it, the draft's tip after it, then Back to the menu.
func _card_first_then_back(label: String) -> void:
	var card := _card()
	_check(_router.current() == "draft" and str(current_scene.get("_phase")) == "board" and card != null
			and _my_picks() == 0,
			"%s: 'Before the draft' meets the coach on the board, before his first pick (at %s, phase %s, card %s, picks %d)" % [
				label, _router.current(), current_scene.get("_phase"), card != null, _my_picks()])
	if card != null:
		_check(_text(card).contains("Before the draft"), "%s: the card is the recruiting panel's 'Before the draft'" % label)
		_check(int(_state.draft_meeting_year) == int(_state.season_year), "%s: the meeting is recorded for this draft" % label)
		_check((await Tap.tap(card.find_child("MeetingDone", true, false))) == "", "%s: To the draft takes a tap" % label)
		await _settle()
		_check(_card() == null, "%s: the card closes" % label)
	await _close_tips()
	_check((await Tap.tap(current_scene.find_child("BackToMenu", true, false))) == "", "%s: Back to the menu takes a tap" % label)
	await _at("main")


## Back on the draft, in memory (Continue) and from the save on disk (a fresh
## launch's Continue): no second card.
func _no_repeat(label: String) -> void:
	var live: Control = current_scene.find_child("ResumeCareer", true, false)
	_check(live != null, "%s: the menu offers the draft to resume" % label)
	if live != null:
		_check((await Tap.tap(live)) == "", "%s: Continue takes a tap" % label)
		await _at("draft")
		_check(_router.current() == "draft" and _card() == null and _my_picks() == 0,
				"%s: back on the draft in memory, the card does not come again (at %s, card %s)" % [label, _router.current(), _card() != null])
		await _close_tips()
		await Tap.tap(current_scene.find_child("BackToMenu", true, false))
		await _at("main")
	# A fresh launch: nothing in memory, the career on disk.
	_state.reset()
	_router.stack = []
	_router.go("main")
	await _settle()
	var cont: Control = current_scene.find_child("ContinueCareer", true, false)
	_check(cont != null, "%s: a fresh launch offers the saved career" % label)
	if cont == null:
		return
	_check((await Tap.tap(cont)) == "", "%s: Continue (from the save) takes a tap" % label)
	await _at("draft")
	_check(_router.current() == "draft" and _state.my_club == CLUB and _card() == null,
			"%s: the reloaded save opens the draft without a second card (at %s, club %s, card %s)" % [
				label, _router.current(), _state.my_club, _card() != null])


## Real 2026 lists: the club on the draft screen, the interview, then the card.
func _test_real_lists_card_first_time() -> void:
	await _new_career("real")
	await _take_club_and_sit_interview("Real 2026 lists")
	await _card_first_then_back("Real 2026 lists")
	await _no_repeat("Real 2026 lists")


## Rebuild (real lists, the bottom club): the same order.
func _test_rebuild_card_first_time() -> void:
	await _new_career("real", "rebuild")
	var club: String = str((_state.challenge as Dictionary).get("club", ""))
	_check(club != "", "Rebuild names its club")
	var tile: Control = current_scene.find_child("Choose_" + club, true, false)
	_check(tile != null and (await Tap.tap(tile)) == "", "Rebuild: the club tile takes a tap")
	await _off("draft")
	_check(_router.current() == "interview", "Rebuild: the interview comes first (at %s)" % _router.current())
	_state.finish_interview([1, 0, 2, 1, 3, 0, 1])   # the answers are tapped above
	_router.replace("draft")
	await _at("draft")
	_check(_card() != null and _my_picks() == 0, "Rebuild: the card meets the coach before his first pick")


## A club taken on the draft screen with the interview already behind the
## coach (a career saved before the interview moved ahead of the draft): the
## card comes straight after the tap, not only once the draft is opened again.
func _test_club_tap_without_interview() -> void:
	await _new_career("real")
	_state.interview_due = false
	var tile: Control = current_scene.find_child("Choose_" + CLUB, true, false)
	_check(tile != null and (await Tap.tap(tile)) == "", "No interview due: the club tile takes a tap")
	await _settle()
	_check(_router.current() == "draft" and str(current_scene.get("_phase")) == "board",
			"No interview due: the tap goes straight to the board (at %s)" % _router.current())
	await _card_first_then_back("No interview due")
	await _no_repeat("No interview due")


## The League redraft has no recruiting panel (it meets before a National
## Draft): not the first time, and not after a reload either.
func _test_redraft_never_shows_it() -> void:
	await _new_career("redraft")
	await _take_club_and_sit_interview("League redraft")
	_check(_router.current() == "draft" and _card() == null, "League redraft: no 'Before the draft' card")
	await _close_tips()
	await Tap.tap(current_scene.find_child("BackToMenu", true, false))
	await _at("main")
	_state.reset()
	_router.stack = []
	_router.go("main")
	await _settle()
	var cont: Control = current_scene.find_child("ContinueCareer", true, false)
	_check(cont != null and (await Tap.tap(cont)) == "", "League redraft: Continue from the save takes a tap")
	await _at("draft")
	_check(_router.current() == "draft" and _card() == null, "League redraft: still no card after a reload")


## Close the first-visit tips over the screen by their Got it.
func _close_tips() -> void:
	for i in range(3):
		var ok: Button = null
		for b in current_scene.find_children("*IntroOk", "Button", true, false):
			if not b.is_queued_for_deletion() and b.is_visible_in_tree():
				ok = b
				break
		if ok == null:
			return
		await Tap.tap(ok)
		await _settle()


func _text(n: Node) -> String:
	var out := []
	for c in n.find_children("*", "Label", true, false):
		out.append((c as Label).text)
	return " ".join(PackedStringArray(out))


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
