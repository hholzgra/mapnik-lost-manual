#! /bin/bash

list=$(find . -name "*.adoc" | xargs egrep -h -o "(include|image)::[^\[]+" | sed -e's/image:://g' -e's/include:://g' -e's/{sourcedir}\///g' | sort | uniq | xargs echo)

echo "book.html: $list" >> .deps/html.d
echo "book.pdf: $list" >> .deps/pdf.d
echo "book.epub: $list" >> .deps/epub.d

