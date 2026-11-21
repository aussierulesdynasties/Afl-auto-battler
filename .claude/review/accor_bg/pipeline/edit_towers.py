s=open('scene.py',newline='').read()
a="exec(open(os.path.join(HERE, 'landmarks.py'), encoding='utf-8').read())"
i=s.index(a); j=s.index('\n',i)
s=s[:j+1]+"if spec.get('extra_py'):\n    for _f in spec['extra_py']: exec(open(os.path.join(HERE, _f), encoding='utf-8').read())\n"+s[j+1:]
open('scene.py','w',newline='').write(s)
