f='fence_mask.py'; s=open(f,newline='').read()
a="""    im = im.filter(ImageFilter.MaxFilter(9))          # grow 2 m
    ImageDraw.floodfill(im, (0, 0), 128)              # outside
    m = np.asarray(im) != 128"""
assert a in s
s=s.replace(a,"""    im = im.filter(ImageFilter.MaxFilter(33))         # grow 8 m: closes gate gaps in the fence
    ImageDraw.floodfill(im, (0, 0), 128)              # outside
    m = Image.fromarray(((np.asarray(im) != 128) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(25))   # shrink 6 m back: net 2 m past the model
    m = np.asarray(m) > 0""",1)
open(f,'w',newline='').write(s)
