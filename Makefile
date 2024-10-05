all: html epub pdf examples

.PHONY:all examples clean install html pdf epub

html: book.html

pdf: book.pdf

epub: book.epub

book.pdf: book.adoc .deps/pdf.d
	@echo "Creating PDF"
	@asciidoctor-pdf book.adoc

book.html: book.adoc .deps/html.d
	@echo "Creating HTML"
	@asciidoctor book.adoc

multipage: book.adoc .deps/html.d
	@echo "Creating Multi Page HTML"
	@asciidoctor -r asciidoctor-multipage -b multipage_html5 -D book/ --backend multipage_html5 -a data-uri book.adoc

book.epub: book.adoc images/cover.svg .deps/epub.d
	@echo "Creating epub"
	@asciidoctor-epub3 book.adoc

examples:
	@make -C examples

clean:
	@rm -f *.html *.pdf
	@make -C examples clean

install: all 
	@echo "Transferring files to webserver"
	@rsync -avu -e 'ssh -ax' . h6:/var/www/html/mapnik-lost-manual/

install-html: book.html 
	@echo "Transferring files to webserver"
	@rsync -avu -e 'ssh -ax' . h6:/var/www/html/mapnik-lost-manual/

depend:
	@./adoc-dependencies.sh
