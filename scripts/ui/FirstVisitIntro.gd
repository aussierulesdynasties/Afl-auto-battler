class_name FirstVisitIntro
extends RefCounted
## First-visit intros for the main screens that had none (plan step 3b,
## register row 27): the Season stats intro's sheet, word for word in look -
## a title, two or three plain lines from the coach's side, and "Got it".
## Opens once per device (the first postseason's: once per career), only while
## this career's tips are on (GameState.intro_due); seen the moment it opens.

const TEXT := {
	"draft": ["The draft", [
		"Here we pick the kids who will carry our club in five years.",
		"When our pick comes up, choose a player from the pool.",
	]],
	"league_draft": ["The League redraft", [
		"Every club starts from nothing. Each drafts a list of 44 from the league's players.",
		"Each player we take costs his salary. Our list must fit under the cap. It must have at least two rucks.",
		"When our pick comes up, take a player from the pool. The position counts show where we're short.",
	]],
	"combine": ["The Combine", [
		"Four tests on the day. Every club sees the same results.",
		"They tell us about the athlete: speed, running, spring, kicking. They don't tell us he can play.",
		"His junior numbers are on his sheet, with our scouts' guess at OVR and POT. Tap a name to weigh him up.",
	]],
	"selection": ["Picking the side", [
		"Our match-day 23 for this week. Auto-pick names it until you move someone.",
		"Move players on and off the ground to set the side you want.",
	]],
	"coaching": ["How we play", [
		"Our game plan: how we play every week, set against what our list is good at.",
		"Each plan suits some lists more than others. We can change it before any match.",
	]],
	"list": ["Your list", [
		"Every player on your list: who he is, whether he is fit, and how good he is.",
		"Tap a player to see his profile, his contract and how he is developing.",
	]],
	"staff": ["Our staff", [
		"You are the senior coach. These are the five people who work for you.",
		"Tap a coach to see what he is good at.",
	]],
	"offseason": ["The off-season", [
		"Between the Grand Final and the draft, we rebuild the list. Contracts, free agents and trades all happen here.",
		"Keep the players we want first. Then fill the gaps.",
	]],
	"contracts": ["Contract talks", [
		"He names a salary and a term. Meet his terms and he signs on the spot.",
		"Offer less and he names his lowest. Three failed offers and he tests free agency.",
		"Offer under two-thirds of his lowest and he's insulted. It counts as two failed offers and costs morale.",
	]],
	"trade": ["Trading", [
		"Choose a club. Put players or picks on each side. A no comes with their reason.",
		"To buy, add one of theirs alone and Ask their price. To sell, Ask around or Put on the trade table.",
		"Contenders want help now. Rebuilders want youth and picks. Trading closes when the draft starts.",
	]],
	"draft_trade": ["Trading picks", [
		"Tonight only picks change hands, from this draft and the next two.",
		"When a club bids for our pick, its offer shows at the top. Accept it, or build a deal below.",
		"The draft waits while we deal. Tap Back to the draft when done.",
	]],
	"preseason": ["The pre-season", [
		"The weeks before Round 1. Get our squad fit and try our ideas out.",
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
