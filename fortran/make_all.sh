#/usr/bin/bash
(cd Julian; ./make_julian.sh)
(cd MyWWW; ./make_www.sh)
(cd Tools/escher; ./make_escher.sh)
(cd Tools/euclid; ./make_euclid.sh)
(cd Tools/rspk; ./make_rspk.sh)
cd Tools
./make_tools.sh
