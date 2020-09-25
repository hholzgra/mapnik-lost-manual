#! /bin/bash

rm -f *.png
for xml in *.xml
do
	base=$(basename $xml .xml)
	if [ "$xml" -nt "$base.svg" ] 
	then
		echo "processing $xml"
		./render.sh $xml
	fi
done
