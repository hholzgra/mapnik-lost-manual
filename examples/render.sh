#! /bin/bash
xml=$(realpath $1)
base=${xml%.xml}

cd $(dirname $0)

# render.py output goes to temporary files first, as the PNG still
# needs to be trimmed
mkdir -p tmp
tmpnam=$(mktemp -p tmp tmprenderXXXXXXXXXX)
trap 'rm -f $tmpnam*' EXIT

if ! ./render.py $(realpath --relative-to=. $xml) $tmpnam
then
	exit 5
fi

mv $tmpnam.svg $base.svg
if ! convert -regard-warnings -trim $tmpnam.png $base.png 2>/dev/null
then
	cp $tmpnam.png $base.png
fi
