import json
s=open('landmarks.py',encoding='utf-8',newline='').read(); a=open('arenas_lm.py',encoding='utf-8',newline='').read()
if 'arenas' not in s:
    k='# build: one object per material'; s=s.replace(k,a+'\n'+k,1)
    s=s.replace("'girl': lm_mat('girl', 0.5, alpha=True)}","'girl': lm_mat('girl', 0.5, alpha=True), 'arena_wall': lm_mat('arena_wall', 0.6), 'copper': lm_mat('copper', 0.45, metal=0.3), 'ribwhite': lm_mat('ribwhite', 0.5), 'glazed': lm_mat('glazed', 0.15), 'bubble': lm_mat('bubble', 0.4), 'tiers': lm_mat('tiers', 0.8), 'pitch': lm_mat('pitch', 0.9)}")
    open('landmarks.py','w',encoding='utf-8',newline='').write(s)
sp=json.load(open('spec/mcg.json'));sp['landmarks']=['spire','shrine','arenas'];json.dump(sp,open('spec/mcg.json','w'),indent=1)
print(s.count('arena_wall'))
