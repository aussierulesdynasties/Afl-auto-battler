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
const KEYS := ["draft", "selection", "coaching", "list", "staff", "offseason", "preseason", "season_review",
		"contracts", "trade", "draft_trade", "league_draft"]
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
	await _t("_test_contract_and_trade_tutorials")
	await _t("_test_draft_trade_tutorial")
	await _t("_test_postseason_on_hub")
	await _t("_test_postseason_when_knocked_out")
	await _t("_test_postseason_not_when")
	await _t("_test_postseason_per_career")
	await _t("_test_postseason_not_used_without_you")
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


## A fresh career's first off-season, every intro unseen and tips on, with
## one of your players out of contract so there are talks to open.
func _fresh_offseason() -> void:
	_reset_seen()
	_state.reset()
	_state.replay_seed = SUITE_SEED
	_state.tutorials = true
	_state.start_season("FRE", root.get_node("GameDB").club_list("FRE"))
	_state.season.round_index = _state.season.fixture.size()
	_state.open_offseason()
	var p: Dictionary = _state.my_list[0]
	p["contract_years"] = 1
	for k in ["resigned", "talks", "retiring"]:
		p.erase(k)


func _tap_named(host: Node, node_name: String) -> String:
	var b: Control = host.find_child(node_name, true, false)
	if b == null:
		return "no " + node_name
	var why: String = await Tap.tap(b)
	await _settle()
	return why


## The trade and contract tutorials (row T3.R56): each opens over its own
## screen the first time a finger gets there, Got it takes a tap, Back closes
## it before the screen, and it never comes back. Tips off: neither opens.
func _test_contract_and_trade_tutorials() -> void:
	_fresh_offseason()
	root.size = Vector2i(390, 844)
	var s: Control = load("res://scenes/OffseasonScene.tscn").instantiate()
	root.add_child(s)
	await _settle()
	_check(s.find_child("OffseasonIntroOk", true, false) != null, "The off-season opens with its own intro first")
	_check((await _tap_named(s, "OffseasonIntroOk")) == "", "Off-season Got it takes a tap")
	_check(s.find_child("ContractsIntro", true, false) == null, "No contract tutorial before any talks")
	_check((await _tap_named(s, "Negotiate")) == "", "Talk contract takes a tap")
	_check(s.find_child("ContractTalks", true, false) != null, "The talks sheet opens")
	var ok: Button = s.find_child("ContractsIntroOk", true, false)
	_check(ok != null and ok.size.y >= 44.0, "...with the contract tutorial over it, Got it thumb-sized")
	_check((await _tap_named(s, "ContractsIntroOk")) == "", "Contract Got it takes a tap")
	_check(s.find_child("ContractsIntro", true, false) == null and s.find_child("ContractTalks", true, false) != null,
			"Got it closes the tutorial and leaves the talks open")
	_check((await _tap_named(s, "CancelTalks")) == "", "Cancel closes the talks")
	_check((await _tap_named(s, "Negotiate")) == "", "Talk contract again")
	_check(s.find_child("ContractTalks", true, false) != null and s.find_child("ContractsIntro", true, false) == null,
			"Talks a second time: no tutorial")
	await _tap_named(s, "CancelTalks")
	_check((await _tap_named(s, "Tab_trade")) == "", "The Trade tab takes a tap")
	_check(s.find_child("TradeIntroOk", true, false) != null, "The Trade tab opens the trade tutorial")
	_check(s.find_child("MakeTrade", true, false) != null, "...over the trade sheet")
	_check(s.handle_back(), "Back closes the trade tutorial first")
	await _settle()
	_check(s.find_child("TradeIntro", true, false) == null and s.is_inside_tree(), "...and the off-season stays")
	await _tap_named(s, "Tab_contracts")
	await _tap_named(s, "Tab_trade")
	_check(s.find_child("TradeIntro", true, false) == null, "Trade tab a second time: no tutorial")
	s.queue_free()
	await _settle()
	# Tips off: neither opens, and neither is used up.
	_fresh_offseason()
	_state.tutorials = false
	s = load("res://scenes/OffseasonScene.tscn").instantiate()
	root.add_child(s)
	await _settle()
	await _tap_named(s, "Negotiate")
	_check(s.find_child("ContractTalks", true, false) != null and s.find_child("ContractsIntro", true, false) == null,
			"Tips off: talks open with no tutorial")
	await _tap_named(s, "CancelTalks")
	await _tap_named(s, "Tab_trade")
	_check(s.find_child("MakeTrade", true, false) != null and s.find_child("TradeIntro", true, false) == null,
			"Tips off: no trade tutorial")
	_check(not bool(_state.get_setting("seen_contracts_intro", false)) and not bool(_state.get_setting("seen_trade_intro", false)),
			"Tips off leaves both unseen")
	s.queue_free()
	_state.tutorials = true
	await _settle()


## Draft night's pick trading: the first Trade picks opens its tutorial over
## the sheet; Got it takes a tap and the sheet stays; the next time, none.
func _test_draft_trade_tutorial() -> void:
	_fresh_offseason()
	_state.set_setting("seen_draft_intro", true)
	_state.set_setting("seen_combine_intro", true)
	root.size = Vector2i(390, 844)
	if not _state.begin_intake_draft():
		_check(false, "The draft opens")
		return
	var draft = _state.draft
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _settle()
	var skip: Button = ui.find_child("MeetingDone", true, false)
	if skip != null:
		skip.pressed.emit()
		await _settle()
	var guard := 0
	while not draft.is_user_turn() and not draft.is_finished() and guard < 200:
		guard += 1
		draft.auto_until_user_turn()
	ui.call("_refresh")
	await _settle()
	_check((await _tap_named(ui, "TradePicks")) == "", "Trade picks takes a tap")
	_check(ui.find_child("TradeSheet", true, false) != null, "The pick-trading sheet opens")
	_check(ui.find_child("DraftTradeIntroOk", true, false) != null, "...with its tutorial over it")
	_check((await _tap_named(ui, "DraftTradeIntroOk")) == "", "Got it takes a tap")
	_check(ui.find_child("DraftTradeIntro", true, false) == null and ui.find_child("TradeSheet", true, false) != null,
			"Got it closes the tutorial, the sheet stays")
	_check((await _tap_named(ui, "TradeSheetClose")) == "", "Back to the draft takes a tap")
	_check((await _tap_named(ui, "TradePicks")) == "", "Trade picks again")
	_check(ui.find_child("TradeSheet", true, false) != null and ui.find_child("DraftTradeIntro", true, false) == null,
			"Trade picks a second time: no tutorial")
	ui.queue_free()
	_state.draft = null
	await _settle()


## A club in the finals at this ladder place, tips on, the intro not yet seen.
func _in_finals(rank: int) -> void:
	_reset_seen()
	_state.set_setting("seen_weekly_loop_intro", true)
	_state.reset()
	_state.replay_seed = SUITE_SEED
	_state.tutorials = true
	_state.start_season("COL", root.get_node("GameDB").club_list("COL"))
	var sea = _state.season
	var codes: Array = sea.ladder.keys()
	codes.sort()
	codes.erase("COL")
	codes.insert(rank - 1, "COL")
	for i in range(codes.size()):
		var row: Dictionary = sea.ladder[codes[i]]
		row["w"] = 20 - i
		row["l"] = 3 + i
		row["d"] = 0
		row["p"] = 23
		row["pf"] = 2400 - i * 20
		row["pa"] = 2000
	sea.round_index = sea.fixture.size()
	sea.recalc_ladder()
	sea.start_finals()
	_state.week_events = []


func _hub() -> Control:
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	return hub


func _gone(hub: Control) -> void:
	hub.queue_free()
	await _settle()


## Once the finals are over the hub says the order, in the buttons' own words,
## before anything is decided; a tap closes it, Back closes it, and it's once.
func _test_postseason_on_hub() -> void:
	_in_finals(1)
	var hub: Control = await _hub()
	_check(hub.find_child("PostseasonIntro", true, false) == null, "No postseason intro while the finals are on")
	await _gone(hub)
	_state.season.finals["done"] = true
	hub = await _hub()
	_check(hub.find_child("PostseasonIntro", true, false) != null, "The finals over, the hub opens the postseason intro")
	for l in _FV.TEXT["postseason"][1]:
		_check(str(l).length() <= 120, "Postseason intro line is short: %s" % l)
	var said := " ".join(_FV.TEXT["postseason"][1])
	var at: Array = []
	for step in ["Season review", "Trades & Contracts", "National Draft", "pre-season", "Round 1"]:
		at.append(said.find(step))
	var sorted := at.duplicate()
	sorted.sort()
	_check(not at.has(-1) and at == sorted, "It names each stop, in the order they come (%s)" % str(at))
	var ok: Button = hub.find_child("PostseasonIntroOk", true, false)
	_check(ok != null and (await Tap.tap(ok)) == "", "Got it takes a finger's tap")
	await _settle()
	_check(hub.find_child("PostseasonIntro", true, false) == null, "Got it closes it")
	_check(hub.find_child("WeekActions", true, false) != null, "...and the off-season's buttons are there")
	await _gone(hub)
	hub = await _hub()
	_check(hub.find_child("PostseasonIntro", true, false) == null, "It opens once")
	await _gone(hub)
	_state.postseason_intro_seen = false
	hub = await _hub()
	_check(hub.find_child("PostseasonIntro", true, false) != null, "Unseen again, it's there")
	_check(hub.handle_back(), "Back closes it first")
	await _settle()
	_check(hub.find_child("PostseasonIntro", true, false) == null and hub.is_inside_tree(), "...and stays on the hub")
	await _gone(hub)


## Knocked out early: the league plays on from the hub, and the intro waits until
## the last results are closed.
func _test_postseason_when_knocked_out() -> void:
	_in_finals(14)
	var hub: Control = await _hub()
	var weeks := 0
	while not _state.season.is_season_over() and weeks < 8:
		weeks += 1
		hub.call("_sim_week")
		await _settle()
		_check(hub.find_child("PostseasonIntro", true, false) == null, "No intro over week %d's results" % weeks)
		var go: Button = hub.find_child("ResultsContinue", true, false)
		if not _state.season.is_season_over() and go != null:
			go.pressed.emit()
			await _settle()
	_check(_state.season.is_season_over(), "The finals play out with him watching")
	var last: Button = hub.find_child("ResultsContinue", true, false)
	_check(last != null, "The Grand Final's results come up")
	if last != null:
		_check((await Tap.tap(last)) == "", "Continue takes a finger's tap")
		await _settle()
	_check(hub.find_child("PostseasonIntro", true, false) != null, "The results closed, the intro opens")
	await _gone(hub)


## Tips off stays off, sacked the off-season isn't his, a press conference goes
## first, a draft under way is past it. None of them uses up the intro.
func _test_postseason_not_when() -> void:
	_in_finals(1)
	_state.season.finals["done"] = true
	_state.tutorials = false
	var hub: Control = await _hub()
	_check(hub.find_child("PostseasonIntro", true, false) == null, "Tips off: no postseason intro")
	await _gone(hub)
	_state.tutorials = true
	_state.board["sacked"] = true
	hub = await _hub()
	_check(hub.find_child("PostseasonIntro", true, false) == null, "Sacked: no postseason intro")
	await _gone(hub)
	_state.board["sacked"] = false
	_state.draft = load("res://scripts/sim/Draft.gd").new([])
	_state.draft.intake_mode = true
	hub = await _hub()
	_check(hub.find_child("PostseasonIntro", true, false) == null, "A draft under way: no postseason intro")
	await _gone(hub)
	_state.draft = null
	_check(_state.intro_due("postseason"), "None of them used it up")


## The sheet belongs to the career: a new career on the same device sees it, the
## save carries it, a save from before it doesn't get it, and it's the first
## postseason only, seen or not.
func _test_postseason_per_career() -> void:
	_in_finals(1)
	_state.season.finals["done"] = true
	var hub: Control = await _hub()
	_check(hub.find_child("PostseasonIntro", true, false) != null, "A fresh career sees it")
	await _gone(hub)
	_check(not _state.intro_due("postseason"), "...once")
	_check(not bool(_state.get_setting("seen_postseason_intro", false)), "...and the device keeps no mark of it")
	var saved: Dictionary = _state._save_state()
	_check(bool(saved.get("postseason_intro_seen", false)), "The save carries it")
	_in_finals(1)
	_state.season.finals["done"] = true
	_check(_state.intro_due("postseason"), "A new career on the same device gets it")
	hub = await _hub()
	_check(hub.find_child("PostseasonIntro", true, false) != null, "...on the hub")
	await _gone(hub)
	_state.postseason_intro_seen = false
	saved = _state._save_state()
	_check(not bool(saved.get("postseason_intro_seen", true)), "Unseen saves as unseen")
	var unseen: bool = _state._restore_career(saved.duplicate(true))
	_check(unseen and _state.intro_due("postseason"), "...and loads as unseen")
	var old: Dictionary = saved.duplicate(true)
	old.erase("postseason_intro_seen")
	var loaded: bool = _state._restore_career(old)
	_check(loaded and not _state.intro_due("postseason"), "A save from before the sheet isn't a fresh career")
	# Tips off through the first postseason: the next one doesn't make up for it.
	_in_finals(1)
	_state.season.finals["done"] = true
	_state.tutorials = false
	var rolled: bool = _state.start_next_season()
	_check(rolled, "The season rolls on")
	_state.tutorials = true
	_check(not _state.intro_due("postseason"), "Past his first postseason, it's gone, seen or not")


## Bug-bash 6 (2026-11-10): a season played without you (sim-ahead, waiting
## for Tasmania, a pre-made history) closing must not use up the sheet; only
## his own first postseason does.
func _test_postseason_not_used_without_you() -> void:
	_in_finals(1)
	_state.season.finals["done"] = true
	_check(_state.my_first_season == _state.season_year, "A club from the start: this season is his first")
	# The 2029 National Draft shape: the club chosen after a season played without you.
	_state.my_first_season = 0
	var year: int = _state.season_year
	_check(_state.start_next_season(), "The season played without you rolls on")
	_check(_state.intro_due("postseason"), "...and his first postseason's sheet is still due")
	_check(_state.my_first_season == year + 1, "The next season is his first")
	var saved: Dictionary = _state._save_state()
	_check(int(saved.get("my_first_season", 0)) == year + 1, "The save carries his first season")
	# Years with no club of yours at all (sim-ahead).
	_in_finals(1)
	_state.season.finals["done"] = true
	_state.my_first_season = 0
	_state.sim_ahead = true
	_state.my_club = ""
	_check(_state.start_next_season(), "A sim-ahead year rolls on")
	_check(_state.my_first_season == 0, "...with no first season of his")
	_state.my_club = "COL"
	_state.sim_ahead = false
	_check(_state.intro_due("postseason"), "...and the sheet still due")


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
