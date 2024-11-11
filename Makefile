all: multipage html epub pdf

PHONY = all clean install depend
PHONY += html pdf epub multipage

-include .deps/book.d
-include .deps/examples.d

this_dir = $(if $(pathsubst /%,,$(lastword $(MAKEFILE_LIST))),$(dir $(CURDIR)/$(lastword $(MAKEFILE_LIST))),$(dir $(lastword $(MAKEFILE_LIST))))

TOP_DIR := $(abspath .)
THIS_DIR := $(call this_dir)

html: book.html

pdf: book.pdf

epub: book.epub

multipage: book/book.html

book.adoc:
	@touch book.adoc

book.pdf: book.adoc 
	@echo "Creating PDF"
	@asciidoctor-pdf book.adoc

book.html: book.adoc 
	@echo "Creating HTML"
	@asciidoctor book.adoc

book/book.html: book.adoc
	@echo "Creating Multi Page HTML"
	@asciidoctor -r asciidoctor-multipage -b multipage_html5 -D book/ --backend multipage_html5 -a data-uri book.adoc

book.epub: book.adoc images/cover.svg
	@echo "Creating epub"
	@asciidoctor-epub3 book.adoc

clean:
	@git clean -fX

install: all 
	@echo "Transferring files to webserver"
	@rsync -avu --chmod=ugo=rx . /var/www/html/mapnik-lost-manual/

install-web: all 
	@echo "Transferring files to webserver"
	@rsync -avu --chmod=ugo=rx -e 'ssh -axC' . h6:/var/www/html/mapnik-lost-manual/

depend::
	@php tools/adoc-dep.php book.adoc > .deps/book.d
	@tools/mapnik-deps.sh > .deps/examples.d 

include examples/Makefile
include examples/data/Makefile

.PHONY : $(PHONY)
