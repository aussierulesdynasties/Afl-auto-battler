# Seat gate board: 1992-era Gorringe seats in the photo beside the model's seat-height close-ups (renders r_seats_front/r_seats_row)
from PIL import Image,ImageDraw,ImageFont
from proofs1992 import photo_panel
R='../../../.claude/review/north_hobart'
ph=photo_panel('gorringe','se_end').crop((200,400,450,560)).resize((750,480),Image.LANCZOS)
fr=Image.open(R+'/renders/r_seats_front.png').convert('RGB').resize((750,750))
rw=Image.open(R+'/renders/r_seats_row.png').convert('RGB').resize((1200,750))
B=Image.new('RGB',(750+750+1200+40,800),(24,24,24));d=ImageDraw.Draw(B);f=ImageFont.truetype('arial.ttf',22)
B.paste(ph,(0,40));B.paste(fr,(770,40));B.paste(rw,(1540,40))
for x,t in((0,'photo: Gorringe SE end seats'),(770,'model: SE end block, front'),(1540,'model: seat height along a row (empty)')):d.text((x+6,8),t,fill=(255,255,255),font=f)
B.save(R+'/boards/gorringe_seats.png');print(B.size)
