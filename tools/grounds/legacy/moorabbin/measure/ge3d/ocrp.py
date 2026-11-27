# ocrp.py DIR PTS.json OUT.json : ocr.py on 4 workers, each with its own temp file
import sys,json,re,subprocess,os,tempfile
from multiprocessing import Pool
d,pf,out=sys.argv[1:4];pts=json.load(open(pf))
rx=re.compile(r"(\d+)°(\d+)'([\d.]+)\"S\s*(\d+)°(\d+)'([\d.]+)\"E\s*(-?\d+)\s*m")
def one(i):
    f='%s/r%05d.png'%(d,i);p=pts[i]
    if not os.path.exists(f): return None
    tf=tempfile.mktemp(suffix='.png');subprocess.run(['convert',f,'-resize','400%','-colorspace','gray',tf])
    t=subprocess.run(['tesseract',tf,'-','--psm','7'],capture_output=True,text=True,timeout=30,env=dict(os.environ,OMP_THREAD_LIMIT='1')).stdout;os.remove(tf)
    m=rx.search(t.replace(' ',''))
    if m: g=[float(x) for x in m.groups()];return p+[-(g[0]+g[1]/60+g[2]/3600),g[3]+g[4]/60+g[5]/3600,g[6]]
    return p+[None,None,None]
with Pool(4) as P: res=[r for r in P.map(one,range(len(pts)),chunksize=20) if r is not None]
json.dump(res,open(out,'w'));print(len(res),sum(r[2] is None for r in res),'unread')
