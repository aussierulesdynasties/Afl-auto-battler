from PIL import Image,ImageDraw,ImageFont
f=lambda s:ImageFont.truetype('C:/Windows/Fonts/arial.ttf',s)
ol=Image.open('ol.png').convert('RGB').resize((1300,1300))
B=Image.new('RGB',(1300+760,1300),(24,26,32));B.paste(ol,(0,0));d=ImageDraw.Draw(B)
rows=[('Sector (angle from pitch centre)','Model edge vs satellite'),
('Players Stand roof 204-275','notches + tips: 0.03-1.75 m'),
('West face 168-200','~0.5 m (white wall strip x -119)'),
('Low SW canopy 131-165','~1 m'),
('West 110-130','~1.5 m'),
('NW stair tower 99.5-105.5','48.75 vs 47 m (1.75 m)'),
('North stand 60-100','49.5-50.5 vs 50-51 m (<1 m)'),
('NE corner 20-36','1-2 m'),
('East (Reg Hickey) -20..20','21-23 vs ~22 m (~1 m)'),
('SE pocket block 279-285','45 vs 45 m (<1 m)'),
('SE pocket kerb 285-303','~1 m'),
('SE roof -100..-82','zig-zag ~1 m'),
('Light-tower heads','NW, SW <2 m; SE, NE moved onto them')]
d.text((1320,20),'GMHBA Stadium: top-down vs Esri z19',font=f(30),fill=(240,240,240))
d.text((1320,62),'north up, 0.25 m/px, lean corrected (y+0.035 z)',font=f(20),fill=(170,180,200))
d.text((1320,88),'model silhouette traced on the satellite, grid 10 m',font=f(20),fill=(170,180,200))
y=140
for i,(a,b) in enumerate(rows):
    c=(255,210,120) if i==0 else (235,235,235)
    d.text((1320,y),a,font=f(22),fill=c);d.text((1320,y+28),b,font=f(22),fill=(140,220,160) if i else c);y+=66
d.text((1320,y+10),'Polar unwraps (red = model edge) in proof/topdown/',font=f(20),fill=(170,180,200))
B.save('../topdown_board.png')
