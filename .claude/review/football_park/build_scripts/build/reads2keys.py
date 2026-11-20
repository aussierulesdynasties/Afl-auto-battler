# python reads2keys.py CAM READS.json OUT.json : each edge {pts:[[u,v]..], z:..} -> [[t,d],...] sorted by t
import sys,json
sys.path.insert(0,'../b')
from td import uv2td
p=json.load(open(sys.argv[1]))['p'];R=json.load(open(sys.argv[2]));out={}
for k,e in R.items():
    ks=sorted([[round(float(a),2) for a in uv2td(p,u,v,e['z'])] for u,v in e['pts']])
    out[k]=ks;print(k,e['z'],[(round(t),round(d,1)) for t,d in ks])
json.dump(out,open(sys.argv[3],'w'))
