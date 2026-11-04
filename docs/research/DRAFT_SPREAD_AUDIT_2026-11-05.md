# Draft AI spread audit (TODO row 22), 2026-11-05

Seeded all-AI League Draft, 20 seeds, current main logic. Reproduce:
`godot --headless --path . --script tools/audit/run_audit.gd -- draft_logic_impl spread 20`.
Nothing in the draft logic changed; this is evidence only. Balance stays the director's call.

## 1. Role concentration ("six key forwards in the first eleven picks")

Average count per draft, by kind (KPF = key forward by `Matchups._is_key_forward`).

| Band | KPF | FWD | MID | DEF | RUCK |
|---|---|---|---|---|---|
| Picks 1-11, AI drafts | 4.55 | 0.95 | 4.70 | 0.55 | 0.25 |
| Pool best 11 by rating | 3 | 0 | 7 | 0 | 1 |
| Pool best 11 by club worth (rating and potential, no scouting error) | 5 | 1 | 4 | 1 | 0 |
| Picks 1-30, AI drafts | 6.85 | 3.00 | 12.65 | 5.85 | 1.65 |
| Pool best 30 by club worth | 9 | 3 | 13 | 5 | 0 |

Most key forwards in one draft's first 11 picks: 7.

What causes it: the clubs value young high-potential tall forwards (Darcy 72 now / 92 potential, Amiss, Morris) near the top, and the AI follows that value. The scarcity weight is near zero in the first picks, so this is not the AI chasing a position. By pick 30 key forwards are *under* their worth share (6.85 against 9). The director's report reproduces, but it comes from how the pool is valued, not from a broken pick rule. Spreading picks by force would mean a quota, which the roadmap rules out.

## 2. Named boards (the director's examples)

Mean pick (range) across 20 seeds.

| Player | Mean | Range | Player | Mean | Range |
|---|---|---|---|---|---|
| Sam Darcy | 7.0 | 1-14 | Luke Jackson | 29.6 | 16-40 |
| Max Gawn | 32.1 | 6-327 | Josh Worrell | 35.4 | 20-49 |
| Cody Walker | 57.9 | 26-97 | Jagga Smith | 67.2 | 30-97 |
| Jake Waterman | 91.3 | 55-125 | Max Hall | 92.5 | 61-135 |
| Noah Anderson | 96.7 | 58-123 | Tom Stewart | 229 | 31-413 |
| Christian Petracca | 316 | 67-372 | Jack Viney | 315 | 172-476 |

Dan McStay is not in the pool. Callum Wilkie (31, DEF, 88) goes at 61.9 on average (22-163). Petracca, Viney and Stewart going in the 200s-300s, and Gawn's 6-327 spread, are the outliers worth his look: older players are discounted by the clubs' horizon, and the per-club scouting error widens the range.

## 3. Draft list scroll in the exported web build

Exported the Web preset with Godot 4.7.2 and served it locally. In a new career I picked Fremantle and opened the League Draft (on the clock at pick 18), then:

| Step | Result |
|---|---|
| Browser wheel event on the pool (6 notches down) | The list moves down, from Bailey Smith to Taylor Walker; no reversal |
| Tap a row, card opens, tap Close | The list stays at Taylor Walker; no snap to the top |
| Drag the scrollbar down, tap Noah Anderson, Close | The list stays where it was dragged |

The browser pane's own scroll tool did not reach the game canvas, but a real browser `WheelEvent` on the canvas did. Not tried: a phone's touch drag (no device here). The headless guard is `_test_pick_keeps_scroll` in `tests/run_draft_ui_tests.gd`.

## Questions for the director

- Key forwards follow the pool's worth: answered 2026-11-05, "Leave it as is".
- Should Petracca, Viney and Stewart fall that far in a redraft, and is Gawn's range acceptable?
