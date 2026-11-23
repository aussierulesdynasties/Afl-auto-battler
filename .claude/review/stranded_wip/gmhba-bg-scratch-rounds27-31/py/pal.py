import json,sys
s=json.load(open(sys.argv[1]))
for k in ('walls_tower','walls_block','far_flat','far_veg','haze'): print(k,s.get(k))
