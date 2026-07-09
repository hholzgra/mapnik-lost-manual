all: multipage html epub pdf

PHONY = all clean install depend check
PHONY += html pdf epub multipage

-include .deps/book.d
-include .deps/examples.d

this_dir = $(if $(pathsubst /%,,$(lastword $(MAKEFILE_LIST))),$(dir $(CURDIR)/$(lastword $(MAKEFILE_LIST))),$(dir $(lastword $(MAKEFILE_LIST))))

TOP_DIR := $(abspath .)
THIS_DIR := $(call this_dir)

# does the installed mapnik already support the ArcSymbolizer?
ARC_SUPPORT ?= $(shell python3 -c 'import mapnik,sys; sys.exit(0 if hasattr(mapnik,"ArcSymbolizer") else 1)' 2>/dev/null && echo 1)
export ARC_SUPPORT
ADOCFLAGS = $(if $(ARC_SUPPORT),-a mapnik-arc)

html: book.html

pdf: book.pdf

epub: book.epub

multipage: book/book.html

book.adoc:
	@touch book.adoc

book.pdf: book.adoc
	@echo "Creating PDF"
	@asciidoctor-pdf $(ADOCFLAGS) book.adoc

book.html: book.adoc
	@echo "Creating HTML"
	@asciidoctor $(ADOCFLAGS) book.adoc

book/book.html: book.adoc
	@echo "Creating Multi Page HTML"
	@asciidoctor -r asciidoctor-multipage -b multipage_html5 -D book/ --backend multipage_html5 -a data-uri $(ADOCFLAGS) book.adoc

book.epub: book.adoc images/cover.svg
	@echo "Creating epub"
	@asciidoctor-epub3 $(ADOCFLAGS) book.adoc

check:
	@echo "Checking all examples render"
	@tools/check-examples.sh
	@echo "Checking book builds without warnings"
	@asciidoctor --failure-level=WARN $(ADOCFLAGS) -o /dev/null book.adoc

clean:
	@git clean -fX

check:
	@pre-commit run --all-files

install: all check
	@echo "Transferring files to webserver"
	@rsync -avu --chmod=ugo=rx . /var/www/html/mapnik-lost-manual/

install-web: all check
	@echo "Transferring files to webserver"
	@rsync -avu --chmod=ugo=rx -e 'ssh -axC' . h6:/var/www/html/mapnik-lost-manual/

depend::
	@mkdir -p .deps
	@php tools/adoc-dep.php book.adoc > .deps/book.d
	@tools/mapnik-deps.sh > .deps/examples.d

include examples/Makefile
include examples/data/Makefile

.PHONY : $(PHONY)
