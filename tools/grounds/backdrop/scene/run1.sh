set -e
WORK=${WORK:-/home/user/work}; REPO=${REPO:-$(cd "$(dirname "$0")/../../../.." && pwd)}
g=$1; cd $WORK/proto; P=python3
mkdir -p data/$g/prep out/$g
# the model's own flat ground that the game hides where the backdrop is drawn (GroundModels.BACKDROP_HIDES)
SKIP=$(case $g in barossa|sky|jiangwan|hands|blacktown|summit|macpoint) echo concourse;; waca) echo land road brick;; bruce) echo g_ground;; north_hobart) echo ground;; esac)
cp $WORK/data/$g/osm.json $WORK/data/$g/osm_parts.json data/$g/
$P mkspec2.py $g
L=$($P -c "import json;s=json.load(open('spec/$g.json'));print(s['lat'],s['lon'])")
$P fetch.py $g $L 1 | tail -2
$P sat_fetch.py spec/$g.json 1500 1.0 | tail -1
GLB=$($P -c "import json;print(json.load(open('spec/$g.json'))['glb'])")
$P probe_outline.py -- "$GLB" data/$g/prep/footprint.json $SKIP 2>&1 | grep OUTLINE
$P prep.py spec/$g.json 2>&1 | tail -4
$P bake_ground.py $g 2>&1 | tail -1
rm -f out/$g/scene.blend; $P scene.py -- spec/$g.json 2>&1 | grep -vE "unregister_class|^$" | tail -5
ls -la out/$g/
Y=$($P -c "import json;print(json.load(open('spec/$g.json'))['yaw'])")
mkdir -p $WORK/bd/$g
BG_HULL_SKIP=$(echo $SKIP | tr ' ' ',') BG_YAW=$Y BG_BUDGET=${BG_BUDGET:-800000} BG_VARIANTS=2 BG_SLICE=120000 $P $REPO/tools/grounds/backdrop/reduce.py -- out/$g/scene.blend $WORK/bd/$g/${g}_backdrop.glb ${TEX:-4096} > $WORK/bd/$g/reduce.log 2>&1
tail -3 $WORK/bd/$g/reduce.log; ls -la $WORK/bd/$g
