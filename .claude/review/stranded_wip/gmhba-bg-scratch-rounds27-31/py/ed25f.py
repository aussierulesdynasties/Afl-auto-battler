import sys
p = sys.argv[1]; s = open(p, encoding='utf-8', newline='').read()
a = " 'barwon': ((115, 1149), 'barwon', None), 'oldpo': ((218, 1104), 'oldpo', 13.0)}"
assert a in s
b = """ 'barwon': ((115, 1149), 'barwon', None), 'oldpo': ((218, 1104), 'oldpo', 13.0),
 'gmhba': ((542, 1300), 'gmhba', None), 'worksafe': ((378, 1353), 'worksafe', None), 'holiday': ((49, 1100), 'holiday', None),
 'rhotel': ((985, 1150), 'rhotel', None), 'edgewater': ((739, 1468), 'edgewater', None), 'civic': ((938, 1287), 'civic', None),
 'rydges': ((184, 776), 'rydges', None)}   # second set: py_mk_tower25.py"""
s = s.replace(a, b); open(p, 'w', encoding='utf-8', newline='').write(s); print('ok')
