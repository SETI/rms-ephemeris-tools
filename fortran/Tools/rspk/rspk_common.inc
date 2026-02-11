c*******************************************************************************
c rspk_common.inc
c
c FORTRAN include file containing common block and definitions for RSPK toolkit.
c
c Mark Showalter, PDS Rings Node, August 2005
c*******************************************************************************

c Fixed constants
        character*(*)   SPICE_PATH, DATA_PATH
        parameter       (SPICE_PATH = '/var/www/SPICE/')
        parameter       (DATA_PATH  = '/var/www/SPICE/')

c Planet and SPK status files
        integer*4               planet_num, planet_id
        logical*4               pool_loaded

c Time shift parameters
        integer                 MAXSHIFTS
        parameter               (MAXSHIFTS = 20)
        integer*4               nshifts, shift_id(MAXSHIFTS)
        double precision        shift_dt(MAXSHIFTS)

c Observer location parameters
        integer*4               obs_id
        logical*4               obs_is_set
        double precision        obs_lat, obs_lon, obs_alt

c Define common, properly aligned

        common  /RSPK_COMMON/   planet_num, planet_id,
     &                          pool_loaded,
     &                          obs_id, obs_is_set,
     &                          nshifts, shift_id,
     &                          shift_dt,
     &                          obs_lat, obs_lon, obs_alt

c*******************************************************************************
