#! /bin/bash
base=$(basename $1 .xml)
./render.py $base.xml
mv render.svg $base.svg
# convert -trim render.png $base.png
# rm -f render.png
