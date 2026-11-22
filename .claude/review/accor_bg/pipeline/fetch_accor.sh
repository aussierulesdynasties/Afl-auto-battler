cd "D:/Temp/claude/9cde8b3442051ee1/8e9d400c-05c9-4bcc-aeef-038762663b40/scratchpad/proto"; PY=C:/Python314/python.exe
$PY -E fetch.py accor -33.84722 151.06333 1800 2>&1 | tail -2
cp data/accor/osm.json data/accor/osm_orig.json
sed 's/-28.0213,153.3500,-27.9913,153.3842/-33.8622,151.0453,-33.8322,151.0813/g' water_fetch.sh > water_accor.sh; bash water_accor.sh "$PWD/data/accor"; $PY -E osm_merge.py accor
$PY -E sat_fetch.py spec/accor.json 1500 0.5 2>&1 | tail -1
curl -s -o ../msbf_accor.csv.gz "$(grep ',311230132,' ../msbf_links.csv | cut -d, -f3)"; $PY -E msbf_cut.py spec/accor.json ../msbf_accor.csv.gz
echo FETCH_DONE
