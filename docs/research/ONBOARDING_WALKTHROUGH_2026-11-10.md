# Onboarding on fresh saves: walkthrough record (row T3.R56, 2026-11-10)

The director asked: "Walk through genuinely fresh saves with full onboarding
enabled, not a mature save with tutorial flags already set."

Every walk below starts from a **new settings file** (no tip seen on this
device) and a **new career at Fremantle**, with Tutorials on unless the mode
says otherwise. The walk is a test suite, `tests/run_onboarding_walk_tests.gd`,
so it reruns on every CI pass. Each line it prints (`WALK|mode|...`) is copied
below. Tips are closed with a real tap on Got it (`tests/tap.gd`).

How tips are stored, which shapes every finding:

- Each screen's tip shows once **per device** (settings file, `seen_<key>_intro`).
- The postseason tip is the one exception: it is **per career**.
- Tutorials On/Off is per career (New career's toggle, then Settings).

## Records

Run: GitHub `run_on_github.yml`, suite `onboarding_walk`. "No tip" on a screen
he has already seen is the expected result.

### 1. Initial draft (League redraft)

| Screen | Tip |
| --- | --- |
| Choose your club | none (his club isn't his yet) |
| The board, after choosing Fremantle | **The League redraft** |
| 44 players taken, Start season | none |

Gap found and fixed: the board used to show the National Draft's tip ("pick the
kids…") over Choose your club.

### 2. Weekly loop (straight on from the draft)

| Screen | First visit | Second visit |
| --- | --- | --- |
| Appointment interview | none | – |
| Pre-season | **The pre-season** | – |
| Hub, Round 1 | **Your week** | none |
| Selection | **Picking the side** | none |
| Coaching | **How we play** | none |
| Training | **How training works** | none |
| List | **Your list** | none |
| Staff | **Your staff** | none |
| Season stats | **Season stats** | none |

Every tip shows once and stays closed afterwards. The appointment interview has
no tip; its own questions are what it explains.

### 3. First postseason (top of the ladder, finals won from the hub)

| Stop | Tip |
| --- | --- |
| Hub, Round 1 | **Your week** (closed) |
| Grand Final over | the press conference comes first |
| Hub after it | **After the finals** (the order of what's ahead) |
| Season review | awards night first, then **Season review** |
| Trades & Contracts | **The off-season** |
| Talk contract, own player | **Contract talks** (new) |
| Trade tab | **Trading** (new) |
| National Draft | the recruiting panel first, then **The draft** |
| Trade picks on draft night | **Trading picks** (new) |

Gaps found and fixed on this walk: the Season review tip never followed awards
night, and the draft tip never followed the recruiting panel.

### 4. Early elimination (8th, out in the first week of the finals)

| Moment | Tip |
| --- | --- |
| Five finals weeks played on from the hub | none while the finals are on |
| Grand Final results closed | none yet: the press conference after the Grand Final comes first |
| Hub after the press conference | **After the finals** |

He gets the same postseason tip as a premier, once the season is over.

### 5. Reload (save half-way through the tips, quit, load)

| Screen | Tip |
| --- | --- |
| Hub, Round 1, then Selection | **Your week**, **Picking the side** |
| Save, quit, load | Tutorials still on |
| Hub after the reload | none (seen) |
| Selection after the reload | none (seen) |
| Coaching, never opened before | **How we play** (still due) |

The postseason tip is still due after the reload.

### 6. Skip

The hub's first tip has **Skip**. One tap closes it and the week's buttons are
there. Skip covers that tip only: Selection still shows **Picking the side**.
Skipping help never skips a football decision.

### 7. Off (Tutorials off at New career)

No tip on the draft board, the hub, Selection, Coaching, Training, List, Staff
or Season stats. Turned On in Settings mid-career, the unseen tips come
(Selection showed **Picking the side** on its next visit).

### 8. Replay

**Not implemented.** Settings has 16 rows; the only tips control is Tutorials
On/Off. Turning it Off then On does not bring back a tip already seen
(Selection stayed quiet). A coach who closed a tip too fast cannot read it again.

## Gaps found

| Gap | Where | Status |
| --- | --- | --- |
| The National Draft's tip copy ("pick the kids who will carry your club") opened over Choose your club on the **League redraft**, where nobody picks kids | DraftScene | Fixed: the redraft has its own tip, "The League redraft", shown on the board once the club is chosen |
| On the National Draft the recruiting panel opens first and the draft tip **never followed it** | DraftScene | Fixed: the tip opens when the panel closes |
| On a career's first Season review, awards night opens first and the **Season review tip never followed it** | SeasonReviewScene | Fixed: the tip opens once awards night is done |
| No tip on the off-season's Trade tab or in contract talks | OffseasonScene | Built: "Trading" and "Contract talks" |
| No tip on the draft-night pick trading sheet | DraftTradeSheet | Built: "Trading picks" |
| During the League redraft the tip's card and button are the game's no-club red, not Fremantle's purple | The whole redraft board: `GameState.my_club` stays empty until Start season | Open: the board has the same red; not this row's change |
| **Replay is not implemented.** No control re-opens a tip already seen; Tutorials Off then On does not reset what was seen | Settings | Open: written down, not built |
| A second new career on the same device sees no screen tips (they are per device); only the postseason tip comes again | GameState | Open: by design today, written down |
| The match day momentum note is not part of this walk | MatchScene | Covered by `run_matchday_tests` |

## The new tips (copy)

- **Trading** (off-season, Trade tab, first tap): choose a club and put players
  or picks on each side, a no comes with their reason; want one of theirs, add
  him alone and Ask their price; selling, Ask around or use the trade table;
  contenders want help now, rebuilders want youth and picks; trading closes
  when the draft starts.
- **Contract talks** (first Talk contract with your own player): he names a
  salary and a term, meet it and he signs; offer less and he names his lowest;
  three failed offers and he tests free agency; under two-thirds of his lowest
  insults him, counts as two and costs morale.
- **Trading picks** (draft night, Trade picks): only picks change hands, this
  draft's and the next two; bids for your pick show at the top; the draft waits
  while the sheet is open.
- **The League redraft** (board, after Choose your club): 44 from the league's
  players, each costs his salary, under the cap with at least two rucks.

Each was checked against the rules it describes: `Contracts.gd` (three offers,
the counter is his floor for that term, under two-thirds is an insult costing
two offers and 5% morale), the row 67 trade flow (Ask their price, Ask around,
the trade table) and `Draft.is_valid` (44, cap, two rucks).
