import json
m=json.load(open('spec/peoplefirst.json'))
s=dict(m)
s.update(name='accor',lat=-33.847086,lon=151.063400,seed=11,clear_r_m=170,near_half_m=1500,tree_r_m=1500,street_trees=12,glb='ground/accor.glb',haze_m=18000,road_mesh=True)
s.pop('paint_poly',None); s.pop('trim_base',None)
P=s['palette']
P.update(ground_default=[132,140,100],lawn=[100,138,70],yard=[118,138,88],water=[62,92,96],
 walls_house=[[224,214,196],[198,170,140],[176,120,96],[226,222,212]],
 roofs_house=[[150,86,66],[96,100,104],[196,196,190],[128,74,58],[70,76,84]],
 far_veg=[70,96,62],haze=[194,204,214])
s['tree_kinds']=['red_gum','paperbark','ghost_gum']
s['levels_default'].update({'house':4.5,'apartments':24,'office':30,'hotel':40,'stadium':40})
json.dump(s,open('spec/accor.json','w'),indent=1)
# Olympic Park forecourt pavers, traced on the satellite (sat_1km.jpg px -> m)
def _m(p): return [round((p[0]*2000/1400-1000)*0.5,1), round(-(p[1]*2000/1400-1000)*0.5,1)]
_pl=[(440,0),(700,0),(1060,700),(1120,790),(560,1040),(460,880),(450,690),(500,560),(590,440),(680,330),(680,210),(620,130),(440,110)]
s['paint_poly']=[['paved',[_m(p) for p in _pl]]]
P['paved']=[129,112,104]; P['paved_pavers']=[129,112,104]; P['tower_steel']=[176,188,198]
json.dump(s,open('spec/accor.json','w'),indent=1)
s['extra_py']=['accor_towers.py','accor_landmarks.py','accor_halls.py','accor_annex.py']; s['pave_tile_m']=40.0; s['pave_rot_deg']=-52.5   # boulevard axis, measured on the satellite tower rows
json.dump(s,open('spec/accor.json','w'),indent=1)
