s=open('scene.py',encoding='utf-8').read()
o1="keep=lambda b, v=_v: not _lime(b) and 'abcd'"
assert o1 in s
s=s.replace(o1,"keep=lambda b, v=_v: not _lime(b) and not _shed(b) and 'abcd'",1)
o2="for _v in 'abcd':   # each building its own"
s=s.replace(o2,"""_shed = lambda b: b['a'] < 80 and b['c'] != 'tower'   # small sheds and kiosks: corrugated sheeting + roller door (texture session: no plain boxes)
for _cl in ('house', 'block'):
    build_class(_cl, 'fac_shed.png', 6.0, 4.5, keep=lambda b: not _lime(b) and _shed(b), tag='_shed')
"""+o2,1)
open('scene.py','w',encoding='utf-8',newline='').write(s)
