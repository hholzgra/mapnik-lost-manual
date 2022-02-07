#! /bin/bash
base=$(basename $1 .xml)
dir=$(dirname $1)
cp $dir/$base.xml render.xml
./render.py render.xml
mv render.svg $dir/$base.svg
convert -trim render.png $dir/$base.png
rm -f render.png render.xml
