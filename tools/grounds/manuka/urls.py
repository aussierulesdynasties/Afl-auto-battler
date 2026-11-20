import json,re,sys
d=json.load(open(sys.argv[1],encoding='utf-8'))
pat=re.compile(r'https?:[^\s"\\]+?\.(?:jpe?g|png|webp)',re.I)
for b in d:
    t=b.get('text','')
    print('BLOCK',len(t),t[:100].replace('\n',' '))
    for u in dict.fromkeys(pat.findall(t)):
        if re.search(r'-\d+x\d+\.',u) or re.search(r'logo|icon',u,re.I):continue
        print('  ',u)
