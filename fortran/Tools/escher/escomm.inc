c This include file declares common /ESCOMM/, which contains key information
c about the postscript plot.
c
c Mark Showalter 12/13/96
c Updated 5/16/01 to move initializations to ESFILE.FOR.
c Updated 1/23/10 for correct alignment

        character*256   outfil
c       data            outfil/' '/

        character*80    creator, fonts
c       data            creator/' '/, fonts/' '/

        integer         outuni
c       data            outuni/0/

        integer         xsave, ysave

        logical         drawn
c       data            drawn/.FALSE./

        common  /ESCOMM/ outuni, outfil, creator, fonts,
     &                   xsave, ysave, drawn
        save    /ESCOMM/

