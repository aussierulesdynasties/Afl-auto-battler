# Texture proof: each hand-made texture (centre 512 px tile) beside a crop of the same surface in a reference photo, with stddev.
from PIL import Image,ImageDraw,ImageFont,ImageStat
from proofs1992 import photo_panel,NEW
try:FN=ImageFont.truetype('arial.ttf',20)
except Exception:FN=ImageFont.load_default()
# photo crops: (board tag, part, box) from the committed proof boards, or ('file', path, box) for the 1990 photo
# (photo_1990_scoreboard.jpg: scoreboardpressure.com/2011/08/23/north-hobart-tasmania/, 1990 TFL grand final; reference only)
P90='../../../.claude/review/north_hobart/boards/photo_1990_scoreboard.jpg'
# roof_iron: the Ryde/Lewis roofs are the Gorringe's maroon iron (same hue in the 1992 aerial, 0.8x as bright), so it is paired with the Gorringe roof photo
REF={'roof_iron':('gorringe','roof_gables',(230,120,380,200)),'roof_gor':('gorringe','roof_gables',(230,120,380,200)),
 'brick':('gorringe','se_end',(215,560,320,650)),
 'render_cream':('gorringe','entrance',(130,120,230,160)),'seats':('gorringe','se_end',(260,465,430,540)),
 'post_maroon':('gorringe','se_end',(190,330,220,500)),'fascia':('gorringe','se_end',(300,226,440,256)),
 'pediment':('gorringe','clock_gable',(55,110,180,150)),'trim_white':('gorringe','roof_gables',(185,100,235,190)),
 'ceiling':('gorringe','se_end',(300,340,450,368)),'roof_white':('aerial','ryde_stand',(110,238,570,256)),
 'asphalt':('gorringe','wall_pilasters_stairs',(440,192,600,214)),'tread':('aerial','lewis_stand',(30,140,170,260)),
 'concrete':('gorringe','wall_pilasters_stairs',(340,180,420,212)),'cladding_grey':('gorringe','se_end',(120,300,160,450)),
 'steel_dark':('file',P90,(222,190,250,300)),'pole_grey':('gorringe','entrance',(256,60,270,250)),
 'sb_face':('file',P90,(255,185,360,280)),'interior_dark':('gorringe','wall_pilasters_stairs',(665,118,750,170)),
 'fence_white':('aerial','gorringe',(81,427,86,482)),'glass_screen':('gorringe','posts_deck',(610,125,850,230)),
 'roof_clear':('file','ref_full_1992.png',(3980,2860,4060,2960)),'bench':('file','ref_full_1992.png',(2320,2820,2420,2870)),
 'clock':('gorringe','clock_gable',(185,85,250,145)),
 'gor_name':('gorringe','clock_gable',(115,138,320,162)),'club_sign_lettered':('gorringe','entrance',(190,92,375,114))}
def crop(tag,part,b):return (Image.open(part).convert('RGB') if tag=='file' else photo_panel(tag,part)).crop(b)
def fit(im,T):
    w,h=im.size;k=T/max(w,h);im=im.resize((max(1,int(w*k)),max(1,int(h*k))));B=Image.new('RGB',(T,T),(20,20,20));B.paste(im,((T-im.size[0])//2,(T-im.size[1])//2));return B
names=['roof_iron','roof_gor','brick','render_cream','seats','post_maroon','fascia','pediment','trim_white','ceiling','roof_white','asphalt','tread','concrete',
 'cladding_grey','steel_dark','pole_grey','sb_face','interior_dark','fence_white','glass_screen','roof_clear','bench','clock','gor_name','club_sign_lettered']
T=260;cols=4;rows=(len(names)+cols-1)//cols;S=Image.new('RGB',(cols*(2*T+30),rows*(T+34)),(20,20,20));d=ImageDraw.Draw(S)
for k,n in enumerate(names):
    x,y=(k%cols)*(2*T+30),(k//cols)*(T+34);t=Image.open(f'tex/{n}.png').convert('RGB');w,h=t.size;s=min(512,w,h)
    tile=t.crop(((w-s)//2,(h-s)//2,(w-s)//2+s,(h-s)//2+s)).resize((T,T));S.paste(tile,(x,y+30))
    sd=ImageStat.Stat(t.convert('L')).stddev[0];lab=f'{n} sd {sd:.1f}'
    if n in REF:tag,part,b=REF[n];S.paste(fit(crop(tag,part,b),T),(x+T+8,y+30));lab+=f" | photo: {'1990 photo' if part==P90 else ('1992 aerial' if tag=='file' else tag+' '+part)}"
    else:lab+=' | no photo crop'
    d.text((x+4,y+6),lab,fill=(255,255,255),font=FN)
S.save(f'{NEW}/northhobart_1992_textures.png');print(S.size)
