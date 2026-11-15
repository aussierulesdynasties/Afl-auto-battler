# Pre-2012 overall: how much each skill counts

_Ruling 19 (director, 2026-11-15): before 2012 there is no AFL Player Rating, so a season's overall is built from its skills, weighted by what the AFL Player Rating rewarded in 2012-2025. Written by tools/wheelo/weights_report.py from tools/wheelo/fit.py._

How it was measured: every 2012-2025 season was rated twice, once from Wheelo (the AFL Player Rating against his position) and once from only the stats a past era recorded. For each position, the weights are the mix of skills that best matches the AFL Player Rating; no skill may count against a player. "Match" is how closely that mix follows the real rating (1 = exactly).

## 1987-1997

Recorded: kicks, marks, handballs, goals, behinds, hit-outs, tackles and free kicks. No contested possessions, contested marks, clearances, inside 50s, rebounds or bounces, so Contested ball, Contested marking, Intercepting, Carry and Creating sit at the position's average and count for nothing, and Uncontested marking (marks less contested marks) is every mark.

| Position | Match | Skills, most important first |
|---|---|---|
| Key Defender | 0.65 | Kicking 30%, Handballing 19%, Uncontested marking 19%, Durability 12%, Pressure 12%, Discipline 6% |
| General defender | 0.76 | Kicking 45%, Handballing 20%, Accuracy 13%, Durability 9%, Pressure 7%, Goalkicking 3%, Discipline 3% |
| Midfielder | 0.86 | Kicking 35%, Handballing 33%, Pressure 16%, Goalkicking 13%, Durability 2% |
| Mid-Forward | 0.87 | Kicking 33%, Handballing 29%, Goalkicking 19%, Pressure 10%, Durability 5%, Accuracy 4% |
| General forward | 0.83 | Kicking 32%, Goalkicking 21%, Handballing 19%, Pressure 15%, Accuracy 7%, Discipline 3%, Durability 2% |
| Key Forward | 0.85 | Kicking 36%, Goalkicking 26%, Handballing 14%, Pressure 11%, Accuracy 6%, Durability 3%, Discipline 2% |
| Ruck | 0.84 | Ruck 32%, Handballing 25%, Kicking 17%, Accuracy 8%, Goalkicking 7%, Discipline 5%, Pressure 3%, Durability 3% |

## 1998

Recorded: the 1987 list plus rebound 50s, inside 50s, clearances and clangers. Still no contested marks, so Uncontested marking is every mark.

| Position | Match | Skills, most important first |
|---|---|---|
| Key Defender | 0.65 | Kicking 28%, Uncontested marking 20%, Handballing 18%, Durability 12%, Pressure 10%, Discipline 8%, Creating 3% |
| General defender | 0.77 | Kicking 38%, Handballing 16%, Accuracy 16%, Durability 9%, Creating 7%, Pressure 4%, Discipline 4%, Uncontested marking 2%, Goalkicking 2% |
| Midfielder | 0.90 | Creating 20%, Handballing 18%, Contested ball 16%, Kicking 14%, Goalkicking 10%, Pressure 8%, Discipline 7%, Accuracy 3%, Durability 3% |
| Mid-Forward | 0.89 | Creating 22%, Handballing 22%, Goalkicking 16%, Kicking 14%, Pressure 7%, Durability 5%, Contested ball 5%, Accuracy 4%, Discipline 4% |
| General forward | 0.85 | Goalkicking 22%, Kicking 17%, Handballing 16%, Creating 15%, Pressure 11%, Accuracy 7%, Discipline 6%, Contested ball 3%, Durability 2% |
| Key Forward | 0.85 | Kicking 35%, Goalkicking 27%, Handballing 12%, Pressure 10%, Accuracy 6%, Durability 4%, Discipline 3%, Contested ball 2% |
| Ruck | 0.88 | Ruck 35%, Handballing 15%, Discipline 9%, Contested ball 9%, Goalkicking 7%, Accuracy 7%, Uncontested marking 7%, Creating 5%, Pressure 3%, Durability 3% |

## 1999-2002

Recorded: everything AFL Tables keeps except goal assists and time on ground.

| Position | Match | Skills, most important first |
|---|---|---|
| Key Defender | 0.74 | Kicking 31%, Handballing 18%, Contested marking 17%, Pressure 10%, Discipline 10%, Durability 9%, Carry 3%, Contested ball 3% |
| General defender | 0.83 | Kicking 30%, Accuracy 16%, Handballing 12%, Contested ball 9%, Contested marking 8%, Creating 7%, Durability 6%, Discipline 5%, Carry 4%, Pressure 2% |
| Midfielder | 0.92 | Contested ball 22%, Creating 16%, Kicking 15%, Handballing 14%, Discipline 9%, Pressure 6%, Goalkicking 6%, Accuracy 4%, Carry 3%, Contested marking 2%, Durability 2% |
| Mid-Forward | 0.90 | Creating 19%, Handballing 18%, Kicking 12%, Goalkicking 12%, Contested ball 11%, Pressure 6%, Durability 6%, Accuracy 5%, Discipline 4%, Carry 4%, Contested marking 2% |
| General forward | 0.87 | Goalkicking 18%, Kicking 15%, Handballing 13%, Contested ball 11%, Creating 10%, Pressure 9%, Accuracy 7%, Discipline 7%, Carry 5%, Contested marking 2%, Durability 2% |
| Key Forward | 0.86 | Kicking 32%, Goalkicking 23%, Handballing 9%, Pressure 8%, Accuracy 6%, Contested ball 5%, Contested marking 5%, Discipline 5%, Durability 3%, Carry 3% |
| Ruck | 0.89 | Ruck 33%, Handballing 17%, Contested ball 10%, Discipline 7%, Accuracy 7%, Goalkicking 6%, Kicking 6%, Contested marking 4%, Creating 4%, Pressure 3%, Durability 2% |

## 2003-2011

Recorded: everything AFL Tables keeps. Still no pressure acts, metres gained, intercept possessions, one-on-ones, coaches votes or speed (those start in 2012).

| Position | Match | Skills, most important first |
|---|---|---|
| Key Defender | 0.75 | Kicking 27%, Durability 18%, Contested marking 15%, Handballing 15%, Discipline 9%, Pressure 9%, Carry 3%, Contested ball 3% |
| General defender | 0.83 | Kicking 31%, Accuracy 14%, Durability 11%, Handballing 11%, Contested ball 10%, Contested marking 7%, Creating 6%, Discipline 5%, Carry 4% |
| Midfielder | 0.92 | Contested ball 24%, Kicking 21%, Handballing 12%, Creating 9%, Discipline 8%, Pressure 7%, Goalkicking 6%, Durability 5%, Carry 4%, Accuracy 3%, Contested marking 2% |
| Mid-Forward | 0.91 | Kicking 18%, Creating 15%, Handballing 14%, Contested ball 12%, Goalkicking 10%, Durability 8%, Pressure 7%, Accuracy 5%, Carry 5%, Discipline 4%, Contested marking 2% |
| General forward | 0.88 | Kicking 16%, Goalkicking 15%, Creating 13%, Handballing 12%, Contested ball 11%, Pressure 8%, Accuracy 7%, Discipline 7%, Carry 5%, Durability 5%, Contested marking 2% |
| Key Forward | 0.87 | Kicking 26%, Goalkicking 20%, Handballing 8%, Pressure 7%, Creating 7%, Durability 7%, Accuracy 6%, Contested ball 5%, Contested marking 5%, Discipline 5%, Carry 3% |
| Ruck | 0.89 | Ruck 32%, Handballing 15%, Contested ball 10%, Kicking 7%, Discipline 7%, Accuracy 7%, Goalkicking 5%, Creating 5%, Contested marking 5%, Pressure 3%, Durability 3% |
