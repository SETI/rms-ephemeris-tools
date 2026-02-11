PATH=/usr/local/bin:/usr/bin gfortran -o ephem3_xxx.bin \
    ephem3_xxx.f viewer3_utils.f \
    rspk/rspk.a ../MyWWW/www.a ../Julian/julian.a /home/shared/lib/libspice.a

PATH=/usr/local/bin:/usr/bin gfortran -o tracker3_xxx.bin \
    tracker3_xxx.f viewer3_utils.f \
    rspk/rspk.a euclid/euclid.a escher/escher.a ../MyWWW/www.a \
    ../Julian/julian.a /home/shared/lib/libspice.a

PATH=/usr/local/bin:/usr/bin gfortran -o viewer3_mar.bin \
    viewer3_mar.f viewer3_utils.f \
    rspk/rspk.a euclid/euclid.a escher/escher.a ../MyWWW/www.a \
    ../Julian/julian.a /home/shared/lib/libspice.a

PATH=/usr/local/bin:/usr/bin gfortran -o viewer3_jup.bin \
    viewer3_jup.f viewer3_utils.f \
    rspk/rspk.a euclid/euclid.a escher/escher.a ../MyWWW/www.a \
    ../Julian/julian.a /home/shared/lib/libspice.a

PATH=/usr/local/bin:/usr/bin gfortran -o viewer3_sat.bin \
    viewer3_sat.f viewer3_utils.f \
    rspk/rspk.a euclid/euclid.a escher/escher.a ../MyWWW/www.a \
    ../Julian/julian.a /home/shared/lib/libspice.a

PATH=/usr/local/bin:/usr/bin gfortran -o viewer3_ura.bin \
    viewer3_ura.f viewer3_utils.f \
    rspk/rspk.a euclid/euclid.a escher/escher.a ../MyWWW/www.a \
    ../Julian/julian.a /home/shared/lib/libspice.a

PATH=/usr/local/bin:/usr/bin gfortran -o viewer3_nep.bin \
    viewer3_nep.f viewer3_utils.f \
    rspk/rspk.a euclid/euclid.a escher/escher.a ../MyWWW/www.a \
    ../Julian/julian.a /home/shared/lib/libspice.a

PATH=/usr/local/bin:/usr/bin gfortran -o viewer3_plu.bin \
    viewer3_plu.f viewer3_utils.f \
    rspk/rspk.a euclid/euclid.a escher/escher.a ../MyWWW/www.a \
    ../Julian/julian.a /home/shared/lib/libspice.a
