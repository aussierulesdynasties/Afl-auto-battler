import re
def sub(fn,pairs):
    s=open(fn,newline='').read()
    for a,b in pairs:
        n=s.count(a); assert n==1,(fn,a[:60],n); s=s.replace(a,b)
    open(fn,'w',newline='').write(s)
def block(fn,start,end,repl):
    s=open(fn,newline='').read();i=s.index(start);j=s.index(end,i)
    open(fn,'w',newline='').write(s[:i]+repl+s[j:])
# banner: blank navy panel (no TIO box, no name)
block('texgen.py',"lx0,lx1=int(sx(14.72)","im.save(os.path.join(OUT,'banner.png'))","# no lettering (director 2026-11-18: \"C: no lettering\"): blank navy panel\n")
# cream band: blank
block('texgen.py',"txt='Bowden McAdam Grandstand'","im.save(os.path.join(OUT,'cream_band.png'))","# no lettering (director 2026-11-18): blank cream panel\n")
# clubroom roof: no TIO box, no Territorians
block('texclub.py',"lx0,lx1=int((24.0-14.1","img=np.asarray(im).astype(float)\n# corrugation","# no lettering (director 2026-11-18): plain blue roof\n")
# pole signs: blank panels
sub('texsite.py',[("pole_sign('sign_tio',(29,92,178),True,(250,250,250),['Traeger','Park Oval'])","pole_sign('sign_tio',(29,92,178),False,(250,250,250),[])  # no lettering (director 2026-11-18)")])
# scoreboard: header stripes kept, no TIO box, no name, no strip lettering
block('texsite.py',"d.rectangle([int(W*0.075),int(hh*0.18)","sy0,sy1=","# no lettering (director 2026-11-18): blank header\n")
sub('texsite.py',[("d.text((W//2,int(H*0.978)),'TED HAYES SCOREBOARD',font=font('segoeuib.ttf',H*0.035),fill=(245,245,245),anchor='mm')\n","")])
