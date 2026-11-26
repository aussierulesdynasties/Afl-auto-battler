#!/usr/bin/env python3
"""Claude Code hooks that enforce this repo's PR rules instead of only writing them down.

Each rule here was broken over and over in PRs #1994 to #2189 (thread "Find why sessions mishandle
PRs", 2026-11-26). Prose in CLAUDE.md did not stop it, so these hooks do:

  pretool   (PreToolUse)
    - merge or auto-merge of a PR that conflicts with main: refused, with the files. GitHub can never
      land it, and arming auto-merge on it only burns a test run.
    - `git merge`/`git pull` of main into a branch that merges cleanly: refused. Pull-request CI
      already tests the branch merged with current main; a clean sync only re-runs the whole CI
      (286 merges of main in 105 merged PRs). Override: MERGE_MAIN_OK=1 in the command, when the
      branch needs code that is only on main.
    - a second `git push` of the same branch within PUSH_GAP_MIN minutes: refused. Each push cancels
      the run the last push started (337 pushes after opening in 105 merged PRs). Override:
      PUSH_AGAIN_OK=1 in the command, once the earlier run has finished or failed.
    - cancelling a Tests run on main's push event (gh run cancel, the actions/runs cancel APIs, the
      GitHub MCP cancel_workflow_run): refused. Main runs one push at a time and keeps only the
      newest waiting one, so a running main run is always worth finishing; 25 of 35 main runs were
      cancelled by hand on 25-26 Nov, some after every job had passed. A run whose event and branch
      can't be read is refused too. Override: CANCEL_RUN_OK=1 in the command.
    - merge or auto-merge of a PR that changes a workflow under .github/workflows with no successful
      run of that workflow on the PR's head commit: refused. A workflow is only proven by running
      it: pr_cap.yml (#2186) passed review and CI, then failed live on every PR open because its gh
      commands needed a token scope MERGE_TOKEN lacks. Run it from the branch (workflow_dispatch,
      `gh workflow run <file> --ref <branch>`) and link the green run. A workflow with no trigger
      that can run from a branch: label the PR workflow-untestable and say why in its body.
  stop      (Stop)
    - ending a turn after a push with nothing armed to wake the session when CI finishes: blocked
      once. A cloud session that just ends its turn never hears that its run went red.
  start     (SessionStart)
    - a cloud session (CLAUDE_CODE_REMOTE=true) gets Godot and gdlint, so it can run the suites
      before pushing instead of using CI as its test runner, and the repo's pre-push hook.

Every check fails open: if git or the network errors, the tool call goes ahead.
"""
import json
import os
import re
import subprocess
import sys
import time

PUSH_GAP_MIN = 20
GIT_TIMEOUT = 120

PUSH_RE = re.compile(r"\bgit\s+(?:-C\s+\S+\s+)?push\b")
MERGE_RE = re.compile(r"\bgit\s+(?:-C\s+\S+\s+)?(merge|pull)\b([^;&|\n]*)")
GH_MERGE_RE = re.compile(r"\bgh\s+pr\s+merge\s+#?(\d+)")
WATCH_TOOLS = {
    "mcp__claude-code-remote__subscribe_pr_activity",
    "mcp__claude-code-remote__send_later",
    "mcp__claude-code-remote__create_trigger",
    "ScheduleWakeup",
    "CronCreate",
    "Monitor",
}
WATCH_BASH_RE = re.compile(r"\bgh\s+(run\s+watch|pr\s+checks\b[^\n]*--watch)")
MERGED_TOOLS = {"mcp__github__merge_pull_request"}
CANCEL_RE = re.compile(r"\bgh\s+run\s+cancel\s+(\d+)|actions/runs/(\d+)/(?:force-)?cancel\b")
REPO = "aussierulesdynasties/Afl-auto-battler"


def git(cwd, *args, timeout=GIT_TIMEOUT):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=timeout)


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))
    sys.exit(0)


def merge_conflicts(cwd, base, head):
    """Files that conflict when head merges onto base; [] when clean; None when git can't tell."""
    r = git(cwd, "merge-tree", "--write-tree", "--name-only", "--no-messages", base, head)
    if r.returncode not in (0, 1) and git(cwd, "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        git(cwd, "fetch", "-q", "--unshallow", "--filter=blob:none", "origin", "main", timeout=300)
        r = git(cwd, "merge-tree", "--write-tree", "--name-only", "--no-messages", base, head)
    if r.returncode == 0:
        return []
    if r.returncode == 1:
        return sorted({l for l in r.stdout.splitlines()[1:] if l.strip()})
    return None


def gh_json(path):
    try:
        r = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=30)
        return json.loads(r.stdout) if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None


def check_workflows_proven(number, repo):
    pr = gh_json(f"repos/{repo}/pulls/{number}")
    files = gh_json(f"repos/{repo}/pulls/{number}/files?per_page=100")
    if not pr or files is None:
        return
    if any(l.get("name") == "workflow-untestable" for l in pr.get("labels", [])):
        return
    sha = pr.get("head", {}).get("sha", "")
    changed = sorted({f["filename"].split("/")[-1] for f in files
                      if f.get("status") != "removed" and f["filename"].startswith(".github/workflows/")
                      and f["filename"].endswith((".yml", ".yaml"))})
    unproven = []
    for wf in changed:
        runs = gh_json(f"repos/{repo}/actions/workflows/{wf}/runs?head_sha={sha}&status=success&per_page=1")
        if runs is not None and not runs.get("total_count"):
            unproven.append(wf)
    if unproven:
        deny(f"PR #{number} changes {', '.join(unproven)} and none of them has a successful run on its "
             f"head commit {sha[:9]}. Run each from the branch first (`gh workflow run <file> --ref "
             "<branch>`, or the event it listens to), check it went green, and link the run in the PR. "
             "pr_cap.yml merged on green CI and then failed live on every PR. If a workflow cannot "
             "run from a branch, label the PR workflow-untestable and say why. (.claude/hooks/pr_guard.py)")


def check_pr_merge(cwd, number, repo=REPO):
    if git(cwd, "fetch", "-q", "--filter=blob:none", "origin", "main",
           f"+refs/pull/{number}/head:refs/claude-guard/pr-{number}").returncode != 0:
        return
    files = merge_conflicts(cwd, "origin/main", f"refs/claude-guard/pr-{number}")
    if files:
        shown = ", ".join(files[:12]) + (f" and {len(files) - 12} more" if len(files) > 12 else "")
        deny(f"PR #{number} conflicts with main in: {shown}. It cannot merge, and auto-merge on it "
             "never fires, so arming it only wastes a test run. Merge origin/main into the branch, "
             "resolve, run the touched suites, push once, then merge. (.claude/hooks/pr_guard.py)")
    check_workflows_proven(number, repo)


FETCH_RE = re.compile(r"\bgit\s+(?:-C\s+\S+\s+)?fetch\s+(?:-\S+\s+)*origin\s+([^\s;&|]+)")


def main_target(cwd, args, before):
    """True when a `git merge`/`git pull` brings main in. `before` is the command text ahead of it,
    so `git fetch origin <branch> && git merge FETCH_HEAD` is judged by what that fetch names."""
    words = args.split()
    if any(w in ("origin/main", "main", "refs/remotes/origin/main") for w in words):
        return True
    if "FETCH_HEAD" in words:
        fetched = FETCH_RE.findall(before)
        if fetched:
            return fetched[-1].split(":")[0] in ("main", "refs/heads/main")
        head = git(cwd, "rev-parse", "--git-path", "FETCH_HEAD").stdout.strip()
        try:
            first = open(head if os.path.isabs(head) else os.path.join(cwd, head)).readline()
        except OSError:
            return False
        return "branch 'main' of" in first
    return False


def check_main_merge(cwd, verb, args, command, before):
    if "MERGE_MAIN_OK=1" in command or "--abort" in args or "--continue" in args:
        return
    if not main_target(cwd, args, before):
        return
    branch = git(cwd, "branch", "--show-current").stdout.strip()
    if branch in ("", "main"):
        return
    if git(cwd, "fetch", "-q", "--filter=blob:none", "origin", "main").returncode != 0:
        return
    if merge_conflicts(cwd, "HEAD", "origin/main") == []:
        deny(f"main merges cleanly into {branch}, so this `git {verb}` is not needed: pull-request CI "
             "already tests your branch merged with current main, and a sync only re-runs the whole "
             "CI. Merge main only when it conflicts (GitHub says DIRTY) or the branch needs code that "
             "is only on main; then prefix the command with MERGE_MAIN_OK=1. (.claude/hooks/pr_guard.py)")


def push_log_path(cwd):
    common = git(cwd, "rev-parse", "--git-common-dir").stdout.strip()
    if not common:
        return None
    return os.path.join(cwd, common) if not os.path.isabs(common) else common


def check_push(cwd, command):
    if "--delete" in command or "--tags" in command or " -d " in command:
        return
    branch = git(cwd, "branch", "--show-current").stdout.strip()
    common = push_log_path(cwd)
    if not branch or branch == "main" or not common:
        return
    path = os.path.join(common, "claude-push-log.json")
    try:
        log = json.load(open(path))
    except (OSError, ValueError):
        log = {}
    now = time.time()
    last = log.get(branch) or {}
    if not isinstance(last, dict):
        last = {}
    # The last push counts only if it landed: the remote-tracking branch is at the sha it pushed.
    landed = last.get("sha") and git(cwd, "rev-parse", "-q", "--verify",
                                     f"refs/remotes/origin/{branch}").stdout.strip() == last["sha"]
    if landed and now - last.get("t", 0) < PUSH_GAP_MIN * 60 and "PUSH_AGAIN_OK=1" not in command:
        mins = int((now - last["t"]) / 60)
        deny(f"You pushed {branch} {mins} min ago. Another push now cancels the CI run that push "
             f"started and puts the branch at the back of the runner queue. Batch your commits and "
             f"push once. If that run already finished or failed, prefix the command with "
             f"PUSH_AGAIN_OK=1. (.claude/hooks/pr_guard.py)")
    log[branch] = {"t": now, "sha": git(cwd, "rev-parse", "HEAD").stdout.strip()}
    try:
        json.dump(log, open(path, "w"))
    except OSError:
        pass


def run_event(run_id, repo):
    """(event, head_branch) of an Actions run, or None when gh can't read it."""
    try:
        r = subprocess.run(["gh", "api", f"repos/{repo}/actions/runs/{run_id}", "--jq",
                            '.event + " " + .head_branch'], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    parts = r.stdout.split()
    return tuple(parts) if r.returncode == 0 and len(parts) == 2 else None


def check_cancel(run_id, repo, command=""):
    if "CANCEL_RUN_OK=1" in command:
        return
    info = run_event(run_id, repo)
    if info and not (info[0] == "push" and info[1] == "main"):
        return
    what = "is a Tests run on a push to main" if info else "could not be read (it may be a push run on main)"
    deny(f"Run {run_id} {what}. Main runs one push at a time and keeps only the newest waiting push "
         "on its own, so cancelling it throws away a run that may have passed and leaves main "
         "untested; it never starts your own run sooner. Let it finish. If a run really must go, "
         "ask the director, then prefix the command with CANCEL_RUN_OK=1. (.claude/hooks/pr_guard.py)")


def pretool(data):
    tool = data.get("tool_name", "")
    inp = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    if tool in ("mcp__github__merge_pull_request", "mcp__github__enable_pr_auto_merge"):
        if inp.get("pullNumber"):
            repo = f"{inp.get('owner')}/{inp.get('repo')}" if inp.get("owner") else REPO
            check_pr_merge(cwd, int(inp["pullNumber"]), repo)
        return
    if tool == "mcp__github__actions_run_trigger":
        if inp.get("method") == "cancel_workflow_run" and inp.get("run_id"):
            repo = f"{inp.get('owner')}/{inp.get('repo')}" if inp.get("owner") else REPO
            check_cancel(int(inp["run_id"]), repo)
        return
    if tool != "Bash":
        return
    command = inp.get("command", "")
    for m in CANCEL_RE.finditer(command):
        rm = re.search(r"repos/([^/\s]+/[^/\s]+)/actions/runs", command)
        check_cancel(int(m.group(1) or m.group(2)), rm.group(1) if rm else REPO, command)
    m = GH_MERGE_RE.search(command)
    if m:
        check_pr_merge(cwd, int(m.group(1)))
    for m in MERGE_RE.finditer(command):
        check_main_merge(cwd, m.group(1), m.group(2), command, command[:m.start()])
    if PUSH_RE.search(command):
        check_push(cwd, command)


def tool_uses(transcript):
    """(name, input) of every tool call in the transcript, in order."""
    out = []
    try:
        with open(transcript, encoding="utf-8") as f:
            for line in f:
                if '"tool_use"' not in line:
                    continue
                try:
                    msg = json.loads(line).get("message") or {}
                except ValueError:
                    continue
                for c in msg.get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        out.append((c.get("name", ""), c.get("input") or {}))
    except OSError:
        pass
    return out


def is_push(name, inp):
    if name == "Bash":
        cmd = inp.get("command", "")
        return bool(PUSH_RE.search(cmd)) and "--delete" not in cmd and "NO_CI_WATCH=1" not in cmd
    return name in ("mcp__github__push_files", "mcp__github__create_or_update_file")


def is_watch(name, inp):
    if name in WATCH_TOOLS or name in MERGED_TOOLS:
        return True
    return name == "Bash" and bool(WATCH_BASH_RE.search(inp.get("command", "")))


def stop(data):
    if data.get("stop_hook_active"):
        return
    calls = tool_uses(data.get("transcript_path") or "")
    last_push = max((i for i, (n, x) in enumerate(calls) if is_push(n, x)), default=-1)
    if last_push < 0:
        return
    last_watch = max((i for i, (n, x) in enumerate(calls) if is_watch(n, x)), default=-1)
    if last_watch > last_push:
        return
    print(json.dumps({"decision": "block", "reason":
        "You pushed, and nothing will wake you when CI finishes, so a red run would sit unnoticed "
        "until the director asks. Before ending the turn: subscribe to the PR's activity "
        "(mcp__claude-code-remote__subscribe_pr_activity, load it with ToolSearch), or schedule a "
        "check-in, or watch the run (`gh pr checks <n> --watch`). If the push has no PR and no CI, "
        "say so and end the turn. (.claude/hooks/pr_guard.py)"}))


def start(data):
    if os.environ.get("CLAUDE_CODE_REMOTE") != "true":
        return
    root = data.get("cwd") or os.getcwd()
    top = git(root, "rev-parse", "--show-toplevel").stdout.strip() or root
    notes = []
    if os.path.exists(os.path.join(top, "tools/hooks/pre-push")):
        git(top, "config", "core.hooksPath", "tools/hooks")
    have_godot = subprocess.run("command -v godot", shell=True, capture_output=True).returncode == 0
    if not have_godot:
        r = subprocess.run(["bash", os.path.join(top, ".claude/hooks/install_godot.sh")],
                           capture_output=True, text=True, timeout=240)
        notes.append(r.stdout.strip() or r.stderr.strip()[-300:])
    else:
        notes.append("Godot is on PATH.")
    notes.append("Run the touched suites (tools/run_tests.sh <suite>) before you push; CI is not your "
                 "test runner. After a push, subscribe to the PR's activity so a red run wakes you.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                             "additionalContext": " ".join(n for n in notes if n)}}))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    try:
        {"pretool": pretool, "stop": stop, "start": start}.get(mode, lambda d: None)(data)
    except subprocess.TimeoutExpired:
        pass
