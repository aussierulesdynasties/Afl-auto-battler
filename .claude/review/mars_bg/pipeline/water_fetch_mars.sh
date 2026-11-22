cd "$1"; w=30; B="-37.5535,143.8299,-37.5245,143.8663"
Q="[out:json][timeout:180];(relation[\"natural\"=\"water\"]($B);relation[\"waterway\"=\"riverbank\"]($B);way[\"amenity\"=\"parking\"]($B);relation[\"amenity\"=\"parking\"]($B);way[\"area:highway\"]($B);way[\"highway\"=\"pedestrian\"][\"area\"=\"yes\"]($B);relation[\"leisure\"]($B);relation[\"landuse\"]($B););out geom;"
for i in 1 2 3 4 5 6; do
 for s in https://overpass-api.de/api/interpreter https://overpass.private.coffee/api/interpreter; do
  curl -s -A "stadium-scene-prototype/0.1" --data-urlencode "data=$Q" $s -o osm_water.json
  head -c 1 osm_water.json | grep -q '{' && { echo OK $s; exit 0; }
 done; sleep $w; w=$((w*2))
done; echo FAIL
