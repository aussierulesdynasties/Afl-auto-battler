p='canopy_mask.py'; s=open(p,newline='').read()
old="can = (exg > 6) & (L < 75) | (exg > 20) & (L < 95)"
new="""_li = Image.fromarray(L.astype(np.uint8)); _sm = _li.resize((_li.width // 8, _li.height // 8), Image.BOX).filter(ImageFilter.MedianFilter(5))
Lb = np.asarray(_sm.resize(_li.size, Image.BILINEAR), float)   # local ground level (~20 m median)
can = (exg > -4) & (L < 70) & (L < Lb - 12)"""
assert old in s; s=s.replace(old,new); open(p,'w',newline='').write(s); print('ok')
