# WAFL scrape helper: downloads each page named in a list file into a cache folder (fetch.py <list> <base url> <out dir>).
# Kept as the record of how tools/state_leagues/staging/ was made; tools/state_leagues/build.py
# rebuilds data/state_leagues/ from staging/ without them.
import sys,os,time,urllib.request,urllib.error
lst,base,out=sys.argv[1:4]
os.makedirs(out,exist_ok=True)
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"
fail=open(os.path.join(out,'_fail.txt'),'a')
for s in open(lst).read().split():
    p=os.path.join(out,s+'.html')
    if os.path.exists(p) and os.path.getsize(p)>0: continue
    for attempt in range(3):
        try:
            r=urllib.request.urlopen(urllib.request.Request(base+'/'+s,headers={'User-Agent':UA}),timeout=30)
            open(p,'wb').write(r.read()); break
        except urllib.error.HTTPError as e:
            fail.write(f'{s} {e.code}\n'); fail.flush(); break
        except Exception as e:
            time.sleep(3)
    else:
        fail.write(f'{s} ERR\n'); fail.flush()
    time.sleep(0.4)
print('done',lst)
