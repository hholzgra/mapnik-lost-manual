#! /bin/bash
base=$(basename $1 .xml)
dir=$(dirname $1)
tmpnam=$(basename $(mktemp -p . tmprenderXXXXXXXXXX))

cp $dir/$base.xml $tmpnam.xml
./render.py $tmpnam
mv $tmpnam.svg $dir/$base.svg
if ! convert -regard-warnings -trim $tmpnam.png $dir/$base.png
then
	cp $tmpnam.png $dir/$base.png
fi
rm -f $tmpnam $tmpnam.png $tmpnam.xml
