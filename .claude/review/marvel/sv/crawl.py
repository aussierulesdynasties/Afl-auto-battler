# BFS over Street View panoramas near the stadium via photometa; writes panos.json {id: {lat,lng,h,p,r,date,local}}
import sys,os,re,json,subprocess
sys.argv=[sys.argv[0]]+sys.argv[1:]
HERE=os.path.dirname(os.path.abspath(__file__));__file__=os.path.join(HERE,'sv.py')
exec(open(os.path.join(HERE,'sv.py'),encoding='utf-8').read().split('if __name__')[0])
U=('https://www.google.com/maps/photometa/v1?authuser=0&hl=en&gl=au&pb=!1m4!1smaps_sv.tactile!11m2!2m1!1b1!2m2!1sen!2sau'
   '!3m3!1m2!1e2!2s{}!4m57!1e1!1e2!1e3!1e4!1e5!1e6!1e8!1e12!2m1!1e1!4m1!1i48!5m1!1e1!5m1!1e2!6m1!1e1!6m1!1e2!9m36!1m3!1e2!2b1!3e2'
   '!1m3!1e2!2b0!3e3!1m3!1e3!2b1!3e2!1m3!1e3!2b0!3e3!1m3!1e8!2b0!3e3!1m3!1e1!2b0!3e3!1m3!1e4!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e10!2b0!3e3')
NB=re.compile(r'\[\[2,"([A-Za-z0-9_-]{22})"\],null,\[\[null,null,(-?[\d.]+),(-?[\d.]+)\],(?:null|\[[^\]]*\]),\[([-\d.]+),([-\d.]+),([-\d.]+)\]\]')
G=json.load(open(os.path.join(MV,'osm/geo.json'),encoding='utf-8'));a=np.array(G['ways']['22971441'])
OUT=loc(np.c_[a,np.zeros(len(a))])[:-1]
from matplotlib.path import Path as MP
poly=MP(OUT)
def dist(p):
    d=min(np.linalg.norm(OUT-p,axis=1));return 0 if poly.contains_point(p) else d
db=json.load(open(os.path.join(HERE,'panos.json'))) if os.path.exists(os.path.join(HERE,'panos.json')) else {}
todo=list(sys.argv[1:]) or [k for k,v in db.items() if not v.get('done')]
R=float(os.environ.get('R','70'))
while todo:
    pid=todo.pop(0)
    if db.get(pid,{}).get('done'):continue
    s=subprocess.run(['curl','-s','-A','stadium-ref/1.0',U.format(pid)],capture_output=True).stdout.decode('utf-8','replace')
    dates=re.findall(r'\[(20[0-2]\d),(1[0-2]|[1-9])\]',s)
    nb=NB.findall(s)
    e=db.setdefault(pid,{});e['done']=1
    if dates:e['date']='%s-%02d'%(dates[-1][0],int(dates[-1][1]))
    for i,la,lo,h,p,r in nb:
        la,lo=float(la),float(lo);q=st(la,lo);d=dist(q)
        f=db.setdefault(i,{});f.update(lat=la,lng=lo,h=float(h),p=float(p),r=float(r),s=round(q[0],1),t=round(q[1],1),d=round(d,1))
        if d<R and not f.get('done') and i not in todo:todo.append(i)
    print(pid,e.get('date'),len(nb),'todo',len(todo),flush=True)
    json.dump(db,open(os.path.join(HERE,'panos.json'),'w',newline=''),indent=0)
