%.svg : %.xml
	./render.sh $<

all: $(addsuffix .svg, $(basename $(wildcard *.xml)))

clean:
	rm -f $(addsuffix .svg, $(basename $(wildcard *.xml)))
	rm -f *~ \#* .\#*
