all: multipage html epub pdf

PHONY = all clean install install-web check
PHONY += html pdf epub multipage

# does the installed mapnik already support the ArcSymbolizer?
ARC_SUPPORT ?= $(shell python3 -c 'import mapnik,sys; sys.exit(0 if hasattr(mapnik,"ArcSymbolizer") else 1)' 2>/dev/null && echo 1)
export ARC_SUPPORT
ADOCFLAGS = $(if $(ARC_SUPPORT),-a mapnik-arc)

# auto-generated dependencies; make rebuilds these and restarts when
# they are missing or older than their sources:
#  - book.d defines BOOK_DEPS, everything the book pulls in via
#    include:: and image:: (chapter .adoc files, example styles,
#    rendered example images, other images)
#  - examples.d makes each rendered example image additionally depend
#    on the data files, symbols and images its style references
-include .deps/book.d
-include .deps/examples.d

adoc_files := book.adoc $(shell find chapters -name '*.adoc')
example_styles := $(shell find examples -name '*.xml' -not -path '*/disabled/*')

.deps/book.d: $(adoc_files) tools/adoc-deps.py
	@mkdir -p .deps
	@tools/adoc-deps.py book.adoc > $@

.deps/examples.d: $(example_styles) tools/mapnik-deps.py
	@mkdir -p .deps
	@tools/mapnik-deps.py > $@

ifeq ($(ARC_SUPPORT),)
# without arc support the arc chapter is not part of the book, so its
# .adoc file and examples must not be prerequisites either
BOOK_DEPS := $(filter-out chapters/xml/symbolizer/arc.adoc examples/Symbolizer/Arc/%,$(BOOK_DEPS))
endif

html: book.html

pdf: book.pdf

epub: book.epub

multipage: book/book.html

book.pdf: book.adoc $(BOOK_DEPS)
	@echo "Creating PDF"
	@asciidoctor-pdf $(ADOCFLAGS) book.adoc

book.html: book.adoc $(BOOK_DEPS)
	@echo "Creating HTML"
	@asciidoctor $(ADOCFLAGS) book.adoc

book/book.html: book.adoc $(BOOK_DEPS)
	@echo "Creating Multi Page HTML"
	@asciidoctor -r asciidoctor-multipage -b multipage_html5 -D book/ --backend multipage_html5 -a data-uri $(ADOCFLAGS) book.adoc

book.epub: book.adoc $(BOOK_DEPS) images/cover.svg
	@echo "Creating epub"
	@asciidoctor-epub3 $(ADOCFLAGS) book.adoc

check:
	@echo "Checking all examples render"
	@tools/check-examples.sh
	@echo "Checking book builds without warnings"
	@asciidoctor --failure-level=WARN $(ADOCFLAGS) -o /dev/null book.adoc
	@asciidoctor-epub3 --failure-level=WARN $(ADOCFLAGS) -o /dev/null book.adoc

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

include examples/Makefile
include examples/data/Makefile

.PHONY : $(PHONY)
