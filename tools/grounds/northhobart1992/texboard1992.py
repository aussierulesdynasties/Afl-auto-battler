# Texture proof: each hand-made texture (centre 512 px tile) beside a crop of the same surface in a reference photo, with stddev.
from PIL import Image,ImageDraw,ImageFont,ImageStat
from proofs1992 import photo_panel,NEW
try:FN=ImageFont.truetype('arial.ttf',20)
except Exception:FN=ImageFont.load_default()
REF={'roof_iron':('aerial','lewis_stand',(330,330,450,420)),'brick':('gorringe','se_end',(215,560,320,650)),
 'render_cream':('gorringe','entrance',(130,120,230,160)),'seats':('gorringe','se_end',(260,465,430,540)),
 'post_maroon':('gorringe','se_end',(190,330,220,500)),'fascia':('gorringe','se_end',(150,262,440,288)),
 'pediment':('gorringe','clock_gable',(55,110,180,150)),'trim_white':('gorringe','roof_gables',(250,130,420,200)),
 'roof_white':('aerial','ryde_stand',(85,170,160,240)),'tread':('aerial','lewis_stand',(30,140,170,260)),
 'concrete':('gorringe','se_end',(170,550,215,690)),'clock':('gorringe','clock_gable',(185,85,250,145)),
 'gor_name':('gorringe','clock_gable',(115,138,320,162)),'club_sign_lettered':('gorringe','entrance',(190,92,375,114))}
def fit(im,T):
    w,h=im.size;k=T/max(w,h);im=im.resize((max(1,int(w*k)),max(1,int(h*k))));B=Image.new('RGB',(T,T),(20,20,20));B.paste(im,((T-im.size[0])//2,(T-im.size[1])//2));return B
names=['roof_iron','brick','render_cream','seats','post_maroon','fascia','pediment','trim_white','ceiling','roof_white','asphalt','tread','concrete',
 'cladding_grey','steel_dark','pole_grey','sb_black','sb_face','interior_dark','fence_white','glass_screen','roof_clear','bench','clock','gor_name','club_sign_lettered']
T=260;cols=4;rows=(len(names)+cols-1)//cols;S=Image.new('RGB',(cols*(2*T+30),rows*(T+34)),(20,20,20));d=ImageDraw.Draw(S)
for k,n in enumerate(names):
    x,y=(k%cols)*(2*T+30),(k//cols)*(T+34);t=Image.open(f'tex/{n}.png').convert('RGB');w,h=t.size;s=min(512,w,h)
    tile=t.crop(((w-s)//2,(h-s)//2,(w-s)//2+s,(h-s)//2+s)).resize((T,T));S.paste(tile,(x,y+30))
    sd=ImageStat.Stat(t.convert('L')).stddev[0];lab=f'{n} sd {sd:.1f}'
    if n in REF:tag,part,b=REF[n];S.paste(fit(photo_panel(tag,part).crop(b),T),(x+T+8,y+30));lab+=f' | photo: {tag} {part}'
    else:lab+=' | no photo crop'
    d.text((x+4,y+6),lab,fill=(255,255,255),font=FN)
S.save(f'{NEW}/northhobart_1992_textures.png');print(S.size)
