# Epic and MetaHuman files

MetaHuman is the 3D players' body and is a final decision. This page is only about using it the way
Epic's licence allows: **MetaHuman files, and anything made from them, never sit as raw files in this
public repo.** They live in a private repo and are copied in when you build, test or work.

## What is private

`tools/epic_assets.lock` lists every file (35 today) with its sha256, and pins one commit of the
private repo (`gabebartolo-spec/ard-asset-pipeline`, branch `epic-assets`, same paths as here):

| Files | What they are |
| --- | --- |
| `assets/oval3d/player_mh.glb` | the MetaHuman footballer body (with the clips) |
| `assets/oval3d/crew_mh.glb` | umpire, trainer and runner clothes cut from that body's surface |
| `assets/oval3d/cuts/*.res` (19) | each club's guernsey cut from that body |
| `assets/oval3d/skin/*.png` (6) | MetaHuman skin maps (colour, normal, roughness) for head and body |
| `assets/oval3d/heads/MEL_11, MEL_37, MEL_41` (`.glb` and `_tex.jpg`) | MetaHuman heads (Chandler, Cross) |
| `assets/oval3d/injury_clips.glb`, `assets/oval3d/crowd_set.res` | Mixamo motion (injuries) and Mixamo crowd bodies: Mixamo allows them in a game but not shared as raw files, so they are private too (2026-11-28) |

Their `.import` files stay here (Godot's import settings only). Measurements we took from the body
(`player_mh_builds.json` joint offsets, `heads/socket.json` neck ring) are numbers, not Epic's art, and
stay public. The Tripo heads, MPFB body and crew, hair, guernsey art and turf are not Epic's
(`tools/epic_guard_allow.txt` says where each came from).

## Working with them

- `tools/epic_assets.sh fetch` copies the pinned files into place (seconds; skips files already right).
  `tools/run_tests.sh` and `tools/export_builds.sh` run it for you; an export refuses to go on without them.
- Access: your own GitHub sign-in (the director's PC), or `EPIC_ASSETS_TOKEN`. A cloud Claude session
  attaches `gabebartolo-spec/ard-asset-pipeline` first. CI passes the repo secret `EPIC_ASSETS_TOKEN`
  (falling back to `MERGE_TOKEN`) through `.github/actions/epic-assets`, in every job that draws 3D.
  The files are never cached or uploaded raw by CI; only built games carry them.
- Changed one (a new guernsey cut, a rebuilt body)? `tools/epic_assets.sh publish "why"` commits the
  working copies to the private repo, pushes and updates the pin; commit `tools/epic_assets.lock`.
  A new Epic-derived file: `tools/epic_assets.sh publish "why" PATH...` also adds it to `assets/oval3d/.gitignore` (or the root one for a path elsewhere).
- `tools/check_epic_files.py` (CI lint job) fails if a pinned path, anything in `cuts/` or `skin/`, a
  MetaHuman-named model, a glb naming MetaHuman parts inside, a byte-for-byte copy of any Epic file this
  repo ever held (`tools/epic_blobs.txt`) or an undeclared model or texture under `assets/oval3d/` is
  committed.

## What Epic's licence says (read 2026-11-23)

[metahuman.com/license](https://www.metahuman.com/license?lang=en-US): "MetaHuman is included as part of
your standard Unreal Engine license, meaning it's free to use for anyone making under $1 million USD in
revenue" and "MetaHumans can be used with any engine or creative software."

The Unreal Engine EULA it points to ([unrealengine.com/eula/unreal](https://www.unrealengine.com/eula/unreal))
is behind a bot check from the cloud, so the text below is Epic's own published PDF of the EULA,
version 18.1 of 2023 ([cdn2.unrealengine.com](https://cdn2.unrealengine.com/unreal-engine-end-user-license-agreement-18-1-a8e14000e547.pdf)).
The live page may have changed since; read it on the PC to confirm. That version also predates
MetaHuman joining the engine licence (2025), so reading MetaHuman as "Licensed Technology" follows
metahuman.com's own words, not a clause that names MetaHuman.

- **Section 3:** "Any Product that you Distribute that incorporates Licensed Technology must incorporate
  the Licensed Technology only in object code and only as an inseparable part of the Product."
  A built game (APK, exe, web pack) is that. A public repo of raw `.glb`/`.png` files is not.
- **Section 4:** "You may only Distribute Licensed Technology (including as modified by you) outside of a
  Product as expressly permitted by this Section 4", and its permissions are only to other Unreal
  licensees (engine code), Examples, and code snippets. So MetaHuman files, and files made from them
  ("as modified by you"), may not be shared raw with the public.
- **Section 3(a)(i):** no royalty for "asset files, such as character models and animations ... that you
  developed using the Engine Code, including in Products that use or rely on other video game engines".
  The Royalty Addendum also never applies under US$1,000,000 gross per product, and its release form
  (unrealengine.com/release) is only for a product that will generate royalty-bearing revenue.
- **Section 3(c):** end users may use it only inside the product, "pursuant to an end user license
  agreement that explicitly disclaims any representations, warranties, conditions, and liabilities related
  to the Licensed Technology".
- **Section 6(a), credits:** "If a Product you develop under this Agreement has credits", it must carry
  "[Product name] uses Unreal® Engine. Unreal® is a trademark or registered trademark of Epic Games, Inc.
  in the United States of America and elsewhere." and "Unreal® Engine, Copyright 1998 – xxxx, Epic Games,
  Inc. All rights reserved." The game has no credits screen today; when it gets one, these lines go in.

Not settled from the cloud: the MetaHuman FAQ answers (they load only in a browser), including its AI
question. Our face fit reads player photos, not MetaHuman files.

## The old copies in git history

Moving the files out stops new copies; every commit since #1722 (2026-11-16) still holds them, and
anyone can download them from those commits. The director chose to purge them (2026-11-23). It
rewrites history and force-pushes main and every branch, which cannot be undone.

1. **Freeze.** Every Claude thread and PC worktree pushes its work (or saves a patch); the merge queue
   is emptied; nobody pushes until step 6.
2. **Rewrite:** `tools/epic_purge.sh rewrite WORKDIR` (needs `pip install git-filter-repo`). It clones
   every branch (not GitHub's `refs/pull/*`), strips the blob ids in `tools/epic_blobs.txt` (47 today)
   plus any other version of a pinned file, or of a file in `cuts/` or `skin/`, found on any branch at
   the time (a branch opened since the list was written; it names them for the list), keeps every commit and message, and checks that no
   listed blob is left and that no branch tip changed except by losing an Epic file.
   Every commit id changes, back to the first (filter-repo drops GitHub's signatures on its squash
   merges), but every tree, message, author and date stays. Dry run 2026-11-23 on a copy of all 410
   branches: 43 s; 3,786 commits before and after; no Epic blob left; 214 tips differ from before only
   by the Epic files; the push test refused a branch moved after the clone and left it untouched.
3. **Push:** `tools/epic_purge.sh push WORKDIR`, signed in as a repository admin (main's ruleset lets an
   admin bypass; otherwise switch the rule off for the push). Each branch is pushed with a lease on the
   value it had when cloned, so a branch pushed to since then is refused and listed, never lost. Open
   PRs follow their rewritten branches.
4. **GitHub Support:** the `refs/pull/*` refs are GitHub's and cannot be pushed; the ones from #1722 on
   still point at old commits. Ask Support ("Removing sensitive data from a repository") to dereference
   them and run garbage collection, listing the affected PRs.
5. **CI:** turn on the history check in the lint job (`python3 -I tools/check_epic_files.py --commits
   origin/main..HEAD`, with `fetch-depth: 0`), so a branch that still carries the old history fails.
6. **Every clone starts again:** each PC worktree and cloud thread re-clones (or fetches and rebases its
   own commits onto the new main: trees are identical, only commit ids changed). A stale branch merged
   and pushed would put the files back.

The repo has no forks (checked 2026-11-23).
