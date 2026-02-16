gcc -I../include -c \
dates.c \
format.c \
juldates.c \
leapsecs.c \
parse.c \
seconds.c \
tai_et.c \
utc_tai.c
gfortran -I../include -c fjulian.for

gcc -I../include -c fortran.c rlerrors.c rlmemory.c
gfortran -I../include -c fstrings.for

ar cr julian.a \
dates.o \
format.o \
juldates.o \
leapsecs.o \
parse.o \
seconds.o \
tai_et.o \
utc_tai.o \
fjulian.o \
fortran.o \
rlerrors.o \
rlmemory.o \
fstrings.o \

ranlib julian.a

gfortran -I../include -o tconvert tconvert.for julian.a

rm -f *.o
