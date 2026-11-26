# CI runners on the director's PC (removed 2026-11-26)

Removed on 2026-11-26 (director: "Remove it"). WSL Ubuntu is uninstalled, the seven runner
registrations and the keepalive task are deleted, and the repo variable `QUEUE_RUNNER` is
`github`, so every job runs on GitHub's runners. `tests.yml` still holds the `pc` path, unused.
The rest of this file is the old setup, kept as a record.

## What it was

The merge queue spent most of its time waiting for GitHub's free runners (2026-11-22: median
128 minutes from a group's start to its verdict, with about 9 jobs running at once across every
PR; 2026-11-23: 4 to 6). Merge-queue groups can run on two runners on the director's PC instead
(Ryzen 7 9700X, Windows, in WSL Ubuntu, capped at 8 GB). Since 2026-11-25 (director: "turn the
PC runners on") this repo's own pull requests and pushes to main use the PC too, but only when one
of its runners is online and idle at the moment the run is planned; otherwise they run on GitHub's
runners, so the PC only ever adds capacity. A third, small runner (`afl-plan`) runs only the
plan job that makes that choice, so this repo's runs plan within seconds instead of waiting in
GitHub's queue (director, 2026-11-25). With the PC paused, those runs wait until WSL is back;
set `QUEUE_RUNNER` to anything but `pc` to send everything to GitHub.

## Safety

- The repo is public. Jobs go to the PC only from merge-queue groups, pushes to main and pull
  requests whose branch is in this repo: all code that someone with write access pushed. A fork's
  pull request runs on GitHub's runners. A fork's workflow file
  comes from the fork, so the approval setting below is what stops a fork from pointing itself at
  the PC: never loosen it.
- Settings > Actions > General > "Approval for running fork pull request workflows from contributors":
  "Require approval for all external contributors".
- Each runner is a systemd service in WSL, running as the unprivileged Linux user `runner`, not as a
  Windows admin. It only sees the files WSL gives it.
- The switch is the repo variable `QUEUE_RUNNER`. With `pc`, the plan job (on GitHub's runners)
  asks the runners API (secret `MERGE_TOKEN`) for `afl-queue` runners: a queue group uses the PC when
  at least one is online; this repo's pull requests and pushes to main when at least one is online
  and idle. Otherwise, and with anything else or unset, the run uses GitHub's runners.
- Pausing for a game: `wsl --shutdown` in Windows. Groups planned after that run on GitHub's
  runners. A group already sent to the PC waits until WSL is back (or the queue's 240 min timeout
  sends it back to the queue), so pause between groups when you can.
- The runners share the PC with the director's own use, games included. On 2026-11-23 six
  uncapped runners took about 15 GB, ran the PC out of memory and crashed a game. The director
  then chose two runners under a 6 GB cap. On 2026-11-25 the dataset check (a full export, near
  4.8 GB) and a shard (about 2.5 GB) ran at once and went over it; the director raised the cap to
  8 GB (31 GB in the PC).
- WSL's `/tmp` is a RAM disk (4 GB at the 8 GB cap) that counts against the cap. The dataset
  check's exported pack filled it on 2026-11-25, so the setup script puts `/tmp` on the disk
  (it masks `tmp.mount`). A per-runner `TMPDIR` was tried first and made Godot's import crash.

## Setup (once)

1. Windows, as admin: `wsl --install -d Ubuntu` (reboot if asked), then create the Ubuntu user.
2. In Ubuntu: add `[boot]` / `systemd=true` to `/etc/wsl.conf`; in Windows, `wsl --shutdown`.
3. `%UserProfile%\.wslconfig`, a hard cap so the runners can never starve Windows:
   ```
   [wsl2]
   memory=8GB
   processors=4
   swap=0
   vmIdleTimeout=-1
   ```
   Then `wsl --shutdown` again. WSL cannot use more than `memory`; a job that needs more fails, not
   the PC. `vmIdleTimeout=-1` keeps WSL up with nobody logged in to it.
4. Task Scheduler: a task "WSL Ubuntu keepalive (AFL runners)" that runs at log on:
   `wsl.exe -d Ubuntu --exec /bin/sleep infinity` (hidden). It starts WSL and its runner services
   when Windows starts, and keeps the WSL VM up.
5. In Ubuntu, in a clone of this repo: get a registration token
   (`gh api -X POST repos/aussierulesdynasties/Afl-auto-battler/actions/runners/registration-token -q .token`,
   needs a repo admin) and run `sudo REG_TOKEN=<token> bash tools/ci_runner/setup_wsl_runners.sh 2`.
6. Check the runners are "Idle" at Settings > Actions > Runners, then set `QUEUE_RUNNER` to `pc`
   (`gh variable set QUEUE_RUNNER --body pc`).

Two runners fit the 8 GB cap: a shard runs one Godot process (about 2.5 GB), and the dataset check's
export peaks near 4.8 GB. More runners need a bigger cap, which is for the director to decide.
The planning runner (`setup_wsl_runners.sh plan`) runs no Godot and needs a few MB.
