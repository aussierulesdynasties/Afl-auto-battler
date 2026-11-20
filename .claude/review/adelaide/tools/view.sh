# view.sh POS TGT OUT [SUN_AZ] [LENS]: one orbit-camera render at full detail (absolute out path)
D=$(pwd -W); B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
POS=$1 TGT=$2 SUN_AZ=${4:-150} SUN_EL=40 LENS=${5:-35} RW=1600 RH=900 "$B" -b -P tools/render.py -- orbit "$D/$3" 0 0 0 > rend/v.log 2>&1
