all: html epub pdf examples

.PHONY:all examples clean install html pdf epub

html: book.html

pdf: book.pdf

epub: book.epub

book.pdf: book.adoc examples
	@echo "Creating PDF"
	@asciidoctor-pdf book.adoc

book.html: book.adoc examples
	@echo "Creating HTML"
	@asciidoctor book.adoc

book.epub: book.adoc examples images/cover.svg
	@echo "Creating epub"
	@asciidoctor-epub3 book.adoc

examples:
	@make -C examples

clean:
	@rm -f *.html *.pdf
	@make -C examples clean

install: all 
	@echo "Transferring files to webserver"
	@rsync -avu -e 'ssh -ax' . h5:/var/www/html/mapnik-lost-manual/

install-html: book.html 
	@echo "Transferring files to webserver"
	@rsync -avu -e 'ssh -ax' . h5:/var/www/html/mapnik-lost-manual/


