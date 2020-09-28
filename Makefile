all: book.pdf book.html book.epub examples

.PHONY:all examples clean install

book.pdf: book.txt examples
	@echo "Creating PDF"
	@asciidoctor-pdf book.txt

book.html: book.txt examples
	@echo "Creating HTML"
	@asciidoctor book.txt

book.epub: book.txt examples images/cover.svg
	@echo "Creating epub"
	@asciidoctor-epub3 book.txt

examples:
	@make -C examples

clean:
	@rm -f *.html *.pdf
	@make -C examples clean

install: all
	@echo "Transferring files to webserver"
	@scp -rq * h5:/var/www/html/mapnik-lost-manual/
