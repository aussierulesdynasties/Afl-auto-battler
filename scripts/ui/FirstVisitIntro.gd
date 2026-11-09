class_name FirstVisitIntro
extends RefCounted
## First-visit intros for the main screens that had none (plan step 3b,
## register row 27): the Season stats intro's sheet, word for word in look -
## a title, two or three plain lines from the coach's side, and "Got it".
## Opens once per device (the first postseason's: once per career), only while
## this career's tips are on (GameState.intro_due); seen the moment it opens.

const TEXT := {
	"draft": ["The draft", [
		"This is where you pick the kids who will carry your club in five years.",
		"When your pick comes up, choose a player from the pool.",
	]],
	"combine": ["The Combine", [
		"Four tests on the day, and every club sees the same results.",
		"They tell you about the athlete: speed, running, spring, kicking. They don't tell you he can play.",
		"His junior numbers and your scouts' guess at OVR and POT are on his sheet. Tap a name to weigh it up.",
	]],
	"selection": ["Picking the side", [
		"Your match-day 23 for this week. Until you move someone, the best side is picked for you.",
		"Move players on and off the field to set the team you want.",
	]],
	"coaching": ["How we play", [
		"Your game plan: how your side plays every week, set against what your list is good at.",
		"Pick the plan that suits the players you have. You can change it before any match.",
	]],
	"list": ["Your list", [
		"Every player on your list: who he is, whether he is fit, and how good he is.",
		"Tap a player to see his profile, his contract and how he is developing.",
	]],
	"staff": ["Your staff", [
		"You are the senior coach. These are the five people who work for you.",
		"Tap a coach to see what he is good at.",
	]],
	"offseason": ["The off-season", [
		"Between the Grand Final and the draft you rebuild: contracts, free agents and trades.",
		"Sort out the players you want to keep first, then fill the gaps.",
	]],
	"preseason": ["The pre-season", [
		"The weeks before Round 1: get the squad fit and try your ideas out.",
		"Work through each stop in order, then start the season.",
	]],
	"season_review": ["Season review", [
		"How your season went: who won the flag, how your list went, and the final ladder.",
		"Read it, then move on to the off-season and start building for next year.",
	]],
	"postseason": ["After the finals", [
		"First the Season review: awards night, then how your year went.",
		"Then Trades & Contracts: re-sign players, chase free agents, do deals. It all stays open until you start the draft.",
		"After the National Draft comes the pre-season, then Round 1.",
	]],
}


const GROUP := "first_visit_intro"


## Back closes an open intro first, like the four older intros. True if one closed.
static func close_open(host: Node) -> bool:
	if not is_instance_valid(host):
		return false
	for n in host.get_children():
		if n.is_in_group(GROUP) and not n.is_queued_for_deletion():
			n.queue_free()
			return true
	return false


## Opens the intro for key over host if it is due. Returns the sheet, or null.
static func show_if_due(host: Control, key: String) -> Control:
	if not is_instance_valid(host) or not host.is_inside_tree() or not TEXT.has(key) \
			or not GameState.intro_due(key):
		return null
	return show(host, key)


static func show(host: Control, key: String) -> Control:
	var title: String = TEXT[key][0]
	var lines: Array = TEXT[key][1]
	var box := UiKit.modal_box(host, 520.0, 0.0)
	var overlay: Control = box["overlay"]
	var node := "".join(Array(key.split("_")).map(func(s: String) -> String: return s.capitalize()))
	overlay.name = node + "Intro"
	overlay.add_to_group(GROUP)
	UiKit.close_on_outside_tap(box)
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.heading(title, UiKit.TITLE))
	for line in lines:
		var l := UiKit.lbl(line, 14, UiKit.TEXT)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(l)
	GameState.mark_intro_seen(key)
	var ok := UiKit.btn("Got it", UiKit.NAME, true)
	ok.name = node + "IntroOk"
	ok.custom_minimum_size = Vector2(0, 48)
	ok.pressed.connect(func():
		if is_instance_valid(overlay):
			overlay.queue_free())
	(box["footer"] as VBoxContainer).add_child(ok)
	return overlay
