#!/usr/bin/env bash
# Sets up N GitHub Actions runners for the merge queue inside WSL (Ubuntu), each its own
# systemd service running as the unprivileged user "runner". Run as root inside WSL:
#
#   sudo REG_TOKEN=<token> bash tools/ci_runner/setup_wsl_runners.sh [N]
#
# REG_TOKEN is a repository registration token (valid one hour):
#   gh api -X POST repos/aussierulesdynasties/Afl-auto-battler/actions/runners/registration-token -q .token
# Every runner gets the label "afl-queue"; tests.yml sends its jobs there while the repo variable
# QUEUE_RUNNER is "pc", except pull requests from forks.
# The runner is github.com/actions/runner (MIT licence); it updates itself.
set -euo pipefail
N="${1:-6}"
REPO_URL="https://github.com/aussierulesdynasties/Afl-auto-battler"
VER="2.338.2"   # GitHub refuses runners older than 2.329.0; they update themselves after
: "${REG_TOKEN:?set REG_TOKEN to a registration token}"
[ "$(id -u)" = 0 ] || { echo "run as root (sudo)"; exit 1; }
grep -q '^systemd=true' /etc/wsl.conf 2>/dev/null || {
	echo "WSL needs systemd: add '[boot]' and 'systemd=true' to /etc/wsl.conf, run 'wsl --shutdown' in Windows, then run this again"; exit 1; }
apt-get update -qq
apt-get install -y -qq curl unzip git python3 zstd ca-certificates libicu-dev >/dev/null
id runner >/dev/null 2>&1 || useradd -m -s /bin/bash runner
cd /home/runner
[ -f "runner-$VER.tar.gz" ] || curl -sSL -o "runner-$VER.tar.gz" \
	"https://github.com/actions/runner/releases/download/v$VER/actions-runner-linux-x64-$VER.tar.gz"
for i in $(seq 1 "$N"); do
	d="/home/runner/r$i"
	if [ -f "$d/.runner" ]; then echo "r$i already configured"; continue; fi
	mkdir -p "$d" && tar -xzf "runner-$VER.tar.gz" -C "$d" && chown -R runner:runner "$d"
	sudo -u runner "$d/config.sh" --unattended --url "$REPO_URL" --token "$REG_TOKEN" \
		--name "$(hostname)-afl-$i" --labels afl-queue --work _work --replace
	(cd "$d" && ./svc.sh install runner && ./svc.sh start)
done
echo "Done: $N runners. Check them at $REPO_URL/settings/actions/runners"
