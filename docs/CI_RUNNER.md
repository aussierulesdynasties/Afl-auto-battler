# Merge-queue runners on the director's PC

The merge queue spent most of its time waiting for GitHub's free runners (2026-11-22: median
128 minutes from a group's start to its verdict, with about 9 jobs running at once across every
PR). Merge-queue groups and pushes to main can run on runners on the director's PC instead
(Ryzen 7 9700X, Windows, in WSL Ubuntu). Pull requests always stay on GitHub's runners.

## Safety

- The repo is public. Only `merge_group` and `push` (to main) jobs go to the PC. Both run code that
  someone with write access already queued or merged. A pull request's jobs, including a fork's, never
  reach the PC (`runs-on` in `.github/workflows/tests.yml`).
- Settings > Actions > General > "Approval for running fork pull request workflows from contributors":
  "Require approval for all external contributors".
- Each runner is a systemd service in WSL, running as the unprivileged Linux user `runner`, not as a
  Windows admin. It only sees the files WSL gives it.
- The switch is the repo variable `QUEUE_RUNNER`. With `pc`, the queue uses the PC. With anything
  else, or unset, it uses GitHub's runners. Turn it off before the PC is off for long, or queued jobs
  wait until it comes back.

## Setup (once)

1. Windows, as admin: `wsl --install -d Ubuntu` (reboot if asked), then create the Ubuntu user.
2. In Ubuntu: add `[boot]` / `systemd=true` to `/etc/wsl.conf`; in Windows, `wsl --shutdown`.
3. `%UserProfile%\.wslconfig`: `[wsl2]`, `vmIdleTimeout=-1` and `memory=` about 70% of the PC's RAM,
   so WSL stays up with nobody logged in to it. Then `wsl --shutdown` again.
4. Task Scheduler: at log on, run `wsl.exe -d Ubuntu --exec sleep infinity` (hidden), which starts WSL
   and its runner services when Windows starts.
5. In Ubuntu, in a clone of this repo: get a registration token
   (`gh api -X POST repos/aussierulesdynasties/Afl-auto-battler/actions/runners/registration-token -q .token`,
   needs a repo admin) and run `sudo REG_TOKEN=<token> bash tools/ci_runner/setup_wsl_runners.sh 6`.
6. Check the six runners are "Idle" at Settings > Actions > Runners, then set `QUEUE_RUNNER` to `pc`
   (`gh variable set QUEUE_RUNNER --body pc`).

Six runners suit an 8-core CPU: a shard runs one Godot process. Raise or lower N to match.
