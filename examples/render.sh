#! /bin/bash
base=$(basename $1 .xml)
./render.py $base.xml
convert -trim render.png $base.png
rm -f render.png
