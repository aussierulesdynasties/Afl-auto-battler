# texture proof: each hand-painted map (left) beside a crop of the same surface in the 1990s photo (right), grey stddev
import json,numpy as np
from PIL import Image,ImageDraw
PH=Image.open('ref.jpg').convert('RGB').resize((1023,576),Image.LANCZOS)
ROWS=[('roof','near roof sheeting',(500,437)),('roofm','members roof',(482,89)),('facade','outer wall under the roof',(480,458)),
('fvoid','undercroft behind columns',(380,461)),('seat_R','seats, red bay (empty)',(685,387)),('seat_Y','seats, yellow bay (empty)',(590,408)),
('pave','concourse paving',(870,462)),('kioskr','kiosk red',(428,462)),('kioskb','kiosk navy',(557,464)),('kiosko','kiosk orange',(446,462)),
('greenpaint','long low building',(520,507)),('glass','members glass band',(485,128)),('steel','light tower steel',(140,350)),
('grass','outside embankment grass',(975,455)),('dirt','outside dirt',(930,505)),('white','white paint (low building roof)',(620,482)),
('dirtA','near ring dirt',(300,495)),('dirtS','near slope dirt',(415,545)),('dirtP','pink dirt by the building',(510,530)),('grass_nl','near-left slope grass',(270,551)),('asph','near ring asphalt',(750,485)),
('asphp','plaza and road',(600,540)),('grass_n','near-right dry grass',(800,545)),('steeldk','dark steel deck (near left)',(307,460)),('mastg','members roof masts',(480,76))]
C=230;pad=8;cols=4;rows=(len(ROWS)+cols-1)//cols
B=Image.new('RGB',(cols*(2*C+3*pad),rows*(C+40)+10),(24,24,24));d=ImageDraw.Draw(B)
lst=[]
for k,(n,lab,(x,y)) in enumerate(ROWS):
    T=Image.open('tex2/%s.png'%n).convert('RGB');g=np.asarray(T.convert('L'),float).std();lst.append((n,g))
    t=T.crop((0,0,min(256,T.width),min(256,T.height))).resize((C,C),Image.LANCZOS)
    p=PH.crop((x-10,y-10,x+10,y+10)).resize((C,C),Image.LANCZOS)
    cx=(k%cols)*(2*C+3*pad)+pad;cy=(k//cols)*(C+40)+30
    B.paste(t,(cx,cy));B.paste(p,(cx+C+pad,cy));d.text((cx,cy-20),'%s - %s  (grey std %.1f)'%(n,lab,g),fill=(255,255,255))
B.save('out/texture_board.jpg',quality=90)
M=json.load(open('mats.json'));allstd=[(n,np.asarray(Image.open('tex2/%s.png'%n).convert('L'),float).std()) for n in M]
open('out/texture_stddev.txt','w').write('grey stddev (PIL L, 0-255) of every texture in the model; rule: >= 10\n'+'\n'.join('%-12s %5.1f'%v for v in allstd)+'\nmin %.1f\n'%min(v for _,v in allstd))
print('min std',min(allstd,key=lambda v:v[1]))
