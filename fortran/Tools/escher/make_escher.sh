#! /bin/bash
PATH=/usr/local/bin:/usr/bin gfortran -c *.f
rm -f *.a
ar crs escher.a *.o
rm -f *.o
