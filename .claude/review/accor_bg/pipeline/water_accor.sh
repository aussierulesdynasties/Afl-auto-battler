cd "$1"; w=30
for i in 1 2 3 4 5 6; do
 for s in https://overpass-api.de/api/interpreter https://overpass.private.coffee/api/interpreter; do
  curl -s -A "stadium-scene-prototype/0.1" --data-urlencode 'data=[out:json][timeout:180];(relation["natural"="water"](-33.8622,151.0453,-33.8322,151.0813);relation["waterway"="riverbank"](-33.8622,151.0453,-33.8322,151.0813);way["amenity"="parking"](-33.8622,151.0453,-33.8322,151.0813);relation["amenity"="parking"](-33.8622,151.0453,-33.8322,151.0813);way["area:highway"](-33.8622,151.0453,-33.8322,151.0813);way["highway"="pedestrian"]["area"="yes"](-33.8622,151.0453,-33.8322,151.0813););out geom;' $s -o osm_water.json
  head -c 1 osm_water.json | grep -q '{' && { echo OK $s; exit 0; }
 done; sleep $w; w=$((w*2))
done; echo FAIL
