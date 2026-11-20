# OSM outlines in the Cazaly's local frame (x east, y north, metres from the pitch centroid) -> work/osm_xy.json
import sys,os,json,xml.etree.ElementTree as ET;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import geo
R=ET.parse('osm/cazalys.osm').getroot();N={n.get('id'):(float(n.get('lat')),float(n.get('lon'))) for n in R.iter('node')}
W={w.get('id'):[nd.get('ref') for nd in w.iter('nd')] for w in R.iter('way')}
keep={'614183155':'pitch','614183153':'stadium','614183154':'stand_w','311996699':'bldg_sw','311996705':'bldg_s','311996779':'bldg_w',
 '1080461478':'bldg_n1','1080461479':'bldg_se','1080461480':'bldg_n2','1080461481':'bldg_nw'}
r=lambda p:[round(float(t),2) for t in geo.ll2xy(*p)]
out={k:[r(N[n]) for n in W[i]] for i,k in keep.items()}
json.dump(out,open('work/osm_xy.json','w'),indent=0);print({k:len(v) for k,v in out.items()})
