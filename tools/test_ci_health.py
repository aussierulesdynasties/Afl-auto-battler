"""Checks for tools/ci_health.py's rules on made-up GitHub data, with no network."""
import datetime as dt
import unittest

from ci_health import analyse

NOW = dt.datetime(2026, 11, 27, 12, 0, tzinfo=dt.timezone.utc)


def t(minutes_ago):
    return (NOW - dt.timedelta(minutes=minutes_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(rid, status, branch="b", sha="s1", event="pull_request", age=10, started=None,
        conclusion=None, name="Tests", path=".github/workflows/tests.yml"):
    return {"id": rid, "name": name, "status": status, "conclusion": conclusion, "event": event,
            "path": path,
            "head_branch": branch, "head_sha": sha, "created_at": t(age),
            "run_started_at": t(started if started is not None else age), "html_url": f"u/{rid}"}


def pr(n, branch="b", sha="s1", draft=False, idle_min=10):
    return {"number": n, "title": f"PR {n}", "draft": draft, "updated_at": t(idle_min),
            "html_url": f"p/{n}", "head": {"ref": branch, "sha": sha}}


class CiHealthTests(unittest.TestCase):
    def test_healthy(self):
        out = analyse(NOW, [run(1, "in_progress")], [pr(1)], [run(2, "completed", "main", "m", "push",
                      conclusion="success")], [run(3, "completed", conclusion="success", name="N")])
        self.assertEqual(out, {"problems": [], "cancel": []})

    def test_superseded_and_closed_pr_runs_are_cancelled(self):
        out = analyse(NOW, [run(1, "in_progress", sha="old", age=15), run(2, "queued", branch="gone", age=15)],
                      [pr(1)], [], [])
        self.assertEqual(out["cancel"], [1, 2])
        self.assertIn("newer commits", out["problems"][0])
        self.assertIn("PR is closed", out["problems"][1])

    def test_other_workflows_and_young_runs_are_not_cancelled(self):
        roadmap = run(1, "in_progress", branch="gone", age=30, name="Roadmap close",
                      path=".github/workflows/roadmap_close.yml")
        young = run(2, "queued", sha="old", age=3)
        self.assertEqual(analyse(NOW, [roadmap, young], [pr(1)], [], []), {"problems": [], "cancel": []})

    def test_long_queue_and_long_run(self):
        out = analyse(NOW, [run(1, "queued", age=95), run(2, "in_progress", age=200, started=160),
                            run(3, "queued", age=30)], [pr(1)], [], [])
        self.assertEqual(len(out["problems"]), 2)
        self.assertIn("waited 95 min", out["problems"][0])
        self.assertIn("running 160 min", out["problems"][1])

    def test_ghost_runs_are_ignored(self):
        out = analyse(NOW, [run(1, "queued", event="push", branch="old", age=60 * 24 * 10)], [], [], [])
        self.assertEqual(out["problems"], [])

    def test_red_main_ignores_cancelled_pushes(self):
        tests = [run(1, "completed", "main", "a", "push", conclusion="cancelled"),
                 run(2, "completed", "main", "b", "push", conclusion="failure")]
        self.assertIn("Main is red", analyse(NOW, [], [], tests, [])["problems"][0])
        tests[1]["conclusion"] = "success"
        self.assertEqual(analyse(NOW, [], [], tests, [])["problems"], [])

    def test_red_nightly(self):
        out = analyse(NOW, [], [], [], [run(1, "completed", conclusion="failure", name="N")])
        self.assertIn("nightly", out["problems"][0])

    def test_idle_prs(self):
        prs = [pr(1, "a", "x", idle_min=180), pr(2, "b", "y", idle_min=60 * 25),
               pr(3, "c", "z", draft=True, idle_min=60 * 24 * 4), pr(4, "d", "w", idle_min=30)]
        tests = [run(9, "completed", "a", "x", conclusion="failure"),
                 run(8, "completed", "d", "w", conclusion="failure")]
        probs = analyse(NOW, [], prs, tests, [])["problems"]
        self.assertEqual(len(probs), 3)
        self.assertIn("#1", probs[0]); self.assertIn("is red", probs[0])
        self.assertIn("#2", probs[1]); self.assertIn("is ready", probs[1])
        self.assertIn("#3", probs[2]); self.assertIn("draft", probs[2])


if __name__ == "__main__":
    unittest.main()
