#!/usr/bin/env python3
"""CI health check: finds stuck or wasted CI runs and idle PRs, and reports them on one issue.

Run by .github/workflows/ci_health.yml (every 2 hours, after pushes to main, and on demand).
It used to be a scheduled task on one Claude account (2026-11-26); it lives here so it runs
whichever account, session or person works on the repo.

What it checks (thresholds below):
  - runs waiting for a runner for over QUEUED_MIN minutes
  - runs going for over RUNNING_MIN minutes (no job here should take that long)
  - pull request Tests runs at least 10 min old that test a commit the PR has moved past, or a
    closed PR, and still hold runners (the PR's head is read again just before): force-cancelled (safe cleanup, director's standing rule 2026-11-26), then reported
  - main: the newest finished push run of Tests failed
  - the newest nightly long-suite run failed
  - open ready PRs whose newest Tests run failed and that nobody has touched for RED_IDLE_H hours
  - open ready PRs untouched for STALE_READY_H hours, drafts untouched for STALE_DRAFT_D days

When anything is found it opens (or updates) one issue titled ISSUE_TITLE; when everything is
healthy again it closes that issue with a comment. Known noise is skipped: run records older than
7 days (repo_hygiene.yml deletes them; GitHub refuses to cancel them), and a cancelled main push
run (pushes to main keep only the newest waiting run on purpose).

Usage: GH_TOKEN=... GH_REPO=owner/name [THROTTLE_MIN=60] python3 tools/ci_health.py [--dry-run]
  --dry-run prints the report and changes nothing (no cancels, no issue).
Stdlib only, so the job needs no install step.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request

QUEUED_MIN = 90
RUNNING_MIN = 150
RED_IDLE_H = 2
STALE_READY_H = 24
STALE_DRAFT_D = 3
GHOST_DAYS = 7
MIN_AGE_CANCEL = 10
ISSUE_TITLE = "CI health check: problems found"
TESTS = "Tests"
NIGHTLY = "Nightly long suites"


def parse_t(s: str) -> dt.datetime:
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)


def minutes(a: dt.datetime, b: dt.datetime) -> int:
    return int((b - a).total_seconds() // 60)


class Api:
    def __init__(self, token: str, repo: str):
        self.token, self.repo = token, repo

    def call(self, method: str, path: str, body: dict | None = None):
        url = path if path.startswith("https://") else f"https://api.github.com/repos/{self.repo}/{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else None

    def pages(self, path: str, key: str | None = None, limit: int = 5) -> list:
        out = []
        sep = "&" if "?" in path else "?"
        for page in range(1, limit + 1):
            got = self.call("GET", f"{path}{sep}per_page=100&page={page}")
            items = got[key] if key else got
            out += items
            if len(items) < 100:
                break
        return out


def analyse(now: dt.datetime, active_runs: list, prs: list, recent_tests: list, nightly: list) -> dict:
    """Pure: returns {'problems': [str], 'cancel': [run ids]} from the fetched data."""
    problems: list[str] = []
    cancel: list[int] = []
    open_heads = {p["head"]["ref"]: p["head"]["sha"] for p in prs}

    for r in active_runs:
        created = parse_t(r["created_at"])
        age = minutes(created, now)
        if age > GHOST_DAYS * 24 * 60:
            continue
        label = f'{r["name"]} run [{r["id"]}]({r["html_url"]}) on `{r["head_branch"]}`'
        # Only Tests runs: other workflows run on a closed PR on purpose (Roadmap close runs after
        # a merge). Young runs are left alone: the PR list may be a moment older than the run.
        if (r["event"] == "pull_request" and r.get("path", "").endswith("/tests.yml") and age >= MIN_AGE_CANCEL
                and open_heads.get(r["head_branch"]) != r["head_sha"]):
            cancel.append(r["id"])
            why = "its PR is closed" if r["head_branch"] not in open_heads else "its PR has newer commits"
            problems.append(f"{label} was still {r['status'].replace('_', ' ')} although {why}: force-cancelled.")
            continue
        if r["status"] in ("queued", "waiting", "requested", "pending") and age > QUEUED_MIN:
            problems.append(f"{label} has waited {age} min for a runner.")
        elif r["status"] == "in_progress":
            started = parse_t(r.get("run_started_at") or r["created_at"])
            ran = minutes(started, now)
            if ran > RUNNING_MIN:
                problems.append(f"{label} has been running {ran} min (stuck, or cancelled but still holding runners).")

    main_done = [r for r in recent_tests
                 if r["event"] == "push" and r["head_branch"] == "main" and r["status"] == "completed"
                 and r["conclusion"] != "cancelled"]
    if main_done and main_done[0]["conclusion"] not in ("success", "skipped"):
        r = main_done[0]
        problems.append(f'Main is red: Tests run [{r["id"]}]({r["html_url"]}) on {r["head_sha"][:7]} '
                        f'ended {r["conclusion"]}. Every PR that touches the same suites will fail until it is fixed.')

    nightly_done = [r for r in nightly if r["status"] == "completed" and r["conclusion"] != "cancelled"]
    if nightly_done and nightly_done[0]["conclusion"] not in ("success", "skipped"):
        r = nightly_done[0]
        problems.append(f'The newest nightly long-suite run [{r["id"]}]({r["html_url"]}) ended {r["conclusion"]}.')

    newest_pr_run: dict[str, dict] = {}
    for r in recent_tests:
        if r["event"] == "pull_request" and r["status"] == "completed":
            newest_pr_run.setdefault(r["head_sha"], r)
    for p in prs:
        idle_h = minutes(parse_t(p["updated_at"]), now) / 60
        tag = f'PR [#{p["number"]}]({p["html_url"]}) "{p["title"][:70]}"'
        if p["draft"]:
            if idle_h > STALE_DRAFT_D * 24:
                problems.append(f"{tag} is a draft nobody has touched for {int(idle_h // 24)} days.")
            continue
        run = newest_pr_run.get(p["head"]["sha"])
        if run and run["conclusion"] == "failure" and idle_h > RED_IDLE_H:
            problems.append(f"{tag} is red ([run]({run['html_url']})) and nobody has touched it for {int(idle_h)} h.")
        elif idle_h > STALE_READY_H:
            problems.append(f"{tag} is ready but nobody has touched it for {int(idle_h)} h.")
    return {"problems": problems, "cancel": cancel}


def report_issue(api: Api, problems: list[str], now: dt.datetime, run_url: str) -> str:
    issues = api.pages("issues?state=open&creator=github-actions%5Bbot%5D", limit=2)
    mine = [i for i in issues if i["title"] == ISSUE_TITLE and "pull_request" not in i]
    if not problems:
        for i in mine:
            api.call("POST", f'issues/{i["number"]}/comments',
                     {"body": f"Healthy again at {now:%Y-%m-%d %H:%M} UTC ([check]({run_url})). Closing."})
            api.call("PATCH", f'issues/{i["number"]}', {"state": "closed", "state_reason": "completed"})
        return f"healthy; closed {len(mine)} issue(s)" if mine else "healthy"
    body = (f"Found by the CI health check at {now:%Y-%m-%d %H:%M} UTC ([check]({run_url})). "
            "This issue is rewritten on every check and closed when everything is healthy.\n\n"
            + "\n".join(f"- {p}" for p in problems)
            + "\n\nHow it decides: `tools/ci_health.py`. Workflow: `.github/workflows/ci_health.yml`.")
    if mine:
        api.call("PATCH", f'issues/{mine[0]["number"]}', {"body": body})
        return f'updated issue #{mine[0]["number"]}'
    made = api.call("POST", "issues", {"title": ISSUE_TITLE, "body": body})
    return f'opened issue #{made["number"]}'


def main() -> int:
    dry = "--dry-run" in sys.argv
    token, repo = os.environ.get("GH_TOKEN", ""), os.environ.get("GH_REPO", "")
    if not token or not repo:
        print("GH_TOKEN and GH_REPO are needed", file=sys.stderr)
        return 2
    api = Api(token, repo)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    own_run = os.environ.get("GITHUB_RUN_ID")
    throttle = int(os.environ.get("THROTTLE_MIN") or 0)
    if throttle:
        # After a push to main: skip when a check already finished in the last THROTTLE_MIN minutes.
        last = api.call("GET", "actions/workflows/ci_health.yml/runs?status=success&per_page=3")["workflow_runs"]
        last = [r for r in last if str(r["id"]) != own_run and r["event"] != "pull_request"]
        if last and minutes(parse_t(last[0]["created_at"]), now) < throttle:
            print(f"Skipped: the last check ran under {throttle} min ago ({last[0]['html_url']}).")
            return 0
    active = []
    for st in ("queued", "in_progress", "waiting"):
        active += api.pages(f"actions/runs?status={st}", key="workflow_runs", limit=3)
    active = [r for r in active if str(r["id"]) != own_run]
    prs = api.pages("pulls?state=open", limit=3)
    recent_tests = api.pages("actions/workflows/tests.yml/runs?", key="workflow_runs", limit=2)
    nightly = api.call("GET", "actions/workflows/nightly.yml/runs?per_page=10")["workflow_runs"]

    found = analyse(now, active, prs, recent_tests, nightly)
    # Read each cancel candidate's PR head again, so a push made while this ran never loses its run.
    owner = repo.split("/")[0]
    keep = []
    for r in [r for r in active if r["id"] in found["cancel"]]:
        now_heads = api.call("GET", f'pulls?state=open&head={owner}:{r["head_branch"]}')
        if any(p["head"]["sha"] == r["head_sha"] for p in now_heads):
            keep.append(r["id"])
    if keep:
        found["cancel"] = [i for i in found["cancel"] if i not in keep]
        found["problems"] = [p for p in found["problems"] if not any(f"[{i}]" in p for i in keep)]
    for p in found["problems"]:
        print(f"- {p}")
    if not found["problems"]:
        print("Healthy: nothing stuck, main and the nightly green, no idle PRs.")
    if dry:
        print("(dry run: nothing cancelled, no issue written)")
        return 0
    for rid in found["cancel"]:
        try:
            api.call("POST", f"actions/runs/{rid}/force-cancel")
        except urllib.error.HTTPError as e:
            print(f"force-cancel {rid} failed: HTTP {e.code}")
    run_url = f'https://github.com/{repo}/actions/runs/{own_run}' if own_run else "local"
    print(report_issue(api, found["problems"], now, run_url))
    return 0


if __name__ == "__main__":
    sys.exit(main())
