import json,sys
p=sys.argv[1]; s=json.load(open(p)); pal=s['palette']
pal['court_blue']=[96,104,126]; pal['netball']=[66,81,114]
json.dump(s,open(p,'w'),indent=1)
