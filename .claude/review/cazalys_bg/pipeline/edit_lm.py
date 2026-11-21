p = 'scene.py'
s = open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'
old = "build_class('house', 'wall.png', 3.6, 3.2)"
assert s.count(old) == 1
s = s.replace(old, "exec(open(os.path.join(HERE, 'landmarks.py'), encoding='utf-8').read())   # hand-built landmarks replace their generic boxes" + nl + old)
open(p, 'w', encoding='utf-8', newline='').write(s)
import json
sp = 'spec/mcg.json'; d = json.load(open(sp)); d['landmarks'] = ['a108', 'eureka', 'rialto', 'spire', 'shrine', 'skipping']
json.dump(d, open(sp, 'w'), indent=1); print('ok')
