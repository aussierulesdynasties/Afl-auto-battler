set -e
WORK=${WORK:-/home/user/work}; REPO=${REPO:-$(cd "$(dirname "$0")/../../../.." && pwd)}
g=$1; cd $WORK/proto; P=python3
mkdir -p data/$g/prep out/$g
# the model's own flat ground that the game hides where the backdrop is drawn (GroundModels.BACKDROP_HIDES)
SKIP=$(case $g in blacktown) echo concourse_far detail detail_far surfaces;; barossa|sky|jiangwan|hands|summit|macpoint) echo concourse;; waca) echo land road brick;; bruce) echo g_ground;; north_hobart) echo ground;; esac)
cp $WORK/data/$g/osm.json $WORK/data/$g/osm_parts.json data/$g/
$P mkspec2.py $g
if $P -c "import json,sys;sys.exit(0 if json.load(open('spec/$g.json')).get('dem_nsw') else 1)"; then [ -f data/$g/dem_nsw_near.npy ] || $P dem_nsw.py spec/$g.json; fi
L=$($P -c "import json;s=json.load(open('spec/$g.json'));print(s['lat'],s['lon'])")
$P fetch.py $g $L 1 | tail -2
$P sat_fetch.py spec/$g.json 1500 1.0 | tail -1
GLB=$($P -c "import json;print(json.load(open('spec/$g.json'))['glb'])")
$P probe_outline.py -- "$GLB" data/$g/prep/footprint.json $SKIP 2>&1 | grep OUTLINE
$P prep.py spec/$g.json 2>&1 | tail -4
$P cars.py spec/$g.json 2>&1 | tail -1
$P roofplant.py spec/$g.json 2>&1 | tail -1
$P bake_ground.py $g 2>&1 | tail -1
rm -f out/$g/scene.blend; $P scene.py -- spec/$g.json 2>&1 | grep -vE "unregister_class|^$" | tail -5
ls -la out/$g/
Y=$($P -c "import json;print(json.load(open('spec/$g.json'))['yaw'])")
mkdir -p $WORK/bd/$g
BG_CAMS="$(python3 -c "import json,sys;x=json.load(open(sys.argv[1])).get(sys.argv[2]);print(json.dumps(x) if x else '')" $REPO/tools/grounds/backdrop/scene/broadcast_cams.json $g)" BG_KEEP_TREES=${BG_REAL:+1} BG_HULL_SKIP=${HULL_SKIP:-$(case $g in blacktown) echo detail,fence,roofs,seat,stands,towers,concourse_far;; *) echo $SKIP | tr ' ' ',';; esac)} BG_YAW=$Y BG_BUDGET=${BG_BUDGET:-$([ -n "$BG_REAL" ] && echo 1600000 || echo 800000)} BG_VARIANTS=2 BG_SLICE=120000 $P $REPO/tools/grounds/backdrop/reduce.py -- out/$g/scene.blend $WORK/bd/$g/${g}_backdrop.glb ${TEX:-4096} ${NEAR_R:-350} ${MID_KEEP:-0.4} ${FAR_KEEP:-0.15} > $WORK/bd/$g/reduce.log 2>&1
tail -3 $WORK/bd/$g/reduce.log; ls -la $WORK/bd/$g
