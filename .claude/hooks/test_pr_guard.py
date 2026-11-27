"""Tests for .claude/hooks/pr_guard.py on throwaway git repos (no network, no GitHub).

  python3 -I .claude/hooks/test_pr_guard.py
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pr_guard.py")


def sh(cwd, *args):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, (args, r.stdout, r.stderr)
    return r.stdout.strip()


def commit(cwd, name, text, msg):
    with open(os.path.join(cwd, name), "w") as f:
        f.write(text)
    sh(cwd, "git", "add", name)
    sh(cwd, "git", "commit", "-qm", msg)
    return sh(cwd, "git", "rev-parse", "HEAD")


def run(mode, data, env=None):
    r = subprocess.run([sys.executable, HOOK, mode], input=json.dumps(data), capture_output=True,
                       text=True, env={**os.environ, **(env or {})})
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout) if r.stdout.strip() else None


def denied(out):
    return bool(out) and out["hookSpecificOutput"]["permissionDecision"] == "deny"


class Guard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        self.origin = os.path.join(t, "origin.git")
        self.work = os.path.join(t, "work")
        sh(t, "git", "init", "-q", "--bare", "-b", "main", self.origin)
        sh(t, "git", "clone", "-q", self.origin, self.work)
        for k, v in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
            sh(self.work, "git", "config", k, v)
        commit(self.work, "a.txt", "1\n", "base")
        sh(self.work, "git", "push", "-q", "origin", "HEAD:main")
        sh(self.work, "git", "checkout", "-qb", "claude/x")
        commit(self.work, "b.txt", "branch\n", "branch work")

    def tearDown(self):
        self.tmp.cleanup()

    def main_moves(self, text):
        """Another PR lands on main, editing a.txt."""
        other = os.path.join(self.tmp.name, "other")
        sh(self.tmp.name, "git", "clone", "-q", self.origin, other)
        for k, v in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
            sh(other, "git", "config", k, v)
        commit(other, "a.txt", text, "main moves")
        sh(other, "git", "push", "-q", "origin", "HEAD:main")

    def bash(self, command):
        return run("pretool", {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": self.work})

    def test_clean_main_merge_refused_override_allowed(self):
        self.main_moves("1\nmain\n")
        self.assertTrue(denied(self.bash("git merge origin/main")))
        self.assertTrue(denied(self.bash("git fetch origin main && git merge --no-edit FETCH_HEAD")))
        self.assertFalse(denied(self.bash("MERGE_MAIN_OK=1 git merge origin/main")))

    def test_conflicting_main_merge_allowed(self):
        commit(self.work, "a.txt", "branch side\n", "branch edits a")
        self.main_moves("main side\n")
        self.assertFalse(denied(self.bash("git merge origin/main")))

    def test_own_branch_sync_never_refused(self):
        self.main_moves("1\nmain\n")
        sh(self.work, "git", "push", "-q", "origin", "claude/x")
        self.assertFalse(denied(self.bash("git fetch origin claude/x && git merge --no-edit FETCH_HEAD")))
        self.assertFalse(denied(self.bash("git pull")))

    def test_second_push_soon_refused_unless_first_failed_to_land(self):
        self.assertFalse(denied(self.bash("git push -u origin claude/x")))
        # The first push never landed (no remote-tracking branch): pushing again is fine.
        self.assertFalse(denied(self.bash("git push -u origin claude/x")))
        sh(self.work, "git", "push", "-q", "-u", "origin", "claude/x")
        commit(self.work, "c.txt", "more\n", "drip")
        self.assertTrue(denied(self.bash("git push")))
        self.assertFalse(denied(self.bash("PUSH_AGAIN_OK=1 git push")))

    def pr_head(self, number):
        sh(self.work, "git", "push", "-q", "origin", f"HEAD:refs/pull/{number}/head")

    def mcp_merge(self, number, tool="mcp__github__enable_pr_auto_merge"):
        return run("pretool", {"tool_name": tool, "cwd": self.work,
                               "tool_input": {"owner": "o", "repo": "r", "pullNumber": number}})

    def test_merge_of_conflicting_pr_refused(self):
        commit(self.work, "a.txt", "branch side\n", "branch edits a")
        self.pr_head(7)
        self.main_moves("main side\n")
        out = self.mcp_merge(7)
        self.assertTrue(denied(out))
        self.assertIn("a.txt", out["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertTrue(denied(self.bash("gh pr merge 7 --squash")))

    def test_merge_of_clean_pr_allowed(self):
        self.pr_head(8)
        self.main_moves("1\nmain\n")
        self.assertIsNone(self.mcp_merge(8, "mcp__github__merge_pull_request"))

    def transcript(self, calls):
        path = os.path.join(self.tmp.name, "t.jsonl")
        with open(path, "w") as f:
            for name, inp in calls:
                f.write(json.dumps({"message": {"content": [
                    {"type": "tool_use", "name": name, "input": inp}]}}) + "\n")
        return path

    def test_stop_after_push_without_watch_blocked_once(self):
        t = self.transcript([("Bash", {"command": "git push -u origin claude/x"})])
        self.assertEqual(run("stop", {"transcript_path": t})["decision"], "block")
        self.assertIsNone(run("stop", {"transcript_path": t, "stop_hook_active": True}))

    def test_stop_after_subscribe_allowed(self):
        t = self.transcript([("Bash", {"command": "git push"}),
                             ("mcp__claude-code-remote__subscribe_pr_activity", {"pullNumber": 1})])
        self.assertIsNone(run("stop", {"transcript_path": t}))
        t = self.transcript([("mcp__claude-code-remote__subscribe_pr_activity", {"pullNumber": 1}),
                             ("Bash", {"command": "git push"})])
        self.assertEqual(run("stop", {"transcript_path": t})["decision"], "block")

    def test_stop_without_push_allowed(self):
        t = self.transcript([("Bash", {"command": "git status"})])
        self.assertIsNone(run("stop", {"transcript_path": t}))

    def fake_gh(self):
        """A gh on PATH that answers run 1 as a main push, run 2 as a PR run, and fails on others."""
        d = os.path.join(self.tmp.name, "bin")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "gh"), "w") as f:
            f.write('#!/bin/sh\ncase "$2" in\n  */runs/1) echo "push main";;\n'
                    '  */runs/2) echo "pull_request claude/x";;\n  *) exit 1;;\nesac\n')
        os.chmod(os.path.join(d, "gh"), 0o755)
        return {"PATH": d + os.pathsep + os.environ["PATH"]}

    def cancel(self, command=None, run_id=None):
        if command is not None:
            data = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": self.work}
        else:
            data = {"tool_name": "mcp__github__actions_run_trigger", "cwd": self.work, "tool_input": {
                "method": "cancel_workflow_run", "owner": "o", "repo": "r", "run_id": run_id}}
        return run("pretool", data, env=self.fake_gh())

    def test_cancel_of_main_push_run_refused(self):
        self.assertTrue(denied(self.cancel("gh run cancel 1")))
        self.assertTrue(denied(self.cancel("gh api -X POST repos/o/r/actions/runs/1/force-cancel")))
        self.assertTrue(denied(self.cancel(run_id=1)))
        self.assertTrue(denied(self.cancel("gh run cancel 9")))  # unreadable: refused
        self.assertFalse(denied(self.cancel("CANCEL_RUN_OK=1 gh run cancel 1")))

    def test_cancel_of_pr_run_allowed(self):
        self.assertFalse(denied(self.cancel("gh run cancel 2")))
        self.assertIsNone(self.cancel(run_id=2))
        self.assertIsNone(run("pretool", {"tool_name": "mcp__github__actions_run_trigger", "cwd": self.work,
                                          "tool_input": {"method": "rerun_failed_jobs", "run_id": 1}}))

    def gh_for_workflow_pr(self, runs):
        d = os.path.join(self.tmp.name, "bin2")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "gh"), "w") as f:
            f.write('#!/bin/sh\ncase "$2" in\n'
                    '  */pulls/8) echo \'{"head": {"sha": "abc"}, "labels": []}\';;\n'
                    '  */pulls/8/files*) echo \'[{"filename": ".github/workflows/x.yml", "status": "modified"}]\';;\n'
                    f'  */runs*) echo \'{{"total_count": {runs}}}\';;\n  *) exit 1;;\nesac\n')
        os.chmod(os.path.join(d, "gh"), 0o755)
        return {"PATH": d + os.pathsep + os.environ["PATH"]}

    def test_merge_of_unrun_workflow_change_refused(self):
        self.pr_head(8)
        data = {"tool_name": "mcp__github__enable_pr_auto_merge", "cwd": self.work,
                "tool_input": {"owner": "o", "repo": "r", "pullNumber": 8}}
        out = run("pretool", data, env=self.gh_for_workflow_pr(0))
        self.assertTrue(denied(out))
        self.assertIn("x.yml", out["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertIsNone(run("pretool", data, env=self.gh_for_workflow_pr(1)))

    def test_start_outside_cloud_does_nothing(self):
        self.assertIsNone(run("start", {"cwd": self.work}, env={"CLAUDE_CODE_REMOTE": ""}))


if __name__ == "__main__":
    unittest.main(verbosity=1)
