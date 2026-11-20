exec(open('pj.py',encoding='utf-8').read())
I=np.asarray(Image.open('ref.jpg').convert('RGB').resize((1023,576),Image.LANCZOS),float)
for sm in np.arange(394.0,522.1,8.0):
    rows=[]
    for z in np.arange(40,45.6,0.5):
        p=proj(P([sm],53.0,z)[0])[0];x,y=int(round(p[0])),int(round(p[1]))
        seg=I[y,x-4:x+5];g=seg@[0.299,0.587,0.114];k=int(np.argmax(np.abs(g-np.median(g))))
        rows.append((z,x-4+k,seg[k].astype(int),int(np.median(g))))
    # topmost z where the line pixel differs from the background by > 15
    top=max([r[0] for r in rows if abs((r[2]@[0.299,0.587,0.114])-r[3])>15],default=None)
    print(int(sm),'top~',top,'post rgb',np.mean([r[2] for r in rows if r[0]<=43],0).astype(int))
