# OSM outlines in the Accor local frame (x east, y north, metres from the OSM centroid of way 4385777) -> work/osm_xy.json
import sys,os,json;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import geo
D=json.load(open('osm/accor.json',encoding='utf-8'));N={e['id']:(e['lat'],e['lon']) for e in D['elements'] if e['type']=='node'}
W={e['id']:e for e in D['elements'] if e['type']=='way'}
keep={4385777:'stadium',119389038:'arch_w',119389039:'arch_e'}
r=lambda p:[round(float(t),2) for t in p]
out={v:[r(geo.ll2xy(*N[n])) for n in W[k]['nodes'][:-1]] for k,v in keep.items()}
json.dump(out,open('work/osm_xy.json','w',newline=''),indent=0)
print({k:len(v) for k,v in out.items()})
