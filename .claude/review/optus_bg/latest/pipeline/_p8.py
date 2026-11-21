import json
s=open('landmarks.py',encoding='utf-8').read();a=open('_pav.txt').read()
if 'opt_pav' not in s: s=s.replace('# build: one object per material',a+'# build: one object per material',1)
open('landmarks.py','w',encoding='utf-8',newline='').write(s)
p='spec/optus.json';j=json.load(open(p));L=j.setdefault('landmarks',[])
if 'opt_pav' not in L: L.append('opt_pav')
print(L);json.dump(j,open(p,'w'),indent=1)
