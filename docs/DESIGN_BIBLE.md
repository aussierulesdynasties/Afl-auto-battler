# Aussie Rules Dynasties: Design Bible

_Director's decisions, brainstorm of 2026-10-09. Session record:
[brainstorms/2026-10-09-design-bible.md](brainstorms/2026-10-09-design-bible.md)._

_Updated 2026-11-12 with the director's consent: press-line wording, pillar order, story question._

## What this document is

The bible holds the ultimate truth for Aussie Rules Dynasties. It is a philosophy
that informs all development, not a roadmap, and it schedules no work.

- Where CLAUDE.md, the roadmap or any other document disagrees with the bible,
  the bible wins and the other document is corrected.
- The bible changes only with the director's explicit consent for each
  individual update. No agent edits it on its own judgement.
- Everything in it was said or chosen by the director.

## The vision

A simulation that feels like a story, a legacy, a dynasty.

**The defining moment.** A player you took with a risky draft pick wins the
Brownlow. The satisfaction is that your vision and your faith paid off.

**The other side of it.** The same pick fails. The player feels disappointed, but
understands the risk was theirs to take. Risks can pay off and risks can fail. It
is up to the player, and the game is objective about it.

## The first pillar: story

A simulation that feels like a story, a legacy, a dynasty. The coach's career is
the centre of the game.

## The second pillar: a deep simulator

It is real footy. Player ratings reflect reality, and decisions move the odds,
never the certainty.

## The third pillar: player agency

Player agency is the third pillar. It is what sets this game apart from simulators
that lean toward the uninteractive.

- This is not a spreadsheet simulator.
- Setup and observation are fine, but the game has active participation as well.
- The game is designed for a player who plays most matches and sims the odd one.
  Playing hands-off is the gamer's call, and the risk of it is theirs.

## The fourth pillar: readability and intuitive interfaces

_Director, 2026-10-13._

Readability and intuitive interfaces are a core pillar of this project, paramount
to its success. It is a challenge for an information-heavy game, but it is what
we have to aspire to.

This applies to the entire game. On every screen:

- Sections feel distinct. Text that is all the same colour harms readability;
  club colours and strategic use of bold set sections apart.
- A player's allegiance is obvious.
- No text becomes overlooked.
- When we can explain info visually rather than with copy, it's better (director,
  2026-11-10).

## The principles

One ethos runs through every decision in the game: the player knows the risk, the
risk is theirs to take, and the results are explained clearly and objectively.

1. **The risk belongs to the player.** The game does not soften a failure or take
   the decision away.
2. **Decisions move the odds, never the certainty.** Perfect coaching with a
   weaker list maximises your chances but guarantees nothing. In AFL you can
   never take a result for granted; a poor team can knock off an unprepared
   opponent.
3. **The game shows what each decision led to.** Some outcomes are obvious: you
   decide to shoot, and it scores or it doesn't. Others need clear UI and
   deliberate copy: what the roaming interceptor did, whether the switched
   defender halted the forward's run. The player assesses whether it met their
   expectations.
4. **Reading the game is the skill.** Every decision gate says what each option
   does for you and what it costs, with the size and the odds, in football words.
   The game never says which option is better: every option carries a positive and
   a negative, and the weighing is the coach's. Randomness is fine when the gate has
   named the risk. (Director, 2026-10-18: "I still want the football language, but I
   also want full transparency behind each decision and the impact it will have";
   "the decision should still be relatively opaque and both options carrying
   positives and negatives"; wording approved as written.)
5. **No excessive UI.** The player should not feel they will develop arthritis
   from clicking.

## The coach

The player is a coach, and every decision is roleplaying: event calls, in-game
moments (defend now, or attack now?), answers in press conferences, the look of
Forge creations, the list management strategy.

**What can affect the sim.** What the coach says or decides can affect the sim.
How the club looks or sounds never does. Weather is the one exception: it should
matter.

**Press conferences.** Answers affect the sim: player morale, board expectations
and relationships with the press. Journalists have personalities.

- Every answer carries a named risk: the odds of each outcome are shown before
  you answer.
- The press conference tests media literacy, relationship management and board
  compliance.
- The effect is visible afterwards. Criticise a young player and his morale may
  drop, or his resolve may tighten. The gamer sees their words had an impact, for
  better or worse, and adjusts or carries on.

## Match day and the visual sim

Match day is the culmination of list management and decisions made for this
specific match. Matchup changes, game plan adjustments and in-game decisions all
give the player agency over the result.

The visual sim is the closest the game comes to its target feel. It is real
footy: a visual simulation of the obtuse stats that sit behind every sports sim.

| Kind of move | Examples | How the player sees it |
| --- | --- | --- |
| Structural | Game plan, flooding the backline, stacking the contest | The visual sim changes greatly |
| Individual | A player role, a positional switch | The role shows on the ground; the game feed and post-quarter and post-match copy explain how effective it was |

## Immersion and the art standard

Immersion is a believable world that responds to the coach. It breaks when:

- coaching moves do not change the game
- player ratings do not reflect reality
- the visual sim does not update to a change in strategy
- the art is wrong: bad anatomy, awkward staging, or a misunderstanding of what
  sets AFL apart, including the dimensions and conventions of an AFL field

**The art standard.** Art goes through an internal QA process before the
director's final verdict. Obvious aberrations and ugly errors are picked up by
the agent, without the director babysitting. Known faults that must never reach
the director:

- skin showing through a jumper
- an animation that looks bizarre
- a ball that hovers, or acts independently of the player using it

## The feature test

A feature must be justifiable based on its intent. It does not need to pass every
question below, but it must answer to at least the intent it claims.

- Does it add to the coach's story or the club's legacy?
- Does it enhance the core philosophy of the game?
- Does it increase immersion?
- Does it create better roleplaying opportunities?
- Does it deepen player agency?
- Does it feel and look beautiful and fun to play?
- Is it understandable, not obtuse or opaquely implemented?

**Who decides.** The agent assesses whether a feature deserves to exist and says
so. The director's say is final.

## Balance

Balance is settled when two things are both true: testing shows numbers similar
to real AFL, and the director's playtest passes the vibe check.

Player ratings that reflect reality are part of this work, not a separate goal.
Balance is still settling.

## What this game will not have

_Director, 2026-11-12: "All but 14 and 15" of the drafted list. Each line keeps
the words of his that it comes from._

- You coach the side; you never play the footy yourself. (2026-10-18: "Playable
  control")
- No microtransactions or real-money purchases. (2026-10-05: "Zero
  microtransactions.")
- No guaranteed wins: good coaching improves your chances but never makes a
  result certain. (2026-10-09: "Decisions move the odds, never the certainty.")
- The game never tells you which option is best. (2026-10-18: "The game never
  says which option is better")
- How your club looks or sounds never changes a result. (2026-10-09: "How the
  club looks or sounds never does.")
- No hidden help or cheats for either side, and no add-on special-ability perks.
  (2026-10-05: "Reject RPG ability furniture and hidden AI resource advantages.")
- No unseen hand that fixes close finishes or props up struggling rivals.
  (2026-10-05: "Reject an AI director that rigs close finishes")
- No made-up turning points in a quiet win. (2026-10-05: "A quiet professional
  win needs no fabricated turning point.")
- No permadeath, no fantasy-style recruiting, and no extra injuries just for
  drama. (2026-10-05: "Reject permadeath, fantasy recruitment and increased
  injury frequency for drama.")
- Rival clubs never act on information they couldn't know. (2026-10-05: "Rivals
  must not react to information they could not know.")
- No compulsory weekly press conference. (2026-10-05: "mandatory conferences")
- No separate dialogue system for conversations. (2026-10-05: "a separate
  dialogue engine")
- No personality quiz that gives the coach permanent bonuses. (2026-10-05: "a
  personality quiz that assigns arbitrary permanent buffs")
- No invented scandals about real-named players. (2026-10-11: "never an invented
  scandal for a real-named player.")
- No skipping ahead to the Grand Final; "Sim the week" is the only fast path.
  (2026-11-03: "cut")
- No landscape mode on phones; PC keeps its wide layout. (2026-11-05: "Drop
  landscape")
- No light theme for now: parked, not ruled out. (2026-10-13: "i dont want to
  waste time on it")

## Open questions for the director

- How does weather affect a match? It is decided that it matters; the system is
  not designed.
- Pre-timeskip survey (a roadmap item): a full survey, or the simpler version
  where the sim follows the club's existing instructions and asks only about what
  nothing else covers?
