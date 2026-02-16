PATH=/usr/local/bin:/usr/bin gfortran -c *.f
PATH=/usr/local/bin:/usr/bin gcc -c *.c
rm -f *.a
ar crs www.a *.o
rm -f *.o
