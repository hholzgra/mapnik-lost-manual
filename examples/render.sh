#! /bin/bash
base=$(basename $1 .xml)
dir=$(dirname $1)
tmpnam=$(basename $(mktemp -p . tmprenderXXXXXXXXXX))

cp $dir/$base.xml $tmpnam.xml

if ./render.py $tmpnam
then
	mv $tmpnam.svg $dir/$base.svg
	if ! convert -regard-warnings -trim $tmpnam.png $dir/$base.png 2>/dev/null
	then
		cp $tmpnam.png $dir/$base.png
	fi
fi

rm -f $tmpnam*
