"""Which open pull requests will conflict: each with main, and each pair in either landing order.

The director's rule (2026-11-13): test landing orders with `git merge-tree` before arming PRs
that share a file. This does it for every open, non-draft PR at once, with no checkout and no
working-tree change (git merge-tree --write-tree only writes objects).

  python3 tools/pr_conflicts.py                 # fetch the open PRs and report
  python3 tools/pr_conflicts.py --no-fetch      # use the refs already fetched
  python3 tools/pr_conflicts.py --json          # machine-readable, for the workflow

For a pair A, B it lands A on main, then B on that result (and the other way round), so a
conflict that only appears once the first PR has merged is caught. Exit 0 always: a conflict
is a report, not a failure; the PR owner resolves it.
"""
import argparse
import json
import subprocess
import sys


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode not in (0, 1):
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r


def merge(base_tree_commit, head):
    """Merges head onto base. Returns (tree or None, conflicted files)."""
    r = git("merge-tree", "--write-tree", "--name-only", "--no-messages", base_tree_commit, head)
    lines = r.stdout.splitlines()
    tree = lines[0] if lines else None
    if r.returncode == 0:
        return tree, []
    return None, sorted(set(l for l in lines[1:] if l.strip()))


def commit_of(tree, parent):
    """A throwaway commit for a merged tree, so the next merge has a base (objects only)."""
    return git("commit-tree", tree, "-p", parent, "-m", "pr_conflicts landing").stdout.strip()


MARK = "<!-- pr-conflicts "


def message(n, base, with_main, pairs, title):
    """The comment for PR n, or "" when it has no conflict. Names files, never the commit, so a
    new main that leaves the same conflicts posts nothing new."""
    lines = []
    if n in with_main:
        lines.append(f"- **Conflicts with main now:** {', '.join(f'`{f}`' for f in with_main[n])}. "
                     "Merge `origin/main` and resolve; it cannot merge (and auto-merge never fires) until then.")
    for c in pairs:
        if n not in (c["a"], c["b"]):
            continue
        other = c["b"] if n == c["a"] else c["a"]
        mine_first = c["a_first"] if n == c["a"] else c["b_first"]
        theirs_first = c["b_first"] if n == c["a"] else c["a_first"]
        when = ("whichever lands second" if mine_first and theirs_first
                else ("if this PR lands first" if mine_first else f"if #{other} lands first"))
        lines.append(f"- **Conflicts with #{other}** ({title.get(other, '')[:60]}) {when}: "
                     f"{', '.join(f'`{f}`' for f in c['files'])}. The PR that lands second resolves it; "
                     "removing the overlap before both are queued avoids a dropped queue entry.")
    return "\n".join(lines)


def post_comments(repo, base, prs, with_main, pairs, title):
    """One comment per PR whose conflict list changed since the last one this posted; an older
    one is deleted so the thread keeps only the current list. A PR whose conflicts cleared gets
    its comment edited to say so (no new notification)."""
    import hashlib
    slug = repo or subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                                  capture_output=True, text=True, check=True).stdout.strip()

    def api(*a, body=None):
        cmd = ["gh", "api", *a]
        r = subprocess.run(cmd + (["--input", "-"] if body is not None else []),
                           input=json.dumps(body) if body is not None else None,
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"warning: gh api {' '.join(a)}: {r.stderr.strip()}", file=sys.stderr)
            return None
        return json.loads(r.stdout) if r.stdout.strip() else {}

    for p in prs:
        n = p["number"]
        text = message(n, base, with_main, pairs, title)
        digest = hashlib.sha1(text.encode()).hexdigest()[:12] if text else "clear"
        old = [c for c in (api(f"repos/{slug}/issues/{n}/comments?per_page=100") or [])
               if c.get("body", "").startswith(MARK)]
        last = old[-1]["body"][len(MARK):].split(" ", 1)[0] if old else None
        if digest == last or (digest == "clear" and not old):
            continue
        if digest == "clear":
            api(f"repos/{slug}/issues/comments/{old[-1]['id']}", "-X", "PATCH",
                body={"body": f"{MARK}clear -->\nLanding-order check (tools/pr_conflicts.py): "
                              f"no conflicts with main `{base[:9]}` or any open PR now."})
            continue
        for c in old:
            api(f"repos/{slug}/issues/comments/{c['id']}", "-X", "DELETE")
        api(f"repos/{slug}/issues/{n}/comments", "-X", "POST",
            body={"body": f"{MARK}{digest} -->\nLanding-order check against main `{base[:9]}` "
                          f"(tools/pr_conflicts.py, `git merge-tree`):\n{text}"})
        print(f"commented on #{n}")


def open_prs(repo):
    cmd = ["gh", "pr", "list", "--state", "open", "--limit", "200", "--json", "number,headRefName,isDraft,title"]
    if repo:
        cmd += ["--repo", repo]
    return [p for p in json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
            if not p["isDraft"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="")
    ap.add_argument("--base", default="main")
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--comment", action="store_true",
                    help="post one comment on each PR whose conflicts changed since its last one (the workflow)")
    args = ap.parse_args()

    prs = open_prs(args.repo)
    refs = {p["number"]: f"refs/remotes/origin/{p['headRefName']}" for p in prs}
    if not args.no_fetch:
        specs = [f"+refs/heads/{args.base}:refs/remotes/origin/{args.base}"]
        specs += [f"+refs/heads/{p['headRefName']}:{refs[p['number']]}" for p in prs]
        git("fetch", "-q", "--no-tags", "origin", *specs)
    base = git("rev-parse", f"refs/remotes/origin/{args.base}").stdout.strip()

    with_main, landed = {}, {}
    for p in prs:
        n = p["number"]
        if git("rev-parse", "-q", "--verify", refs[n], check=False).returncode != 0:
            continue
        tree, files = merge(base, refs[n])
        if files:
            with_main[n] = files
        else:
            landed[n] = commit_of(tree, base)

    pairs = []
    nums = sorted(landed)
    for i, a in enumerate(nums):
        for b in nums[i + 1:]:
            _, ab = merge(landed[a], refs[b])
            _, ba = merge(landed[b], refs[a])
            if ab or ba:
                pairs.append({"a": a, "b": b, "files": sorted(set(ab) | set(ba)),
                              "a_first": bool(ab), "b_first": bool(ba)})

    title = {p["number"]: p["title"] for p in prs}
    if args.json:
        print(json.dumps({"base": base, "prs": len(prs), "with_main": with_main, "pairs": pairs}, indent=1))
        return 0
    if args.comment:
        post_comments(args.repo, base, prs, with_main, pairs, title)
    print(f"{len(prs)} open ready PRs against {args.base} {base[:9]}")
    for n, files in sorted(with_main.items()):
        print(f"  #{n} conflicts with {args.base} now: {', '.join(files)}  ({title[n][:50]})")
    for c in pairs:
        order = "either order" if c["a_first"] and c["b_first"] else ("when #%d lands first" % (c["a"] if c["a_first"] else c["b"]))
        print(f"  #{c['a']} x #{c['b']} conflict {order}: {', '.join(c['files'])}")
    if not with_main and not pairs:
        print("  no conflicts with main or between any pair")
    return 0


if __name__ == "__main__":
    sys.exit(main())
