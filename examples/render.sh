#! /bin/bash
base=$(basename $1 .xml)
dir=$(dirname $1)
tmpnam=$(basename $(mktemp -p . tmprenderXXXXXXXXXX))

cp $dir/$base.xml $tmpnam.xml
./render.py $tmpnam
mv $tmpnam.svg $dir/$base.svg
convert -trim $tmpnam.png $dir/$base.png
rm -f $tmpnam $tmpnam.png $tmpnam.xml
