import json
f='prep.py'; s=open(f,newline='').read()
a="skin = [tuple(H)] + [pol(29.0, a0 + math.radians(x)) for x in np.linspace(-45, 45, 24)]"; assert a in s
s=s.replace(a,"skin = [tuple(H)] + [pol(18.44 * math.cos(math.radians(x)) + math.sqrt(29.0 ** 2 - (18.44 * math.sin(math.radians(x))) ** 2), a0 + math.radians(x)) for x in np.linspace(-45, 45, 31)]   # grass line: 29 m arc round the mound, out to the foul lines",1)
open(f,'w',newline='').write(s)
f='build.sh'; s=open(f,newline='').read()
a='data/$g/prep/footprint.json 2>&1 | grep OUTLINE'; assert a in s
nl='\r\n' if '\r\n' in s else '\n'
s=s.replace(a, a+nl+'  TB=$(C:/Python314/python.exe -E -c "import json;print(\' \'.join(json.load(open(\'spec/$g.json\')).get(\'trim_base\',[])))"); if [ -n "$TB" ]; then "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P probe_outline.py -- "$GLB" data/$g/prep/fence_outline.json $TB 2>&1 | grep OUTLINE; fi',1)
open(f,'w',newline='').write(s)
f='spec/traeger.json'; d=json.load(open(f))
d['paint_at']=[[-69,167,"turf_blue"],[98,88,"court_blue"],[111,82,"court_blue"],[116,53,"court_blue"],[129,47,"court_blue"]]
d['trim_base']=["ground_dirt"]
json.dump(d,open(f,'w'),indent=1)
print('ok')
