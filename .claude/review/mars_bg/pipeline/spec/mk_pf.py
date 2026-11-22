import json
m=json.load(open('spec/mcg.json'))
s={k:m[k] for k in m if k not in ('rail_cut','rail_geo','landmarks')}
s.update(name='peoplefirst',lat=-28.0063139,lon=153.3671007,seed=7,clear_r_m=150,near_half_m=1500,tree_r_m=1500,street_trees=12,glb='ground/peoplefirst.glb',haze_m=18000,road_mesh=True)
P=s['palette']
P.update(ground_default=[120,138,96],lawn=[92,140,62],yard=[112,140,84],spinifex=[78,112,60],sand=[214,200,166],water=[58,96,98],
 road=[78,80,80],path=[196,190,176],paved=[184,182,174],parking=[96,96,94],
 walls_house=[[236,232,220],[214,204,182],[196,170,136],[226,222,212]],
 walls_block=[[232,230,222],[204,198,184],[184,190,196],[214,206,190]],
 walls_tower=[[226,228,226],[150,176,190],[96,124,140],[206,200,188]],
 roofs_house=[[176,96,66],[108,112,112],[206,206,198],[146,80,58],[78,84,90]],
 roofs_flat=[[222,224,220],[176,178,176],[150,152,150]],
 far_flat=[112,134,92],far_veg=[66,98,58],far_steep=[60,88,56],haze=[190,204,216],sky_top=[64,124,192],sky_hor=[196,212,226])
s['cover']=m['cover']+[['natural','wetland','spinifex'],['leisure','golf_course','lawn']]
s['tree_kinds']=['red_gum','paperbark','ghost_gum']
s['levels_default'].update({'*':5,'house':4.5,'residential':4.5,'detached':4.5,'apartments':12,'commercial':8,'office':14,'retail':7,'industrial':8,'warehouse':9,'school':7,'stadium':24})
json.dump(s,open('spec/peoplefirst.json','w'),indent=1)
