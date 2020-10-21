all: book.pdf book.html book.epub examples

.PHONY:all examples clean install

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
	@scp -rq * h5:/var/www/html/mapnik-lost-manual/
