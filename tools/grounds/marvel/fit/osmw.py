import sys,glob,json
sys.path.insert(0,'/home/user/Afl-auto-battler/tools/grounds/marvel')
import surrounds as S
fs=sorted(glob.glob('/tmp/marvel_surrounds_*.osm'))
water=[];pier=[]
for f in fs:
    tr,ways=S.load(f,[])
    for t,p in ways:
        if len(p)<3:continue
        if t.get('natural')=='water' or t.get('waterway')=='riverbank' or t.get('natural')=='coastline' or t.get('place')=='sea':water.append(p)
        if t.get('man_made') in('pier','jetty') or t.get('_id') in S.LANDMARK_WAYS:pier.append((t.get('man_made'),t.get('_id'),p))
json.dump(dict(water=water,pier=[(a,b,p) for a,b,p in pier]),open('osm_w.json','w'))
print(len(water),len(pier))
