p='prep.py';s=open(p,newline='').read();N='\r\n' if '\r\n' in s else '\n'
a="    cls = 'tower' if h >= 25 else ('house' if (A < 350 and h < 9) else 'block')"
assert s.count(a)==1
s=s.replace(a,a+N+"    if t.get('tower:type') == 'bridge': cls = 'pylon'   # bridge pylons: plain cladding, no windows")
open(p,'w',newline='').write(s)
p='scene.py';s=open(p,newline='').read()
a="build_class('tower', *spec.get('tower_tex', ['tower.png', 3.0, 3.6]))"
assert s.count(a)==1
s=s.replace(a,a+N+"if any(b['c'] == 'pylon' for b in BL): build_class('pylon', 'mv_pylon.png', 4.0, 4.0)");open(p,'w',newline='').write(s);print('ok')
