#! /bin/bash
base=$(basename $1 .xml)
dir=$(dirname $(realpath $1))

cd $(dirname $0)
mkdir -p tmp
tmpnam=$(mktemp -p tmp tmprenderXXXXXXXXXX)

status=3

cp $dir/$base.xml $tmpnam.xml

if ./render.py $tmpnam
then
	mv $tmpnam.svg $dir/$base.svg
	if ! convert -regard-warnings -trim $tmpnam.png $dir/$base.png 2>/dev/null
	then
		cp $tmpnam.png $dir/$base.png
	fi
	rm -f $tmpnam*
	status=0
else
	status=5
fi

exit $status
