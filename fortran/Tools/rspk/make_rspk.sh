PATH=/usr/local/bin:/usr/bin gfortran -c *.f
rm -f *.a
ar crs rspk.a *.o
rm -f *.o
