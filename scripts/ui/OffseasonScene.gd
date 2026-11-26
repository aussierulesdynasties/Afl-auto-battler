extends Control
## The off-season between the Grand Final and the national draft: contracts,
## free agency, trades and the club's annual department allocation.

var _name_index := {}
var _root: VBoxContainer
var _tab := "contracts"
var _notice := ""
## A notice that gives a reason (a free agent who turned you down or chose a
## rival, P-18) reads as text, not a success, with the rival's name in its ink.
var _notice_club := ""
var _notice_club_text := ""   # the reason notice it belongs to: any other notice stays as it was
var _trade_club := ""
var _mine: Array = []     # your player and pick ids in the trade
var _theirs: Array = []   # theirs
var _trade_side := "theirs"   # which list the builder shows to add from
var _choosing_club := false   # the club sheet is open
var _counter_key := ""
var _counter := {}
var _scroll_box: ScrollContainer
var _scroll_tab := ""
var _scroll_positions := {}
## The draft gate's Delist: open Contracts scrolled to "Out of contract" (once).
var _land_on_expiring := false
## A PC's Contracts: the man whose card shows beside the list.
var _pick_id := ""
## A short PC's Contracts card: "contract" (what he wants and the buttons) or
## "ratings" (his time with us and every rating); it stays put as he picks men.
var _card_stage := "contract"
## The height under the tabs as last laid out (0 until then): a PC's Contracts
## and Our list fill it rather than scroll.
var _room := 0.0
var _release_overlay: Control
var _talk_overlay: Control
var _talk_id := ""
var _talk_fa := false   # talking to a free agent rather than your own player
var _offer_salary := 0
var _offer_years := 0
var _talk_reply := ""
var _fa_sort := "value"
var _fa_sort_desc := true
var _asked_id := ""       # the player you asked around about (P-50)
var _asked: Array = []    # every rival's answer, GameState.ask_around
var _price := {}          # their price for one of their players: {"club", "id", "line"}, GameState.ask_price


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if GameState.season == null:
		Router.replace("main")
		return
	GameState.open_offseason()
	# The draft's list gate sends the coach to the tab he chose (Delist or Trade).
	if DraftSpotsSheet.route_tab != "":
		_tab = DraftSpotsSheet.route_tab
		DraftSpotsSheet.route_tab = ""
		# Delist lands on the players he can delist, not on the Retiring cards.
		_land_on_expiring = _tab == "contracts"
	# Your club's colour behind the page, as on the hub and match day
	# (director, 2026-10-10: every screen in the gameday style).
	add_child(ClubBackdrop.new().setup(GameState.my_club))
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(margin, 12)
	add_child(margin)
	_root = UiKit.vbox(UiKit.GAP)
	margin.add_child(_root)
	for code in GameDB.active_clubs(GameState.season_year):
		if code != GameState.my_club:
			_trade_club = code
			break
	get_viewport().size_changed.connect(func():
		if is_inside_tree() and not UiKit.keyboard_resize(self):
			_build())
	_build()
	FirstVisitIntro.show_if_due.call_deferred(self, "offseason")


func _build() -> void:
	_name_index = {}
	if is_instance_valid(_scroll_box):
		_scroll_positions[_scroll_tab] = UiKit.scroll_place(_scroll_box)
	UiKit.clear(_root)
	_root.add_child(UiKit.top_bar("Off-season", true))
	var head := UiKit.panel(UiKit.PANEL, UiKit.Space.ROOM, 8)
	_root.add_child(head)
	var hv := UiKit.vbox(UiKit.Space.TIGHT)
	# A PC: what you just did, and its Undo, sit beside the list's brief in
	# the heading's empty right-hand third, so a signing never pushes Contracts down.
	var news := hv
	if _wide() and (_notice != "" or not GameState.recruit_undo_last().is_empty()):
		var split := UiKit.hbox(UiKit.Space.GUTTER)
		head.add_child(split)
		hv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		hv.size_flags_stretch_ratio = 2.0
		split.add_child(hv)
		news = UiKit.vbox(UiKit.Space.TIGHT)
		news.name = "HeadNews"
		news.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		split.add_child(news)
	else:
		head.add_child(hv)
	var room := GameState.cap_room()
	hv.add_child(UiKit.lbl("%s of the %s salary cap  ·  %s  ·  %d on our list" % [Contracts.money(GameState.my_payroll()),
			Contracts.money(GameState.cap_for(GameState.my_club)), cap_room_words(room), GameState.my_list.size()], 15,
			UiKit.GOOD if room >= 0 else UiKit.BAD, true))
	# A season that paid every player less (2020): said under the cap it changes.
	var cut := Contracts.pay_cut_note(Contracts.money_year)
	if cut != "":
		var cut_l := _para(cut, 13, UiKit.TEXT)
		cut_l.name = "PayCutNote"
		hv.add_child(cut_l)
	# Your challenge's rule, said where it bites: who you may bring in.
	if Challenge.kind(GameState) in ["youth", "rebuild"]:
		var rule := _para(Challenge.stated_line(GameState), 13, UiKit.EMPH)
		rule.name = "ChallengeRule"
		hv.add_child(rule)
	if not GameState.offseason_open():
		hv.add_child(_para("The off-season is closed. Trades and contracts open when the season ends. They close when the national draft starts.", 13, UiKit.MUTED))
	else:
		# This year's list problem in three lines (P-48): the brief, no advice.
		var brief := UiKit.vbox(UiKit.Space.SLIM)
		brief.name = "ListProblem"
		hv.add_child(brief)
		var lines := GameState.list_problem()
		for i in lines.size():
			var l := UiKit.lbl(str(lines[i]), 14, UiKit.TEXT, i == 0)
			l.name = "ListProblem_%d" % i
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			brief.add_child(l)
	if _notice != "":
		var said := _why_para(_notice, _notice_club, 13, UiKit.TEXT) if _notice_club_text != "" and _notice == _notice_club_text \
				else _para(_notice, 13, UiKit.GOOD)
		said.name = "OffseasonNotice"
		news.add_child(said)
	_undo_row(news)
	var tabs := UiKit.hbox(UiKit.Space.TIGHT)
	_root.add_child(tabs)
	var tab_list := [["contracts", "Contracts"], ["agents", "Agents"], ["trade", "Trade"], ["budget", "Budget"]]
	# A PC: the whole list is a stage of its own, not the foot of Contracts.
	if _wide():
		tab_list.insert(1, ["list", "Our list"])
	elif _tab == "list":
		_tab = "contracts"
	for t in tab_list:
		var b := UiKit.tab(str(t[1]), _tab == str(t[0]))
		b.name = "Tab_" + str(t[0])
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.pressed.connect(func():
			_tab = str(t[0])
			_notice = ""
			_notice_club = ""
			_notice_club_text = ""
			_choosing_club = false
			_build()
			if _tab == "trade":
				FirstVisitIntro.show_if_due(self, "trade"))
		tabs.add_child(b)
	var body := UiKit.vbox(UiKit.Space.CLOSE)
	_scroll_box = UiKit.scroll(body)
	_scroll_tab = _tab
	_root.add_child(_scroll_box)
	match _tab:
		"contracts":
			if _wide():
				_contracts_pc(body)
			else:
				_contracts(body)
		"list":
			_whole_list(body)
		"agents":
			_agents(body)
		"trade":
			_trade(body)
		"budget":
			_budget(body)
	UiKit.restore_scroll(_scroll_box, int(_scroll_positions.get(_tab, 0)))
	if _wide() and _tab in ["contracts", "list"]:
		# These pages fit their window. A scroll bar would take 10 px of width, rewrap the card's
		# words and grow the page past the window it fitted.
		_scroll_box.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
		_fit_room(_scroll_box, _room_now())
	if _land_on_expiring and _tab == "contracts":
		_land_on_expiring = false
		# A PC opens Contracts on the first man out of contract already.
		if not _wide():
			_scroll_to_expiring.call_deferred(_scroll_box, body)


## Scrolls the Contracts list so the "Out of contract" heading is at its top.
func _scroll_to_expiring(sc: ScrollContainer, body: Control) -> void:
	for i in range(2):
		await get_tree().process_frame
	if not is_instance_valid(sc) or not is_instance_valid(body):
		return
	var head := body.find_child("OutOfContractHead", true, false) as Control
	if head != null:
		sc.scroll_vertical = int(head.global_position.y - body.global_position.y)


## Your last delisting, free-agent signing or re-signing can be taken back
## until the national draft starts (row 119, P-09). One tap, no confirm: the
## undo puts everything back as it was, so it is its own safety net.
func _undo_row(hv: VBoxContainer) -> void:
	var last := GameState.recruit_undo_last()
	if last.is_empty():
		return
	var name := str(last["name"])
	var did := ""
	match str(last["kind"]):
		"release":
			did = "We delisted %s." % name
		"sign":
			did = "%s signed with us." % name
		"resign":
			did = "%s re-signed." % name
	var row := UiKit.hbox(UiKit.GAP)
	row.name = "UndoLast"
	hv.add_child(row)
	# Right after the action its own notice names him; the row then only says
	# what Undo does, so the same news is not printed twice.
	var text := "Undo it any time before the national draft starts." if _notice.contains(name) \
			else did + " Undo it any time before the national draft starts."
	var said := _para(text, 13, UiKit.TEXT)
	said.name = "UndoLastText"
	said.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(said)
	var b := UiKit.btn("Undo", 15)
	b.name = "UndoAction"
	b.custom_minimum_size = Vector2(0, _tap_h()) if _wide() else Vector2(88, 48)
	b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	b.pressed.connect(func():
		var r := GameState.undo_recruit()
		_notice = str(r["reason"])
		_prune_trade()  # an undone signing takes him out of the trade being built
		_notice_club = ""
		_notice_club_text = ""
		_build())
	row.add_child(b)


func _budget(body: VBoxContainer) -> void:
	var year := GameState.department_budget_year if GameState.department_budget_year > 0 \
			else GameState.season_year + 1
	body.add_child(UiKit.lbl("Club budget · %d" % year, UiKit.NAME, UiKit.EMPH, true))
	body.add_child(_para(
			"We have %s to spend on the football year. It resets next off-season. Nothing carries over." \
			% ClubBudget.money_m(ClubBudget.ANNUAL_M, year), 13, UiKit.MUTED))
	var spent := GameState.department_budget_spent_m()
	var remaining := GameState.department_budget_remaining_m()
	var summary := UiKit.lbl("%s spent  ·  %s left" % [ClubBudget.money_m(spent, year), ClubBudget.money_m(maxf(0.0, remaining), year)],
			14, UiKit.TEXT, true)
	summary.name = "BudgetSummary"
	body.add_child(summary)
	# A league fine (YearEvents) cuts this year's budget: say so beside the total.
	var fine_cut := ClubBudget.ANNUAL_M - GameState.department_budget_annual_m()
	if fine_cut > 0.001:
		var fine := _para("The league's fine takes %s off our budget this year." % ClubBudget.money_m(fine_cut, year), 13, UiKit.BAD)
		fine.name = "BudgetFine"
		body.add_child(fine)
	body.add_child(UiKit.spacer(UiKit.Space.TIGHT))

	for area in ClubBudget.AREA_ORDER:
		var level := GameState.department_budget_level(area)
		var card := UiKit.panel(UiKit.PANEL, UiKit.GAP, 8)
		card.name = "Budget_" + area
		body.add_child(card)
		var v := UiKit.vbox(UiKit.Space.TIGHT)
		card.add_child(v)
		var head := UiKit.hbox(UiKit.GAP)
		v.add_child(head)
		var label := UiKit.lbl(str(ClubBudget.AREA_LABEL[area]), UiKit.BODY, UiKit.TEXT, true)
		label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		head.add_child(label)
		head.add_child(UiKit.line("%s · %s" % [
				ClubBudget.level_label(level), ClubBudget.money_m(ClubBudget.cost_m(level), year)], 13, UiKit.MUTED, true))

		var current := _para(ClubBudget.benefit_text(area, level), 13, UiKit.TEXT)
		current.name = "BudgetBenefit_" + area
		v.add_child(current)

		var next_text := UiKit.lbl("", 12, UiKit.MUTED)
		next_text.name = "BudgetNext_" + area
		next_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		if level < ClubBudget.LEVELS.size() - 1:
			next_text.text = "Raise to %s (%s). %s" % [
					ClubBudget.level_label(level + 1), ClubBudget.money_m(ClubBudget.cost_m(level + 1), year),
					ClubBudget.benefit_text(area, level + 1)]
		else:
			next_text.text = "Fully funded."
		v.add_child(next_text)

		var controls := UiKit.hbox(UiKit.Space.CLOSE)
		v.add_child(controls)
		var lower := UiKit.btn("Lower", UiKit.SECONDARY)
		lower.name = "BudgetLower_" + area
		lower.custom_minimum_size.y = 44
		lower.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		lower.disabled = level <= 0
		lower.pressed.connect(_change_budget.bind(area, level - 1))
		controls.add_child(lower)

		var raise := UiKit.btn("Raise", UiKit.SECONDARY)
		raise.name = "BudgetRaise_" + area
		raise.custom_minimum_size.y = 44
		raise.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		raise.disabled = level >= ClubBudget.LEVELS.size() - 1 \
				or not GameState.can_set_department_budget(area, level + 1)
		raise.pressed.connect(_change_budget.bind(area, level + 1))
		controls.add_child(raise)


func _change_budget(area: String, level: int) -> void:
	var result := GameState.set_department_budget(area, level)
	_notice = "" if bool(result.get("ok", false)) else str(result.get("reason", ""))
	_build()


func _contracts(body: VBoxContainer) -> void:
	# A retiring player is in Retiring above, not up for a contract.
	var expiring := Contracts.expiring(GameState.my_list).filter(func(q): return not GameState.retiring_now(q))
	_compensation_lines(body)
	_retiring(body)
	if GameState.offseason_open():
		body.add_child(_unsigned_rule(12))
	var head := UiKit.lbl("Out of contract  (%d)" % expiring.size(), UiKit.BODY, UiKit.EMPH, true)
	head.name = "OutOfContractHead"
	body.add_child(head)
	if expiring.is_empty():
		body.add_child(_para("Nobody is out of contract this year.", 13, UiKit.MUTED))
	for p in expiring:
		var card := _player_card(p, _contract_detail(p))
		body.add_child(card)
		var row := UiKit.hbox(UiKit.Space.TIGHT)
		row.name = "Contract_" + str(p["id"])
		_action_slot(card).add_child(row)
		_contract_parts(p, row, card.get_child(0) as VBoxContainer, 12, 44)
	body.add_child(UiKit.lbl("Our whole list", UiKit.BODY, UiKit.EMPH, true))
	var sorted := GameState.my_list.duplicate()
	sorted.sort_custom(func(a, b): return int(a.get("salary", 0)) > int(b.get("salary", 0)))
	for p in sorted:
		# The season just played still counts in contract_years until the
		# rollover (Re-signed above says years - 1 too).
		var left := int(p.get("contract_years", 1)) - 1
		var term := "out of contract" if left <= 0 else "%d season%s left" % [left, "" if left == 1 else "s"]
		body.add_child(_para("%s  ·  %d OVR  ·  %s  ·  %s" % [
				GameDB.player_display_name(p), int(Rating.ovr(p)), Contracts.money(int(p.get("salary", 0))),
				term], 12, UiKit.TEXT))


## Your players retiring at the end of the off-season. A healthy one can be
## asked once to go around again; his answer, and its reason, stays shown.
func _retiring(body: VBoxContainer) -> void:
	var rows: Array = GameState.retiring_players()
	if rows.is_empty():
		return
	body.add_child(UiKit.lbl("Retiring  (%d)" % rows.size(), UiKit.BODY, UiKit.EMPH, true))
	for r in rows:
		var p: Dictionary = r["p"]
		var card := _player_card(p, _retiring_detail(p))
		card.name = "Retiring_" + str(p["id"])
		body.add_child(card)
		var v := card.get_child(0) as VBoxContainer
		var talk: Dictionary = r["talk"]
		if not talk.is_empty():
			var said := _para(str(talk["reason"]), 13, UiKit.GOOD if bool(talk["stays"]) else UiKit.TEXT)
			said.name = "RetireAnswer"
			v.add_child(said)
		elif bool(r["can_ask"]):
			# An action said as words beside the fact (guide §3), not a bar per row.
			var ask := UiKit.text_action("Ask him to go around again")
			ask.name = "TalkRound"
			ask.alignment = HORIZONTAL_ALIGNMENT_LEFT
			ask.pressed.connect(func():
				GameState.talk_round(str(p["id"]))
				_build())
			_action_slot(card).add_child(ask)
			_ask_stakes(p, v)
		elif p.has("talked_round"):
			v.add_child(_para("He went around again once already. This time he's going.", 12, UiKit.MUTED))


## The draft picks we get for players we lost in free agency.
func _compensation_lines(body: VBoxContainer) -> void:
	var clubs := GameDB.active_clubs(GameState.season_year).size()
	for c in GameState.compensation:
		if str(c["club"]) == GameState.my_club:
			var got := _para("We get a draft pick %s for losing %s to %s." % [
					Contracts.pick_words(int(c["after"]), clubs), str(c["name"]), GameDB.club_name(str(c["to"]))], 13, UiKit.TEXT)
			got.name = "CompReceived"
			body.add_child(got)


## What happens to a man left unsigned. No free agency before 2012 (EraRules
## free_agency): he re-signs or is delisted (bug bash 4, L13).
func _unsigned_rule(size: int) -> Control:
	var how := "Leave one of our best 23 unsigned and he tests free agency. Our offer stands at his asking price. Rivals can beat it. Other players re-sign for two seasons if the cap allows." \
			if EraRules.on("free_agency", GameState.season_year) \
			else "Leave a player unsigned and he re-signs for two seasons if the cap allows; if it doesn't, he is delisted. Free agency starts in 2012."
	var how_para := _para(how, size, UiKit.MUTED)
	how_para.name = "UnsignedRule"
	return how_para


func _contract_detail(p: Dictionary) -> String:
	var want := Contracts.wants(p)
	return "%d OVR  ·  %d POT  ·  age %d  ·  on %s  ·  wants %s for %d seasons" % [
			int(Rating.ovr(p)), int(p.get("potential", Rating.ovr(p))), int(p.get("age", 0)),
			Contracts.money(int(p.get("salary", 0))), Contracts.money(int(want["salary"])), int(want["years"])]


func _retiring_detail(p: Dictionary) -> String:
	var g := GameState.season_games(str(p["id"]))
	return "%d OVR  ·  age %d  ·  %s this year" % [
			int(Rating.ovr(p)), int(p.get("age", 0)), "1 game" if g == 1 else "%d games" % g]


## What asking a retiring man to go around again gains and costs.
func _ask_stakes(p: Dictionary, info: VBoxContainer) -> void:
	var g := GameState.season_games(str(p["id"]))
	var gc := ListCosts.ask_lines(Retirement.no_reason(p, GameState.season_year, g, GameState.career_facts))
	info.add_child(UiKit.stake_row(str(gc[0]), "AskGain"))
	info.add_child(UiKit.stake_row(str(gc[1]), "AskCost"))


## A man out of contract, on a phone's card or a PC's: what he said or the odds
## into `info`, his actions (`h` tall) into `row`.
func _contract_parts(p: Dictionary, row: HBoxContainer, info: VBoxContainer, size: int, h: int) -> void:
	if bool(p.get("resigned", false)):
		row.add_child(UiKit.line("Re-signed for %d more seasons at %s" % [int(p["contract_years"]) - 1,
				Contracts.money(int(p.get("salary", 0)))], 13, UiKit.GOOD, true))
		return
	var talks: Dictionary = p.get("talks", {})
	if bool(talks.get("walked", false)):
		var gone := "Talks broke down. He'll test free agency"
		if talks.has("refused"):
			gone = Contracts.REFUSED_CARD % int(talks["refused"])
		row.add_child(UiKit.line(gone, UiKit.SECONDARY, UiKit.BAD, true))
		var proj := _para(str(GameState.projected_compensation(p)["reason"]), size, UiKit.TEXT)
		proj.name = "CompProjection"
		info.add_child(proj)
		return
	if talks.has("counter"):
		info.add_child(_para("He'd sign for %s over %d season%s." % [
				Contracts.money(int(talks["counter"])), int(talks["years"]), "" if int(talks["years"]) == 1 else "s"], size, UiKit.TEXT))
	var odds := _refuse_odds(p, size)
	if odds != null:
		odds.name = "RefuseOdds"
		info.add_child(odds)
	var talk := UiKit.btn("Talk contract", UiKit.SECONDARY)
	talk.name = "Negotiate"
	talk.custom_minimum_size = Vector2(0, h)
	# Across a phone's card; on a PC sized to its words.
	if not _wide():
		talk.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	talk.pressed.connect(_open_talks.bind(str(p["id"])))
	row.add_child(talk)
	# Talked round this off-season: he stays until the next one (the ask's cost).
	if ListStings.release_held(p, GameState.season_year + 1):
		var held := _para(ListCosts.HELD_LINE, size, UiKit.TEXT)
		held.name = "ReleaseHeld"
		info.add_child(held)
		return
	var rel := UiKit.btn("Release", UiKit.SECONDARY)
	rel.name = "Release"
	rel.custom_minimum_size = Vector2(0, h)
	rel.pressed.connect(_confirm_release.bind(p))
	row.add_child(rel)


func _confirm_release(p: Dictionary) -> void:
	if is_instance_valid(_release_overlay):
		return
	var box := UiKit.modal_box(self, 440.0, 0.0)
	_release_overlay = box["overlay"]
	_release_overlay.name = "ReleaseConfirmation"
	box["body"].add_child(_para("Release %s?" % GameDB.player_display_name(p), 20, UiKit.TEXT))
	# What the club remembers of him, once (P-37): the drop has a face. Read-only.
	var kept := Remembered.release_line(p, GameState.career_facts, GameState.my_club,
			GameState.with_us(p), GameState.LEARN_JOBS)
	if kept != "":
		var memory := _para(kept, 14, UiKit.TEXT)
		memory.name = "ReleaseRemembered"
		box["body"].add_child(memory)
	box["body"].add_child(_para("He leaves our list and becomes a free agent. We get no draft pick if he signs elsewhere.", 14, UiKit.TEXT))
	var gc := ListCosts.release_lines(p)
	box["body"].add_child(UiKit.stake_row(str(gc[0]), "ReleaseGain"))
	box["body"].add_child(UiKit.stake_row(str(gc[1]), "ReleaseCost"))
	var release := UiKit.btn("Release player", UiKit.NAME, true)
	release.name = "ConfirmRelease"
	release.custom_minimum_size.y = 44
	release.pressed.connect(func():
		_close_release()
		_notice = str(GameState.release_player(str(p["id"]))["reason"])
		_prune_trade()
		_build())
	box["footer"].add_child(release)
	var cancel := UiKit.btn("Cancel", UiKit.NAME)
	cancel.name = "CancelRelease"
	cancel.custom_minimum_size.y = 44
	cancel.pressed.connect(_close_release)
	box["footer"].add_child(cancel)


func _close_release() -> void:
	if is_instance_valid(_release_overlay):
		_release_overlay.queue_free()
	_release_overlay = null


func handle_back() -> bool:
	if FirstVisitIntro.close_open(self):
		return true
	if _choosing_club and _tab == "trade":
		_choosing_club = false
		_build()
		return true
	if is_instance_valid(_talk_overlay):
		_close_talks()
		return true
	if not is_instance_valid(_release_overlay):
		return false
	_close_release()
	return true


## Contract talks: propose a salary and a term; he accepts, counters or, after
## too many failed offers, walks. Nothing is signed until he accepts.
func _open_talks(player_id: String, free_agent := false) -> void:
	_talk_fa = free_agent
	_talk_id = player_id
	var p := _talk_player()
	if p.is_empty():
		return
	var want := Contracts.wants(p)
	var talks: Dictionary = p.get("talks", {})
	_talk_reply = ""
	_offer_salary = int(talks.get("counter", want["salary"]))
	# Never carry the last player's term into these talks.
	_offer_years = 0
	if free_agent:
		# Start from your standing offer, if you have one on the table.
		for row in GameState.fa_offers(player_id):
			if bool(row["mine"]):
				_offer_salary = int(row["salary"])
				_offer_years = int(row["years"])
	if not free_agent or _offer_years <= 0:
		_offer_years = int(talks.get("years", want["years"]))
	_show_talks()
	# Your own player's talks get the contract tutorial; a free agent's market
	# reads differently and explains itself on the sheet.
	if not free_agent:
		FirstVisitIntro.show_if_due(self, "contracts")


func _talk_player() -> Dictionary:
	return GameState.free_agent(_talk_id) if _talk_fa else GameState.list_player(_talk_id)


func _show_talks() -> void:
	if is_instance_valid(_talk_overlay):
		_talk_overlay.queue_free()
	var p := _talk_player()
	var want := Contracts.wants(p)
	var talks: Dictionary = p.get("talks", {})
	var terms := GameState.free_agent_terms(_talk_id) if _talk_fa else {}
	var box := UiKit.modal_box(self, 440.0, 0.0)
	_talk_overlay = box["overlay"]
	_talk_overlay.name = "ContractTalks"
	var v: VBoxContainer = box["body"]
	var talk_name := _para(GameDB.player_display_name(p), 20, UiKit.TEXT)
	talk_name.name = "TalkPlayerName"
	v.add_child(NameLink.tappable(talk_name, str(p["id"])))
	v.add_child(_para("Age %d  ·  %d OVR  ·  %s POT  ·  on %s now" % [int(p.get("age", 0)), int(Rating.ovr(p)),
			str(GameState.pot_view(p)["text"]), Contracts.money(int(p.get("salary", 0)))], 13, UiKit.MUTED))
	# For a free agent his terms include what his options add.
	var meet_salary := int(want["salary"]) + int(terms.get("premium", 0))
	v.add_child(_para("He wants %s a season for %d seasons. %s" % [Contracts.money(meet_salary), int(want["years"]),
			Contracts.stance(p)], 15, UiKit.TEXT))
	if not _talk_fa:
		# How far he bends, with the sizes: his lowest, the price of a shorter
		# deal and where an offer insults him (Contracts.bend_line).
		var bend := _para(Contracts.bend_line(p, GameState.culture_effect(GameState.my_club, "resign_floor")), 13, UiKit.TEXT)
		bend.name = "TalksBend"
		v.add_child(bend)
	# Under 50 he may refuse you whatever you offer (director 2026-11-08); a
	# player you let go is asked the same.
	if not _talk_fa or str(p.get("released_by", "")) == GameState.my_club:
		var odds := _refuse_odds(p, 14)
		if odds != null:
			odds.name = "TalksRefuse"
			v.add_child(odds)
	var no_spot := RookieList.add_block(GameState.my_list, "senior") if _talk_fa else ""
	if no_spot == "senior":
		v.add_child(_para("Our senior list is full at %d. Release a player first." % RookieList.senior_spots(), 14, UiKit.BAD))
	elif no_spot != "":
		v.add_child(_para(RookieList.block_words(GameState.my_list, no_spot) + " Release a player first.", 14, UiKit.BAD))
	elif _talk_fa:
		# A spot he fills is one a draft pick needed: say which pick passes.
		var cost := GameState.signing_costs_pick_line()
		if cost != "":
			var pick_cost := _para(cost, 14, UiKit.BAD)
			pick_cost.name = "FaPickCost"
			v.add_child(pick_cost)
	for reason in terms.get("reasons", []):
		var why := _para(str(reason), 14, UiKit.BAD if bool(terms["refuse"]) else UiKit.TEXT)
		why.name = "FreeAgentReason"
		v.add_child(why)
	if _talk_fa:
		_offers_table(v)
	var reply := _talk_reply
	if reply == "" and talks.has("counter"):
		reply = "He'd sign for %s over %d season%s." % [Contracts.money(int(talks["counter"])), int(talks["years"]),
				"" if int(talks["years"]) == 1 else "s"]
	if reply != "":
		var r := _para(reply, 15, UiKit.TEXT)
		r.name = "TalksReply"
		v.add_child(r)
	var left := Contracts.MAX_OFFERS - int(talks.get("failed", 0))
	if talks.has("failed") and left == 1:
		v.add_child(_para("One more failed offer and he'll test free agency.", 13, UiKit.BAD))
	v.add_child(UiKit.lbl("Seasons", 14, UiKit.EMPH, true))
	var term_opts := []
	for y in range(1, Contracts.MAX_YEARS + 1):
		term_opts.append([str(y), str(y)])
	v.add_child(UiKit.choice_grid("Term", term_opts, str(_offer_years), 4, func(k: String):
		_offer_years = int(k)
		_show_talks()))
	v.add_child(UiKit.lbl("Salary a season", 14, UiKit.EMPH, true))
	var srow := UiKit.hbox(UiKit.GAP)
	v.add_child(srow)
	var less := UiKit.btn("−", UiKit.HEADING)
	less.name = "SalaryDown"
	less.custom_minimum_size = Vector2(56, 44)
	less.disabled = _offer_salary <= Contracts.senior_min()
	less.pressed.connect(func():
		_offer_salary = maxi(Contracts.senior_min(), _offer_salary - Contracts.salary_step())
		_show_talks())
	srow.add_child(less)
	var amount := UiKit.lbl(Contracts.money(_offer_salary), 20, UiKit.TEXT, true)
	amount.name = "SalaryOffer"
	amount.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	amount.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	srow.add_child(amount)
	var more := UiKit.btn("+", UiKit.HEADING)
	more.name = "SalaryUp"
	more.custom_minimum_size = Vector2(56, 44)
	more.pressed.connect(func():
		_offer_salary += Contracts.salary_step()
		_show_talks())
	srow.add_child(more)
	# Your own player's current salary is already on the books; a free
	# agent's is not.
	var on_books := 0 if _talk_fa else int(p.get("salary", 0))
	var room_after := GameState.cap_room() + on_books - _offer_salary
	var blocked := bool(terms.get("refuse", false)) or (_talk_fa and not RookieList.senior_spot_free(GameState.my_list))
	v.add_child(_para("Cap room after this deal: %s" % room_after_words(room_after), 14,
			UiKit.TEXT if room_after >= 0 else UiKit.BAD))
	if _talk_fa:
		var best_other := 0
		for row in GameState.fa_offers(_talk_id):
			if not bool(row["mine"]):
				best_other = maxi(best_other, int(row["worth"]))
		var fl := Contracts.fa_lines(_offer_salary, _offer_years,
				GameState.fa_offer_worth(_talk_id, _offer_salary, _offer_years), best_other)
		v.add_child(UiKit.stake_row(GateOdds.gain(str(fl[0])), "FaGain"))
		v.add_child(UiKit.stake_row(GateOdds.cost(str(fl[1])), "FaCost"))
	if not _talk_fa:
		var floor_price := Contracts.lowest(p, _offer_years) - GameState.culture_resign_discount(GameState.my_club, p, _offer_years)
		var hl := ListCosts.haggle_lines(_offer_salary, int(want["salary"]), floor_price, left)
		if not hl.is_empty():
			v.add_child(UiKit.stake_row(str(hl[0]), "HaggleGain"))
			v.add_child(UiKit.stake_row(str(hl[1]), "HaggleCost"))
	var final := _talk_fa and GameState.fa_market_stage(_talk_id) == "final"
	var offer := UiKit.btn("%s %s for %d season%s" % ["Final offer:" if final else "Offer", Contracts.money(_offer_salary), _offer_years,
			"" if _offer_years == 1 else "s"], 16, true)
	offer.name = "MakeOffer"
	offer.custom_minimum_size.y = 44
	offer.disabled = room_after < 0 or blocked
	offer.pressed.connect(_make_offer.bind(_offer_salary, _offer_years))
	box["footer"].add_child(offer)
	var meet := UiKit.btn("Meet his terms: %s for %d seasons" % [Contracts.money(meet_salary), int(want["years"])], 16)
	meet.name = "MeetTerms"
	meet.custom_minimum_size.y = 44
	meet.disabled = GameState.cap_room() + on_books < meet_salary or blocked
	meet.pressed.connect(_make_offer.bind(meet_salary, int(want["years"])))
	box["footer"].add_child(meet)
	var cancel := UiKit.btn("Cancel", UiKit.NAME)
	cancel.name = "CancelTalks"
	cancel.custom_minimum_size.y = 44
	cancel.pressed.connect(_close_talks)
	box["footer"].add_child(cancel)


## The offers on the table, his view of each, and where the talks stand.
## Four short columns that fit a phone: club, salary, years, his view.
func _offers_table(v: VBoxContainer) -> void:
	var rows := GameState.fa_offers(_talk_id)
	v.add_child(UiKit.lbl("Offers on the table", 14, UiKit.EMPH, true))
	if rows.is_empty():
		v.add_child(_para("No club has made an offer.", 13, UiKit.MUTED))
	else:
		var grid := GridContainer.new()
		grid.name = "OffersTable"
		grid.columns = 4
		grid.add_theme_constant_override("h_separation", UiKit.Space.ROOM)
		grid.add_theme_constant_override("v_separation", UiKit.Space.TIGHT)
		for h in ["Club", "Salary", "Years", "His view"]:
			grid.add_child(UiKit.line(h, 12, UiKit.MUTED))
		for row in rows:
			var who := "Us" if bool(row["mine"]) else GameDB.club_short(str(row["club"]))
			var club := UiKit.line(who, UiKit.SECONDARY, UiKit.TEXT, bool(row["leading"]))
			club.name = "Offer_" + str(row["club"])
			grid.add_child(club)
			grid.add_child(UiKit.line(Contracts.money(int(row["salary"])), 13, UiKit.TEXT, bool(row["leading"])))
			grid.add_child(UiKit.line(str(row["years"]), UiKit.SECONDARY, UiKit.TEXT, bool(row["leading"])))
			var view := _para(("Leading. " if bool(row["leading"]) else "") + str(row["view"])
					+ " Worth %s to him." % Contracts.money(int(row["worth"])), 12, UiKit.TEXT)
			view.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			view.custom_minimum_size.x = 120
			grid.add_child(view)
		v.add_child(grid)
	# How he weighs any offer, in dollars (row T1.R26 FA weights).
	var weigh := _para(Contracts.weigh_line(GameState.free_agent(_talk_id)), 12, UiKit.MUTED)
	weigh.name = "FaWeights"
	v.add_child(weigh)
	var log: Array = GameState.free_agent(_talk_id).get("market_log", [])
	if not log.is_empty():
		var said := _para("After our offer: " + " ".join(PackedStringArray(log)), 13, UiKit.TEXT)
		said.name = "RivalResponses"
		v.add_child(said)
	var stage := GameState.fa_market_stage(_talk_id)
	var note := "Rivals see our offer and can answer it once. Our second offer is final." if stage == "open" \
			else ("Our next offer is final. Rivals answer, then he decides." if stage == "final" else "")
	if note != "" and not rows.is_empty():
		v.add_child(_para(note + " Otherwise he decides when free agency closes.", 12, UiKit.MUTED))


func _make_offer(salary: int, years: int) -> void:
	var r := GameState.offer_free_agent(_talk_id, salary, years) if _talk_fa \
			else GameState.offer_contract(_talk_id, salary, years)
	if str(r.get("answer", "")) == "table":
		_talk_reply = str(r["reason"])
		# Your offer stands; the stepper starts from it for any final offer.
		_offer_salary = salary
		_offer_years = years
		_show_talks()
		return
	if str(r.get("answer", "")) == "counter":
		_talk_reply = str(r["reason"])
		_offer_salary = int(r["salary"])
		_offer_years = years
		_show_talks()
		return
	_close_talks()
	_notice = str(r["reason"])
	_notice_club = str(r.get("club", ""))
	_notice_club_text = _notice if r.has("code") else ""
	_build()


## "His opinion of you: 44 out of 100. 6% he won't re-sign with us." when his
## opinion of you is under 50, else null.
func _refuse_odds(p: Dictionary, size: int) -> Control:
	var chance := GameState.resign_refuse_chance(p)
	if chance <= 0:
		return null
	return _para(Contracts.REFUSE_ODDS % [GameState.opinion_of_you(str(p.get("id", ""))), chance, GameDB.player_display_name(p)], size, UiKit.BAD)


func _close_talks() -> void:
	if is_instance_valid(_talk_overlay):
		_talk_overlay.queue_free()
	_talk_overlay = null


func _agents(body: VBoxContainer) -> void:
	var fas := GameState.free_agents.duplicate()
	var controls := UiKit.hbox(UiKit.Space.TIGHT)
	controls.name = "FreeAgentSort"
	for entry in [["value", "Value"], ["overall", "OVR"], ["potential", "POT"], ["age", "Age"]]:
		var key := str(entry[0])
		var label := str(entry[1])
		if key == _fa_sort:
			label += " ↓" if _fa_sort_desc else " ↑"
		var sort_btn := UiKit.tab(label, key == _fa_sort)
		sort_btn.name = "AgentSort_" + key
		sort_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		sort_btn.pressed.connect(func():
			if _fa_sort == key:
				_fa_sort_desc = not _fa_sort_desc
			else:
				_fa_sort = key
				_fa_sort_desc = true
			_build())
		controls.add_child(sort_btn)
	body.add_child(controls)
	var fam := _para(TeamFamiliarity.signing_line(), UiKit.SECONDARY, UiKit.TEXT)
	fam.name = "AgentsFamiliarity"
	body.add_child(fam)
	fas.sort_custom(func(a, b):
		var av: float
		var bv: float
		match _fa_sort:
			"overall":
				av = float(Rating.ovr(a, 0))
				bv = float(Rating.ovr(b, 0))
			"potential":
				av = float(GameState.pot_view(a)["mid"])
				bv = float(GameState.pot_view(b)["mid"])
			"age":
				av = float(a.get("age", 0))
				bv = float(b.get("age", 0))
			_:
				av = Contracts.worth(a)
				bv = Contracts.worth(b)
		if av == bv:
			return str(a.get("id", "")) < str(b.get("id", ""))
		return av > bv if _fa_sort_desc else av < bv)
	if fas.is_empty():
		body.add_child(_para("No free agents right now. Rivals let players go when the season ends.", 13, UiKit.MUTED))
	# Each card is built as it scrolls into view, not all 98 on every tap
	# (0.3 s, bug bash 2026-11-25; director, batch F): the list looks the same.
	_agent_body = body
	_agent_queue = fas
	_agent_built = 0
	_more_agents(_agents_shown)
	# Built straight onto a box (the trade screen's familiarity line, a test), the
	# tab has no scroll of its own to watch.
	if not is_instance_valid(_scroll_box):
		return
	var bar := _scroll_box.get_v_scroll_bar()
	bar.value_changed.connect(func(_v: float) -> void: _check_agents_end())
	bar.changed.connect(_check_agents_end)


## Cards built when the list opens, and added each time the scroll comes
## within a screen of the last one built.
const AGENT_BATCH := 10
## The most cards built so far: a rebuild (a sort, closing talks) builds as many
## again, so the list comes back at the same place.
var _agents_shown := AGENT_BATCH
var _agent_queue: Array = []
var _agent_built := 0
var _agent_body: VBoxContainer
var _agents_check_queued := false


## After a scroll or a layout: within a screen of the last card built, build the
## next few. Deferred, so cards are never added while the list lays itself out.
func _check_agents_end() -> void:
	if _agents_check_queued:
		return
	_agents_check_queued = true
	_agents_end.call_deferred()


func _agents_end() -> void:
	_agents_check_queued = false
	if _tab != "agents" or not is_instance_valid(_scroll_box) or not is_instance_valid(_agent_body) \
			or _agent_body.get_parent() != _scroll_box or _agent_built >= _agent_queue.size():
		return
	var bar := _scroll_box.get_v_scroll_bar()
	if bar.value + bar.page < bar.max_value - _scroll_box.size.y:
		return
	_more_agents(AGENT_BATCH)


## Builds the next `n` cards of the list, after the last one built.
func _more_agents(n: int) -> void:
	if not is_instance_valid(_agent_body):
		return
	var body := _agent_body
	var fas := _agent_queue.slice(_agent_built, mini(_agent_built + n, _agent_queue.size()))
	_agent_built += fas.size()
	_agents_shown = maxi(_agents_shown, _agent_built)
	for p in fas:
		var want := Contracts.wants(p)
		var card := _player_card(p, "%d OVR  ·  %s POT  ·  age %d  ·  wants %s for %d seasons  ·  from %s" % [
				int(Rating.ovr(p)), str(GameState.pot_view(p)["text"]), int(p.get("age", 0)),
				Contracts.money(int(want["salary"])), int(want["years"]),
				GameDB.club_short(str(p.get("released_by", "")))])
		PlayerSheet.synergy_fit_block(card.get_child(0) as VBoxContainer, p, 12)
		var offers := GameState.fa_offers(str(p["id"]))
		if not offers.is_empty():
			var bits := PackedStringArray()
			for o in offers.slice(0, 3):
				bits.append("%s %s for %d" % ["us" if bool(o["mine"]) else GameDB.club_short(str(o["club"])), Contracts.money(int(o["salary"])), int(o["years"])])
			var line := "Offers: " + ", ".join(bits) + (" and %d more" % (offers.size() - 3) if offers.size() > 3 else "")
			(card.get_child(0) as VBoxContainer).add_child(_para(line + ".", 12, UiKit.TEXT))
		var row := UiKit.hbox(UiKit.Space.TIGHT)
		row.name = "Agent_" + str(p["id"])
		_action_slot(card).add_child(row)
		var talks: Dictionary = p.get("talks", {})
		var barred := Challenge.block_reason(GameState, p)
		if bool(talks.get("walked", false)):
			row.add_child(UiKit.line("Talks broke down. He'll look elsewhere", UiKit.SECONDARY, UiKit.BAD, true))
		elif barred != "":
			# Your challenge bars him: said before any talks, not after.
			(card.get_child(0) as VBoxContainer).add_child(_para(barred, 12, UiKit.MUTED))
			var shut := UiKit.btn(Challenge.short_tag(GameState, p), UiKit.SECONDARY)
			shut.name = "FreeAgentBarred"
			shut.custom_minimum_size = Vector2(0, 44)
			shut.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			shut.disabled = true
			_compact_actions(row, shut)
			row.add_child(shut)
		else:
			if talks.has("counter"):
				(card.get_child(0) as VBoxContainer).add_child(_para("He'd sign for %s over %d season%s." % [
						Contracts.money(int(talks["counter"])), int(talks["years"]), "" if int(talks["years"]) == 1 else "s"], 12, UiKit.TEXT))
			var talk := UiKit.btn("Talk contract", UiKit.SECONDARY)
			talk.name = "FreeAgentTalks"
			talk.custom_minimum_size = Vector2(0, 44)
			talk.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			_compact_actions(row, talk)
			talk.pressed.connect(_open_talks.bind(str(p["id"]), true))
			row.add_child(talk)
		body.add_child(card)


## The trade builder, one screen for a phone: who you're trading with, what
## you give and get (tap Remove to take something out), their answer and
## Make trade; then one list at a time - theirs or yours, picks first - to
## add from. Nothing here shows a value: their answer is in words.
func _trade(body: VBoxContainer) -> void:
	if _choosing_club:
		_trade_club_sheet(body)
		return
	_offers(body)
	_requests(body)
	var who := UiKit.hbox(UiKit.GAP)
	who.add_child(UiKit.ellipsis("Trading with %s" % GameDB.club_name(_trade_club), UiKit.NAME, UiKit.TEXT, true))
	who.get_child(0).size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var change := UiKit.btn("Change club", 14)
	change.name = "TradeClub"
	change.custom_minimum_size = Vector2(0, 44)
	change.pressed.connect(func():
		_choosing_club = true
		_build())
	who.add_child(change)
	body.add_child(who)
	var outlook := GameState.team_outlook(_trade_club)
	var phase := str(outlook.get("phase", GameState.club_phase(_trade_club)))
	var rating := _para(str(outlook.get("line", "")), 14, UiKit.TEXT)
	rating.name = "TradeClubOutlook"
	body.add_child(rating)
	var stance := {"rebuilding": "They guard young talent and want players for the future.",
			"building": "They weigh this season and the future evenly.",
			"contending": "They want players who help them win now."}
	var cycle := _para(str(stance.get(phase, "")), 13, UiKit.MUTED)
	cycle.name = "TradeClubPhase"
	body.add_child(cycle)
	body.add_child(UiKit.spacer(UiKit.Space.TIGHT))
	_package(body, "We give", _mine, GameState.my_club, "GiveRow_",
			"Nothing yet. Add from our list below.")
	_package(body, "We get", _theirs, _trade_club, "GetRow_",
			"Nothing yet. Add from their list below.")
	if not _theirs.is_empty():
		var fam := _para(TeamFamiliarity.signing_line(), UiKit.SECONDARY, UiKit.TEXT)
		fam.name = "TradeFamiliarity"
		body.add_child(fam)
	var verdict := GameState.evaluate_trade(_trade_club, _mine, _theirs)
	var empty := _mine.is_empty() or _theirs.is_empty()
	var shopping := _mine.size() == 1 and _theirs.is_empty()
	# One of theirs and nothing of yours yet: you can ask what they'd want (row 67).
	var buying := _theirs.size() == 1 and _mine.is_empty() and not GameState.draft_night_open()
	var prompt := "Add what we want back. Or put him on the trade table." if shopping else \
			("Add what we'd give. Or ask their price." if buying else "Put something on each side.")
	# Their answer in one line, with the reason their decision took (P-18);
	# the club's name wears its ink, and a refusal reads as text, not grey.
	var answer := _para(prompt, 14, UiKit.MUTED) if empty else \
			_why_para(str(verdict["reason"]), _trade_club, 14, UiKit.GOOD if bool(verdict["ok"]) else UiKit.TEXT)
	answer.name = "TradeVerdict"
	if not empty:
		answer.set_meta("code", str(verdict.get("code", "")))
	# Their price, when you asked it for the player still on the sheet.
	if str(_price.get("club", "")) == _trade_club and _theirs.size() == 1 and _theirs[0] == str(_price.get("id", "")):
		var said := _why_para(str(_price["line"]), _trade_club, 14, UiKit.TEXT)
		said.name = "TradePrice"
		body.add_child(said)
	body.add_child(answer)
	if not empty and not bool(verdict["ok"]):
		var counter := _counter_for(_trade_club, _mine, _theirs)
		if not counter.is_empty():
			var ask := _para(str(counter["say"]), 14, UiKit.TEXT)
			ask.name = "TradeCounter"
			body.add_child(ask)
			var apply := UiKit.btn("Make that change", 14)
			apply.name = "TradeCounterApply"
			apply.custom_minimum_size = Vector2(0, 44)
			apply.pressed.connect(func():
				_mine = (counter["mine"] as Array).duplicate()
				_theirs = (counter["theirs"] as Array).duplicate()
				_build())
			body.add_child(apply)
	var go := UiKit.btn("Make trade", UiKit.NAME, true)
	go.name = "MakeTrade"
	go.custom_minimum_size = Vector2(0, 48)
	go.disabled = not bool(verdict["ok"])
	go.pressed.connect(func():
		var r := GameState.make_trade(_trade_club, _mine, _theirs)
		_notice = str(r["reason"])
		if bool(r["ok"]):
			_mine = []
			_theirs = []
		_build())
	body.add_child(go)
	if buying:
		var price := UiKit.btn("Ask their price", UiKit.BODY)
		price.name = "AskPrice"
		price.custom_minimum_size = Vector2(0, 44)
		price.pressed.connect(func():
			var r := GameState.ask_price(_trade_club, str(_theirs[0]))
			_price = {"club": _trade_club, "id": str(_theirs[0]), "line": str(r["line"])}
			if bool(r["ok"]):
				_mine = (r["mine"] as Array).duplicate()
			_build())
		body.add_child(price)
	if shopping:
		var listed := GameState.trade_table.has(str(_mine[0]))
		var table := UiKit.btn("Already on the trade table" if listed else "Put on the trade table", UiKit.BODY)
		table.name = "TradeTable"
		table.custom_minimum_size = Vector2(0, 44)
		table.disabled = listed
		table.pressed.connect(func():
			var r := GameState.put_on_trade_table(str(_mine[0]))
			_notice = str(r["reason"])
			if bool(r["ok"]):
				_mine = []
				_scroll_positions["trade"] = 0
			_build())
		body.add_child(table)
		if not str(_mine[0]).begins_with("pick:"):
			var ask := UiKit.btn("Ask around", UiKit.BODY)
			ask.name = "AskAround"
			ask.custom_minimum_size = Vector2(0, 44)
			ask.pressed.connect(func():
				_asked_id = str(_mine[0])
				_asked = GameState.ask_around(_asked_id)
				_build())
			body.add_child(ask)
	_answers(body)
	body.add_child(UiKit.spacer(UiKit.SECTION - 6))
	var sides := UiKit.hbox(UiKit.Space.TIGHT)
	for t in [["theirs", "Their list"], ["mine", "Our list"]]:
		var tb := UiKit.tab(str(t[1]), _trade_side == str(t[0]))
		tb.name = "TradeSide_" + str(t[0])
		tb.pressed.connect(func():
			_trade_side = str(t[0])
			_build())
		sides.add_child(tb)
	body.add_child(sides)
	if _trade_side == "mine":
		_draft_picks(body, GameState.my_club, _mine, "Mine_")
		_pick_grid(body, GameState.my_list, _mine, "Mine_")
	else:
		_draft_picks(body, _trade_club, _theirs, "Their_")
		_pick_grid(body, GameState.season.lists.get(_trade_club, []), _theirs, "Their_")


## What every rival said when you asked around about one of your players
## (P-50): one line each, keen clubs first, and for a club that would deal a
## way into the usual trade sheet with its answer filled in.
func _answers(body: VBoxContainer) -> void:
	if _asked_id == "" or GameState.list_player(_asked_id).is_empty():
		_asked_id = ""
		_asked = []
		return
	var p := GameState.list_player(_asked_id)
	var box := UiKit.vbox(UiKit.Space.CLOSE)
	box.name = "AskAnswers"
	body.add_child(box)
	var head := NameInk.label("Asked around about %s" % GameDB.player_display_name(p), _names(), UiKit.BODY, UiKit.EMPH, true)
	head.name = "AskHead"
	box.add_child(head)
	for row in _asked:
		var club := str(row["club"])
		var keen := str(row["kind"]) != "no"
		var line := _why_para(str(row["line"]), club, 13, UiKit.TEXT)
		line.name = "Answer_" + club
		if not keen:
			box.add_child(line)
			continue
		var h := UiKit.hbox(UiKit.GAP)
		line.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(line)
		var go := UiKit.btn("Trade with them", 13)
		go.name = "AskTrade_" + club
		go.custom_minimum_size = Vector2(0, 44)
		go.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		go.pressed.connect(func():
			_trade_club = club
			_mine = (row["mine"] as Array).duplicate()
			_theirs = (row["theirs"] as Array).duplicate()
			_asked_id = ""
			_asked = []
			_scroll_positions["trade"] = 0
			_build())
		h.add_child(go)
		box.add_child(h)


## Offers rival clubs have put to you: what they'd give and want, in words,
## with Accept and No thanks.
func _offers(body: VBoxContainer) -> void:
	var open := GameState.open_trade_offers()
	if open.is_empty():
		return
	body.add_child(UiKit.lbl("Offers for our players", UiKit.BODY, UiKit.EMPH, true))
	for i in open:
		var text := _para(GameState.trade_offer_text(i), 14, UiKit.TEXT)
		text.name = "Offer_%d" % i
		body.add_child(text)
		var row := UiKit.hbox(UiKit.GAP)
		var buttons := [["Accept", "OfferAccept_%d" % i, true]]
		# A story's offer can't be turned down: none taken, the best goes
		# through when trades close (LegacyRollover, director 2026-11-25).
		if str((GameState.trade_offers[i] as Dictionary).get("canon", "")) == "":
			buttons.append(["No thanks", "OfferDecline_%d" % i, false])
		for b in buttons:
			var btn := UiKit.btn(str(b[0]), 14)
			btn.name = str(b[1])
			btn.custom_minimum_size = Vector2(0, 44)
			btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			var accept: bool = b[2]
			btn.pressed.connect(func():
				if accept:
					_notice = str(GameState.accept_trade_offer(i)["reason"])
					_prune_trade()
				else:
					GameState.decline_trade_offer(i)
				_build())
			row.add_child(btn)
		body.add_child(row)
	body.add_child(UiKit.spacer(UiKit.SECTION - 6))


## Players who have asked to be traded that concern you: yours, and those
## elsewhere who named your club - one line each, and for theirs a way to
## start the trade.
func _requests(body: VBoxContainer) -> void:
	var ids := GameState.my_trade_requests()
	if ids.is_empty():
		return
	body.add_child(UiKit.lbl("Asked to be traded", 15, UiKit.EMPH, true))
	for id in ids:
		var club := str(GameState.trade_requests[id]["club"])
		var row := UiKit.hbox(UiKit.GAP)
		row.name = "Request_" + str(id)
		var text := _para(GameState.trade_request_line(str(id)), 14, UiKit.TEXT)
		text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(text)
		if club != GameState.my_club:
			var go := UiKit.btn("Trade for him", 13)
			go.name = "RequestTrade"
			go.custom_minimum_size = Vector2(0, 44)
			go.pressed.connect(func():
				_trade_club = club
				_theirs = [str(id)]
				_mine = []
				_trade_side = "mine"
				_build())
			row.add_child(go)
		body.add_child(row)
	body.add_child(UiKit.spacer(UiKit.SECTION - 6))


## The counter for this offer, worked out once per offer (it tries every
## one of your players and picks).
func _counter_for(club: String, mine: Array, theirs: Array) -> Dictionary:
	var key := "%s|%s|%s|%d" % [club, ",".join(mine), ",".join(theirs), GameState.my_list.size()]
	if key != _counter_key:
		_counter_key = key
		_counter = GameState.trade_counter(club, mine, theirs)
	return _counter


## One side of the trade: each player or pick on its own line with Remove.
func _package(body: VBoxContainer, title: String, ids: Array, club: String, prefix: String, none: String) -> void:
	body.add_child(UiKit.lbl(title, UiKit.BODY, UiKit.EMPH, true))
	if ids.is_empty():
		body.add_child(_para(none, 13, UiKit.MUTED))
		return
	for id in ids.duplicate():
		var row := UiKit.hbox(UiKit.GAP)
		row.name = prefix + str(id).replace(":", "_")
		# A player wears his club's ink, as in the Ask around answers (row 174:
		# "sanders uncoloured?"); a pick stays plain.
		var ink := UiKit.TEXT if str(id).begins_with("pick:") else NameInk.player_ink(club)
		var what := UiKit.ellipsis(_asset_line(str(id), club), 14, ink)
		what.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(what)
		var rm := UiKit.btn("Remove", UiKit.SECONDARY)
		rm.name = "Remove"
		rm.custom_minimum_size = Vector2(88, 44)
		rm.pressed.connect(func():
			ids.erase(id)
			_build())
		row.add_child(rm)
		body.add_child(row)


## Drop from the trade builder anyone (or any pick) that has since left the
## club offering it - released, or moved in an accepted trade - so no stale
## row blocks the next trade.
func _prune_trade() -> void:
	_mine = _mine.filter(func(id): return str(GameState._trade_assets([id], GameState.my_club)["code"]) == "")
	var club := _trade_club
	_theirs = _theirs.filter(func(id): return club != "" and str(GameState._trade_assets([id], club)["code"]) == "")


## A player or pick in a trade, in a line: "Name, MID 72" or the pick.
func _asset_line(id: String, club: String) -> String:
	if id.begins_with("pick:"):
		var pk := GameState.pick_asset(id)
		return _pick_label(pk) if not pk.is_empty() else "-"
	for p in GameState.season.lists.get(club, []):
		if str(p["id"]) == id:
			return "%s, %s %d" % [GameDB.player_display_name(p), Ratings.role_tag(p), int(Rating.ovr(p))]
	return "-"


## Every other club, two to a row; Back or a choice closes it.
func _trade_club_sheet(body: VBoxContainer) -> void:
	body.add_child(UiKit.lbl("Trade with", UiKit.BODY, UiKit.EMPH, true))
	var options := []
	for code in GameDB.active_clubs(GameState.season_year):
		if code != GameState.my_club:
			options.append([code, "%s · %s" % [GameDB.club_name(code),
					TeamRating.category(GameState.club_phase(code))]])
	body.add_child(UiKit.choice_grid("TradeClubChoice", options, _trade_club, 2, func(code: String):
		if code != _trade_club:
			_theirs = []
		_trade_club = code
		_choosing_club = false
		_build()))


## A club's tradeable draft picks, earliest first: "2027 first round, No. 3"
## (next year's has no number yet), and the club it came from if it was
## traded in.
func _draft_picks(body: VBoxContainer, code: String, chosen: Array, prefix: String) -> void:
	var picks := GameState.club_picks(code)
	if picks.is_empty():
		return
	body.add_child(UiKit.lbl("Draft picks", 14, UiKit.MUTED, true))
	for pk in picks:
		var id := str(pk["id"])
		var b := _asset_button(_pick_label(pk, false), chosen.has(id))
		b.name = prefix + id.replace(":", "_")
		b.pressed.connect(_toggle.bind(chosen, id))
		body.add_child(b)
		# How the club got it: its own, or from whom and for what.
		var story := _para(GameState.pick_story(int(pk["year"]), int(pk["round"]), str(pk["origin"])),
				12, UiKit.TEXT)
		story.name = "PickStory_" + id.replace(":", "_")
		body.add_child(story)


## A list to add players from, best first: name, position, age, OVR and POT.
func _pick_grid(body: VBoxContainer, list: Array, chosen: Array, prefix: String) -> void:
	body.add_child(UiKit.lbl("Players", 14, UiKit.MUTED, true))
	var sorted := list.duplicate()
	sorted.sort_custom(func(a, b):
		if int(Rating.ovr(a)) != int(Rating.ovr(b)):
			return int(Rating.ovr(a)) > int(Rating.ovr(b))
		return str(a["id"]) < str(b["id"]))
	for p in sorted:
		var id := str(p["id"])
		# Their players your challenge bars from coming to you: the tag sits
		# by his name, where a trimmed row still shows it, and he can't be added.
		var tag := Challenge.short_tag(GameState, p) if prefix == "Their_" else ""
		# Who he is on the first line (Untouchable by his name, then his position);
		# on a phone his age and ratings go on a second line, so a long position
		# never cuts them off.
		var head := "%s%s%s  ·  %s" % [GameDB.player_display_name(p), "  ·  " + tag if tag != "" else "",
				"  ·  Untouchable" if GameState.is_untouchable(id) else "", Ratings.role_tag(p)]
		var facts := "Age %d  ·  %d OVR  ·  %s POT" % [int(p.get("age", 0)), int(Rating.ovr(p)),
				str(GameState.pot_view(p)["text"])]
		var b := _asset_button(head + ("  ·  " if _wide() else "\n") + facts, chosen.has(id))
		b.name = prefix + id
		b.disabled = tag != "" and not chosen.has(id)
		b.pressed.connect(func():
			if not NameLink.on_profile_tap(b):
				_toggle(chosen, id))
		NameLink.profile_tap_text(b, id)
		body.add_child(b)


func _asset_button(text: String, on: bool) -> Button:
	var b := UiKit.btn(text, 14)
	b.custom_minimum_size = Vector2(0, 44)
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.clip_text = true
	b.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	UiKit.set_selected(b, on)
	return b


## Add or take out one player or pick; a side holds at most GameState.TRADE_MAX.
func _toggle(chosen: Array, id: String) -> void:
	if chosen.has(id):
		chosen.erase(id)
	elif chosen.size() < GameState.TRADE_MAX:
		chosen.append(id)
	_build()


func _pick_label(pk: Dictionary, with_via := true) -> String:
	var nth: String = ["first", "second", "third", "fourth"][clampi(int(pk["round"]) - 1, 0, 3)]
	var text := "%d %s round" % [int(pk["year"]), nth]
	if int(pk["year"]) == GameState.season_year:
		text += ", No. %d" % int(pk["positions"][0][0])
	if with_via and str(pk["origin"]) != str(pk["owner"]):
		text += " (via %s)" % GameDB.club_name(str(pk["origin"]))
	return text


## A PC: actions sit together at the right of a row, sized to their words,
## not as bars across the screen (director, 2026-10-10).
func _wide() -> bool:
	var w := UiKit.view_width(self)
	return ScreenLayout.roomy(w, UiKit.view_height(self))


func _compact_actions(row: HBoxContainer, main: Button) -> void:
	if not _wide():
		return
	row.alignment = BoxContainer.ALIGNMENT_END
	main.size_flags_horizontal = Control.SIZE_SHRINK_END
	main.custom_minimum_size.x = 200


func _player_card(p: Dictionary, detail: String) -> PanelContainer:
	# An editorial row, not a tile (guide §3): no surface, a rule under it.
	var card := UiKit.panel(UiKit.PANEL_ALT, UiKit.GAP, 6)
	var quiet := UiKit.style(Color.TRANSPARENT, UiKit.GAP, 0)
	quiet.set_border_width_all(0)
	quiet.border_width_bottom = 1
	quiet.border_color = UiKit.LINE
	quiet.content_margin_top = UiKit.Space.ROOM
	quiet.content_margin_bottom = UiKit.Space.ROOM
	card.add_theme_stylebox_override("panel", quiet)
	var v := UiKit.vbox(UiKit.Space.THIN)
	card.add_child(v)
	# A PC: who he is on the left, the actions on the same line at the right.
	var info := v
	if _wide():
		var top := UiKit.hbox(UiKit.Space.PAD)
		v.add_child(top)
		info = UiKit.vbox(UiKit.Space.THIN)
		info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		top.add_child(info)
		var slot := UiKit.hbox(UiKit.Space.TIGHT)
		slot.name = "Actions"
		slot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		top.add_child(slot)
		card.set_meta("actions", slot)
	var h := UiKit.hbox(UiKit.Space.CLOSE)
	info.add_child(h)
	# One width for every role so the names line up down the list.
	var chip := UiKit.role_chip(Ratings.role_tag(p))
	chip.custom_minimum_size.x = 72
	h.add_child(chip)
	var who := UiKit.ellipsis(GameDB.player_display_name(p), UiKit.BODY, UiKit.TEXT, true)
	who.name = "PlayerName_" + str(p["id"])
	h.add_child(NameLink.tappable(who, str(p["id"])))
	info.add_child(_para(detail, 12, UiKit.MUTED))
	# His top three rated attributes, as every card shows them (row 150).
	info.add_child(PlayerSheet.top_three(p, UiKit.FINE, true))
	return card


## Where a card's actions go: beside him on a PC, under him on a phone.
func _action_slot(card: PanelContainer) -> Container:
	if card.has_meta("actions"):
		return card.get_meta("actions")
	return card.get_child(0) as VBoxContainer


## Every club's players by name from the season's lists (they follow trades), so
## a name in a sentence wears his club's colour (NameInk); made again on each build.
func _names() -> Dictionary:
	if _name_index.is_empty() and GameState.season != null:
		_name_index = NameInk.from_lists(GameState.season.lists)
	return _name_index


## A line naming a rival club: the club's name in its ink, players' names in
## theirs (NameInk).
func _why_para(text: String, club: String, size: int, colour: Color) -> Control:
	var index: Dictionary = _names().duplicate()
	if club != "":
		index[GameDB.club_name(club)] = club
	var l := NameInk.label(text, index, size, colour)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


## The cap room in the off-season heading. Over the cap says so in words, not
## in BAD alone: money() never goes below $0k.
static func cap_room_words(room: int) -> String:
	if room >= 0:
		return "cap room %s" % Contracts.money(room)
	return "over the cap by %s" % Contracts.money(-room)


## What an offer leaves under the cap, in words: "none, $120k over the cap".
static func room_after_words(room_after: int) -> String:
	if room_after >= 0:
		return Contracts.money(room_after)
	return "none, %s over the cap" % Contracts.money(-room_after)


func _para(text: String, size: int, colour: Color) -> Control:
	var l := NameInk.label(text, _names(), size, colour)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


# -- A PC (UI batch 5, director's board A): Contracts is the list of players to
# decide on, and the picked one's card beside it; the whole list is its own tab.
# Nothing scrolls: both fill the room under the tabs.

## A short PC window (960 x 540): its controls stay a finger's 44 units. A
## full one draws a unit as 1.5 px, so 36 units is 54 px.
func _short_pc() -> bool:
	return UiKit.view_height(self) < 640.0


func _tap_h() -> int:
	return 44 if _short_pc() else 36


## The height under the tabs. Until the first layout measures it, the top bar,
## the heading and the tabs are taken as 221 units (1920 x 1080).
func _room_now() -> float:
	return _room if _room > 0.0 else UiKit.view_height(self) - 221.0


## The room is known only once laid out, and the heading grows after a signing,
## a notice or an undo: when it differs from the room built for, build again.
func _fit_room(sc: ScrollContainer, used: float) -> void:
	sc.resized.connect(func():
		if sc.size.y > 0.0 and absf(sc.size.y - used) > 1.0:
			_room = sc.size.y
			_build.call_deferred())


## Who Contracts decides on: retiring first, then out of contract.
func _to_decide() -> Array:
	var out: Array = []
	for r in GameState.retiring_players():
		out.append({"p": r["p"], "retire": r})
	for p in Contracts.expiring(GameState.my_list).filter(func(q): return not GameState.retiring_now(q)):
		out.append({"p": p, "retire": {}})
	return out


## Where he stands, in a few words for his row in the list.
func _status(e: Dictionary) -> Array:
	var p: Dictionary = e["p"]
	var r: Dictionary = e["retire"]
	if not r.is_empty():
		var talk: Dictionary = r["talk"]
		if not talk.is_empty() and bool(talk["stays"]):
			return ["Going around again", UiKit.GOOD]
		return ["Retiring", UiKit.MUTED]
	if bool(p.get("resigned", false)):
		return ["Re-signed", UiKit.GOOD]
	var talks: Dictionary = p.get("talks", {})
	if bool(talks.get("walked", false)):
		return ["Talks broke down", UiKit.BAD]
	var want := Contracts.wants(p)
	var years := int(want["years"])
	return ["wants %s for %d %s" % [Contracts.money(int(want["salary"])), years, "season" if years == 1 else "seasons"],
			UiKit.TEXT]


func _contracts_pc(body: VBoxContainer) -> void:
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_compensation_lines(body)
	var all := _to_decide()
	if all.is_empty():
		body.add_child(_para("Nobody is out of contract this year.", UiKit.SMALL, UiKit.MUTED))
		return
	var ids := all.map(func(e): return str(e["p"]["id"]))
	# The first man still to sign, unless the coach picked someone.
	if not ids.has(_pick_id):
		_pick_id = str(all[0]["p"]["id"])
		for e in all:
			if (e["retire"] as Dictionary).is_empty() and not bool(e["p"].get("resigned", false)):
				_pick_id = str(e["p"]["id"])
				break
	var split := UiKit.hbox(UiKit.Space.COLUMN)
	split.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(split)
	# As many rows to a column as the room holds; one column has room for more.
	var row_h := 44 if _short_pc() else 40
	var per_col := maxi(1, int(floor((_room_now() + UiKit.Space.SLIM) / float(row_h + UiKit.Space.SLIM))))
	var cols := int(ceil(float(all.size()) / float(per_col)))
	var rich := cols == 1
	var list := UiKit.hbox(UiKit.Space.PAD)
	list.name = "DecideList"
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	split.add_child(list)
	for c in cols:
		var col := UiKit.vbox(UiKit.Space.SLIM)
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		list.add_child(col)
		for i in range(c * per_col, mini(all.size(), (c + 1) * per_col)):
			col.add_child(_decide_row(all[i], rich, row_h))
	var pane := UiKit.panel(UiKit.PANEL, UiKit.Space.LOOSE, 0)
	pane.name = "DecideCard"
	pane.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pane.size_flags_stretch_ratio = 1.1 if rich else 1.0
	split.add_child(pane)
	var pv := UiKit.vbox(UiKit.Space.CLOSE)
	pane.add_child(pv)
	for e in all:
		if str(e["p"]["id"]) != _pick_id:
			continue
		var p: Dictionary = e["p"]
		var retiring := not (e["retire"] as Dictionary).is_empty()
		var head := _name_row(p, 20)
		pv.add_child(head)
		# A short window can't hold the whole card: Contract and Ratings take turns beside his name.
		var ratings := _short_pc() and _card_stage == "ratings"
		if _short_pc():
			head.add_child(UiKit.segmented("CardStage", [["contract", "Contract"], ["ratings", "Ratings"]], _card_stage,
					func(k):
						_card_stage = str(k)
						_build()))
		pv.add_child(_para(_retiring_detail(p) if retiring else _contract_detail(p), UiKit.SMALL, UiKit.MUTED))
		if ratings:
			var w := PlayerSheet.with_us_block(p)
			if w != null:
				pv.add_child(UiKit.spacer(UiKit.Space.PAD))
				pv.add_child(w)
			_ratings_grid(pv, p)
			continue
		pv.add_child(PlayerSheet.top_three(p, UiKit.SECONDARY, _short_pc()))
		var acts := _decide_parts(e, pv)
		pv.add_child(UiKit.spacer(UiKit.Space.TIGHT))
		pv.add_child(acts)
		_decide_more(pv, p, _short_pc())
		var fill := Control.new()
		fill.size_flags_vertical = Control.SIZE_EXPAND_FILL
		pv.add_child(fill)
		if not retiring and GameState.offseason_open():
			pv.add_child(_unsigned_rule(UiKit.SMALL))


## The picked man's lines under his facts (an answer, the odds, the gain and the
## cost) into `info`, and his actions, sized to their words, into the row it returns.
func _decide_parts(e: Dictionary, info: VBoxContainer) -> HBoxContainer:
	var row := UiKit.hbox(UiKit.Space.TIGHT)
	var p: Dictionary = e["p"]
	var r: Dictionary = e["retire"]
	if r.is_empty():
		row.name = "Contract_" + str(p["id"])
		_contract_parts(p, row, info, UiKit.SMALL, _tap_h())
		return row
	row.name = "Retiring_" + str(p["id"])
	var talk: Dictionary = r["talk"]
	if not talk.is_empty():
		var said := _para(str(talk["reason"]), UiKit.SMALL, UiKit.GOOD if bool(talk["stays"]) else UiKit.TEXT)
		said.name = "RetireAnswer"
		info.add_child(said)
	elif bool(r["can_ask"]):
		_ask_stakes(p, info)
		var ask := UiKit.btn("Ask him to go around again", UiKit.SECONDARY)
		ask.name = "TalkRound"
		ask.custom_minimum_size = Vector2(0, _tap_h())
		ask.pressed.connect(func():
			GameState.talk_round(str(p["id"]))
			_build())
		row.add_child(ask)
	elif p.has("talked_round"):
		info.add_child(_para("He went around again once already. This time he's going.", UiKit.SMALL, UiKit.MUTED))
	return row


func _name_row(p: Dictionary, size: int) -> HBoxContainer:
	var h := UiKit.hbox(UiKit.Space.CLOSE)
	var chip := UiKit.role_chip(Ratings.role_tag(p))
	chip.custom_minimum_size.x = UiKit.ROLE_COL
	h.add_child(chip)
	var who := UiKit.ellipsis(GameDB.player_display_name(p), size, UiKit.TEXT, true)
	who.name = "PlayerName_" + str(p["id"])
	h.add_child(NameLink.tappable(who, str(p["id"])))
	return h


## The card also says where he is headed: how he is developing and his match
## ratings this season; on a full PC, his time with us and every rating, as the
## player sheet lists them (a short one shows those on its Ratings stage).
func _decide_more(pv: VBoxContainer, p: Dictionary, short: bool) -> void:
	pv.add_child(UiKit.spacer(UiKit.Space.TIGHT if short else UiKit.Space.PAD))
	var dev := _para(GameState.development_state(p), UiKit.SECONDARY if short else UiKit.BODY, UiKit.TEXT)
	dev.name = "DecideDevelopment"
	pv.add_child(dev)
	var form := ReservesForm.profile_lines(GameState.form_log, GameState.reserves_log, str(p.get("id", "")))
	if not form.is_empty():
		var fl := _para("Match ratings. " + " ".join(form), UiKit.FINE if short else UiKit.SECONDARY, UiKit.TEXT)
		fl.name = "DecideForm"
		pv.add_child(fl)
	if short:
		return
	var w := PlayerSheet.with_us_block(p)
	if w != null:
		pv.add_child(UiKit.spacer(UiKit.Space.TIGHT))
		pv.add_child(w)
	_ratings_grid(pv, p)


## Every rating, three across, each number right beside its attribute.
func _ratings_grid(pv: VBoxContainer, p: Dictionary) -> void:
	var attr: Dictionary = p.get("attr", {}) if p.get("attr") is Dictionary else {}
	if attr.is_empty():
		return
	pv.add_child(UiKit.spacer(UiKit.Space.PAD))
	pv.add_child(UiKit.section("Ratings"))
	var grid := GridContainer.new()
	grid.name = "DecideRatings"
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", UiKit.Space.SPREAD)
	grid.add_theme_constant_override("v_separation", 0)
	pv.add_child(grid)
	var unknown: Array = p.get("attr_unrecorded", [])
	var rows: Array = PlayerSheet.ATTR_ROWS.duplicate()
	rows.append(["leadership", "Leadership"])
	for r in rows:
		var v := float(Leadership.of(p)) if r[0] == "leadership" else \
				(-1.0 if unknown.has(r[0]) else float(attr.get(r[0], 0.0)))
		var cell := UiKit.hbox(UiKit.Space.SNUG)
		cell.name = "Rating_" + str(r[0])
		cell.add_child(UiKit.line(str(r[1]), UiKit.SMALL, UiKit.TEXT))
		cell.add_child(UiKit.line("—" if v < 0.0 else str(int(round(v))), UiKit.SMALL, UiKit.MUTED))
		grid.add_child(cell)


## One man in the list: a tap shows his card. In one column the row has room
## for his role and facts; in two, his name over where he stands.
func _decide_row(e: Dictionary, rich: bool, row_h: int) -> Button:
	var p: Dictionary = e["p"]
	var on := str(p["id"]) == _pick_id
	var b := Button.new()
	b.name = "Decide_" + str(p["id"])
	b.custom_minimum_size = Vector2(0, row_h)
	b.focus_mode = Control.FOCUS_ALL
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(UiKit.TEXT, 0.09) if on else Color.TRANSPARENT
	sb.border_color = UiKit.TEXT if on else UiKit.LINE
	sb.border_width_left = 3 if on else 0
	sb.border_width_bottom = 0 if on else 1
	for state in ["normal", "pressed", "hover_pressed"]:
		b.add_theme_stylebox_override(state, sb)
	var hv := sb.duplicate() as StyleBoxFlat
	if not on:
		hv.bg_color = Color(UiKit.TEXT, 0.05)
	b.add_theme_stylebox_override("hover", hv)
	b.add_theme_stylebox_override("focus", UiKit.focus_ring())
	b.pressed.connect(func():
		_pick_id = str(p["id"])
		_build())
	var m := MarginContainer.new()
	m.set_anchors_preset(Control.PRESET_FULL_RECT)
	m.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for side in ["left", "right"]:
		m.add_theme_constant_override("margin_" + side, UiKit.Space.ROOM)
	b.add_child(m)
	var h := UiKit.hbox(UiKit.Space.PAD)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	m.add_child(h)
	var st := _status(e)
	if rich:
		var chip := UiKit.role_chip(Ratings.role_tag(p))
		chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		h.add_child(chip)
		var who := UiKit.ellipsis(GameDB.player_display_name(p), UiKit.BODY, UiKit.TEXT, true)
		who.mouse_filter = Control.MOUSE_FILTER_IGNORE
		who.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		# Sized to his name, so his figure sits beside it, not across the row.
		who.size_flags_horizontal = Control.SIZE_FILL
		var font := who.get_theme_font("font")
		who.custom_minimum_size.x = minf(260.0, font.get_string_size(who.text, HORIZONTAL_ALIGNMENT_LEFT, -1, who.get_theme_font_size("font_size")).x + 2.0)
		h.add_child(who)
		var facts := UiKit.line("%d OVR  ·  age %d" % [int(Rating.ovr(p)), int(p.get("age", 0))], UiKit.SMALL, UiKit.MUTED)
		facts.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(facts)
		var room := Control.new()
		room.mouse_filter = Control.MOUSE_FILTER_IGNORE
		room.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(room)
		var s := UiKit.line(str(st[0]), UiKit.SMALL, st[1], true)
		s.custom_minimum_size.x = 170
		s.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		s.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(s)
	else:
		var v := UiKit.vbox(0)
		v.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		v.alignment = BoxContainer.ALIGNMENT_CENTER
		h.add_child(v)
		var who := UiKit.ellipsis(GameDB.player_display_name(p), UiKit.BODY, UiKit.TEXT, true)
		who.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(who)
		var s := UiKit.ellipsis(str(st[0]), UiKit.SMALL, st[1], false)
		s.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(s)
	return b


# -- Our list, a stage of its own on a PC: a table in three columns, by salary,
# its rows spread to the height so it neither scrolls nor ends half way down.
func _whole_list(body: VBoxContainer) -> void:
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var sorted := GameState.my_list.duplicate()
	sorted.sort_custom(func(a, b): return int(a.get("salary", 0)) > int(b.get("salary", 0)))
	var cols := 3
	var per := int(ceil(float(sorted.size()) / float(cols)))
	var short := _short_pc()
	var fs := UiKit.FINE if short else UiKit.BODY
	var head_h := 22.0 if short else 30.0
	var avail := _room_now() - head_h - UiKit.Space.TIGHT
	var row_h := clampf(floor(avail / float(maxi(1, per))), 20.0, 44.0)
	var h := UiKit.hbox(UiKit.Space.COLUMN if short else UiKit.Space.APART)
	h.name = "WholeList"
	body.add_child(h)
	for c in cols:
		var col := UiKit.vbox(0)
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(col)
		col.add_child(_list_row(["Player", "OVR", "Pay", "Contract"], fs, head_h, "", short))
		for i in range(c * per, mini(sorted.size(), (c + 1) * per)):
			var p: Dictionary = sorted[i]
			# The season just played still counts in contract_years until the
			# rollover (Re-signed says years - 1 too).
			var left := int(p.get("contract_years", 1)) - 1
			var term := "out of contract" if left <= 0 else "%d season%s left" % [left, "" if left == 1 else "s"]
			col.add_child(_list_row([GameDB.player_display_name(p), str(int(Rating.ovr(p))),
					Contracts.money(int(p.get("salary", 0))), term], fs, row_h, str(p["id"]), short))


## One row of Our list (or its heading when `id` is empty): his name, rating,
## pay and what is left of his contract, each in its own column.
func _list_row(cells: Array, fs: int, row_h: float, id: String, short: bool) -> Control:
	var head := id == ""
	var row := PanelContainer.new()
	row.custom_minimum_size.y = row_h
	var sb := UiKit.line_row(false)
	sb.content_margin_left = 0
	sb.content_margin_right = 0
	row.add_theme_stylebox_override("panel", sb)
	var h := UiKit.hbox(UiKit.GAP)
	row.add_child(h)
	var ink := UiKit.MUTED if head else UiKit.TEXT
	var size := UiKit.FINE if head else fs
	var who := UiKit.ellipsis(str(cells[0]), size, ink, not head)
	who.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	who.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	if head:
		h.add_child(who)
	else:
		who.name = "ListName_" + id
		var tap := NameLink.tappable(who, id)
		tap.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(tap)
	var widths := [28, 44, 92] if short else [40, 64, 130]
	for k in range(1, 4):
		var l := UiKit.line(str(cells[k]), size, ink)
		l.custom_minimum_size.x = widths[k - 1]
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT if k < 3 else HORIZONTAL_ALIGNMENT_LEFT
		h.add_child(l)
	return row
