# Ground models

The stadium models, seat files and baked textures in `assets/grounds/<slug>/` are not committed to
this repo. They live in the private repo `gabebartolo-spec/ard-asset-pipeline`, on the branch
`ground-assets`, at the same paths. Godot's `.import` file for each one stays here.

Why (director, 2026-11-26): every rebuild of a ground added another 20 to 60 MB to this repo's
history for good. `marvel.glb` alone had 24 versions. Old model versions were 1.3 GB of a 7 GB history,
and they grew by about 800 MB a week. Git LFS was ruled out because its free tier's 10 GB a month of
downloads would run out after a few CI checkouts.

## Working with them

- `tools/ground_assets.sh fetch` copies the pinned files into place. It takes seconds when nothing
  has changed, and skips files that are already right. `tools/run_tests.sh` and
  `tools/export_builds.sh` run it for you, and so does every CI job that uses the
  `.github/actions/epic-assets` action.
- **Changed a ground, or added a new one?** Build it into `assets/grounds/<slug>/` as before. Then run
  `tools/ground_assets.sh publish "why" [NEW PATH...]` and commit the `tools/ground_assets.lock` that
  it updates. You only need to name paths that are new: every path already pinned is re-published
  from your working copy. Also commit the new `.import` files. Never `git add -f` a model:
  `assets/grounds/.gitignore` ignores everything but `.import` files, and the CI lint job
  (`tools/check_epic_files.py`) fails if a model gets committed.
- Two open PRs that both publish ground changes will conflict on the lock. Merge main in, run
  `tools/ground_assets.sh publish` again, and commit the new lock.
- Access works the same way as for the Epic files: your own GitHub sign-in, or `EPIC_ASSETS_TOKEN`.
  CI uses that same secret. A cloud Claude session attaches `gabebartolo-spec/ard-asset-pipeline`
  first.
- The lock pins one commit and a sha256 per file (`repo`, `branch`, `commit` lines, then
  `sha256  path`). `tools/ground_assets_diff.py BASE HEAD` lists the ground files whose pin changed,
  which is how ground-shots works out which grounds a PR touched. `tools/select_suites.py` runs the
  ground suites when the lock changes, and `tools/ground_packs/export.sh` names packs by the pinned
  hashes.

## History

Old versions are still in this repo's git history until the planned one-off rewrite, which will be
done together with the Epic purge (docs/EPIC_ASSETS.md).
