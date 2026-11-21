import json, collections
p='scene.py'; s=open(p,encoding='utf-8',newline='').read()
a=" and float(np.mean(np.asarray(PAL['roofs_flat'][b['roof'] % len(PAL['roofs_flat'])]))) >= 150: kind, RT = 'corr', 7.2"
assert a in s; s=s.replace(a,": kind, RT = 'corr', 7.2")
s=s.replace("w / 2 / 7.2","w / 2 / 3.6").replace("s_[i] / 7.2","s_[i] / 3.6").replace("s_[i + 1] / 7.2","s_[i + 1] / 3.6")
open(p,'w',encoding='utf-8',newline='').write(s)
g=json.load(open('spec/gmhba.json')); g['palette']['court_blue']=[52,66,120]; json.dump(g,open('spec/gmhba.json','w'),indent=1)
R=json.load(open('data/gmhba/prep/roads.json'))
print(collections.Counter((r['hw'],r['oneway']) for r in R if r['hw'] in('trunk','primary','secondary')))
