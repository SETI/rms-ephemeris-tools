PATH=/usr/local/bin:/usr/bin gfortran -o tracker2_mar.bin \
    tracker2_mar.f \
    rspk/rspk.a euclid/euclid.a escher/escher.a ../MyWWW/www.a \
    ../Julian/julian.a /home/shared/lib/libspice.a

PATH=/usr/local/bin:/usr/bin gfortran -o tracker2_jup.bin \
    tracker2_jup.f \
    rspk/rspk.a euclid/euclid.a escher/escher.a ../MyWWW/www.a \
    ../Julian/julian.a /home/shared/lib/libspice.a

PATH=/usr/local/bin:/usr/bin gfortran -o tracker2_sat.bin \
    tracker2_sat.f \
    rspk/rspk.a euclid/euclid.a escher/escher.a ../MyWWW/www.a \
    ../Julian/julian.a /home/shared/lib/libspice.a

PATH=/usr/local/bin:/usr/bin gfortran -o tracker2_ura.bin \
    tracker2_ura.f \
    rspk/rspk.a euclid/euclid.a escher/escher.a ../MyWWW/www.a \
    ../Julian/julian.a /home/shared/lib/libspice.a

PATH=/usr/local/bin:/usr/bin gfortran -o tracker2_nep.bin \
    tracker2_nep.f \
    rspk/rspk.a euclid/euclid.a escher/escher.a ../MyWWW/www.a \
    ../Julian/julian.a /home/shared/lib/libspice.a

PATH=/usr/local/bin:/usr/bin gfortran -o tracker2_jupc.bin \
    tracker2_jupc.f \
    rspk/rspk.a euclid/euclid.a escher/escher.a ../MyWWW/www.a \
    ../Julian/julian.a /home/shared/lib/libspice.a

PATH=/usr/local/bin:/usr/bin gfortran -o tracker2_satc.bin \
    tracker2_satc.f \
    rspk/rspk.a euclid/euclid.a escher/escher.a ../MyWWW/www.a \
    ../Julian/julian.a /home/shared/lib/libspice.a
