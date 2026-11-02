"""One-off: add the finals cards' second slice (A3, A9, A14, A15, A16, B7, B8, B9) to
data/stories, behind the finals_cards_2 switch. Kept as the record of what was added;
running it again replaces the cards with these ids. Run from the repo root."""
import json

F = "finals_cards_2"


def m(d, who="all"):
	return {"op": "morale", "d": d, "who": who}


def cul(strand, d, why):
	return {"op": "culture", "strand": strand, "d": d, "why": why}


def card(id, cat, **kw):
	c = {"id": id, "category": cat, "feature": F, "subject": {"kind": "club"}}
	c.update(kw)
	return c


SEASON_END = {"phase": ["season_end"], "priority": True, "cooldown": 0, "weight": 1}

CARDS = {
	"members": [
		card("finals_drought_over", "members", phase=["finals"], bye=True, per_season=1, weight=3,
			when={"finals_week": 1, "years_since_final_min": 3},
			title=["Our first final since {last_final_year}"],
			text=["The queue for tickets runs round the block. The players can hear the supporters from the track."],
			choices=[
				{"key": "feel", "label": "Let the players feel it",
				 "effects": [m(6), cul("together", 2, "The players shared the first final in years with the supporters")],
				 "result": "The players walk the queue after training, signing whatever's handed to them."},
				# Board +1 swapped for Standards +1 (director, 2026-11-03).
				{"key": "outside", "label": "Keep the noise outside",
				 "effects": [{"op": "xp", "d": 3, "who": "all"},
							 cul("standards", 1, "You kept the first final in years a week like any other")],
				 "result": "Same drills, same meetings, same Thursday. The doors stay shut."},
			]),
		card("gf_premiers", "members", **SEASON_END, when={"result": "premier"},
			title=["Premiers"],
			text=["{margin_line} {history_line} {best_line}"],
			choices=[
				{"key": "celebrate", "label": "Celebrate it properly",
				 "effects": [m(10), cul("together", 2, "You let the premiership players celebrate it properly"),
							 {"op": "running", "d": -1}],
				 "result": "The celebrations run for a week."},
				# Board +3 swapped out (director, 2026-10-13).
				{"key": "again", "label": "One week, then go again",
				 "effects": [m(4), cul("ambition", 2, "One week of celebrations, then you set the next target")],
				 "result": "One week, then the talk turns to doing it again."},
			]),
	],
	"media": [
		card("finals_prelim_week", "media", phase=["finals"], when={"finals_week": 4},
			title=["One win from the Grand Final"],
			text=["Everyone outside the club wants to talk about the last Saturday in September. You need them thinking about this week."],
			choices=[
				# Board +2 swapped for Standards +2 (director, 2026-10-13 and 2026-11-03).
				{"key": "ban", "label": "No Grand Final talk at the club",
				 "effects": [cul("standards", 2, "You banned Grand Final talk in prelim week"), m(-2)],
				 "result": "Anyone who says the words buys the coffees. Nobody slips."},
				{"key": "dream", "label": "Let them dream a little",
				 "effects": [m(5), {"op": "slow_start", "who": "side", "chance": 20, "on": "week"}],
				 "result": "The players talk about the big day. Training has an edge to it."},
			]),
		card("finals_written_off", "media", phase=["finals"], when={"finals_week_max": 4, "underdog": True},
			title=["Most of the tips have {opp} winning"],
			text=["They finished above you, and the papers have noticed. The reporters want to know if you've read it."],
			choices=[
				{"key": "pin", "label": "Pin the tips up in the rooms", "effects": [m(5, "side")],
				 "result": "Every tip for {opp} goes on the noticeboard. The players read them twice."},
				# Board +2 swapped for Togetherness +2 (director, 2026-10-13 and 2026-11-03).
				{"key": "back", "label": "Back your players in the press",
				 "effects": [m(2, "side"), cul("together", 2, "You backed your players in the press before a final")],
				 "result": "\"We finished below them. We've beaten better sides.\" The players notice."},
			]),
		card("finals_one_week_short", "media", **SEASON_END, when={"result": "eliminated", "lost_prelim": True},
			title=["One week short"],
			text=["A preliminary final lost. The first question in the press conference: has this list gone as far as it can?"],
			choices=[
				{"key": "not_done", "label": "This group isn't done",
				 "effects": [m(4), cul("ambition", 2, "You told the press this group isn't done")],
				 "result": "\"We'll be back here, and we'll go one better.\""},
				# Board +3 removed (director, 2026-10-13).
				{"key": "nobody", "label": "Nobody's spot is safe",
				 "effects": [cul("standards", 2, "You told the press nobody's spot was safe after the prelim"), m(-5)],
				 "result": "\"We'll look hard at the list and at how we play. Nobody's spot is safe.\" The players read every word."},
			]),
	],
	"leadership": [
		card("finals_knocked_out", "leadership", **SEASON_END, when={"result": "eliminated", "lost_prelim": False},
			title=["Knocked out"],
			text=["Out in the {lost_final}. The rooms are silent, and the players are waiting for you."],
			choices=[
				{"key": "demands", "label": "Tell them what next year demands",
				 "effects": [cul("standards", 2, "You set the bar for next year in the rooms after the finals exit"), m(-3)],
				 "result": "Short and blunt: next year starts in November, and it starts harder."},
				# Morale +3 removed: Togetherness only (director, 2026-10-13).
				{"key": "thanks", "label": "Thank them for the year",
				 "effects": [cul("together", 2, "You thanked the players when the season ended")],
				 "result": "You go round the room, one by one. A few heads come up."},
			]),
		card("gf_runners_up", "leadership", **SEASON_END, when={"result": "runner_up"},
			title=["Runners-up"],
			text=["{margin_line} {history_line} {best_line} Nothing in football is quieter than the losing rooms."],
			choices=[
				{"key": "photo", "label": "Put the photo up in the gym",
				 "effects": [cul("ambition", 2, "The premiers' lap of honour went up in your gym"), m(-4)],
				 "result": "A photo of the other side's lap of honour goes up in the gym. Nobody can miss it."},
				# Morale +4 removed: Togetherness only (director, 2026-10-13).
				{"key": "let_go", "label": "Let it go: it was a big year",
				 "effects": [cul("together", 2, "You told the players to be proud of their year")],
				 "result": "You tell them to be proud of the year. Summer can start."},
			]),
	],
	"community": [
		card("gf_night_before", "community", phase=["finals"], when={"finals_week": 5}, weight=1, cooldown=60,
			title=["The night before"],
			text=["{forecast_line} Some of them won't sleep a wink."],
			choices=[
				{"key": "together", "label": "All together",
				 "effects": [m(4, "side"), cul("together", 2, "The players spent the night before the Grand Final together")],
				 "result": "One long table, a few quiet words from the captain, lights out by ten."},
				{"key": "families", "label": "With their families",
				 "effects": [{"op": "fresh", "who": "side"}],
				 "result": "Dinner at home and their own bed. Nobody's in a hurry to talk footy."},
			]),
	],
}

if __name__ == "__main__":
	for cat, cards in CARDS.items():
		path = "data/stories/%s.json" % cat
		with open(path, encoding="utf-8") as f:
			raw = f.read()
		deck = json.loads(raw)
		ids = {c["id"] for c in cards}
		deck = [c for c in deck if c.get("id") not in ids] + cards
		with open(path, "w", encoding="utf-8", newline="") as f:
			f.write(json.dumps(deck, indent="\t", ensure_ascii=False) + "\n")
		print(cat, len(cards))
