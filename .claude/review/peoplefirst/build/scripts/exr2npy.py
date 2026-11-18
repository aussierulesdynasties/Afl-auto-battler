import bpy,numpy as np,sys
for n in sys.argv[sys.argv.index('--')+1:]:
    im=bpy.data.images.load(bpy.path.abspath('//'+n) if False else n);im.colorspace_settings.name='Non-Color'
    w,h=im.size;a=np.empty(w*h*4,np.float32);im.pixels.foreach_get(a)
    a=a.reshape(h,w,4)[::-1,:,:3];np.save(n.replace('.exr','.npy'),a);print('OK',n,a.shape,a.min(),a.max())
