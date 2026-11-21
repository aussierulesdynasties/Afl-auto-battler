f='build.sh'; s=open(f,newline='').read()
a='fence_mask.py -- "$GLB" data/$g/prep/fence_mask.npy $TB 2>&1 | grep MASK; fi'; assert a in s
s=s.replace(a,'fence_mask.py -- "$GLB" data/$g/prep/fence_polys.json $TB 2>&1 | grep POLYS; C:/Python314/python.exe -E fence_mask.py data/$g/prep/fence_polys.json data/$g/prep/fence_mask.npy; fi',1)
open(f,'w',newline='').write(s); print('ok')
