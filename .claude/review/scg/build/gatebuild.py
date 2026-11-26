# rebuild gate/: turntable_4 (2x2 of t0-t3), facade_closeup, close-ups, board and heritage crop from the latest renders
import shutil;from PIL import Image
T='out/turn/';G='gate/'
sh=Image.new('RGB',(1600,1000))
for i in range(4):sh.paste(Image.open(T+f't{i}.png').convert('RGB').resize((800,500),Image.LANCZOS),((i%2)*800,(i//2)*500))
sh.save(G+'turntable_4.png')
shutil.copy(T+'close.png',G+'facade_closeup.png')
for n in ('trumper_back','oreilly_back','heritage_roofs'):shutil.copy(T+n+'.png',G+n+'.png')
shutil.copy('g/board0.png',G+'board_photo_model_overlay.png');shutil.copy('g/mes1.png',G+'crop_heritage.png')
print('gate ok')
