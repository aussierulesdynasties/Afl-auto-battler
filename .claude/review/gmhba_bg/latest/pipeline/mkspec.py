import json
s=json.load(open('spec/mcg.json'))
s.update(name='gmhba',lat=-38.158219,lon=144.354577,glb='../glb/gmhba.glb',near_half_m=1500,tree_r_m=1500,clear_r_m=150,landmarks=[],rail_geo=True)
s.pop('rail_cut',None)
s['tree_kinds']=['elm','red_gum','plane']
json.dump(s,open('spec/gmhba.json','w'),indent=1)
s=json.load(open('spec/gmhba.json'))
W=[(2470,0),(2470,25),(2560,30),(2600,45),(2640,55),(2650,90),(2665,110),(2700,125),(2750,150),(2800,175),(2850,190),(2900,195),(3000,195),(3000,0)]
s['paint_poly']=[['water',[[px-1500,1500-py] for px,py in W]]]
s['cover'].append(['natural','beach|sand','sand'])
json.dump(s,open('spec/gmhba.json','w'),indent=1)
