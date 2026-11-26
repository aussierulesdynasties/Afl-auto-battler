#!/bin/bash
# the Traeger model's build in the cloud (Blender's Python module): stand/club/model prims -> blend -> game glb
set -e
B=/home/user/tools/bpyenv/bin/python
O=${1:-out/b}
python3 stand.py > $O.py.log && python3 standuv.py >> $O.py.log && python3 club.py >> $O.py.log && python3 model.py >> $O.py.log
NO_RENDER=1 $B blend.py -- prims.json cam.json $O.a > $O.blend.log 2>&1
mkdir -p $O.d
$B drop_run.py -- $O.a/traeger.blend $O.d > $O.drop.log 2>&1
$B join_for_game.py -- $O.d/traeger.glb $O.j.glb > $O.join.log 2>&1
$B fix_r14.py -- $O.j.glb $O.r14.glb > $O.r14.log 2>&1
$B fix_r15.py -- $O.r14.glb $O.glb > $O.r15.log 2>&1
echo built $O.glb
