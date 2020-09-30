%.svg : %.xml
	@echo $@
	@./render.sh $<

.PHONY: all,clean,show-latest

all: $(addsuffix .svg, $(basename $(wildcard *.xml)))

clean:
	@rm -f $(addsuffix .svg, $(basename $(wildcard *.xml)))
	@rm -f *~ \#* .\#*

show-latest: all
	@ls -t *.svg | head -1 | xargs display &
