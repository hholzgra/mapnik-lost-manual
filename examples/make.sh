#! /bin/bash

for xml in *.xml
do
	echo "processing $xml"
	./render.sh $xml
done
