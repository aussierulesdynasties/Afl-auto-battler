# Coach arc catalogue (plan step 1a), 2026-11-03

A draft for the director. Keep, change or cut each arc before anyone builds the arc engine.
The story is the coach's career. Arcs sit beside the random deck. They do not replace it.

## What the card system can already do

- **Arcs exist, but only short ones.** A choice sets a flag (`op: flag`) on a player or on the club, stamped with
  the week. A follow-up card names the flag and a window (`needs: {flag, after, within}`). Beats are `start`, middle
  and `end`. An arc that nobody returns to lapses. The arcs in the deck today: `contract_wait`, `captain_slump`,
  `captain_contract`, `captain_succession`, `papers` and `backed_kid`. Each one lasts about one season at most
  (windows are counted in weeks, 30 to a season).
- **Conditions (`when` / `where`)**: `_min`, `_max`, `_every`, equality, `flag`, `no_flag`. Club facts include board,
  trust, ladder, round, phase, winning_run, losing_run, finals_week, finals_math, premiers, gf_run, gf_again,
  lost_last_final, rival, opp, captain/vice, has_kid/kid_name and the papers (pred_rank, words_behind, writer).
  Player facts include age, overall, potential, form, games, contract_years, injured_weeks, morale, trust, role,
  selected, new_here, debut_year, last_season, milestone_next and real_named.
- **Effects (`op`)**: morale, trust, board, xp, rest, fresh, heavy_legs, sore, rush_back, slow_start, running, drill,
  culture, promise_win, expects_game, start_backing, back_kid, role_trial, captaincy_swap, extend_early, open_price,
  new_club_go / new_club_keep, on_record, talk_note, delegate, news, loss_sting and flag.
- **Sim facts outside the deck**: board confidence, warned, poor_seasons and sacked (`ClubLife.season_end`), plus
  the board goal and its history. Also the honour roll (one entry per season), rivalry_history, trade_requests,
  rival offers in the off-season, CoachMarket (AI coaches are sacked, hired, promoted and retire), CoachPathway
  (retired players become coaches) and retirements.

## The arcs

For each arc: its trigger, its beats (a choice, then what that choice changes), its endings, what it remembers and
which deck cards it can reuse.

### 1. The hot seat
- **Trigger**: board `warned` is true at season end, or board confidence is under 40 by round 8.
- **Beats**
  1. Pre-season. The chairman sets the line. *Accept the target* (board +5, goal fixed) or *Argue for a lower one*
     (board -5, goal one rung easier).
  2. Round 6, after 3 or more losses in a row. *Change the game plan* (role_trial on two players, side morale -2)
     or *Hold the line* (side trust +3, board -4).
  3. Mid-season. A board member leaks to the press. *Go public* (board -6, sets the media-villain flag, side
     morale +3) or *Say nothing* (board -2).
  4. Round 18, the must-win game. promise_win. A win gives board +10. A loss gives board -10.
- **Endings**: he survives (warned is cleared, and a "survivor" flag gives board +5 next year). He is sacked (the
  career moves on to arc 2 or 7). He resigns first (no sacking on his record, and the board history says "resigned").
- **Remembers**: the chairman (who needs a name), the board member who leaked and the must-win opponent.
- **Reuses**: `board_wants_answers`, `board_president_lunch`.

### 2. The sack and the way back
- **Trigger**: `board.sacked` is true. Today the career ends at this point.
- **Beats**
  1. The phone call. *Go quietly* (reputation kept) or *Speak to the media* (reputation down, the rivalry with the
     old club goes up).
  2. A season out. Pick one: assistant at a top club (one coach skill up), a media job (reputation up) or rest.
  3. Offers come from CoachMarket vacancies. *Take the first one* or *Wait for a better club* (he may get none).
  4. The first match against the club that sacked him.
- **Endings**: back as a senior coach at a new club. Back as an assistant. Career over (the honour roll records it).
- **Remembers**: the club that sacked him, the chairman and the players he left behind.
- **Reuses**: none. Everything here is new, and it is the most expensive arc on this list for the engine (the coach
  must be able to change clubs).

### 3. Poached
- **Trigger**: his team finishes top 4 twice, or wins a flag, and a rival club's senior job opens in CoachMarket.
- **Beats**
  1. A rival president calls in September. *Listen* (board -5 if it leaks) or *Hang up* (board +5, sets the "loyal"
     flag).
  2. The offer, with a bigger list budget. *Use it to get a new contract here* (board -8, contract +2 years),
     *Take the job* (he moves clubs) or *Say no*.
  3. The players hear about it, and the captain asks him straight. *Tell the truth* (captain trust +4, side morale -3)
     or *Deny it* (on_record: if he leaves, every player he coaches later knows he broke his word).
- **Endings**: he stays as the loyal coach. He stays with a better contract and a cooler board. He leaves, the old
  club becomes a rival, and arc 7 can start.
- **Remembers**: the rival club and its president, and the captain who asked.
- **Reuses**: the wording of the `contracts_*` cards for the contract talk, and `on_record`.

### 4. Board feud
- **Trigger**: the coach refuses two board asks in one season (this needs a counter), or board confidence and team
  trust are 30 or more points apart.
- **Beats**
  1. The board cuts the football budget. *Accept* (training drills are limited) or *Fight* (board -8, sets the
     "feud" flag).
  2. The board wants a say in selection (a sponsor's favourite player). *Pick him* (side morale -3, board +6) or
     *Refuse*.
  3. A board election. *Back the challenger* (if he wins, board resets to 60 and is loyal; if he loses, board -15)
     or *Stay out of it*.
- **Endings**: peace. He wins over the board. He loses, and arc 1 starts.
- **Remembers**: the president, the challenger and the sponsor's player.
- **Reuses**: `board_sponsor_shoot`, `board_billboards`.

### 5. The protege
- **Trigger**: the coach backs a kid aged 18-20 with potential 80+ (`back_kid` or `start_backing` sets the flag).
- **Beats** (across 3-6 seasons)
  1. Year 1, the timing of his debut. *Throw him in* (xp up, risk of soreness) or *Hold him back* (his morale -2).
  2. Year 2. Rival clubs ask about him in the trade period. *Untouchable* (open_price off) or *Listen*.
  3. Year 3, the leadership group. *Put him in* (his trust +5, older players' morale -2) or *Not yet*.
  4. Year 4 or later, the captaincy. *Hand it to him* (captaincy_swap) or *Keep the old captain*.
  5. His contract. He names the coach as the reason he stays. If the coach was sacked or has left, the kid may
     follow him (arc 2 or 3).
- **Endings**: he goes from rookie to captain under this coach. He leaves for a rival (a reunion comes later). He
  busts, and the media remember the hype (arc 10).
- **Remembers**: the player, the season the coach backed him and the rival that asked about him.
- **Reuses**: the whole `backed_kid` arc and `captain_succession_*`.

### 6. One year too long
- **Trigger**: a player aged 31+ with `last_season` true (Retirement.intends) and 150+ games.
- **Beats**
  1. At the rollover. *Talk him round for one more year* or *Let him go* (with a farewell game).
  2. Mid-season, his form is low. *Keep picking him* (his morale +3, side morale -2) or *Drop him* (his trust -8,
     culture -1).
  3. He asks for a farewell game. *Give it to him* (he is selected next week) or *Say no*.
  4. After he retires he may become a coach (CoachPathway). He becomes the coach's assistant, or his enemy.
- **Endings**: a send-off. A sour exit, and he goes on to coach a rival. The coach was right, and the veteran has one
  last good year.
- **Remembers**: the veteran, his games and goals, and whether the coach dropped him.
- **Reuses**: `captain_slump_*` and the dropped-player cards in `selection.json`.

### 7. The old-club reunion
- **Trigger**: arc 2 or 3 has ended with the coach at a new club, and the fixture is against his old club.
- **Beats**
  1. The week before, the papers call it a grudge match. *Play it down* or *Bite* (media flag, side morale +4,
     board -2).
  2. A former player of his plays for the other side. *Tag him* or *Ignore him*.
  3. The handshake after the game. The words he chooses go in the news.
- **Endings**: a win that is remembered at every later meeting. A loss the old club enjoys. A later reconciliation
  (the old club asks him back).
- **Remembers**: the old club, its chairman and the players he coached there.
- **Reuses**: the week cards in `rivals.json` (they already read `rival` and `opp`).

### 8. The drought
- **Trigger**: 5 seasons in the job without a flag, or a club drought of 10+ years counted from the honour roll.
- **Beats**
  1. Pre-season. The president says "flag or bust". *Accept* (the board goal becomes the flag) or *Ask for time*.
  2. Trade period. *Go all in* (trade picks for a star who is ready now, so later seasons are weaker) or *Build*.
  3. Finals. One card a week, with the stakes rising (reuses the finals cards).
  4. Grand Final week.
- **Endings**: the drought is broken (a big legacy gain and a line in the almanac). Another miss (board -10). Each
  failure makes the drought one year longer.
- **Remembers**: the count of years, the last flag and the Grand Final opponents.
- **Reuses**: the finals deck (`finals_week`, `gf_run`, `gf_again`, `lost_last_final`).

### 9. The star who wants out
- **Trigger**: a top-3 player with contract_years 1 and morale under 50, or a trade request.
- **Beats**
  1. His manager calls. *Meet him* (talk_note) or *Deal through the manager only*.
  2. *Give him a bigger role* (role_trial), *Make him captain* or *Shop him* (open_price).
  3. Trade period. Let him go to the rival that wants him, or keep him on a one-year deal.
- **Endings**: he stays and is loyal (his morale can't drop as low again). He leaves, and the coach faces him twice a
  year. He stays and sulks.
- **Remembers**: the player, the rival club and what the coach promised.
- **Reuses**: `contract_wait`, `captain_contract_*`, `new_club_go` / `new_club_keep`.

### 10. Media darling or villain
- **Trigger**: the `papers` arc ends with the coach on record, or he makes 3 public statements in one season.
- **Beats**
  1. He is offered a weekly radio spot. *Take it* (board +3, risk of a heavy week) or *Say no*.
  2. A journalist names a player as the problem. *Defend him* (his trust +5, worse with the media) or *Agree*
     (his trust -8).
  3. A Mad Monday story leaks. *Front it* or *Blame the players*.
- **Endings**: darling (the board likes him, the players think he is distracted). Villain (board down, the players
  close ranks, morale up). Quiet.
- **Remembers**: the journalist (the `writer` fact exists already) and the player who was named.
- **Reuses**: `media_in_the_papers`, `media_papers_fronts_group`, `on_record`.

### 11. The assistant who wants his job
- **Trigger**: an assistant coach with a high reputation (CoachMarket) while board confidence is under 50.
- **Beats**
  1. The assistant is seen at lunch with the president. *Confront him* or *Give him more to do* (delegate).
  2. The assistant is offered a senior job elsewhere. *Back him* (he leaves, and the staff has a gap) or *Block it*.
  3. If the coach is sacked, the assistant gets his job.
- **Endings**: the assistant leaves on good terms (a friend at a rival club). He takes the coach's job. He stays loyal.
- **Remembers**: the assistant and the club he goes to.
- **Reuses**: the `delegate` effects.

### 12. The rivalry he made
- **Trigger**: rivalry_history between his club and another rises past a line (finals meetings, close games).
- **Beats**
  1. The other coach says something in the press. *Answer him* or *Ignore him*.
  2. A trade between the two clubs. *Deal with them* or *Never*.
  3. A final against them.
- **Endings**: a rivalry the almanac names. A truce.
- **Remembers**: the rival club and its coach by name, and every final between them.
- **Reuses**: `rivals.json`.

### 13. Family club
- **Trigger**: the son or brother (FamilyTies) of a player he coached is eligible for the draft.
- **Beats**
  1. *Use the father-son pick* (it costs a pick) or *Let him go to the draft*.
  2. His debut, with his father in the stands.
  3. He plays against the coach for another club, or wins a flag with him.
- **Endings**: a family dynasty under one coach. The one that got away.
- **Remembers**: the father, the son and the pick.
- **Reuses**: `family.json`.

### 14. Legacy
- **Trigger**: 10 seasons coached, 250 games or 2 flags.
- **Beats**
  1. His milestone game. The club asks how to mark it. *Make it about the players* or *Accept the honour*.
  2. *Choose a successor* from his assistants or former players (CoachPathway).
  3. *Retire on top* or *Coach one more year* (arc 6, for the coach himself).
- **Endings**: he retires a legend (an almanac entry and a statue line). He goes a year too long. He leaves with his
  successor ready.
- **Remembers**: every flag, the protege, the successor and the clubs he coached.
- **Reuses**: the milestone banners.

## What the engine needs that does not exist yet

1. **Arc state across seasons.** Windows are counted in weeks and close after about a season. Arcs need beats tied
   to points in the season (pre-season, trade period, rollover, round N), and they must live for up to 10 seasons.
2. **Off-season beats.** Cards come only in the regular season and the finals today. The trade period, the rollover
   and the draft need card slots.
3. **Named people who are not players.** The chairman, the president, a board challenger, rival coaches,
   assistants and journalists. CoachMarket has coaches, but there is no named board and no named press.
4. **A coach record for the player.** Reputation, seasons, games, flags, clubs coached and sackings. CoachMarket
   keeps this for AI coaches, but not for the player's coach.
5. **Changing clubs.** The career ends at the sack today. Arcs 2, 3 and 7 need the coach to leave, join another club
   and carry on in the same save.
6. **Arc facts in conditions.** `meets` reads only facts and flags. It needs: the state of another arc (arc 7 needs
   arc 2 or 3 done), a counter per arc (refusals, statements), seasons since an event, and facts from the honour
   roll (seasons without a flag).
7. **New effects.** Change the board goal, cut the budget, give the coach a contract, trade a pick, use a father-son
   pick, an assistant leaves, the coach changes club, reputation up or down, write an almanac entry.
8. **Arc priority against the deck.** Today a due beat comes first and one card a week is normal. With several arcs
   open, the week needs a cap (for example one arc beat plus one deck card).
9. **Text for remembered names.** Cards need tokens for names they remember: `{old_club}`, `{chairman}`,
   `{protege}`, `{rival_coach}`.
10. **Collisions to agree on.** The almanac branch (claude/club-almanac) should own the legacy record, and arcs write
    to it. The match story branch (claude/match-hero-why) can feed arc beats (for example, the hero of the reunion game).
