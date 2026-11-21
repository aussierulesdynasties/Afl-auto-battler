# Plaza (hard ground) outline traced on Esri sat/esri_025.png, metres (x east, y north). Clean straight runs.
import json
D=json.load(open('model/mcg.json'));HARD=D['plaza_poly'];PAVE=D['paving_poly']
import sys
from PIL import Image, ImageDraw
if __name__=='__main__':
    im=Image.open('sat/esri_025.png').convert('RGB');d=ImageDraw.Draw(im)
    P=[((x+260)*4,(260-y)*4) for x,y in HARD];d.line(P+[P[0]],fill=(255,0,255),width=3)
    Q=[((x+260)*4,(260-y)*4) for x,y in PAVE];d.line(Q+[Q[0]],fill=(0,255,0),width=2)
    for p in P:d.ellipse((p[0]-5,p[1]-5,p[0]+5,p[1]+5),outline=(0,255,255),width=2)
    im.crop((300,200,1800,1800)).save(sys.argv[1] if len(sys.argv)>1 else 'work/plazapoly.png')
