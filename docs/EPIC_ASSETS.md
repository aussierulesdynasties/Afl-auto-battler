# Epic and MetaHuman files

MetaHuman is the 3D players' body and is a final decision. This page is only about using it the way
Epic's licence allows: **MetaHuman files, and anything made from them, never sit as raw files in this
public repo.** They live in a private repo and are copied in when you build, test or work.

## What is private

`tools/epic_assets.lock` lists every file (33 today) with its sha256, and pins one commit of the
private repo (`gabebartolo-spec/ard-asset-pipeline`, branch `epic-assets`, same paths as here):

| Files | What they are |
| --- | --- |
| `assets/oval3d/player_mh.glb` | the MetaHuman footballer body (with the clips) |
| `assets/oval3d/crew_mh.glb` | umpire, trainer and runner clothes cut from that body's surface |
| `assets/oval3d/cuts/*.res` (19) | each club's guernsey cut from that body |
| `assets/oval3d/skin/*.png` (6) | MetaHuman skin maps (colour, normal, roughness) for head and body |
| `assets/oval3d/heads/MEL_11, MEL_37, MEL_41` (`.glb` and `_tex.jpg`) | MetaHuman heads (Chandler, Cross) |

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
anyone can download them from those commits. Removing them means rewriting history and force-pushing
main and every branch, which cannot be undone. It is the director's call; nothing below has run.

The plan, step by step:

1. **Freeze.** Every Claude thread and PC worktree pushes its work (or saves a patch); the merge queue
   is emptied; no thread pushes until step 7.
2. **Rewrite** on the director's PC (his credentials), in a fresh mirror clone:
   `git clone --mirror https://github.com/aussierulesdynasties/Afl-auto-battler purge.git`, then
   `grep -oE '^[0-9a-f]{40}' tools/epic_blobs.txt > ids.txt` and
   `git -C purge.git filter-repo --strip-blobs-with-ids ../ids.txt` (pip `git-filter-repo`). Only those
   45 file versions go; every other file and every commit message stays. Check: `git -C purge.git
   rev-list --objects --all | grep -Ff ids.txt` prints nothing.
3. **Allow the force-push:** in the ruleset "main merge queue" (id 27075439) add a bypass for the push, or
   switch it off for the minutes of step 4 (only the director can).
4. **Push:** `git -C purge.git push --force origin 'refs/heads/*:refs/heads/*'` (405 branches; open PRs
   follow their rewritten branches). Restore the ruleset.
5. **GitHub Support:** the 2,029 `refs/pull/*` refs are GitHub's and cannot be pushed; about 360 of them
   (PRs from #1722 on) still point at old commits. Ask Support ("Removing sensitive data from a
   repository") to dereference them and run garbage collection, listing the affected PRs.
6. **CI:** turn on the history check in the lint job (`python3 -I tools/check_epic_files.py --commits
   origin/main..HEAD`, with `fetch-depth: 0`), so a branch that still carries the old history fails.
7. **Every clone starts again:** each PC worktree and cloud thread re-clones (or `git fetch` and
   rebases its own commits onto the new main: trees are identical, only commit ids changed). A stale
   branch merged and pushed would put the files back.

The repo has no forks (checked 2026-11-23).
