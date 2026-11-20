# OSM outlines in the Riverway local frame (x east, y north, metres from the pitch centroid) -> work/osm_xy.json
import sys,os,json;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import geo
D=json.load(open('osm/riverway.json',encoding='utf-8'));N={e['id']:(e['lat'],e['lon']) for e in D['elements'] if e['type']=='node'}
W={e['id']:e for e in D['elements'] if e['type']=='way'}
keep={175599085:'pitch',175599089:'stadium'}
r=lambda p:[round(float(t),2) for t in geo.ll2xy(*p)]
out={k:[r(N[n]) for n in W[i]['nodes']] for i,k in keep.items()}
out['towers']=[r((e['lat'],e['lon'])) for e in D['elements'] if e['type']=='node' and e.get('tags',{}).get('tower:type')=='lighting']
json.dump(out,open('work/osm_xy.json','w'),indent=0);print({k:len(v) for k,v in out.items()})
