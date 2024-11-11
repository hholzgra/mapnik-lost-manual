#! /bin/bash

for style in $(find examples -name "*.xml")
do
    if ! [[ "$style" =~ 'examples/disabled' ]] then
       for ext in png svg
       do
	   php tools/mapnik-deps.php $style $(dirname $style)/$(basename $style .xml).$ext examples
       done
    fi
done
