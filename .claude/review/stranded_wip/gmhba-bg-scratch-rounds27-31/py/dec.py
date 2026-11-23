import sys,re,base64
t=open(sys.argv[1],encoding='utf-8').read(); m=re.search(r'B64START([A-Za-z0-9+/=]+)B64END',t)
open(sys.argv[2],'wb').write(base64.b64decode(m.group(1))); print('ok',len(m.group(1)))
