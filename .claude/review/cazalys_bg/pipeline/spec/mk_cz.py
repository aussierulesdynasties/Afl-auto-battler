import json
s=json.load(open('spec/peoplefirst.json'))
s.update(name='cazalys',lat=-16.9356941,lon=145.7490634,seed=11,glb='ground/cazalys.glb',paint_poly=[])
P=s['palette']
P.update(ground_default=[118,140,90],lawn=[88,138,58],yard=[106,138,78],spinifex=[60,98,50],far_flat=[96,130,80],far_veg=[46,82,46],far_steep=[40,72,42],haze=[186,202,214])
s['tree_kinds']=['red_gum','paperbark','ghost_gum']
json.dump(s,open('spec/cazalys.json','w'),indent=1)
s=json.load(open('spec/cazalys.json'))
s['tree_kinds']=['raintree','fig','palm','palm','paperbark']
s['far_step_m']=100; s['haze_m']=30000
s['palette'].update(far_flat=[72,104,58],far_veg=[36,66,38],far_steep=[30,58,34],haze=[178,196,206])
json.dump(s,open('spec/cazalys.json','w'),indent=1)
s['facade_atlas']='facades.png'
s['palette'].update(ground_default=[120,138,96],lawn=[92,140,62],yard=[112,140,84],spinifex=[78,112,60])
json.dump(s,open('spec/cazalys.json','w'),indent=1)

s=json.load(open('spec/cazalys.json'))  # applied 2026-11-20 texture-session pass 2 (already in json)
# 2026-11-20 precision pass: commercial land is no longer painted solid 'paved'; aerial_paving.py traces its real lots
s=json.load(open('spec/cazalys.json')); s['cover']=[[k,v,('yard' if v=='commercial|retail|industrial|construction' else pk)] for k,v,pk in s['cover']]; s['aerial_paint']=True
json.dump(s,open('spec/cazalys.json','w'),indent=1)
