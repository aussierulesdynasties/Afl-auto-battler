m = open(r'D:/Temp/claude/b5e56bf702cd3703/4ee81fc3-6cf4-400f-9ad6-28a5df4e19ee/scratchpad/proto/scene.py', encoding='utf-8').read(); c = open('scene.py', encoding='utf-8').read()
s, e = '# ---------- rails:', '# ---------- buildings ----------'
blk = m[m.index(s):m.index(e)]
c = c[:c.index(s)] + blk + c[c.index(e):]
open('scene.py', 'w', encoding='utf-8', newline='').write(c); print('ok')
