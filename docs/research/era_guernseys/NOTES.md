# Era guernseys 1990-2026 (TODO row 142, Legacy L9)

What the figures and crests wear is drawn picture by picture (below, "The kit atlas"). `era_guernseys.csv`
has one row per club per spec era, from 1990 (or the club's entry) to 2026, resolved
exactly as the game resolves `data/legacy/clubs_by_year.csv` over `data/clubs.csv`. A blank `to` means the era
runs to 2026: that row is today's guernsey, unchanged. `game_spec` is the spec the game draws
(`design:base/pattern/pattern2[/shorts[/pattern3]]`).

## Source

footyjumpers.com, each club's home-guernsey page (the `source` column), read year by year from its pictures.
Earlier text-only research (2026-11-11, Wikipedia and club sites) left open checks; every one is closed below.

## Hex colours

- A colour the club still wears keeps today's hex from `data/clubs.csv`. The footyjumpers pictures are
  illustrations, and their palettes are not reliable enough to override the game's colours.
- A colour the club no longer wears is sampled from the picture named in the row's note:
  - Fremantle 1995 green #065D1E and red #DC0000 (Fremantle-1995). Its purple sampled #321E64; today's #2A0D54 is kept.
  - West Coast navy: #021A31 (West-Coast-1995), #05173F (West-Coast-2000), #0D1D42 (West-Coast-2016).
  - Port Adelaide teal sampled #009CA6; today's #008AAB is kept.
- Kept as approved in PR 1508: the Bears' 1990-91 cerise and gold (the picture samples #B51F41 and #FFC211).
- Melbourne's 1990 navy samples darker (#061022); today's is kept, as above.

## Open checks, closed from the pictures

| Check | Finding |
| --- | --- |
| Adelaide side panels | Only 2006-09 (crows06). Full low hoops 1991-2005 and from 2010; the earlier "2006-15" was wrong. |
| Brisbane Lions layouts | Today's yoke 1997-2009 and from 2014; 2010-13 blue to mid-chest over maroon (lions10). |
| Gold Coast 2011-24 | The same side panels as today, in gold instead of dark red. |
| GWS 2012 | Orange top, charcoal below cut by a white G, 2012-20 (giants12); today's from 2021. |
| Footscray hoop | One wide red hoop edged white round the middle, 1990-96 (dogs90); a red chest hoop and red back 1997-2011 (dogs97); two hoops from 2012. |
| Fremantle anchor sides | Green on the wearer's right, red on his left, 1995-2010; three chevrons from 2011. |
| West Coast | Royal wings 1990-94; navy wings 1995-99 (the earlier "royal to 1999" was wrong); navy, white and gold tricolour 2000-15; navy wings 2016-17; royal wings from 2018. |
| Port 1997 | Teal top, black below, claw slashes rising to the wearer's left shoulder, 1997-2009. |
| St Kilda | The cross guernsey 1997-2001 (saints97); today's panels otherwise. |
| Sydney | The Opera House guernsey on white 1990-91 (swans90); today's from 1992. |

## The kit atlas, picture by picture (director 2026-11-13)

The director rejected the era-level chart ("at least 90% of guernsey iterations are missing"), so every
footyjumpers home picture 1990-2025 is drawn: `tools/kits/kits.txt`, one line per picture (553 pictures,
268 drawings), drawn by `tools/kits/kit_atlas.py` into `assets/vignette/kits_atlas.png` and
`data/legacy/kits.csv` (which seasons wear which cell). Each drawing copies the picture's stripe and hoop
counts and widths, back, collar, trim and panels. Pictures that differ only in what is not drawn share a
drawing. A picture worn for part of a season is drawn and charted but worn by no season. The match figures
(design 100 + cell) and the crest read the atlas; the spec above still gives socks, shorts and the oval's discs.
2026 on is `data/clubs.csv`'s own guernsey, unchanged. Chart: `tools/visual/capture_era_chart.gd`.

Calls made from the pictures: North's 2016 home is the blue one (the white 2016 picture is the clash);
Port's 2004-06 and 2013 "Away" pictures are the home design with other sponsors.

## New designs in the game

anchor, power97, eagles00, swans90, giants12, saints97, lions10, dogs90, dogs97 and crows06: drawn on the
match figures (`assets/vignette/figure.gdshader`), the crest (`assets/ui/badge/badge_designs.png`, cells 17-26)
and the oval's discs (`PitchView.DISC_FAMILY` maps each to a disc shape). The anchor needs a third pattern colour
(`pattern3`, the spec's fifth token).
