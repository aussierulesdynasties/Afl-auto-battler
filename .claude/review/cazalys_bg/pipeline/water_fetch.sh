cd "$1"; w=30
for i in 1 2 3 4 5 6; do
 for s in https://overpass-api.de/api/interpreter https://overpass.private.coffee/api/interpreter; do
  curl -s -A "stadium-scene-prototype/0.1" --data-urlencode 'data=[out:json][timeout:180];(relation["natural"="water"](-28.0213,153.3500,-27.9913,153.3842);relation["waterway"="riverbank"](-28.0213,153.3500,-27.9913,153.3842);way["amenity"="parking"](-28.0213,153.3500,-27.9913,153.3842);relation["amenity"="parking"](-28.0213,153.3500,-27.9913,153.3842);way["area:highway"](-28.0213,153.3500,-27.9913,153.3842);way["highway"="pedestrian"]["area"="yes"](-28.0213,153.3500,-27.9913,153.3842););out geom;' $s -o osm_water.json
  head -c 1 osm_water.json | grep -q '{' && { echo OK $s; exit 0; }
 done; sleep $w; w=$((w*2))
done; echo FAIL
