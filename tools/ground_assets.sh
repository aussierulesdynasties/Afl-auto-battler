#!/usr/bin/env bash
# The ground models (assets/grounds/: .glb, seat .bin, baked textures) live in a private repo, not in
# this public one, so each rebuild stops adding 20 to 60 MB to its history (docs/GROUND_ASSETS.md).
#
#   tools/ground_assets.sh fetch               # copy the pinned files into place (skips files already right)
#   tools/ground_assets.sh check               # exit 1 unless every pinned file is in place and matches
#   tools/ground_assets.sh publish "msg" [PATH...]
#                                              # commit the working copies of the pinned files (and any new
#                                              # PATHs) to the private repo, push, and update the pin
#
# The pin is tools/ground_assets.lock (repo, branch, commit, a sha256 per file); the .import files stay
# here. Same machinery and token as the Epic files (tools/epic_assets.sh, EPIC_ASSETS_TOKEN).
# GROUND_ASSETS_CACHE (default ~/.cache/ard-ground-assets) holds the private repo's git objects.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
ASSETS_LOCK="$here/ground_assets.lock" \
ASSETS_CACHE="${GROUND_ASSETS_CACHE:-$HOME/.cache/ard-ground-assets}" \
ASSETS_WHAT="ground models" ASSETS_DOC="docs/GROUND_ASSETS.md" ASSETS_TAG="ground assets" \
ASSETS_SCRIPT="$here/ground_assets.sh" \
	exec bash "$here/epic_assets.sh" "$@"
