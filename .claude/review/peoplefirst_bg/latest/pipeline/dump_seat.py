import bpy
for n in ('seat_up','seat_low','aisle_up'):
    im=bpy.data.images[n]; im.filepath_raw='//../../seatimg_%s.png'%n; im.file_format='PNG'; im.save(); print('SAVED',n)
