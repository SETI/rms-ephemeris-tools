PATH=/usr/local/bin:/usr/bin gfortran -o ephem2_xxx.bin \
    ephem2_xxx.f \
    rspk/rspk.a ../MyWWW/www.a ../Julian/julian.a /home/shared/lib/libspice.a

PATH=/usr/local/bin:/usr/bin gfortran -o ephem2_xxx_sc.bin \
    ephem2_xxx_sc.f \
    rspk/rspk.a ../MyWWW/www.a ../Julian/julian.a /home/shared/lib/libspice.a
