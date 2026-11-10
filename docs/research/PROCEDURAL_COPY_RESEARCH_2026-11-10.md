# Let the save write its own stories

_Research report, 2026-11-10. Answers the director's question: can scripts compose the story of a match, a season or a career from specific data points? Built from three research notes (codebase inventory at main 88ea5634, game narrative systems, NLG and automated sports journalism). Nothing was run: no Godot, no tests. Repo citations are `file:line` at 88ea5634._

## 1. Answer first

**Yes, and the game is already halfway there.** Aussie Rules Dynasties already turns data into sentences in a dozen places: MatchStory picks a hero, a turning point and reasons after every match; the almanac writes a 3-5 sentence "story of the season"; the coach-arc log reads like a coaching biography. What is missing is one layer that sits over all of them: a script that gathers the facts a story could use, scores which ones matter, plans the story, and writes it from hand-authored phrase banks. That is the same design that AP, NTB in Norway and United Robots use for real sports reports, and on the academic RotoWire benchmark it got the facts right 99% of the time against 72% for neural models ([Wiseman et al. 2017](https://ar5iv.labs.arxiv.org/html/1707.08052)). The recommendation is **templates plus salience scoring, written in GDScript, with no language model at runtime**. A model's only safe job is offline: drafting phrase variants that a person then chooses or rejects. The first slice should be **a player's career story**, the "risky pick wins the Brownlow" story from the bible, because every fact it needs already survives the save, keyed by player id. It can also be generated and tested from the premade histories without simulating new seasons.

## 2. What the game already has

**The takeaway: careers and seasons are well kept; matches lose almost everything once the round ends.** MatchSim produces about 1,100 events a match, each with score, momentum and actor, plus an "impact" ledger that splits the result into the coach's decisions, the players and luck (`scripts/sim/MatchSim.gd:156-163, 1278-1309, 4689-4735`). The save keeps a slim result (score, quarters and every goal and behind with minute and kicker), a box score for the current season only, and a fuller review copy of your most recent match (`scripts/state/CareerSave.gd:28-36, 314-364`). Season and career facts are durable and keyed by id. So any rich match story has to be written at full time and saved as text, which is what MatchStory already does. Season and career stories can be regenerated years later.

| Source | Data kept | Grain | What's thrown away, and would be needed |
| --- | --- | --- | --- |
| MatchSim feed and event log (`MatchSim.gd:3-10, 1278-1309`); MatchNotes feed_line, quarter_facts, calls_lines, turning_points, duel_story (`scripts/ui/match/MatchNotes.gd:1-7, 80-1705`) | Live only. Every event has quarter, minute, kind, player, score and momentum; also set-shot choice, intercept source and duel | Event | The whole log after the round (`CareerSave.gd:28-36`), and momentum on non-scoring events even in the review copy. You would need it for "the run of play turned when..." in any past match. |
| Impact ledger (`MatchSim.gd:156-163`) | Expected points per cause: moments, gameplan, loose, tag, pep, bursts, minder (the coach's causes); legs, traits, form (players and bounce) | Match | **Lost entirely**, not even in the last-match review (`CareerSave.gd:339-364`). It is the most story-relevant data dropped: "your tag on X was worth N points". |
| Slim result plus scoring log (`MatchSim.gd:4676-4686`; `CareerSave.gd:319-336`) | Score, goals, behinds, quarters, margin, venue, and every goal and behind as [quarter, minute, side, goal/behind, kicker, set shot] | Match, every match | Marks, tackles, injuries and coach calls. Enough for goal runs, comebacks and clutch kicks. |
| Box score (`CareerSave.gd:314-335`; `GS:1508-1517`) | Packed player stat lines | Match, current season | Wiped at rollover (`GS:2518-2522`) |
| Post-quarter and post-match: CoachReport (`scripts/sim/CoachReport.gd:1-8, 325-358`), Headlines (`scripts/core/Headlines.gd:1-36`), ComebackTelling (`scripts/core/ComebackTelling.gd:1-27, 107-258`) | Text is shown live; headline and comeback logic read break scores and the scoring log | Match | The half-time analysis is not stored |
| MatchStory (`scripts/sim/MatchStory.gd:1-17, 86-150, 289-313`) | Per match, your club only: hero, hero line, turning point, 1-3 reasons, headline, your best in a loss, comeback and final flags. Last 120 kept (`GS:233-239`) | Match | Records past 120 are trimmed, but first folded into the digest (below) |
| Match-story digest (`MatchStory.gd:359-398`; `GS:11865-11885`) | Per year, never trimmed: heroes with counts, best win, worst loss, best final win, close final loss, comebacks, close wins and losses | Season | Nothing a season story needs |
| Weekly story deck (`scripts/sim/StoryEngine.gd:1-29, 425-549`; 135 cards in `data/stories/*.json`) | Cooldowns, flags, arcs; choice and outcome only on the week's card | Event | **The choice and its result vanish after the week** unless they set a flag or a trust reason (`StoryEngine.gd:366-376, 463-500`) |
| Coach arcs (`scripts/sim/CoachArcs.gd:1-51`; `data/arcs/coach_arcs.json`; log lines `scripts/state/ClubArcs.gd:46, 151, 264, 451, 480`) | 14 arcs; coach record (seasons, games, flags, clubs, sackings); a 400-line log of every beat, answer and ending | Career | Nothing; this is already a career story at line grain |
| Almanac (`scripts/sim/Almanac.gd:1-27, 44-119, 365-432`) | One page per season: ladder spot, W-L-D, finals, awards with names written in, top goalkicker, records, legends, season hero, story of the season and its parts | Season | **`story_parts.arc` is designed but always empty**. Other clubs' ladder rows and the finals bracket are not kept. |
| Club histories and rivalries (`scripts/core/ClubHistory.gd:1-19`; `scripts/state/LeagueNews.gd:1-44`; `scripts/core/Rivalries.gd:43-110`) | Real pre-career flags; "first flag since", rivalry meetings and close finals | Season, career | Rivalry events are capped and cool each season |
| Honour roll (`GS:6404-6455`; `scripts/sim/Awards.gd:315-392`) | Per season: premier, runner-up, Brownlow, Coleman, Rising Star, Norm Smith, your B&F, your record; award rows by player id with votes | Season | **Brownlow 2nd-10th** and the other full tables are overwritten yearly (`Awards.gd:364-373`) |
| Honour board (`scripts/sim/HonourBoard.gd:1-40`) | Every notable former player of your club: games, goals, B&F, flags, Brownlow, AA years, how he left | Career | Nothing for qualifiers; non-qualifiers keep no card |
| CareerFacts and CareerRecord, #1100 / row T5.r110 (`scripts/sim/CareerFacts.gd:1-48`; `scripts/sim/CareerRecord.gd:1-28`; `docs/TODO.md:95`) | Rows [year, match, kind, club, coach's decision, outcome] for injury, project and talk; outlive trades and retirement. CareerRecord writes debut, flags, milestones, awards. | Career | Only three decision kinds. The "coach's ledger" on the stats hub is still open in T5.r110. |
| Player career and firsts, highs, backing, honours (`scripts/sim/Career.gd:1-40`; `Firsts.gd:1-30`; `CareerHighs.gd:1-27`; `Backing.gd:6, 60-70`; `Almanac.gd:216-260`) | Totals, club stints, per-season stat lines, debut and first goal, career highs, coach promises and their outcome, honours | Career | **No per-season rating** (`p["history"]` is not appended, `GameDB.gd:1134-1200`), so "how far he came" can't be told from ratings |
| Draft fields (`GS:2300-2310, 2738-2752`; `scripts/sim/Prospects.gd:735-736, 909-910`) | drafted_year, type, pick, round, drafted_club; draft_rank for generated prospects | Career | **Overall at draft** is in the Draft's pick history, which is not saved (`scripts/sim/Draft.gd:585-600`) |
| Press (`scripts/sim/MediaConference.gd:1-65, 499-506`; `GS:11971-12090`) | Anti-repeat counts, claims that can be quoted back, each journalist's standing | Event | **No log of question, answer and result**; only standing and trust-log reasons survive |
| News and NewsFront (`GS:11363-11376`; `scripts/ui/NewsFront.gd`) | Text items, capped at 120 | Event | Prose only, and trimmed. Trades survive only as career stints (`GS:7033, 7278, 8054`). |
| Milestones (`scripts/sim/Milestones.gd:1-23, 105-145`) | Log of games, goals, first win, first final with value and text | Event, career | Nothing |
| Board history (`GS:12334`) | Per season: goal, met, position, confidence, verdict | Season | Nothing |

**The house style is already right for this.** Copy lives in pure static "rules and wording" classes using `%` format strings, or JSON `{token}` templates filled with `String.format` (`StoryEngine.gd:512-549`). Variation uses seeded RNG streams of the form `hash("story|seed|year|week")`, so a reload gives the same words (`StoryEngine.gd:152`). The game has no localisation: 0 `tr(` calls. Tests check that facts trace back to the data rather than comparing golden text (`tests/test_match_story.gd:110-233`). MatchStory already has a "said once" rule from the director's 2026-11-06 bug report (`MatchStory.gd:49-81`).

## 3. How others do it

**The takeaway: every system that players or editors trust picks facts first and writes second, from authored language. The ones that feel alive also remember what they said.**

**Football Manager** is the cautionary tale. Its press conference bank was about 500 questions by FM2010, with roughly 100 more added for FM2011 ([PC Gamer](https://www.pcgamer.com/miles-jacobson-on-football-manager-2011/3)). Players have still called press conferences and interviews repetitive for a decade ([WhatCulture 2013](https://whatculture.com/gaming/football-manager-2014-9-issues-it-really-should-fix?page=3); [Steam FM2024](https://steamcommunity.com/app/2252570/discussions/0/599650146629717899)). SI has published nothing primary on how FM writes its news. The inference is that a bigger bank alone doesn't fix repetition on a weekly surface; deciding what is worth saying, and how often, does.

**Out of the Park Baseball** has three layers. Box scores and the almanac are pure data. Routine news is algorithmic. Authored "storylines" are XML trees of linked articles with trigger conditions that can run for days or years, and since OOTP 13 some are interactive, with the user's choice affecting player and club ([OOTP newsletter](https://www.ootpdevelopments.com/newsletters/nl0094/)). The XML format is public; modders write more, and one fed it to ChatGPT to draft new ones ([OOTP forums](https://forums.ootpdevelopments.com/showthread.php?p=5178752)). A separate project writing recaps from a sim's event log summarises the log first and narrates second ([Deep Dugout](https://deep-dugout.pages.dev/about/front-office)). The game's coach arcs already match OOTP's storyline layer.

**Dwarf Fortress, Caves of Qud, RimWorld and Wildermyth** sit on a spectrum. Dwarf Fortress keeps every event (over 500,000 in a thousand-year world) and lets you browse them: accurate, but not a story ([Pickering](https://ryanpickering.gitbooks.io/honour-s-research-project-blog/content/updates/post6-jan-6.html)). Caves of Qud generates only 10-22 events per sultan, in a fixed shape: an origin, random core events, a guaranteed "becomes ruler" beat, and death. Each event has a plain version and a more flattering tomb inscription ([Qud wiki](https://wiki.cavesofqud.com/wiki/Sultan_history); [Grinblat & Bucklew 2017](https://pcgworkshop.com/archive/grinblat2017subverting.pdf)). RimWorld keeps a small, documented set of `{PAWN_nameDef}`-style symbols and handles articles and pronouns centrally ([RimWorld wiki](https://rimworldwiki.com/wiki/Modding_Tutorials/GrammarResolver)). Wildermyth's generated histories write queryable "aspects" that later authored scenes call back to ([Wildermyth Writer's Guide](https://www.wildermyth.com/wiki/Writer%27s_Guide)). Inference: Qud's shape fits an AFL career (debut, a few salient seasons, a guaranteed milestone, retirement), and Wildermyth's tags are how "the after-the-siren winner in 2027" becomes something a later Brownlow line can mention.

**Crusader Kings 3 and other Paradox games** keep text grammatical by putting grammar in engine getters (pronouns, possessives, name forms with case flags) and by choosing **whole alternative sentences** by condition (`first_valid` / `triggered_desc`) rather than splicing fragments. Numbers have format codes (sign, percent, ordinal) and positive/negative colouring ([CK3 wiki](https://ck3.paradoxwikis.com/Localization)). The notes did not verify Stellaris's equivalent; it is assumed to be the same family.

**Valve's dynamic dialogue and storylets** supply what grammars lack. Valve matches hundreds of world facts against thousands of lines, and the line with the most criteria satisfied wins, with broad lines as fallbacks ([GDC Vault, Ruskin 2012](https://gdcvault.com/play/1015317/AI-driven-Dynamic-Dialog-through); [Short 2012](https://emshort.blog/2012/03/16/gdc-2012-talk-on-dynamic-dialogue/)). Emily Short calls this salience-based narrative: start with broad defaults and add more specific lines over time at little risk. The cost is that the weights are set by trial and error ([Short 2016](https://emshort.blog/2016/04/12/beyond-branching-quality-based-and-salience-based-narrative-structures/)). Storylets are small, self-contained, recombinable units ([Short 2019](https://emshort.blog/2019/11/29/storylets-you-want-them/)). Tracery shows how far a pure replacement grammar goes on its own ([Compton et al. 2015](https://link.springer.com/10.1007/978-3-319-27036-4_14)).

**Newsrooms do the same thing at scale.** AP's Wordsmith went from about 300 to several thousand earnings stories a quarter ([journalism.co.uk](https://www.journalism.co.uk/how-ap-is-using-automation-to-increase-story-output-tenfold/)), and AP's editors configured it to cover about 10,000 minor league baseball games a year in AP style ([Poynter](https://www.poynter.org/tech-tools/2016/the-associated-press-will-use-automated-writing-to-cover-the-minor-leagues/)). During testing, journalists checked every report against its source before go-live ([bestpractice.ai](https://www.bestpractice.ai/ai-case-study-best-practice/the_associated_press_transforms_raw_earnings_data_into_publishable_stories_using_natural_language_generation)). NTB's football robot writes six to eight paragraphs in seconds from a live-score database plus a history database. Its one named pre-launch error credited an own-goal scorer as the match winner: a logic error, not a typo ([journalism.co.uk 2016](https://journalism.co.uk/news/norwegian-news-agency-is-betting-on-automation-for-football-coverage/s2/a647189)). United Robots lets the AI choose the angle, then fills the text from house-style language. It also texts coaches after the game and drops their replies in as quotes ([GXPress](https://www.gxpress.net/article/7572/robot-adds-coaches-comments-to-match-reports)). Narrative Science-style systems flag big swings in win probability and rank angles such as "back-and-forth" or "heroic individual performance" by a 1-10 importance score ([Diakopoulos ch.3](https://mtm.uni-koeln.de/veranstaltungen-sources/diakopoulos-19/diakopoulos-2019-automatingthenews-ch3-markiert-p.114.pdf)). In Australia, ACM's PlayHQ deal for local footy is a data feed, not a writer ([Mi-3](https://mi-3.com.au/02-04-2024/acm-play-hq-partner-boost-local-sports-coverage-regional-australians)).

**The academic picture agrees.** The standard pipeline runs content selection, then structure, then wording (aggregation, pronouns, word choice), then sentences ([Gatt & Krahmer 2018](https://arxiv.org/pdf/1703.09902)). The notes could not open Reiter & Dale's text directly, but this stage list is the standard one and matches Gatt & Krahmer. On RotoWire basketball, the template system's facts were 99.3% supported by the data against 71.8% for the best neural model. The neural text was more fluent, but weak at choosing and ordering facts ([Wiseman et al. 2017](https://ar5iv.labs.arxiv.org/html/1707.08052)). Thomson & Reiter hand-checked neural RotoWire stories and found about **20 errors per 300-word story**, mostly wrong numbers and names. A usable system needs well under one. The automatic checks caught only about a third of the number errors ([Thomson & Reiter 2020](https://ar5iv.labs.arxiv.org/html/2011.03992)). STREAK (1994) was the first report generator to place facts in history, such as streaks and records ([Robin](https://academiccommons.columbia.edu/doi/10.7916/D83203ZF)), and that historical context is what this game's stories most need.

### What makes copy feel alive, and what makes it read like a mail merge

| Mail-merge symptom | Fix |
| --- | --- |
| The same opening every week (FM press) | Memory: write back "said X in round N", weight used lines down, use variants in order ([Short 2016](https://emshort.blog/2016/04/12/beyond-branching-quality-based-and-salience-based-narrative-structures/)) |
| Filler when nothing happened | Salience includes frequency: say nothing when no angle scores high enough |
| Generic praise that could be about anyone | Most-specific-line-wins; specific lines must name the player, the quarter, the margin or the ground |
| Every fact listed (Dwarf Fortress, RotoWire templates' low precision) | Choose a few facts first, then write; cap the sentence count (the almanac already caps at 5) |
| Broken grammar ("1 goals", "the Fremantle") | Central getters for plurals, possessives and ordinals; whole alternative sentences rather than spliced fragments (CK3) |
| A wrong role or outcome (NTB's own goal) | Property tests on logic: the winner matches the score, "comeback" only when the trailing margin was big enough |
| No history ("third straight four-goal haul" is missing) | Read the season digest, records and career highs (STREAK) |
| Feels impersonal | Callbacks to the coach's own past choices and words (Wildermyth tags, United Robots' coach quotes) |

## 4. Ways to build it, simplest to richest

**The takeaway: the first two layers are cheap, fit the existing code, and give AP-grade reliability. Arcs and memory are where the feeling of a story comes from. A runtime language model costs more than it gives.**

**A. Template grammar with slots and conditions.** Each story type has sentence templates with `{slots}` and conditions. The first matching whole sentence wins, as in StoryEngine's `variant()` and CK3's `first_valid`. *Data:* whatever the save holds. *Authoring:* low; this is how MatchStory, Almanac and CareerRecord already work. *Tests:* seeded golden outputs, plus a fact-check that every number and name in the text appears in the fact record the sentence was built from. *Godot fit:* native. Use `String.format` on dictionaries, plus a tiny helper set (plural, possessive, ordinal, "A, B and C" via the existing `name_list`).

**B. Salience scoring.** First gather candidate facts ("angles"), each with a weight, then write only the top few. Candidate AFL angles, inferred from the sources rather than taken from any one of them: an upset against expectation, the biggest margin swing (comeback), lead changes in the last quarter, a blowout, records and milestones, streaks, a career best against the player's own average, ladder consequences (into or out of the eight), and **the risky pick paying off** (drafted_pick far below draft_rank, or a late pick, followed by an award). MatchStory's clutch-goal rule and stat-edge thresholds are already a small salience scorer (`MatchStory.gd:19-25, 86-150`). *Data:* candidate facts plus history (digest, records, highs). *Authoring:* medium; the weights need tuning by eye ([Short 2016](https://emshort.blog/2016/04/12/beyond-branching-quality-based-and-salience-based-narrative-structures/)). *Tests:* property tests over many seeds: no angle fires without its condition, no two angles contradict, and the top angle matches a hand-labelled expectation on a small fixed set. *Godot fit:* plain static functions returning `[{angle, weight, facts}]`.

**C. Story arcs across weeks and seasons.** A story is a planned shape, not a list: Qud's skeleton (origin, salient middle, guaranteed milestone, end) for a career, or set-up, turn, verdict for a season. The coach arcs already do this for the coach, and the almanac's `arc` slot is waiting for one sentence from them. *Data:* the arc log, CareerFacts and honours; already durable. *Authoring:* medium-high; each arc shape needs beats and endings. *Tests:* every arc that begins either ends or lapses with a logged reason, and an ending's sentence agrees with the facts (a "made it" ending needs games or an award). *Godot fit:* already proven by `CoachArcs.gd` and `ClubArcs.gd`.

**D. Variation pools and memory.** Each angle gets several phrasings, chosen by a seeded stream (`hash("tale|seed|year|week|angle")`). A memory store records which phrasings and callbacks have been used, so the game doesn't repeat itself and can say "again". *Data:* a small said-log in the save (a few bytes per story). *Authoring:* this is where the writing hours go; the notes found no study of how many variants per slot avoid felt repetition. *Tests:* repetition metrics over a simulated season (how often the same opening appears; distinct phrasing counts), as the press repeat audit already does (`docs/PRESS_REPEAT_EVIDENCE_2026-11-10.md:16-19`). *Godot fit:* native.

**E. On-device or offline language model, weighed honestly.** Gemma 3 1B (int4) is a 529 MB file. On a flagship Galaxy S24 Ultra it decodes at about 47 tokens a second on CPU, with about 1.1 GB peak memory, and Google recommends phones with more than 4 GB of RAM ([HF model card](https://huggingface.co/litert-community/Gemma3-1B-IT)). Older or mid-range phones run 1-2B models at about 3-16 tokens a second ([HF benchmark matrix](https://huggingface.co/datasets/dispatchAI/per-chip-benchmark-matrix); [Arm](https://learn.arm.com/learning-paths/mobile-graphics-and-gaming/voice-assistant/7-performance/)), so a paragraph takes many seconds. Godot's main route is NobodyWho, a llama.cpp GDExtension; its sources disagree on the minimum Godot version, Android runs through a Kotlin binding, and one source calls mobile use from Godot experimental ([NobodyWho docs](https://docs.nobodywho.ooo/)). Even with a pinned seed and greedy sampling, output can differ across threads, devices and versions ([llama.cpp issue](https://gh.r-mj.com/ggml-org/llama.cpp/issues/22956)), which breaks seeded tests. Worst of all, small models invent numbers and names: about 20 errors per story even in models trained for this task ([Thomson & Reiter 2020](https://ar5iv.labs.arxiv.org/html/2011.03992)). That is incompatible with a bible that wants outcomes told objectively. A "templates fix the facts, the model only rephrases" hybrid lowers the risk but doesn't remove it. It would need a post-check that every number and proper noun matches the input, plus a template fallback, and such checks miss changes of meaning. **The safe use is at build time**: a large model drafts many variants per angle offline, a person chooses which to keep, and they ship as static phrase banks with the same slots. That has no runtime cost, stays deterministic, and keeps "designed by a person" intact. Model licences (Gemma, Llama) were not verified in the notes; check them before any use.

| Layer | Data needs | Authoring effort | Test strategy | Godot fit |
| --- | --- | --- | --- | --- |
| A Templates | Existing save | Low | Golden text plus fact-check | Native, already used |
| B Salience | Plus history stores | Medium | Properties over many seeds | Native |
| C Arcs | Arc log, CareerFacts | Medium-high | Arc closure plus endings agree with facts | Proven in CoachArcs |
| D Variation and memory | Small said-log | High (the writing) | Repetition metrics | Native |
| E Runtime model | Plus a 0.5-1 GB model | Low writing, high engineering | Cannot be seeded reliably | Experimental plugin |
| E' Build-time drafting | None at runtime | Curation time | Same as A-D | Native |

## 5. Fit with the design bible

**The takeaway: procedural copy is principle 3 made concrete (show what each decision led to), but only if the coach's decisions are still in the save when the story is written. Today most in-match decisions are not.**

The defining moment, a risky draft pick winning the Brownlow, is fully traceable today: honour-roll Brownlow row (player id) → `drafted_pick`, `drafted_year`, `drafted_club` → the coach record's clubs and years, which show whether this coach made the pick (an inference: drafted_club and drafted_year fall inside one of the coach's stints). Principle 1 shapes the wording rules. The same composer must tell the failed pick just as plainly: "Pick 9, 2028. 31 games, delisted 2032." Headlines.gd already says losses are reported plainly and never mocked (`scripts/core/Headlines.gd:1-6`). If the director wants a flattering register at all (Qud's tomb text), it belongs only on farewell and honour-board surfaces and must never contradict the record. That is a question for him (section 7).

| Coach decision | Stored today? | Where |
| --- | --- | --- |
| Draft pick | **Yes** | `drafted_*` on the player (`GS:2300-2310`); overall at draft lost |
| Backing promise and its outcome | **Yes** | `p["backed"]` (`Backing.gd:60-70`) |
| Sit-down talks, development projects | **Yes** | CareerFacts (`GS:6099, 13384-13388`) |
| Coach-arc beat answers | **Yes** | Arc log, 400 lines (`ClubArcs.gd:151`) |
| Board goal met or missed | **Yes** | Board history (`GS:12334`) |
| Retirement talk | **Yes** | `p["retire_talk"]` (per the G7 audit; not re-verified) |
| Pre-season papers answer | **Yes** | `rec.choice`, `rec.result` (`GS:3786-3800`) |
| Best in-match call, as text | Partly | One MatchStory reason line, last 120 matches |
| Game plan, tags, loose man, moments and their worth in points | **No** | Impact ledger and timeline dropped (`CareerSave.gd:28-36, 339-364`) |
| Press answers and what came of them | **No** | Only standing and anti-repeat memory |
| Weekly story-card choices | **No** | Only flags and trust reasons (`StoryEngine.gd:463-500`) |
| Trades (who for whom) | **No** | Only career stints |

### Example outputs

Each example shows the data rows it is built from. Every number and name in the text must appear in those rows; that is the fact-check.

**Career (real output, seed 2027, Fremantle).** This is what the coach-arc log already produces (`tools/output/coach-arcs-2-story.txt`, lines quoted verbatim):

```
Data: coach {games 205, seasons 9, flags 0, sackings 1,
       clubs [FRE 2027-2032 "first job" (chairman David Bishop), RIC 2033- "poached"]}
2027 Season start [one_year_too_long] BEGINS: Mason Cox has 158 games behind him and his body is telling him it is the last year.
2028 Season start [one_year_too_long] ENDS (one_more): Mason Cox has gone round again: one more year.
2029 Season start [board_feud] ENDS (won_over): The challenger won the vote. The new board is the coach's board.
2032 R6 [poached] The offer from Richmond: Take the job. You sign for Richmond, to start next season. It stays quiet, for now.
2036 Season start [legacy] BEGINS: 10 seasons, 205 games, 0 flag(s). The coach's legacy is being talked about.
```

A career composer would pick three of these by salience and write them as one passage. Mock rewrite, built only from the lines above:

> **MOCK OUTPUT from real data.** Six seasons at Fremantle under David Bishop's board, then a fight for it: the challenger you backed won the 2029 vote. Richmond came for you in 2032 and you went. Ten seasons and 205 games in, there is still no flag.

Note "0 flag(s)" in the real log: exactly the plural fault a central helper fixes.

**Match (MOCK DATA).**

```
Data (MOCK): result {home FRE, away MEL, score [86,80], goals [12,11], behinds [14,14],
  quarters [[20,26],[22,18],[18,24],[26,12]], margin 6, label "Round 14", venue "Optus Stadium"}
  scoring [..., [4,27,0,1,"FRE_31",1]]   # Q4 27 min, Fremantle goal, FRE_31, set shot
  break score at 3QT: FRE 60, MEL 68
  MatchStory {hero_id FRE_31, hero_name "Luke Jackson", hero_line "2 goals, 24 disposals",
  reasons ["You won the clearances 41 to 33."]}
  angles: comeback_from_3qt (8 down) w=7; clutch_goal (Q4 27', margin within 12) w=9
```

> **MOCK OUTPUT.** Down 8 at three-quarter time, Fremantle beat Melbourne by 6 at Optus Stadium. Luke Jackson's set shot in the 27th minute of the last quarter put them in front. You won the clearances 41 to 33.

Fact-check: 8 = 68 − 60; 6 = margin; 27 and set shot from the scoring row; 41 and 33 from the reason. Each passes.

**Season (MOCK DATA).** The almanac already writes this; the gap is the empty `arc` slot.

```
Data (MOCK): almanac 2031 {club WBD, ladder 3, of 18, w 16, l 7, d 0, finals_tag "lost_gf",
  season_hero {name "Sam Darcy", count 6}, story_parts.arc ""}
  digest 2031 {close_final_loss {opp "STK", margin 4, label "Grand Final"}}
  coach_arcs.log [2031, "Season start", "drought", "BEGINS: 5 seasons under this coach and no flag."]
```

> **MOCK OUTPUT.** The Western Bulldogs finished 3rd at 16-7 and lost the 2031 Grand Final to St Kilda by 4. Sam Darcy was the match hero 6 times. *(arc slot, new:)* It was the fifth season under this coach without a flag.

**Draft pick to Brownlow (MOCK DATA).** The bible's defining moment.

```
Data (MOCK): player MEL_44 {name "Ollie Byrne", drafted_year 2027, drafted_type "national",
  drafted_pick 38, draft_rank 12, drafted_club "MEL", firsts.debut {2028, "Round 3"},
  career.games 96, honours.brownlow 1}
  honour_roll 2032 {brownlow {id MEL_44, votes 31, club MEL}}
  coach.clubs [MEL 2026-] -> this coach made the pick (inference: 2027 within the stint)
  angle: risky_pick_paid (pick 38 vs class rank 12; award = Brownlow) w=10
```

> **MOCK OUTPUT.** You took Ollie Byrne at pick 38 in the 2027 national draft. The class rankings had him 12th. He debuted in Round 3, 2028. Five years later he won the Brownlow with 31 votes.

The failed version, from the same composer: "You took Ollie Byrne at pick 38 in 2027. He played 14 games and was delisted in 2030." No softening, no blame.

## 6. Writing style hook

**The takeaway: keep three layers apart (facts, angles, wording), and any coach voice can be dropped in later without touching the fact logic.** A separate session is defining the on-screen coach voice (written style only, never audio) in `docs/research/COPY_VOICE_RESEARCH_2026-11-10.md`, which has not landed. Nothing here should pre-empt it.

The fact layer builds a typed record, and only it reads the save. The angle layer scores the record and returns angle ids with their slots. The phrase layer maps `angle id + register` to sentence variants. A register is a tag such as `record` (plain, data-faithful), `coach` (the coming voice) or `legend` (if the director allows a commemorative register). Changing the voice means editing or adding phrase rows; the fact-check still passes because the slots are the same.

```json
{ "angle": "risky_pick_paid",
  "slots": ["name", "pick", "year", "rank", "award", "votes"],
  "phrases": {
    "record": ["{name}: pick {pick}, {year} draft (ranked {rank} in the class). {award}, {votes} votes."],
    "coach":  ["(to be written from the voice research)"] } }
```

Two rules make this safe. A phrase may only use the slots its angle declares; a validator rejects any others, as `StoryDeck.validate` already does for cards (`scripts/sim/StoryDeck.gd:81-137`). And numbers are formatted by helpers, never typed into phrases, so a voice can change the words around "31 votes" but not the 31. This also leaves room for localisation later (an inference: phrase rows map onto translation keys), though there is none today.

## 7. Questions for the director

These are decisions only he can make. Rulings already cover whether rival clubs get the same treatment and whether options are equal.

1. **Which story first:** a player's career (the draft pick to Brownlow), the season (filling the almanac's empty arc sentence), or a richer match story?
2. **Where stories appear on a portrait phone:** player sheet Career section, news feed, Brownlow night, almanac page, farewell and honour board, or a new place? Should a story ever take a screen of its own?
3. **Is a language model ever acceptable?** Never; only offline, to draft variants he then chooses; or (not recommended) on the phone?
4. **Authoring budget:** who writes the phrase banks (him, an agent drafting for his edit, or build-time model drafts he curates), and roughly how many phrasings per angle before he signs off?
5. **Save size for richer stories:** may the save keep more per match (the impact ledger's coach rows, about a few hundred bytes a match: an estimate, not measured), a per-season rating per player, overall at draft, the Brownlow top 10, and a trade log? Each makes a story possible that can't be told today.
6. **Register:** may farewells and the honour board use a warmer, commemorative tone that leaves out flaws (never contradicting the record), or is everything told in the plain record register?
7. **Silence:** when nothing scores high enough, is "no story this week" acceptable rather than a filler line?
8. **Length:** how many sentences may a story run on the phone: one line, three, or five like the almanac?

## 8. Build scope: first shippable slice

**Recommendation (his call, see questions 1 and 2): a player career story, starting with the "pick to award" story, generated from data that already survives the save.** Reasons, weighed against the alternatives: it is the bible's defining moment; every fact it needs is durable and keyed by player id (draft fields, career lines, firsts, highs, honours, honour roll, backing, CareerFacts, coach record), so it can be regenerated at any time rather than only at full time; it extends T5.r110's CareerRecord rather than starting fresh; and it can be tested on the four premade histories in `data/histories/` plus synthetic players, with no long simulation. The season story (filling `story_parts.arc`) is a smaller alternative and a good second slice. A richer match story is blocked on question 5, because the coach's in-match calls are dropped at the end of each round.

### Brief for a new session

**Goal.** Add `scripts/sim/CareerTale.gd`, a pure static "rules and wording" class like MatchStory and CareerRecord. Given a player id and the save state, it returns up to N sentences plus, for each sentence, the facts it used: `[{text, angle, facts: {slot: value}}]`. It never writes to the save; story text is not the source of truth (`docs/research/AFL_LONG_CAREER_STORY_RESEARCH.md:67-80`).

**Data it reads** (exact fields):
- Player dict: `name`, `drafted_year`, `drafted_type`, `drafted_pick`, `draft_round`, `draft_rank` (generated prospects only; absent for real players, so fall back to pick alone), `drafted_club` (`GS:2300-2310, 2738-2752`; `Prospects.gd:735-736`).
- `p["career"]`: games, goals, stints, lines (`scripts/sim/Career.gd:1-40`); `p["firsts"]` (`Firsts.gd:1-30`); `p["highs"]` (`CareerHighs.gd:1-27`); `p["honours"]` (`Almanac.gd:216-260`); `p["backed"]` (`Backing.gd:60-70`).
- `GS.honour_roll[*]` Brownlow, Coleman, Rising Star, Norm Smith and B&F rows by id, with votes (`GS:6404-6455`).
- `GS.career_facts[id]` rows (`CareerFacts.gd:1-48`); `GS.honour_board` rows for departed players (`HonourBoard.gd:1-40`); `GS.departed_names`.
- `GS.coach_arcs.coach.clubs` (code, from, to), to say "you took him" only when the coach was at `drafted_club` in `drafted_year`.

**Angles for the slice** (weights to tune by eye, then shown to the director): `risky_pick_paid` (award after a late pick or pick well below class rank), `pick_fell_short` (the same pick, few games, delisted or retired early, told plainly), `backed_and_delivered` / `backed_and_broken` (backing ledger), `debut_to_milestone`, `career_best`, `flag_with_you`. Cap the output at 3 sentences (question 8 may change this).

**Files to create or change:**
- Create `scripts/sim/CareerTale.gd`, with the angle scorer and composer, plus helpers for plurals, ordinals, possessives and the existing `name_list`.
- Create `data/tales/career.json`, the phrase bank: angle → slots → `record` register phrases only. Leave the `coach` register empty for the voice session.
- Create a validator that rejects undeclared slots, modelled on `StoryDeck.validate`.
- Create `tests/test_career_tale.gd` and add it to `tools/ci_shards.txt`.
- **No new UI in this slice.** Wiring onto the player sheet or Brownlow night waits for question 2. If he answers, the smallest hook is a line above CareerRecord's section, with a real-tap check per CLAUDE.md.

**Test plan:**
- Golden outputs: 6-8 hand-built synthetic players (late pick plus Brownlow; early pick delisted; real player without draft_rank; father-son with no pick; traded mid-career; retired, honour board only), each with the exact expected text.
- Fact-check property: for every player in all four premade histories, every number in the output appears among the sentence's `facts` values, those values equal the save fields, every name maps to the right id, and no `{` or `}` is left. Also check "1 goal", not "1 goals".
- Logic properties: `risky_pick_paid` never fires without an award row for that id; "you took him" never fires outside the coach's stint; a failure angle and a payoff angle never fire together.
- Determinism: same save, same text, across a save/load round trip.
- Godot runs: one suite, run once locally through the shared slot (`C:/kt/test_slot.sh`), then CI. No balance run is needed, because nothing touches the sim.

**Limits.** Mobile portrait; no sim changes; no save-schema change in this slice (anything from question 5 is a separate row); English only; no language model; keep Godot launches to the minimum because test slots are shared; follow the `afl-ui-writing` skill for all wording; and use no Collingwood in any capture.

**Done looks like.** CareerTale returns stories for every player in the premade histories with zero fact-check failures. Golden tests are green in CI. Ten sample stories, including at least two failures told plainly, are pasted in the PR for the director to read. The PR body has a standalone "Closes row N" line if a TODO row is assigned.

**Open questions that block or shape this slice** (repeated from section 7): 1, which story first; 2, where it appears; 4, who writes the phrase bank and how many variants; 6, whether a commemorative register is allowed; 8, story length. Question 5 (save size) does not block this slice, but it decides whether overall-at-draft and rating trajectory ("how far he came") can join later.
