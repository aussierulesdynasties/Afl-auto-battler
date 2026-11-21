# Build Accor Stadium (row 202 2b)

Session local_9b7c5f35, worktree `.claude/worktrees/dazzling-margulis-e47fa0`.

## Where the work is now

Model on PR #1921 (glb 886fb1e8).

---

## The session's handoff file (verbatim, C-Users-DANTE-Documents-GitHub-Afl-auto-battler-claude-worktrees-dazzling-margulis-e47fa0.md)

# Handoff: Accor Stadium ground model (row 202 2b)

### State
Pickup: taken (C:/Users/DANTE/Documents/GitHub/Afl-auto-battler/.claude/worktrees/dazzling-margulis-e47fa0)
working: background task bgcpa5o6k (rebuild with clustered roof dark bays, blue-grey ribbed side facade, tower disc caps; then top + 8 GE views + proofs). 3c0fa6a4 stale; bg-accor told; send it the new md5 the moment it lands (lead says reply now, overrides 3am lock). Photos: .claude/review/accor/ref/gimg (urls.txt, img/, SOURCES.txt), surround 14 valid (exclude 100, 105). Ruling: READY needs a side-by-side board per part (render at photo angle + named photo, MATCH/FAIL per region). PR with auto-merge OFF (lead 11-21). Not committed.

### Task
Build Accor Stadium from scratch per ground_builder_rules.md (shared notes folder local_64d97632-…). READY to ground lead local_6e4c78c4-058b-47c9-8f00-8696d4de4f2b with HEAD == ls-remote and "no open faults", then PR ("Part of row 202" on its own line), auto-merge OFF per lead 2026-11-21.

### Where things are
- Worktree dazzling-margulis-e47fa0, branch claude/dazzling-margulis-e47fa0. Work in tools/grounds/accor/ (untracked) + Oval3D.gd seat_aqua/seat_teal colours.
- Overlays ge/top within ~2 m; signs, fins, canopy, pylons, towers matched.
- Latest fixes: ramp texture tiles 4x per drum (helix closes); ramp bands pale grey (200,198,192) not beige; the red-paver apron was reverted: 'paving' is the inner field apron, and the model has no outer forecourt. proofs.py: seat template renamed T->TM (it overwrote the camera target T and broke orbit). Ship jobs need accor.glb + *.bin copied into the out dir.
- Proofs in render/proof (facade_*, join_*, seatcu_*, sign_*, turntable_*). Contact sheets in scratchpad cs0-cs6.

### Next
1. When bxhalyz0k ends: read facade close-ups (no streaks), md5, then git add tools/grounds/accor + Oval3D.gd, commit, push.
2. (seatcu renamed to west: done.) Texture-vs-photo crops + stddev list. Board in .claude/review/accor/.
3. Send bg-accor local_5dca6420 the new md5. Merge origin/main, commit, push, HEAD == ls-remote, READY to lead, PR.

### Gotchas
- proofs.py needs an ABSOLUTE out dir. Exit traceback from addon.py is harmless.
- GE cams: l = 520 m / 65° / fovy 35, tz 5. l090 shows the WEST facade.
- Chrome port 9433 mine, 9417 another session's.
