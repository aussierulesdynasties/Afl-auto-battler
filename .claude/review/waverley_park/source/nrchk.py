exec(open('gen.py',encoding='utf-8').read().split('# ---------------- seat block colours')[0])
ZR_IN,ZR_OUT,DR_IN,DR_OUT=8.9,15.6,19.7,35.2
def zroof(d):return ZR_IN+(ZR_OUT-ZR_IN)*(d-DR_IN)/(DR_OUT-DR_IN)
DINK=np.array([(0,32),(47,31),(63,29),(86,27),(97,28),(105,22),(119,21),(140,19.7),(195,19.7),(205,21.0),(230,21.2),(240,23.0),(246,23.6),(250,25.0),(253,26.0),(297.6,23.8),(300,24),(309,25.5),(318,28),(328,32),(PER,32)],float)
def DIN(s):return float(np.interp(s%PER,DINK[:,0],DINK[:,1]))
pts=[]
for s in range(195,254,5):
    pts.append((s,DIN(s),zroof(DIN(s)),'i%d'%s));pts.append((s,DR_OUT,ZR_OUT,'o'))
pts.append((252.5,DR_OUT,ZR_OUT,'end'))
import subprocess,sys
subprocess.run([sys.executable,'kchk.py','690','320','900','430','4',repr(pts),'out/nr.png'],check=True)
