"""Director 2026-11-20 'Yes, dark like photo': water reflects less (specular level 0.15, roughness 0.15)."""
P = 'scene.py'; s = open(P, newline='').read()
a = "_wb.inputs['IOR'].default_value = 1.33; _wb.inputs['Roughness'].default_value = 0.03"; assert s.count(a) == 1
s = s.replace(a, "_wb.inputs['IOR'].default_value = 1.33; _wb.inputs['Roughness'].default_value = 0.15; _wb.inputs['Specular IOR Level'].default_value = 0.15")
open(P, 'w', newline='').write(s); print('ok')
